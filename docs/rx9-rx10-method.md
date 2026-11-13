# RX9 and RX10: what the public Intents swaps are made of, and how big they are: method fixed before the query runs

Committed 2026-11-13 (UTC time in the addendum entry). NEAR-only follow-ups to the frozen rebuild (tag `rebuild-frozen`); separate files, labelled RX so they do not collide with the forward tests F1 to F4 or the rebuild's FU labels. Data cutoff 2026-11-04, block 223,088,015, enforced in code. Inputs are the staged BigQuery tables `swaps`, `swaps_solver`, `intents_events`, `tokens`, `prices` (personal project, dataset `nfs_rebuild`), so the query reads megabytes, not terabytes. The query is `sql/rx/rx9_rx10_mix.sql`; the analysis is `pipeline/rx_analysis.py` (`rx9`, `rx10`).

Scope, stated up front: **public simple swaps only** (exactly two `token_diff` legs from two accounts, the Q3/Q4 definition), priced by the rebuild's rule (stable tokens at 1.00, majors at the UTC day's CoinGecko close, other tokens unpriced). By the Q4 result 94.5% of simple swaps are priced; complex receipts (FU3 adds 62% to priced volume when anchored) and confidential flow are absent. Every share below is a share of *this* priced population, not of NEAR Intents' volume.

## RX9: route mix (which assets, which chains)
Pair = the two distinct token IDs of the swap, mapped by the `tokens` table to symbol, chain and a stable flag. Class: stable-to-stable (both flagged stable), stable-to-volatile (one), volatile-to-volatile (none). A token not in the table is "unknown" and the swap is excluded from the class shares (its count is reported).
- **H-RX9a (stable-heavy):** stable-to-stable swaps carry at least **50%** of priced volume. Falsified below **25%**.
- **H-RX9b (few routes):** the top 5 unordered symbol pairs carry at least **50%** of priced volume. Falsified below **30%**.
- **H-RX9c (NEAR token is a minor leg):** swaps with the NEAR token (symbol `NEAR` or `wNEAR`) on either side carry at most **10%** of priced volume. Falsified above **25%**. This is the volume that touches NEAR itself, not the fee wallets' NEAR (those are separate rungs of the ladder).
- **H-RX9d (cross-chain):** swaps whose two tokens sit on different blockchains carry at least **70%** of priced volume. Falsified below **40%**.
- Also reported: the top 25 pairs by volume with swaps, volume and chain pair; weekly stable-to-stable share (7-day blocks from 2026-08-07); count of unknown-token swaps.

## RX10: swap size and dependence on large swaps
Size = the swap's priced volume (largest priced leg).
- **H-RX10a (a long tail of retail-size swaps):** the median priced swap is under **$1,000**. Falsified above **$5,000**.
- **H-RX10b (big swaps carry the dollars):** swaps of at least **$100,000** are under 1% of priced swaps and carry at least **30%** of priced volume. Falsified if they carry under **15%**, or if they are 1% or more of swaps.
- **H-RX10c (no single day dominates):** the largest single day is under **5%** of priced volume. Falsified above **10%**. Post hoc extra if it fails: the same figure without that day.
- Also reported: percentiles (p10, p25, p50, p75, p90, p99, p99.9) of swap size, volume and swap count by size bucket (<$100, $100 to 1K, 1K to 10K, 10K to 100K, 100K to 1M, 1M or more), the 10 largest swaps by size (transaction receipt id prefix only, first 8 characters).

## What this does not show
Volume of public swaps is a lower bound on the user volume (complex receipts, confidential swaps and unpriced tokens are absent). A bp rate on this volume is not NEAR's revenue: the fee wallets are fed by several paths (FU4, FU5). The solver and user sides are inferred. No causal reading is drawn from the mix.
