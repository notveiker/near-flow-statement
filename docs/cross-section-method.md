# Cross-section of fee-sharing tokens: method and fetcher, fixed before any held protocol is fetched

Committed 2026-11-13 02:17 UTC (2026-11-13). **Order of work, enforced in code:** (1) the forward tests F1 to F4 are scored first (`python3 -m pipeline.score_forward --score`, which refuses to run before 2026-11-14 00:00 UTC); (2) only then is anything fetched for `near-intents`, `thorchain-dex`, `chainflip-amm` or `maya-protocol`. `pipeline/fetch_cross_section.py` raises on those four slugs unless the real score result exists on disk and the clock is past 2026-11-14 00:00 UTC; nothing has been fetched for them under this method. (The earlier `pipeline/fetch_peers.py` run for the same four is older and is not used here.)

## Window
30 complete UTC days, **2026-10-15 to 2026-11-13**. This overlaps the forward-test window (11-06 to 11-13) by design; because the scoring runs first and the cross-section cannot change F1 to F4, that is allowed. The data cutoff of the Intents rebuild (2026-11-04) does not apply to this analysis.

## Cohort
Tier 1, the four cross-chain swap venues (fetch held): NEAR Intents (`near-intents`, token NEAR), THORChain (`thorchain-dex`, RUNE), Chainflip (`chainflip-amm`, FLIP), Maya (`maya-protocol`, CACAO). Tier 2, comparators with a fee-sharing token (fetch allowed now). **A comparator is in the cohort only if its table entry carries a citation for the fee-sharing mechanism** (buyback, burn, staking distribution or vote-escrow) that was found before its numbers were seen; an entry without one is excluded, not guessed. The candidates listed in `COMPARATORS` have **citations pending**, so the fetcher includes none of them yet; a slug DefiLlama does not know is recorded as missing, never replaced.

## Metrics (per protocol, over the window)
1. **Capture ratio** = sum of DefiLlama `dailyHoldersRevenue` (USD) / USD value of net new token supply, where net new supply = circulating supply at the end minus at the start (CoinGecko market cap / price on the first and last day), valued at the window's mean daily price. If the supply fell (net burn) the protocol is reported as `net_burn` and ranked above every finite ratio. For NEAR Intents the repo's measured-wallet figure (`PREREG.md`) is reported next to the DefiLlama one, and the DefiLlama one is used for the ranking (same basis for all).
2. **Revenue over fees** = sum of `dailyRevenue` / sum of `dailyFees`.
3. **Partner share** = affiliate, broker or integrator fees / gross fees, for the four swap venues only, from each venue's own public series (the source for each is written into the output at fetch time and has to be reachable without a key; if it is not, the value is `null`, never estimated). Tier 2 is `n/a`.

## Hypotheses (directional, written to fail; none changes `PREREG.md`'s rating rule)
- **H-X1:** NEAR Intents' capture ratio is in the bottom half of the protocols with a defined ratio. **Falsified** if it is in the top third. Needs at least 6 protocols with a defined ratio, else "not scorable".
- **H-X2:** NEAR Intents' revenue over fees is below the cohort median. **Falsified** if it is above the 60th percentile.
- **H-X3:** among the four swap venues NEAR Intents has the highest partner share. **Falsified** if it is not in the top two. Needs at least 3 of the 4 with a non-null partner share.
- Rules: missing days make a protocol "not scorable" for that metric (no fill); every result is published, including misses; ties share the better rank.

## Fetcher
`python3 -m pipeline.fetch_cross_section` fetches Tier 2 only. `python3 -m pipeline.fetch_cross_section --held` adds the four, and refuses unless the guard passes. Per-protocol DefiLlama endpoints (`/summary/fees/{slug}?dataType=`) are used, **not** the all-protocol overview, because the overview payload contains the four held protocols. Every fetch is saved to `data/raw/cross_section/` with SHA-256 and fetch time.
