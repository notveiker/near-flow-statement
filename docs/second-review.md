# Second review (exploratory)

This page records a second review of the repository and its sources, made on 2026-11-12. That was after the freeze, after the H1a-H1c results, and after the forward-test window opened.

- **Everything here is exploratory.** It was chosen after the freeze and is not pre-registered. It changes no pre-registered result: H1a fails, H1b and H1c are inconclusive, and the frozen rule outputs Hold.
- **Data are dated 2026-11-04 or earlier** unless a line says otherwise.
- **Every figure says how to recompute it:** from a committed file (which rows, and which rule), or from a chain read at a named block. A figure is in `data/metrics.json` only if it carries a marker.
- **Disclosures and corrections** from the same review are in [`PREREG-ADDENDUM.md`](../PREREG-ADDENDUM.md), in the 2026-11-12 23:50 UTC entry.

## 1. Who holds the captured NEAR, and on what terms

- **Balances.** At block 223,088,015, the last block of 2026-11-04, `view_account` gives:
  - `fefundsadmin.sputnik-dao.near` (the front-end fund): 1,973,571 NEAR;
  - `1csfundsadmin.sputnik-dao.near`: 271 NEAR.

  Neither has any NEAR locked. The buyback wallet's balance at the same block is in `data/raw/rpc/buyback_balance_endpoints.json`. With it, the front-end fund holds 47.6% of the three wallets' NEAR. None of the three wallets burns, stakes or locks its NEAR.
- **Which wallet got the ladder's arrivals.** Of the ladder's 15.81<!--n:ladder_all_wallets_pct_of_issuance-->%, 11.0<!--n:ladder_buyback_only_pct_of_issuance-->% arrived in the buyback wallet. The other 4.81 points arrived in the front-end fund.
- **The front-end fund has never sent NEAR to the buyback wallet.** Its 17 proposals (ids 0-16; `get_proposals` at the same block) include no NEAR transfer. Its 15 approved transfers moved 2,450,900 USDC:
  - ten to `auroraliqsupport.near`;
  - four to `aurorafinance.sputnik-dao.near`;
  - one to `aurorasupport.near`.

  These are the recipient account ids as the chain records them. Their names do not show who controls the accounts, and the review did not establish what these transfers paid for. Nothing here suggests that they were improper. Some of the USDC appears to have come back as NEAR bought through NEAR Intents; that was not re-checked.
- **Who decides.** The fund's policy at the same block (`get_policy`) gives the same five members to its Requestor, Admin and Approver roles: `aurorafinance1.near`, `aurorafinance2.near`, `aurorafinance3.near`, `auroracfo.near` and `paperclip-maximizer.near`.
  - A transfer needs 2 approvals.
  - A policy change, a new member or a code upgrade (`upgrade_self`) needs one Admin vote.
- **What the terms say.** The 1Click terms make forwarding the fees a permission: section 3 of `THESIS.md` quotes "may be directed". No document the review read gives NEAR holders a claim on the fees.
- **Reading (inferred).** "Value capture" here means fees that an operator chooses to route to wallets held by two different signer sets. The ladder measures arrivals in those wallets, not NEAR removed from supply.

## 2. The escrow share rose in a step, not a trend

All figures in this section come from `data/raw/escrow/deliveries.csv`, summing `amount_yocto` by `wallet`, `path` and `day`.

| Period | Buyback wallet: escrow share of NEAR delivered | Front-end fund: escrow share |
|---|---|---|
| 2026-07-07 to 07-31 | 17.5% | 31.0% |
| 2026-08-15 to 08-28 | 28.4% | 52.7% |
| 2026-08-29 to 09-02 | 53.4% | 90.6% |
| 2026-09-03 to 10-26 | 55.1% | 98.2% |
| 2026-10-27 to 11-04 | 56.4% | 100.0% |

- **The monthly figures are the same step.** The figures in section 5 of `THESIS.md` (28.6<!--n:escrow_share_buyback_2026_08_pct-->%, 53.0<!--n:escrow_share_buyback_2026_09_pct-->%, 57.4<!--n:escrow_share_buyback_2026_10_pct-->%) are this step seen through calendar months. From 09-03 the buyback wallet's weekly share moves between 43% and 73%, with no trend.
- **The public front-end fee stopped on the same dates.**
  - near.com's public fee account (`176121bd…`, rows whose `path_detail` starts with `recurring:176121bd`) paid the front-end fund 1,940 NEAR a day over 07-07 to 08-28, and 107 a day over 08-29 to 11-04.
  - Escrow releases to the fund rose from 1,399 to 4,901 NEAR a day, which is more than the public stream lost.
  - The dates match near.com making confidential settlement its default at the end of August. The review found this only in secondary reports; NEAR Intents' changelog does not list it.
- **Reading (inferred).** "The share keeps rising" is not what the data show. There was a drift through July and August, then a step at 08-29, then a flat level. The bottom-of-range test in section 5 of `THESIS.md` ("stops rising") is therefore already met, for a reason that says nothing about whether the releases are fees.

## 3. A documented 1Click price change on 2026-09-03

- **The fee pages changed.**
  - The archived fee page of 2026-08-11 ([web.archive.org/web/20260811143259/https://docs.near-intents.org/resources/fees](https://web.archive.org/web/20260811143259/https://docs.near-intents.org/resources/fees)) reads "With API key Only the 0.0001% protocol fee".
  - The archived fee-configuration page of 2026-10-05 ([web.archive.org/web/20261005092048/https://docs.near-intents.org/integration/distribution-channels/1click-api/fee-config](https://web.archive.org/web/20261005092048/https://docs.near-intents.org/integration/distribution-channels/1click-api/fee-config)) reads "1Click charges 20 bps", with 1 bp on stablecoin pairs, and "1Click's half has a 20 bps minimum".
- **The 1Click data change on 09-03.** In `data/raw/explorer/daily.json`, `fee_split.usd_in_no_fee_listed` divided by `usd_in` gives:
  - 25.7% of 1Click volume listing no fee on 09-02, and 1.4% on 09-03;
  - 37.5% over 08-07 to 09-01, and 5.9% over 09-03 to 10-05.
- **DefiLlama shows the same step.** Captured revenue per dollar of volume (`data/raw/llama/`, revenue divided by volume over the same days) is 2.49 bp over 08-29 to 09-02, and 4.62 bp over 09-03 to 10-26. (Note, 2026-11-13: DefiLlama's volume itself changes definition on 2026-09-01, so three of the first window's five days are on the new definition and two on the old; [`leg-count.md`](leg-count.md).)
- **One channel ran for a single week.** The `trustwallet` channel in `by_channel` appears on 7 days only, 10-23 to 10-29. It lists 12.0% of the explicit buyback fees of the 30 days to 11-04. Without it the explicit rate is 3.68 bp, against 4.08<!--n:take_b3_bb_explicit_bp--> bp with it.
- **Reading (inferred).** The rise in the explicit fee in section 3 of `THESIS.md` is mainly a price change, not organic growth, so it should not be annualised.

## 4. The public trail is thinning after 2026-10-27

- **Transfer counts are falling.** From `data/raw/bq/collector_inflows.json` (sum of `n` per collector and day):

  | Collector | Average a day, 10-06 to 10-28 | 10-29 | 11-03 | 11-04 |
  |---|---|---|---|---|
  | B | 4,387 | 2,577 | 1,594 | 109 |
  | A | 7,682 | 6,099 | 5,375 | 2,739 |

- **The change is documented.** NEAR Intents' changelog says that 1Click swaps settle confidentially from 2026-10-27. Samples of settlement batches read during the review (not committed) suggest the move was gradual rather than a single switch.
- **Reading (inferred).** The 4.53<!--n:ladder_public_collectors_pct_of_issuance-->% rung traceable to public collectors describes a settlement regime that is ending. The per-swap method of `docs/intents-fee-flows.md` will not be repeatable on confidential swaps.

## 5. Price and issuance policy move the ratios

- **Dollars and NEAR diverge.** By 30-day block, DefiLlama revenue and the NEAR that arrived in the three wallets (`deliveries.csv`) were:

  | Block | DefiLlama revenue | NEAR arrived |
  |---|---|---|
  | 08-07 to 09-05 | $910,120 | 486,064 |
  | 09-06 to 10-05 | $1,934,392 | 506,616 |
  | 10-06 to 11-04 | $1,992,164 | 418,766 |

  Revenue rose 118.9% in dollars while NEAR arrivals fell 13.8%.
- **Half the share comes from the inflation cut.** The ladder divides NEAR by net issuance, and protocol v81 (2025-10-29) halved the inflation cap. At the old cap, the same arrivals would be about 7.9% of net issuance, not 15.81<!--n:ladder_all_wallets_pct_of_issuance-->%. The arithmetic is the ladder share × (g − b) ÷ (2g − b), where g is the window's gross issuance (8.0098<!--n:h1a_gross_issuance_90d_m-->M NEAR) and b its burn (76.84<!--n:h1a_burn_90d_k-->K NEAR) over the same 90 days.
- **Reading (inferred).** The capture share, the take rate and G_obs depend partly on NEAR's price and on the issuance cap that governance sets.

## 6. G_obs measures a step in the capture ratio

These figures compare the 180 days to 2026-11-04 with the 180 days before, using `data/raw/llama/` sums:

- **Revenue grew 2.645-fold**, which annualises to 619<!--n:rating_g_obs_pct-->%, the pipeline's figure.
- **Over the same windows, fees rose only 3.4% and volume 29.6%.** Revenue went from 9.5% to 24.4% of fees. (Note, 2026-11-13: the later window holds 65 days after 2026-09-01, when DefiLlama's volume began to count confidential-treasury flow, so part of the 29.6% is that change of definition. The revenue-to-fees ratio uses no volume; [`leg-count.md`](leg-count.md).)
- **The figure is fragile.** With 182-day windows the same calculation gives 426%.
- **Reading (inferred).** The growth leg of the frozen rule rests on a rise in the share of fees captured, which sections 2 and 3 date to late August and September. It does not rest on growth in activity. Hold is unchanged.

## 7. DefiLlama is not an independent check

- **The same wallets.** DefiLlama's NEAR Intents revenue adapter (`fees/near-intents/index.ts` in `DefiLlama/dimension-adapters`) counts NEAR and wNEAR arriving in the same three wallets. It cites NEAR's own Dune query 6740088. The 100.9<!--n:revwallets_vs_llama_rev_pct-->% match in `docs/intents-fee-flows.md` therefore confirms the pricing and the wallet list. It is not a count from a second source.
- **The volume series is NEAR's own.** DefiLlama's NEAR Intents volume is a dataset that NEAR uploads to Dune. The review found no published definition of it.

## 8. H1b's lower bound turns on single days

Inputs: `data/raw/bq/h1b_a_native_flows.json` and `h1b_b_wnear_logs.json`, level 3, under the rules in `pipeline/h1b.py`, dropping one day at a time.

- **The bound is a small net of large flows.** The 4.42<!--n:h1b_net_inflow_lower_m-->M NEAR lower bound is the net of 267.2M NEAR in and 262.8M NEAR out.
- **Single days move it across the threshold:**
  - without 2026-10-29: 17.60M;
  - without 2026-10-02: 8.76M;
  - without 2026-09-18: −1.35M.

  Two single days lift it above gross issuance (8.0098<!--n:h1a_gross_issuance_90d_m-->M), and one turns it negative.
- **Reading.** "Inconclusive" is right, and the bound is too unstable to be read as close to Buy.

## 9. H1a measures churn

Input: `data/raw/bq/staking_flows_daily.json`.

- **Gross flows dwarf rewards.** Over the 90 days, 188.0M NEAR flowed into staking pools and 235.3M out. That is 26.1 and 32.6 times the 7.2088<!--n:h1a_staking_rewards_90d_m-->M NEAR of rewards. The net, 47.26M, is the 6.56<!--n:h1a_ratio_as_written_x-->× of H1a as written.
- **The fail survives trimming.** Dropping the 5 largest net-outflow days and the 5 largest net-inflow days leaves 4.67×. Dropping 10 of each leaves 2.79×. H1a still fails either way.
- **Reading.** The fail is robust. But the test compares a net of large principal moves with rewards, so it does not show whether the rewards themselves stay staked.

## 10. The partner-fee floor

- **What the published floor counts.** `partners_kept_vs_near_rev_low_x` (1.75<!--n:partners_kept_vs_near_rev_low_x-->×) subtracts from the listed partner fees ($4,454.2<!--n:explorer_partner_fees_all_usd_k-->K) only the buyback wallet's unexplained dollars ($942.2<!--n:buybacks_unexplained_usd_k-->K).
- **A lower floor.** If the front-end fund's escrow arrivals ($616.9<!--n:revwallets_frontend_usd_k-->K) may also be partner money:
  - the floor is (listed partner fees − unexplained buyback dollars − front-end escrow arrivals) ÷ the revenue wallets' $2,009.7<!--n:revwallets_usd_k-->K = 1.44<!--n:partners_kept_vs_near_rev_floor_x-->× (`partners_kept_vs_near_rev_floor_x`, added 2026-11-13);
  - NEAR's share of the partner fees on swaps without a buyback entry is at most 37.0<!--n:near_share_of_partner_fees_max_wide_pct-->%.
- **Context.** `THESIS.md` already states that the published floor leaves the front-end fund out. This section gives the number.

## 11. The peer set

- **Only one venue is halved.** The net share (38.6<!--n:intents_share_peerset_30d_net_pct-->%) halves NEAR Intents' volume only. (Note, 2026-11-13: halving is exact for public swaps but not for the confidential flow DefiLlama counts from 2026-09-01; restated on one-sided volume the share is 46.6<!--n:legcount_peer_share_lo_pct-->% to 48.1<!--n:legcount_peer_share_hi_pct-->% if that flow is swap volume, 23.9<!--n:legcount_peer_share_public_lo_pct-->% to 25.0<!--n:legcount_peer_share_public_hi_pct-->% if not; [`leg-count.md`](leg-count.md).) DefiLlama's THORChain and Maya adapters read Midgard's `totalVolume`, which counts both pool legs of an asset-to-asset swap.
- **A like-for-like share is not computable here.** Treating every venue alike moves the share up from the net figure toward the reported 55.7<!--n:intents_share_peerset_30d_pct-->%. Where it lands needs Midgard's leg split, which the committed data do not hold.
- **The ranking depends on the set.** Intents leads the four venues in the thesis's peer set. Intent-based bridges such as Relay and Across report larger 30-day volumes on DefiLlama (not committed here), so a wider set changes the ranking.

## 12. What ties Intents to the token

- **The verifier's own fee is tiny.** At block 223,088,015, `intents.near` returns `fee` 1 (one pip, 0.0001%), paid to `fee_collector` `7066024d…7f05`. The revenue the ladder counts comes from 1Click's fee configuration, which is off-chain, not from the contract.
- **The swap step has moved off mainnet.** According to NEAR Intents' documentation, since 2026-10-27 the swap step of 1Click runs on the NEAR Private Shard. Custody, deposits and withdrawals stay on NEAR mainnet.
- **Reading (inferred).** The fees reach the token through a routing choice that can be reversed. The contract does not enforce it.

## What this review did not settle

- **Whether DefiLlama's NEAR Intents volume counts both legs of each swap.** This moves every take rate and the peer share by about 2×. Summing one day of `intents.near` settlement legs before 2026-11-05 and comparing it with DefiLlama's volume for that day would settle it. (Settled in part on 2026-11-13, exploratory: it counts both legs of public swaps, and from 2026-09-01 confidential-treasury flow at about one leg. What that flow represents is still open; [`leg-count.md`](leg-count.md).)
- **Who sold the NEAR that the front-end fund bought with USDC.**
- **How much of the escrow stream is near.com's front-end fee moved off the public rails,** as against new fees.
- **Whether the escrow releases are fee revenue at all.** That is still unattested. Section 5 of `THESIS.md` already names an attestation by NEAR as the evidence that would settle it.
