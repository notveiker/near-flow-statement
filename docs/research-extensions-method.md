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
