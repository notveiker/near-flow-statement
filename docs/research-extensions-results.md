# Research extensions RX1 to RX3: results

Method: [research-extensions-method.md](research-extensions-method.md), committed at `c86431b` (2026-11-13 03:02:43 UTC) before the queries ran. NEAR only; cutoff 2026-11-04 respected; `rx1_users` 0.2 GB and `rx3_relayer` 145 GB billed (`data/raw/rx/jobs.jsonl`); RX2 is local. Computed by `pipeline/rx_analysis.py`; `data/derived/rx_results.json`.

## RX1: Intents "users" on chain: the unit is not a person
- **879,026 accounts** took the user side of 1,222,617 public-leg simple swaps (\$2.17B priced), about 1.4 swaps per account. Every 7-day block is almost entirely new accounts: 57K to 87K active accounts per block, of which 99.9% are first seen that block (the last block is 4 days). **Retention is 0.08%** (225 of 289,789 accounts first seen in the first four blocks are active four or more blocks later).
- **H-RX1c falsified as written (rule 30%), and the reading is that accounts are not users.** The near-zero return rate is what a fresh account per swap produces: 1Click gives each swap its own deposit address, which then trades as an Intents account (INFERRED; the chain shows only that almost no account is ever reused). So per-user retention and per-user concentration cannot be measured from public legs for this flow.
- **H-RX1a falsified:** the top 10 accounts carry **4.2%** of priced volume (rule 25%; top 1 1.3%, top 100 7.7%, top 1,000 22.3%). **H-RX1b falsified:** 2,850 accounts with at least \$100K (0.32% of accounts) carry 34.7% of volume (rule 80%; falsified under 60%).
- **The largest "users" are solvers.** Of the top four by volume, `kipseli.near` (\$28.4M), `crux-solver.near` (\$17.7M), `0x8c60fa…` and `brlabs-solver.near` are inferred solvers acting as the user side of other solvers' swaps, because the solver rule picks the side with more counterparties. Their share is small either way.
- **What it does support:** volume sits in larger accounts even though accounts are fresh: accounts with at least \$10K of total volume are about 3.9% of accounts and carry about 76% of priced volume, close to the 77% the Explorer-based note reports for swaps of at least \$10K.

| Account volume bucket | Accounts | Share | Volume (\$M) | Share | Fills |
|---|---|---|---|---|---|
| a_<100 | 489,400 | 55.7% | 12 | 0.6% | 495,977 |
| b_100-1k | 238,223 | 27.1% | 90 | 4.2% | 239,332 |
| c_1k-10k | 117,431 | 13.4% | 414 | 19.1% | 137,207 |
| d_10k-100k | 31,122 | 3.5% | 903 | 41.6% | 57,696 |
| e_>=100k | 2,850 | 0.3% | 753 | 34.7% | 292,405 |

## RX2: what the solvers keep on stable swaps
- **Total margin: \$87,508** over 90 days on same-symbol stable-to-stable swaps (\$655M paid, 1.34 bp), across 26 solvers, **none negative** in total. **H-RX2b supported:** that is **1.8%** of the \$4.74M delivered to the three revenue wallets in the same window (rule: under 25%; falsified above 50%). **H-RX2a supported:** the top 3 solvers carry 61% of the pool (rule 50%).
- The pool is led by the three hex-named solvers that price large tickets (\$19.8K, \$18.7K and \$14.9K at 4.6, 8.6 and 4.2 bp); the high-volume solvers earn almost nothing per dollar (0.9 bp for `0x8c60fa…`, 0.2 bp for the `blockzen` pair).
- Lower bound only: stable swaps with public legs, same-symbol class. It shows that the visible solver margin on this flow is small next to what NEAR's wallets receive (about 54 times as much).

## RX3: who signs the transactions sent to `intents.near` (exact)
| Month | Transactions | Signers | Top signer | Top-1 share | Top-5 share |
|---|---|---|---|---|---|
| 2025-06 | 596,322 | 17,282 | `intents.near` | 91.9% | 92.4% |
| 2025-07 | 3,405,261 | 16,338 | `intents.near` | 99.2% | 99.3% |
| 2025-08 | 1,767,888 | 11,046 | `intents.near` | 99.1% | 99.3% |
| 2025-09 | 1,160,325 | 19,482 | `intents.near` | 98.0% | 98.2% |
| 2025-10 | 2,321,056 | 26,272 | `intents.near` | 98.4% | 98.5% |
| 2025-11 | 2,793,003 | 6,742 | `intents.near` | 99.6% | 99.7% |
| 2025-12 | 1,254,115 | 3,361 | `intents.near` | 99.4% | 99.7% |
| 2026-01 | 879,533 | 5,214 | `intents.near` | 99.2% | 99.2% |
| 2026-02 | 925,417 | 3,958 | `intents.near` | 97.7% | 99.2% |
| 2026-03 | 1,015,700 | 2,749 | `intents.near` | 96.4% | 98.8% |
| 2026-04 | 990,376 | 3,295 | `intents.near` | 93.9% | 99.3% |
| 2026-05 | 1,007,193 | 5,025 | `intents.near` | 92.4% | 98.7% |
| 2026-06 | 1,086,418 | 2,907 | `intents.near` | 89.1% | 99.2% |
| 2026-07 | 1,322,992 | 2,124 | `intents.near` | 81.7% | 99.5% |
| 2026-08 | 1,715,112 | 1,885 | `intents.near` | 79.4% | 99.7% |
| 2026-09 | 2,031,812 | 9,363 | `intents.near` | 74.8% | 99.1% |
| 2026-10 | 2,013,820 | 5,354 | `intents.near` | 71.7% | 98.9% |
| 2026-11 | 433,503 | 536 | `intents.near` | 82.5% | 99.4% |

- **H-RX3b supported:** the top 5 signers carry 98.7% or more of the transactions in every month 2026-05 to 2026-10 (rule 95%).
- **H-RX3a neither supported nor falsified:** the top signer's share is above 80% in 2026-05 (92.4%), 06 (89.1%) and 07 (81.7%) but **falls to 79.4%, 74.8% and 71.7% in August to October** (rule needs 80% in every month; falsified only under 60%). The lowest 7-day block is 67.2%.
- **The top signer is `intents.near` itself** in every month (the contract's own account signs the transactions that call it; INFERRED: a relayer using that account's key), at 99% or more from 2025-07 to 2026-01, then a steady fall to 72% by October while the number of distinct signers stays in the thousands and the top 5 stay at 99%. The next signers (2026-05 on): `escrow.ai.near`. So concentration in one signer is easing into a handful of operators, not a broad set.
- 7-day blocks ending on the dates shown (top-1 share): 07-22: 79% 07-29: 81% 08-05: 79% 08-12: 78% 08-19: 79% 08-26: 83% 09-02: 78% 09-09: 77% 09-16: 70% 09-23: 75% 09-30: 75% 10-07: 70% 10-14: 75% 10-21: 67% 10-28: 68% 11-04: 81%.
- This is pre-window context for the pre-registered F4 relayer test (top-1 above 80% through an outage week); it does not score it, and nothing from the forward window was read.
