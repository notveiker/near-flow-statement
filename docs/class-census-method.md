# Class C counted exactly on the full chain, and what else fell: method fixed before the queries run

Committed 2026-11-13 02:46 UTC (2026-11-13). Post hoc and exploratory (it follows the April result and the sample's class-adjusted result); it changes no pre-registered test. Source `transactions` only, `block_date` and `block_height <= 223088015` on every scan, run by `pipeline.windows run-file` (dry-run first, capped, job IDs and SHA-256 in `data/raw/april/jobs.jsonl`). Queries `sql/april/c1_class_daily.sql` (306.7 GB) and `c2_signer_decline.sql` (30.7 GB). Computed by `pipeline/class_census_analysis.py`.

## Part 1: class C exactly (2023-01-01 to 2026-11-04)
Class C as in `history-class-adjusted-method.md` (signers `hotwallet.kaiching`, `users.kaiching`, `sweat-migration.near`, or receivers ending `.users.kaiching`). Per day and month: transactions in C by part and its share of all transactions; per quarter: transactions per day outside C.
- **H-E1:** C's exact share of 2025Q3 transactions is between **25% and 45%** (the sample said 31% on 198 clusters, 43% on 268). Falsified outside 15% to 60%.
- **H-E2 (the sample was right):** the exact ratio 2026Q3 / 2025Q3 of transactions per day **outside C** lies inside the sample's primary-cut 90% interval (0.237 to 0.373); the exact raw ratio lies inside 0.157 to 0.272. Each is reported as inside or outside; an outside result is a failure of the sample for that quantity.
- **Onset:** first month in which C is at least 1% and the first at least 10% of all transactions; the sample said 2023Q3 and 2024Q3.

## Part 2: what else fell (2025Q3 to 2026Q3, outside C)
Per signer, transactions in 2025-07-01..09-30 (a) and 2026-07-01..09-30 (b), signers and receivers of C excluded. Gross decline = sum over signers of max(a - b, 0).
- **Concentrated:** at most **20 signers** carry 50% of the gross decline. **Broad:** at least **500 signers** are needed for 50%. Between: mixed.
- Reported: the 60 largest decliners with their most frequent receiver, the 20 largest risers, and the share of the decline carried by the top 1, 5 and 20.
- A decliner is labelled only by what the data shows (name, most frequent receiver); any reading of purpose is **INFERRED**.
- If the ex-C total fell less than 50% between the two quarters on the full chain, the "ex-C fell about 70%" statement of the sample result is corrected.
