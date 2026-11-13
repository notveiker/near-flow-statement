"""Sampler check against the full chain for transactions per day (docs/history-sample-validation.md). Writes data/derived/history_sample_validation.json."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from statistics import median

from pipeline.near_sample import load_plan
from pipeline.sample_metrics import bootstrap, pct
from .common import RAW, ROOT


def cut(plan, rows, ids):
    return bootstrap(plan, [r for r in rows if ids is None or r["id"] in ids])


def main() -> int:
    plan = load_plan(ROOT / "data" / "sample")
    rows = [json.loads(x) for x in (ROOT / "data" / "derived" / "sample_clusters.jsonl").read_text().splitlines() if x]
    tx = {r["day"]: int(r["tx"]) for r in json.loads((RAW / "validation" / "tx_daily_census.json").read_text())}
    final = set(json.loads((ROOT / "data" / "sample" / "final_cut.json").read_text())["final_cut_rule_literal"]["ids"])
    out = {}
    for name, ids in (("primary_198", final), ("all_268", None)):
        boot = cut(plan, rows, ids)
        per = []
        for s in plan["strata"]:
            q = s["id"]
            if q in ("2020Q3", "2026Q4") or q not in boot or boot[q]["n"] < 5:
                continue
            d0 = datetime.fromtimestamp(s["t0_ns"] / 1e9, timezone.utc).date()
            d1 = datetime.fromtimestamp(s["t1_ns"] / 1e9, timezone.utc).date()
            days = [d for d in tx if d0.isoformat() <= d <= d1.isoformat()]
            ref = sum(tx[d] for d in days) / len(days)
            est = boot[q]["point"]["tx_per_day"]
            lo, hi = pct(boot[q]["draws"]["tx_per_day"], 0.05), pct(boot[q]["draws"]["tx_per_day"], 0.95)
            per.append({"quarter": q, "clusters": boot[q]["n"], "census_tx_per_day": ref, "estimate": est, "lo90": lo, "hi90": hi, "covered": lo <= ref <= hi,
                        "rel_error": est / ref - 1, "days": len(days)})
        era = lambda f: [p for p in per if f(p["quarter"])]
        cov = lambda ps: sum(p["covered"] for p in ps) / len(ps) if ps else None
        mae = lambda ps: median(abs(p["rel_error"]) for p in ps) if ps else None
        out[name] = {"scored_quarters": len(per), "covered": sum(p["covered"] for p in per), "coverage": cov(per), "intervals_too_narrow_by_rule": cov(per) < 0.8,
                     "median_abs_rel_error": mae(per), "median_signed_rel_error": median(p["rel_error"] for p in per),
                     "pre_2025": {"n": len(era(lambda q: q < "2025")), "coverage": cov(era(lambda q: q < "2025")), "median_abs_rel_error": mae(era(lambda q: q < "2025"))},
                     "from_2025": {"n": len(era(lambda q: q >= "2025")), "coverage": cov(era(lambda q: q >= "2025")), "median_abs_rel_error": mae(era(lambda q: q >= "2025"))},
                     "quarters": per, "not_covered": [p["quarter"] for p in per if not p["covered"]]}
    dest = ROOT / "data" / "derived" / "history_sample_validation.json"
    dest.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print("wrote", dest.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
