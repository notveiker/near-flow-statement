# Ask A results: is H1a's staking outflow unusual?

Method: [staking-windows-method.md](staking-windows-method.md), committed at `3332fc2` (2026-11-13 02:11 UTC) before any earlier window ran. H1a is **not re-scored**. Computed by `python3 -m pipeline.staking_analysis` from saved BigQuery outputs (`data/raw/windows/`, job IDs, SQL hashes and SHA-256 in `jobs.jsonl` and `data/MANIFEST.json`); results in `data/derived/staking_windows.json`. Cutoff 2026-11-04 respected (the price series is truncated to it in code).

## What ran, and what did not (the 1.5 TB rule)
All eight windows would cost **2,004 GB** (dry run), over the 1.5 TB limit. Windows were run most recent first while the running total stayed under it: **W1 to W6 ran (1,311 GB billed)**; **W7 (2024-11-15 to 2025-02-12) and W8 (2024-08-17 to 2024-11-14) were not run.** The earliest window run starts 2025-02-13, not late 2024. Running W7 and W8 costs a further 693 GB; it needs your go-ahead.

## Per window (NEAR, millions; net outflow = outflow minus inflow; rewards = pool-credited `validator_accounts_update`)
| Window | Seed day to end | Inflow | Outflow | Net outflow | Rewards | Net / rewards | Net / pool total at start | NEAR price change | Flow residual |
|---|---|---|---|---|---|---|---|---|---|
| H1a | 2026-08-06 to 2026-11-04 | 188.0 | 235.3 | +47.3 | 7.04 | 6.71 | +7.6% | +126% | +7.1 |
| W1 | 2026-05-08 to 2026-08-06 | 155.4 | 142.3 | -13.1 | 7.11 | -1.84 | -2.1% | +6% | -8.1 |
| W2 | 2026-02-07 to 2026-05-08 | 110.1 | 103.9 | -6.2 | 7.02 | -0.88 | -1.0% | +48% | -0.0 |
| W3 | 2025-11-09 to 2026-02-07 | 185.5 | 216.5 | +31.1 | 6.95 | 4.47 | +5.0% | -63% | +0.0 |
| W4 | 2025-08-11 to 2025-11-09 | 172.4 | 211.6 | +39.2 | 12.79 | 3.07 | +6.0% | +13% | +0.2 |
| W5 | 2025-05-13 to 2025-08-11 | 161.3 | 141.5 | -19.8 | 13.43 | -1.47 | -3.2% | -18% | -0.2 |
| W6 | 2025-02-12 to 2025-05-13 | 138.7 | 139.0 | +0.3 | 12.91 | 0.02 | +0.0% | -1% | +0.1 |

Quirks kept as they are: the first change of a pool in the window drops out unless the pool also changed on the seed day, and `receipt_processing` mixes delegator flows with the pool's own gas. The "flow residual" (change in pool totals minus the summed flows) is the size of what the query does not account for; it is +7.1M NEAR for the H1a window, -8.1M for W1 and under 0.2M for W2 to W6. The H1a window's 6.71 here is the query's own rewards denominator (7.04M); the report's 6.56 uses 7.21M (90% of gross), a different denominator.

## Where H1a ranks (7 windows: H1a plus six earlier)
- **Rank 1 of 7** by net over rewards (6.71), by net outflow (47.3M) and by net share of stake (7.6%). The next are W3 (4.47, 5.0%) and W4 (3.07, 6.0%). Three of the six earlier windows had net inflow (W1 -1.84, W2 -0.88, W5 -1.47), W6 was flat (0.02).
- **By the rule as written the reading is "unusual"** (rank 1 and at least 1.5 times the median of the earlier windows). **That is true only because the median of the earlier windows is negative (-0.43)**, which makes the 1.5 times test trivial; I applied it literally and say so. Against the largest earlier ratio (W3, 4.47) H1a is 1.50 times higher, and two earlier windows (W3 and W4) were also net outflows of at least 3 times rewards. So the honest reading: the highest of seven, with two earlier windows of the same sign and about half to two thirds the size, and three of six with the opposite sign.
- **Rewards halved between W4 and W3:** about 12.8M to 13.4M NEAR per window in W4 to W6, 7.0M to 7.1M from W3 on, so the ratio is also moved by the denominator.
- **Rank correlation of net outflow with NEAR's price change (7 windows):** Spearman rho = **+0.43**, exact permutation p = 0.35; the same for net share of stake (the pool total barely moves). Reading by the rule: **weak** (neither at least 0.6 nor under 0.3). The sign is positive, the opposite of "outflow follows a price fall": H1a's window had the largest price rise (+126%) and W3 the largest fall (-63%), and both were large net-outflow windows. With seven points this says nothing firm.
- **Two things this does not do:** it does not re-score H1a, and with W7 and W8 missing it cannot say how the 2024 autumn compares.
