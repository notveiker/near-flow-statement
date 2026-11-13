# History sample, class-adjusted: results (post hoc)

Method: [history-class-adjusted-method.md](history-class-adjusted-method.md), committed at `28739ea` (2026-11-13 02:42:48 UTC) before the class counts were computed. **Post hoc and exploratory; U1 to U5 are untouched.** Class C = signers `hotwallet.kaiching`, `users.kaiching`, `sweat-migration.near`, or receivers ending `.users.kaiching`. Code `pipeline/sample_class.py`, rows `data/derived/sample_class_rows.jsonl`, results `data/derived/history_class_adjusted.json`. Primary cut: the 198 clusters sealed by the stopping-rule time; the 268-cluster figures are given where they differ.

## Quarterly series (primary cut; millions of transactions per day)
| Quarter | Clusters | All | Outside C | C share |
|---|---|---|---|---|
| 2020Q3 | 6 | 0.00 | 0.00 | 0% |
| 2020Q4 | 6 | 0.02 | 0.02 | 0% |
| 2021Q1 | 6 | 0.01 | 0.01 | 0% |
| 2021Q2 | 6 | 0.13 | 0.13 | 0% |
| 2021Q3 | 6 | 0.28 | 0.28 | 0% |
| 2021Q4 | 6 | 0.23 | 0.23 | 0% |
| 2022Q1 | 6 | 0.45 | 0.45 | 0% |
| 2022Q2 | 6 | 0.57 | 0.57 | 0% |
| 2022Q3 | 6 | 0.26 | 0.26 | 0% |
| 2022Q4 | 6 | 0.42 | 0.42 | 0% |
| 2023Q1 | 6 | 0.36 | 0.36 | 0% |
| 2023Q2 | 6 | 0.39 | 0.39 | 0% |
| 2023Q3 | 6 | 0.39 | 0.36 | 7% |
| 2023Q4 | 6 | 3.49 | 3.44 | 2% |
| 2024Q1 | 6 | 5.38 | 5.06 | 6% |
| 2024Q2 | 6 | 7.81 | 7.32 | 6% |
| 2024Q3 | 6 | 6.06 | 4.84 | 20% |
| 2024Q4 | 6 | 6.79 | 4.93 | 27% |
| 2025Q1 | 12 | 7.54 | 4.90 | 35% |
| 2025Q2 | 12 | 4.83 | 3.12 | 35% |
| 2025Q3 | 11 | 4.01 | 2.77 | 31% |
| 2025Q4 | 11 | 5.33 | 1.76 | 67% |
| 2026Q1 | 11 | 4.24 | 1.12 | 74% |
| 2026Q2 | 11 | 0.85 | 0.85 | 0% |
| 2026Q3 | 11 | 0.83 | 0.83 | 0% |
| 2026Q4 | 11 | 1.16 | 1.13 | 2% |

## Predictions
- **H-C1 supported.** C carries **31%** of sampled transactions in 2025Q3 (43% with all 268 clusters) and **0%** in 2026Q3. It reaches 1% in 2023Q3 and 10% in 2024Q3, and is **67% to 74% of sampled transactions in 2025Q4 and 2026Q1**; it is 0% from 2026Q2.
- **H-C2 falsified (primary cut).** The ratio 2026Q3 / 2025Q3 of transactions per day is 0.21 raw (90% interval 0.16 to 0.27) and **0.30 outside C** (0.24 to 0.37), 1.45 times the raw ratio (needed 2; falsified under 1.5). With all 268 clusters it is 0.31 outside C against 0.18 raw, 1.75 times: between the two bars. So the class explains a large part of the quarter-on-quarter step at April 2026, but **not most of the year-on-year fall**: traffic outside C also fell by about 70% between 2025Q3 and 2026Q3 (2.77M to 0.83M a day).
- **H-C3 not supported.** What is left did not grow: ex-C ratio 0.30, below 1.0. Distinct signers outside C per 100 blocks: ratio 0.28 (0.24 to 0.33).
- **Not a rescue of U1.** U1 as pre-registered (ratio 0.18, interval 0.14 to 0.23, needed 1.5) still fails; removing C does not bring it near.

## Reading
The April result and this one fit together: one automated class grew from 6% of the sampled series in 2024Q1 to 27% in 2024Q4 and ran at 31% to 74% from 2025Q1 to 2026Q1 and stopped on 2026-04-02, which makes the series very steep at that date; but the rest of the series was already falling, from 4.9M transactions a day outside C in 2025Q1 to 0.83M in 2026Q3. A quarter-on-quarter "activity" comparison that crosses 2026-04 is therefore dominated by C, and a year-on-year comparison is dominated by the broad decline of everything else, which this analysis does not explain.

## Correction after the full-chain count (`class-census-results.md`)
Counting C exactly on the full chain gives 51.8% of 2025Q3 transactions, not the 31% (198 clusters) or 43% (268) estimated here, so H-C1's "at least 30%" holds but the sample understated the class. The ex-C fall of 2025Q3 to 2026Q3 is confirmed (ratio 0.317, inside the sample interval) and is **concentrated**, not broad: two `.tg` relay signers carry 61% of it. The phrase "broad decline of everything else" above is superseded by that result.
