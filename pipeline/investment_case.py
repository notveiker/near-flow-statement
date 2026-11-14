"""The investment case (exploratory, chosen 2026-11-14, after the freeze): what NEAR's price assumes, what the evidence supports,
the scenarios between them, and the signposts that would tell them apart.

Every input is committed data or a stated assumption; nothing here feeds H1a, H1b, H1c, the forward tests or the rating rule.

  1. What the price assumes (a reverse DCF). For NEAR's market cap today to earn a required return r a year to 2031-11-04, and
     then be worth X times its captured revenue, captured revenue must reach  M0 x (1 + r)^N x (S_N / S_0) / X  by then. S_N / S_0
     is the supply growth on the rating rule's own path (with HSP-029): buybacks burn nothing, so a holder's share of supply
     shrinks by that factor and the market cap has to grow faster to make up for it. r and X are assumptions (R_GRID, X_GRID),
     not estimates; the peer table shows what the market pays per dollar of fees for THORChain and Chainflip today.
  2. What has to multiply. Captured revenue = cross-chain swap volume (the peer set) x Intents' share x NEAR's take rate. The
     required multiple is split into the market's growth at its last-year pace, the share at its 12-month high, and the take
     rate the rest would need, against the gross fee Intents charges today.
  3. Scenarios. Bear, base and bull values for each factor, each one a number in the data (ANCHORS below), run against the
     rule's supply path at the rule's constant price: coverage (captured revenue / USD value of net new supply, P3's quantity)
     on 2031-11-04.
  4. Sensitivity. The base coverage with one factor at a time moved to its bear and bull value, and the price to its 365-day
     low and high.
  5. Peer valuation. Market cap / fees for NEAR (on Intents' gross fees and on captured revenue), THORChain and Chainflip.
  6. Staking float. NEAR in staking pools at the two ends of H1a's window, against total supply.
  7. Measured coverage history (P3's quantity, priced daily) and the signposts.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from .common import YOCTO, add_days, read_raw
from .model import supply_path

R_GRID = (10, 15, 20)          # required annual return, %: an assumption, not an estimate
X_GRID = (10, 25, 50)          # market cap / annual captured revenue in 2031: an assumption (peers trade at or below the low end today)
BASE_R, BASE_X = 15, 25
P1_LINE_PCT, P2_LINE_USD, P3_LINE_PCT = 55, 6.0e6, 25   # PREREG.md: P1 (share, 365 days), P2 (captured revenue, 90 days), P3 (coverage)
PEERS = ("near-intents", "thorchain-dex", "chainflip-amm", "maya-protocol")   # the peer set, as pipeline.compute
SHARE_MONTHS = ("2025-11", "2026-10")      # the last 12 full months
TAKE_MONTHS = ("2026-03", "2026-10")       # the full months after the fee switch (2026-02-23)
HIST_STEP_DAYS = 7
# Which number in the data each scenario takes (THESIS.md section 6.3; chosen after the annual volumes were computed, see the
# 2026-11-14 entry of PREREG-ADDENDUM.md):
ANCHORS = {
    "bear": {"g": "cagr_2y", "share": "share_min", "take": "take_min", "hsp": False},
    "base": {"g": "cagr_1y", "share": "share_90d", "take": "take_90d", "hsp": True},
    "bull": {"g": "cagr_4y", "share": "share_max", "take": "take_max", "hsp": True},
}


def _r(x: float, n: int = 1) -> float:
    return round(x, n)


def _wsum(series: dict[str, float], end: str, days: int) -> float:
    return sum(series.get(add_days(end, -i), 0.0) for i in range(days))


def _month_sums(series: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for d, v in series.items():
        out[d[:7]] = out.get(d[:7], 0.0) + v
    return out


def investment_case(m: dict, rev: dict[str, float], vol: dict[str, dict[str, float]], fees: dict[str, dict[str, float]],
                    supply: dict[str, float], price: dict[str, float], ov: dict | None = None) -> dict:
    """Write the ic_* metrics into m; return the chart series {"cov_hist": [...]}.

    ov, for the update to 2026-11-13 (pipeline/update.py), replaces the as-of date, the horizon, the price and market cap at the
    as-of date, the time the peers' market caps are read at and the file they are read from. Everything else is the same code."""
    ra = read_raw("rpc/rating_assumptions.json")
    asof = ra["asof"]
    a0 = date.fromisoformat(asof)
    target = date.fromisoformat(ra["target_date"])
    n_years = float(ra["horizon_years"])
    p0 = float(ra["price_usd"])
    snap = read_raw("coingecko/near_snapshot.json")
    mcap0 = float(snap["market_cap_usd"])
    if ov:
        asof, n_years, p0, mcap0 = ov["asof"], ov["n_years"], ov["p0"], ov["mcap0"]
        a0 = date.fromisoformat(asof)

    # ---------- today ----------
    r90 = _wsum(rev, asof, 90)
    v90 = _wsum(vol["near-intents"], asof, 90)
    mkt90 = sum(_wsum(vol[s], asof, 90) for s in PEERS)
    f90 = _wsum(fees["near-intents"], asof, 90)
    share90, take90 = v90 / mkt90, r90 / v90
    rev_ann0 = r90 * 365 / 90
    m["ic_rev_90d_ann_m"] = _r(rev_ann0 / 1e6, 1)
    m["ic_market_90d_b"] = _r(mkt90 / 1e9, 2)
    m["ic_share_90d_pct"] = _r(share90 * 100, 1)
    m["ic_take_90d_bp"] = _r(take90 * 1e4, 2)
    m["ic_gross_bp_90d"] = _r(f90 / v90 * 1e4, 1)

    paths = {h: supply_path(a0, target, h) for h in (True, False)}
    s0, sN = paths[True][a0], paths[True][target]
    dil90 = {h: (paths[h][target] - paths[h][target - timedelta(days=90)]) * p0 for h in paths}
    m["ic_supply_factor_x"] = _r(sN / s0, 3)

    # ---------- 1. what the price assumes ----------
    for rr in R_GRID:
        for xx in X_GRID:
            need = mcap0 * (1 + rr / 100) ** n_years * (sN / s0) / xx
            m[f"ic_implied_cagr_r{rr}_x{xx}_pct"] = _r(((need / rev_ann0) ** (1 / n_years) - 1) * 100, 1)
    need_base = mcap0 * (1 + BASE_R / 100) ** n_years * (sN / s0) / BASE_X
    k_req = need_base / rev_ann0
    m["ic_required_rev_2031_m"] = _r(need_base / 1e6, 0)
    m["ic_required_multiple_x"] = _r(k_req, 1)
    m["ic_base_r_pct"], m["ic_base_x"] = BASE_R, BASE_X
    for i, rr in enumerate(R_GRID):
        m[f"ic_grid_r{i}_pct"] = rr
    for i, xx in enumerate(X_GRID):
        m[f"ic_grid_x{i}"] = xx
    m["ic_p1_line_pct"], m["ic_p2_line_usd_m"], m["ic_p3_line_pct"] = P1_LINE_PCT, P2_LINE_USD / 1e6, P3_LINE_PCT
    m["ic_years_n"] = n_years

    # ---------- the market: annual peer-set volume, five full years ----------
    years = [_wsum_all(vol, add_days(asof, -365 * k)) for k in range(5)]   # years[0] = the 365 days to the as-of date
    for k, y in enumerate(years):
        m[f"ic_market_y{k}_b"] = _r(y / 1e9, 1)
    cagr = {n: (years[0] / years[n]) ** (1 / n) - 1 for n in (1, 2, 3, 4)}
    for n, g in cagr.items():
        m[f"ic_market_cagr_{n}y_pct"] = _r(g * 100, 1)
    # The same without NEAR Intents (added 2026-11-14 after the review): last year's growth of the set is all Intents'.
    ex = [_wsum_all(vol, add_days(asof, -365 * k), exclude="near-intents") for k in range(5)]
    for n in (1, 2, 4):
        m[f"ic_market_ex_intents_cagr_{n}y_pct"] = _r(((ex[0] / ex[n]) ** (1 / n) - 1) * 100, 1)
    m["ic_intents_vol_1y_x"] = _r(_wsum(vol["near-intents"], asof, 365) / _wsum(vol["near-intents"], add_days(asof, -365), 365), 1)

    # ---------- share and take anchors ----------
    mv = {s: _month_sums(vol[s]) for s in PEERS}
    months = sorted(k for k in mv["near-intents"] if SHARE_MONTHS[0] <= k <= SHARE_MONTHS[1])
    shares = {k: mv["near-intents"][k] / sum(mv[s].get(k, 0.0) for s in PEERS) for k in months}
    mr = _month_sums(rev)
    takes = {k: mr.get(k, 0.0) / mv["near-intents"][k] for k in sorted(mv["near-intents"]) if TAKE_MONTHS[0] <= k <= TAKE_MONTHS[1]}
    smin, smax = min(shares, key=shares.get), max(shares, key=shares.get)
    tmin, tmax = min(takes, key=takes.get), max(takes, key=takes.get)
    anchors = {"cagr_1y": cagr[1], "cagr_2y": cagr[2], "cagr_4y": cagr[4], "share_90d": share90, "share_min": shares[smin],
               "share_max": shares[smax], "take_90d": take90, "take_min": takes[tmin], "take_max": takes[tmax]}
    m["ic_share_min_pct"], m["ic_share_min_month"] = _r(shares[smin] * 100, 1), smin
    m["ic_share_max_pct"], m["ic_share_max_month"] = _r(shares[smax] * 100, 1), smax
    m["ic_take_min_bp"], m["ic_take_min_month"] = _r(takes[tmin] * 1e4, 2), tmin
    m["ic_take_max_bp"], m["ic_take_max_month"] = _r(takes[tmax] * 1e4, 2), tmax

    # ---------- 2. what has to multiply (base r and X) ----------
    f_mkt = (1 + cagr[1]) ** n_years
    f_share = shares[smax] / share90
    f_take = k_req / (f_mkt * f_share)
    m["ic_mult_market_x"] = _r(f_mkt, 2)
    m["ic_mult_share_x"] = _r(f_share, 2)
    m["ic_mult_take_x"] = _r(f_take, 1)
    m["ic_take_needed_bp"] = _r(take90 * f_take * 1e4, 1)
    m["ic_take_needed_vs_gross_x"] = _r(take90 * f_take / (f90 / v90), 1)
    g_full = (k_req / (f_share * (f90 / v90) / take90)) ** (1 / n_years) - 1
    m["ic_market_cagr_needed_full_fee_pct"] = _r(g_full * 100, 1)

    # ---------- 3. scenarios ----------
    def coverage(g: float, share: float, take: float, hsp: bool, px: float = p0) -> float:
        rev_n = mkt90 * (1 + g) ** n_years * share * take
        return rev_n / (dil90[hsp] / p0 * px)

    scn = {}
    for name, a in ANCHORS.items():
        g, sh, tk = anchors[a["g"]], anchors[a["share"]], anchors[a["take"]]
        rev_n = mkt90 * (1 + g) ** n_years * sh * tk * 365 / 90
        cov = coverage(g, sh, tk, a["hsp"])
        scn[name] = cov
        m[f"ic_{name}_market_cagr_pct"] = _r(g * 100, 1)
        m[f"ic_{name}_share_pct"] = _r(sh * 100, 1)
        m[f"ic_{name}_take_bp"] = _r(tk * 1e4, 2)
        m[f"ic_{name}_hsp029"] = "yes" if a["hsp"] else "no"
        m[f"ic_{name}_rev_2031_m"] = _r(rev_n / 1e6, 1)
        m[f"ic_{name}_rev_multiple_x"] = _r(rev_n / rev_ann0, 2)
        m[f"ic_{name}_rev_cagr_pct"] = _r(((rev_n / rev_ann0) ** (1 / n_years) - 1) * 100, 1)
        m[f"ic_{name}_coverage_2031_pct"] = _r(cov * 100, 1)
        m[f"ic_{name}_mcap_to_rev_2031_x"] = _r(mcap0 / rev_n, 1)
        m[f"ic_{name}_vs_required_pct"] = _r(rev_n / need_base * 100, 1)

    # the bull case at the three-year pace instead of the four-year one (the three-year window starts at the 2023 low)
    bull3 = mkt90 * (1 + cagr[3]) ** n_years * shares[smax] * takes[tmax] * 365 / 90
    m["ic_bull3y_rev_multiple_x"] = _r(bull3 / rev_ann0, 1)
    m["ic_bull3y_vs_required_pct"] = _r(bull3 / need_base * 100, 0)

    # ---------- 4. sensitivity of the base coverage ----------
    b = ANCHORS["base"]
    base_args = {"g": anchors[b["g"]], "share": anchors[b["share"]], "take": anchors[b["take"]], "hsp": True}
    pxs = [v for k, v in price.items() if add_days(asof, -364) <= k <= asof]
    m["ic_price_365d_low_usd"], m["ic_price_365d_high_usd"] = _r(min(pxs), 2), _r(max(pxs), 2)
    tor = {
        "market": (coverage(**{**base_args, "g": cagr[2]}), coverage(**{**base_args, "g": cagr[4]})),
        "share": (coverage(**{**base_args, "share": shares[smin]}), coverage(**{**base_args, "share": shares[smax]})),
        "take": (coverage(**{**base_args, "take": takes[tmin]}), coverage(**{**base_args, "take": takes[tmax]})),
        "hsp029": (coverage(**{**base_args, "hsp": False}), coverage(**base_args)),
        "price": (coverage(**base_args, px=max(pxs)), coverage(**base_args, px=min(pxs))),
    }
    for k, (lo, hi) in tor.items():
        m[f"ic_tor_{k}_lo_pct"], m[f"ic_tor_{k}_hi_pct"] = _r(lo * 100, 1), _r(hi * 100, 1)

    # ---------- 5. peer valuation ----------
    caps = read_raw(ov["caps"] if ov else "coingecko/peer_caps_30d.json")
    t_snap = ov["t_ms"] if ov else datetime.fromisoformat(snap["last_updated"].replace("Z", "+00:00")).timestamp() * 1000
    for slug, key in (("thorchain-dex", "thorchain"), ("chainflip-amm", "chainflip")):
        ts, cap = min(caps[slug]["market_caps"], key=lambda p: abs(p[0] - t_snap))
        f365 = _wsum(fees[slug], asof, 365)
        m[f"ic_peer_{key}_mcap_m"] = _r(cap / 1e6, 1)
        m[f"ic_peer_{key}_fees_365d_m"] = _r(f365 / 1e6, 2)
        m[f"ic_peer_{key}_mcap_to_fees_x"] = _r(cap / f365, 1)
        m["ic_peer_caps_at_utc"] = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
    fi365 = _wsum(fees["near-intents"], asof, 365)
    m["ic_near_intents_fees_365d_m"] = _r(fi365 / 1e6, 2)
    m["ic_near_mcap_to_intents_fees_x"] = _r(mcap0 / fi365, 1)
    m["ic_near_mcap_to_rev_90d_ann_x"] = _r(mcap0 / rev_ann0, 0)

    # ---------- 6. staking float (H1a's window ends) ----------
    pe = read_raw("rpc/pool_endpoints_archival.json")
    ei = read_raw("rpc/epoch_issuance.json")
    b0, b1 = (str(x) for x in pe["blocks"])
    st0 = sum(int(v[0]) for v in pe["pools"].values()) / YOCTO
    st1 = sum(int(v[1]) for v in pe["pools"].values()) / YOCTO
    ts0, ts1 = (int(ei["endpoints"][k]["total_supply"]) / YOCTO for k in (b0, b1))
    m["ic_staked_start_m"], m["ic_staked_end_m"] = _r(st0 / 1e6, 1), _r(st1 / 1e6, 1)
    m["ic_staked_share_start_pct"], m["ic_staked_share_end_pct"] = _r(st0 / ts0 * 100, 1), _r(st1 / ts1 * 100, 1)
    m["ic_float_change_90d_m"] = _r(((ts1 - st1) - (ts0 - st0)) / 1e6, 1)
    m["ic_float_change_vs_net_supply_x"] = _r(((ts1 - st1) - (ts0 - st0)) / (ts1 - ts0), 1)

    # ---------- 7. measured coverage (P3's quantity, priced daily) and the signposts ----------
    def p3(end: str) -> float | None:
        dil, days = 0.0, 0
        for i in range(90):
            k, prev = add_days(end, -i), add_days(end, -i - 1)
            if k in supply and prev in supply and k in price:
                dil += (supply[k] - supply[prev]) * price[k]
                days += 1
        return _wsum(rev, end, 90) / dil if days == 90 and dil > 0 else None

    hist = []
    d = a0
    while True:
        v = p3(d.isoformat())
        if v is None:
            break
        hist.append({"date": d.isoformat(), "cov_pct": _r(v * 100, 2)})
        d -= timedelta(days=HIST_STEP_DAYS)
    hist.reverse()
    m["ic_cov_hist_first_date"], m["ic_cov_hist_first_pct"] = hist[0]["date"], _r(hist[0]["cov_pct"], 1)
    m["ic_cov_hist_points_n"] = len(hist)

    # signposts: how far today's value is from the line that would favour the upside (100% = at the line)
    m["ic_sp_coverage_pct"] = _r(m["p3_quantity_90d_asof_pct"] / P3_LINE_PCT * 100, 0)                          # P3, M1: 25% on 2027-11-04
    m["ic_sp_revenue_pct"] = _r(r90 / P2_LINE_USD * 100, 0)                                                   # P2: $6.0M in 90 days by 2027-05-04
    m["ic_sp_share_pct"] = _r(m["intents_share_peerset_365d_pct"] / P1_LINE_PCT * 100, 0)                       # P1: 55% over 365 days on 2027-05-04
    m["ic_sp_market_pct"] = _r(m["ic_market_cagr_1y_pct"] / m["rating_g_req_pct"] * 100, 0)          # market growth against G_req
    m["ic_sp_take_pct"] = _r(m["ic_take_90d_bp"] / m["ic_take_needed_bp"] * 100, 0)                   # take rate against what the price needs
    m["ic_sp_staking_pct"] = _r(0.5 / m["h1a_ratio_as_written_x"] * 100, 0)                            # H1a's pass line (0.5x) against today's ratio
    return {"cov_hist": hist}


def _wsum_all(vol: dict[str, dict[str, float]], end: str, exclude: str = "") -> float:
    return sum(_wsum(vol[s], end, 365) for s in PEERS if s != exclude)
