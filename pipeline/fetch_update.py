"""Fetch the keyless inputs of the update to 2026-11-13 (exploratory, 2026-11-14, after F1-F4 were scored).

The analysis stops at 2026-11-04, the pre-registered cutoff, and its snapshots stay as committed. This fetcher writes fresh copies
of the keyless series under data/raw/update/ and records them in data/MANIFEST.json; pipeline/update.py computes the upd_* metrics
from them, to the last full UTC day before the score (2026-11-13). Same endpoints and the same kept fields as pipeline/fetch_keyless.py
and pipeline/fetch_peer_caps.py:

  DefiLlama   summary/dexs/<slug>?dataType=dailyVolume and summary/fees/<slug>?dataType=dailyFees for the four peer-set venues,
              summary/fees/near-intents?dataType=dailyRevenue
  Nearblocks  /v1/charts (daily total supply)
  CoinGecko   coins/near/market_chart (365 days, daily) and coins/<id>/market_chart (30 days) for NEAR, RUNE and FLIP

Run: python3 -m pipeline.fetch_update
"""
from __future__ import annotations

import time

from .common import http_json, write_raw
from .fetch_keyless import PEERS, llama_summary
from .fetch_peer_caps import COINS

CG = "https://api.coingecko.com/api/v3"
DIR = "update"


def main() -> int:
    for slug in PEERS:
        write_raw(f"{DIR}/llama/volume_{slug}.json", llama_summary("dexs", slug, "dailyVolume"),
                  f"https://api.llama.fi/summary/dexs/{slug}?dataType=dailyVolume")
        write_raw(f"{DIR}/llama/fees_{slug}.json", llama_summary("fees", slug, "dailyFees"),
                  f"https://api.llama.fi/summary/fees/{slug}?dataType=dailyFees")
    write_raw(f"{DIR}/llama/dailyRevenue_near-intents.json", llama_summary("fees", "near-intents", "dailyRevenue"),
              "https://api.llama.fi/summary/fees/near-intents?dataType=dailyRevenue")
    print("ok    defillama")
    write_raw(f"{DIR}/nearblocks/charts.json", http_json("https://api.nearblocks.io/v1/charts"), "https://api.nearblocks.io/v1/charts")
    print("ok    nearblocks")
    hist = http_json(f"{CG}/coins/near/market_chart", {"vs_currency": "usd", "days": "365", "interval": "daily"})
    write_raw(f"{DIR}/coingecko/near_market_chart_365d.json", hist, f"{CG}/coins/near/market_chart?vs_currency=usd&days=365&interval=daily")
    caps = {}
    for slug, coin in COINS.items():
        time.sleep(15)  # keyless rate limit
        d = http_json(f"{CG}/coins/{coin}/market_chart", {"vs_currency": "usd", "days": "30"})
        caps[slug] = {"coingecko_id": coin, "prices": d["prices"], "market_caps": d["market_caps"]}
    write_raw(f"{DIR}/coingecko/peer_caps_30d.json", caps,
              f"{CG}/coins/<id>/market_chart?vs_currency=usd&days=30 for {', '.join(COINS.values())}")
    print("ok    coingecko")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
