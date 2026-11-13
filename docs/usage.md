# Usage from BigQuery (exploratory)

*Exploratory, chosen after the freeze (2026-11-13). Not a pre-registered test, and it feeds no rating. Every number marked with an `n:` comment is recomputed from committed data by `make reproduce`. Queries: `sql/usage_daily.sql`, `sql/usage_receipts.sql`, `sql/usage_signer_groups.sql`; results in `data/raw/bq/`.*

The track brief asks for BigQuery queries on daily active accounts, transaction counts and contract usage. Until 2026-11-13 the thesis used Nearblocks' charts instead and said the BigQuery queries were not run. This page runs them.

## 1. The Nearblocks series are BigQuery's, exactly

On all 395<!--n:usage_bq_days_n--> days from 2025-10-06 to 2026-11-04, the BigQuery count of transactions equals Nearblocks' `txns`, and the count of distinct transaction signers equals Nearblocks' `active_accounts`, on 395<!--n:usage_bq_nearblocks_match_days_n--> of them. So Nearblocks' "active accounts" are distinct transaction signers a day, and its "transactions" are signed transactions. The definitions the thesis called undocumented are now known, and the figures in `THESIS.md` section 3 stand: 61.6<!--n:usage_bq_signers_30d_k-->K signers a day over the 30 days to 2026-11-04, against 269.0<!--n:usage_bq_signers_yago_30d_k-->K on the same days a year earlier.

What that definition means: a meta-transaction counts once, for the relayer that signs it, not for the user it acts for. NEAR has many relayed users, so signers undercount them (section 3).

## 2. The 2026-04-02 step is one application

Daily transactions fell from 4,169.8<!--n:l1_step_tx_before_k-->K on 2026-03-31 to 1,063.4<!--n:l1_step_tx_after_k-->K on 2026-04-02. Three signers of Sweat Economy's accounts (`hotwallet.kaiching`, `users.kaiching`, `sweat-migration.near`) signed 3,209.4<!--n:usage_bq_step_kaiching_tx_before_k-->K transactions on 03-31 and 144.2<!--n:usage_bq_step_kaiching_tx_after_k-->K on 04-02: 98.7<!--n:usage_bq_step_kaiching_share_pct-->% of the step. Relayed users (accounts a relayer acted for) fell from 3,146.4<!--n:usage_bq_step_relayed_before_k-->K to 331.5<!--n:usage_bq_step_relayed_after_k-->K on the same days. So the step is not a change in what Nearblocks counts. It is the end of one application's high-volume on-chain activity.

Why it stopped is not in the data, and we found no published account of it: Sweat's own notice of 2026-10-01 that the Sweat Wallet and the SWEAT token "as they exist today" end on 2026-12-30 is dated six months later, and the exploit of SWEAT's contract reported on 2026-04-29 came four weeks later. Whether those transactions were users' activity or automated bookkeeping by the application is not something a signer count can say.

What remains of Sweat is still NEAR's largest signer: `sweat-relayer.near` signed 26.6<!--n:usage_bq_top1_signer_tx_share_30d_pct-->% of all transactions over the 30 days to 2026-11-04, and the ten largest signers 61.0<!--n:usage_bq_top10_signer_tx_share_30d_pct-->%. If Sweat's wind-down on 2026-12-30 ends that relayer's traffic, the transaction count will fall again for the same reason, without telling us anything new about other usage.

## 3. The fall in active accounts is HOT's Telegram accounts

Signers whose account id ends in `.tg` (HOT Wallet's Telegram accounts) averaged 249.9<!--n:usage_bq_tg_signers_yago_30d_k-->K a day over 2025-10-06 to 11-04 and 45.6<!--n:usage_bq_tg_signers_30d_k-->K over 2026-10-06 to 11-04. That is 98.5<!--n:usage_bq_tg_share_of_signer_drop_pct-->% of the fall in daily signers. All other signers went from 19.1<!--n:usage_bq_non_tg_signers_yago_30d_k-->K to 16.0<!--n:usage_bq_non_tg_signers_30d_k-->K a day (-16.2<!--n:usage_bq_non_tg_signers_yoy_pct-->%). We found no published explanation of the `.tg` decline; secondary reports of a new HOT "L2" claim path do not date it or link it to fewer signers.

Counting relayed users as well (distinct transaction signers acting for themselves, plus the accounts relayers acted for), there were 118.4<!--n:usage_bq_users_incl_relayed_30d_k-->K a day over the 30 days to 2026-11-04, against 2,912.9<!--n:usage_bq_users_incl_relayed_yago_30d_k-->K a year earlier, when relayers acted for 2,650.9<!--n:usage_bq_relayed_yago_30d_k-->K accounts a day (now 58.1<!--n:usage_bq_relayed_30d_k-->K), most of them Sweat's.

Read together: almost all of the fall in NEAR's headline usage is two consumer applications, Sweat and HOT, and neither is NEAR Intents. Usage outside them fell by about a sixth. Whether any of these accounts hold or sell NEAR is not shown.

## 4. Contract usage did not fall

Distinct accounts that received a function call averaged a median of 1,449<!--n:usage_bq_contracts_called_median_30d_n--> a day over the 30 days to 2026-11-04, against 1,461<!--n:usage_bq_contracts_called_median_yago_n--> a year earlier. Counting only contracts called directly by a transaction's signer (not by another contract), the mean rose from 849.0<!--n:usage_bq_contracts_direct_yago_n--> to 1,296.5<!--n:usage_bq_contracts_direct_30d_n--> a day (+52.7<!--n:usage_bq_contracts_direct_yoy_pct-->%). We use the median for all contracts because a few days carry tens of thousands of one-off receivers (92,659 on 2025-10-12), which looks like account spam rather than contract use. Nearblocks' "active contracts" series, which steps on 2026-04-02, is close to the number of distinct transaction receivers, not to contracts called, and we do not use it.

## Limits

- A signer is an account, not a person, and nothing here is filtered for sybils. The `.tg` and `.kaiching` groupings are by account-id suffix; that those accounts belong to HOT and Sweat is our reading of their names and of the accounts that sign for them.
- The receipt-level counts (relayed users, contracts called) cover three spans only: 2025-10-06 to 11-04, 2026-03-25 to 04-08 and 2026-10-06 to 11-04.
- None of this measures NEAR Intents, whose swaps are mostly signed by solvers and relayers on behalf of users on other chains.
