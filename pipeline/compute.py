"""Compute every published number from data/raw/ (offline) into data/metrics.json and data/series.json.

Nothing here touches the network. Each metric records the inputs it came from in METRIC_SOURCES,
which the dashboard prints under each chart.

Run: python3 -m pipeline.compute
"""
from __future__ import annotations

import json
from collections import defaultdict

from .common import DATA, METRICS, YOCTO, add_days, day, read_raw

FEE_SWITCH = "2026-02-23"  # NEAR Intents fee switch / buyback start (DefiLlama methodology)
PEERS = ["near-intents", "thorchain-dex", "chainflip-amm", "maya-protocol"]
PEER_LABEL = {"near-intents": "NEAR Intents", "thorchain-dex": "THORChain",
              "chainflip-amm": "Chainflip", "maya-protocol": "Maya"}


def llama_daily(rel: str) -> dict[str, float]:
    d = read_raw(rel)
    return {day(t): float(v) for t, v in (d.get("totalDataChart") or [])}


def window_sum(series: dict[str, float], end: str, days: int) -> float:
    start = add_days(end, -days + 1)
    return sum(v for k, v in series.items() if start <= k <= end)


def monthly(series: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for k, v in series.items():
        out[k[:7]] += v
    return dict(sorted(out.items()))


def r(x: float, n: int = 2) -> float:
    return round(x, n)


def build() -> tuple[dict, dict]:
    # ---------- inputs ----------
    vol = {s: llama_daily(f"llama/volume_{s}.json") for s in PEERS}
    fees = {s: llama_daily(f"llama/fees_{s}.json") for s in PEERS}
    rev = llama_daily("llama/dailyRevenue_near-intents.json")
    hold = llama_daily("llama/dailyHoldersRevenue_near-intents.json")
    chainfees = llama_daily("llama/chainfees_near.json")

    nb_rows = sorted(read_raw("nearblocks/charts.json")["charts"], key=lambda x: x["date"])
    nb = {row["date"][:10]: row for row in nb_rows}
    supply = {k: int(v["total_supply"]) / YOCTO for k, v in nb.items() if v.get("total_supply")}

    cg = read_raw("coingecko/near_market_chart_365d.json")
    price: dict[str, float] = {}
    for ms, p in cg["prices"]:
        price[day(ms / 1000)] = float(p)  # last point of each UTC day wins
    snap = read_raw("coingecko/near_snapshot.json")
    blk = read_raw("rpc/final_block.json")
    cfg = read_raw("rpc/protocol_config.json")
    vals = read_raw("rpc/validators.json")
    wal = read_raw("rpc/wallets.json")["accounts"]

    # As-of date: the last day present in every daily series we combine.
    asof = min(max(vol["near-intents"]), max(rev), max(supply), max(price), max(chainfees))
    m: dict = {"asof": asof}

    # ---------- market ----------
    total_supply = int(blk["total_supply"]) / YOCTO
    m["price_usd"] = r(snap["price_usd"], 3)
    m["mcap_usd_b"] = r(snap["market_cap_usd"] / 1e9, 2)
    m["total_supply_m"] = r(total_supply / 1e6, 2)
    m["rpc_block"] = blk["height"]

    # ---------- NEAR Intents ----------
    v = vol["near-intents"]
    m["intents_vol_30d_b"] = r(window_sum(v, asof, 30) / 1e9)
    m["intents_vol_prior30d_b"] = r(window_sum(v, add_days(asof, -30), 30) / 1e9)
    m["intents_vol_90d_b"] = r(window_sum(v, asof, 90) / 1e9)
    m["intents_vol_365d_b"] = r(window_sum(v, asof, 365) / 1e9, 1)
    m["intents_vol_30d_per_day_m"] = r(window_sum(v, asof, 30) / 30 / 1e6, 1)
    f30 = window_sum(fees["near-intents"], asof, 30)
    rv30 = window_sum(rev, asof, 30)
    h30 = window_sum(hold, asof, 30)
    v30 = window_sum(v, asof, 30)
    m["intents_fees_30d_m"] = r(f30 / 1e6)
    m["intents_rev_30d_m"] = r(rv30 / 1e6)
    m["intents_holdersrev_30d_m"] = r(h30 / 1e6)
    m["intents_rev_365d_m"] = r(window_sum(rev, asof, 365) / 1e6)
    m["take_gross_bp_30d"] = r(f30 / v30 * 1e4, 1)
    m["take_captured_bp_30d"] = r(rv30 / v30 * 1e4, 2)
    m["capture_share_30d_pct"] = r(rv30 / f30 * 100, 1)

    # ---------- L1 ----------
    m["l1_fees_30d_k"] = r(window_sum(chainfees, asof, 30) / 1e3, 1)
    m["l1_fees_365d_m"] = r(window_sum(chainfees, asof, 365) / 1e6, 2)
    m["intents_rev_vs_l1fees_30d_x"] = r(rv30 / window_sum(chainfees, asof, 30), 1)
    num, den = cfg["burnt_gas_reward"]
    m["gas_burn_share_pct"] = r((1 - num / den) * 100, 0)
    m["protocol_version"] = cfg["protocol_version"]
    mi_num, mi_den = cfg["max_inflation_rate"]
    m["max_inflation_pct"] = r(mi_num / mi_den * 100, 2)

    def nb_avg(key: str, end: str, days: int) -> float:
        start = add_days(end, -days + 1)
        xs = [float(nb[k][key]) for k in nb if start <= k <= end and nb[k].get(key) not in (None, "")]
        return sum(xs) / len(xs)

    nb_end = min(asof, max(nb))
    m["tx_per_day_30d_k"] = r(nb_avg("txns", nb_end, 30) / 1e3, 0)
    m["tx_per_day_30d_yoy_pct"] = r((nb_avg("txns", nb_end, 30) / nb_avg("txns", add_days(nb_end, -365), 30) - 1) * 100, 1)
    m["active_accounts_30d_k"] = r(nb_avg("active_accounts", nb_end, 30) / 1e3, 1)
    m["active_accounts_30d_yoy_pct"] = r((nb_avg("active_accounts", nb_end, 30) / nb_avg("active_accounts", add_days(nb_end, -365), 30) - 1) * 100, 1)

    # ---------- supply / issuance (net of burn, from daily total supply) ----------
    def supply_delta(end: str, days: int) -> float:
        return supply[end] - supply[add_days(end, -days)]

    d30 = supply_delta(asof, 30)
    d365 = supply_delta(asof, 365)
    m["net_issuance_near_per_day_30d_k"] = r(d30 / 30 / 1e3, 1)
    m["net_supply_growth_365d_pct"] = r(d365 / supply[add_days(asof, -365)] * 100, 2)
    m["net_supply_growth_30d_annualized_pct"] = r(d30 / supply[add_days(asof, -30)] * 365 / 30 * 100, 2)

    # USD value of net new supply, priced daily.
    def issuance_usd(end: str, days: int) -> float:
        tot = 0.0
        for i in range(days):
            k = add_days(end, -i)
            prev = add_days(k, -1)
            if k in supply and prev in supply and k in price:
                tot += (supply[k] - supply[prev]) * price[k]
        return tot

    iu30 = issuance_usd(asof, 30)
    m["net_issuance_usd_30d_m"] = r(iu30 / 1e6)
    m["coverage_rev_usd_30d_pct"] = r(rv30 / iu30 * 100, 1)
    rev_near_30 = sum(rev.get(add_days(asof, -i), 0) / price[add_days(asof, -i)] for i in range(30)
                      if add_days(asof, -i) in price)
    m["coverage_rev_near_30d_pct"] = r(rev_near_30 / d30 * 100, 1)
    m["breakeven_rev_multiple_30d_x"] = r(iu30 / rv30, 1)

    # ---------- buybacks: label vs wallet ----------
    implied = sum(vv / price[k] for k, vv in hold.items() if k >= FEE_SWITCH and k in price)
    bb = int(wal["buybacks.multisignature.near"]["amount"]) / YOCTO
    m["holdersrev_since_switch_m"] = r(sum(vv for k, vv in hold.items() if k >= FEE_SWITCH) / 1e6)
    m["buyback_implied_near_m"] = r(implied / 1e6, 2)
    m["buyback_wallet_near_m"] = r(bb / 1e6, 3)
    m["buyback_wallet_vs_implied_pct"] = r(bb / implied * 100, 1)
    m["fefunds_wallet_near_m"] = r(int(wal["fefundsadmin.sputnik-dao.near"]["amount"]) / YOCTO / 1e6, 3)
    m["treasury_wallet_near_m"] = r(int(wal["treasury.near"]["amount"]) / YOCTO / 1e6, 3)

    # ---------- staking ----------
    staked = sum(int(s) for _, s in vals["stakes"]) / YOCTO
    m["validators"] = vals["count"]
    m["staked_near_m"] = r(staked / 1e6, 1)
    m["staked_share_pct"] = r(staked / total_supply * 100, 1)
    m["gross_staking_yield_pct"] = r(0.9 * (mi_num / mi_den) / (staked / total_supply) * 100, 2)

    # ---------- peers ----------
    peer_rows = []
    tot30 = sum(window_sum(vol[s], asof, 30) for s in PEERS)
    tot365 = sum(window_sum(vol[s], asof, 365) for s in PEERS)
    for s in PEERS:
        pv30 = window_sum(vol[s], asof, 30)
        pf30 = window_sum(fees[s], asof, 30)
        peer_rows.append({"venue": PEER_LABEL[s], "slug": s, "vol_30d_b": r(pv30 / 1e9),
                          "vol_365d_b": r(window_sum(vol[s], asof, 365) / 1e9, 1),
                          "fees_30d_m": r(pf30 / 1e6), "fee_bp_30d": r(pf30 / pv30 * 1e4, 1) if pv30 else None,
                          "share_30d_pct": r(pv30 / tot30 * 100, 1)})
    m["peers"] = peer_rows
    m["intents_share_peerset_30d_pct"] = r(window_sum(vol["near-intents"], asof, 30) / tot30 * 100, 1)
    m["intents_share_peerset_365d_pct"] = r(window_sum(vol["near-intents"], asof, 365) / tot365 * 100, 1)
    # Net-basis sensitivity: DefiLlama's Intents volume is leg-sum (both sides of a swap).
    net30 = window_sum(vol["near-intents"], asof, 30) / 2
    m["intents_share_peerset_30d_net_pct"] = r(net30 / (tot30 - window_sum(vol["near-intents"], asof, 30) + net30) * 100, 1)

    # ---------- valuation ----------
    mcap = snap["market_cap_usd"]
    m["mcap_to_rev_30d_annualized_x"] = r(mcap / (rv30 * 365 / 30), 0)
    m["mcap_to_rev_365d_x"] = r(mcap / window_sum(rev, asof, 365), 0)

    # ---------- series for charts ----------
    months = sorted(set(monthly(vol["near-intents"])))
    mv = {s: monthly(vol[s]) for s in PEERS}
    mrev, mfee = monthly(rev), monthly(fees["near-intents"])
    series = {
        "intents_monthly": [{"month": mo, "vol_b": r(mv["near-intents"].get(mo, 0) / 1e9),
                             "rev_m": r(mrev.get(mo, 0) / 1e6, 3),
                             "captured_bp": r(mrev.get(mo, 0) / mv["near-intents"][mo] * 1e4, 2) if mv["near-intents"].get(mo) else None,
                             "gross_bp": r(mfee.get(mo, 0) / mv["near-intents"][mo] * 1e4, 1) if mv["near-intents"].get(mo) else None}
                            for mo in months],
        "peer_share_monthly": [{"month": mo, **{s: r(mv[s].get(mo, 0) / max(1e-9, sum(mv[p].get(mo, 0) for p in PEERS)) * 100, 1)
                                                for s in PEERS}} for mo in months],
        "l1_monthly": [{"month": mo, "tx_per_day_k": r(sum(float(nb[k]["txns"]) for k in nb if k.startswith(mo)) /
                                                       max(1, sum(1 for k in nb if k.startswith(mo))) / 1e3, 0)}
                       for mo in sorted({k[:7] for k in nb}) if mo >= "2024-01"],
        "supply_daily": [{"date": k, "supply_m": r(supply[k] / 1e6, 3)} for k in sorted(supply) if k >= "2024-11-01"],
    }
    return m, series


def main() -> int:
    m, series = build()
    METRICS.write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")
    (DATA / "series.json").write_text(json.dumps(series, indent=1, sort_keys=True) + "\n")
    print(f"wrote {METRICS.relative_to(DATA.parent)} ({len(m)} metrics, as of {m['asof']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
