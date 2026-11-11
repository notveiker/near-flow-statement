"""Exploratory post-freeze measures on the same sampled clusters: what NEAR Intents and Chain Signatures did on chain.

Not part of the pre-registered tests U1-U5 (docs/history-sample-prereg.md) and labelled that way wherever it appears.
Per cluster it counts, from the logs and receipts in the block itself:
  executed       `intents_executed` events emitted by intents.near (batches of intents settled)
  intents        intents inside those events
  token_diff     public-mode swap legs (`token_diff` events)
  deposits       `mt_mint` events on intents.near
  withdrawals    `mt_burn` events on intents.near
  signs          receipts executed on v1.signer calling `sign` (Chain Signatures requests)
Quarterly estimates use the same stratified cluster design and cluster bootstrap as sample_metrics.

    python3 -m pipeline.sample_extras rows --root data/sample --out data/derived/sample_extras.jsonl
    python3 -m pipeline.sample_extras results --plan data/sample/plan.json --rows data/derived/sample_extras.jsonl --out data/derived/sample_extras_results.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

from pipeline.near_sample import load_plan, read_cluster
from pipeline.sample_metrics import BOOT, pct, stratum_scale

INTENTS = "intents.near"
SIGNER = "v1.signer"
FIELDS = ("executed", "intents", "token_diff", "deposits", "withdrawals", "signs")
BOOT_SEED = 20261112


def block_extras(blk: dict) -> Counter:
    c: Counter = Counter()
    for sh in blk.get("shards", []):
        for r in sh.get("receipt_execution_outcomes", []):
            rcpt = r.get("receipt") or {}
            eo = r["execution_outcome"]["outcome"]
            if rcpt.get("receiver_id") == SIGNER:
                act = (rcpt.get("receipt") or {}).get("Action") or {}
                for a in act.get("actions", []):
                    if isinstance(a, dict) and a.get("FunctionCall", {}).get("method_name") == "sign":
                        c["signs"] += 1
            if eo.get("executor_id") != INTENTS:
                continue
            for lg in eo.get("logs", []):
                if not lg.startswith("EVENT_JSON:"):
                    continue
                try:
                    e = json.loads(lg[11:])
                except json.JSONDecodeError:
                    continue
                ev = e.get("event")
                if ev == "intents_executed":
                    c["executed"] += 1
                    c["intents"] += len(e.get("data", []))
                elif ev == "token_diff":
                    c["token_diff"] += len(e.get("data", []))
                elif ev == "mt_mint":
                    c["deposits"] += 1
                elif ev == "mt_burn":
                    c["withdrawals"] += 1
    return c


def cluster_extras(cluster: dict, blocks) -> dict:
    tot: Counter = Counter()
    for d in blocks:
        if d["b"] is not None:
            tot.update(block_extras(d["b"]))
    return {"id": cluster["id"], "stratum": cluster["stratum"], "heights": cluster["end"] - cluster["start"] + 1, **{f: tot[f] for f in FIELDS}}


def rows_cmd(root: Path, out: Path) -> int:
    plan = load_plan(root)
    root = Path(root)
    done = {p.stem for p in (root / "clusters").glob("*.json") if (root / "clusters" / f"{p.stem}.jsonl.gz").exists()}
    old = {}
    if Path(out).exists():
        old = {json.loads(x)["id"]: x for x in Path(out).read_text().splitlines() if x}
    n = 0
    with open(out, "w") as f:
        for c in plan["clusters"]:
            if c["id"] not in done:
                continue
            f.write(old.get(c["id"]) or json.dumps(cluster_extras(c, read_cluster(root, c["id"])), sort_keys=True, separators=(",", ":")))
            f.write("\n")
            n += 1
    print(f"{n} cluster rows -> {out}")
    return 0


def per_day(rows: list[dict], scale: float) -> dict:
    H = sum(r["heights"] for r in rows)
    return {f: sum(r[f] for r in rows) / H * scale for f in FIELDS}


def results_cmd(plan_path: Path, rows_path: Path, out: Path) -> int:
    plan = json.loads(Path(plan_path).read_text())
    strata = {s["id"]: s for s in plan["strata"]}
    rows = [json.loads(x) for x in Path(rows_path).read_text().splitlines() if x]
    by: dict[str, list[dict]] = {}
    for r in rows:
        by.setdefault(r["stratum"], []).append(r)
    series = []
    for sid, rs in sorted(by.items()):
        scale = stratum_scale(strata[sid])
        rng = random.Random(f"{BOOT_SEED}:{sid}")
        draws = {f: [] for f in FIELDS}
        for _ in range(BOOT):
            s = per_day([rs[rng.randrange(len(rs))] for _ in rs], scale)
            for f in FIELDS:
                draws[f].append(s[f])
        point = per_day(rs, scale)
        series.append({"quarter": sid, "clusters": len(rs), **{f: {"point": point[f], "lo90": pct(draws[f], .05), "hi90": pct(draws[f], .95)} for f in FIELDS}})
    doc = {"label": "exploratory, post-freeze; not part of U1-U5", "bootstrap": {"B": BOOT, "seed": BOOT_SEED}, "series": series}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    print(f"{len(rows)} clusters, {len(series)} quarters")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("rows")
    p.add_argument("--root", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("results")
    p.add_argument("--plan", required=True)
    p.add_argument("--rows", required=True)
    p.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "rows":
        return rows_cmd(Path(a.root), Path(a.out))
    return results_cmd(Path(a.plan), Path(a.rows), Path(a.out))


if __name__ == "__main__":
    sys.exit(main())
