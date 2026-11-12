# How much of NEAR's value capture can you verify?

*An investment thesis for NEAR, built as a token flow statement. Window: the 30 days to 2026-11-04 for value capture, the 90 days 2026-08-07 → 11-04 for supply. Every number marked with an `n:` comment is recomputed from committed data by `make reproduce`.*

**The pre-registered result comes first.** H1b, whether less NEAR reached exchanges than was minted, is **inconclusive**. Only 20.0 <!--n:h1b_coverage_count_pct-->% of the top-100 NEAR receivers carry a citable exchange label, below the 50% our pre-registration requires, so net exchange inflow is reported as a range: 4.42 <!--n:h1b_net_inflow_lower_m-->M to 152.45 <!--n:h1b_net_inflow_upper_m-->M NEAR, against 8.0098 <!--n:h1a_gross_issuance_90d_m-->M NEAR minted. H1a fails: net staking outflow was 6.56 <!--n:h1a_ratio_as_written_x-->× staking rewards. H1c is inconclusive. The frozen rating rule therefore outputs **Hold**: Buy needed H1b to pass, Avoid needed it to fail. Everything below the scorecard, including the headline ladder, is **exploratory and was chosen after the freeze** ([`PREREG-ADDENDUM.md`](PREREG-ADDENDUM.md), 2026-11-07 entry).

## The thesis in one paragraph

NEAR mints about 88,295 <!--n:net_issuance_near_per_day_window--> NEAR a day. Over the 30 days to 2026-11-04, the NEAR that verifiably arrived in NEAR's three Intents revenue wallets offset **15.81 <!--n:ladder_all_wallets_pct_of_issuance-->%** of that. Only **4.53 <!--n:ladder_public_collectors_pct_of_issuance-->** points of it can be traced on chain to public fee collectors. The other **11.25 <!--n:ladder_escrow_unshields_pct_of_issuance-->** points arrived as releases from the Confidential Intents escrow: the NEAR is there, but which fee stream paid for it is not visible from outside. So NEAR's measured value capture is a range, 4.5-15.8% of issuance, and a per-stream attestation by NEAR would collapse it to one number. Even the top of the range covers about a sixth of issuance, and the buyback wallet's NEAR is held, not burned.

## 1. The ladder (exploratory, post-freeze)

| Rung, 30 days to 2026-11-04 | % of net issuance |
|---|---|
| NEAR delivered to all three revenue wallets (base case for valuation) | 15.81 <!--n:ladder_all_wallets_pct_of_issuance--> |
| … of which the buyback wallet alone | 11.00 <!--n:ladder_buyback_only_pct_of_issuance--> |
| Traceable to two recurring public fee collectors | 4.53 <!--n:ladder_public_collectors_pct_of_issuance--> |
| Released from the Confidential Intents escrow; fee stream unattested | 11.25 <!--n:ladder_escrow_unshields_pct_of_issuance--> |
| One other recurring source | 0.03 <!--n:ladder_other_pct_of_issuance--> |

- **The rungs are not nested.** Collectors + escrow + the other source = all three wallets. The buyback-wallet line is a subset of the total.
- **Denominator.** Net issuance is 88,295 NEAR/day, from archival `total_supply` at blocks 218,718,000 and 223,087,766 (`data/raw/escrow/issuance_reads.json`), matched to the window. The repo's older figure, 15.7 <!--n:coverage_rev_near_30d_pct-->% on 88.2 <!--n:net_issuance_near_per_day_30d_k-->K/day, is the same quantity on a slightly different denominator.
- **The top rung reconciles.** Our three-wallet total, 418.8 <!--n:revwallets_near_k-->K NEAR, is 100.9 <!--n:revwallets_vs_llama_rev_pct-->% of DefiLlama's reported Intents revenue for the same days.
- **The escrow share is rising.** Share of the buyback wallet's NEAR that arrived via the escrow: Aug 28.6 <!--n:escrow_share_buyback_2026_08_pct-->%, Sep 53.0 <!--n:escrow_share_buyback_2026_09_pct-->%, Oct 57.4 <!--n:escrow_share_buyback_2026_10_pct-->%. (July from 07-07: 17.5 <!--n:escrow_share_buyback_2026_07_pct-->%.) Before October, the funding of each delivery is attributed from samples; October's is complete.
- **Valuation basis.** We value NEAR on what reaches the wallets, 15.81%. The 4.53% traceable-only figure is a labelled sensitivity, not the base case.

## 2. How we know it is the escrow, and what is actually missing

- **Unshields are exact-amount by design.** A confidential withdrawal shows on chain as the escrow paying the exact amount to a fresh account, which then withdraws it to a revenue wallet. In the window, all 909 <!--n:escrow_funded_exact_30d_n--> such deliveries were funded by the escrow for the exact amount, to the yoctoNEAR (100.0 <!--n:escrow_funded_exact_30d_pct-->%).
- **The escrow's identity is documented.** Account `51e8f94d…7cbe` is `PRIVATE_TREASURY_ACCOUNT_ID` in NEAR's Confidential Intents docs, "a production constant shared by all participants".
- **Anyone can re-check it.** Every delivery and its funding transfer is in `data/raw/escrow/deliveries.csv`. `python3 -m pipeline.fetch_escrow verify` re-reads rows from FastNEAR and archival RPC, with no key.
- **The escrow's ledger is public; the fee origin is not.** Its wNEAR balance reconciles to its transfer events at both ends of the window, deposits are visible, and releases to the revenue wallets are 1.2% of its outflow (`docs/chain-rebuild-results.md`).
- **What is missing is attestation, not NEAR.** The NEAR verifiably arrived. Two documented NEAR-side fee streams fit, and the public chain cannot split the 11.25 points between them:
  - **near.com's fees.** NEAR says near.com swaps "direct 100% of fees to a NEAR revenue wallet", without naming which. near.com's public-mode fee account pays the front-end fund (`fefundsadmin`), never the buyback wallet; its confidential-mode fee account exists only inside the private ledger.
  - **The Confidential Infrastructure Fee.** The 1Click terms (Schedule 1 §6.2, §6.4) say Intents Technology "sets, charges, and retains" it on confidential swaps, with no share to integrators. Forwarding it to NEAR's wallets is then a choice.
- **The falsifier.** A per-stream attestation by NEAR (which fees fund which escrow releases) would turn the range into one number. Nothing here alleges misconduct: this is a privacy feature working as designed, and the question is auditability.

## 3. Who else gets paid (1Click, 30 days)

These numbers come from the NEAR Intents Explorer API, which needs a partner key, and from on-chain wallet arithmetic. Details: [`docs/intents-fee-flows.md`](docs/intents-fee-flows.md), [`docs/partner-concentration.md`](docs/partner-concentration.md).

- **Captured take.** NEAR's captured revenue was 4.98 <!--n:take_captured_bp_30d-->bp of reported volume, 32.5 <!--n:capture_share_30d_pct-->% of gross fees.
- **Partners keep more than NEAR.** Partners kept at least 1.81 <!--n:partners_kept_vs_near_rev_low_tight_x-->× NEAR's entire captured revenue. On partner swaps with no buyback fee entry, at most 19.6 <!--n:near_share_of_partner_fees_max_tight_pct-->% of fees reaches NEAR's wallets. Per-swap evidence shows partners are paid their full listed fee on chain (for SwapKit, 102 <!--n:fee_ev_swapkit_fees_paid_onchain_n--> of 112 <!--n:fee_ev_swapkit_fees_listed_n--> fee entries sampled), so no split comes out of it. Whatever 1Click charges on top, and whether it forwards any of it to NEAR, is not visible.
- **SwapKit is the concentration risk.** It routes 38.2 <!--n:swapkit_vol_share_pct-->% of 1Click volume and paid NEAR $159 <!--n:swapkit_buyback_fees_usd--> in explicit fees over 30 days. If it left, NEAR would lose about 2.0 <!--n:swapkit_exit_traceable_pct-->% of captured revenue on the traceable streams, and at most 43.0 <!--n:swapkit_exit_ceiling_pct-->% (73.7 <!--n:swapkit_exit_ceiling_all_escrow_pct-->% if the escrow NEAR reaching the front-end fund is counted too). The ceilings exist because escrow NEAR cannot be attributed.
- **NEAR's take is rising, from a low base.** NEAR's explicit fee inside 1Click went from 1.83 <!--n:take_b1_bb_explicit_bp--> bp of volume (Aug 7 – Sep 5) to 4.08 <!--n:take_b3_bb_explicit_bp--> bp (Oct 6 – Nov 4), mostly because more volume carries a buyback fee entry (23.6 <!--n:take_b1_vol_with_bb_pct-->% → 43.0 <!--n:take_b3_vol_with_bb_pct-->%). Partner fees stayed about ten times higher (40.3 <!--n:take_b3_partner_bp--> bp in the last block).
- **Volume is not the token.** Intents is 55.7 <!--n:intents_share_peerset_30d_pct-->% of its cross-chain peer set by reported volume, but only 3.5 <!--n:explorer_near_side_swap_share_pct-->% of 1Click volume has NEAR on one side. 1Click was a net route out of NEAR: $24.0 <!--n:explorer_out_of_near_usd_m-->M out against $14.6 <!--n:explorer_into_near_usd_m-->M in.

## 4. The supply side (pre-registered)

Details: [`docs/supply-side.md`](docs/supply-side.md).

- **H1a fails.** Over the 90 days, stakers withdrew 6.56 <!--n:h1a_ratio_as_written_x-->× what they earned (5.96 <!--n:h1a_ratio_with_lst_pool_x-->× with `lst-pool.near` added). Prior research traces most of the net outflow to 14 accounts that reach one unlabelled hub; those accounts moved no NEAR into Intents.
- **H1b and H1c are inconclusive** for lack of exchange labels. The buyback wallet's growth, 1.48 <!--n:h1c_identified_buying_m-->M NEAR, is 33.48 <!--n:h1c_ratio_lower_pct-->% of the lower bound of exchange inflow and 0.97 <!--n:h1c_ratio_upper_pct-->% of the upper.
- **Rating: Hold**, as the frozen rule outputs. Required captured-revenue growth is 33.2 <!--n:rating_g_req_pct-->%/yr; observed is 619.0 <!--n:rating_g_obs_pct-->%/yr in USD and 71.4 <!--n:rating_g_obs_near_pct-->% in NEAR terms. The ladder does not feed the rule.

## 5. Risks and what would change our mind

- **Toward Buy.** A per-stream attestation showing the escrow releases are fee revenue would fix capture at the top of the range. Sourced exchange labels that raise coverage above 50% could let H1b pass, which, with G_obs above G_req, is the rule's Buy.
- **Toward Avoid.** Escrow releases that turn out to be one-off or discretionary; SwapKit or another large channel leaving; captured revenue growth falling below about 17%/yr, half of G_req.
- **Pending resolvers.** HSP-029's issuance cut clears its timelock on 2026-11-16, after the deadline; G_req assumes it. Forward tests F1-F4 are scored after 2026-11-14 by `pipeline/score_forward.py`, misses included.

## Limits

- **Collector roles.** Collector A's role (the explicit buyback fee) is cross-checked: its priced inflows are 96.5 <!--n:collector_a_vs_explicit_fees_pct-->% of the fees the Explorer lists. Collector B's role (a share of quote improvement) is inferred from committed, re-checkable per-swap evidence: it is paid a variable cut on 43 <!--n:fee_ev_collector_b_swaps_n--> of 195 <!--n:fee_ev_swaps_n--> sampled swaps across channels. The quote it would be measured against is not in the Explorer API, so the role is consistent with the docs rather than proven.
- **Partner numbers** rest on one key-gated source (the Explorer API).
- **Escrow funding** before October is sample-attributed.
- **Not reproduced here.** Prior exploratory work on NEAR's revenue dashboard and the front-end fund's history is not in this repo and is not cited.
