# Collector rung split by funder (exploratory)

Written 2026-11-13, after the freeze, by an AI coding assistant at the owner's request. It changes no pre-registered result and does not feed the rating rule. Terms are in the [glossary](glossary.md).

## Question

The ladder's collector rung, 4.53<!--n:ladder_public_collectors_pct_of_issuance--> points of net issuance over 2026-10-06 to 11-04, is the NEAR that collectors A (`5880ad2b…47dd`, explicit buyback fee) and B (`143f2bb4…3cfb31`) delivered to the revenue wallets. NEAR Intents' changelog says 1Click swaps settle confidentially from 2026-10-27, so some of the fees reaching the collectors may themselves have come through the Confidential Intents escrow. How much?

## Method

- **Data.** `sql/collector_inflow_funders.sql` reads every dip4 `transfer` into A or B in the window (330,260<!--n:collectors_transfers_n--> transfers) and classifies its sender:
  - `escrow_direct`: the sender is the escrow (`51e8f94d…7cbe`);
  - `escrow_funded`: the sender received a dip4 transfer from the escrow between 2026-09-22 and that block;
  - `public_swap`: otherwise, and the same receipt carries a `token_diff` for the sender;
  - `other`: none of these.
- **Reconciled.** Summed over class, the output equals `data/raw/bq/collector_inflows.json` for every day, collector and token, amounts and counts. `pipeline/compute.py` (`collector_funders`) stops the build if it does not.
- **Checked.** `sql/collector_funder_checks.sql`: every escrow-funded sender paid a collector exactly once (100.0<!--n:collector_escrow_funded_sender_single_tx_pct-->%), on one day (100.0<!--n:collector_escrow_funded_sender_single_day_pct-->%); 99.8<!--n:collector_escrow_funded_funded_once_pct-->% were funded by the escrow once, and 95.4<!--n:collector_escrow_funded_no_other_inflow_pct-->% had no dip4 transfer from anyone else. The median gap from funding to fee was at most 6<!--n:collector_escrow_funded_lag_blocks_median_max--> blocks in each period, and the longest was 278,526<!--n:collector_escrow_funded_lag_blocks_max--> blocks (about three days). **Overlap (disclosed 2026-11-13):** 12,846<!--n:collector_escrow_funded_with_diff_n--> of the escrow-funded transfers (19.8<!--n:collector_escrow_funded_with_diff_pct-->%; 10,633<!--n:collector_escrow_funded_with_diff_pre_n--> before 2026-10-27, 2,213<!--n:collector_escrow_funded_with_diff_post_n--> from then) also carried the sender's `token_diff` in the same receipt: public swaps by accounts the escrow had funded. The class rule puts them in `escrow_funded`, so "publicly settled" in this file means "not escrow-funded". Their share of the USD value is not computed, because the committed amounts are not split by that flag. Every `public_swap` transfer came with the sender's `token_diff` in the same receipt (100.0<!--n:collector_public_swap_with_token_diff_pct-->%).
- **Weighting.** USD value at committed CoinGecko prices (`token_usd`, as for `collector_a_inflow_usd_k`). The collectors' NEAR comes from all their fee tokens: collector A's wNEAR fees were 11.8<!--n:collector_a_wnear_inflow_near_k-->K NEAR against 97.6<!--n:collector_a_delivered_near_k-->K NEAR delivered.
- **Timing.** Each day's NEAR delivered (`data/raw/escrow/deliveries.csv`, paths `collector_a` and `collector_b`) takes that day's escrow share. Collector A delivers the day it is paid: the correlation of its daily fee value with its daily deliveries is 0.93<!--n:collector_a_inflow_delivery_corr_lag0--> on the same day and 0.45<!--n:collector_a_inflow_delivery_corr_lag1--> a day later.

## Result

| Part of the collector rung | NEAR | % of net issuance |
|---|---|---|
| Fees from publicly settled swaps | 105.2<!--n:ladder_collectors_public_swap_near_k-->K | 3.97<!--n:ladder_collectors_public_swap_pct_of_issuance--> |
| … collector A | | 3.12<!--n:ladder_collector_a_public_swap_pct_of_issuance--> |
| … collector B | | 0.85<!--n:ladder_collector_b_public_swap_pct_of_issuance--> |
| Fees paid from escrow-funded single-use accounts (all collector A) | 14.8<!--n:ladder_collectors_escrow_funded_near_k-->K | 0.56<!--n:ladder_collectors_escrow_funded_pct_of_issuance--> |
| Escrow directly, or other | under 1 NEAR | 0.00 |

- **Through the escrow in all:** 11.25<!--n:ladder_escrow_unshields_pct_of_issuance--> (unshields to the wallets) + 0.56<!--n:ladder_collectors_escrow_funded_pct_of_issuance--> = 11.81<!--n:ladder_escrow_all_pct_of_issuance--> points.
- **Range for the escrow part:**
  - 0.55<!--n:ladder_collectors_escrow_funded_pooled_pct_of_issuance-->, with shares pooled before and after 2026-10-27 instead of taken by day;
  - 0.58<!--n:ladder_collectors_escrow_funded_imputed_pct_of_issuance-->, if collector A's transfers in unpriced tokens (12.2<!--n:collector_a_unpriced_transfers_pct-->%) are valued at their class mean.
- **Weighting by count would overstate it:** 1.13<!--n:ladder_collectors_escrow_funded_by_count_pct_of_issuance--> points. Before 10-27 escrow-funded fees averaged $0.2<!--n:collector_a_escrow_funded_mean_fee_pre_usd--> against $2.85<!--n:collector_a_public_swap_mean_fee_pre_usd--> for public ones.
- **Collector A by period:** the escrow-funded share of its fee value was 2.4<!--n:collector_a_escrow_usd_share_pre_pct-->% over 10-06 to 10-26 (28.0<!--n:collector_a_escrow_count_share_pre_pct-->% of transfers) and 39.4<!--n:collector_a_escrow_usd_share_post_pct-->% from 10-27 (36.1<!--n:collector_a_escrow_count_share_post_pct-->% of transfers). It rose from 5.7<!--n:collector_a_escrow_usd_share_first_post_day_pct-->% on 10-27 to 96.0<!--n:collector_a_escrow_usd_share_last_day_pct-->% on 11-04.
- **Collector B** received no escrow-funded fee (0<!--n:collector_b_escrow_funded_n-->).

## Daily table

Same-day attribution. "A escrow $ share" is the escrow-funded share of collector A's priced fee value that day; "NEAR out" is NEAR delivered to the revenue wallets.

| Day | A transfers | A escrow-funded | A inflow $ | A escrow $ share | A NEAR out | A NEAR via escrow | B transfers | B inflow $ | B NEAR out | Public NEAR | Escrow NEAR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10-06 | 7,726 | 2,452 | 7,432 | 5.0% | 1,308 | 66 | 3,985 | 2,267 | 412 | 1,654 | 66 |
| 10-07 | 7,827 | 2,458 | 10,387 | 3.9% | 2,116 | 83 | 4,565 | 3,564 | 634 | 2,668 | 83 |
| 10-08 | 9,982 | 3,772 | 13,646 | 3.6% | 2,240 | 82 | 6,641 | 5,985 | 1,274 | 3,432 | 82 |
| 10-09 | 9,910 | 2,999 | 32,087 | 1.6% | 7,974 | 126 | 5,780 | 4,695 | 1,088 | 8,936 | 126 |
| 10-10 | 7,816 | 2,491 | 22,895 | 1.5% | 4,463 | 66 | 4,443 | 7,131 | 1,303 | 5,699 | 66 |
| 10-11 | 7,437 | 2,420 | 27,450 | 0.9% | 4,772 | 45 | 4,296 | 4,378 | 903 | 5,630 | 45 |
| 10-12 | 8,937 | 3,043 | 11,961 | 3.2% | 2,310 | 74 | 5,266 | 3,874 | 605 | 2,841 | 74 |
| 10-13 | 9,182 | 3,320 | 8,834 | 3.7% | 1,856 | 69 | 5,261 | 1,728 | 420 | 2,207 | 69 |
| 10-14 | 9,138 | 3,058 | 10,883 | 3.3% | 2,271 | 75 | 5,439 | 3,258 | 680 | 2,876 | 75 |
| 10-15 | 6,750 | 1,826 | 9,762 | 3.0% | 1,750 | 53 | 4,609 | 3,710 | 591 | 2,287 | 53 |
| 10-16 | 7,424 | 2,208 | 8,155 | 4.3% | 1,675 | 72 | 4,086 | 2,437 | 627 | 2,230 | 72 |
| 10-17 | 5,934 | 1,347 | 9,336 | 3.5% | 1,949 | 67 | 3,005 | 1,506 | 217 | 2,099 | 67 |
| 10-18 | 5,505 | 1,277 | 7,552 | 3.2% | 1,612 | 52 | 3,237 | 4,817 | 650 | 2,210 | 52 |
| 10-19 | 6,716 | 1,574 | 18,795 | 2.1% | 2,915 | 60 | 3,743 | 1,854 | 665 | 3,520 | 60 |
| 10-20 | 6,186 | 1,519 | 12,766 | 2.6% | 3,055 | 80 | 3,166 | 9,675 | 2,587 | 5,562 | 80 |
| 10-21 | 7,375 | 1,822 | 10,418 | 4.4% | 2,413 | 107 | 4,349 | 3,351 | 649 | 2,954 | 107 |
| 10-22 | 7,752 | 1,794 | 12,767 | 2.4% | 2,770 | 67 | 4,023 | 2,557 | 486 | 3,190 | 67 |
| 10-23 | 7,736 | 1,630 | 13,914 | 2.1% | 3,271 | 68 | 4,300 | 3,180 | 652 | 3,854 | 68 |
| 10-24 | 7,094 | 1,421 | 12,698 | 1.9% | 2,842 | 53 | 3,885 | 1,679 | 237 | 3,025 | 53 |
| 10-25 | 6,575 | 1,288 | 21,014 | 1.2% | 5,153 | 61 | 3,521 | 4,317 | 1,139 | 6,231 | 61 |
| 10-26 | 7,982 | 1,363 | 23,804 | 1.3% | 5,767 | 77 | 4,579 | 7,845 | 1,609 | 7,299 | 77 |
| 10-27 | 8,836 | 1,359 | 22,671 | 5.7% | 5,014 | 285 | 4,793 | 4,820 | 960 | 5,690 | 285 |
| 10-28 | 6,872 | 1,592 | 16,242 | 9.2% | 3,964 | 364 | 3,930 | 3,677 | 933 | 4,533 | 364 |
| 10-29 | 6,099 | 2,214 | 9,952 | 36.5% | 4,434 | 1,619 | 2,577 | 3,980 | 1,140 | 3,954 | 1,619 |
| 10-30 | 7,948 | 2,996 | 18,900 | 40.5% | 4,490 | 1,817 | 3,331 | 3,858 | 991 | 3,663 | 1,817 |
| 10-31 | 5,760 | 2,179 | 16,449 | 53.0% | 3,843 | 2,037 | 1,945 | 948 | 230 | 2,037 | 2,037 |
| 11-01 | 5,995 | 2,218 | 10,659 | 50.4% | 2,633 | 1,326 | 2,106 | 1,098 | 239 | 1,546 | 1,326 |
| 11-02 | 5,119 | 1,994 | 17,570 | 53.4% | 4,360 | 2,329 | 1,969 | 1,048 | 272 | 2,304 | 2,329 |
| 11-03 | 5,375 | 2,688 | 8,163 | 68.5% | 2,334 | 1,598 | 1,594 | 802 | 265 | 1,000 | 1,598 |
| 11-04 | 2,739 | 2,533 | 7,854 | 96.0% | 2,002 | 1,921 | 109 | 123 | 0 | 81 | 1,921 |
| **30 days** | | | | | **97,554** | **14,799** | | | **22,458** | **105,213** | **14,799** |

## What this does not show

- **Which fee the escrow-funded accounts paid.** The fees reach collector A, the explicit buyback fee's collector, so they are consistent with buyback fees on confidentially settled swaps. The swap itself is not visible; its public trace, a solver shield paired with an unshield, is described in [`confidential-flow.md`](confidential-flow.md).
- **Before 2026-09-22.** The query looks for escrow funding from 2026-09-22 only. The median gap is a few blocks, so a sender funded earlier would be unusual, but it would be counted as `public_swap` (if it swapped publicly) or `other`.
- **Prices.** Unpriced tokens are left out of the USD shares; the imputed reading above bounds their effect.

## Recipe

```bash
python3 -m pipeline.compute   # recomputes every number above from the committed data, offline
NFS_BQ_MAX_GB=80 python3 -m pipeline.bq_run collector_inflow_funders   # re-runs the query (gcloud; about 67 GB)
NFS_BQ_MAX_GB=80 python3 -m pipeline.bq_run collector_funder_checks    # the checks (about 67 GB)
```
