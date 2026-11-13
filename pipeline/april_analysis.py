"""Ask B: apply docs/april-drop-method.md to the saved outputs. Writes data/derived/april_drop.json."""
from __future__ import annotations

import json
from datetime import date, timedelta

from .common import RAW, ROOT, sha256

A = RAW / "april"


def load(n):
    return json.loads((A / f"{n}.json").read_text())


def main() -> int:
    daily = load("b1_daily")
    tx = {r["day"]: int(r["tx"]) for r in daily}
    sg = {r["day"]: int(r["signers"]) for r in daily}
    rc = {r["day"]: int(r["receivers"]) for r in daily}
    mean = lambda d, a, b: sum(v for k, v in d.items() if a <= k <= b) / sum(1 for k in d if a <= k <= b)
    q = {"2026-Q1": ("2026-01-01", "2026-03-31"), "2026-Q2": ("2026-04-01", "2026-06-30"), "2026-Q3": ("2026-07-01", "2026-09-30"),
         "2025-Q3": ("2025-07-01", "2025-09-30"), "2025-Q4": ("2025-10-01", "2025-12-31")}
    quarters = {k: {"tx_per_day": mean(tx, *v), "signers_per_day": mean(sg, *v), "receivers_per_day": mean(rc, *v)} for k, v in q.items()}

    def step(day, d=tx):
        d0 = date.fromisoformat(day)
        a = [(d0 + timedelta(i)).isoformat() for i in range(7)]
        b = [(d0 - timedelta(7 - i)).isoformat() for i in range(7)]
        return sum(d[x] for x in a) / sum(d[x] for x in b)
    days = sorted(tx)[10:-10]
    steps = sorted(((step(d), d) for d in days))[:3]
    one_day = sorted(((tx[days[i]] / tx[days[i - 1]], days[i]) for i in range(1, len(days))))[:3]
    s0402 = step("2026-04-02")
    res = {"quarters": quarters, "q2_over_q1_tx": quarters["2026-Q2"]["tx_per_day"] / quarters["2026-Q1"]["tx_per_day"],
           "q2_over_q1_signers": quarters["2026-Q2"]["signers_per_day"] / quarters["2026-Q1"]["signers_per_day"],
           "q2_over_q1_receivers": quarters["2026-Q2"]["receivers_per_day"] / quarters["2026-Q1"]["receivers_per_day"],
           "step_0402_7d_ratio": s0402, "step_exists_at_0402": s0402 <= 0.6, "largest_7d_steps": steps, "largest_1d_drops": one_day,
           "tx_0401_0402_0403": [tx["2026-04-01"], tx["2026-04-02"], tx["2026-04-03"]],
           "signers_0401_0402": [sg["2026-04-01"], sg["2026-04-02"]], "receivers_0401_0402": [rc["2026-04-01"], rc["2026-04-02"]]}
    # monthly concentration
    mrows = load("b2_monthly_top20")
    months = {}
    for r in mrows:
        m = months.setdefault(r["month"], {"total": int(r["month_total"]), "top": []})
        m["top"].append({"receiver": r["receiver"], "n": int(r["n"]), "share": float(r["share"])})
    for m, v in months.items():
        sh = [x["share"] for x in v["top"]]
        v["top1_share"], v["top5_share"], v["top20_share"] = sh[0], sum(sh[:5]), sum(sh)
        v["top1"] = v["top"][0]["receiver"]
    res["months"] = {m: {k: v[k] for k in ("total", "top1", "top1_share", "top5_share", "top20_share")} for m, v in sorted(months.items())}
    res["months_top5_receivers"] = {m: [(x["receiver"], round(x["share"], 4)) for x in v["top"][:5]] for m, v in sorted(months.items())}
    # fortnights
    f = load("b3_fortnights")
    summ = next(r for r in f if r["part"] == "summary")
    before, after, gross, n_signers, n_drop = (float(summ[k]) for k in ("x1", "x2", "x3", "x4", "x5"))
    nshare = {r["k"]: int(float(r["x1"])) for r in f if r["part"] == "n_signers_for_share"}
    top = sorted([r for r in f if r["part"] == "top_signer"], key=lambda r: int(float(r["x4"])))
    fam = sorted([(r["k"], float(r["x1"]), float(r["x2"]), float(r["x3"])) for r in f if r["part"] == "family"], key=lambda t: -t[3])
    half = nshare["0.5"]
    first_half = [r for r in top if int(float(r["x4"])) <= min(half, len(top))]
    fb, fa = sum(float(r["x1"]) for r in first_half), sum(float(r["x2"]) for r in first_half)
    top_fam_share = fam[0][3] / gross
    c1 = half <= 10
    c2 = top_fam_share >= 0.60
    c3 = bool(first_half) and (fa / fb <= 0.10) and half <= len(top)
    c4 = res["step_exists_at_0402"]
    broad = half >= 1000 and top_fam_share <= 0.30
    res["fortnights"] = {"before_total": before, "after_total": after, "net_change": after - before, "after_over_before": after / before, "gross_drop": gross,
                         "signers_total": int(n_drop and float(summ["x4"])), "signers_with_a_drop": int(n_drop), "signers_for_50pct": half, "signers_for_80pct": nshare["0.8"], "signers_for_90pct": nshare["0.9"],
                         "first_half_signers_before": fb, "first_half_signers_after": fa, "first_half_after_over_before": (fa / fb) if fb else None,
                         "top_signers": [{"signer": r["k"], "before": float(r["x1"]), "after": float(r["x2"]), "drop": float(r["x3"]), "cum_share": float(r["x5"]), "rank": int(float(r["x4"]))} for r in top[:15]],
                         "families": [{"family": a, "before": b_, "after": a_, "drop": d_, "share_of_gross_drop": d_ / gross} for a, b_, a_, d_ in fam[:15]],
                         "top_family_share": top_fam_share, "criteria": {"i_signers_for_half_le_10": c1, "ii_top_family_ge_60pct": c2, "iii_first_half_fall_ge_90pct": c3, "iv_step_at_0402": c4},
                         "one_class_ended": c1 and c2 and c3 and c4, "broad_fall": broad}
    res["classification"] = "one class of automated traffic ended" if res["fortnights"]["one_class_ended"] else "a broad fall" if broad else "mixed / between"
    dest = ROOT / "data" / "derived" / "april_drop.json"
    dest.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(f"wrote {dest.relative_to(ROOT)} ({sha256(dest)[:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
