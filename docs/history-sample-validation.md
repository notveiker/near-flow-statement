# History sample: validation against the full chain (partial substitute), method fixed before it runs

Committed 2026-11-13 02:44 UTC (2026-11-13), before the census query ran or any comparison was computed. The pre-registered validation (`docs/history-sample-prereg.md`, "Validation of the sampler itself": draw clusters from a node census 200 times and report 90%-interval coverage per metric) has not been run; the census blocks are not held (`docs/history-sample-final-cut.md`). This is a **different and partial check**, labelled so: for the one metric the public dataset can reproduce exactly, transactions per day, the sample's quarterly estimates are compared with the full chain. It does not validate the other metrics and does not replace the pre-registered design.

## Reference (the census)
`sql/validation/tx_daily_census.sql`: transactions per UTC day for every day from 2020-07-21 to 2026-11-04 in `bigquery-public-data.crypto_near_mainnet_us.transactions` (all transactions, any status, `block_height <= 223088015`; same count as a chunk's transaction list, which is what the sampler counts). The reference for a quarter is the mean transactions per day over the stratum's UTC dates.

## Sample estimate
The `tx_per_day` point and 90% cluster-bootstrap interval of `pipeline/sample_metrics.py` (same estimator, 2,000 resamples, same seed), computed for the **primary cut (198 clusters sealed by the stopping-rule time)** and for all 268 as a sensitivity.

## Scored quarters
Every stratum except **2020Q3** (starts mid-day on 2020-07-21) and **2026Q4** (runs past the cutoff date). 24 quarters.

## Rules (written before the comparison)
- **Coverage** = share of scored quarters whose 90% interval contains the census value. By the pre-registration's own rule, **coverage below 80% means the intervals are labelled "too narrow" and not relied on**; at or above 80% there is no evidence of that. (At a nominal 90%, 24 quarters give about 21.6 covered on average.)
- **Point error:** median absolute relative error and median signed relative error (bias) of the point estimate against the census; reported by era (the 18 strata before 2025 have 6 clusters each, the 6 from 2025Q1 to 2026Q3 have 11 or 12).
- A quarter with fewer than 5 clusters is not scored (none expected).
- No quarter is dropped or re-defined after seeing the comparison. The result is published whatever it is, including a finding that the intervals are too narrow.

## Addendum: the other full-chain-reproducible metrics (added 2026-11-13 02:49 UTC, before their queries run)
Same logic, for the quarters 2025Q1 to 2026Q3 (7 quarters; the plan has 11 or 12 clusters in each). Census queries: `sql/validation/outcomes_daily_census.sql` (execution_outcomes per day: all outcomes, outcomes executed on `intents.near`, tokens burnt; about 673 GB) and `tx_burn_daily_census.sql` (tokens burnt at transaction-to-receipt conversion). Mapping to the sampler's metrics: `receipts_per_day` = outcomes per day; `intents_per_day` = outcomes executed on `intents.near` per day; `burn_near_per_day` = outcome tokens burnt plus conversion tokens burnt per day.
- **Definition check first.** For each metric, the median over the 7 quarters of (sample estimate / census value). **If it lies outside 0.9 to 1.1 the definitions are taken not to match and no coverage is claimed for that metric** (reported as a mismatch, not as a sampler failure).
- **Coverage rule** as before: 90% interval covers the census value; below 80% of quarters is "too narrow" (with 7 quarters that means 5 or fewer covered). Point error as median absolute relative error.
- The result is reported for the primary 198-cluster cut and for all 268. Nothing is dropped.
