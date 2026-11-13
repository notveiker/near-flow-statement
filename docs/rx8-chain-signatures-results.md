# RX8: Chain Signatures, direct transactions to `v1.signer`, counted exactly: results

Method: the RX8 and RX8b sections of [research-extensions-method.md](research-extensions-method.md), committed at `60aafcb` and `5162dd5` (2026-11-13 03:16:16 and 03:17:15 UTC) before the queries ran (`rx8_signer_tx_daily` 194 GB, `rx8b_signer_top` 31 GB; `data/raw/rx/jobs.jsonl`). NEAR only; cutoff respected. `pipeline/rx_analysis.py` (`rx8`).

| Quarter | Days | Transactions to `v1.signer` per day | Distinct senders per day | Failed |
|---|---|---|---|---|
| 2025Q1 | 88 (two zero-transaction days, 2025-01-06 and 01-19, have no rows and are left out of the averages) | 399 | 7 | 0.0% |
| 2025Q2 | 91 | 529 | 9 | 0.0% |
| 2025Q3 | 92 | 3,268 | 11 | 0.0% |
| 2025Q4 | 92 | 5,330 | 12 | 0.0% |
| 2026Q1 | 90 | 10,518 | 11 | 0.0% |
| 2026Q2 | 91 | 29,808 | 13 | 0.0% |
| 2026Q3 | 92 | 27,450 | 19 | 0.0% |
| 2026Q4 | 35 | 15,624 | 20 | 0.0% |
(2026Q4 is 35 days to the cutoff.)

- **H-RX8a not supported, not falsified:** 2026Q3 is **8.4 times** 2025Q3 (rule: 10 times; falsified under 3). Growth is real but the peak was in 2026Q2 (29.8K a day) and the quarter to 11-04 runs at 15.6K a day.
- **H-RX8c neither:** distinct senders per day went from 11 to 19 (1.75 times; rule 3 times). **H-RX8d falsified:** the top 3 senders carry 24% of 2026Q3 transactions (rule 80%), but see the next point.
- **What the senders are.** Ten accounts carry almost identical counts, about 182K transactions each in 2026Q3 (7.2% apiece): `everstake-mpc-1.near`, `multichain-mainnet-aurora.near`, `blacksandtech.near`, `n1-multichain.near`, `nodemonster.near`, `mpc-lgns.near`, `stakin-mpc.near`, `near-mpc-staking4all-01.near`, `mpch-01.near`, `svrn-01.near` and others, with a second tier of smaller ones. By name these are node operators of the MPC network behind Chain Signatures (**INFERRED from names**), and the transactions are theirs, not users': the same count from every node is the pattern of nodes each answering the same stream of requests. The largest single sender, `tx-bench.near`, a benchmarking-style account, sent **42% of the 2025Q3 count** and 10% in 2026Q3.

| Sender | 2025Q3 | 2026Q3 | Share of 2026Q3 |
|---|---|---|---|
| `tx-bench.near` | 125,299 | 247,078 | 9.8% |
| `everstake-mpc-1.near` | 2,279 | 183,435 | 7.3% |
| `multichain-mainnet-aurora.near` | 22,137 | 183,339 | 7.3% |
| `blacksandtech.near` | 21,413 | 182,751 | 7.2% |
| `n1-multichain.near` | 19,773 | 182,698 | 7.2% |
| `nodemonster.near` | 22,801 | 182,523 | 7.2% |
| `mpc-lgns.near` | 22,010 | 181,957 | 7.2% |
| `stakin-mpc.near` | 2,018 | 181,898 | 7.2% |
| `near-mpc-staking4all-01.near` | 22,160 | 181,851 | 7.2% |
| `mpch-01.near` | 0 | 181,670 | 7.2% |
| `svrn-01.near` | 0 | 180,941 | 7.2% |
| `greenfield-mpc01.near` | 0 | 103,806 | 4.1% |

- **What this does and does not measure.** The direct-transaction count is a node-side activity count. If every node posts once per request, requests would be near 2K a day (182K per node over 92 days), not 27K; if only some nodes answer each request, between the two. The sample's 36.6K a day counts `sign` calls received (user-side, receipts) and is within a factor of 2 of this count (ratio 1.33, H-RX8b numerically true), but the two are different things, so that agreement is not a validation. **The number of Chain Signatures user requests per day is therefore not established by either**; the exact receipt-level count costs 4.7 TB in BigQuery and was not run. What is established: direct usage is from a small, near-fixed set of accounts (19 a day), 42% of the 2025Q3 count was one benchmarking account, and the growth from 2025Q3 to 2026Q3 in this series (8.4 times) is smaller than the sample's (about 26 times) and has been falling since 2026Q2.

## Cross-check with the repo's census figure
`data/derived/census_metrics.json` reports `signatures_per_day_k` = 15.7, annualised from `v1.signer` `respond` calls in the 10.3-hour node census (the research note says so). That is the same kind of count as this one (node-side responses), and the exact direct-transaction series for 2026Q4 (35 days to 11-04) is **15,624 a day**, within 1% of the census figure. So the census number was a good estimate of node-side activity, and it should be read as responses, not as user requests.
