"""The update to 2026-11-13 (exploratory, chosen 2026-11-14, after F1-F4 were scored).

The analysis stops at 2026-11-04, the pre-registered cutoff, and none of its metrics moves. This module reads the keyless series
fetched again on 2026-11-14 (pipeline/fetch_update.py, data/raw/update/) up to the last full UTC day before the score, 2026-11-13,
and writes upd_* metrics beside the committed ones: the market, Intents' revenue, take and share of the peer set, supply, the
measured coverage of dilution (P3's quantity), and the whole investment case (pipeline/investment_case.py run again on the
new series, its keys prefixed upd_). The pre-registered tests, the ladder and the 1Click charts stay at 2026-11-04: their inputs
need a BigQuery scan or the Explorer API key.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from .common import RAW, YOCTO, add_days, day, read_raw
from .compute import PEERS, llama_daily, r, window_sum

END = "2026-11-13"            # the last full UTC day before the score
TARGET = date(2031, 11, 4)    # the horizon of the rating rule and the investment case
DIR = "update"


def available() -> bool:
    return (RAW / DIR / "llama" / "dailyRevenue_near-intents.json").exists()


def _cut(series: dict[str, float]) -> dict[str, float]:
    return {k: v for k, v in series.items() if k <= END}


def update(m: dict) -> None:
    vol = {s: _cut(llama_daily(f"{DIR}/llama/volume_{s}.json")) for s in PEERS}
    fees = {s: _cut(llama_daily(f"{DIR}/llama/fees_{s}.json")) for s in PEERS}
    rev = _cut(llama_daily(f"{DIR}/llama/dailyRevenue_near-intents.json"))
    nb = {row["date"][:10]: row for row in read_raw(f"{DIR}/nearblocks/charts.json")["charts"]}
    supply = _cut({k: int(v["total_supply"]) / YOCTO for k, v in nb.items() if v.get("total_supply")})
    cg = read_raw(f"{DIR}/coingecko/near_market_chart_365d.json")
    price = _cut({day(ms / 1000): float(p) for ms, p in cg["prices"]})          # last point of each UTC day wins, as in compute.py
    caps = _cut({day(ms / 1000): float(c) for ms, c in cg["market_caps"]})
    asof = min(max(vol["near-intents"]), max(rev), max(supply), max(price), max(caps), END)
    m["upd_asof"] = asof
    m["upd_price_usd"] = r(price[asof], 3)
    m["upd_mcap_usd_b"] = r(caps[asof] / 1e9, 2)

    v30 = window_sum(vol["near-intents"], asof, 30)
    rv30 = window_sum(rev, asof, 30)
    tot30 = sum(window_sum(vol[s], asof, 30) for s in PEERS)
    tot365 = sum(window_sum(vol[s], asof, 365) for s in PEERS)
    m["upd_intents_vol_30d_b"] = r(v30 / 1e9)
    m["upd_intents_rev_30d_m"] = r(rv30 / 1e6)
    m["upd_take_captured_bp_30d"] = r(rv30 / v30 * 1e4)
    m["upd_intents_share_peerset_30d_pct"] = r(v30 / tot30 * 100, 1)
    m["upd_intents_share_peerset_365d_pct"] = r(window_sum(vol["near-intents"], asof, 365) / tot365 * 100, 1)
    m["upd_thorchain_share_peerset_30d_pct"] = r(window_sum(vol["thorchain-dex"], asof, 30) / tot30 * 100, 1)
    m["upd_thorchain_volume_30d_b"] = r(window_sum(vol["thorchain-dex"], asof, 30) / 1e9)
    d30 = supply[asof] - supply[add_days(asof, -30)]
    d365 = supply[asof] - supply[add_days(asof, -365)]
    m["upd_net_issuance_near_per_day_30d_k"] = r(d30 / 30 / 1e3, 1)
    m["upd_net_supply_growth_365d_pct"] = r(d365 / supply[add_days(asof, -365)] * 100, 2)

    # the measured coverage of dilution at the as-of date: P3's quantity, priced daily, as pipeline/investment_case.py computes it
    dil, days = 0.0, 0
    for i in range(90):
        k, prev = add_days(asof, -i), add_days(asof, -i - 1)
        if k in supply and prev in supply and k in price:
            dil += (supply[k] - supply[prev]) * price[k]
            days += 1
    p3 = window_sum(rev, asof, 90) / dil if days == 90 and dil > 0 else None
    m["upd_p3_quantity_90d_pct"] = r(p3 * 100, 1) if p3 is not None else None

    # the investment case again, on the new series: same code, as-of date, horizon, price and market cap from the update
    from .investment_case import investment_case
    scratch = dict(m)
    scratch["p3_quantity_90d_asof_pct"] = m["upd_p3_quantity_90d_pct"]
    scratch["intents_share_peerset_365d_pct"] = m["upd_intents_share_peerset_365d_pct"]
    t_ms = datetime(*date.fromisoformat(asof).timetuple()[:3], 23, tzinfo=timezone.utc).timestamp() * 1000
    investment_case(scratch, rev, vol, fees, supply, price,
                    ov={"asof": asof, "n_years": (TARGET - date.fromisoformat(asof)).days / 365.25, "p0": price[asof],
                        "mcap0": caps[asof], "caps": f"{DIR}/coingecko/peer_caps_30d.json", "t_ms": t_ms})
    for k, v in scratch.items():
        if k.startswith("ic_"):
            m["upd_" + k] = v
    m["upd_ic_years_n"] = r(m["upd_ic_years_n"], 2)
