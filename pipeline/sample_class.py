"""Post hoc class counts for the history sample (docs/history-class-adjusted-method.md). Not part of the pre-registered tests U1-U5.

    python3 -m pipeline.sample_class rows --root data/sample --out data/derived/sample_class_rows.jsonl
    python3 -m pipeline.sample_class results
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from multiprocessing import Pool
from pathlib import Path

from pipeline.near_sample import load_plan, read_cluster
from pipeline.sample_metrics import BOOT, BOOT_SEED, pct, stratum_scale

SIGNERS = ("hotwallet.kaiching", "users.kaiching", "sweat-migration.near")
RECV_SUFFIX = ".users.kaiching"
ROOT = Path(__file__).resolve().parents[1]


def row(args) -> dict:
    root, cid = args
    plan_c = None
    c = {"tx_c": 0, "tx_hotwallet": 0, "tx_sweat": 0, "tx_users_signer": 0, "tx_recv_family": 0, "tx": 0}
    outside: set = set()
    nulls = 0
    for d in read_cluster(Path(root), cid):
        if d["b"] is None:
            nulls += 1
            continue
        for sh in d["b"].get("shards", []):
            ch = sh.get("chunk")
            for t in (ch.get("transactions", []) if ch else []):
                b = t["transaction"]
                s, r = b["signer_id"], b["receiver_id"]
                c["tx"] += 1
                in_c = False
                if s == "hotwallet.kaiching":
                    c["tx_hotwallet"] += 1; in_c = True
                elif s == "sweat-migration.near":
                    c["tx_sweat"] += 1; in_c = True
                elif s == "users.kaiching":
                    c["tx_users_signer"] += 1; in_c = True
                if r.endswith(RECV_SUFFIX):
                    if not in_c:
                        c["tx_recv_family"] += 1
                    in_c = True
                if in_c:
                    c["tx_c"] += 1
                if s not in SIGNERS:
                    outside.add(s)
    c.update(id=cid, signers_outside_c=len(outside), null_heights=nulls)
    return c


def rows_cmd(root: Path, out: Path) -> int:
    plan = load_plan(root)
    done = [c["id"] for c in plan["clusters"] if (root / "clusters" / f"{c['id']}.jsonl.gz").exists() and (root / "clusters" / f"{c['id']}.json").exists()]
    with Pool(6) as p:
        rows = p.map(row, [(str(root), i) for i in done])
    Path(out).write_text("\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in rows) + "\n")
    print(f"{len(rows)} class rows -> {out}")
    return 0


def quarter_stat(rs: list[dict], scale: float) -> dict:
    H = sum(r["heights"] for r in rs)
    tx = sum(r["tx"] for r in rs)
    txc = sum(r["tx_c"] for r in rs)
    return {"tx_per_day": tx / H * scale, "tx_per_day_exc": (tx - txc) / H * scale, "c_share": txc / tx if tx else float("nan"),
            "signers_per_100_exc": sum(r["signers_outside_c"] / r["heights"] * 100 for r in rs) / len(rs)}


def analyse(plan: dict, rows: list[dict], cut_ids: set | None) -> dict:
    strata = {s["id"]: s for s in plan["strata"]}
    by: dict = {}
    for r in rows:
        if cut_ids is None or r["id"] in cut_ids:
            by.setdefault(r["stratum"], []).append(r)
    boot = {}
    for sid, rs in sorted(by.items()):
        scale = stratum_scale(strata[sid])
        rng = random.Random(f"classadj:{BOOT_SEED}:{sid}")
        draws = {k: [] for k in ("tx_per_day", "tx_per_day_exc", "c_share", "signers_per_100_exc")}
        for _ in range(BOOT):
            s = quarter_stat([rs[rng.randrange(len(rs))] for _ in rs], scale)
            for k in draws:
                draws[k].append(s[k])
        boot[sid] = {"n": len(rs), "point": quarter_stat(rs, scale), "draws": draws}

    def ratio(m, a, b):
        if a not in boot or b not in boot or boot[a]["n"] < 5 or boot[b]["n"] < 5:
            return None
        rs_ = [x / y for x, y in zip(boot[a]["draws"][m], boot[b]["draws"][m]) if y and y == y and x == x]
        return {"point": boot[a]["point"][m] / boot[b]["point"][m], "lo90": pct(rs_, 0.05), "hi90": pct(rs_, 0.95)}
    series = [{"quarter": q, "clusters": b["n"], **{k: {"point": b["point"][k], "lo90": pct(b["draws"][k], 0.05), "hi90": pct(b["draws"][k], 0.95)} for k in b["draws"]}} for q, b in sorted(boot.items())]
    raw, exc, sg = ratio("tx_per_day", "2026Q3", "2025Q3"), ratio("tx_per_day_exc", "2026Q3", "2025Q3"), ratio("signers_per_100_exc", "2026Q3", "2025Q3")
    c25, c26 = boot["2025Q3"]["point"]["c_share"], boot["2026Q3"]["point"]["c_share"]
    first1 = next((q for q, b in sorted(boot.items()) if b["point"]["c_share"] >= 0.01), None)
    first10 = next((q for q, b in sorted(boot.items()) if b["point"]["c_share"] >= 0.10), None)
    return {"clusters": sum(b["n"] for b in boot.values()), "series": series, "ratio_raw_2026Q3_over_2025Q3": raw, "ratio_exc": exc, "ratio_signers_exc": sg,
            "c_share_2025Q3": c25, "c_share_2026Q3": c26, "first_quarter_c_ge_1pct": first1, "first_quarter_c_ge_10pct": first10,
            "H_C1_supported": c25 >= 0.30 and c26 <= 0.05, "H_C1_falsified": c25 < 0.15 or c26 > 0.10,
            "exc_over_raw": exc["point"] / raw["point"] if exc and raw else None,
            "H_C2_supported": bool(exc and raw and exc["point"] >= 2 * raw["point"]), "H_C2_falsified": bool(exc and raw and exc["point"] < 1.5 * raw["point"]),
            "H_C3_supported": bool(exc and exc["point"] >= 1.0 and exc["lo90"] > 0.8), "ex_c_u1_style_pass": bool(exc and exc["point"] >= 1.5 and exc["lo90"] > 1)}


def results_cmd() -> int:
    plan = load_plan(ROOT / "data" / "sample")
    rows_c = {json.loads(x)["id"]: json.loads(x) for x in (ROOT / "data" / "derived" / "sample_class_rows.jsonl").read_text().splitlines() if x}
    base = {json.loads(x)["id"]: json.loads(x) for x in (ROOT / "data" / "derived" / "sample_clusters.jsonl").read_text().splitlines() if x}
    rows = [{**base[i], **rows_c[i]} for i in rows_c if i in base]
    for r in rows:   # the class counts and the base counts must agree on transactions
        assert r["tx"] == base[r["id"]]["tx"], r["id"]
    cut = set(json.loads((ROOT / "data" / "sample" / "final_cut.json").read_text())["final_cut_rule_literal"]["ids"])
    res = {"primary_198_sealed_by_stop": analyse(plan, rows, cut), "sensitivity_all_268": analyse(plan, rows, None), "post_hoc": True,
           "u1_as_preregistered": json.loads((ROOT / "data" / "derived" / "history_results.json").read_text())["tests"]["U1"]}
    dest = ROOT / "data" / "derived" / "history_class_adjusted.json"
    dest.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print("wrote", dest.relative_to(ROOT))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("rows"); p.add_argument("--root", required=True); p.add_argument("--out", required=True)
    sub.add_parser("results")
    a = ap.parse_args(argv)
    return rows_cmd(Path(a.root), Path(a.out)) if a.cmd == "rows" else results_cmd()


if __name__ == "__main__":
    sys.exit(main())
