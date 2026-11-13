"""Apply docs/class-census-method.md to the saved outputs. Writes data/derived/class_census.json."""
from __future__ import annotations

import json
from collections import defaultdict

from .common import RAW, ROOT

A = RAW / "april"


def qof(day: str) -> str:
    return f"{day[:4]}Q{(int(day[5:7]) - 1) // 3 + 1}"


def main() -> int:
    daily = json.loads((A / "c1_class_daily.json").read_text())
    f = lambda r, k: int(r[k])
    tot = defaultdict(lambda: defaultdict(float))
    mon = defaultdict(lambda: defaultdict(float))
    days = defaultdict(int)
    for r in daily:
        c = sum(f(r, k) for k in ("tx_hotwallet", "tx_sweat", "tx_users_signer", "tx_recv_family"))
        for acc, key in ((tot, qof(r["day"])), (mon, r["day"][:7])):
            acc[key]["tx"] += f(r, "tx"); acc[key]["c"] += c
            for k in ("tx_hotwallet", "tx_sweat", "tx_users_signer", "tx_recv_family"):
                acc[key][k] += f(r, k)
        days[qof(r["day"])] += 1
    q = {k: {"days": days[k], "tx_per_day": v["tx"] / days[k], "c_per_day": v["c"] / days[k], "exc_per_day": (v["tx"] - v["c"]) / days[k], "c_share": v["c"] / v["tx"],
             "parts_per_day": {p: v[p] / days[k] for p in ("tx_hotwallet", "tx_sweat", "tx_users_signer", "tx_recv_family")}} for k, v in sorted(tot.items())}
    m = {k: {"tx": v["tx"], "c": v["c"], "c_share": v["c"] / v["tx"]} for k, v in sorted(mon.items())}
    first1 = next((k for k, v in m.items() if v["c_share"] >= 0.01), None)
    first10 = next((k for k, v in m.items() if v["c_share"] >= 0.10), None)
    raw_ratio = q["2026Q3"]["tx_per_day"] / q["2025Q3"]["tx_per_day"]
    exc_ratio = q["2026Q3"]["exc_per_day"] / q["2025Q3"]["exc_per_day"]
    samp = json.loads((ROOT / "data" / "derived" / "history_class_adjusted.json").read_text())["primary_198_sealed_by_stop"]
    sr, se = samp["ratio_raw_2026Q3_over_2025Q3"], samp["ratio_exc"]
    share = q["2025Q3"]["c_share"]
    res = {"quarters": q, "months": m, "first_month_c_ge_1pct": first1, "first_month_c_ge_10pct": first10,
           "c_share_2025Q3": share, "H_E1_supported": 0.25 <= share <= 0.45, "H_E1_falsified": share < 0.15 or share > 0.60,
           "raw_ratio_2026Q3_over_2025Q3": raw_ratio, "exc_ratio_2026Q3_over_2025Q3": exc_ratio,
           "H_E2_raw_inside_sample_interval": sr["lo90"] <= raw_ratio <= sr["hi90"], "H_E2_exc_inside_sample_interval": se["lo90"] <= exc_ratio <= se["hi90"],
           "sample_intervals": {"raw": sr, "exc": se}}
    d = json.loads((A / "c2_signer_decline.json").read_text())
    s = next(r for r in d if r["part"] == "summary")
    n = {r["k"]: int(float(r["x1"])) for r in d if r["part"] == "n_for_share"}
    top = sorted([r for r in d if r["part"] == "top_decline"], key=lambda r: int(float(r["x4"])))
    dec = float(s["x3"])
    res["decline"] = {"ex_c_a": float(s["x1"]), "ex_c_b": float(s["x2"]), "ex_c_b_over_a": float(s["x2"]) / float(s["x1"]), "gross_decline": dec, "gross_rise": float(s["x4"]), "signers": int(float(s["x5"])),
                      "signers_for_50pct": n["0.5"], "signers_for_80pct": n["0.8"], "concentrated": n["0.5"] <= 20, "broad": n["0.5"] >= 500,
                      "top1_share": float(top[0]["x3"]) / dec, "top5_share": sum(float(r["x3"]) for r in top[:5]) / dec, "top20_share": sum(float(r["x3"]) for r in top[:20]) / dec,
                      "top_decliners": [{"signer": r["k"], "a": float(r["x1"]), "b": float(r["x2"]), "decline": float(r["x3"]), "cum_share": float(r["x5"]), "top_receiver": r["note"]} for r in top[:20]],
                      "top_risers": [{"signer": r["k"], "a": float(r["x1"]), "b": float(r["x2"]), "rise": float(r["x3"]), "top_receiver": r["note"]} for r in sorted([r for r in d if r["part"] == "top_rise"], key=lambda r: -float(r["x3"]))[:10]]}
    dest = ROOT / "data" / "derived" / "class_census.json"
    dest.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print("wrote", dest.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
