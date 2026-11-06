"""Fetch every keyless source into data/raw/ and record it in data/MANIFEST.json.

Sources (no API keys needed):
  - DefiLlama: NEAR Intents volume, fees, revenue, holders revenue; NEAR chain fees;
    cross-chain swap peers (THORChain, Chainflip, Maya) volume and fees.
  - Nearblocks /v1/charts: daily txns, active accounts, total supply, fees.
  - CoinGecko: NEAR price history (365 days) and a current market snapshot.
  - NEAR JSON-RPC (FastNEAR): final block, protocol config, validators, revenue/treasury wallets.

Run: python3 -m pipeline.fetch_keyless
"""
from __future__ import annotations

import sys

from .common import http_json, write_raw

LLAMA = "https://api.llama.fi"
RPCS = [
    "https://rpc.mainnet.fastnear.com",
    "https://free.rpc.fastnear.com",
    "https://rpc.mainnet.near.org",
]

# Native cross-chain swap venues compared with NEAR Intents (DefiLlama slugs).
PEERS = ["near-intents", "thorchain-dex", "chainflip-amm", "maya-protocol"]

# Accounts that receive NEAR Intents revenue or protocol issuance.
WALLETS = [
    "buybacks.multisignature.near",    # NEAR buyback multisig (bought NEAR is held here)
    "1csfundsadmin.sputnik-dao.near",  # 1Click fee collection (sweeps into buybacks)
    "fefundsadmin.sputnik-dao.near",   # near-intents.org front-end fee fund
    "treasury.near",                   # protocol treasury (~10% of issuance)
    "intents.near",                    # NEAR Intents verifier contract
]


def llama_summary(kind: str, slug: str, data_type: str) -> dict:
    d = http_json(f"{LLAMA}/summary/{kind}/{slug}",
                  {"dataType": data_type, "excludeTotalDataChartBreakdown": "true"})
    keep = ("name", "slug", "methodology", "totalDataChart", "total24h", "total30d",
            "total1y", "totalAllTime", "chains")
    return {k: d.get(k) for k in keep if k in d}


def rpc(method: str, params) -> dict:
    last = None
    for url in RPCS:
        try:
            r = http_json(url, body={"jsonrpc": "2.0", "id": "nfs", "method": method, "params": params},
                          retries=3)
            if "result" in r:
                return r["result"]
            last = r.get("error")
        except RuntimeError as exc:
            last = exc
    raise RuntimeError(f"rpc {method} failed on all endpoints: {last}")


def fetch_llama() -> None:
    for slug in PEERS:
        write_raw(f"llama/volume_{slug}.json", llama_summary("dexs", slug, "dailyVolume"),
                  f"{LLAMA}/summary/dexs/{slug}?dataType=dailyVolume")
        write_raw(f"llama/fees_{slug}.json", llama_summary("fees", slug, "dailyFees"),
                  f"{LLAMA}/summary/fees/{slug}?dataType=dailyFees")
    for dt in ("dailyRevenue", "dailyHoldersRevenue"):
        write_raw(f"llama/{dt}_near-intents.json", llama_summary("fees", "near-intents", dt),
                  f"{LLAMA}/summary/fees/near-intents?dataType={dt}")
    write_raw("llama/chainfees_near.json", llama_summary("fees", "near", "dailyFees"),
              f"{LLAMA}/summary/fees/near?dataType=dailyFees")


def fetch_nearblocks() -> None:
    d = http_json("https://api.nearblocks.io/v1/charts")
    write_raw("nearblocks/charts.json", d, "https://api.nearblocks.io/v1/charts")


def fetch_coingecko() -> None:
    cg = "https://api.coingecko.com/api/v3"
    hist = http_json(f"{cg}/coins/near/market_chart", {"vs_currency": "usd", "days": "365", "interval": "daily"})
    write_raw("coingecko/near_market_chart_365d.json", hist,
              f"{cg}/coins/near/market_chart?vs_currency=usd&days=365&interval=daily")
    snap = http_json(f"{cg}/coins/near", {"localization": "false", "tickers": "false",
                                          "community_data": "false", "developer_data": "false"})
    md = snap["market_data"]
    keep = {
        "last_updated": snap.get("last_updated"),
        "price_usd": md["current_price"]["usd"],
        "market_cap_usd": md["market_cap"]["usd"],
        "fdv_usd": md["fully_diluted_valuation"]["usd"],
        "circulating_supply": md["circulating_supply"],
        "total_supply": md["total_supply"],
    }
    write_raw("coingecko/near_snapshot.json", keep, f"{cg}/coins/near")


MAJORS = ["bitcoin", "ethereum", "solana", "zcash", "tron", "ripple", "binancecoin", "litecoin", "dogecoin"]


def fetch_coingecko_majors() -> None:
    """Daily USD prices (90 days) for the non-stablecoin tokens that reach NEAR's fee collectors."""
    import time
    cg = "https://api.coingecko.com/api/v3"
    out = {}
    for coin in MAJORS:
        out[coin] = http_json(f"{cg}/coins/{coin}/market_chart",
                              {"vs_currency": "usd", "days": "90", "interval": "daily"})["prices"]
        time.sleep(15)  # keyless rate limit (~5 calls/min)
    write_raw("coingecko/majors_90d.json", out, f"{cg}/coins/<coin>/market_chart?vs_currency=usd&days=90&interval=daily")


def fetch_rpc() -> None:
    block = rpc("block", {"finality": "final"})
    hdr = block["header"]
    write_raw("rpc/final_block.json",
              {"height": hdr["height"], "timestamp_ns": hdr["timestamp"], "total_supply": hdr["total_supply"],
               "epoch_id": hdr["epoch_id"], "gas_price": hdr["gas_price"]},
              "rpc block {finality: final}")
    cfg = rpc("EXPERIMENTAL_protocol_config", {"finality": "final"})
    rt = cfg.get("runtime_config", {})
    tc = rt.get("transaction_costs", {})
    write_raw("rpc/protocol_config.json", {
        "protocol_version": cfg.get("protocol_version"),
        "max_inflation_rate": cfg.get("max_inflation_rate"),
        "protocol_reward_rate": cfg.get("protocol_reward_rate"),
        "num_blocks_per_year": cfg.get("num_blocks_per_year"),
        "epoch_length": cfg.get("epoch_length"),
        "burnt_gas_reward": tc.get("burnt_gas_reward"),
        "storage_amount_per_byte": rt.get("storage_amount_per_byte"),
        "num_shards": len(cfg.get("shard_layout", {}).get("V2", cfg.get("shard_layout", {}).get("V3", {})).get("shard_ids", []) or []),
        "at_block": hdr["height"],
    }, "rpc EXPERIMENTAL_protocol_config {finality: final}")
    vals = rpc("validators", [None])
    cur = vals["current_validators"]
    write_raw("rpc/validators.json", {
        "epoch_height": vals.get("epoch_height"),
        "count": len(cur),
        "stakes": sorted(((v["account_id"], v["stake"]) for v in cur), key=lambda x: -int(x[1])),
        "at_block": hdr["height"],
    }, "rpc validators [null]")
    accts = {}
    for a in WALLETS:
        r = rpc("query", {"request_type": "view_account", "block_id": hdr["height"], "account_id": a})
        accts[a] = {"amount": r["amount"], "locked": r["locked"], "storage_usage": r["storage_usage"]}
    write_raw("rpc/wallets.json", {"at_block": hdr["height"], "accounts": accts},
              f"rpc view_account at block {hdr['height']}")


def main(argv: list[str]) -> int:
    steps = [("defillama", fetch_llama), ("nearblocks", fetch_nearblocks),
             ("coingecko", fetch_coingecko), ("coingecko_majors", fetch_coingecko_majors), ("rpc", fetch_rpc)]
    if argv:  # e.g. `python3 -m pipeline.fetch_keyless coingecko_majors` refreshes one source only
        steps = [s for s in steps if s[0] in argv]
    failed = []
    for name, fn in steps:
        try:
            fn()
            print(f"ok    {name}")
        except Exception as exc:  # keep going; the previous snapshot stays in place
            failed.append(name)
            print(f"FAIL  {name}: {exc}", file=sys.stderr)
    if failed:
        print(f"{len(failed)} source(s) failed; their previous snapshots were kept: {failed}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
