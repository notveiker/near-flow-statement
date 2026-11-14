"""Fetch the market caps of NEAR and of the peer venues' tokens, for the peer valuation of the forward view (exploratory, 2026-11-14).

CoinGecko /coins/{id}/market_chart, 30 days (hourly points), keyless. Writes data/raw/coingecko/peer_caps_30d.json and records it
in data/MANIFEST.json. The comparison reads the point nearest NEAR's committed snapshot (coingecko/near_snapshot.json), so every
market cap is from the same hour.

Peers: THORChain (RUNE) and Chainflip (FLIP). Maya Protocol's token (CACAO) is not listed on CoinGecko (its search for "cacao" and
"maya" returned no CACAO on 2026-11-14), so Maya is left out of the valuation and kept in the volume and fee series.

Run: python3 -m pipeline.fetch_peer_caps
"""
from __future__ import annotations

import time

from .common import http_json, write_raw

CG = "https://api.coingecko.com/api/v3"
COINS = {"near-intents": "near", "thorchain-dex": "thorchain", "chainflip-amm": "chainflip"}   # DefiLlama slug -> CoinGecko id


def main() -> int:
    out = {}
    for slug, coin in COINS.items():
        d = http_json(f"{CG}/coins/{coin}/market_chart", {"vs_currency": "usd", "days": "30"})
        out[slug] = {"coingecko_id": coin, "prices": d["prices"], "market_caps": d["market_caps"]}
        time.sleep(15)  # keyless rate limit
    write_raw("coingecko/peer_caps_30d.json", out, f"{CG}/coins/<id>/market_chart?vs_currency=usd&days=30 for {', '.join(COINS.values())}")
    print("ok    coingecko peer caps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
