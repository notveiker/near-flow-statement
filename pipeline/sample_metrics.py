"""Metrics, estimators and the pre-registered history tests, computed from the sampled clusters.

Inputs: a sample root written by pipeline.near_sample (plan.json plus sealed clusters).
Outputs (small, committed): data/derived/sample_clusters.jsonl (one row per cluster) and
data/derived/history_results.json (quarter series with intervals, U1-U5 verdicts, counter-evidence table).

Definitions are in docs/history-sample-prereg.md. The ones that need a precise reading of the NEARDATA block:
  tx            one entry of a chunk's transaction list (a meta-transaction counts once)
  ok_tx         the transaction's own outcome is not a Failure (a receipt was created); receipt-level failures are
                counted separately in ok_receipts and are reported but not tested
  burnt         sum of tokens_burnt over transaction outcomes and receipt execution outcomes, in NEAR
  intents       a receipt executed with receiver_id == "intents.near"
  signers       distinct transaction signer_id in the cluster

Run:
    python3 -m pipeline.sample_metrics rows    --root data/sample --out data/derived/sample_clusters.jsonl
    python3 -m pipeline.sample_metrics results --plan data/sample/plan.json --rows data/derived/sample_clusters.jsonl --out data/derived/history_results.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

from pipeline.near_sample import load_plan, read_cluster

YOCTO = 10**24
INTENTS = "intents.near"
TOP_KEEP = 200  # receivers kept per cluster; the rest are pooled into "other"
BOOT = 2000
BOOT_SEED = 20261111


# ---------------------------------------------------------------- per-cluster metrics
def _failed(status) -> bool:
    return isinstance(status, dict) and "Failure" in status


def block_counts(blk: dict, recv: Counter, signers: set) -> dict:
    """Scalar counts for one NEARDATA block; updates the receiver counter and signer set."""
    tx = ok = rc = rc_ok = intents = 0
    burnt = 0
    for sh in blk.get("shards", []):
        ch = sh.get("chunk")
        if ch:
            for t in ch.get("transactions", []):
                tx += 1
                body = t["transaction"]
                recv[body["receiver_id"]] += 1
                signers.add(body["signer_id"])
                eo = t["outcome"]["execution_outcome"]["outcome"]
                ok += not _failed(eo["status"])
                burnt += int(eo["tokens_burnt"])
        for r in sh.get("receipt_execution_outcomes", []):
            eo = r["execution_outcome"]["outcome"]
            rc += 1
            rc_ok += not _failed(eo["status"])
            burnt += int(eo["tokens_burnt"])
            rcpt = r.get("receipt")
            if rcpt and rcpt.get("receiver_id") == INTENTS:
                intents += 1
    return {"tx": tx, "ok_tx": ok, "receipts": rc, "ok_receipts": rc_ok, "intents": intents, "burnt_yocto": burnt}


def cluster_row(cluster: dict, blocks) -> dict:
    """blocks: iterable of {"h", "b"} for the cluster's heights. Returns one row of scalars plus receiver counts."""
    tot = Counter()
    recv: Counter = Counter()
    signers: set = set()
    nulls = 0
    for d in blocks:
        if d["b"] is None:
            nulls += 1
            continue
        tot.update(block_counts(d["b"], recv, signers))
    top = recv.most_common(TOP_KEEP)
    other = sum(recv.values()) - sum(v for _, v in top)
    return {
        "id": cluster["id"], "stratum": cluster["stratum"], "start": cluster["start"], "heights": cluster["end"] - cluster["start"] + 1,
        "null_heights": nulls, "tx": tot["tx"], "ok_tx": tot["ok_tx"], "receipts": tot["receipts"], "ok_receipts": tot["ok_receipts"],
        "intents": tot["intents"], "burnt_near": tot["burnt_yocto"] / YOCTO, "signers": len(signers),
        "receivers": dict(top), "receivers_other": other,
    }


def rows_cmd(root: Path, out: Path) -> int:
    plan = load_plan(root)
    done = {p.stem for p in (Path(root) / "clusters").glob("*.json")}
    old = {}
    if Path(out).exists():
        old = {json.loads(x)["id"]: x for x in Path(out).read_text().splitlines() if x}
    n = 0
    with open(out, "w") as f:
        for c in plan["clusters"]:
            if c["id"] not in done:
                continue
            if c["id"] in old:
                f.write(old[c["id"]] + "\n")
            else:
                f.write(json.dumps(cluster_row(c, read_cluster(root, c["id"])), sort_keys=True, separators=(",", ":")) + "\n")
            n += 1
    print(f"{n} cluster rows -> {out}")
    return 0


# ---------------------------------------------------------------- estimators
METRICS = ["tx_per_day", "ok_share", "tx_per_day_ex_top", "signers_per_100", "burn_near_per_day", "intents_per_day",
           "top_receiver_share", "ok_receipt_share", "receipts_per_day"]


def stratum_scale(st: dict) -> float:
    """Heights per day in the stratum, from its boundary timestamps."""
    days = (st["t1_ns"] - st["t0_ns"]) / 86_400e9
    return (st["h1"] - st["h0"] + 1) / days


def quarter_stat(rows: list[dict], scale: float, top: str | None) -> dict:
    """All metrics for one resample (or the full sample) of a quarter's cluster rows."""
    H = sum(r["heights"] for r in rows)
    tx = sum(r["tx"] for r in rows)
    top_tx = sum(r["receivers"].get(top, 0) for r in rows) if top else 0
    return {
        "tx_per_day": tx / H * scale,
        "ok_share": sum(r["ok_tx"] for r in rows) / tx if tx else float("nan"),
        "tx_per_day_ex_top": (tx - top_tx) / H * scale,
        "signers_per_100": sum(r["signers"] / r["heights"] * 100 for r in rows) / len(rows),
        "burn_near_per_day": sum(r["burnt_near"] for r in rows) / H * scale,
        "intents_per_day": sum(r["intents"] for r in rows) / H * scale,
        "top_receiver_share": top_tx / tx if tx else float("nan"),
        "ok_receipt_share": sum(r["ok_receipts"] for r in rows) / max(sum(r["receipts"] for r in rows), 1),
        "receipts_per_day": sum(r["receipts"] for r in rows) / H * scale,
    }


def top_receiver(rows: list[dict]) -> str | None:
    c: Counter = Counter()
    for r in rows:
        c.update(r["receivers"])
    return c.most_common(1)[0][0] if c else None


def pct(xs: list[float], p: float) -> float:
    xs = sorted(x for x in xs if x == x)
    if not xs:
        return float("nan")
    i = (len(xs) - 1) * p
    lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def bootstrap(plan: dict, rows: list[dict], B: int = BOOT, seed: int = BOOT_SEED) -> dict:
    """{quarter: {"n": clusters, "top": id, "point": {metric: v}, "draws": {metric: [B values]}}}."""
    strata = {s["id"]: s for s in plan["strata"]}
    by: dict[str, list[dict]] = {}
    for r in rows:
        by.setdefault(r["stratum"], []).append(r)
    out = {}
    for sid, rs in sorted(by.items()):
        scale, top = stratum_scale(strata[sid]), top_receiver(rs)
        rng = random.Random(f"{seed}:{sid}")
        draws = {m: [] for m in METRICS}
        for _ in range(B):
            s = quarter_stat([rs[rng.randrange(len(rs))] for _ in rs], scale, top)
            for m in METRICS:
                draws[m].append(s[m])
        out[sid] = {"n": len(rs), "top": top, "point": quarter_stat(rs, scale, top), "draws": draws}
    return out


def ratio(boot: dict, metric: str, num: str, den: str) -> dict | None:
    if num not in boot or den not in boot:
        return None
    a, b = boot[num]["draws"][metric], boot[den]["draws"][metric]
    rs = [x / y for x, y in zip(a, b) if y and y == y and x == x]
    p = boot[num]["point"][metric] / boot[den]["point"][metric] if boot[den]["point"][metric] else float("nan")
    return {"num": num, "den": den, "metric": metric, "point": p, "lo90": pct(rs, 0.05), "hi90": pct(rs, 0.95)}


def diff(boot: dict, metric: str, num: str, den: str) -> dict | None:
    if num not in boot or den not in boot:
        return None
    ds = [x - y for x, y in zip(boot[num]["draws"][metric], boot[den]["draws"][metric])]
    return {"point": boot[num]["point"][metric] - boot[den]["point"][metric], "lo90": pct(ds, 0.05), "hi90": pct(ds, 0.95)}


def verdicts(boot: dict) -> dict:
    """The five pre-registered tests. A test with a missing quarter is 'not scorable', never estimated."""
    q_now, q_prev, q_int = "2026Q3", "2025Q3", "2025Q1"
    res = {}

    def mk(i, hyp, r, thr, extra_pass=True, extra=None):
        if r is None:
            res[i] = {"hypothesis": hyp, "verdict": "not scorable"}
            return
        ok = r["point"] >= thr and r["lo90"] > 1 and extra_pass
        res[i] = {"hypothesis": hyp, "ratio": r, "threshold": thr, "verdict": "pass" if ok else "fail", **(extra or {})}

    mk("U1", "NEAR usage has grown (tx per day)", ratio(boot, "tx_per_day", q_now, q_prev), 1.5)
    top_d = diff(boot, "top_receiver_share", q_now, q_prev)
    r2 = ratio(boot, "tx_per_day_ex_top", q_now, q_prev)
    share_ok = top_d is not None and top_d["point"] <= 0
    mk("U2", "The growth is not one contract", r2, 1.25, share_ok, {"top_receiver_share_change": top_d,
       "top_receiver": {q: boot[q]["top"] for q in (q_prev, q_now) if q in boot}})
    mk("U3", "Intents is a real share of activity (receipts on intents.near per day)", ratio(boot, "intents_per_day", q_now, q_int), 2.0)
    mk("U4", "More distinct users (signers per 100 blocks)", ratio(boot, "signers_per_100", q_now, q_prev), 1.2)
    mk("U5", "Fee burn has grown (NEAR burnt per day)", ratio(boot, "burn_near_per_day", q_now, q_prev), 1.25)
    v = [res[k]["verdict"] for k in ("U1", "U2", "U3")]
    res["overall"] = ("supported by sampled history" if all(x == "pass" for x in v)
                        else "not scorable" if "not scorable" in v else "not supported")
    return res


def series(boot: dict) -> list[dict]:
    out = []
    for sid, b in sorted(boot.items()):
        row = {"quarter": sid, "clusters": b["n"], "top_receiver": b["top"]}
        for m in METRICS:
            row[m] = {"point": b["point"][m], "lo90": pct(b["draws"][m], 0.05), "hi90": pct(b["draws"][m], 0.95)}
        out.append(row)
    return out


def counter_evidence(boot: dict, issuance_near_per_day: float | None = None) -> dict:
    """Counter-evidence, printed whatever the verdicts are."""
    q = "2026Q3"
    t: dict = {}
    if q in boot and issuance_near_per_day:
        t["burn_share_of_issuance_2026Q3"] = boot[q]["point"]["burn_near_per_day"] / issuance_near_per_day
        t["issuance_near_per_day_used"] = issuance_near_per_day
    for m in ("tx_per_day", "intents_per_day", "burn_near_per_day", "signers_per_100", "tx_per_day_ex_top"):
        vals = [(s, b["point"][m]) for s, b in sorted(boot.items())]
        t[f"quarters_where_{m}_fell"] = [s1 for (s0, a), (s1, b) in zip(vals, vals[1:]) if b < a]
    for s in ("2025Q3", "2026Q3"):
        if s in boot:
            t[f"top_receiver_{s}"] = {"account": boot[s]["top"], "share": boot[s]["point"]["top_receiver_share"]}
            t[f"ok_share_{s}"] = boot[s]["point"]["ok_share"]
    return t


def results_cmd(plan_path: Path, rows_path: Path, out: Path, issuance: float | None) -> int:
    plan = json.loads(Path(plan_path).read_text())
    rows = [json.loads(x) for x in Path(rows_path).read_text().splitlines() if x]
    boot = bootstrap(plan, rows)
    res = {
        "seed": plan["seed"], "clusters_used": len(rows), "bootstrap": {"B": BOOT, "seed": BOOT_SEED},
        "series": series(boot), "tests": verdicts(boot), "counter_evidence": counter_evidence(boot, issuance),
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(f"{len(rows)} clusters; overall: {res['tests']['overall']}")
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
    p.add_argument("--issuance-near-per-day", type=float, default=None)
    a = ap.parse_args(argv)
    if a.cmd == "rows":
        return rows_cmd(Path(a.root), Path(a.out))
    return results_cmd(Path(a.plan), Path(a.rows), Path(a.out), a.issuance_near_per_day)


if __name__ == "__main__":
    sys.exit(main())
