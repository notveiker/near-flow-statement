# Research extensions RX1 to RX3: method fixed before the queries run

Committed 2026-11-13 03:02 UTC (2026-11-13). New, NEAR-only follow-ups. The Intents rebuild stays frozen (tag `rebuild-frozen`); these use its staged tables where noted and are separate files, labelled RX so they do not collide with the forward tests F1 to F4 or the rebuild's FU labels. Data cutoff 2026-11-04 / block 223,088,015 enforced by `pipeline.windows run-file`; every query dry-run first, capped, with job ID and output SHA-256 in `data/raw/rx/jobs.jsonl`. Numbers are computed by `pipeline/rx_analysis.py`. Descriptive claims about accounts are limited to what the data shows; ownership or purpose is **INFERRED**.

## RX1: how concentrated are Intents users on chain? (`sql/rx/rx1_users.sql`, staged `swaps_solver`)
Window 2026-08-07..2026-11-04. A simple swap's user is the participant that is not the inferred solver; priced volume is the swap's largest priced leg (Q3/Q4 rules). Only public-leg swaps exist here, so confidential flow is absent (stated in the result). Account IDs are pseudonymous; only the first 8 characters of the top 10 are shown and no linking of accounts is attempted.
- **H-RX1a (whale-driven):** the top 10 users carry at least **25%** of priced volume. Falsified below 10%.
- **H-RX1b (a few large accounts):** users with at least $100K of priced volume are under 2% of users and carry at least **80%** of volume. Falsified if they carry under 60%.
- **H-RX1c (users come back):** of users first seen in the first four 7-day blocks (08-07 to 09-03), at least **30%** are active in a block at least four blocks after their first. Falsified under 15%. "First seen" means first seen in the window, so new users are overstated and retention understated (left-censoring); stated in the result.
- Also reported: users, fills, volume per user percentiles by size bucket, active and new users per block.

## RX2: what the big solvers keep on stable swaps (local, from `rb_fu11_a_stable_spread.json`)
Same-symbol stable-to-stable simple swaps (the peg-neutral class of FU11), window 2026-08-07..2026-11-04. Margin = paid minus received by the user, summed per inferred solver (negative values kept).
- **H-RX2a (concentrated margin):** the 3 solvers with the largest net margin carry at least **50%** of the sum of positive solver margins. Falsified below 30%.
- **H-RX2b (a small pool next to NEAR's take):** the total margin over all solvers is under **25%** of the dollars delivered to the three revenue wallets over the same window (FU5: $4.74M); falsified above 50%. This is a lower bound on solver earnings (stable swaps with public legs only).
- Reported: solvers with negative net margin, the margin in bp by solver.

## RX3: who signs the transactions sent to `intents.near`? (`sql/rx/rx3_relayer.sql`, exact, full chain)
Transactions with receiver `intents.near`, 2025-01-01..2026-11-04, by signer, per month and per 7-day block ending 2026-11-04 (last 16 blocks).
- **H-RX3a (one relayer):** the top signer's share is at least **80%** in every month 2026-05 to 2026-10. Falsified if any of those months is under 60%.
- **H-RX3b (a handful of operators):** the top-5 share is at least **95%** in every one of those months. Falsified if any is under 85%.
- Reported: distinct signers, the top signer's name (an account name, not a person), its share by month and by 7-day block, and the minimum 7-day share. This is pre-window context for the pre-registered F4 relayer test, not a score of it; nothing from the forward window (2026-11-06 on) is read.

## RX4: who sends Intents NEAR to the liquid-staking pool and the Omni bridge? (added 2026-11-13 03:04 UTC, before the query runs; `sql/rx/rx4_lst_omni.sql`, staged `intents_events`)
Why: the contract-wide wNEAR books (FU10) show transfers to `lst-pool.near` (8.66M NEAR out, 4.01M in) and to `omni.bridge.near` (10.12M out, 5.92M in) that start in September 2026; a local look at the saved FU10 ledger (monthly totals by counterparty, read before this method was written and stated here) shows no flow to either in July and August beyond small amounts. Window 2026-07-07..2026-11-04.
- Withdrawal events on `intents.near` with receiver `lst-pool.near` or `omni.bridge.near`: the initiating Intents account, month and amount (wNEAR only, token read from the event).
- **H-RX4a (concentrated initiators):** the 3 largest source accounts carry at least **70%** of the NEAR sent to `lst-pool.near` through these events. Falsified below 40%.
- **H-RX4b (it is the solver family):** at least **50%** of that NEAR comes from the FU1 solver family (`solver-priv-liq.near`, `solver-multichain-asset.near`, `-escrow`, `-2`). Falsified below 10%. The same two tests for `omni.bridge.near`.
- If the events do not account for at least 80% of the wrap.near transfer totals of FU10 for the receiver, the shortfall is reported and the shares are for the covered part only. Ownership of any account is INFERRED.

## RX5: does the repo's capture ladder replicate from the chain? (added 2026-11-13 03:13 UTC, before it is computed; local)
The repo's ladder (`data/metrics.json`: all wallets 15.81% of net issuance, of which public collectors 4.53%, escrow unshields 11.25%, other 0.03%; 30 days to 2026-11-04; net issuance $12.71M) was built from `deliveries.csv` and the Explorer path. The rebuild's Q2 deliveries already equal `deliveries.csv` exactly; this recomputes the ladder from the chain's `native_withdraw` deliveries alone, split by the FU4 groups (escrow-funded group = the many-account group the escrow funds; public = `5880ad2b…`, `143f2bb4…`, `176121bd…`), priced at the daily NEAR price, over 2026-10-06..2026-11-04, divided by the repo's $12.71M.
- **H-RX5a:** the chain-derived all-wallet ratio is within **10%** (relative) of 15.81%. Falsified if it differs by more than 25%.
- **H-RX5b:** the escrow-funded share of delivered dollars is within **5 points** of 11.25 / 15.81 = 71.2%. Falsified if it differs by more than 15 points.
- The denominator is the repo's, not re-derived; the numerator is the only thing tested.

## RX6: do Intents' NEAR flows follow the NEAR price? (added 2026-11-13 03:13 UTC, before the query runs; `sql/rx/rx6_wrap_daily.sql`, staged `wrap_intents`)
Daily contract-wide wNEAR ledger (the FU10 line shapes) for 2026-07-07..2026-11-04; NEAR price from `data/raw/windows/near_price_daily_llama.json`. 17 complete 7-day weeks from 2026-07-07 (to 2026-11-01). Weekly net NEAR flow into Intents = (transfers in + refunds in) - (transfers out + refunds out + unwrap); weekly bridge-path deposits = transfers in from `bridge-mng.near` are not separable in this table, so total transfers in are used; weekly price return = last-day close over the previous week's last-day close minus 1.
- **H-RX6a (flows chase price):** Spearman rho of weekly net flow with the same week's price return is at least **+0.30** with a Monte Carlo permutation p at most 0.10 (20,000 permutations, seed 20261113). **Falsified** if rho is at most **-0.30** (flows lean against price). Between: no relation.
- **H-RX6b (lagged):** the same with the net flow of week t and the price return of week t+1, to see whether flows lead.
- Also reported: weekly net flow, unwrap and deposits in NEAR, and the share of weeks with net inflow. No causal reading is drawn (**INFERRED** only as a pattern).

## RX7: who made the September spike? (added 2026-11-13 03:15 UTC, before it is computed; local, from saved FU2b and FU7 outputs)
RX6 found that the weeks of 2026-09-15 and 2026-09-22 carry 31% of the window's gross NEAR flow through Intents. The question is whether that burst is broad or one operator's relay (FU7). Saved inputs: `rb_fu2b_a_daily.json` (wNEAR wrapped by `bridge-mng.near` per day, all of it passed to `intents.near`), `rb_fu7_a_summary.json` (`out_by_day`: NEAR sent by the relay `1244d552…` to `bridge-mng.near` per day), `rx6_wrap_daily.json` (transfers into `intents.near` per day).
- **Spike weeks:** 2026-09-15..09-28. **H-RX7a:** transfers in from `bridge-mng.near` are at least **60%** of all wNEAR transfers into `intents.near` in those two weeks (so the deposit path, not Omni/Ref/LST returns, drives it). Falsified under 30%.
- **H-RX7b (one operator):** the relay's NEAR is at least **40%** of what `bridge-mng.near` wrapped in those two weeks. Falsified under **15%**.
- Also reported for every week of the window: transfers in, bridge-mng's share, the relay's NEAR and its share of bridge-mng's deposits. Day mismatches between tables (UTC date of the log line versus the transaction) are small and not corrected.
