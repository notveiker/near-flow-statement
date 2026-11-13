# What the Confidential Intents flow is, and what the escrow releases move with (exploratory)

*Exploratory, chosen after the freeze (2026-11-13). It changes no pre-registered result, test, threshold or probability, and nothing here feeds the rating rule. F1-F4, P1-P3 and E1-E5 are scored as worded. Every chain day read by the committed queries is 2026-11-04 or earlier. All of it is recomputed by `make reproduce`. Terms are in the [glossary](glossary.md).*

`THESIS.md` left two questions to NEAR: which fees pay for the escrow releases, and what the confidential-treasury flow that DefiLlama's Intents volume counts from 2026-09-01 represents. Neither can be settled without NEAR's disclosure, because confidential swaps settle on FAR, a permissioned chain whose RPC is private. This file narrows both from the public side of the bridge.

## How the public side of a confidential swap looks

NEAR Intents' documentation ([sources-checked](sources-checked.md), row 5.6) describes the mechanism:

- **Shield.** Tokens enter `intents.far` "in exactly one way": a transfer on `intents.near` to the Treasury account (`51e8f94d…7cbe`, our "escrow"), after which the bridge mints the same amount on FAR.
- **Unshield.** An `imt_burn` on FAR, after which "the Treasury releases on `intents.near`".
- **A solver's swap.** The example solver's `swap` bundles the `token_diff` "(the actual swap)" with an `imt_burn` that unshields the received funds immediately.

So every confidential swap leaves public traces as treasury transfers, without its price or counterparty. An escrow release to a revenue wallet is an unshield. Whatever NEAR balance is burned on FAR to pay for it is not visible.

## 1. The treasury↔solver flow is swap volume

`sql/confidential_solver_blocks.sql` lists, for 2026-09-02, 10-08 and 10-22, every block in which a solver shielded or unshielded tokens. A solver is a counterparty with at least 20 shields and at least 20 unshields, with the two counts within 5% of each other. That rule selects eight `solver-*` accounts and one unnamed account. `pipeline/compute.py` (`confidential_flow`) matches each shield block, in block order, to the first unused unshield block of the same solver 1 to 20 blocks later whose value is equal within a tolerance.

| Day | Solver shields, $M | Matched within 3%, % of value | Matched within 1%, % | Matched pairs whose tokens differ, % | Median gap, blocks |
|---|---|---|---|---|---|
| 2026-09-02 | 18.4<!--n:conf_0902_solver_shield_m--> | 98.2<!--n:conf_0902_paired_3pct_pct--> | 91.6<!--n:conf_0902_paired_1pct_pct--> | 100.0<!--n:conf_0902_paired_other_token_pct--> | 7<!--n:conf_0902_paired_gap_median_blocks--> |
| 2026-10-08 | 69.9<!--n:conf_1008_solver_shield_m--> | 72.8<!--n:conf_1008_paired_3pct_pct--> | 63.4<!--n:conf_1008_paired_1pct_pct--> | 99.6<!--n:conf_1008_paired_other_token_pct--> | 8<!--n:conf_1008_paired_gap_median_blocks--> |
| 2026-10-22 | 38.5<!--n:conf_1022_solver_shield_m--> | 87.4<!--n:conf_1022_paired_3pct_pct--> | 70.1<!--n:conf_1022_paired_1pct_pct--> | 100.0<!--n:conf_1022_paired_other_token_pct--> | 8<!--n:conf_1022_paired_gap_median_blocks--> |

- **The pattern.** A solver shields token X and, about eight blocks later, unshields a different token Y of the same value. That is the public trace of one confidential swap seen from the solver's side, as the documentation describes it. Rebalancing would move the same token in and out. Under 1% of shield blocks hold a token without a price (0.63<!--n:conf_0902_shield_blocks_unpriced_pct-->%, 0.42<!--n:conf_1008_shield_blocks_unpriced_pct-->% and 0.59<!--n:conf_1022_shield_blocks_unpriced_pct-->%).
- **What is unmatched.** On 10-08, the busiest day, a quarter of the value is unmatched at 3%. Greedy matching in block order misses pairs when one solver runs overlapping swaps. Wider value differences (fees or price moves) also go unmatched. The unmatched value is not evidence of non-swap flow.
- **What the chain still does not show.** The user side of these swaps is partly hidden, because users can hold balances on FAR. The price each user paid is not shown. A user swap routed through two solvers leaves two solver pairs.

### What this does to the leg count

[`leg-count.md`](leg-count.md) read one treasury↔solver pair as one confidential swap and took one-sided confidential volume as half of all treasury transfers ("reading 1"). Solver shields are a smaller share of those transfers: 31.9<!--n:legcount_0902_solver_shield_over_treasury_pct-->%, 30.7<!--n:legcount_1008_solver_shield_over_treasury_pct-->% and 30.8<!--n:legcount_1022_solver_shield_over_treasury_pct-->% on the three days. The rest are non-solver shields and unshields, which are mostly the user side of the same swaps. Taking solver shields as one-sided confidential volume ("reading 3"):

| Day | Solver shields, $M | (DefiLlama − 2 × public one-sided) ÷ solver shields | k on reading 3 |
|---|---|---|---|
| 2026-08-18 | 4.8<!--n:legcount_0818_solver_shield_m--> | -0.04<!--n:legcount_0818_gap_over_solver_shield--> | 1.78<!--n:legcount_0818_k_solver--> |
| 2026-08-31 | 16.1<!--n:legcount_0831_solver_shield_m--> | 0.03<!--n:legcount_0831_gap_over_solver_shield--> | 1.59<!--n:legcount_0831_k_solver--> |
| 2026-09-02 | 18.4<!--n:legcount_0902_solver_shield_m--> | 1.55<!--n:legcount_0902_gap_over_solver_shield--> | 1.89<!--n:legcount_0902_k_solver--> |
| 2026-10-08 | 69.9<!--n:legcount_1008_solver_shield_m--> | 1.84<!--n:legcount_1008_gap_over_solver_shield--> | 1.92<!--n:legcount_1008_k_solver--> |
| 2026-10-22 | 38.5<!--n:legcount_1022_solver_shield_m--> | 1.62<!--n:legcount_1022_gap_over_solver_shield--> | 1.8<!--n:legcount_1022_k_solver--> |

- **From 2026-09-01, DefiLlama counts confidential swaps at close to both legs.** The part of its volume above both legs of public swaps is 1.55<!--n:legcount_0902_gap_over_solver_shield--> to 1.84<!--n:legcount_1008_gap_over_solver_shield--> times the solver shields. So k, DefiLlama's volume ÷ one-sided volume, is 1.8<!--n:legcount_k_solver_window_lo--> to 1.92<!--n:legcount_k_solver_window_hi--> on the window's two measured days. That is near the 2 of the halved basis, and far from reading 2's 3.77<!--n:legcount_k_public_window_lo--> to 4.01<!--n:legcount_k_public_window_hi-->. Before 09-01 the flow was on chain but not counted (−0.04 and 0.03).
- **Restated window figures (30 days to 2026-11-04, exploratory).** Captured take 8.97<!--n:legcount_take_captured_bp_solver_lo--> to 9.55<!--n:legcount_take_captured_bp_solver_hi--> bp of one-sided volume. Escrow releases 6.47<!--n:legcount_escrow_bp_solver_lo--> to 6.89<!--n:legcount_escrow_bp_solver_hi--> bp. 1Click's share of Intents volume 49.7<!--n:legcount_oneclick_share_solver_lo_pct-->% to 52.9<!--n:legcount_oneclick_share_solver_hi_pct-->%. Intents' share of the peer set 39.7<!--n:legcount_peer_share_solver_lo_pct-->% to 41.2<!--n:legcount_peer_share_solver_hi_pct-->%, against 38.6<!--n:intents_share_peerset_30d_net_pct-->% on the halved basis. These use the same method and the same caveat as `leg-count.md`: k is taken from two days, and nothing after 10-22 was measured.
- **Why not exactly 2.** If part of the solver flow is one user swap routed through two solvers, solver shields overstate one-sided volume and the true k lies nearer 2. Some non-swap flow may also be counted. The chain cannot separate the two.
- **The cross-check.** Valued with the same prices, the daily query's treasury total on each of the five days is 100.0<!--n:legcount_1022_daily_query_over_leg_query_pct-->% of the leg-count query's total (`legcount_*_daily_query_over_leg_query_pct` in `data/metrics.json`, the same on all five days).

## 2. The escrow releases move with confidential volume, not with 1Click

Escrow releases are the NEAR delivered to the revenue wallets through the escrow path (`escrow_unshield` in `data/raw/escrow/deliveries.csv`), priced at the day's close. `sql/confidential_treasury_daily.sql` gives daily solver shields from 2026-08-07 to 11-04. 97.0<!--n:conf_daily_solver_shields_priced_pct-->% of those transfers are priced, as stablecoins, NEAR or one of the majors. The other series come from the Intents Explorer (`data/raw/explorer/daily.json`). All are correlated over the 90 days.

| Correlation of daily escrow releases with… | Levels | Minus a centred 7-day mean | Day-over-day change of log(1 + x) |
|---|---|---|---|
| Confidential solver shields | 0.73<!--n:conf_rel_corr_solver--> | 0.61<!--n:conf_rel_corr_solver_detrended--> | 0.59<!--n:conf_rel_corr_solver_dlog--> |
| 1Click volume (Explorer) | 0.16<!--n:conf_rel_corr_oneclick--> | 0.24<!--n:conf_rel_corr_oneclick_detrended--> | 0.08<!--n:conf_rel_corr_oneclick_dlog--> |
| 1Click's explicit buyback fee | 0.35<!--n:conf_rel_corr_bbfee--> | 0.05<!--n:conf_rel_corr_bbfee_detrended--> | -0.03<!--n:conf_rel_corr_bbfee_dlog--> |

- **The same day fits best.** With releases one day after the volume the correlation is 0.52<!--n:conf_rel_corr_solver_lag1-->. With releases one day before, 0.49<!--n:conf_rel_corr_solver_lead1-->. On twelve weekly sums it is 0.94<!--n:conf_rel_corr_solver_weekly-->. The fit survives removing the common trend and differencing, so it is not just two series growing together.
- **The listed fees are paid elsewhere.** 1Click's explicit buyback fee arrives through collector A, whose priced inflows are 96.5<!--n:collector_a_vs_explicit_fees_pct-->% of the fees the Explorer lists. The escrow releases are therefore a separate stream, not those fees counted twice.
- **Their size.** Releases were 10.7<!--n:conf_rel_bp_of_solver_aug--> bp of solver shield volume in August (from 08-07), 13.2<!--n:conf_rel_bp_of_solver_sep--> in September and 17.3<!--n:conf_rel_bp_of_solver_oct--> in October, and 14.8<!--n:conf_rel_bp_of_solver_window--> bp over the 30 days to 11-04. Solver shields over those 30 days were $971.6<!--n:conf_solver_shields_window_m-->M.
- **Fixed proportions.** The buyback wallet received 1.14<!--n:conf_rel_bb_over_fe_aug-->, 1.32<!--n:conf_rel_bb_over_fe_sep--> and 1.11<!--n:conf_rel_bb_over_fe_oct--> times what the front-end fund received from the escrow in August, September and October (1.34<!--n:conf_rel_bb_over_fe_window--> over the window). Two streams that keep a steady ratio while both scale with confidential volume look like two fee lines on the same swaps.
- **The front-end fee moved to confidential settlement at the end of August.** Near-intents.org's 0.2% fee, as 1Click lists it to `fefundsadmin`, averaged $4.07<!--n:conf_fe_listed_usd_per_day_pre-->K a day from 08-07 to 08-28 and $0.28<!--n:conf_fe_listed_usd_per_day_post-->K from 08-29. Over the same spans, escrow releases to that fund rose from $3.89<!--n:conf_fe_escrow_usd_per_day_pre-->K to $19.38<!--n:conf_fe_escrow_usd_per_day_post-->K a day. The [second review](second-review.md), section 2, saw the same switch in near.com's public fee account. It came days before DefiLlama's volume began counting the treasury flow (2026-09-01).

## What this settles, and what it does not

- **Settled enough to use (inferred, not attested).** The escrow releases behave like fees charged on confidential swaps and unshielded the same day: they move with confidential volume day by day, at a fairly stable rate per dollar of that volume, in steady proportions between the two wallets. Releases that were one-off or discretionary would not track daily volume. This is the reading (i) that E1-E5 (`PREREG-ADDENDUM.md`, 2026-11-13 06:23 UTC) test forward. E4's reported-not-scored line, releases against volume outside the Explorer, pointed the same way.
- **Still unattested.** *Which* fee each release is: near.com's front-end fee, 1Click's platform fee on confidentially settled swaps, or the Confidential Infrastructure Fee of the 1Click terms ([`THESIS.md`](../THESIS.md), section 2). Nor is it shown whether every such fee reaches the wallets. Only NEAR can say. The range in `THESIS.md` stays a range; this evidence places the escrow rung's NEAR as recurring fee revenue rather than one-off transfers.
- **Not a share of fees.** Releases in basis points of solver volume are not a fee rate: solver volume overstates swap volume if some swaps pass two solvers, and fees taken in tokens other than NEAR are not in the releases.

## Recipe

1. `sql/confidential_treasury_daily.sql` (BigQuery, `crypto_near_mainnet_us.execution_outcomes`, about 162 GB): every successful `dip4` transfer into or out of the treasury from 2026-07-01 to 2026-11-04, summed per day, direction, token and counterparty class. Output `data/raw/bq/confidential_treasury_daily.json`, run by `NFS_BQ_MAX_GB=170 python3 -m pipeline.bq_run confidential_treasury`.
2. `sql/confidential_solver_blocks.sql` (about 4.2 GB): every solver shield and unshield block on 2026-09-02, 10-08 and 10-22, with tokens and raw amounts. Output `data/raw/bq/confidential_solver_blocks.json`, run by `python3 -m pipeline.bq_run confidential_solver`.
3. `python3 -m pipeline.compute` (`confidential_flow`, and the reading-3 lines of `leg_count`): the matching, the correlations and the restated figures. Prices come from `data/raw/coingecko/leg_count_prices.json` on the five measured days, and from stablecoins, `near_market_chart_365d.json` and `majors_90d.json` for the daily series.
