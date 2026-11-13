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


def other_metrics(plan, rows, final) -> dict:
    """Addendum of docs/history-sample-validation.md: receipts, intents receipts and burn for 2025Q1..2026Q3 against execution_outcomes and transactions."""
    oc = {r["day"]: r for r in json.loads((RAW / "validation" / "outcomes_daily_census.json").read_text())}
    tb = {r["day"]: float(r["tx_burnt_near"] or 0) for r in json.loads((RAW / "validation" / "tx_burn_daily_census.json").read_text())}
    cens = {"receipts_per_day": lambda d: int(oc[d]["outcomes"]), "intents_per_day": lambda d: int(oc[d]["on_intents"]),
            "burn_near_per_day": lambda d: float(oc[d]["burnt_near"]) + tb[d]}
    res = {}
    for name, ids in (("primary_198", final), ("all_268", None)):
        boot = cut(plan, rows, ids)
        res[name] = {}
        for m, f in cens.items():
            per = []
            for s in plan["strata"]:
                q = s["id"]
                if not ("2025Q1" <= q <= "2026Q3") or q not in boot or boot[q]["n"] < 5:
                    continue
                d0 = datetime.fromtimestamp(s["t0_ns"] / 1e9, timezone.utc).date().isoformat()
                d1 = datetime.fromtimestamp(s["t1_ns"] / 1e9, timezone.utc).date().isoformat()
                days = [d for d in oc if d0 <= d <= d1]
                ref = sum(f(d) for d in days) / len(days)
                est = boot[q]["point"][m]
                lo, hi = pct(boot[q]["draws"][m], 0.05), pct(boot[q]["draws"][m], 0.95)
                per.append({"quarter": q, "census": ref, "estimate": est, "lo90": lo, "hi90": hi, "covered": lo <= ref <= hi, "ratio": est / ref if ref else None})
            med_ratio = median(p["ratio"] for p in per if p["ratio"] is not None)
            match = 0.9 <= med_ratio <= 1.1
            res[name][m] = {"quarters": per, "median_sample_over_census": med_ratio, "definitions_match": match,
                            "coverage": (sum(p["covered"] for p in per) / len(per)) if match else None, "covered": sum(p["covered"] for p in per), "n": len(per),
                            "too_narrow_by_rule": (sum(p["covered"] for p in per) / len(per) < 0.8) if match else None,
                            "median_abs_rel_error": median(abs(p["ratio"] - 1) for p in per)}
    return res


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
    out["other_metrics"] = other_metrics(plan, rows, final)
    dest = ROOT / "data" / "derived" / "history_sample_validation.json"
    dest.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print("wrote", dest.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
