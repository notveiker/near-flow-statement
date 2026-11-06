"""Compute every published number from data/raw/ (offline) into data/metrics.json and data/series.json.

Nothing here touches the network. Each metric records the inputs it came from in METRIC_SOURCES,
which the dashboard prints under each chart.

Run: python3 -m pipeline.compute
"""
from __future__ import annotations

import json
from collections import defaultdict

from .common import DATA, METRICS, RAW, YOCTO, add_days, day, read_raw

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


COLLECTOR_A = "5880ad2b362620fadf759cbceb1cd5737ce8c6ed7fb8e9942881e6731f9247dd"  # explicit buyback appFee
COLLECTOR_B = "143f2bb439575c286f4f585163f0e5fb4e464f8ce57ec06ae80741407d3cfb31"  # quote-improvement share
# Confidential Intents treasury: PRIVATE_TREASURY_ACCOUNT_ID, "a production constant shared by all participants"
# (docs.near-intents.org, Confidential Intents). Unshields (private -> public) release tokens from it.
PRIVATE_TREASURY_ESCROW = "51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe"
USD6 = ("eth-0xdac17f958d2ee523a2206206994597c13d831ec7", "eth-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "tron-d28a265909efecdcee7c5028585214ea0b96f015", "base-0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
        "arb-0xaf88d065e77c8cc2239327c5edb3a432268e5831", "arb-0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9",
        "sol-5ce3bf3a31af18be40ba30f721101b4341690186", "sol-c800a4bd850783ccb82c2b2c7e84175443606352",
        "17208628f84f5d6ad33f0da3bbbeb27ffcb398eac501a31bd6ad2011e36133a1", "usdt.tether-token.near",
        "137_qiStmoQJDQPTebaPjgx5VBxZv6L")
# token -> (CoinGecko id or "usd", decimals). Checked against amountInUsd/amountIn of sampled 1Click swaps.
TOKEN_PRICE = {"nep141:wrap.near": ("near", 24), "nep141:sol.omft.near": ("solana", 9),
               "nep141:eth.omft.near": ("ethereum", 18), "nep141:base.omft.near": ("ethereum", 18),
               "nep141:arb.omft.near": ("ethereum", 18), "nep141:hood.omft.near": ("ethereum", 18),
               "nep141:nbtc.bridge.near": ("bitcoin", 8), "nep141:btc.omft.near": ("bitcoin", 8),
               "nep141:zec.omft.near": ("zcash", 8), "nep141:tron.omft.near": ("tron", 6),
               "nep141:xrp.omft.near": ("ripple", 6), "nep141:ltc.omft.near": ("litecoin", 8),
               "nep245:v2_1.omni.hot.tg:56_2CMMyVTGZkeyNZTSvS5sarzfir6g": ("usd", 18)}


def token_usd(token: str, amount: float, d: str, prices: dict) -> float | None:
    if any(k in token for k in USD6):
        return amount / 1e6
    if token not in TOKEN_PRICE:
        return None
    coin, dec = TOKEN_PRICE[token]
    p = 1.0 if coin == "usd" else prices.get(coin, {}).get(d)
    return None if p is None else amount / 10 ** dec * p


def concentration(m: dict, near_price: dict, lo: str, hi: str) -> None:
    """Partner concentration: which channels NEAR's Intents revenue depends on, and what is traceable."""
    days = [x for x in read_raw("explorer/daily.json")["days"] if lo <= x["date"] <= hi]
    ch: dict = defaultdict(lambda: [0, 0.0, 0.0, 0.0])
    for x in days:
        for k, vals in x["by_channel"].items():
            for i, val in enumerate(vals):
                ch[k][i] += val
    usd = sum(v[1] for v in ch.values())
    bb = sum(v[3] for v in ch.values())
    sk = [v for k, v in ch.items() if k.startswith("swapkit/")]
    m["swapkit_vol_share_pct"] = r(sum(v[1] for v in sk) / usd * 100, 1)
    m["swapkit_partner_fees_usd_k"] = r(sum(v[2] for v in sk) / 1e3, 1)
    m["swapkit_buyback_fees_usd"] = r(sum(v[3] for v in sk), 0)
    m["swapkit_subchannels"] = [{"channel": k, "vol_share_pct": r(v[1] / usd * 100, 1), "partner_fee_bp": r(v[2] / v[1] * 1e4, 1)}
                                for k, v in sorted(ch.items(), key=lambda kv: -kv[1][1]) if k.startswith("swapkit/")][:6]
    ranked = sorted(ch.items(), key=lambda kv: -kv[1][3])
    m["buyback_fee_by_channel"] = [{"channel": k, "share_pct": r(v[3] / bb * 100, 1), "vol_share_pct": r(v[1] / usd * 100, 1),
                                    "buyback_bp": r(v[3] / v[1] * 1e4, 1)} for k, v in ranked[:8]]
    m["buyback_fee_top3_share_pct"] = r(sum(v[3] for _, v in ranked[:3]) / bb * 100, 1)
    m["buyback_fee_unreferred_share_pct"] = r(ch["(none)"][3] / bb * 100, 1)
    m["buyback_fee_hhi"] = r(sum((v[3] / bb) ** 2 for v in ch.values()), 3)
    m["volume_channel_hhi"] = r(sum((v[1] / usd) ** 2 for v in ch.values()), 3)
    # Same, with SwapKit as one channel (it is one exit risk): its sub-channels merged.
    merged: dict = defaultdict(float)
    for k, v in ch.items():
        merged["swapkit" if k.startswith("swapkit/") else k] += v[1]
    m["volume_channel_hhi_swapkit_merged"] = r(sum((x / usd) ** 2 for x in merged.values()), 3)
    m["swapkit_share_of_intents_net_pct"] = r(m["swapkit_vol_share_pct"] * m["explorer_vs_llama_net_pct"] / 100, 1)
    # The same wallet, two integrations: Trust Wallet direct (pays NEAR) vs Trust via SwapKit (does not).
    for key, k in (("trust_direct", "trustwallet"), ("trust_via_swapkit", "swapkit/trustswapkit.near")):
        v = ch.get(k, [0, 0.0, 0.0, 0.0])
        m[f"{key}_vol_share_pct"] = r(v[1] / usd * 100, 1)
        m[f"{key}_buyback_bp"] = r(v[3] / v[1] * 1e4, 1) if v[1] else 0.0
        m[f"{key}_partner_bp"] = r(v[2] / v[1] * 1e4, 1) if v[1] else 0.0

    # Where the buyback wallet's NEAR came from (native_withdraw sources).
    src: dict = defaultdict(lambda: [0.0, 0.0])
    fef_other = 0.0  # fefundsadmin's non-collector (escrow-path) inflow, USD
    for x in read_raw("bq/buyback_withdraw_sources.json"):
        k = "a" if x["src"] == COLLECTOR_A else "b" if x["src"] == COLLECTOR_B else "other"
        if x["wallet"] != "buybacks.multisignature.near":
            if k == "other":
                fef_other += float(x["near"]) * near_price[x["day"]]
            continue
        src[k][0] += float(x["near"]); src[k][1] += float(x["near"]) * near_price[x["day"]]
    tot = sum(v[1] for v in src.values())
    m["bb_from_collector_a_usd_k"] = r(src["a"][1] / 1e3, 1)
    m["bb_from_collector_b_usd_k"] = r(src["b"][1] / 1e3, 1)
    m["bb_from_escrow_unshield_usd_k"] = r(src["other"][1] / 1e3, 1)
    m["bb_from_escrow_unshield_share_pct"] = r(src["other"][1] / tot * 100, 1)
    # Tighter ceiling on NEAR's share of fees on swaps with no buyback entry: collector B's NEAR is
    # quote improvement, not fee share, so only the confidential-escrow unshields (fee stream unattested) could hide one.
    m["near_share_of_partner_fees_max_tight_pct"] = r(src["other"][1] / 1e3 / m["explorer_partner_fees_no_bb_usd_k"] * 100, 1)
    m["partners_kept_vs_near_rev_low_tight_x"] = r(
        (m["explorer_partner_fees_all_usd_k"] - src["other"][1] / 1e3) / m["revwallets_usd_k"], 2)

    # Value what reached each collector (token amounts x daily USD price).
    prices = {c: {day(ms / 1000): float(p) for ms, p in pts} for c, pts in read_raw("coingecko/majors_90d.json").items()}
    prices["near"] = near_price
    val: dict = defaultdict(float)
    n_all: dict = defaultdict(int)
    n_val: dict = defaultdict(int)
    for x in read_raw("bq/collector_inflows.json"):
        k = "a" if x["collector"] == COLLECTOR_A else "b"
        n_all[k] += int(x["n"])
        v = token_usd(x["token"], float(x["amount"]), x["day"], prices)
        if v is not None:
            val[k] += v; n_val[k] += int(x["n"])
    m["collector_a_inflow_usd_k"] = r(val["a"] / 1e3, 1)
    m["collector_b_inflow_usd_k"] = r(val["b"] / 1e3, 1)
    m["collector_a_valued_transfers_pct"] = r(n_val["a"] / n_all["a"] * 100, 1)
    m["collector_b_valued_transfers_pct"] = r(n_val["b"] / n_all["b"] * 100, 1)
    m["collector_a_vs_explicit_fees_pct"] = r(val["a"] / 1e3 / m["explorer_appfees_to_buybacks_usd_k"] * 100, 1)

    # SwapKit exit: revenue at risk, 30-day basis, as % of NEAR's captured Intents revenue.
    # Traceable: explicit buyback fees on SwapKit swaps + collector B (quote improvement) pro rata to volume.
    # Ceiling: + all NEAR unshielded from the Confidential Intents escrow to the buyback wallet; which fee
    # stream it comes from is not visible on the public ledger.
    traceable = sum(v[3] for v in sk) + val["b"] * m["swapkit_vol_share_pct"] / 100
    m["swapkit_exit_traceable_usd_k"] = r(traceable / 1e3, 1)
    m["swapkit_exit_traceable_pct"] = r(traceable / 1e3 / m["revwallets_usd_k"] * 100, 1)
    m["swapkit_exit_ceiling_pct"] = r((traceable + src["other"][1]) / 1e3 / m["revwallets_usd_k"] * 100, 1)
    # Wider ceiling: the ledger cannot exclude a partner settlement in the escrow NEAR that reached the
    # front-end wallet either, so the same logic run on all escrow-path NEAR.
    m["fefunds_escrow_path_usd_k"] = r(fef_other / 1e3, 1)
    m["swapkit_exit_ceiling_all_escrow_pct"] = r((traceable + src["other"][1] + fef_other) / 1e3 / m["revwallets_usd_k"] * 100, 1)


def escrow_ladder(m: dict, lo: str, hi: str) -> None:
    """Escrow-unshield evidence (data/raw/escrow/, re-checkable with pipeline.fetch_escrow).

    Each delivery of NEAR to the revenue wallets is classified by its withdrawing account; single-use
    accounts carry their funding hop. Rungs are NEAR delivered per day over lo..hi as % of net issuance per
    day between the two archival total_supply reads. Exploratory, post-freeze (not a PREREG test)."""
    import csv
    from fractions import Fraction
    path = RAW / "escrow" / "deliveries.csv"
    if not path.exists():
        return
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    reads = read_raw("escrow/issuance_reads.json")["reads"]
    (t0, s0), (t1, s1) = sorted((int(x["timestamp_ns"]), int(x["total_supply"])) for x in reads)
    iss = Fraction(s1 - s0, YOCTO) / Fraction(t1 - t0, 86400 * 10**9)
    win = [x for x in rows if lo <= x["day"] <= hi]
    from datetime import date
    n_days = (date.fromisoformat(hi) - date.fromisoformat(lo)).days + 1

    def near(sel) -> Fraction:
        return Fraction(sum(int(x["amount_yocto"]) for x in win if sel(x)), YOCTO)

    single = [x for x in win if x["path"] in ("escrow_unshield", "other") and x["single_use_account"]]
    verified = [x for x in single if x["funder"] == PRIVATE_TREASURY_ESCROW and x["exact_amount_flag"] == "1"]
    m["escrow_unshields_30d_n"] = len([x for x in win if x["path"] == "escrow_unshield"])
    m["escrow_single_use_30d_n"] = len(single)
    m["escrow_funded_exact_30d_n"] = len(verified)
    m["escrow_funded_exact_30d_pct"] = r(len(verified) / len(single) * 100, 1) if single else 0.0
    bb = lambda x: x["wallet"] == "buybacks.multisignature.near"
    m["escrow_share_of_buyback_near_30d_pct"] = r(float(near(lambda x: bb(x) and x["path"] == "escrow_unshield")
                                                     / near(bb) * 100), 1)
    m["net_issuance_near_per_day_window"] = r(float(iss), 0)
    for key, sel in (("all_wallets", lambda x: True), ("buyback_only", bb),
                     ("public_collectors", lambda x: x["path"] in ("collector_a", "collector_b")),
                     ("escrow_unshields", lambda x: x["path"] == "escrow_unshield")):
        m[f"ladder_{key}_pct_of_issuance"] = r(float(near(sel) / n_days / iss * 100), 2)
    tot, esc = defaultdict(int), defaultdict(int)
    for x in rows:
        if bb(x):
            tot[x["day"][:7]] += int(x["amount_yocto"])
            esc[x["day"][:7]] += int(x["amount_yocto"]) if x["path"] == "escrow_unshield" else 0
    m["escrow_share_of_buyback_by_month"] = [{"month": k, "share_pct": r(esc[k] / tot[k] * 100, 1),
                                              "note": "from 07-07" if k == "2026-07" else ""}
                                             for k in sorted(tot) if k <= hi[:7]]


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

    # ---------- staking-pool flows (BigQuery account_changes; PREREG H1a) ----------
    if (RAW / "bq" / "staking_flows_daily.json").exists():
        rows = read_raw("bq/staking_flows_daily.json")
        tot = lambda k: sum(float(x[k]) for x in rows)  # noqa: E731
        rewards, inflow, outflow = tot("rewards_near"), tot("inflow_near"), tot("outflow_near")
        m["pool_flow_days"] = len(rows)
        m["pool_rewards_90d_m"] = r(rewards / 1e6, 2)
        m["pool_inflow_90d_m"] = r(inflow / 1e6, 1)
        m["pool_outflow_90d_m"] = r(outflow / 1e6, 1)
        m["pool_net_outflow_90d_m"] = r((outflow - inflow) / 1e6, 1)
        m["pool_net_outflow_to_rewards_x"] = r((outflow - inflow) / rewards, 2)
        ends = {x["block_date"]: float(x["pool_total_near"]) for x in read_raw("bq/staking_pool_totals_endpoints.json")}
        start, end = ends["2026-08-06"], ends["2026-11-04"]
        m["pool_total_start_m"] = r(start / 1e6, 1)
        m["pool_total_end_m"] = r(end / 1e6, 1)
        m["pool_total_change_m"] = r((end - start) / 1e6, 1)
        # Residual between the endpoint balances and the summed daily flows (method check, not a finding).
        m["pool_flow_residual_m"] = r(((end - start) - (rewards + tot("gas_rebate_near") + inflow - outflow)) / 1e6, 1)
        # H1a: pass if net staking outflow < 50% of staking rewards. Must hold under both measures.
        net_by_endpoint = rewards - (end - start)
        m["h1a_pass"] = bool((outflow - inflow) < 0.5 * rewards and net_by_endpoint < 0.5 * rewards)

    # ---------- 1Click swaps from the Intents Explorer API (one-sided amountInUsd) ----------
    if (RAW / "explorer" / "daily.json").exists():
        days = [x for x in read_raw("explorer/daily.json")["days"] if add_days(asof, -29) <= x["date"] <= asof]
        if days:
            n_days = len(days)
            usd = sum(x["usd_in"] for x in days)
            llama_same = sum(v.get(x["date"], 0) for x in days)
            m["explorer_days"] = n_days
            m["explorer_usd_in_m"] = r(usd / 1e6, 1)
            m["explorer_swaps_k"] = r(sum(x["n"] for x in days) / 1e3, 1)
            m["explorer_vs_llama_reported_pct"] = r(usd / llama_same * 100, 1)
            m["explorer_vs_llama_net_pct"] = r(usd / (llama_same / 2) * 100, 1)
            ref = defaultdict(float)
            for x in days:
                for t in x["top_referrals"]:
                    ref[t["referral"]] += t["usd_in"]
            shares = sorted(((k, val / usd * 100) for k, val in ref.items()), key=lambda kv: -kv[1])
            m["explorer_top_channels"] = [{"channel": k, "share_pct": r(s, 1)} for k, s in shares[:8]]
            m["explorer_channel_hhi"] = r(sum((s / 100) ** 2 for _, s in shares), 3)
            fee = defaultdict(float)
            for x in days:
                for k, val in x["fee_usd_by_recipient"].items():
                    fee[k] += val
            tot_fee = sum(fee.values())
            m["explorer_appfees_usd_k"] = r(tot_fee / 1e3, 1)
            m["explorer_appfees_bp"] = r(tot_fee / usd * 1e4, 1)
            m["explorer_appfees_to_buybacks_usd_k"] = r(fee.get("buybacks.multisignature.near", 0) / 1e3, 1)
            m["explorer_appfees_to_buybacks_pct"] = r(fee.get("buybacks.multisignature.near", 0) / tot_fee * 100, 1)
            m["explorer_top_fee_recipients"] = [{"recipient": k, "usd_k": r(val / 1e3, 1)}
                                                for k, val in sorted(fee.items(), key=lambda kv: -kv[1])[:8]]

            def sum_dict(key: str) -> dict:
                out: dict = defaultdict(float)
                for x in days:
                    for k, val in (x.get(key) or {}).items():
                        out[k] += val
                return out

            if all("fee_split" in x for x in days):
                # What the NEAR token itself gets from Intents flow: swaps into / out of wNEAR.
                nl = sum_dict("near_leg")
                legs = sum_dict("usd_by_asset_leg")
                m["explorer_near_leg_share_pct"] = r(legs.get("nep141:wrap.near", 0) / usd * 100, 1)
                # Swaps with NEAR on exactly one side, as a share of swap volume (not leg-weighted).
                m["explorer_near_side_swap_share_pct"] = r((nl["into_usd"] + nl["out_usd"]) / usd * 100, 1)
                m["explorer_into_near_usd_m"] = r(nl["into_usd"] / 1e6, 1)
                m["explorer_out_of_near_usd_m"] = r(nl["out_usd"] / 1e6, 1)
                m["explorer_net_near_sold_usd_m"] = r((nl["out_usd"] - nl["into_usd"]) / 1e6, 1)
                stables = [k for k in legs if any(s in k for s in (
                    "eth-0xdac17f958d2ee523a2206206994597c13d831ec7", "eth-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                    "tron-d28a265909efecdcee7c5028585214ea0b96f015", "usdt.tether-token.near",
                    "17208628f84f5d6ad33f0da3bbbeb27ffcb398eac501a31bd6ad2011e36133a1",
                    "base-0x833589fcd6edb6e08f4c7c32d4f71b54bda02913", "arb-0xaf88d065e77c8cc2239327c5edb3a432268e5831"))]
                m["explorer_stablecoin_leg_share_pct"] = r(sum(legs[k] for k in stables) / usd * 100, 1)
                m["explorer_top_asset_legs"] = [{"asset": k, "share_pct": r(val / usd * 100, 1)}
                                                for k, val in sorted(legs.items(), key=lambda kv: -kv[1])[:10]]
                # Size: swaps of $10K+ (buckets are lower edges in USD).
                sb: dict = defaultdict(lambda: [0, 0.0])
                for x in days:
                    for k, (n, v) in x["size_buckets"].items():
                        sb[k][0] += n; sb[k][1] += v
                big = [k for k in sb if float(k) >= 10_000]
                n_all = sum(v[0] for v in sb.values())
                m["explorer_swaps_10k_plus_n_pct"] = r(sum(sb[k][0] for k in big) / n_all * 100, 1)
                m["explorer_swaps_10k_plus_vol_pct"] = r(sum(sb[k][1] for k in big) / usd * 100, 1)
                # Who keeps the listed fees: explicit buyback entries vs partner entries.
                fs = sum_dict("fee_split")
                m["explorer_vol_with_buyback_fee_pct"] = r(fs["usd_in_with_bb"] / usd * 100, 1)
                m["explorer_partner_fees_no_bb_usd_k"] = r(fs["partner_without_bb_usd"] / 1e3, 1)
                m["explorer_partner_fees_all_usd_k"] = r((fs["partner_without_bb_usd"] + fs["partner_with_bb_usd"]) / 1e3, 1)
                # Realized cost vs listed fees, swaps $1K-$50K: (in - out) minus listed fee = solver/market spread.
                cost: dict = defaultdict(lambda: [0, 0.0, 0.0, 0.0])
                for x in days:
                    for k, vals in x["realized_cost_1k_50k"].items():
                        for i, val in enumerate(vals):
                            cost[k][i] += val
                m["explorer_realized_cost_by_listed_bp"] = [
                    {"listed_bp_from": int(float(k)), "n": int(v[0]), "realized_bp": r(v[2] / v[1] * 1e4, 1),
                     "listed_bp": r(v[3] / v[1] * 1e4, 1), "excess_bp": r((v[2] - v[3]) / v[1] * 1e4, 1)}
                    for k, v in sorted(cost.items(), key=lambda kv: float(kv[0]))]
                tc = [sum(v[i] for v in cost.values()) for i in range(4)]
                m["explorer_excess_over_listed_bp"] = r((tc[2] - tc[3]) / tc[1] * 1e4, 1)

    # ---------- NEAR's revenue wallets: native NEAR arriving from outside the wallet set ----------
    if (RAW / "bq" / "revenue_wallet_inflows.json").exists():
        rw = read_raw("bq/revenue_wallet_inflows.json")
        wn = read_raw("bq/revenue_wallet_wnear_inflows.json") if (RAW / "bq" / "revenue_wallet_wnear_inflows.json").exists() else []
        lo, hi = min(x["day"] for x in rw), max(x["day"] for x in rw)
        by_w: dict = defaultdict(float)
        by_w_near: dict = defaultdict(float)
        for x in rw + [y for y in wn if lo <= y["day"] <= hi]:
            by_w[x["wallet"]] += float(x["near"]) * price[x["day"]]
            by_w_near[x["wallet"]] += float(x["near"])
        tot_w = sum(by_w.values())
        llama_rev = sum(v for k, v in rev.items() if lo <= k <= hi)
        m["revwallets_window"] = f"{lo}..{hi}"
        m["revwallets_usd_k"] = r(tot_w / 1e3, 1)
        m["revwallets_near_k"] = r(sum(by_w_near.values()) / 1e3, 1)
        m["revwallets_buybacks_usd_k"] = r(by_w["buybacks.multisignature.near"] / 1e3, 1)
        m["revwallets_frontend_usd_k"] = r(by_w["fefundsadmin.sputnik-dao.near"] / 1e3, 1)
        m["revwallets_frontend_share_pct"] = r(by_w["fefundsadmin.sputnik-dao.near"] / tot_w * 100, 1)
        m["revwallets_vs_llama_rev_pct"] = r(tot_w / llama_rev * 100, 1)
        ex_days = [x["date"] for x in read_raw("explorer/daily.json")["days"]] if (RAW / "explorer" / "daily.json").exists() else []
        same_window = "explorer_partner_fees_no_bb_usd_k" in m and m.get("explorer_days") == len(
            [d for d in ex_days if lo <= d <= hi]) and add_days(asof, -29) == lo and asof == hi
        if not same_window:
            print(f"note: revenue-wallet window {lo}..{hi} differs from the Explorer window; partner-fee bound skipped")
        if same_window:
            bb_explicit = m["explorer_appfees_to_buybacks_usd_k"]
            unexplained = m["revwallets_buybacks_usd_k"] - bb_explicit
            partner_nobb = m["explorer_partner_fees_no_bb_usd_k"]
            # Upper bound: every buyback-wallet dollar not explained by explicit buyback fee entries came
            # from partners whose fee lists show no buyback entry. The documented default is 50%.
            m["buybacks_unexplained_usd_k"] = r(unexplained, 1)
            m["near_share_of_partner_fees_max_pct"] = r(unexplained / partner_nobb * 100, 1)
            kept_low = m["explorer_partner_fees_all_usd_k"] - max(unexplained, 0)
            m["partners_kept_vs_near_rev_low_x"] = r(kept_low / m["revwallets_usd_k"], 2)
            m["partners_kept_vs_near_rev_high_x"] = r(m["explorer_partner_fees_all_usd_k"] / m["revwallets_usd_k"], 2)
            concentration(m, price, lo, hi)
            escrow_ladder(m, lo, hi)

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
