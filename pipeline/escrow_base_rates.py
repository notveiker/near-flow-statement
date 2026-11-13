"""Base rates of the escrow-release forward tests E1-E5 (PREREG-ADDENDUM.md, 2026-11-13 06:23 UTC entry). Exploratory.

Recomputes, from committed data only and from days up to 2026-11-04 only, every base rate that entry quotes, over every 30-day
window ending 2026-08-05 to 2026-11-04 (92 windows), and separately over the 39 windows ending 2026-09-27 to 11-04. It reads
data/raw/escrow/deliveries.csv, data/raw/coingecko/near_market_chart_365d.json, data/raw/llama/volume_near-intents.json and
data/raw/explorer/daily.json, makes no network call, and writes nothing: none of these figures is in data/metrics.json.
tests/test_escrow_base_rates.py checks the printed figures against the entry.

Run:  python3 -m pipeline.escrow_base_rates
"""
from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from datetime import date, timedelta

from .common import RAW, read_raw

CUTOFF = "2026-11-04"          # no day after this is read
FIRST_END = "2026-08-05"       # first window end (92 windows to CUTOFF)
SETTLED_END = "2026-09-27"     # first window that holds only days from 2026-08-29
YOCTO = 10 ** 24
EPOCH = date(1970, 1, 1).toordinal()


def add_days(d: str, n: int) -> str:
    return (date.fromisoformat(d) + timedelta(days=n)).isoformat()


def day_of(ms: float) -> str:
    """UTC day of a millisecond timestamp."""
    return date.fromordinal(EPOCH + int(ms // 86_400_000)).isoformat()


def pearson(x: list[float], y: list[float]) -> float:
    mx, my = sum(x) / len(x), sum(y) / len(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / (sxx * syy) ** 0.5


def load() -> dict:
    price: dict[str, float] = {}
    for ms, p in read_raw("coingecko/near_market_chart_365d.json")["prices"]:
        d = day_of(ms)
        if d <= CUTOFF:
            price[d] = float(p)  # last point of each UTC day wins, as in pipeline/compute.py
    vol = {}
    for t, v in read_raw("llama/volume_near-intents.json").get("totalDataChart") or []:
        d = day_of(int(t) * 1000)
        if d <= CUTOFF:
            vol[d] = float(v) / 2  # halved, as the entry says
    exp = {x["date"]: float(x["usd_in"]) for x in read_raw("explorer/daily.json")["days"] if x["date"] <= CUTOFF}
    esc_lots: dict[str, list[float]] = defaultdict(list)   # NEAR per escrow delivery, by day
    coll_a: dict[str, float] = defaultdict(float)           # collector A NEAR, by day
    with open(RAW / "escrow" / "deliveries.csv", newline="", encoding="utf-8") as f:
        for x in csv.DictReader(f):
            if x["day"] > CUTOFF:
                continue
            near = int(x["amount_yocto"]) / YOCTO
            if x["path"] == "escrow_unshield":
                esc_lots[x["day"]].append(near)
            elif x["path"] == "collector_a":
                coll_a[x["day"]] += near
    return {"price": price, "vol": vol, "exp": exp, "esc": esc_lots, "a": coll_a}


def windows(D: dict) -> list[dict]:
    out = []
    end = FIRST_END
    while end <= CUTOFF:
        days = [add_days(end, -29 + i) for i in range(30)]
        P, V, E, A = D["price"], D["vol"], D["esc"], D["a"]
        esc_near = [sum(E.get(d, [])) for d in days]
        esc_usd = [esc_near[i] * P[d] for i, d in enumerate(days)]
        lots_usd = [n * P[d] for d in days for n in E.get(d, [])]
        vol = [V[d] for d in days]
        w = {
            "end": end,
            "e1_days": sum(1 for d in days if E.get(d)),
            "e2_band_pct": 100 * sum(1 for u in lots_usd if 900 <= u < 5000) / len(lots_usd),
            "e2_floor_pct": 100 * sum(1 for u in lots_usd if u >= 900) / len(lots_usd),
            "e3_max_day_pct": 100 * max(esc_near) / sum(esc_near),
            "e3_window_near": sum(esc_near),
            "e4_r": pearson(esc_usd, vol),
            "e5_bp": sum(A.get(d, 0.0) * P[d] for d in days) / sum(vol) * 1e4,
            "escrow_bp": sum(esc_usd) / sum(vol) * 1e4,
        }
        if all(d in D["exp"] for d in days):
            w["e4_outside_r"] = pearson(esc_usd, [V[d] - D["exp"][d] for d in days])
            w["e4_explorer_r"] = pearson(esc_usd, [D["exp"][d] for d in days])
        out.append(w)
        end = add_days(end, 1)
    return out


def summary() -> dict:
    D = load()
    W = windows(D)
    S = [w for w in W if w["end"] >= SETTLED_END]
    X = [w for w in W if "e4_outside_r" in w]
    XS = [w for w in X if w["end"] >= SETTLED_END]
    settled_days = [add_days("2026-08-29", i) for i in range((date.fromisoformat(CUTOFF) - date(2026, 8, 29)).days + 1)]
    counts = [len(D["esc"].get(d, [])) for d in settled_days]
    e5_miss = [w for w in W if not 1.30 <= round(w["e5_bp"], 2) <= 2.50]
    a_usd = {d: D["a"].get(d, 0.0) * D["price"][d] for d in D["price"] if d in D["a"]}
    return {
        "n_windows": len(W), "n_settled": len(S),
        "e1_pass": sum(w["e1_days"] >= 28 for w in W), "e1_pass_settled": sum(w["e1_days"] >= 28 for w in S),
        "e1_min_days_settled": min(w["e1_days"] for w in S),
        "e1_min_daily_count_from_0829": min(counts), "e1_median_daily_count_from_0829": statistics.median(counts),
        "e2_pass": sum(w["e2_band_pct"] >= 95 for w in W), "e2_min_band_pct": round(min(w["e2_band_pct"] for w in W), 1),
        "e2_min_band_end": min(W, key=lambda w: w["e2_band_pct"])["end"],
        "e2_min_floor_pct": round(min(w["e2_floor_pct"] for w in W), 1),
        "e3_pass": sum(w["e3_max_day_pct"] <= 15 for w in W), "e3_pass_settled": sum(w["e3_max_day_pct"] <= 15 for w in S),
        "e3_max_settled_pct": round(max(w["e3_max_day_pct"] for w in S), 1),
        "e3_max_all_pct": round(max(w["e3_max_day_pct"] for w in W), 1),
        "e3_day_1004_near": round(sum(D["esc"]["2026-10-04"])), "e3_day_1015_near": round(sum(D["esc"]["2026-10-15"])),
        "e3_window_near_to_cutoff": round(W[-1]["e3_window_near"]),
        "e4_pass": sum(w["e4_r"] >= 0.20 for w in W), "e4_pass_settled": sum(w["e4_r"] >= 0.20 for w in S),
        "e4_min_settled": round(min(w["e4_r"] for w in S), 3), "e4_median_settled": round(statistics.median(w["e4_r"] for w in S), 3),
        "e4_min_all": round(min(w["e4_r"] for w in W), 3),
        "e4_min_all_ends": [w["end"] for w in W if round(w["e4_r"], 3) == round(min(x["e4_r"] for x in W), 3)],
        "e4_outside_n": len(X), "e4_outside_pass": sum(w["e4_outside_r"] >= 0.20 for w in X),
        "e4_outside_median_settled": round(statistics.median(w["e4_outside_r"] for w in XS), 3),
        "e4_explorer_median_settled": round(statistics.median(w["e4_explorer_r"] for w in XS), 3),
        "e5_pass": len(W) - len(e5_miss), "e5_miss": [(w["end"], round(w["e5_bp"], 2)) for w in e5_miss],
        "e5_settled_min_bp": round(min(w["e5_bp"] for w in S), 2), "e5_settled_max_bp": round(max(w["e5_bp"] for w in S), 2),
        "e5_bp_to_cutoff": round(W[-1]["e5_bp"], 2),
        "e5_usd_1103": round(a_usd["2026-11-03"]), "e5_usd_1104": round(a_usd["2026-11-04"]),
        "escrow_bp_1020_1104": (round(min(w["escrow_bp"] for w in W if w["end"] >= "2026-10-20"), 2),
                                round(max(w["escrow_bp"] for w in W if w["end"] >= "2026-10-20"), 2)),
    }


def main() -> int:
    for k, v in summary().items():
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
