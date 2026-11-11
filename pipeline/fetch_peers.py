"""Protocol revenue and token market caps for NEAR Intents and the other native cross-chain venues (keyless).

DefiLlama `dailyRevenue` is the share of fees a protocol keeps for itself or its token; for the peers it is not the same
quantity as NEAR's captured revenue wallets, which pipeline/compute.py reconciles separately. Market caps are CoinGecko
spot values at fetch time.

    python3 -m pipeline.fetch_peers
Output: data/raw/peers/revenue.json, data/raw/peers/market_caps.json
"""
from __future__ import annotations

import sys

from .common import http_json, utc_now, write_raw

VENUES = {"near-intents": "NEAR Intents", "thorchain-dex": "THORChain", "chainflip-amm": "Chainflip", "maya-protocol": "Maya"}
TOKENS = ["near", "thorchain", "chainflip", "cacao"]


def main() -> int:
    rev = {}
    for slug in VENUES:
        row = {}
        for dt in ("dailyRevenue", "dailyHoldersRevenue", "dailyFees"):
            d = http_json(f"https://api.llama.fi/summary/fees/{slug}", params={"dataType": dt})
            row[dt] = [[t, v] for t, v in d["totalDataChart"][-400:]]
        rev[slug] = row
        print(slug, {k: round(sum(v for _, v in r[-30:]) / 1e6, 2) for k, r in row.items()})
    write_raw("peers/revenue.json", {"venues": VENUES, "series": rev, "fetched_utc": utc_now()}, "https://api.llama.fi/summary/fees/{slug}?dataType=")
    mc = http_json("https://api.coingecko.com/api/v3/coins/markets", params={"vs_currency": "usd", "ids": ",".join(TOKENS), "per_page": 10})
    write_raw("peers/market_caps.json", {"fetched_utc": utc_now(), "coins": [{k: x[k] for k in ("id", "symbol", "current_price", "market_cap", "fully_diluted_valuation")} for x in mc]},
              "https://api.coingecko.com/api/v3/coins/markets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
