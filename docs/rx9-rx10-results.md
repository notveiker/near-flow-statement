# RX9 and RX10 results: what the public Intents swaps are made of, and how big they are

Rules and falsifiers: [rx9-rx10-method.md](rx9-rx10-method.md), committed `d2b923c` (06:46:20 UTC, 2026-11-13) before the query ran (06:46:25 UTC). Query `sql/rx/rx9_rx10_mix.sql` on the staged tables (20.2 GB billed), job `ask_rx9_rx10_mix_20261113T064625Z`; the output was first written to a wrong folder by a path typo, so the same query was run a second time into `data/raw/rx/` (job `ask_rx9_rx10_mix_20261113T064652Z`, served from cache, 0 bytes billed); the two outputs have the same SHA-256 (`a72e765d…`). The stray copy was deleted. Numbers are computed by `python3 -m pipeline.rx_analysis` into `data/derived/rx_results.json` (keys `rx9`, `rx10`).

Population: 1,155,239 public simple swaps with a priced leg, $2.171B (the rebuild's Q4 figure, $2.17B, reproduced). Not included: complex receipts, confidential swaps and unpriced tokens, so every share below is a share of this population.

Disclosure on thresholds: they were written after the rebuild's Q4, FU11 and RX1 results were known, which showed that stable-to-stable swaps were common and that small swaps dominate in count. The thresholds were set before this query ran; the sizes of the shares were not known.

## Results

| Hypothesis | Rule (committed) | Result | Verdict |
|---|---|---|---|
| H-RX9a stable-heavy | stable-to-stable ≥ 50% of volume (falsified < 25%) | 52.3% (stable-to-volatile 38.1%, volatile-to-volatile 9.6%) | supported, narrowly |
| H-RX9b few routes | top 5 symbol pairs ≥ 50% (falsified < 30%) | 63.1% | supported |
| H-RX9c NEAR is a minor leg | NEAR or wNEAR on either side ≤ 10% (falsified > 25%) | 1.5% (66,410 swaps) | supported |
| H-RX9d cross-chain | tokens on different chains ≥ 70% (falsified < 40%) | 90.2% | supported |
| H-RX10a retail-size tail | median under $1,000 (falsified > $5,000) | median $99 | supported |
| H-RX10b big swaps carry the dollars | ≥ $100K swaps under 1% of swaps and ≥ 30% of volume (falsified < 15%) | 0.24% of swaps (2,825), 30.2% of volume | supported, narrowly (0.2 points above the line) |
| H-RX10c no day dominates | largest day under 5% (falsified > 10%) | 2.3% (2026-09-21, $49.7M, 19,313 swaps) | supported |

## What the mix looks like

- **The top pairs** (share of priced volume): USDT/USDT 26.5%, USDC/USDT 13.9%, BTC/USDT 12.9%, USDT/USDT(DEPRECATED) 5.2%, ETH/USDT 4.7%, BTC/USDC 4.6%, USDT/ZEC 4.2%, USDC/USDC 3.7%, ETH/USDC 2.5%, USDC/ZEC 2.2%. The top-25 list with swaps and shares is in `rx_results.json`.
- **Post hoc (not pre-registered):** pairs with the same symbol on both sides (USDT/USDT, USDC/USDC, ETH/ETH and the deprecated variants) are **36.7% of priced volume**. That is a stablecoin or ETH moved from one chain to another through Intents, a bridge-like use; whether the two sides are always on different chains was not checked row by row (the pair table's maximum chain count is 2).
- **Post hoc:** ZEC appears in three of the top ten pairs (USDT/ZEC, USDC/ZEC, then ETH/ZEC and BTC/ZEC in the next five), about 9% of volume in the top 15 pairs.
- **Post hoc:** the stable-to-stable share by 7-day block from 2026-08-07 is 63%, 64%, 50%, 64%, 56%, 58%, 46%, 49%, 45%, 50%, 43%, 47%, 50%: it drifts down by roughly 15 points from the first block to the last three blocks. One quarter of data, so this is a pattern, not a trend.

## What the sizes look like

| Size | Share of swaps | Share of volume |
|---|---|---|
| under $100 | 50.6% | 0.6% |
| $100 to 1K | 35.2% | 5.1% |
| $1K to 10K | 11.1% | 21.3% |
| $10K to 100K | 2.9% | 42.7% |
| $100K to 1M | 0.24% | 29.8% |
| $1M or more | 8 swaps | 0.4% |

- Percentiles: p10 $2, p25 $11, p50 $99, p75 $296, p90 $2,000, p99 $32.7K, p99.9 $199.8K.
- **The dollars sit in the 3% of swaps above $10K** (72.9% of volume), while half of all swaps are under $100 and carry 0.6%. A revenue rate in bp on this volume therefore depends on how the fee is applied to the large swaps, not on the count of users or swaps.
- Post hoc: five of the ten largest swaps are within 0.3% of $1.0M (the largest is $2.17M); round-sized orders are an INFERENCE, not shown.
- Largest days: 2026-09-21 2.3%, 2026-10-09 2.2%, 2026-09-17 2.1%.

## What this does not show

Volume of public swaps with priced legs only; complex receipts (FU3: +62% when anchored) and confidential swaps are absent. A share of volume is not a share of NEAR's revenue (FU4 and FU5 trace the wallets). Solver and user sides are inferred. The mix shows what is routed, not why; no causal reading is drawn. Two of the verdicts (RX9a and RX10b) pass by less than 3 points and 0.2 points, so a small change in the pricing or the bucket rule could flip them.
