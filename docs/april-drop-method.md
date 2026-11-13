# Ask B: what stopped in April 2026? Method and thresholds, fixed before any query runs

Committed 2026-11-13 02:12 UTC (2026-11-13). Source: `bigquery-public-data.crypto_near_mainnet_us.transactions` only, every scan filtered on `block_date` and on `block_height <= 223088015` (data cutoff 2026-11-04). The claim to test: transactions per day fell to about a fifth between 2026-Q1 and 2026-Q2. Queries `sql/april/b1_daily.sql`, `b2_monthly_top20.sql`, `b3_fortnights.sql`, run by `python3 -m pipeline.windows run-file` (dry-run first, capped, job ids and output SHA-256 in `data/raw/april/jobs.jsonl`). Numbers are computed by `pipeline/april_analysis.py` from the saved files.

## Parts
1. **Per day**, 2025-07-01..2026-11-04: transactions, distinct signers, distinct receivers. Also reported: Q1 and Q2 2026 mean transactions per day and their ratio, and the date of the largest one-day or one-week step.
2. **Per month**: the 20 most-called receivers, their transaction counts and their share of the month; and the share of the month's transactions in the top 1, top 5, top 20.
3. **The fortnights either side of 2026-04-02**: before = 2026-03-19..2026-04-01, after = 2026-04-02..2026-04-15 (14 days each; the date is Victor's). The transactions that disappear are measured at the signer level as **gross drop** = the sum over signers of max(transactions before minus after, 0), and at the receiver level the same way, grouped into families (the receiver itself for the 40 receivers with the largest drop; otherwise `<64hex>`, `<0x-eth>`, or the suffix after the first dot). Reported: net change in transactions, gross drop, how many signers carry 50%, 80% and 90% of the gross drop, the top signers, and the share of the gross drop carried by each receiver family.

## Does the step belong to 2026-04-02?
A **step at 04-02** exists only if the mean daily transactions of the 7 days from 04-02 are at most 60% of the mean of the 7 days before. If not, the drop is not a step at that date (it is gradual or elsewhere), and the fortnight classification below is reported as a description of that fortnight only, not as "what stopped".

## Classification (written before the numbers are seen)
- **"One class of automated traffic ended"** requires all four: (i) at most **10 signers** carry 50% of the gross signer drop; (ii) at least **60%** of the gross drop goes to **one** receiver family; (iii) the signers that carry the first half of the drop fall by at least **90%** in total (after / before at most 0.1); (iv) the step exists at 04-02 as defined above.
- **"A broad fall"**: at least **1,000 signers** are needed for 50% of the gross drop **and** no receiver family carries more than **30%** of it.
- **Mixed / between**: anything else (reported with the numbers, not forced into either).
- A different date for the step, or a fall that is already there before 03-19, makes the 04-02 reading "not at this date" whatever the shares are.

## What this cannot say
Signers are accounts, not people; a single operator can run many. "Receiver family" is a naming rule, not an entity. Failed transactions are included. No claim is made about the cause beyond what the grouping shows (**INFERRED** if any is drawn).
