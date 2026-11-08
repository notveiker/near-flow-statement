"""PREREG H1a exactly as written, the 7.1M endpoint residual, and the rating-rule inputs. Offline, stdlib only.

Call order in compute.build(): h1a(m) after the staking-pool block (h1b reads m["h1a_gross_issuance_90d_m"]),
rating(m) after h1b(m) (it reads m["h1b_verdict"]).

Inputs (data/raw/):
  rpc/epoch_issuance.json           epoch-start and predecessor headers (pipeline/fetch_issuance.py)
  rpc/pool_endpoints_archival.json  per-pool archival totals at blocks 210,238,033 / 223,088,015 + residual checks
  rpc/rating_assumptions.json       frozen rating constants (HSP-029 ramp, activation, price) with sources
  bq/staking_flows_daily.json, bq/staking_pool_totals_endpoints.json   (the repo's existing H1a queries)
  llama/dailyRevenue_near-intents.json, coingecko/near_market_chart_365d.json

H1a (PREREG.md): pass if net staking outflow < 50% of staking rewards; staking rewards = 90% of gross issuance;
gross measured from epoch-boundary block headers. mint(s) = supply(s) - supply(prev(s)) + burnt(s) at each epoch
start s; gross = sum over starts in blocks 210,238,034..223,088,015; burn = gross - net (exact, by the identity).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from .common import RAW, read_raw

YOCTO = 10**24
W_FIRST, W_LAST = 210_238_034, 223_088_015
B0, B1 = "210238033", "223088015"

# Fixed in PREREG.md (frozen). tests/test_prereg_spec.py compares each with the frozen text.
H1A_PASS_BELOW_X = 0.5      # H1a: net staking outflow < 50% of staking rewards (strict)
STAKING_REWARD_SHARE = 0.9  # staking rewards = 90% of gross issuance
AVOID_DIVISOR = 2           # rating rule: Avoid if G_obs < G_req / 2 (strict); Buy if G_obs >= G_req


def _epochs() -> tuple[dict, list[dict]]:
    d = read_raw("rpc/epoch_issuance.json")
    f = d["epoch_fields"]
    rows = sorted((dict(zip(f, r)) for r in d["epochs"]), key=lambda x: x["start_height"])
    return d, rows


def issuance() -> dict:
    """Gross, net, burn over the window; realised cap share; post-v87 burn/day. NEAR floats."""
    d, rows = _epochs()
    p = d["protocol"]
    cap = p["max_inflation_rate"][0] / p["max_inflation_rate"][1]
    inw = [r for r in rows if W_FIRST <= r["start_height"] <= W_LAST]
    gross = sum(int(r["mint"]) for r in inw)
    net = int(d["endpoints"][B1]["total_supply"]) - int(d["endpoints"][B0]["total_supply"])
    shares, v87_burn, v87_secs = [], 0, 0.0
    for a, b in zip(rows, rows[1:]):
        dur = (b["start_timestamp_ns"] - a["start_timestamp_ns"]) / 1e9
        if W_FIRST <= b["start_height"] <= W_LAST:  # b's mint pays for epoch a
            shares.append(int(b["mint"]) / (cap * int(b["prev_total_supply"]) * dur / p["num_seconds_per_year"]))
        if a["start_height"] >= p["v87_first_epoch_start"]:  # whole epoch a burn
            v87_burn += int(a["start_total_supply"]) - int(b["prev_total_supply"]) + int(a["start_burnt"])
            v87_secs += dur
    return {"gross": gross / YOCTO, "net": net / YOCTO, "burn": (gross - net) / YOCTO, "n_epochs": len(inw),
            "supply_end": int(d["endpoints"][B1]["total_supply"]) / YOCTO,
            "cap_share": sum(shares) / len(shares), "burn_per_day_v87": v87_burn / YOCTO / (v87_secs / 86400)}


def h1a_passes(rewards: float, *net_outflows: float) -> bool:
    """H1a as written: every measure of net staking outflow is below 50% of staking rewards (strictly)."""
    return all(out < H1A_PASS_BELOW_X * rewards for out in net_outflows)


def h1a(m: dict) -> None:
    if not (RAW / "rpc" / "epoch_issuance.json").exists():
        return
    iss = issuance()
    rows = read_raw("bq/staking_flows_daily.json")
    tot = {k: sum(float(x[k]) for x in rows) for k in ("rewards_near", "gas_rebate_near", "inflow_near", "outflow_near")}
    net_out = tot["outflow_near"] - tot["inflow_near"]
    rewards = STAKING_REWARD_SHARE * iss["gross"]
    m["h1a_gross_issuance_90d_m"] = round(iss["gross"] / 1e6, 4)
    m["h1a_net_supply_change_90d_m"] = round(iss["net"] / 1e6, 4)
    m["h1a_burn_90d_k"] = round(iss["burn"] / 1e3, 2)
    m["h1a_epochs_in_window"] = iss["n_epochs"]
    m["h1a_staking_rewards_90d_m"] = round(rewards / 1e6, 4)
    m["h1a_ratio_as_written_x"] = round(net_out / rewards, 2)
    m["h1a_pass_as_written"] = h1a_passes(rewards, net_out)

    if not (RAW / "rpc" / "pool_endpoints_archival.json").exists():
        return
    pe = read_raw("rpc/pool_endpoints_archival.json")
    t0 = sum(int(v[0]) for v in pe["pools"].values()) / YOCTO
    t1 = sum(int(v[1]) for v in pe["pools"].values()) / YOCTO
    endpoint_out = tot["rewards_near"] - (t1 - t0)  # net outflow = rewards credited - change in pool balances
    m["h1a_ratio_endpoint_archival_x"] = round(endpoint_out / rewards, 2)
    m["h1a_pass_as_written"] = h1a_passes(rewards, net_out, endpoint_out)
    lst = pe["lst_pool"]
    lst_flow = lst["native_in_near"] - lst["native_out_near"]
    m["h1a_ratio_with_lst_pool_x"] = round((net_out - lst_flow) / rewards, 2)

    # Residual between the repo's endpoint query and the flows (PREREG-ADDENDUM 2026-11-05: 7.1M).
    ends = {x["block_date"]: float(x["pool_total_near"]) for x in read_raw("bq/staking_pool_totals_endpoints.json")}
    flow_delta = tot["rewards_near"] + tot["gas_rebate_near"] + tot["inflow_near"] - tot["outflow_near"]
    fc = pe["flipside_check"]
    flip = [(int(a) + int(b)) / YOCTO for a, b in fc["amount_locked"]]
    # flipside.pool.near had no balance change on 08-06, so the repo's 08-06 total (pools with a change that day)
    # omits it; the flows count its 7.1M in-window withdrawal.
    m["h1a_residual_repo_m"] = round(((ends["2026-11-04"] - ends["2026-08-06"]) - flow_delta) / 1e6, 2)
    m["h1a_residual_flipside_m"] = round(flip[1] / 1e6, 2) if flip[0] == flip[1] else 0.0
    m["h1a_residual_left_k"] = round(((t1 - t0) - flow_delta) / 1e3, 1)  # archival state vs flows


def _llama(rel: str) -> dict[str, float]:
    return {datetime.fromtimestamp(t, tz=timezone.utc).date().isoformat(): float(v)
            for t, v in read_raw(rel)["totalDataChart"]}


def _span(lo: date, n: int) -> list[str]:
    return [(lo + timedelta(days=i)).isoformat() for i in range(n)]


def _cap(d: date, act: date | None, a: dict) -> float:
    if act is None or d < act:
        return a["start_cap"]
    months = (d - act).days / (365.25 / 12)
    return a["start_cap"] - (a["start_cap"] - a["target_cap"]) * min(months, a["ramp_months"]) / a["ramp_months"]


def g_req(ra: dict, iss: dict, r90: float, hsp029: bool = True) -> float:
    """Annual growth so that captured revenue in the 90 days to target_date = USD value of net new supply in the
    same 90 days. Supply simulated daily from the window-end header: + cap(t) * cap_share * S / 365 - burn/day."""
    asof, target = date.fromisoformat(ra["asof"]), date.fromisoformat(ra["target_date"])
    act = date.fromisoformat(ra["hsp029"]["activation_date"]) if hsp029 else None
    s, d, path = iss["supply_end"], asof, {}
    while d < target:
        d += timedelta(days=1)
        s += _cap(d, act, ra["hsp029"]) * iss["cap_share"] * s / 365 - iss["burn_per_day_v87"]
        path[d] = s
    n90 = path[target] - path[target - timedelta(days=90)]
    return (n90 * ra["price_usd"] / r90) ** (1 / ra["horizon_years"]) - 1


def rating_rule(h1b: str, go: float, gr: float) -> str:
    """PREREG: Buy if G_obs >= G_req and H1b passes; Avoid if G_obs < G_req/2 and H1b fails; Hold otherwise.

    `h1b` is the H1b verdict text ("pass", "fail", "inconclusive ...", "pending"); only a leading "pass" or "fail"
    counts, so an inconclusive or pending H1b always gives Hold."""
    if h1b.startswith("pass") and go >= gr:
        return "Buy"
    if h1b.startswith("fail") and go < gr / AVOID_DIVISOR:
        return "Avoid"
    return "Hold"


def rating(m: dict) -> None:
    if not (RAW / "rpc" / "rating_assumptions.json").exists() or not (RAW / "rpc" / "epoch_issuance.json").exists():
        return
    ra = read_raw("rpc/rating_assumptions.json")
    iss = issuance()
    rev = _llama(ra["revenue_series"].split(" ")[0])
    asof = date.fromisoformat(ra["asof"])
    w90 = _span(asof - timedelta(days=ra["r90_days"] - 1), ra["r90_days"])
    n = ra["g_obs_days"]
    wa = _span(asof - timedelta(days=n - 1), n)
    wb = _span(asof - timedelta(days=2 * n - 1), n)
    if any(k not in rev for k in w90 + wa + wb):
        m["rating_output"] = "not computable (revenue days missing)"
        return
    r90 = sum(rev[k] for k in w90)
    gr = g_req(ra, iss, r90)
    go = (sum(rev[k] for k in wa) / sum(rev[k] for k in wb)) ** (365 / n) - 1
    m["rating_r90_usd_m"] = round(r90 / 1e6, 2)
    m["rating_g_req_pct"] = round(gr * 100, 1)
    m["rating_g_req_no_hsp029_pct"] = round(g_req(ra, iss, r90, hsp029=False) * 100, 1)
    m["rating_g_obs_pct"] = round(go * 100, 1)
    px = {datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat(): float(p)
          for ms, p in read_raw("coingecko/near_market_chart_365d.json")["prices"]}
    if all(k in px for k in wa + wb):  # sensitivity only: same windows in NEAR terms
        ga = sum(rev[k] / px[k] for k in wa) / sum(rev[k] / px[k] for k in wb)
        m["rating_g_obs_near_pct"] = round((ga ** (365 / n) - 1) * 100, 1)

    v = str(m.get("h1b_verdict", "pending"))
    m["rating_if_h1b_pass"], m["rating_if_h1b_fail"] = rating_rule("pass", go, gr), rating_rule("fail", go, gr)
    m["rating_output"] = rating_rule(v, go, gr) if not v.startswith("pending") else "pending (H1b not scored)"
