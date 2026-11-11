"""Third-party facts with the exact sentence that supports each one, checked against the live page.

Every entry names a URL and a quotation. `fetch` downloads the page, normalises whitespace and fails the entry if the
quotation is not found, so a fact cannot drift from its source without the build noticing. The committed file records
the SHA-256 of each page as fetched, the retrieval time and the quotation. Pages change, so the hash is evidence of
what was read, not something a later run is expected to match; `verify` re-checks only that each quotation is still on
its page.

    python3 -m pipeline.fetch_web_facts fetch
    python3 -m pipeline.fetch_web_facts verify
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import urllib.request

from .common import RAW, utc_now, write_raw

UA = "Mozilla/5.0 (research; github.com/notveiker/near-flow-statement)"

BITWISE = "https://bitwiseinvestments.com/newsroom/the-bitwise-near-etf-nrr-launches-as-first-spot-near-etp-in-the-us"
NANSEN = "https://nansen.ai/post/near-q3-2026-report"
BRAVE = "https://brave.com/blog/near-intents/"
ETFTODAY = "https://cryptoetf.today/en/crypto-etf-filings/coin/near"

FACTS = [
    ("etf_launch", "A spot NEAR ETF trades on NYSE Arca", BITWISE, "today announced the launch of the Bitwise NEAR ETF (NYSE: NRR)"),
    ("etf_date", "The ETF began trading on 29 September 2026", BITWISE, "The Bitwise NEAR ETF will trade on NYSE Arca starting on September 29, 2026, with the ticker NRR"),
    ("etf_fee", "The ETF's management fee is 0.75%", BITWISE, "The management fee will be 0.75%"),
    ("etf_staking", "The ETF stakes its NEAR", BITWISE, "Bitwise intends to stake the Fund"),
    ("etf_first_us", "It is the first spot NEAR ETP in the US", BITWISE, "Launches as First Spot NEAR ETP in the U.S."),
    ("etf_tracker", "Independent tracker lists one approved NEAR ETF", ETFTODAY, "One NEAR ETF trades in the US."),
    ("conf_tvl", "Confidential Intents TVL near $160M at the end of Q3 2026", NANSEN, "Confidential Intents TVL reached approximately $160 million at quarter-end."),
    ("q3_volume", "Intents processed about $10.4B in Q3 2026", NANSEN, "Intents processed approximately $10.4 billion in quarterly volume"),
    ("nearcom_volume", "near.com handled about a quarter of Intents volume in Q3", NANSEN, "near.com processed approximately $2.57 billion in Q3 volume, accounting for roughly one quarter of total Intents volume."),
    ("nearcom_staked", "About 5M NEAR staked through near.com", NANSEN, "approximately 5 million NEAR was staked through the platform"),
    ("ai_staking", "More than 750,000 NEAR staked for NEAR AI inference", NANSEN, "More than 750,000 NEAR has already been staked for inference."),
    ("fee_capture", "Nansen's lifetime fee-capture estimate", NANSEN, "lifetime fee capture stood at approximately 16.4%"),
    ("fee_capture_30d", "Nansen's trailing 30-day capture estimate", NANSEN, "Trailing 30-day capture was 28.4%"),
    ("zec_settled", "More than $2.6B in ZEC settled across Intents before Confidential Intents' general availability", NANSEN, "more than $2.6B in ZEC settled across NEAR Intents"),
    ("brave_volume", "Intents had executed 19M swaps and $14B across 35 chains by March 2026", BRAVE, "executed over 19 million swaps and over $14 billion in all-time volume across 35 chains"),
]


def norm(s: str) -> str:
    s = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", s)
    s = html.unescape(re.sub(r"(?s)<[^>]+>", " ", s))
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", s).strip()


def get(url: str) -> tuple[str, str]:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
        raw = r.read()
    return hashlib.sha256(raw).hexdigest(), norm(raw.decode("utf-8", "replace"))


def run(write: bool) -> int:
    pages: dict[str, tuple[str, str]] = {}
    out, bad = [], 0
    for fid, claim, url, quote in FACTS:
        if url not in pages:
            pages[url] = get(url)
        sha, text = pages[url]
        ok = norm(quote) in text
        bad += not ok
        out.append({"id": fid, "claim": claim, "url": url, "quote": quote, "found": ok, "page_sha256": sha})
        print(("ok   " if ok else "MISS ") + fid)
    if write and not bad:
        write_raw("web/third_party_facts.json", {"retrieved_utc": utc_now(), "facts": out}, "; ".join(sorted({f[2] for f in FACTS})))
    return 1 if bad else 0


def main(argv=None) -> int:
    cmd = (argv or sys.argv[1:] or ["verify"])[0]
    return run(write=(cmd == "fetch"))


if __name__ == "__main__":
    sys.exit(main())
