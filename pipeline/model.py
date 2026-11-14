"""Forward view (exploratory, chosen 2026-11-13, after the freeze): can captured Intents revenue grow into NEAR's dilution?

The question is the frozen rating rule's own (PREREG.md, "Rating rule"): does captured Intents revenue reach the USD value of
net new supply by 2031-11-04? The rule answers it with one constant price and one growth rate (G_req). This module asks it
with a distribution instead, and changes nothing the rule, H1a, H1b or H1c compute.

Coverage = captured Intents revenue over a trailing 90 days (three model months) / USD value of the net new NEAR minted in
the same months. It is the ratio of PREREG prediction P3.

  * Supply: the same daily path as pipeline.h1a.g_req (realised share of the inflation cap, post-v87 burn), with HSP-029's
    ramp (as in G_req) and without it. Deterministic.
  * Volume and price: each model month draws one calendar month at random from the captured-revenue months in the data
    (2025-11 to 2026-10) and applies that month's change in Intents volume (DefiLlama) and in NEAR's mean price (CoinGecko)
    together, so the two keep whatever co-movement the data show. An i.i.d. bootstrap of 11 monthly pairs: no trend, regime
    or mean reversion is added, and the bands are as wide as the data make them.
  * Price drift: NEAR's mean price roughly doubled over those months (a mean monthly change of fwd_price_monthly_mean_pct).
    Replaying that for five years would assume the price trend continues, so the main run removes the mean from the price
    changes (same volatility, same co-movement with volume, no drift). The run with the historical drift is a sensitivity.
    A higher price means each dollar of revenue buys back less NEAR, so it lowers coverage.
  * Take rate: captured revenue / volume over the last 90 days, held fixed (no further fee-share steps). Coverage scales
    with it in proportion, so the sensitivity at other take rates reuses the same paths.

Standard library only; a fixed seed makes the output identical on every run.
"""
from __future__ import annotations

import math
import random
from datetime import date, timedelta

from .common import read_raw
from .h1a import _cap, issuance

SEED = 20261113
N_PATHS = 10_000
MONTHS = 60                       # 2026-11-04 + 60 model months = 2031-11-04, the rating rule's target date
MONTH_DAYS = 365.25 / 12
BOOT_FIRST, BOOT_LAST = "2025-11", "2026-10"   # full calendar months with captured revenue (DefiLlama labels it from 2025-11)
CHECKPOINTS = {"2027": 12, "2028": 24, "2031": 60}
TAKE_SENS = (0.5, 2.0)            # take-rate multipliers for the sensitivity
PCTS = (10, 25, 50, 75, 90)


def _month_key(d: str) -> str:
    return d[:7]


def _pct(xs: list[float], p: float) -> float:
    """Percentile by linear interpolation on a sorted list."""
    k = (len(xs) - 1) * p / 100
    lo = math.floor(k)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def supply_path(asof: date, target: date, hsp029: bool) -> dict[date, float]:
    """NEAR supply by day from the window-end header to target, exactly as pipeline.h1a.g_req simulates it."""
    ra = read_raw("rpc/rating_assumptions.json")
    iss = issuance()
    act = date.fromisoformat(ra["hsp029"]["activation_date"]) if hsp029 else None
    s, d, path = iss["supply_end"], asof, {asof: iss["supply_end"]}
    while d < target:
        d += timedelta(days=1)
        s += _cap(d, act, ra["hsp029"]) * iss["cap_share"] * s / 365 - iss["burn_per_day_v87"]
        path[d] = s
    return path


def boot_pairs(vol: dict[str, float], price: dict[str, float]) -> list[tuple[str, float, float]]:
    """(month, log change in monthly Intents volume, log change in mean monthly NEAR price) for each month after BOOT_FIRST."""
    mv: dict[str, float] = {}
    for d, v in vol.items():
        mv[_month_key(d)] = mv.get(_month_key(d), 0.0) + v
    mp: dict[str, list[float]] = {}
    for d, p in price.items():
        mp.setdefault(_month_key(d), []).append(p)
    months = sorted(k for k in mv if BOOT_FIRST <= k <= BOOT_LAST)
    out = []
    for a, b in zip(months, months[1:]):
        if a in mp and b in mp and mv[a] > 0:
            out.append((b, math.log(mv[b] / mv[a]), math.log((sum(mp[b]) / len(mp[b])) / (sum(mp[a]) / len(mp[a])))))
    return out


def _corr(x: list[float], y: list[float]) -> float:
    mx, my = sum(x) / len(x), sum(y) / len(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return sxy / math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))


def forward(m: dict, rev: dict[str, float], vol: dict[str, float], price: dict[str, float]) -> dict:
    """Write the fwd_* metrics into m and return the chart series {"fwd_fan": [...], "fwd_supply": [...]}."""
    ra = read_raw("rpc/rating_assumptions.json")
    asof = date.fromisoformat(ra["asof"])
    target = asof + timedelta(days=round(MONTHS * MONTH_DAYS))
    last90 = [(asof - timedelta(days=i)).isoformat() for i in range(90)]
    r90 = sum(rev[d] for d in last90)
    v90 = sum(vol[d] for d in last90)
    take = r90 / v90
    p0 = float(ra["price_usd"])

    paths = {h: supply_path(asof, target, h) for h in (True, False)}
    iss = issuance()
    n90_now = iss["net"]                              # net new NEAR over the 90-day supply window (H1a's)
    edges = [asof + timedelta(days=round(k * MONTH_DAYS)) for k in range(MONTHS + 1)]
    new_near = {h: [paths[h][edges[k]] - paths[h][edges[k - 1]] for k in range(1, MONTHS + 1)] for h in paths}

    pairs = boot_pairs(vol, price)
    mean_dp = sum(x[2] for x in pairs) / len(pairs)
    flat = [(mo, dv, dp - mean_dp) for mo, dv, dp in pairs]
    now = r90 / (n90_now * p0)

    def simulate(boot: list[tuple[str, float, float]]) -> dict[bool, list[list[float]]]:
        rng = random.Random(SEED)   # the same draws for every variant (common random numbers)
        cov = {h: [[now] * N_PATHS] + [[0.0] * N_PATHS for _ in range(MONTHS)] for h in paths}
        for i in range(N_PATHS):
            v, p = v90 / 3, p0
            revs, dil = {h: [r90 / 3] * 3 for h in paths}, {h: [n90_now / 3 * p0] * 3 for h in paths}
            for k in range(1, MONTHS + 1):
                _, dv, dp = boot[rng.randrange(len(boot))]
                v *= math.exp(dv)
                p *= math.exp(dp)
                for h in paths:
                    revs[h].append(v * take)
                    dil[h].append(new_near[h][k - 1] * p)
                    cov[h][k][i] = sum(revs[h][-3:]) / sum(dil[h][-3:])
        return {h: [sorted(col) for col in cov[h]] for h in paths}

    srt = simulate(flat)
    drift = simulate(pairs)

    def prob(h: bool, k: int, line: float) -> float:
        col = srt[h][k]
        return sum(1 for x in col if x >= line) / len(col)

    m["fwd_seed"] = SEED
    m["fwd_paths_n"] = N_PATHS
    m["fwd_months_n"] = MONTHS
    m["fwd_target_date"] = target.isoformat()
    m["fwd_boot_months_n"] = len(pairs)
    m["fwd_boot_first"], m["fwd_boot_last"] = pairs[0][0], pairs[-1][0]
    m["fwd_vol_price_corr"] = round(_corr([x[1] for x in pairs], [x[2] for x in pairs]), 2)
    m["fwd_vol_monthly_mean_pct"] = round((math.exp(sum(x[1] for x in pairs) / len(pairs)) - 1) * 100, 1)
    m["fwd_price_monthly_mean_pct"] = round((math.exp(sum(x[2] for x in pairs) / len(pairs)) - 1) * 100, 1)
    m["fwd_take_bp"] = round(take * 1e4, 2)
    m["fwd_coverage_now_pct"] = round(now * 100, 1)
    for tag, k in CHECKPOINTS.items():
        for q in PCTS:
            m[f"fwd_cov_{tag}_p{q}_pct"] = round(_pct(srt[True][k], q) * 100, 1)
        m[f"fwd_p_cov_ge100_{tag}_pct"] = round(prob(True, k, 1.0) * 100, 1)
        m[f"fwd_p_cov_ge25_{tag}_pct"] = round(prob(True, k, 0.25) * 100, 1)
        m[f"fwd_p_cov_ge100_{tag}_no_hsp029_pct"] = round(prob(False, k, 1.0) * 100, 1)
        m[f"fwd_cov_{tag}_p50_no_hsp029_pct"] = round(_pct(srt[False][k], 50) * 100, 1)
        for s in TAKE_SENS:   # coverage is proportional to the take rate: P(cov * s >= 1) = P(cov >= 1 / s)
            m[f"fwd_p_cov_ge100_{tag}_take_x{str(s).replace('.', '_')}_pct"] = round(prob(True, k, 1.0 / s) * 100, 1)
    for tag in ("2027", "2031"):
        k = CHECKPOINTS[tag]
        m[f"fwd_cov_{tag}_p50_price_drift_pct"] = round(_pct(drift[True][k], 50) * 100, 1)
        m[f"fwd_p_cov_ge100_{tag}_price_drift_pct"] = round(sum(1 for x in drift[True][k] if x >= 1.0) / N_PATHS * 100, 1)
    m["fwd_p3_line_pct"] = 25             # PREREG.md, P3: the line it sets
    m["fwd_full_line_pct"] = 100           # revenue equal to the USD value of net new supply, the rating rule's G_req target
    m["fwd_p3_frozen_prob_pct"] = 35.0      # PREREG.md, P3: 0.35 (90-day captured revenue / USD value of net new supply >= 25% at 2027-11-04)

    fan = [{"k": k, "date": edges[k].isoformat(), **{f"p{q}": round(_pct(srt[True][k], q) * 100, 2) for q in PCTS}}
           for k in range(MONTHS + 1)]
    sup = [{"k": k, "date": edges[k].isoformat(), "hsp029_m": round(paths[True][edges[k]] / 1e6, 2),
            "no_hsp029_m": round(paths[False][edges[k]] / 1e6, 2)} for k in range(0, MONTHS + 1, 3)]
    m["fwd_supply_2031_m"] = sup[-1]["hsp029_m"]
    m["fwd_supply_2031_no_hsp029_m"] = sup[-1]["no_hsp029_m"]
    m["fwd_supply_now_m"] = sup[0]["hsp029_m"]
    m["fwd_supply_growth_5y_pct"] = round((sup[-1]["hsp029_m"] / sup[0]["hsp029_m"] - 1) * 100, 1)
    m["fwd_supply_growth_5y_no_hsp029_pct"] = round((sup[-1]["no_hsp029_m"] / sup[0]["no_hsp029_m"] - 1) * 100, 1)
    return {"fwd_fan": fan, "fwd_supply": sup}
