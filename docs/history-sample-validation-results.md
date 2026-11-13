# History sample validation against the full chain: results

Method: [history-sample-validation.md](history-sample-validation.md), committed at `3243a5f` (2026-11-13 02:44:31 UTC) before the census query ran. Census: `sql/validation/tx_daily_census.sql` (87.7 GB, 2,285 days, job and SHA-256 in `data/raw/validation/jobs.jsonl`). Code `pipeline/sample_validation.py`; results `data/derived/history_sample_validation.json`. **Partial substitute for the pre-registered node-census validation; covers transactions per day only.**

## Result by the rule: the intervals are "too narrow" overall, but the failures are all before 2025
- **Coverage on the primary cut (198 clusters): 19 of 24 quarters = 79.2%**, under the 80% bar, so by the pre-registration's own rule the intervals are labelled **too narrow** and are not relied on. With all 268 clusters the coverage is the same (19 of 24). It misses the bar by one quarter (19.2 needed).
- **All five misses are before 2025, where each quarter has 6 clusters:** 2021Q3, 2021Q4, 2022Q3, 2023Q3, 2024Q3. Coverage there is 71% (12 of 17), median absolute error of the point estimate 21%. **From 2025Q1 (11 to 12 clusters per quarter) coverage is 100% (7 of 7)**, median absolute error 12% on the primary cut (8% with 268). The quarters U1 compares (2025Q3 and 2026Q3) are both in the covered group: census 4.84M and 0.74M a day against estimates 4.01M and 0.83M, each inside its interval.
- **Bias:** the median signed error of the point estimate is -3.0% (primary); -3.8% with 268. Overall median absolute error 16.7% (primary), 13.0% (268).
- **Reading.** Intervals from 6 clusters per quarter are too narrow for tx per day; the ones from 11 or 12 clusters are not shown to be. The history report should say that the pre-2025 quarter intervals are not reliable and that nothing in the tests U1 to U5 rests on them. A caveat on this check: 24 quarters give a coverage estimate with a binomial standard error near 8 points, so 79% against a nominal 90% is evidence of narrow intervals in the small strata, not a precise measurement.
- **Correction to the method text:** it said six strata from 2025Q1 to 2026Q3; there are seven (2025Q1 to 2026Q3), and 17 scored strata before 2025 (18 minus the excluded 2020Q3). The scoring itself is as pre-registered.
- **Not covered by this check:** the other metrics (signers per 100 blocks, burn, intents receipts, top-receiver share), which the full-chain public tables do not reproduce in the sampler's definition, and the pre-registered node-census design.

## Per quarter (primary cut, millions of transactions per day; first and last strata not scored)
| Quarter | Clusters | Census | Estimate | 90% interval | Covered |
|---|---|---|---|---|---|
| 2020Q4 | 6 | 0.01 | 0.02 | 0.01 to 0.02 | yes |
| 2021Q1 | 6 | 0.01 | 0.01 | 0.00 to 0.01 | yes |
| 2021Q2 | 6 | 0.10 | 0.13 | 0.09 to 0.16 | yes |
| 2021Q3 | 6 | 0.25 | 0.28 | 0.26 to 0.30 | **no** |
| 2021Q4 | 6 | 0.30 | 0.23 | 0.17 to 0.29 | **no** |
| 2022Q1 | 6 | 0.56 | 0.45 | 0.33 to 0.57 | yes |
| 2022Q2 | 6 | 0.68 | 0.57 | 0.40 to 0.76 | yes |
| 2022Q3 | 6 | 0.44 | 0.26 | 0.22 to 0.31 | **no** |
| 2022Q4 | 6 | 0.45 | 0.42 | 0.31 to 0.54 | yes |
| 2023Q1 | 6 | 0.39 | 0.36 | 0.29 to 0.44 | yes |
| 2023Q2 | 6 | 0.36 | 0.39 | 0.28 to 0.56 | yes |
| 2023Q3 | 6 | 0.77 | 0.39 | 0.28 to 0.54 | **no** |
| 2023Q4 | 6 | 2.52 | 3.49 | 0.64 to 8.88 | yes |
| 2024Q1 | 6 | 4.37 | 5.38 | 3.78 to 6.94 | yes |
| 2024Q2 | 6 | 7.73 | 7.81 | 6.72 to 8.91 | yes |
| 2024Q3 | 6 | 6.88 | 6.06 | 5.28 to 6.81 | **no** |
| 2024Q4 | 6 | 7.49 | 6.79 | 5.80 to 7.76 | yes |
| 2025Q1 | 12 | 6.88 | 7.54 | 6.58 to 8.52 | yes |
| 2025Q2 | 12 | 5.47 | 4.83 | 3.48 to 6.30 | yes |
| 2025Q3 | 11 | 4.84 | 4.01 | 3.23 to 4.86 | yes |
| 2025Q4 | 11 | 4.21 | 5.33 | 4.12 to 6.65 | yes |
| 2026Q1 | 11 | 3.49 | 4.24 | 3.00 to 5.52 | yes |
| 2026Q2 | 11 | 0.85 | 0.85 | 0.77 to 0.94 | yes |
| 2026Q3 | 11 | 0.74 | 0.83 | 0.67 to 1.00 | yes |
