"""Token metadata and daily USD prices for the leg-count check (exploratory, 2026-11-13; docs/leg-count.md).

sql/leg_count_days.sql sums intents.near token_diff and treasury transfer amounts per day and token, in raw units,
for 2026-08-18, 08-31, 09-02, 10-08 and 10-22. This fetcher writes what pipeline/compute.py (leg_count) needs to
price them: each token's decimals and CoinGecko id (from the 1Click token list; its current prices are dropped), and
each CoinGecko id's USD price at 00:00 UTC of each of the five days. The prices come from DefiLlama's keyless coins
API, which serves CoinGecko prices under "coingecko:<id>" and answers one request per day for every id (CoinGecko's
own keyless tier allows a few calls a minute). Each request asks for one timestamp, 00:00 UTC of a day dated
2026-10-22 or earlier, within two hours; nothing later is fetched. Keyless.

Run: python3 -m pipeline.fetch_leg_count   (needs data/raw/bq/leg_count_days.json)
"""
from __future__ import annotations

import datetime as dt
import sys

from .common import http_json, read_raw, write_raw

TOKENS = "https://1click.chaindefuser.com/v0/tokens"
COINS = "https://coins.llama.fi/prices/historical"
DAYS = ["2026-08-18", "2026-08-31", "2026-09-02", "2026-10-08", "2026-10-22"]
UA = "research-script/0.1"  # generic: no repository or owner name in third-party requests


def main(argv: list[str]) -> int:
    used = {r["token"] for r in read_raw("bq/leg_count_days.json")}
    meta = {t["assetId"]: {"decimals": t["decimals"], "symbol": t.get("symbol"), "coingeckoId": t.get("coingeckoId")}
            for t in http_json(TOKENS, user_agent=UA) if t.get("assetId") in used}
    ids = sorted({m["coingeckoId"] for m in meta.values() if m["coingeckoId"]})
    prices: dict[str, dict[str, float]] = {}
    for d in DAYS:
        ts = int(dt.datetime.fromisoformat(d + "T00:00:00+00:00").timestamp())
        assert d <= "2026-10-22"
        got = http_json(f"{COINS}/{ts}/" + ",".join(f"coingecko:{i}" for i in ids),
                        {"searchWidth": "2h"}, user_agent=UA)["coins"]
        for key, v in got.items():
            if abs(int(v["timestamp"]) - ts) <= 2 * 3600:
                prices.setdefault(key.split(":", 1)[1], {})[d] = float(v["price"])
        print(f"  {d}: {len(got)} of {len(ids)} ids priced", flush=True)
    write_raw("coingecko/leg_count_prices.json", {"days": DAYS, "tokens": meta, "prices": prices},
              f"{TOKENS} (decimals and coingeckoId only) + {COINS}/<00:00 UTC of each day>/coingecko:<id>,...?searchWidth=2h")
    print(f"ok    {len(meta)} of {len(used)} tokens listed, {len(prices)} of {len(ids)} CoinGecko ids priced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
