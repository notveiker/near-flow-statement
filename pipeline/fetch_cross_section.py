"""Cross-section of fee-sharing tokens (docs/cross-section-method.md). Fetches per-protocol DefiLlama fee series and CoinGecko price/market-cap
series for the 30-day window 2026-10-15..2026-11-13.

The four swap venues in HELD are refused unless (a) the real forward scoring has run (data/forward/score_*/result.json exists), (b) the clock is
at or after 2026-11-14 00:00 UTC and (c) --held is passed. Nothing is fetched from the all-protocol overview endpoints (they contain the held
protocols). Comparators are fetched only if they carry a citation for their fee-sharing mechanism.

    python3 -m pipeline.fetch_cross_section            # comparators with a citation (none yet)
    python3 -m pipeline.fetch_cross_section --held     # after scoring: adds the four venues
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from .common import ROOT, http_json, utc_now, write_raw

WINDOW = ("2026-10-15", "2026-11-13")
UNLOCK = datetime(2026, 11, 14, 0, 0, tzinfo=timezone.utc)
HELD = {"near-intents": "near", "thorchain-dex": "thorchain", "chainflip-amm": "chainflip", "maya-protocol": "cacao"}
DATATYPES = ("dailyFees", "dailyRevenue", "dailyHoldersRevenue")
# Candidates only: `mechanism_source` must be filled with a citation found before the numbers are seen, or the entry is excluded.
COMPARATORS = [
    {"slug": "aave", "gecko": "aave", "mechanism_source": None},
    {"slug": "uniswap", "gecko": "uniswap", "mechanism_source": None},
    {"slug": "pendle", "gecko": "pendle", "mechanism_source": None},
    {"slug": "lido", "gecko": "lido-dao", "mechanism_source": None},
    {"slug": "gmx", "gecko": "gmx", "mechanism_source": None},
    {"slug": "curve-dex", "gecko": "curve-dao-token", "mechanism_source": None},
    {"slug": "jupiter-aggregator", "gecko": "jupiter-exchange-solana", "mechanism_source": None},
    {"slug": "raydium", "gecko": "raydium", "mechanism_source": None},
]


def scoring_has_run() -> bool:
    return any(ROOT.glob("data/forward/score_*/result.json"))


def assert_allowed(slug: str, now: datetime | None = None, held_flag: bool = False) -> None:
    if slug in HELD:
        now = now or datetime.now(timezone.utc)
        if not held_flag:
            raise PermissionError(f"{slug} is held: pass --held after scoring")
        if now < UNLOCK:
            raise PermissionError(f"{slug} is held until {UNLOCK.isoformat()}")
        if not scoring_has_run():
            raise PermissionError(f"{slug} is held until the forward scoring result exists (data/forward/score_*/result.json)")


def fetch_one(slug: str, gecko: str, source: str | None) -> dict:
    row = {"slug": slug, "gecko": gecko, "mechanism_source": source, "fetched_utc": utc_now()}
    for dt in DATATYPES:
        d = http_json(f"https://api.llama.fi/summary/fees/{slug}", params={"dataType": dt})
        row[dt] = [[t, v] for t, v in d["totalDataChart"][-60:]]
    mc = http_json(f"https://api.coingecko.com/api/v3/coins/{gecko}/market_chart", params={"vs_currency": "usd", "days": 45, "interval": "daily"})
    row["prices"], row["market_caps"] = mc["prices"], mc["market_caps"]
    return row


def main(argv: list[str]) -> int:
    held_flag = "--held" in argv
    todo = [(c["slug"], c["gecko"], c["mechanism_source"]) for c in COMPARATORS if c["mechanism_source"]]
    skipped = [c["slug"] for c in COMPARATORS if not c["mechanism_source"]]
    if held_flag:
        todo += [(s, g, "swap venue (Tier 1)") for s, g in HELD.items()]
    for slug, _, _ in todo:
        assert_allowed(slug, held_flag=held_flag)
    print(f"fetching {[t[0] for t in todo]}; excluded for lack of a citation: {skipped}")
    rows = []
    for slug, gecko, src in todo:
        rows.append(fetch_one(slug, gecko, src))
        print("ok", slug)
    if rows:
        write_raw("cross_section/" + ("all.json" if held_flag else "comparators.json"), {"window": WINDOW, "rows": rows}, "api.llama.fi per-protocol fees + CoinGecko market_chart")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
