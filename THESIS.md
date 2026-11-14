# Can NEAR's Intents business grow into its dilution?

*A long-term investment thesis for NEAR, built on a token flow statement: what NEAR's token earns from NEAR Intents today, what its price assumes that becomes, and what would tell the two apart. Value capture is measured over the 30 days to 2026-11-04, and supply over the 90 days from 2026-08-07 to 2026-11-04. Every number followed by an `n:` comment is recomputed from committed data by `make reproduce`. Not investment advice.*

## The short version

NEAR mints about 88,295<!--n:net_issuance_near_per_day_window--> more NEAR a day than it burns. NEAR Intents, its cross-chain swap business, sends fees to three wallets that DefiLlama counts as NEAR's Intents revenue. Over the 30 days to 2026-11-04, the NEAR that arrived in those wallets was equal to 15.81<!--n:ladder_all_wallets_pct_of_issuance-->% of that new supply. We can trace 4.53<!--n:ladder_public_collectors_pct_of_issuance--> points of it on chain to public fee collectors. Almost all of the rest was released from the Confidential Intents escrow, and which fees paid for it cannot be seen from outside.

That is what the token earns today. The price asks for far more. Suppose Intents' fees had to carry NEAR's price alone, with the price rising 15<!--n:ic_base_r_pct-->% a year and the market cap ending at 25<!--n:ic_base_x-->× revenue in 2031. The fees would have to grow 84.9<!--n:ic_implied_cagr_r15_x25_pct-->% a year. The cross-chain venues we track grew 13.4<!--n:ic_market_cagr_1y_pct-->% last year. At that pace, and with Intents at its best share of the past twelve months, NEAR would have to take 2.5<!--n:ic_take_needed_vs_gross_x-->× the whole fee Intents charges.

So our answer is: not on today's evidence. Intents had the largest share of its peer set over the 30, 90 and 365 days to 2026-11-04, and the fees that reach NEAR are real. But at today's price NEAR is a bet on more than those fees. It is a bet on the L1 itself, on a much larger cross-chain market, or on a much higher take. The rating rule we froze in advance outputs Hold, which carries no view on NEAR.

We wrote our predictions down before we saw any outcome, and we publish every result. One hypothesis failed, two could not be decided, and two of the four one-week forecasts missed. [The scores are below](#how-our-predictions-scored-pre-registered).

*Labels: the hypothesis tests, the rating rule and the dated predictions are pre-registered. The flow statement and the investment case are exploratory, chosen after the freeze ([`PREREG-ADDENDUM.md`](PREREG-ADDENDUM.md)). Terms such as H1a, Hold, the ladder and the escrow are defined in the [glossary](docs/glossary.md).*

## The claim

The hopeful case for NEAR is that Intents' fees grow into the dilution its holders absorb. We tested that case.

NEAR's token captures value from Intents only through the fees routed to NEAR's revenue wallets. Those fees are real, and today they would pay for a fraction of NEAR's dilution. If Intents carried NEAR's price alone, the price would assume the fees grow 84.9<!--n:ic_implied_cagr_r15_x25_pct-->% a year to 2031 ([section 6.1](#61-what-the-price-assumes)). The peer set's volume has not grown that fast over any window in the data. Its fastest was 76.9<!--n:ic_market_cagr_3y_pct-->% a year, over the three years from the 2023 low.

This is a claim about what is measured and what is priced. It is not a valuation, and the Hold is not a recommendation. Value capture that does not pass through those wallets, or that cannot be seen on chain, is not in it. NEAR's market cap also prices the L1, which we do not value here.

## Evidence for

*Exploratory. The detail is in sections [1](#1-the-ladder-exploratory-post-freeze) and [2](#2-how-we-know-it-is-the-escrow-and-what-is-actually-missing-exploratory).*

The NEAR arrives, and we can count it. The 15.81<!--n:ladder_all_wallets_pct_of_issuance-->% is NEAR we watched reach the three wallets on chain. NEAR's own revenue dashboard (revenue.near.org, read on 2026-11-13) lists exactly these three as its "Traceable flow of revenue", although NEAR has not said in words that they are all of its Intents revenue wallets ([`docs/sources-checked.md`](docs/sources-checked.md), row 5.4).

It also behaves like fee revenue. Below, a point is one percentage point of net issuance. Of the 15.81<!--n:ladder_all_wallets_pct_of_issuance--> points, 4.53<!--n:ladder_public_collectors_pct_of_issuance--> trace to two public fee collectors and 11.25<!--n:ladder_escrow_unshields_pct_of_issuance--> arrived as releases from the Confidential Intents escrow. Those releases move with confidential swap volume, day by day. The correlation is 0.73<!--n:conf_rel_corr_solver--> on the same day, against 0.16<!--n:conf_rel_corr_oneclick--> for 1Click's public volume. Fees on confidential swaps would behave that way, though which fee they are is unattested ([`docs/confidential-flow.md`](docs/confidential-flow.md)).

And Intents leads its market. Its share of the peer set's reported volume was 55.7<!--n:intents_share_peerset_30d_pct-->% over the 30 days to 2026-11-04 and 62.1<!--n:intents_share_peerset_365d_pct-->% over the 365 days.

## Evidence against

*Exploratory, except H1a. The detail is in sections [3](#3-evidence-against-who-else-gets-paid-usage-valuation-context-exploratory), [4](#4-the-supply-side-pre-registered-tests-with-labelled-extras) and [6](#6-the-investment-case-what-the-price-assumes-what-the-evidence-supports-exploratory).*

The price is far ahead of the fees. Captured revenue would have to go from $19.6<!--n:ic_rev_90d_ann_m-->M a year to $424<!--n:ic_required_rev_2031_m-->M by 2031. With the market at its last-year pace and Intents at its twelve-month-high share, NEAR's take would have to rise from 4.13<!--n:ic_take_90d_bp--> bp of volume to 37.4<!--n:ic_take_needed_bp--> bp. Today captured revenue would pay for 16.6<!--n:fwd_coverage_now_pct-->% of the dollar value of NEAR's dilution, and in our base scenario it pays for 44.6<!--n:ic_base_coverage_2031_pct-->% in 2031. Only the most favourable combinations reach what the price would assume (section 6.3).

What reaches NEAR is also smaller and less certain than the headline. We can verify a range, 4.53<!--n:ladder_public_collectors_pct_of_issuance-->% to 15.81<!--n:ladder_all_wallets_pct_of_issuance-->% of net issuance. Even the top is about a sixth of issuance, and this data does not show who buys the rest. None of the three wallets burns, stakes or locks the NEAR it receives (section 1). Listed partner fees were 1.44<!--n:partners_kept_vs_near_rev_floor_x-->× to 2.22<!--n:partners_kept_vs_near_rev_high_x-->× NEAR's entire captured revenue (section 3).

The supply side and the usage numbers do not help. H1a, a pre-registered test, failed: net staking outflow was 6.56<!--n:h1a_ratio_as_written_x-->× staking rewards over the 90 days, where a pass needed under 0.5×. Daily active accounts averaged 61.6<!--n:active_accounts_30d_k-->K over the 30 days to 2026-11-04, a change of -77.1<!--n:active_accounts_30d_yoy_pct-->% on the same days a year earlier. BigQuery shows that 98.5<!--n:usage_bq_tg_share_of_signer_drop_pct-->% of that fall is one application, HOT Wallet's Telegram accounts (section 3).

## What would change our mind, in short

We would become more positive if NEAR attested which fees fund the escrow releases and they proved to be recurring fee revenue. That would put value capture toward the top of the range. A take rising toward the 37.4<!--n:ic_take_needed_bp--> bp the price would need would also move us. So would a cross-chain market growing faster than 33.2<!--n:rating_g_req_pct-->% a year, the rating rule's required growth, for several years.

We would become more negative if the escrow releases stopped arriving daily or stopped tracking confidential volume. A take falling back toward 1.36<!--n:ic_take_min_bp--> bp, its lowest month since the fee switch, would move us the same way. So would Intents' share falling toward its twelve-month low of 48.5<!--n:ic_share_min_pct-->%.

The frozen rating moves to Buy only if H1b passes, and that needs sourced exchange labels for many more of the top-100 NEAR receivers. One event is pending: the on-chain timelock of HSP-029, the issuance cut, ends on 2026-11-16. The rating's required growth assumes the cut is in force, and without it the figure is 46.8<!--n:rating_g_req_no_hsp029_pct-->% a year. The full table is [section 5](#5-what-would-change-our-mind), and the values to watch are in [section 6.8](#68-signposts).

## How our predictions scored (pre-registered)

Before the first BigQuery flow result this repository records, we froze three hypotheses with our priors, a rating rule, four forecasts for the week of 2026-11-06 to 2026-11-13, and three longer-dated predictions. `PREREG.md` is the authoritative text. `pipeline/score_forward.py` scored F1-F4 on 2026-11-14 at 07:02 UTC as PASS, MISS or not scorable, as `PREREG.md` words them, and wrote the result to `data/forward/score_20261114T070207Z/`. Every outcome is published, misses included.

| ID | What we predicted | Our probability | What happened | Result |
|---|---|---|---|---|
| H1a | Most staking rewards stay staked: net staking outflow under 0.5× staking rewards | 0.70 | 6.56<!--n:h1a_ratio_as_written_x-->× | Fail |
| H1b | Less NEAR reaches exchanges than is minted | 0.55 | Net exchange inflow of 4.42<!--n:h1b_net_inflow_lower_m-->M to 152.45<!--n:h1b_net_inflow_upper_m-->M NEAR against 8.0098<!--n:h1a_gross_issuance_90d_m-->M minted | Inconclusive |
| H1c | Identified buying is at least 25% of net exchange inflow | 0.40 | 33.48<!--n:h1c_ratio_lower_pct-->% of the lower bound, 0.97<!--n:h1c_ratio_upper_pct-->% of the upper | Inconclusive |
| Rating | The frozen rule's output | none stated | H1b decides it, and H1b is inconclusive | Hold |
| F1 | The buyback wallet's balance at the first final block after 2026-11-14 00:00 UTC is in [2.21M, 2.40M] NEAR | 0.70 | 2,279,854 NEAR at block 224,435,951 | PASS |
| F2 | Mean net supply increase per day (Nearblocks `total_supply`, 2026-11-06 → 11-13) is in [86.0K, 89.5K] NEAR | 0.75 | 86,208 NEAR a day over 8 daily deltas | PASS |
| F3 | The captured take rate over the window is below 4.0 bp | 0.65 | 4.22 bp ($473,131 of revenue on $1.121B of volume) | MISS |
| F4 | NEAR Intents' share of peer-set volume (reported basis) over the window is at least 50% | 0.70 | 37.2% | MISS |
| P1 | Intents' 365-day share of the peer set is at least 55% | 0.65 | Resolves 2027-05-04 | Open |
| P2 | 90-day captured Intents revenue is at least $6.0M (it was $4.84<!--n:rating_r90_usd_m-->M for the 90 days to 2026-11-04) | 0.50 | Resolves 2027-05-04 | Open |
| P3 | 90-day captured revenue ÷ USD value of net new supply is at least 25% | 0.35 | Resolves 2027-11-04 | Open |

**H1b and H1c could not be decided** because exchange labels are missing. Only 20.0<!--n:h1b_coverage_count_pct-->% of the top-100 NEAR receivers carry an exchange label, and 10.0<!--n:h1b_coverage_tier1_count_pct-->% a cited one. The rest are labelled by our own sweep rule. The pre-registration requires 50%, so net exchange inflow is a range and both tests stay open.

**The Hold carries no view on NEAR.** Below 50% label coverage, H1b can come out pass or inconclusive but never fail. Observed revenue growth is 619.0<!--n:rating_g_obs_pct-->% a year, or 71.4<!--n:rating_g_obs_near_pct-->% in NEAR terms. That is far above the rule's Avoid line of 16.6<!--n:rating_g_avoid_line_pct-->% a year, which is half of the required 33.2<!--n:rating_g_req_pct-->%. So the rule could only ever have output Buy or Hold, and had H1b failed it would also have said Hold. The observed growth is a step in the share of fees NEAR captures, not growth in activity. Over the same two 180-day windows gross fees rose 3.4<!--n:sr_fees_180d_change_pct-->% and volume 29.6<!--n:sr_volume_180d_change_pct-->% ([second review](docs/second-review.md), section 6).

**The four forecasts.** Our stated probabilities implied 2.8 passes, and a 0.76 chance of at least one miss if the four were independent. Two passed. The Brier score is 0.266, which is (0.30² + 0.25² + 0.65² + 0.70²) ÷ 4. Lower is better, and a forecaster who always said 0.5 would score 0.25, so we did slightly worse than that. No test was unscorable. We chose to report the Brier score after the freeze and before any F1-F4 outcome was scored (`PREREG-ADDENDUM.md`, 2026-11-13 01:50 UTC entry). It changes no test.

**What F4's miss means.** In the scoring week the peer set's reported volume split THORChain 53.7%, NEAR Intents 37.2%, Chainflip 8.1% and Maya 1.0% (summed from `data/forward/score_20261114T070207Z/snapshot.json`). THORChain's volume had been smaller the week before. One week does not move the 30-, 90- or 365-day shares the investment case uses, and P1 tests the 365-day share on 2027-05-04. But the week is the first sign against the share assumption, and the signposts watch it.

**Still to come.** P1-P3 resolve in 2027 and cannot be scored yet. The escrow-release forward tests E1-E5 are exploratory, not pre-registered. We added them after the freeze but before reading any escrow delivery after 2026-11-04. They cover 2026-11-15 to 12-14 and are scored from 2026-12-16 (`PREREG-ADDENDUM.md`, 2026-11-13 06:23 UTC entry).

## Update to 2026-11-13 (exploratory)

*Chosen on 2026-11-14, after F1-F4 were scored.*

Everything above stops at 2026-11-04, the pre-registered cutoff. We ran the same calculations on DefiLlama, CoinGecko and Nearblocks data fetched again on 2026-11-14, which run to 2026-11-13 (`pipeline/update.py`).

The gap narrowed. NEAR's price would now assume captured revenue grows 79.8<!--n:upd_ic_implied_cagr_r15_x25_pct-->% a year to 2031, which is still faster than any window in the data. NEAR would need 1.6<!--n:upd_ic_take_needed_vs_gross_x-->× Intents' whole gross fee. In the base case captured revenue would pay for 62.2<!--n:upd_ic_base_coverage_2031_pct-->% of NEAR's dilution in 2031. Two things moved: NEAR's market cap fell to $4.48<!--n:upd_mcap_usd_b-->B, and 90-day captured revenue rose to $21.2<!--n:upd_ic_rev_90d_ann_m-->M at an annual rate.

Intents' share of the peer set fell to 45.8<!--n:upd_intents_share_peerset_30d_pct-->% over 30 days as THORChain's volume rose. THORChain's share was 37.6<!--n:upd_thorchain_share_peerset_30d_pct-->%. Intents still leads over 30, 90 and 365 days.

The pre-registered tests, the value-capture ladder and the 1Click charts stay at 2026-11-04. Their inputs need a BigQuery scan or the Explorer API key.

## Where to check each judging criterion

The track brief says the score depends on "evidence someone else can reproduce". nearhackathon.com adds that previous NEAR hackathons evaluated technical implementation, design, impact, originality and sustainability, and offers that as a guide.

| Criterion | Where to check it |
|---|---|
| Reproducible evidence | The README's "do X, see Y" steps; `make reproduce`; `python3 -m pipeline.check --numbers`; the offline tests; `bash scripts/fresh_clone_check.sh` |
| Technical implementation | A standard-library pipeline over archival RPC, BigQuery and keyless APIs. Every revenue-wallet delivery is traced in `data/raw/escrow/deliveries.csv`, and the frozen scorer is `pipeline/score_forward.py` |
| Design | A static dashboard, `site/index.html`: the answer and four headline figures on the first screen, then four tabs of charts, each with its query, its data and one plain sentence on what it shows. It has light, dark and phone layouts, and `site/story.html` tells the same case one chart per screen. Markers tie the figures in the prose to `data/metrics.json`, and a check fails if one disagrees |
| Impact | It turns the claim that Intents revenue buys NEAR into a checkable range. It names the one disclosure that would settle it, a per-stream attestation of the escrow releases. And it shows how far public data gets alone: the releases track confidential swap volume ([`docs/confidential-flow.md`](docs/confidential-flow.md)) |
| Originality | A pre-registration frozen before the first BigQuery flow result the repository records, and a ladder that separates what is traceable on chain from what is not |
| Forward-looking models | `pipeline/investment_case.py` holds the reverse DCF of what the price assumes, the market × share × take split, the scenarios, a sensitivity table, peer valuation and the signposts. `pipeline/model.py` is a Monte Carlo of coverage to 2031 with dated forecasts (M1-M4). Both are standard library and recomputed by `make reproduce` (section 6) |
| Sustainability | It re-runs offline from committed snapshots. P1-P3 resolve in 2027, and the forward tests are scored with misses included |

The gaps against the track prompt are in [Limits](#limits). The BigQuery usage queries the brief asks for (daily active accounts, transaction counts, contract usage) were run on 2026-11-13, after the freeze, and are exploratory ([`docs/usage.md`](docs/usage.md)).

## 1. The ladder (exploratory, post-freeze)

The ladder sorts the NEAR that reached the revenue wallets by how far we can trace it. Each rung is a percentage of net issuance.

| Rung, 30 days to 2026-11-04 | % of net issuance |
|---|---|
| NEAR delivered to all three revenue wallets | 15.81<!--n:ladder_all_wallets_pct_of_issuance--> |
| … of which the buyback wallet alone | 11.00<!--n:ladder_buyback_only_pct_of_issuance--> |
| Traceable to two recurring public fee collectors | 4.53<!--n:ladder_public_collectors_pct_of_issuance--> |
| … of which fees from publicly settled swaps | 3.97<!--n:ladder_collectors_public_swap_pct_of_issuance--> |
| … of which fees paid from escrow-funded single-use accounts | 0.56<!--n:ladder_collectors_escrow_funded_pct_of_issuance--> |
| Released from the Confidential Intents escrow; moves with confidential volume, fee stream unattested | 11.25<!--n:ladder_escrow_unshields_pct_of_issuance--> |
| One other recurring source | 0.03<!--n:ladder_other_pct_of_issuance--> |

**How to read it.** The rungs are not nested. Collectors + escrow + the other source = all three wallets. The buyback-wallet line is a subset of the total, and the two "of which" lines split the collector rung. Counting the 0.56<!--n:ladder_collectors_escrow_funded_pct_of_issuance--> points of fees paid from escrow-funded accounts, 11.81<!--n:ladder_escrow_all_pct_of_issuance--> points passed through the escrow in all. DefiLlama's revenue adapter counts three wallets, but only two were active in the window. `1csfundsadmin.sputnik-dao.near` received no NEAR, so everything arrived at `buybacks.multisignature.near` and `fefundsadmin.sputnik-dao.near`.

**The denominator.** Net issuance is 88,295<!--n:net_issuance_near_per_day_window--> NEAR/day, from archival `total_supply` at blocks 218,718,000 and 223,087,766 (`data/raw/escrow/issuance_reads.json`), matched to the window. `PREREG.md`'s table has an older figure, 15.7<!--n:coverage_rev_near_30d_pct-->% on 88.2<!--n:net_issuance_near_per_day_30d_k-->K NEAR a day. That figure converts DefiLlama's USD revenue to NEAR at daily prices, while the 15.81<!--n:ladder_all_wallets_pct_of_issuance-->% above counts the NEAR itself. They agree closely.

**The total matches DefiLlama, which counts the same wallets.** Our three-wallet total is 418.8<!--n:revwallets_near_k-->K NEAR. Compared in USD, that is 100.9<!--n:revwallets_vs_llama_rev_pct-->% of DefiLlama's reported Intents revenue for the same days. DefiLlama counts what arrives at the same three wallets from outside them, and leaves out internal hops between them. So this confirms the total that arrived, not which fee stream paid for it. Its adapter takes the three wallets from NEAR's own Dune query, so the match checks our pricing and our wallet list. It is not a count from a second source.

### Arrival is not removal

None of the three wallets burns, stakes or locks its NEAR. NEAR's revenue dashboard says the buybacks "permanently remove NEAR from circulation", but its FAQ says only that product revenue "can be deployed" for buybacks or locking. The buyback wallet held 2.187<!--n:buyback_wallet_near_m-->M NEAR at the last block in the committed chain data (223,230,811<!--n:rpc_block-->, 2026-11-05 22:51 UTC, known at the freeze). The F1 score reads the balance again on 2026-11-14. What happens to that NEAR next is not in the data.

The two active wallets are also not alike. Of the points, 11.0<!--n:ladder_buyback_only_pct_of_issuance--> arrived in the buyback wallet. The other 4.81<!--n:ladder_frontend_only_pct_of_issuance--> arrived in the front-end fund, `fefundsadmin.sputnik-dao.near`, which NEAR Intents' fee page names as the recipient of the 0.2% fee on near-intents.org. That fund has never sent NEAR to the buyback wallet, and its signers can change its rules or its code with one vote. Forwarding the fees at all is a permission in the 1Click terms ("may be directed"), not an obligation.

### The ratio moves with price and issuance policy

From the first to the last 30-day block of the supply window, captured revenue in dollars (DefiLlama) rose 118.9<!--n:sr_revenue_usd_first_to_last_block_pct-->%, while the NEAR arriving in the wallets fell 13.8<!--n:sr_near_arrived_fall_first_to_last_block_pct-->%. Against the issuance rate before the 2025-10-29 inflation cut, the same NEAR would be about 7.9<!--n:sr_ladder_at_old_cap_pct-->% of net issuance ([second review](docs/second-review.md), sections 1 and 5).

### Who funded the collectors' fees (added 2026-11-13)

`sql/collector_inflow_funders.sql` classifies all 330,260<!--n:collectors_transfers_n--> transfers into the two collectors in the window by sender. Its totals equal `data/raw/bq/collector_inflows.json` for every day, collector and token.

Collector A received 64,855<!--n:collector_a_escrow_funded_n--> fees from accounts the escrow had funded. Collector B received none (0<!--n:collector_b_escrow_funded_n-->). Those accounts are single-use. Every one of them paid a collector once (100.0<!--n:collector_escrow_funded_sender_single_tx_pct-->%), and 99.8<!--n:collector_escrow_funded_funded_once_pct-->% were funded by the escrow once. The median gap from funding to fee was at most 6<!--n:collector_escrow_funded_lag_blocks_median_max--> blocks, and the longest was 278,526<!--n:collector_escrow_funded_lag_blocks_max--> (`sql/collector_funder_checks.sql`). Every other sender's transfer came with a public swap (`token_diff`) for that sender in the same receipt (100.0<!--n:collector_public_swap_with_token_diff_pct-->%).

The two classes overlap. Of the escrow-funded transfers, 12,846<!--n:collector_escrow_funded_with_diff_n--> (19.8<!--n:collector_escrow_funded_with_diff_pct-->%) also carried a `token_diff` for the sender in the same receipt, so they were public swaps by accounts the escrow had funded. Of these, 10,633<!--n:collector_escrow_funded_with_diff_pre_n--> came before 2026-10-27 and 2,213<!--n:collector_escrow_funded_with_diff_post_n--> from then. We count them as escrow-funded. Their share of the USD value is not computed, because the committed amounts are not split by that flag.

We weight the shares by USD value, because the collectors' NEAR comes from all their fee tokens. Collector A's wNEAR fees were 11.8<!--n:collector_a_wnear_inflow_near_k-->K NEAR against 97.6<!--n:collector_a_delivered_near_k-->K NEAR delivered. Each day's NEAR delivered takes that day's share, since collector A delivers the day it is paid. The correlation of its daily fees with its deliveries is 0.93<!--n:collector_a_inflow_delivery_corr_lag0--> on the same day and 0.45<!--n:collector_a_inflow_delivery_corr_lag1--> a day later. The result is 105.2<!--n:ladder_collectors_public_swap_near_k-->K NEAR from public swaps and 14.8<!--n:ladder_collectors_escrow_funded_near_k-->K NEAR from the escrow.

Other weightings give nearly the same escrow-funded figure, with one exception.

| Weighting | Escrow-funded points |
|---|---|
| By USD value, day by day (the figure used) | 0.56<!--n:ladder_collectors_escrow_funded_pct_of_issuance--> |
| Pooled before and after 2026-10-27 instead of by day | 0.55<!--n:ladder_collectors_escrow_funded_pooled_pct_of_issuance--> |
| With the 12.2<!--n:collector_a_unpriced_transfers_pct-->% of collector A's transfers in unpriced tokens valued at their class mean | 0.58<!--n:ladder_collectors_escrow_funded_imputed_pct_of_issuance--> |
| By transfer count | 1.13<!--n:ladder_collectors_escrow_funded_by_count_pct_of_issuance--> |

The count overstates it. Before 2026-10-27, escrow-funded fees averaged $0.2<!--n:collector_a_escrow_funded_mean_fee_pre_usd--> against $2.85<!--n:collector_a_public_swap_mean_fee_pre_usd--> for public ones.

The escrow-funded share of collector A's fee value has climbed. It was 2.4<!--n:collector_a_escrow_usd_share_pre_pct-->% over 10-06 to 10-26, on 28.0<!--n:collector_a_escrow_count_share_pre_pct-->% of transfers. From 10-27 it was 39.4<!--n:collector_a_escrow_usd_share_post_pct-->%, rising from 5.7<!--n:collector_a_escrow_usd_share_first_post_day_pct-->% on 10-27 to 96.0<!--n:collector_a_escrow_usd_share_last_day_pct-->% on 11-04. Escrow-funded fees appear from the window's first day, which fits the gradual move to confidential settlement that the second review saw in samples. The daily table and the method are in [`docs/collector-funders.md`](docs/collector-funders.md).

### The escrow share stepped up once, at the end of August

This is the share of the buyback wallet's NEAR that arrived via the escrow. By month it was 17.5<!--n:escrow_share_buyback_2026_07_pct-->% in July (from 07-07), 28.6<!--n:escrow_share_buyback_2026_08_pct-->% in August, 53.0<!--n:escrow_share_buyback_2026_09_pct-->% in September and 57.4<!--n:escrow_share_buyback_2026_10_pct-->% in October. By date it is one step after a drift: 23.9<!--n:sr_escrow_share_0713_0828_pct-->% over 07-13 to 08-28, then 55.1<!--n:sr_escrow_share_0903_1026_pct-->% over 09-03 to 10-26 and 56.4<!--n:sr_escrow_share_1027_1104_pct-->% from 10-27 to 11-04.

The step coincides with a change at near.com's public fee account (`APP_FEE_RECIPIENT`). That account all but stopped paying the front-end fund: 1,940<!--n:sr_frontend_public_fee_near_per_day_before--> NEAR a day over 07-07 to 08-28, against 107<!--n:sr_frontend_public_fee_near_per_day_after--> after. Across the same break, escrow releases to that fund rose from 1,399<!--n:sr_frontend_escrow_near_per_day_before--> to 4,901<!--n:sr_frontend_escrow_near_per_day_after--> NEAR a day ([second review](docs/second-review.md), section 2).

The history has one limit. Before 2026-10-06, the funding of the single-use deliveries is mostly attributed from samples. From that date the funding hop of every single-use (escrow-path) delivery in the window is traced.

### No valuation is made here

The range is the finding, not either end. If a model needs one number, 15.81<!--n:ladder_all_wallets_pct_of_issuance-->% is what reached the wallets and 4.53<!--n:ladder_public_collectors_pct_of_issuance-->% is what is traced to public fee collectors (3.97<!--n:ladder_collectors_public_swap_pct_of_issuance-->% to publicly settled swaps). Neither feeds the frozen rating rule.

## 2. How we know it is the escrow, and what is actually missing (exploratory)

**What an unshield looks like on chain.** A confidential withdrawal shows on chain as the escrow paying the exact amount to a fresh account, which then withdraws it to a revenue wallet. That is our observation. The documentation describes the release from the Treasury, not this pattern. In the window, all 909<!--n:escrow_funded_exact_30d_n--> such deliveries were funded by the escrow for the exact amount, to the yoctoNEAR (100.0<!--n:escrow_funded_exact_30d_pct-->%).

**The escrow's identity is documented.** Account `51e8f94d…7cbe` is `PRIVATE_TREASURY_ACCOUNT_ID` in NEAR's Confidential Intents docs, "a production constant shared by all participants". The docs call it the Treasury and say it backs each confidential token one for one; "escrow" is our word for it.

**Anyone can re-check it.** Every delivery is in `data/raw/escrow/deliveries.csv`. A funding transfer is there too for every single-use delivery in the 30-day window (909<!--n:escrow_single_use_30d_n-->) and for a traced sample before it. `python3 -m pipeline.fetch_escrow verify --all` re-reads every row from FastNEAR and archival RPC, with no key. Its output of 2026-11-08 is committed (`data/raw/escrow/verify_all.json`).

**What the re-check does and does not show.** Of the 3,597<!--n:escrow_recheck_rows_n--> rows, 3,587<!--n:escrow_recheck_rows_ok_n--> pass every check. The other 10<!--n:escrow_recheck_failed_n--> fail on block height alone, one to three blocks off. The table holds the block that includes the receipt, and the check compares the block that executes it. So the command exits with status 1 on the committed data. All 1,051<!--n:escrow_recheck_funding_hops_n--> funding transfers pass, including all 909<!--n:escrow_recheck_window_funding_ok_n--> of the window's single-use deliveries.

The 100.0<!--n:escrow_funded_exact_30d_pct-->% above tallies two columns of the table (`funder` and `exact_amount_flag`) over the window's single-use deliveries. Which deliveries are single-use does not depend on those columns. It follows from the committed BigQuery output of the arrivals, and the re-read confirmed the recorded funding transfer of every one of them on the chain.

**The funding scan, re-derived (added 2026-11-13).** The SQL of the original funding scan is not in this repository, and its BigQuery job could not be retrieved on 2026-11-13. A new query, `sql/escrow_funding_scan.sql`, re-derives the funding from the public dataset alone. It finds the same 1,262<!--n:escrow_rescan_deliveries_n--> deliveries in the window, and all 1,262<!--n:escrow_rescan_table_rows_matched_n--> table rows match one. Of those deliveries, 909<!--n:escrow_rescan_single_use_n--> were made by an account that delivered once. For 909<!--n:escrow_rescan_reproduced_n--> of those the query finds the same account, the same funding receipt, a funding of the exact amount, one funding only and no other inflow. So, for the window, the escrow rung no longer rests on uncommitted code. Two gaps remain. The code that assigned the table's path labels is still not committed, and before 2026-10-06 the funding hops are sampled. Details: [`docs/sources-checked.md`](docs/sources-checked.md), sections 2 and 3.

**What is missing is attestation, not NEAR.** The NEAR verifiably arrived. Two candidate NEAR-side fee streams fit, and the public chain cannot split the 11.25<!--n:ladder_escrow_unshields_pct_of_issuance--> points between them.

*near.com's fees.* NEAR says near.com swaps "direct 100% of fees to a NEAR revenue wallet", without naming which. The same answer says swaps through third-party partners are "split 50/50 between NEAR and the partner"; the arithmetic in section 3 tests that. near.com's own code names three fee-related accounts. We discuss two of them and leave out the third, `APP_FEE_DISTRIBUTOR`. `APP_FEE_RECIPIENT` (`176121bd…`) withdrew to the front-end fund (`fefundsadmin`) in every delivery of it in our table (2026-07-07 to 2026-10-21), and to the buyback wallet in none. `CONFIDENTIAL_FEE_RECIPIENT` (`60a0d43b…`) appears nowhere in FastNEAR's public index of the chain. Calling them the public-mode and confidential-mode fee accounts is our reading of those names.

*The Confidential Infrastructure Fee.* The 1Click terms (Schedule 1 §6.2, §6.4) say Intents Technology "sets, charges, and retains" it on confidential swaps, with no share to integrators. They state no rate ("if any", §6.3), and the public fee pages do not mention confidential swaps, so the terms say who would keep such a fee, not that one is charged. Schedule 1 §1.7 adds that infrastructure fees "may be directed by the 1Click Service to a designated fee recipient in connection with NEAR ecosystem infrastructure, development and growth activities", and names no recipient. Forwarding any of it to NEAR's wallets would be a choice, not a documented fact.

**What the public side does show (added 2026-11-13).** Both candidates are fees on confidential swaps, and the releases behave like such fees.

| Daily escrow releases, compared with | Correlation |
|---|---|
| Confidential solver volume, same day | 0.73<!--n:conf_rel_corr_solver--> |
| The same, with a 7-day trend removed | 0.61<!--n:conf_rel_corr_solver_detrended--> |
| The same, on day-over-day changes | 0.59<!--n:conf_rel_corr_solver_dlog--> |
| 1Click's public volume | 0.16<!--n:conf_rel_corr_oneclick--> |
| 1Click's listed buyback fee, which arrives through collector A instead | 0.35<!--n:conf_rel_corr_bbfee--> |

Releases ran at 14.8<!--n:conf_rel_bp_of_solver_window--> bp of solver volume over the window. The buyback wallet got a steady 1.11<!--n:conf_rel_bb_over_fe_oct--> to 1.34<!--n:conf_rel_bb_over_fe_window--> times the front-end fund's share. Near-intents.org's listed 0.2% fee fell from $4.07<!--n:conf_fe_listed_usd_per_day_pre-->K to $0.28<!--n:conf_fe_listed_usd_per_day_post-->K a day after 2026-08-28, while escrow releases to the front-end fund rose from $3.89<!--n:conf_fe_escrow_usd_per_day_pre-->K to $19.38<!--n:conf_fe_escrow_usd_per_day_post-->K. Releases that were one-off or discretionary would not track daily volume. This still does not say which fee each release is ([`docs/confidential-flow.md`](docs/confidential-flow.md)).

**The falsifier.** A per-stream attestation by NEAR, saying which fees fund which escrow releases, would turn the range into one number. Nothing here alleges misconduct. This is consistent with a privacy feature working as documented, and the question is auditability. Since 2026-10-27 attestation may be the only route left: NEAR Intents' changelog says 1Click swaps now settle confidentially, so the public rung is expected to thin out (Limits).

## 3. Evidence against: who else gets paid, usage, valuation context (exploratory)

### Who else gets paid (1Click, 30 days)

These numbers come from the NEAR Intents Explorer API, which needs a partner key, and from on-chain wallet arithmetic. Details: [`docs/intents-fee-flows.md`](docs/intents-fee-flows.md), [`docs/partner-concentration.md`](docs/partner-concentration.md).

**NEAR's captured take (a pre-freeze observation, from `PREREG.md`'s table).** NEAR's captured revenue was 4.98<!--n:take_captured_bp_30d--> bp of reported volume, 32.5<!--n:capture_share_30d_pct-->% of gross fees. Reported volume counts more than one side of a swap, so the take on one-sided volume is higher.

| Volume basis | Captured take |
|---|---|
| Reported volume | 4.98<!--n:take_captured_bp_30d--> bp |
| One-sided, taking confidential solver shields as one-sided confidential volume | 8.97<!--n:legcount_take_captured_bp_solver_lo--> to 9.55<!--n:legcount_take_captured_bp_solver_hi--> bp |
| The two earlier readings of [`docs/leg-count.md`](docs/leg-count.md) | 6.76<!--n:legcount_take_captured_bp_lo--> to 7.18<!--n:legcount_take_captured_bp_hi--> bp, and 18.81<!--n:legcount_take_captured_bp_public_lo--> to 20.0<!--n:legcount_take_captured_bp_public_hi--> bp |

The solver reading is the one the chain supports. It is exploratory and comes from two measured days in the window ([`docs/confidential-flow.md`](docs/confidential-flow.md)). F3 is scored on the reported basis, as `PREREG.md` words it.

**Listed partner fees exceed NEAR's captured revenue.** How far depends on how the front-end fund's NEAR is treated.

| Reading | Listed partner fees ÷ NEAR's entire captured revenue |
|---|---|
| None of NEAR's revenue came out of partner fees | 2.22<!--n:partners_kept_vs_near_rev_high_x-->× |
| None of the front-end fund's NEAR is partner money, tighter reading | 1.81<!--n:partners_kept_vs_near_rev_low_tight_x-->× |
| None of the front-end fund's NEAR is partner money | 1.75<!--n:partners_kept_vs_near_rev_low_x-->× |
| The front-end fund's escrow arrivals may be partner money too | 1.44<!--n:partners_kept_vs_near_rev_floor_x-->× |

The tighter reading treats collector B's NEAR as quote improvement rather than a share of partner fees. That role is inferred, not proven. On the last reading, NEAR's share of the fees on partner swaps with no buyback entry is at most 37.0<!--n:near_share_of_partner_fees_max_wide_pct-->% ([second review](docs/second-review.md), section 10). On partner swaps with no buyback fee entry, at most 22.4<!--n:near_share_of_partner_fees_max_pct-->% of fees reaches NEAR's buyback wallet, or 19.6<!--n:near_share_of_partner_fees_max_tight_pct-->% on the tighter reading.

The per-swap sample shows the listed fee leaving the swap. A payment of about the listed amount reaches an account other than NEAR's two fee collectors for every non-zero partner fee entry except one. For SwapKit that is 102<!--n:fee_ev_swapkit_fees_paid_onchain_n--> of 112<!--n:fee_ev_swapkit_fees_listed_n--> listed entries. The other 10<!--n:fee_ev_swapkit_fees_zero_rate_n--> list a zero rate, so nothing is owed on them. Who owns the receiving accounts is not shown. The sample therefore shows the listed amount leaving the swap in one piece, not who keeps it. Whatever 1Click charges on top, and whether it forwards any of it to NEAR, is not visible.

**SwapKit is the volume concentration risk.** It routes 38.2<!--n:swapkit_vol_share_pct-->% of 1Click volume and paid NEAR $159<!--n:swapkit_buyback_fees_usd--> in explicit fees over 30 days. If it left, NEAR would lose about 2.0<!--n:swapkit_exit_traceable_pct-->% of captured revenue on the streams we can trace to it. The ceiling is far higher, because escrow NEAR cannot be attributed to a channel. It is 43.0<!--n:swapkit_exit_ceiling_pct-->% if all the NEAR unshielded from the escrow to the buyback wallet were SwapKit's, and 73.7<!--n:swapkit_exit_ceiling_all_escrow_pct-->% if the escrow NEAR reaching the front-end fund counted too. These are bounds set by what cannot be attributed, not estimates of SwapKit's share.

**NEAR's explicit fee rate rose from a low base, on falling volume.** NEAR's explicit fee inside 1Click went from 1.83<!--n:take_b1_bb_explicit_bp--> bp of volume (Aug 7 – Sep 5) to 4.08<!--n:take_b3_bb_explicit_bp--> bp (Oct 6 – Nov 4). Most of the rise is more volume carrying a buyback fee entry (23.6<!--n:take_b1_vol_with_bb_pct-->% → 43.0<!--n:take_b3_vol_with_bb_pct-->%).

That shift follows a documented price change. The archived 1Click fee page of 2026-08-11 says an API key pays "Only the 0.0001% protocol fee". The fee-configuration page of 2026-10-05 says "1Click charges 20 bps". The share of 1Click volume listing no fee fell from 25.7% on 09-02 to 1.4% on 09-03. One referral, `trustwallet`, appears on seven days only (10-23 to 10-29) and lists 12.0% of the last block's explicit buyback fees. Without it the rate is 3.68 bp ([second review](docs/second-review.md), section 3).

This is a rate, not an amount. 1Click volume was $1,442<!--n:take_b2_oneclick_usd_m-->M in the middle block and $1,104<!--n:take_b3_oneclick_usd_m-->M in the last. Partner fees were about ten times NEAR's explicit fee in the last block (40.3<!--n:take_b3_partner_bp--> bp against 4.08<!--n:take_b3_bb_explicit_bp--> bp).

The pre-registered F3 tested a different series, the captured take, which is DefiLlama revenue over reported volume. It predicted a fall back below 4.0 bp, because October's high "was a high, not a new level". It missed at 4.22 bp. DefiLlama revenue is NEAR delivered to the wallets and moves with delivery timing. So the miss is consistent with the rise in the explicit fee persisting, but it does not test that rate.

**Volume is not the token.** Intents is 55.7<!--n:intents_share_peerset_30d_pct-->% of its cross-chain peer set by reported volume, but only 3.5<!--n:explorer_near_side_swap_share_pct-->% of 1Click volume has NEAR on one side. 1Click was a net route out of NEAR: $24.0<!--n:explorer_out_of_near_usd_m-->M out against $14.6<!--n:explorer_into_near_usd_m-->M in.

Reported volume also counts swaps more than once. DefiLlama's Intents volume counts both legs of public swaps (measured), plus, from 2026-09-01, confidential-treasury flow at about one leg (measured; what that flow represents is inferred). The inference is now strong. Each solver shield pairs with an unshield of another token of equal value about eight blocks later (measured on three days; [`docs/confidential-flow.md`](docs/confidential-flow.md), exploratory). Solver shields are about 31% of the treasury flow, so about one leg of that flow is close to both legs of the confidential swaps. On the window's measured days, DefiLlama's volume is 1.8<!--n:legcount_k_solver_window_lo-->× to 1.92<!--n:legcount_k_solver_window_hi-->× one-sided volume.

| Volume basis | Intents' share of the peer set |
|---|---|
| Reported volume | 55.7<!--n:intents_share_peerset_30d_pct-->% |
| One-sided, solver reading | 39.7<!--n:legcount_peer_share_solver_lo_pct-->% to 41.2<!--n:legcount_peer_share_solver_hi_pct-->% |
| Reported volume halved | 38.6<!--n:intents_share_peerset_30d_net_pct-->% |
| The two readings of [`docs/leg-count.md`](docs/leg-count.md) | 46.6<!--n:legcount_peer_share_lo_pct-->% to 48.1<!--n:legcount_peer_share_hi_pct-->%, and 23.9<!--n:legcount_peer_share_public_lo_pct-->% to 25.0<!--n:legcount_peer_share_public_hi_pct-->% |

None of these is a like-for-like share, because only Intents is restated. DefiLlama's THORChain and Maya volumes come from Midgard's `totalVolume`, which counts both pool legs of an asset-to-asset swap. F4 and P1 are scored on the reported basis. The four-venue set also leaves out intent bridges such as Relay and Across. Their reported 30-day volumes (DefiLlama bridge series, not committed here) are larger than Intents' ([second review](docs/second-review.md), section 11).

### Usage (Nearblocks, reproduced in BigQuery)

The dashboard card `chart-usage` in `site/index.html` charts the Nearblocks series. The BigQuery queries the brief asks for (exploratory, run on 2026-11-13) are in [`docs/usage.md`](docs/usage.md).

**Active accounts are falling, and the transaction count is not a usable measure.** Daily active accounts averaged 61.6<!--n:active_accounts_30d_k-->K over the 30 days to 2026-11-04. That is -77.1<!--n:active_accounts_30d_yoy_pct-->% on the same 30 days a year earlier and -52.1<!--n:active_accounts_since_step_pct-->% on the first 30 days after 2026-04-02. The daily transaction count is -84.8<!--n:tx_per_day_30d_yoy_pct-->% year on year, at 685<!--n:tx_per_day_30d_k-->K a day. Most of that is one step, between 2026-03-31 and 2026-04-02.

| Daily count | Before the step | After the step |
|---|---|---|
| Transactions | 4,169.8<!--n:l1_step_tx_before_k-->K | 1,063.4<!--n:l1_step_tx_after_k-->K |
| Active contracts | 2,194.2<!--n:l1_step_contracts_before_k-->K | 184.6<!--n:l1_step_contracts_after_k-->K |
| New accounts | 137.1<!--n:l1_step_new_accounts_before_k-->K | 20.7<!--n:l1_step_new_accounts_after_k-->K |
| Active accounts | 139.2<!--n:l1_step_active_accounts_before_k-->K | 137.2<!--n:l1_step_active_accounts_after_k-->K |

Active accounts barely moved at the step. Since the step, transactions are -18.9<!--n:tx_per_day_since_step_pct-->%. Neither series is filtered for sybils, and neither says who holds or sells NEAR.

**What BigQuery adds (exploratory).** On all 395<!--n:usage_bq_nearblocks_match_days_n--> days from 2025-10-06 to 2026-11-04, Nearblocks' transactions equal BigQuery's signed transactions, and its active accounts equal BigQuery's distinct transaction signers. So those definitions are now known.

The step in transactions is one application. Three signers of Sweat Economy's accounts (`hotwallet.kaiching`, `users.kaiching`, `sweat-migration.near`) went from 3,209.4<!--n:usage_bq_step_kaiching_tx_before_k-->K transactions on 03-31 to 144.2<!--n:usage_bq_step_kaiching_tx_after_k-->K on 04-02. That is 98.7<!--n:usage_bq_step_kaiching_share_pct-->% of the step. It is not a change in what Nearblocks counts. Why it stopped is not in the data, and we found no published account.

The fall in active accounts is another application. Signers ending `.tg`, which are HOT Wallet's Telegram accounts, went from 249.9<!--n:usage_bq_tg_signers_yago_30d_k-->K to 45.6<!--n:usage_bq_tg_signers_30d_k-->K a day. That is 98.5<!--n:usage_bq_tg_share_of_signer_drop_pct-->% of the fall. All other signers went from 19.1<!--n:usage_bq_non_tg_signers_yago_30d_k-->K to 16.0<!--n:usage_bq_non_tg_signers_30d_k-->K (-16.2<!--n:usage_bq_non_tg_signers_yoy_pct-->%).

Contract usage did not fall. The median number of contracts called a day was 1,449<!--n:usage_bq_contracts_called_median_30d_n--> against 1,461<!--n:usage_bq_contracts_called_median_yago_n--> a year earlier, and contracts called directly by a transaction's signer rose 52.7<!--n:usage_bq_contracts_direct_yoy_pct-->%.

Transactions are concentrated. `sweat-relayer.near` signed 26.6<!--n:usage_bq_top1_signer_tx_share_30d_pct-->% of them in the window, and the ten largest signers 61.0<!--n:usage_bq_top10_signer_tx_share_30d_pct-->%. Sweat has announced that its wallet and token "as they exist today" end on 2026-12-30. The transaction count may therefore step down again, for a reason that says nothing about other usage.

None of this measures NEAR Intents, and none of it is evidence for or against value capture. It says the headline usage decline is mostly two consumer applications.

### Valuation context (descriptive, not a valuation)

NEAR's market cap is 199<!--n:mcap_to_rev_30d_annualized_x-->× its last 30 days of captured Intents revenue annualised, and 510<!--n:mcap_to_rev_365d_x-->× on the last 365 days, at the CoinGecko snapshot of $4.82<!--n:mcap_usd_b-->B.

## 4. The supply side (pre-registered tests, with labelled extras)

Details: [`docs/supply-side.md`](docs/supply-side.md).

**H1a fails (pre-registered).** Over the 90 days, net staking outflow was 6.56<!--n:h1a_ratio_as_written_x-->× staking rewards. Net staking outflow is withdrawals minus deposits, across all pools. It is a net of large principal flows, 188.0<!--n:sr_staking_inflow_90d_m-->M NEAR in and 235.3<!--n:sr_staking_outflow_90d_m-->M out. So it measures churn, and it does not show whether rewards themselves stay staked. The fail survives dropping the 5 or the 10 largest days on each side (4.67<!--n:sr_h1a_ratio_trim5_x-->× and 2.79<!--n:sr_h1a_ratio_trim10_x-->×; [second review](docs/second-review.md), section 9). With `lst-pool.near` added the ratio is 5.96<!--n:h1a_ratio_with_lst_pool_x-->×. That addition is post hoc, and the test is not redefined. The net figure includes exchange-owned stake moving, which is not a sale.

**Where the outflow came from (exploratory; not a pre-registered test, and not reproduced from raw chain data here).** The committed file `data/raw/unstakers/account_set.json` lists 14<!--n:unstakers_a14_n--> accounts that reach one unlabelled hub within two hops. Their net unstaking over the same 90 days sums to 42.87<!--n:unstakers_a14_net_outflow_m-->M NEAR. By our arithmetic on that file, that is 90.7<!--n:unstakers_a14_share_of_net_outflow_pct-->% of the pools' 47.3<!--n:pool_net_outflow_90d_m-->M NEAR net outflow. The comparison sets a subset's net against the all-account net. Other large net withdrawers appear in the same file, so the 90.7<!--n:unstakers_a14_share_of_net_outflow_pct-->% is not a share of a partition of the outflow. The extraction that produced the file is not in this repository, and the repository does not record when that earlier analysis was done. By any route we could see, those accounts moved no NEAR into Intents. We traced two hops, and meta-transactions are missed.

**H1b and H1c are inconclusive (pre-registered)** for lack of exchange labels. The buyback wallet's growth, 1.48<!--n:h1c_identified_buying_m-->M NEAR, is 33.48<!--n:h1c_ratio_lower_pct-->% of the lower bound of exchange inflow and 0.97<!--n:h1c_ratio_upper_pct-->% of the upper. The lower bound itself is unstable. It is the net of 267.2<!--n:sr_h1b_lower_in_m-->M NEAR in and 262.8<!--n:sr_h1b_lower_out_m-->M out, and dropping one day moves it across gross issuance in either direction. It is 17.6<!--n:sr_h1b_lower_without_1029_m-->M without 2026-10-29, 8.76<!--n:sr_h1b_lower_without_1002_m-->M without 2026-10-02 and -1.35<!--n:sr_h1b_lower_without_0918_m-->M without 2026-09-18 ([second review](docs/second-review.md), section 8).

**Rating: Hold (the frozen rule's output).** Required captured-revenue growth, G_req, is 33.2<!--n:rating_g_req_pct-->% a year, or 46.8<!--n:rating_g_req_no_hsp029_pct-->% without HSP-029. Observed growth, G_obs, is 619.0<!--n:rating_g_obs_pct-->% a year in USD and 71.4<!--n:rating_g_obs_near_pct-->% in NEAR terms. On both measures it is far above the Avoid line, 16.6<!--n:rating_g_avoid_line_pct-->% a year.

Two things about these inputs should be known. G_req's constants (the price level, the HSP-029 ramp and its activation date) were committed after the freeze, in the same commit as the as-written H1a result. They are in `data/raw/rpc/rating_assumptions.json`. And G_obs compares the last 180 days with the 180 before, a base window that straddles the 2026-02-23 fee switch. Neither changes the output, which H1b decides. G_req's burn term also uses supply readings dated 2026-11-05 and 2026-11-06 (`PREREG-ADDENDUM.md`, 2026-11-12 23:50 UTC entry, item 1).

G_obs measures a step in the share of fees captured rather than growth in activity. Over the same windows gross fees rose 3.4<!--n:sr_fees_180d_change_pct-->% and volume 29.6<!--n:sr_volume_180d_change_pct-->%, and 182-day windows give 426% ([second review](docs/second-review.md), section 6). The ladder does not feed the rule.

## 5. What would change our mind

Each row names something that would move us, what it would take, and where it would show. Four rows need more room than a table cell, and their notes follow the table.

| What would move us | What it would take | Where we would see it |
|---|---|---|
| The rating to **Buy** (frozen rule) | H1b passes and G_obs stays at or above G_req (33.2<!--n:rating_g_req_pct-->% a year). H1b passes only if net exchange inflow is below gross issuance (8.0098<!--n:h1a_gross_issuance_90d_m-->M NEAR) under both bounds, or, at 50% coverage or more, under the lower one. Today the bounds are 4.42<!--n:h1b_net_inflow_lower_m-->M and 152.45<!--n:h1b_net_inflow_upper_m-->M NEAR. So it needs sourced exchange labels for many more of the top-100 receivers. | `data/raw/labels/exchange_accounts.json`, then `make reproduce` |
| The rating to **Avoid** (frozen rule) | H1b fails, which needs label coverage of 50% or more, and G_obs falls below 16.6<!--n:rating_g_avoid_line_pct-->% a year. It is 619.0<!--n:rating_g_obs_pct-->% today, or 71.4<!--n:rating_g_obs_near_pct-->% in NEAR terms. | The same list, and DefiLlama's revenue series |
| Value capture toward the **top** of the range | NEAR attests which fees fund the escrow releases, and they are recurring fee revenue. The public side already points that way: the releases track confidential swap volume day by day (section 2). | NEAR's own disclosure; compare with `data/raw/escrow/deliveries.csv` and `data/raw/bq/confidential_treasury_daily.json` |
| Value capture toward the **bottom** of the range | The escrow releases turn out to be one-off or discretionary rather than fees. We would see it in how they arrive (note 1). | A re-run of `sql/escrow_funding_scan.sql` for a later window (it needs gcloud and its dates changed); `python3 -m pipeline.fetch_escrow verify` only re-checks rows already in `data/raw/escrow/deliveries.csv` |
| More concentration risk | SwapKit or another large channel stops routing through 1Click. That is about 2.0<!--n:swapkit_exit_traceable_pct-->% of captured revenue on the traceable streams, and up to 43.0<!--n:swapkit_exit_ceiling_pct-->%. | The Explorer API (key-gated) |
| A stronger usage case | Daily active accounts stop falling: the 30-day average recovers to its level in the first 30 days after the 2026-04-02 step. The latest 30 days are -52.1<!--n:active_accounts_since_step_pct-->% against it. Signers outside HOT's `.tg` accounts are the cleaner series, and they would need to stop falling (-16.2<!--n:usage_bq_non_tg_signers_yoy_pct-->% a year to 2026-11-04). | Nearblocks charts, re-fetched with `make fetch`; `sql/usage_daily.sql` and `sql/usage_signer_groups.sql` with later dates |
| The investment case toward the **upside** (exploratory) | NEAR's captured take rising toward what the price would need (37.4<!--n:ic_take_needed_bp--> bp at the market's last-year pace and Intents' twelve-month-high share), the market growing faster than G_req for several years, or coverage running above the Monte Carlo's middle half (36.6<!--n:fwd_cov_2027_p75_pct-->% by 2027-11). | DefiLlama revenue, fees and volume, re-fetched; `make reproduce` |
| The investment case toward the **downside** (exploratory) | The take falling back toward its lowest month since the fee switch (1.36<!--n:ic_take_min_bp--> bp), Intents' share falling toward its twelve-month low (48.5<!--n:ic_share_min_pct-->%), or NEAR's price rising without revenue, so that each dollar buys back less NEAR. | The same, and CoinGecko |
| The forward tests **F1-F4** (pre-registered) | Scored on 2026-11-14: two passed and two missed (note 2). | `data/forward/score_*/result.json` |
| The longer-dated predictions **P1-P3** (pre-registered) | They resolve on 2027-05-04 and 2027-11-04 and cannot be scored yet (note 3). | DefiLlama's volume and revenue series, NEAR's supply and price: the inputs `make fetch` refreshes, read again after each date |
| A pending resolver | HSP-029's issuance cut (note 4). | The governance record |

**Note 1: how we would recognise one-off escrow releases.** The escrow's share of the buyback wallet's arrivals cannot show it. That share was 28.6<!--n:escrow_share_buyback_2026_08_pct-->%, 53.0<!--n:escrow_share_buyback_2026_09_pct-->% and 57.4<!--n:escrow_share_buyback_2026_10_pct-->% in Aug, Sep and Oct. It stepped up once at the end of August and has been flat since (section 1). The test this row gave until 2026-11-12 ("stops rising and total arrivals fall in the next 30-day block") is therefore already met, for a reason unrelated to the question.

What would show it is a change in how the releases arrive. From 2026-08-29 to 11-04 they came on every one of the 68 days, at least 10 deliveries a day, in lots the same size as the public collectors' fee sweeps (a floor near $1,000). Three changes would move us toward the bottom. The releases could stop arriving daily. They could come mostly in hand-set batches, like those of 2026-10-04 (seven deliveries of 2,021 to 4,183 NEAR to the front-end fund) and 2026-10-15 (three deliveries, 21,229 NEAR). Or they could stop tracking confidential volume. The exploratory forward tests E1-E5 score these patterns over 2026-11-15 to 12-14 (`PREREG-ADDENDUM.md`, 2026-11-13 06:23 UTC entry).

**Note 2: the forward tests.** `pipeline/score_forward.py` scored them on 2026-11-14. F1 and F2 passed. F3 (4.22 bp, above the 4.0 bp line) and F4 (37.2% of the peer set) missed. F3's miss is consistent with the rise in the explicit fee in section 3 persisting, though F3 does not test that rate directly.

One disclosure belongs with the score. The first dry run of the scorer read no scoring-window day for F2 to F4 and only the window-opening block for F1 (item 7 of the 2026-11-06 23:49 UTC entry of `PREREG-ADDENDUM.md`). Later dry runs, and direct reads of the buyback wallet's balance, did touch window days. They are disclosed in its 2026-11-08 05:04 UTC entry.

**Note 3: P1-P3.** `PREREG.md` pre-registers three predictions that resolve later: P1 (2027-05-04), "Intents' 365-day share of the peer set ≥ 55%"; P2 (2027-05-04), "90-day captured Intents revenue ≥ $6.0M. It was $4.84<!--n:rating_r90_usd_m-->M for the 90 days to 2026-11-04"; P3 (2027-11-04), "90-day captured revenue ÷ USD value of net new supply ≥ 25%". None can be scored yet, and nothing in this note is a score. As descriptive context only: the 365-day share of the peer set by reported volume is 62.1<!--n:intents_share_peerset_365d_pct-->% in the committed data (as of 2026-11-04), against P1's 55% bar. On the same descriptive basis P3's quantity for the 90 days to 2026-11-04 is 17.8<!--n:p3_quantity_90d_asof_pct-->%, against P3's 25% bar. That quantity is DefiLlama revenue over the USD value of net new supply, priced daily.

**Note 4: HSP-029.** Its on-chain timelock ends on 2026-11-16, after the deadline (House of Stake API; it matches our sum of the contract's voting start, the voting period and the timelock period). A Directors' decision on execution follows the timelock (House of Stake procedures, §7.5.1), before any protocol release. The proposal text also says the cap is a protocol parameter, so the cut needs validator adoption through a protocol upgrade. That is a further step we do not date. The text does not define "ratification", and we read it as the end of the timelock. G_req assumes the ramp is in force. Without it G_req is 46.8<!--n:rating_g_req_no_hsp029_pct-->% a year, and the rating does not change (`PREREG-ADDENDUM.md`, 2026-11-12 23:50 UTC entry, item 3).

## 6. The investment case: what the price assumes, what the evidence supports (exploratory)

*Built after the freeze: the Monte Carlo (6.7) on 2026-11-13, the rest on 2026-11-14. None of it changes a hypothesis, threshold, probability or the rating, or feeds anything they compute. Code: [`pipeline/investment_case.py`](pipeline/investment_case.py) and [`pipeline/model.py`](pipeline/model.py). Method and recipes: [`docs/investment-case.md`](docs/investment-case.md). Dashboard: the "Investment case" section of `site/index.html`.*

A long-term thesis has to say four things: what the price already assumes, what the evidence supports, how far apart the two are, and what would close the gap. This section takes them in that order. Every figure is recomputed by `make reproduce` from committed data. The section needs two assumptions, a required return and a revenue multiple. We show both as a grid and do not choose for the reader.

### 6.1 What the price assumes

Suppose Intents' captured revenue carried NEAR's price alone. For the price to rise 15<!--n:ic_base_r_pct-->% a year to 2031-11-04, and for the market cap ($4.82<!--n:mcap_usd_b-->B today) to end at 25<!--n:ic_base_x-->× captured revenue, that revenue must grow from $19.6<!--n:ic_rev_90d_ann_m-->M a year to $424<!--n:ic_required_rev_2031_m-->M. The starting figure is the last 90 days at an annual rate. The target is 21.6<!--n:ic_required_multiple_x-->× today, which is **84.9<!--n:ic_implied_cagr_r15_x25_pct-->% a year**.

The arithmetic accounts for dilution. The required return is on the price. Supply grows by 1.094<!--n:ic_supply_factor_x-->× by 2031 on the rating rule's own path with HSP-029, and buybacks burn nothing. So the market cap has to grow faster than the price. A holder who stakes also receives part of the new supply.

| Required return | 10<!--n:ic_grid_x0-->× revenue in 2031 | 25<!--n:ic_grid_x1-->× | 50<!--n:ic_grid_x2-->× |
|---|---|---|---|
| 10<!--n:ic_grid_r0_pct-->% a year | 112.4<!--n:ic_implied_cagr_r10_x10_pct-->% | 76.9<!--n:ic_implied_cagr_r10_x25_pct-->% | 54.0<!--n:ic_implied_cagr_r10_x50_pct-->% |
| 15<!--n:ic_grid_r1_pct-->% a year | 122.1<!--n:ic_implied_cagr_r15_x10_pct-->% | 84.9<!--n:ic_implied_cagr_r15_x25_pct-->% | 61.0<!--n:ic_implied_cagr_r15_x50_pct-->% |
| 20<!--n:ic_grid_r2_pct-->% a year | 131.7<!--n:ic_implied_cagr_r20_x10_pct-->% | 92.9<!--n:ic_implied_cagr_r20_x25_pct-->% | 68.0<!--n:ic_implied_cagr_r20_x50_pct-->% |

**What the market did.** The same venues (THORChain, Chainflip, Maya and NEAR Intents) reported these volumes to DefiLlama over the five full years to 2026-11-04, oldest first: $11.3<!--n:ic_market_y4_b-->B, $9.6<!--n:ic_market_y3_b-->B, $55.1<!--n:ic_market_y2_b-->B, $46.7<!--n:ic_market_y1_b-->B and $53.0<!--n:ic_market_y0_b-->B. That is growth of 13.4<!--n:ic_market_cagr_1y_pct-->% last year, -1.9<!--n:ic_market_cagr_2y_pct-->% a year over two years, 76.9<!--n:ic_market_cagr_3y_pct-->% a year over three (measured from the low) and 47.1<!--n:ic_market_cagr_4y_pct-->% a year over four.

Last year's growth is all Intents' own: its volume grew 9.0<!--n:ic_intents_vol_1y_x-->×. Without Intents, the venues' volume changed by -53.4<!--n:ic_market_ex_intents_cagr_1y_pct-->% last year, -39.6<!--n:ic_market_ex_intents_cagr_2y_pct-->% a year over two years and 15.4<!--n:ic_market_ex_intents_cagr_4y_pct-->% a year over four. Part of last year's rise is also DefiLlama's 2026-09-01 change in what it counts as Intents volume ([`docs/leg-count.md`](docs/leg-count.md)). As a measure of the market's growth it is therefore generous to NEAR.

The 84.9<!--n:ic_implied_cagr_r15_x25_pct-->% the price would assume is above every one of these windows. For comparison, the rating rule's G_req is 33.2<!--n:rating_g_req_pct-->%. That is the growth at which captured revenue would pay for dilution by 2031. We leave G_obs (619.0<!--n:rating_g_obs_pct-->%) out of the comparison, because it is a step in the share of fees captured and not growth in activity.

**One caveat governs this whole section.** NEAR's market cap also prices the L1: its fees, which burn, its staking, and any monetary premium. Setting all of it against Intents' captured revenue shows what Intents would need **if it carried the price alone**. What the L1 itself is worth is not computed here.

### 6.2 What would have to multiply

Captured revenue = cross-chain swap volume × Intents' share × NEAR's take rate. It has to multiply by 21.6<!--n:ic_required_multiple_x--> by 2031.

| Factor | If it does this | It multiplies revenue by |
|---|---|---|
| The market | Grows at its last-year pace for five years | ×1.87<!--n:ic_mult_market_x--> |
| Intents' share | Reaches its twelve-month high, 78.6<!--n:ic_share_max_pct-->%, against 61.7<!--n:ic_share_90d_pct-->% over the last 90 days | ×1.27<!--n:ic_mult_share_x--> |
| NEAR's take rate | Has to supply what is left | ×9.1<!--n:ic_mult_take_x--> |

So the take rate would have to go from 4.13<!--n:ic_take_90d_bp--> bp of volume to **37.4<!--n:ic_take_needed_bp--> bp, 2.5<!--n:ic_take_needed_vs_gross_x-->× the whole 15.2<!--n:ic_gross_bp_90d--> bp gross fee Intents charges today**.

Even if NEAR kept the whole gross fee, and Intents held its twelve-month-high share, the market would have to grow 35.7<!--n:ic_market_cagr_needed_full_fee_pct-->% a year for five years. Fees are a policy choice, so this does not prove the take cannot rise. It shows how far the current fee structure is from what the price would imply.

Each factor is measured on DefiLlama's reported volume. That volume counts both legs of some swaps and, from 2026-09-01, more of Intents' volume ([`docs/leg-count.md`](docs/leg-count.md)). Only the full product, the revenue, is unaffected. Last year's market growth is all Intents' and partly that counting change, so the market factor is generous and the take needed is, if anything, understated.

### 6.3 Scenarios from the data

Each input takes a value from the data.

| Input | Bear | Base | Bull |
|---|---|---|---|
| Market pace | Two-year | Last year | Four-year |
| Intents' share | Twelve-month low, 48.5<!--n:ic_share_min_pct-->% (2026-04) | Last 90 days | Twelve-month high (2026-06) |
| NEAR's take | Lowest full month since the fee switch, 1.36<!--n:ic_take_min_bp--> bp (2026-04) | Last 90 days | Highest month, 5.49<!--n:ic_take_max_bp--> bp (2026-10) |
| HSP-029 | Not in force | In force | In force |

Coverage is captured revenue ÷ the USD value of net new supply, which is P3's quantity. It is taken at the rule's constant price, $3.67<!--n:price_usd-->. That is a flat price, where 6.1 lets the price compound, because the two answer different questions. Coverage is what captured revenue would pay for. Not all of it is bought-back NEAR, and none of it is burned.

| On 2031-11-04 | Bear | Base | Bull |
|---|---|---|---|
| Market growth a year | -1.9<!--n:ic_bear_market_cagr_pct-->% | 13.4<!--n:ic_base_market_cagr_pct-->% | 47.1<!--n:ic_bull_market_cagr_pct-->% |
| Captured revenue, a year | $4.6<!--n:ic_bear_rev_2031_m-->M | $36.7<!--n:ic_base_rev_2031_m-->M | $228.6<!--n:ic_bull_rev_2031_m-->M |
| Coverage of dilution | 3.5<!--n:ic_bear_coverage_2031_pct-->% | 44.6<!--n:ic_base_coverage_2031_pct-->% | 277.5<!--n:ic_bull_coverage_2031_pct-->% |
| Share of the revenue the price assumes | 1.1<!--n:ic_bear_vs_required_pct-->% | 8.7<!--n:ic_base_vs_required_pct-->% | 53.9<!--n:ic_bull_vs_required_pct-->% |
| Today's market cap ÷ 2031 revenue | 1041.1<!--n:ic_bear_mcap_to_rev_2031_x-->× | 131.1<!--n:ic_base_mcap_to_rev_2031_x-->× | 21.1<!--n:ic_bull_mcap_to_rev_2031_x-->× |

The bull case would pay for NEAR's dilution almost three times over. It still reaches only about half the revenue the price would assume at 15<!--n:ic_base_r_pct-->% and 25<!--n:ic_base_x-->×. At the three-year market pace, from the 2023 low, it would reach 136<!--n:ic_bull3y_vs_required_pct-->%. The bull case's revenue grows 63.4<!--n:ic_bull_rev_cagr_pct-->% a year, which exceeds what the price would assume at 50× (54.0<!--n:ic_implied_cagr_r10_x50_pct-->% at a 10% return, 61.0<!--n:ic_implied_cagr_r15_x50_pct-->% at 15%). The bull case is generous in one respect. It grows the whole peer set at its four-year pace and also lifts Intents' share, so it counts some of Intents' share gains twice.

We chose which window anchors each case after the annual volumes, the monthly shares and the monthly take rates had been computed (`PREREG-ADDENDUM.md`, 2026-11-14 entries). Section 6.1 lists every window, so a reader can substitute another.

### 6.4 What moves it most

The base coverage is 44.6<!--n:ic_base_coverage_2031_pct-->%. This table moves one input at a time to its bear and bull value.

| Input moved | Lowest coverage | Highest coverage |
|---|---|---|
| Market growth | 21.6<!--n:ic_tor_market_lo_pct-->% | 163.8<!--n:ic_tor_market_hi_pct-->% |
| NEAR's price, over its 365-day range ($0.96<!--n:ic_price_365d_low_usd--> to $5.89<!--n:ic_price_365d_high_usd-->) | 27.8<!--n:ic_tor_price_lo_pct-->% | 169.8<!--n:ic_tor_price_hi_pct-->% |
| Take rate | 14.7<!--n:ic_tor_take_lo_pct-->% | 59.3<!--n:ic_tor_take_hi_pct-->% |
| Intents' share | 35.1<!--n:ic_tor_share_lo_pct-->% | 56.8<!--n:ic_tor_share_hi_pct-->% |
| HSP-029 | 27.5<!--n:ic_tor_hsp029_lo_pct-->% (not in force) | 44.6<!--n:ic_tor_hsp029_hi_pct-->% |

Market growth and the price move it most. A higher price lowers coverage, because each dollar of revenue buys back less NEAR.

### 6.5 Peer valuation

All three market caps are taken at the same hour (2026-11-05, CoinGecko). Fees are the gross fees charged over 365 days.

| Token | Market cap | Gross fees | Market cap ÷ fees |
|---|---|---|---|
| NEAR, against NEAR Intents' fees | $4.82<!--n:mcap_usd_b-->B | $54.01<!--n:ic_near_intents_fees_365d_m-->M | 89.2<!--n:ic_near_mcap_to_intents_fees_x-->× |
| THORChain (RUNE) | $198.0<!--n:ic_peer_thorchain_mcap_m-->M | $20.21<!--n:ic_peer_thorchain_fees_365d_m-->M | 9.8<!--n:ic_peer_thorchain_mcap_to_fees_x-->× |
| Chainflip (FLIP) | $28.3<!--n:ic_peer_chainflip_mcap_m-->M | $15.39<!--n:ic_peer_chainflip_fees_365d_m-->M | 1.8<!--n:ic_peer_chainflip_mcap_to_fees_x-->× |

NEAR's market cap was also 245<!--n:ic_near_mcap_to_rev_90d_ann_x-->× its captured revenue at the last 90 days' rate. None of this is like for like. NEAR's market cap prices the whole L1, and the peers' fees do not all accrue to their tokens. The grid in 6.1 uses multiples of captured revenue. The peers' multiples on what reaches their token holders would be higher than the ones above, and we have not computed them. Maya Protocol is left out because its token (CACAO) is not listed on CoinGecko. The peer market caps come from a fetch made on 2026-11-14 (`python3 -m pipeline.fetch_peer_caps`), and only the hourly point nearest NEAR's committed snapshot is used.

### 6.6 Supply and the staking float

On the rule's own path, supply grows 9.4<!--n:fwd_supply_growth_5y_pct-->% to 2031-11-04 with HSP-029 and 13.1<!--n:fwd_supply_growth_5y_no_hsp029_pct-->% without. Over H1a's 90-day window the NEAR in staking pools fell from 633.1<!--n:ic_staked_start_m-->M to 592.8<!--n:ic_staked_end_m-->M, or from 48.6<!--n:ic_staked_share_start_pct-->% to 45.2<!--n:ic_staked_share_end_pct-->% of supply. The NEAR outside the pools grew by 48.2<!--n:ic_float_change_90d_m-->M, which is 6.1<!--n:ic_float_change_vs_net_supply_x-->× the net supply increase. Not all of that NEAR is liquid. Whether it was sold is H1b's question, and H1b is inconclusive.

### 6.7 Uncertainty: the Monte Carlo

*Built on 2026-11-13. Its forecasts M1-M4 are exploratory and dated after the freeze; they are in `PREREG-ADDENDUM.md` (2026-11-13 23:50 UTC entry). The main run is unchanged since. The block-bootstrap check and the run without the 2026-09 month were added on 2026-11-14.*

**The question** is the frozen rating rule's own: does captured Intents revenue reach the USD value of net new supply by 2031-11-04? The rule answers with one constant price and one growth rate (G_req, 33.2<!--n:rating_g_req_pct-->% a year). The model answers with a distribution.

**Coverage** is captured revenue over a trailing 90 days ÷ the USD value of the net new NEAR minted in the same 90 days. This is P3's quantity. Today it is 16.6<!--n:fwd_coverage_now_pct-->% at one price, or 17.8<!--n:p3_quantity_90d_asof_pct-->% priced daily, as P3 measures it. It has risen from 11.8<!--n:ic_cov_hist_first_pct-->% on 2026-02-04, the first date with 90 days of prices. The dashboard draws that history before the projection.

**How it is built.**

- *Supply.* The same daily path as G_req (realised share of the inflation cap, post-v87 burn), with HSP-029's ramp and without it.
- *Volume and price.* 10000<!--n:fwd_paths_n--> paths of 60<!--n:fwd_months_n--> months. Each month draws one of the 11<!--n:fwd_boot_months_n--> monthly changes in Intents volume (DefiLlama) and NEAR's mean price (CoinGecko) from 2025-12 to 2026-10. The two are drawn as a pair because they move together (correlation 0.54<!--n:fwd_vol_price_corr-->).
- *Price drift removed.* NEAR's mean price rose 7.4<!--n:fwd_price_monthly_mean_pct-->% a month on average over those months. Replaying that for five years would assume the trend continues. So the main run keeps the price's volatility and its co-movement with volume, and drops its drift. We made this choice after seeing a first run with the drift, and the addendum entry discloses it. The run with the drift is shown as a sensitivity.
- *Take rate.* Captured revenue ÷ volume over the last 90 days, 4.13<!--n:fwd_take_bp-->bp, held fixed. Volume keeps its sample drift of 0.8<!--n:fwd_vol_monthly_mean_pct-->% a month, all of which comes from one month (below).
- *Reproducible.* Standard library only, with a fixed seed. `make reproduce` gives the same numbers on every run.

**Results.**

| Coverage | 2027-11 | 2028-11 | 2031-11-04 |
|---|---|---|---|
| Median path | 19.9<!--n:fwd_cov_2027_p50_pct-->% | 26.6<!--n:fwd_cov_2028_p50_pct-->% | 38.2<!--n:fwd_cov_2031_p50_pct-->% |
| Middle half of paths | 10.7<!--n:fwd_cov_2027_p25_pct-->% to 36.6<!--n:fwd_cov_2027_p75_pct-->% | 10.8<!--n:fwd_cov_2028_p25_pct-->% to 65.4<!--n:fwd_cov_2028_p75_pct-->% | 8.9<!--n:fwd_cov_2031_p25_pct-->% to 156.2<!--n:fwd_cov_2031_p75_pct-->% |
| Paths that cover all dilution | 3.9<!--n:fwd_p_cov_ge100_2027_pct-->% | 15.9<!--n:fwd_p_cov_ge100_2028_pct-->% | 31.8<!--n:fwd_p_cov_ge100_2031_pct-->% |
| Paths at 25% or more (P3's line) | 39.6<!--n:fwd_p_cov_ge25_2027_pct-->% | 52.0<!--n:fwd_p_cov_ge25_2028_pct-->% | 57.8<!--n:fwd_p_cov_ge25_2031_pct-->% |

**Sensitivity.** The share of paths that cover all dilution by 2031-11-04 depends on the run.

| Run | Paths that cover all dilution by 2031-11-04 |
|---|---|
| Main run | 31.8<!--n:fwd_p_cov_ge100_2031_pct-->% |
| Without HSP-029 | 24.5<!--n:fwd_p_cov_ge100_2031_no_hsp029_pct-->% |
| At half today's take rate | 21.7<!--n:fwd_p_cov_ge100_2031_take_x0_5_pct-->% |
| At twice today's take rate | 44.3<!--n:fwd_p_cov_ge100_2031_take_x2_0_pct-->% |
| With the price's historical drift | 0.9<!--n:fwd_p_cov_ge100_2031_price_drift_pct-->% (median coverage 0.6<!--n:fwd_cov_2031_p50_price_drift_pct-->%) |
| Block bootstrap, added on 2026-11-14 | 25.6<!--n:fwd_block_p_cov_ge100_2031_pct-->% (median coverage 37.8<!--n:fwd_block_cov_2031_p50_pct-->%) |

The block bootstrap is a robustness check. It keeps runs of consecutive months together, with a mean block of 3<!--n:fwd_block_mean_months--> months.

**The volume drift comes from one month.** The change from 2026-08 to 2026-09 spans DefiLlama's 2026-09-01 change in what it counts as Intents volume. Without that month, volume changed by -4.5<!--n:fwd_exsep_vol_monthly_mean_pct-->% a month. The 2031 median falls to 1.5<!--n:fwd_exsep_cov_2031_p50_pct-->%, 3.3<!--n:fwd_exsep_p_cov_ge100_2031_pct-->% of paths cover all dilution by 2031, and 19.4<!--n:fwd_exsep_p_cov_ge25_2027_pct-->% reach 25% by 2027-11, against M1's 39.6<!--n:fwd_p_cov_ge25_2027_pct-->%. M1-M4 were dated with the month in and will be scored as dated. This is why the thesis does not rest on them.

**What it says, and does not.** The median path rises because volume keeps the drift of that one month and HSP-029 cuts dilution. It does not rise because the take rate rises. The bands are wide because 11<!--n:fwd_boot_months_n--> months cannot pin a five-year trend. The model shows that uncertainty and does not resolve it, which is why the headline of this thesis rests on 6.1 to 6.3 and not on these probabilities. P3 was frozen with probability 0.35 before any of this. The model, built after the freeze, gives 39.6<!--n:fwd_p_cov_ge25_2027_pct-->% for the same line. P3 is scored on the data, not on the model.

### 6.8 Signposts

These are the values to watch, each against the line that would favour the upside.

| Signpost | Today | The line | Today as a share of the line |
|---|---|---|---|
| Intents' share of the peer set over 365 days | 62.1<!--n:intents_share_peerset_365d_pct-->% | P1's 55% | 113<!--n:ic_sp_share_pct-->% |
| Captured revenue over 90 days | $4.84<!--n:rating_r90_usd_m-->M | P2's $6M | 81<!--n:ic_sp_revenue_pct-->% |
| Coverage | 17.8<!--n:p3_quantity_90d_asof_pct-->% | The 25% of P3 and of M1 (M1 is exploratory, dated after the freeze) | 71<!--n:ic_sp_coverage_pct-->% |
| Market growth | 13.4<!--n:ic_market_cagr_1y_pct-->% | G_req | 40<!--n:ic_sp_market_pct-->% |
| NEAR's take | 4.13<!--n:ic_take_90d_bp--> bp | 37.4<!--n:ic_take_needed_bp--> bp, what the price would need at the market's last-year pace and Intents' twelve-month-high share | 11<!--n:ic_sp_take_pct-->% |
| Net staking outflow against staking rewards | 6.56<!--n:h1a_ratio_as_written_x-->× | H1a's pass line of 0.5× | 8<!--n:ic_sp_staking_pct-->% |

Two events would move the case directly. One is HSP-029 coming into force; its timelock ends on 2026-11-16. The other is a per-stream attestation by NEAR of the escrow releases.

P1 and P2 (pre-registered) resolve on 2027-05-04. P3 (pre-registered) and M1 (exploratory) resolve on 2027-11-04, M3 on 2028-11-03 and M4 on 2031-11-04. All are scored as written, with misses published.

### 6.9 The view, and what would change it

**The view.** Intents had the largest share of its peer set over the 30 days to 2026-11-04: 55.7<!--n:intents_share_peerset_30d_pct-->% of reported volume, or 39.7<!--n:legcount_peer_share_solver_lo_pct-->% to 41.2<!--n:legcount_peer_share_solver_hi_pct-->% on a one-sided basis. Its captured take has risen. In the scoring week that followed, THORChain's volume was larger, and F4 missed at 37.2% (section 5).

As a claim on Intents' fees, though, NEAR is priced for more growth than the data show at today's fees. Only the most favourable combinations reach what the price would assume: the three-year market pace from the 2023 low, or a 50× multiple. The bull case on the four-year pace reaches about half of it. In the base case captured revenue would pay for under half of NEAR's dilution in 2031.

Holding NEAR at today's price is therefore a bet on more than Intents' fee capture. It is a bet on the L1's own value, on a cross-chain market far larger than its history, or on a take rate well above today's gross fee.

**What would change it.** The two investment-case rows of [section 5](#5-what-would-change-our-mind) say what would move this view up or down, and the signposts in 6.8 are the values to watch.

## Limits

**The investment case (exploratory, 2026-11-13 and 2026-11-14).** The required return and the 2031 revenue multiple are assumptions, shown as a grid. NEAR's market cap also prices the L1, which is not valued here. So the growth the price assumes is what Intents would need if it carried the price alone. The scenario anchors were chosen after the annual volumes, monthly shares and monthly take rates were computed. The market history is one peer set whose members changed (THORChain alone before 2024). Last year's growth of the set is all Intents', and partly DefiLlama's 2026-09-01 counting change. We did not compare NEAR with other fee-switch or buyback tokens, because that would need hand-picked external data. See section 6.

**The Monte Carlo.** It draws from eleven monthly pairs. It models no regime, no trend in the take rate and no mean reversion. Its price drift is removed by a choice made after a first run. Its volume drift comes from the one month that spans the counting change. Its coverage uses one price for the 90 days, where P3 prices each day.

**Second review (exploratory, 2026-11-12).** A later review re-ran parts of this analysis from the committed data. It found four things. The escrow share rose in a step at the end of August rather than as a trend. The rise in the explicit fee follows a documented 1Click price change on 2026-09-03. The front-end fund holds its 4.81<!--n:ladder_frontend_only_pct_of_issuance--> points of the ladder under its own five signers and has never forwarded NEAR to the buyback wallet. And H1b's lower bound turns on single days. The review changes no pre-registered result. Details, with a recipe for each figure: [`docs/second-review.md`](docs/second-review.md).

**The public trail is shrinking.** NEAR Intents' changelog says that 1Click swaps settle confidentially from 2026-10-27. Collector B's daily transfers fell from 4,387<!--n:sr_collector_b_transfers_per_day_1006_1028--> on average over 10-06 to 10-28 to 109<!--n:sr_collector_b_transfers_1104--> on 11-04, and collector A's from 7,682<!--n:sr_collector_a_transfers_per_day_1006_1028--> to 2,739<!--n:sr_collector_a_transfers_1104-->. The 4.53<!--n:ladder_public_collectors_pct_of_issuance--> points traced to public collectors describe a settlement regime that is ending. The per-swap method of [`docs/intents-fee-flows.md`](docs/intents-fee-flows.md) will not be repeatable on confidential swaps ([second review](docs/second-review.md), section 4). The fees themselves show it. By 11-04, 96.0<!--n:collector_a_escrow_usd_share_last_day_pct-->% of collector A's fee value came from escrow-funded accounts (section 1). If that share holds, a later 30-day window would show the collector rung mostly as escrow-funded rather than public. That is a forecast, not a measurement.

**Not settled here.** Four questions cannot be answered from the committed data.

- Who sold the NEAR that the front-end fund bought with USDC.
- Whether NEAR treats the front-end fund as buyback money. The fund is a Sputnik DAO with five signers ([second review](docs/second-review.md), section 1). NEAR's revenue dashboard lists it among the three revenue wallets, and NEAR Intents' fee page names it as the recipient of near-intents.org's fee. No source says what the fund does with its NEAR.
- How much of the confidential flow DefiLlama counts is one user swap routed through two solvers. The chain shows the solver pairs are swaps. That narrows the two readings of [`docs/leg-count.md`](docs/leg-count.md), about 2.8<!--n:legcount_reading_gap_take_x-->× apart on take rates, to k of 1.8<!--n:legcount_k_solver_window_lo--> to 1.92<!--n:legcount_k_solver_window_hi--> ([`docs/confidential-flow.md`](docs/confidential-flow.md)).
- Which fees fund the escrow releases. They track confidential volume, but which fee is not shown.

**Collector roles.** Collector A's role, the explicit buyback fee, is cross-checked: its priced inflows are 96.5<!--n:collector_a_vs_explicit_fees_pct-->% of the fees the Explorer lists. Collector B's role, a share of quote improvement, is inferred from committed, re-checkable per-swap evidence. It is paid a variable cut on 43<!--n:fee_ev_collector_b_swaps_n--> of 195<!--n:fee_ev_swaps_n--> sampled swaps across channels. NEAR Intents' fee page defines a quote improvement fee: when a fill beats the quote, the difference is split "50/50" between the user and "the protocol" (read on 2026-11-13). The page does not name the receiving account, and the quote it would be measured against is not in the Explorer API. So the role is consistent with the docs rather than proven.

**Partner numbers** rest on one key-gated source (the Explorer API), and the per-swap evidence is 195<!--n:fee_ev_swaps_n--> swaps from 3<!--n:fee_ev_hours_with_swaps_n--> sampled hours.

**Escrow funding** before 2026-10-06 is mostly sample-attributed. The identity of the escrow account and both candidate fee streams rest on NEAR's documentation, which this repository does not commit. [`docs/sources-checked.md`](docs/sources-checked.md) quotes what each page said on 2026-11-08 and 2026-11-13 and marks where our wording goes beyond it. Pages can change.

**Earlier work outside this repository** is not reproduced here. Apart from the 14-account reading in section 4, which is labelled exploratory, it is not relied on. This repository cannot show whether that analysis preceded the freeze.

**Rating constants.** G_req rests on assumptions committed after the freeze (section 4).

**Usage data.** The Nearblocks series equal BigQuery's counts of signed transactions and distinct signers. The BigQuery queries the brief asks for were run on 2026-11-13 (exploratory, after the freeze). A signer is an account, not a person. Nothing is filtered for sybils, and a relayed meta-transaction counts for its relayer. The HOT and Sweat groupings are by account-id suffix and signer name. The receipt-level counts (relayed users, contracts called) cover three spans only ([`docs/usage.md`](docs/usage.md)).

**H1a** is net of deposits and includes exchange-owned stake moves.

**H1c's numerator.** PREREG defines identified buying as the buyback wallet's balance growth, 1.48<!--n:h1c_identified_buying_m-->M NEAR over the 90 days, and H1c uses all of it. The deliveries from `intents.near` that we trace explain 0.97<!--n:bb_deliveries_90d_m-->M NEAR of it. The other 0.511<!--n:bb_growth_not_delivered_m-->M NEAR (34.5<!--n:bb_growth_not_delivered_pct-->%) is not explained by the committed data, which holds no transfers from other accounts.

Two later reads of the chain trace that remainder. Neither is in the committed data, so no figure from them is marked here. The first, on 2026-11-08 (`docs/sources-checked.md`, 2.7), traces it to ten native transfers from other accounts. Almost all of it came from `1csfundsadmin.sputnik-dao.near`, another NEAR revenue wallet, through two of that DAO's transfer proposals. The second, on 2026-11-13 (`docs/sources-checked.md`, rows 5.2 and 5.3), traces where that wallet's NEAR came from: 484 native withdrawals from `intents.near`, about 555,340 NEAR in all. Almost all of them fall between 2026-01-31 and 2026-04-30 and come from two recurring `intents.near` accounts, neither of them the window's two collectors. NEAR's revenue dashboard shows 555,348.3 NEAR for that wallet.

So the remainder is Intents revenue earned in February to April 2026 and moved into the buyback wallet on 2026-09-09, inside the H1c window. About a third of the numerator is revenue earned before the window and moved between NEAR's own wallets inside it. The verdict is inconclusive whichever numerator is used, because label coverage is below 50%.
