"""Compute every published number from data/raw/ (offline) into data/metrics.json and data/series.json.

Nothing here touches the network. Each metric records the inputs it came from in METRIC_SOURCES,
which the dashboard prints under each chart.

Run: python3 -m pipeline.compute
"""
from __future__ import annotations

import argparse
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
    with open(path, newline="", encoding="utf-8") as f:
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
    for k in sorted(tot):
        if k <= hi[:7]:
            m[f"escrow_share_buyback_{k.replace('-', '_')}_pct"] = r(esc[k] / tot[k] * 100, 1)
    m["ladder_other_pct_of_issuance"] = r(float(near(lambda x: x["path"] == "other") / n_days / iss * 100), 2)


def escrow_recheck(m: dict, lo: str, hi: str) -> None:
    """Counts from the committed output of `python3 -m pipeline.fetch_escrow verify --all` (exploratory).

    That command re-reads every row of data/raw/escrow/deliveries.csv, and every funding transfer, from the chain
    and writes one record per row to data/raw/escrow/verify_all.json. This function only counts those records;
    it makes no network call. The counts are taken from the per-row records and must equal the tool's own summary,
    so a hand-edited file stops the build. A row's "funding error" is any error other than the delivery-side ones
    the tool can raise (a missing delivery, a wrong amount, a block height that differs, a missing or mismatched
    native_withdraw event); with the committed data no row has one."""
    import csv
    path = RAW / "escrow" / "verify_all.json"
    csv_path = RAW / "escrow" / "deliveries.csv"
    if not path.exists() or not csv_path.exists():
        return
    d = read_raw("escrow/verify_all.json")
    with open(csv_path, newline="", encoding="utf-8") as f:
        table = list(csv.DictReader(f))
    rows = {x["delivery_tx_hash"]: x for x in d["rows"]}
    if len(rows) != len(d["rows"]) or set(rows) != {x["delivery_tx_hash"] for x in table}:
        raise ValueError("verify_all.json and deliveries.csv do not list the same delivery transactions")
    delivery_side = ("delivery tx not returned", "no successful Transfer", "block mismatch", "no native_withdraw",
                     "native_withdraw source")

    def funding_errors(x: dict) -> list[str]:
        return [e for e in x["errors"] if not e.startswith(delivery_side)]

    failed = [x for x in d["rows"] if not x["ok"]]
    height_only = [x for x in failed if x["errors"] and all(e.startswith("block mismatch") for e in x["errors"])]
    hops = [x for x in table if x["funding_tx_hash"]]
    hops_ok = [x for x in hops if not funding_errors(rows[x["delivery_tx_hash"]])]
    win = [x for x in table if lo <= x["day"] <= hi and x["path"] in ("escrow_unshield", "other")
           and x["single_use_account"]]
    s = d["summary"]
    counted = {"rows": len(d["rows"]), "rows_ok": len(d["rows"]) - len(failed), "funding_hops": len(hops),
               "funding_hops_ok": len(hops_ok)}
    if any(s[k] != v for k, v in counted.items()):
        raise ValueError(f"verify_all.json: its summary {({k: s[k] for k in counted})} differs from its rows {counted}")
    m["escrow_recheck_rows_n"] = counted["rows"]
    m["escrow_recheck_rows_ok_n"] = counted["rows_ok"]
    m["escrow_recheck_failed_n"] = len(failed)
    m["escrow_recheck_failed_height_only_n"] = len(height_only)
    m["escrow_recheck_funding_hops_n"] = counted["funding_hops"]
    m["escrow_recheck_funding_hops_ok_n"] = counted["funding_hops_ok"]
    m["escrow_recheck_window_single_use_n"] = len(win)
    m["escrow_recheck_window_funding_ok_n"] = len([x for x in win if x["funding_tx_hash"]
                                                   and not funding_errors(rows[x["delivery_tx_hash"]])])
    m["escrow_recheck_window_rows_ok_n"] = len([x for x in win if rows[x["delivery_tx_hash"]]["ok"]])


CONFIDENTIAL_1CLICK = "2026-10-27"  # NEAR Intents changelog: 1Click swaps settle confidentially from this day


def collector_funders(m: dict, near_price: dict, lo: str, hi: str) -> None:
    """Split the public-collector rung of the ladder by who funded the collectors' fees (exploratory, 2026-11-13).

    data/raw/bq/collector_inflow_funders.json classifies every transfer into collector A or B by its sender
    (sql/collector_inflow_funders.sql): a public swap account, a single-use account the Confidential Intents
    treasury had funded (escrow_funded), the treasury itself, or other. Summed over class it must equal
    collector_inflows.json, or the build stops. Shares are USD-weighted, because each collector's NEAR comes
    from all its fee tokens, and each day's NEAR delivered (deliveries.csv) takes that day's share."""
    import csv
    import statistics
    from datetime import date
    if not (RAW / "bq" / "collector_inflow_funders.json").exists():
        return
    fund = read_raw("bq/collector_inflow_funders.json")
    tot: dict = defaultdict(lambda: [0, 0])
    for x in fund:
        k = (x["day"], x["collector"], x["token"])
        tot[k][0] += int(x["amount"]); tot[k][1] += int(x["n"])
    ref = {(x["day"], x["collector"], x["token"]): [int(x["amount"]), int(x["n"])]
           for x in read_raw("bq/collector_inflows.json")}
    if dict(tot) != ref:
        raise ValueError("collector_inflow_funders.json summed over class differs from collector_inflows.json")

    prices = {c: {day(ms / 1000): float(p) for ms, p in pts} for c, pts in read_raw("coingecko/majors_90d.json").items()}
    prices["near"] = near_price
    CLS = ("public_swap", "escrow_funded", "escrow_direct", "other")
    ESC = ("escrow_funded", "escrow_direct")
    coll = {COLLECTOR_A: "a", COLLECTOR_B: "b"}
    usd: dict = defaultdict(float)
    cnt: dict = defaultdict(int)
    usd_n: dict = defaultdict(int)  # priced transfers
    for x in fund:
        if not lo <= x["day"] <= hi:
            continue
        k = (x["day"], coll[x["collector"]], x["class"])
        cnt[k] += int(x["n"])
        v = token_usd(x["token"], float(x["amount"]), x["day"], prices)
        if v is not None:
            usd[k] += v; usd_n[k] += int(x["n"])
    with open(RAW / "escrow" / "deliveries.csv", newline="", encoding="utf-8") as f:
        win = [x for x in csv.DictReader(f) if lo <= x["day"] <= hi]
    dl = [x for x in win if x["path"] in ("collector_a", "collector_b")]
    deliv: dict = defaultdict(float)
    for x in dl:
        deliv[(x["day"], x["path"][-1])] += int(x["amount_yocto"]) / YOCTO
    days = [add_days(lo, i) for i in range((date.fromisoformat(hi) - date.fromisoformat(lo)).days + 1)]
    pre = [d for d in days if d < CONFIDENTIAL_1CLICK]
    post = [d for d in days if d >= CONFIDENTIAL_1CLICK]
    iss = m["net_issuance_near_per_day_window"]

    def share(src: dict, c: str, ds: list, classes=ESC) -> float:
        t = sum(src[(d, c, k)] for d in ds for k in CLS)
        return sum(src[(d, c, k)] for d in ds for k in classes) / t if t else 0.0

    def pts(near: float) -> float:
        return near / len(days) / iss * 100

    # Primary: same-day attribution.
    esc_near = {c: sum(deliv[(d, c)] * share(usd, c, [d]) for d in days) for c in "ab"}
    oth_near = sum(deliv[(d, c)] * share(usd, c, [d], ("other",)) for d in days for c in "ab")
    all_near = sum(deliv.values())
    esc_all = sum(esc_near.values())
    pub_near = all_near - esc_all - oth_near
    m["ladder_collectors_public_swap_pct_of_issuance"] = r(pts(pub_near), 2)
    m["ladder_collectors_escrow_funded_pct_of_issuance"] = r(pts(esc_all), 2)
    m["ladder_collectors_public_swap_near_k"] = r(pub_near / 1e3, 1)
    m["ladder_collectors_escrow_funded_near_k"] = r(esc_all / 1e3, 1)
    m["ladder_collector_a_public_swap_pct_of_issuance"] = r(pts(sum(deliv[(d, "a")] for d in days) - esc_near["a"]), 2)
    m["ladder_collector_b_public_swap_pct_of_issuance"] = r(pts(sum(deliv[(d, "b")] for d in days) - esc_near["b"]), 2)
    ladder_esc = sum(int(x["amount_yocto"]) for x in win if x["path"] == "escrow_unshield") / YOCTO
    m["ladder_escrow_all_pct_of_issuance"] = r(pts(ladder_esc + esc_all), 2)

    # Sensitivities: pooled before / after CONFIDENTIAL_1CLICK; unpriced transfers imputed at their class mean;
    # weighted by transfer count (not a valid weighting: shown because counts and value diverge).
    def pooled(src: dict) -> float:
        return sum(sum(deliv[(d, c)] for d in ds) * share(src, c, ds) for c in "ab" for ds in (pre, post))
    imp: dict = defaultdict(float)
    for c in "ab":
        for ds in (pre, post):
            for k in CLS:
                u, n_p, n = (sum(src[(d, c, k)] for d in ds) for src in (usd, usd_n, cnt))
                imp[(ds[0], c, k)] = u + (n - n_p) * (u / n_p if n_p else 0.0)
    imp_esc = sum(sum(deliv[(d, c)] for d in ds) * share(imp, c, [ds[0]]) for c in "ab" for ds in (pre, post))
    m["ladder_collectors_escrow_funded_pooled_pct_of_issuance"] = r(pts(pooled(usd)), 2)
    m["ladder_collectors_escrow_funded_imputed_pct_of_issuance"] = r(pts(imp_esc), 2)
    m["ladder_collectors_escrow_funded_by_count_pct_of_issuance"] = r(pts(pooled(cnt)), 2)

    # Collector A before / after, and the last day; collector B; mean fee per transfer.
    m["collector_a_escrow_usd_share_pre_pct"] = r(share(usd, "a", pre) * 100, 1)
    m["collector_a_escrow_usd_share_post_pct"] = r(share(usd, "a", post) * 100, 1)
    m["collector_a_escrow_usd_share_first_post_day_pct"] = r(share(usd, "a", post[:1]) * 100, 1)
    m["collector_a_escrow_usd_share_last_day_pct"] = r(share(usd, "a", days[-1:]) * 100, 1)
    m["collector_a_escrow_count_share_pre_pct"] = r(share(cnt, "a", pre) * 100, 1)
    m["collector_a_escrow_count_share_post_pct"] = r(share(cnt, "a", post) * 100, 1)
    for k in CLS:
        m[f"collector_a_{k}_n"] = sum(cnt[(d, "a", k)] for d in days)
        m[f"collector_b_{k}_n"] = sum(cnt[(d, "b", k)] for d in days)
    m["collectors_transfers_n"] = sum(cnt.values())
    for k in ("public_swap", "escrow_funded"):
        u = sum(usd[(d, "a", k)] for d in pre); n = sum(usd_n[(d, "a", k)] for d in pre)
        m[f"collector_a_{k}_mean_fee_pre_usd"] = r(u / n, 2)
    m["collector_a_unpriced_transfers_pct"] = r(
        (1 - sum(usd_n[(d, "a", k)] for d in days for k in CLS) / sum(cnt[(d, "a", k)] for d in days for k in CLS)) * 100, 1)

    # Collector A sweeps the same day: correlation of daily inflow USD with delivered USD, by lag.
    u = [sum(usd[(d, "a", k)] for k in CLS) for d in days]
    v = [deliv[(d, "a")] * near_price[d] for d in days]
    for lag in (0, 1):
        m[f"collector_a_inflow_delivery_corr_lag{lag}"] = r(statistics.correlation(u[:len(u) - lag], v[lag:]), 2)
    m["collector_a_delivered_near_k"] = r(sum(deliv[(d, "a")] for d in days) / 1e3, 1)
    m["collector_a_wnear_inflow_near_k"] = r(sum(int(x["amount"]) for x in fund if x["collector"] == COLLECTOR_A
                                                and x["token"] == "nep141:wrap.near" and lo <= x["day"] <= hi) / YOCTO / 1e3, 1)

    # Checks of the escrow_funded class (data/raw/bq/collector_funder_checks.json, sql/collector_funder_checks.sql).
    if (RAW / "bq" / "collector_funder_checks.json").exists():
        ck = [x for x in read_raw("bq/collector_funder_checks.json") if x["class"] == "escrow_funded"]
        n = sum(int(x["n"]) for x in ck)
        if n != m["collector_a_escrow_funded_n"] + m["collector_b_escrow_funded_n"]:
            raise ValueError("collector_funder_checks.json counts differ from collector_inflow_funders.json")
        for f_ in ("n_sender_single_tx", "n_sender_single_day", "n_funded_once", "n_no_other_inflow"):
            m[f"collector_escrow_funded_{f_[2:]}_pct"] = r(sum(int(x[f_]) for x in ck) / n * 100, 1)
        m["collector_escrow_funded_lag_blocks_median_max"] = max(int(x["lag_blocks_q"][2]) for x in ck)
        pub = [x for x in read_raw("bq/collector_funder_checks.json") if x["class"] == "public_swap"]
        m["collector_public_swap_with_token_diff_pct"] = r(sum(int(x["n_with_diff"]) for x in pub)
                                                           / sum(int(x["n"]) for x in pub) * 100, 1)


def l1_usage(m: dict, nb: dict, end: str) -> list[dict]:
    """Nearblocks daily usage (exploratory, descriptive; data/raw/nearblocks/charts.json).

    Finds the largest one-day fall in daily transactions over the 365 days to `end`, then reports what four
    daily counts did between two days before that day and the day itself (the contract counts fall over two
    days), and the change since it. Nearblocks does not say what its counts include, so a step that hits
    transactions, active contracts and new accounts but not active accounts is reported as a step, not
    explained. Returns the daily series the dashboard charts."""
    def val(k: str, key: str) -> float | None:
        v = nb.get(k, {}).get(key)
        return None if v in (None, "") else float(v)

    def mean(ks: list[str], key: str) -> float:
        xs = [val(k, key) for k in ks]
        xs = [x for x in xs if x is not None]
        return sum(xs) / len(xs)

    days = [k for k in sorted(nb) if add_days(end, -364) <= k <= end]
    falls = [(val(k, "txns") / val(p, "txns"), k) for p, k in zip(days, days[1:])
             if add_days(p, 1) == k and val(p, "txns") and val(k, "txns") is not None]
    if not falls:
        return []
    _, step = min(falls)
    ref = add_days(step, -2)
    m["l1_step_date"] = step
    m["l1_step_ref_date"] = ref
    for tag, key in (("tx", "txns"), ("contracts", "active_contracts"), ("new_accounts", "new_accounts"),
                     ("active_accounts", "active_accounts")):
        m[f"l1_step_{tag}_before_k"] = r(val(ref, key) / 1e3, 1)
        m[f"l1_step_{tag}_after_k"] = r(val(step, key) / 1e3, 1)
    # Like-for-like change since the step: the first 30 days from it against the latest 30 days.
    first = [add_days(step, i) for i in range(30)]
    last = [add_days(end, -i) for i in range(30)]
    for tag, key in (("tx_per_day", "txns"), ("active_accounts", "active_accounts")):
        m[f"{tag}_since_step_pct"] = r((mean(last, key) / mean(first, key) - 1) * 100, 1)
    return [{"date": k, "tx_k": r(val(k, "txns") / 1e3, 1), "active_accounts_k": r(val(k, "active_accounts") / 1e3, 1)}
            for k in sorted(nb) if "2025-10-01" <= k <= end and val(k, "txns") is not None
            and val(k, "active_accounts") is not None]


def bb_reconcile(m: dict) -> None:
    """The buyback wallet's balance growth against the deliveries from intents.near that we trace (exploratory).

    PREREG defines H1c's identified buying as the wallet's balance increase between the H1a window's endpoint
    blocks (same blocks as pipeline/h1b.py), so H1c uses all of it. The deliveries we trace (data/raw/escrow/
    deliveries.csv) explain only part of it; transfers from other accounts are not in that file. Reported, not
    adjusted: the H1c verdict is `inconclusive` whichever numerator is used (coverage is below 50%)."""
    import csv
    from fractions import Fraction
    bal = read_raw("rpc/buyback_balance_endpoints.json")["blocks"]
    lo, hi = "210238033", "223088015"
    growth = Fraction(int(bal[hi]["amount"]) - int(bal[lo]["amount"]), YOCTO)
    with open(RAW / "escrow" / "deliveries.csv", newline="", encoding="utf-8") as f:
        got = Fraction(sum(int(x["amount_yocto"]) for x in csv.DictReader(f)
                           if x["wallet"] == "buybacks.multisignature.near"
                           and "2026-08-07" <= x["day"] <= "2026-11-04"), YOCTO)
    m["bb_deliveries_90d_m"] = r(float(got) / 1e6, 3)
    m["bb_growth_not_delivered_m"] = r(float(growth - got) / 1e6, 3)
    m["bb_growth_not_delivered_pct"] = r(float((growth - got) / growth) * 100, 1)


def take_over_time(m: dict, rev: dict, vol: dict, asof: str) -> None:
    """1Click fee take in three 30-day blocks ending asof (Explorer days must cover all 90)."""
    days = {x["date"]: x for x in read_raw("explorer/daily.json")["days"]}
    for i, tag in ((2, "b1"), (1, "b2"), (0, "b3")):
        hi = add_days(asof, -30 * i); lo = add_days(hi, -29)
        ds = [days[d] for d in days if lo <= d <= hi]
        if len(ds) != 30 or not all("by_channel" in x for x in ds):
            return
        usd = sum(x["usd_in"] for x in ds)
        fs = lambda k: sum(x["fee_split"][k] for x in ds)
        m[f"take_{tag}_window"] = f"{lo}..{hi}"
        m[f"take_{tag}_bb_explicit_bp"] = r(fs("bb_explicit_usd") / usd * 1e4, 2)
        m[f"take_{tag}_partner_bp"] = r((fs("partner_with_bb_usd") + fs("partner_without_bb_usd")) / usd * 1e4, 1)
        m[f"take_{tag}_vol_with_bb_pct"] = r(fs("usd_in_with_bb") / usd * 100, 1)
        m[f"take_{tag}_swapkit_vol_pct"] = r(sum(v[1] for x in ds for k, v in x["by_channel"].items()
                                                 if k.startswith("swapkit/")) / usd * 100, 1)
        lv = sum(vol.get(d, 0) for d in days if lo <= d <= hi)
        lr = sum(rev.get(d, 0) for d in days if lo <= d <= hi)
        m[f"take_{tag}_oneclick_vs_llama_net_pct"] = r(usd / (lv / 2) * 100, 1)
        m[f"take_{tag}_captured_bp"] = r(lr / lv * 1e4, 2)  # DefiLlama revenue / reported (leg-sum) volume
        m[f"take_{tag}_oneclick_usd_m"] = r(usd / 1e6, 0)
    # DefiLlama's series steps on 2026-09-01: 1Click's share of it, the week before vs the week from that day.
    for key, lo, hi in (("before", "2026-08-25", "2026-08-31"), ("after", "2026-09-01", "2026-09-07")):
        ds = [d for d in days if lo <= d <= hi]
        m[f"oneclick_share_of_llama_week_{key}_0901_pct"] = r(
            sum(days[d]["usd_in"] for d in ds) / (sum(vol.get(d, 0) for d in ds) / 2) * 100, 1)


def fee_evidence(m: dict) -> None:
    """Per-swap fee mechanics from data/raw/evidence/ (pipeline.fetch_fee_evidence): 195 in-window swaps.

    A listed fee counts as paid on chain if some intents.near movement in the swap's NEAR txs carries
    amountIn x bps / 1e4 (within 0.6%, at least 2 raw units). The buyback fee must go to collector A;
    partner fees may go to any other account (partners often collect at an implicit account)."""
    ex = read_raw("evidence/fee_sample_explorer.json")
    on = read_raw("evidence/fee_sample_onchain.json")["swaps"]
    bb = "buybacks.multisignature.near"

    def match(moves, amount_in, bps, to_ok):
        want = amount_in * bps / 1e4
        for mv in moves:
            a = int(mv["amount"])
            if a >= 2 and abs(a - want) <= max(2, 0.006 * want) and to_ok(mv["to"]):
                return mv
        return None

    c = defaultdict(int)
    zodl_to, b_bp = set(), []
    recips: dict = defaultdict(lambda: defaultdict(int))
    for sw, o in zip(ex["swaps"], on):
        mv, ain = o["moves"], int(sw["amountIn"])
        sk = sw["channel"].startswith("swapkit/")
        a_moves = [x for x in mv if x["to"] == COLLECTOR_A]
        c["n"] += 1
        c["sk_swaps"] += sk
        for f in sw["appFees"] or []:
            if f["recipient"] == bb:
                c["bb_listed"] += 1
                c["bb_paid_exact"] += match(mv, ain, f["fee"], lambda t: t == COLLECTOR_A) is not None
            else:
                hit = match(mv, ain, f["fee"], lambda t: t not in (COLLECTOR_A, COLLECTOR_B))
                k = "sk" if sk else "zodl" if sw["channel"] == "zodl" else "other"
                c[f"p_{k}_listed"] += 1
                c[f"p_{k}_paid"] += hit is not None
                c[f"p_{k}_zero"] += f["fee"] == 0  # a zero-rate entry is listed but nothing is owed on it
                if hit is None and f["fee"] != 0:
                    c["p_nz_miss"] += 1
                    c["p_nz_miss_escrow"] += any(x["to"] == PRIVATE_TREASURY_ESCROW for x in mv)
                if hit and k == "zodl":
                    zodl_to.add(hit["to"])
                if hit:
                    recips[f["recipient"]][hit["to"]] += 1
        if not any(f["recipient"] == bb for f in sw["appFees"] or []):
            c["unlisted"] += 1
            c["unlisted_a_paid"] += bool(a_moves)
        bmv = [x for x in mv if x["to"] == COLLECTOR_B]
        if bmv:
            c["b_paid"] += 1
            c["b_paid_sk"] += sk
            out = int(sw["amountOut"] or 0)
            # one payment can appear twice with different `from` accounts: count each (tx, token, amount) once
            same = [int(a) for (_, tok, a) in {(x["tx"], x["token"], x["amount"]) for x in bmv}
                    if tok == sw["destinationAsset"]]
            if same and out:
                b_bp.append(sum(same) / out * 1e4)
    m["fee_ev_swaps_n"] = c["n"]
    m["fee_ev_channels_n"] = len({x["channel"] for x in ex["swaps"]})
    m["fee_ev_bb_listed_n"] = c["bb_listed"]
    m["fee_ev_bb_paid_exact_n"] = c["bb_paid_exact"]
    m["fee_ev_unlisted_n"] = c["unlisted"]
    m["fee_ev_unlisted_collector_a_paid_n"] = c["unlisted_a_paid"]
    m["fee_ev_swapkit_fees_listed_n"] = c["p_sk_listed"]
    m["fee_ev_swapkit_fees_paid_onchain_n"] = c["p_sk_paid"]
    m["fee_ev_zodl_fees_listed_n"] = c["p_zodl_listed"]
    m["fee_ev_zodl_fees_paid_onchain_n"] = c["p_zodl_paid"]
    m["fee_ev_zodl_fee_accounts"] = sorted(zodl_to)
    m["fee_ev_other_partner_fees_listed_n"] = c["p_other_listed"]
    m["fee_ev_other_partner_fees_paid_onchain_n"] = c["p_other_paid"]
    m["fee_ev_swapkit_fees_zero_rate_n"] = c["p_sk_zero"]
    m["fee_ev_zodl_fees_zero_rate_n"] = c["p_zodl_zero"]
    m["fee_ev_other_partner_fees_zero_rate_n"] = c["p_other_zero"]
    # Listed partner fees with a non-zero rate that no movement in the swap's NEAR txs matches, and how many
    # of those swaps moved tokens into the Confidential Intents escrow (where the public chain shows no fee).
    m["fee_ev_partner_fees_nonzero_unmatched_n"] = c["p_nz_miss"]
    m["fee_ev_partner_fees_nonzero_unmatched_escrow_n"] = c["p_nz_miss_escrow"]
    m["fee_ev_swapkit_swaps_n"] = c["sk_swaps"]
    m["fee_ev_hours_with_swaps_n"] = len({x["hour"] for x in ex["swaps"]})
    m["fee_ev_partner_fee_accounts"] = {k: max(v, key=v.get) for k, v in sorted(recips.items())
                                        if sum(v.values()) >= 3}
    m["fee_ev_collector_b_swaps_n"] = c["b_paid"]
    m["fee_ev_collector_b_swapkit_swaps_n"] = c["b_paid_sk"]
    b_bp.sort()
    if b_bp:
        m["fee_ev_collector_b_bp_median"] = r(b_bp[len(b_bp) // 2], 2)
        m["fee_ev_collector_b_bp_min"] = r(b_bp[0], 2)
        m["fee_ev_collector_b_bp_max"] = r(b_bp[-1], 1)
        m["fee_ev_collector_b_bp_n"] = len(b_bp)


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
    l1_daily = l1_usage(m, nb, nb_end)

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
    pool_net_out = None
    if (RAW / "bq" / "staking_flows_daily.json").exists():
        rows = read_raw("bq/staking_flows_daily.json")
        tot = lambda k: sum(float(x[k]) for x in rows)  # noqa: E731
        rewards, inflow, outflow = tot("rewards_near"), tot("inflow_near"), tot("outflow_near")
        pool_net_out = outflow - inflow
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
            escrow_recheck(m, lo, hi)
            collector_funders(m, price, lo, hi)

    # ---------- H1a as written: gross issuance from epoch-boundary headers (PREREG-ADDENDUM 2026-11-06) ----------
    if (RAW / "rpc" / "epoch_issuance.json").exists():
        from .h1a import h1a
        h1a(m)  # before h1b: h1b reads m["h1a_gross_issuance_90d_m"]

    # ---------- H1b / H1c (PREREG exchange-flow tests; method in PREREG-ADDENDUM 2026-11-06 23:11 UTC) ----------
    if (RAW / "bq" / "h1b_a_native_flows.json").exists():
        from .h1b import h1b
        h1b(m)

    if (RAW / "escrow" / "deliveries.csv").exists() and (RAW / "rpc" / "buyback_balance_endpoints.json").exists():
        bb_reconcile(m)

    # ---------- Rating rule (PREREG: G_req, G_obs, H1b verdict) ----------
    if (RAW / "rpc" / "rating_assumptions.json").exists():
        from .h1a import rating
        rating(m)
        if "rating_g_req_pct" in m:  # PREREG's Avoid line: G_obs below half of G_req
            m["rating_g_avoid_line_pct"] = r(m["rating_g_req_pct"] / 2, 1)

    # ---------- Large unstakers -> intents.near (exploratory; data/raw/unstakers/, sql/unstakers/) ----------
    if (RAW / "unstakers" / "results.json").exists():
        u = read_raw("unstakers/results.json")
        m["unstakers_into_intents_m"] = r(u["into_intents_total_near_capped"] / 1e6, 2)
        m["unstakers_into_intents_overlap_k"] = r(u["set_into_intents_overlap_near_capped"] / 1e3, 1)
        m["unstakers_overlap_pct_of_1click_near_sold"] = r(u["set_overlap_pct_capped"], 1)
        m["oneclick_near_sold_30d_m"] = r(u["oneclick"]["near_to_x_near_at_daily_price"] / 1e6, 2)

    # The 14 hub-lineage withdrawers' net unstaking over the H1a window, against the pools' net outflow
    # (exploratory). account_set.json is a committed, hash-checked input; the extraction that produced its
    # net_diff values is not in this repository, and its window blocks are the H1a window's.
    if (RAW / "unstakers" / "account_set.json").exists() and pool_net_out:
        aset = read_raw("unstakers/account_set.json")
        a14 = [v["net_diff"] for v in aset["accounts"].values() if "A14_hub_lineage_withdrawer" in v["roles"]]
        if len(a14) == aset["counts"]["A14"] and all(x is not None for x in a14):
            m["unstakers_a14_n"] = len(a14)
            m["unstakers_a14_net_outflow_m"] = r(-sum(a14) / 1e6, 2)
            m["unstakers_a14_share_of_net_outflow_pct"] = r(-sum(a14) / pool_net_out * 100, 1)

    # ---------- 1Click fee take over time (three 30-day blocks; Explorer API) ----------
    if (RAW / "explorer" / "daily.json").exists():
        take_over_time(m, rev, vol["near-intents"], asof)

    # ---------- Per-swap fee evidence (in-window sample, re-checkable on chain) ----------
    if (RAW / "evidence" / "fee_sample_onchain.json").exists():
        fee_evidence(m)

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
        "l1_daily": l1_daily,
    }
    return m, series


def main(argv: list[str] | None = None) -> int:
    # No arguments: --help prints the usage and exits 0 before anything is computed or written, an unknown one exits 2.
    argparse.ArgumentParser(prog="python3 -m pipeline.compute", description="Recompute data/metrics.json and data/series.json "
                            "from data/raw/, offline. Takes no arguments.").parse_args(argv)
    m, series = build()
    METRICS.write_text(json.dumps(m, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (DATA / "series.json").write_text(json.dumps(series, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {METRICS.relative_to(DATA.parent)} ({len(m)} metrics, as of {m['asof']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
