"""NEAR market structure from Binance's public endpoints (spot daily candles, perpetual funding, open interest and the
long/short ratio), with ETH, SOL and BTC for relative performance. No key. Binance blocks some countries (HTTP 451);
run it from an unrestricted region.

Run: python3 -m pipeline.fetch_market
"""
from __future__ import annotations

import time

from .common import http_json, write_raw

SPOT = "https://api.binance.com/api/v3"
FUT = "https://fapi.binance.com"
START_MS = 1_601_510_400_000  # 2020-10-01, the month NEAR listed


def klines(symbol: str) -> list[list]:
    out, start = [], START_MS
    while True:
        page = http_json(f"{SPOT}/klines", {"symbol": symbol, "interval": "1d", "startTime": start, "limit": 1000})
        if not page:
            return out
        out += page
        start = page[-1][6] + 1
        if len(page) < 1000:
            return out
        time.sleep(0.5)


def main() -> None:
    cols = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "trades", "taker_buy_base", "taker_buy_quote"]
    for sym in ("NEARUSDT", "ETHUSDT", "SOLUSDT", "BTCUSDT"):
        rows = klines(sym)
        write_raw(f"market/spot_{sym.lower()}_1d.json", {"columns": cols, "rows": [r[:11] for r in rows]}, f"binance spot klines {sym} 1d")
        time.sleep(0.5)
    write_raw("market/futures_funding_nearusdt.json", http_json(f"{FUT}/fapi/v1/fundingRate", {"symbol": "NEARUSDT", "limit": 1000}), "binance futures fundingRate NEARUSDT")
    write_raw("market/futures_oi_nearusdt_1d.json", http_json(f"{FUT}/futures/data/openInterestHist", {"symbol": "NEARUSDT", "period": "1d", "limit": 30}), "binance futures openInterestHist NEARUSDT")
    write_raw("market/futures_longshort_nearusdt_1d.json", http_json(f"{FUT}/futures/data/globalLongShortAccountRatio", {"symbol": "NEARUSDT", "period": "1d", "limit": 30}), "binance futures globalLongShortAccountRatio NEARUSDT")
    print("market: done")


if __name__ == "__main__":
    main()
