# The investment case: method and recipes (exploratory)

Chosen and built on 2026-11-13 (the Monte Carlo) and 2026-11-14 (the rest), after the freeze. Nothing here changes a hypothesis, threshold, probability or the rating rule, or feeds anything they compute. The summary and the view are in [`THESIS.md`](../THESIS.md), section 6; this file says how each figure is made, so that a reader can recompute it. Code: [`pipeline/investment_case.py`](../pipeline/investment_case.py) and [`pipeline/model.py`](../pipeline/model.py), both called by `python3 -m pipeline.compute`; every figure below is a metric in `data/metrics.json` (keys `ic_*` and `fwd_*`) and is checked against this file by `python3 -m pipeline.check --numbers`.

## Inputs

- **Captured revenue:** DefiLlama's near-intents `dailyRevenue` (`data/raw/llama/dailyRevenue_near-intents.json`), the same series as G_req. Over the 90 days to 2026-11-04 it is $4.84<!--n:rating_r90_usd_m-->M, $19.6<!--n:ic_rev_90d_ann_m-->M a year at that rate.
- **Market:** the peer set of `pipeline/compute.py` (NEAR Intents, THORChain, Chainflip, Maya), DefiLlama's reported daily volume. $18.98<!--n:ic_market_90d_b-->B over the 90 days.
- **Share and take:** Intents' share of the peer set's volume over the 90 days, 61.7<!--n:ic_share_90d_pct-->%, and its captured take, revenue ÷ volume, 4.13<!--n:ic_take_90d_bp--> bp. The gross fee, DefiLlama fees ÷ volume, is 15.2<!--n:ic_gross_bp_90d--> bp. The product market × share × take is the 90-day revenue exactly.
- **Market cap:** CoinGecko's snapshot committed at the freeze, $4.82<!--n:mcap_usd_b-->B; the rating rule's price, $3.67<!--n:price_usd-->.
- **Supply:** the rating rule's own daily path (`pipeline/h1a.py`, `g_req`): the realised share of the inflation cap and the post-v87 burn rate, with HSP-029's ramp and without it. Supply grows 1.094<!--n:ic_supply_factor_x-->× to 2031-11-04 with HSP-029.
- **Peer market caps:** `data/raw/coingecko/peer_caps_30d.json`, fetched on 2026-11-14 by `python3 -m pipeline.fetch_peer_caps` (CoinGecko `market_chart`, 30 days, hourly). Only the point nearest NEAR's snapshot is used.

## 1. What the price assumes (reverse DCF)

Required captured revenue in 2031 = market cap × (1 + r)^5 × (supply in 2031 ÷ supply today) ÷ X, where r is the required rise in NEAR's price a year and X the market cap ÷ revenue multiple in 2031. It sets all of NEAR's market cap against Intents' captured revenue: it is what Intents would need if it carried the price alone. Both are assumptions; the grid is r of 10<!--n:ic_grid_r0_pct-->%, 15<!--n:ic_grid_r1_pct-->% and 20<!--n:ic_grid_r2_pct-->% and X of 10<!--n:ic_grid_x0-->, 25<!--n:ic_grid_x1--> and 50<!--n:ic_grid_x2-->. The supply factor is there because the return is on the price and buybacks burn nothing: the market cap has to grow faster than the price by that factor (a holder who stakes also receives part of the new supply). The growth assumed is (required ÷ today's)^(1/5) − 1: 84.9<!--n:ic_implied_cagr_r15_x25_pct-->% a year at the base (15<!--n:ic_base_r_pct-->%, 25<!--n:ic_base_x-->×), $424<!--n:ic_required_rev_2031_m-->M in 2031, 21.6<!--n:ic_required_multiple_x-->× today.

*Recipe:* `python3 -c "print((4815381622*1.15**5*1.094/25/19.6e6)**0.2-1)"` gives about 0.85 (the committed computation uses unrounded inputs).

## 2. The market's growth

Annual peer-set volume over the 365 days to 2026-11-04 and the four years before it: $53.0<!--n:ic_market_y0_b-->B, $46.7<!--n:ic_market_y1_b-->B, $55.1<!--n:ic_market_y2_b-->B, $9.6<!--n:ic_market_y3_b-->B, $11.3<!--n:ic_market_y4_b-->B (newest first). Growth a year over one to four years: 13.4<!--n:ic_market_cagr_1y_pct-->%, -1.9<!--n:ic_market_cagr_2y_pct-->%, 76.9<!--n:ic_market_cagr_3y_pct-->%, 47.1<!--n:ic_market_cagr_4y_pct-->%. Before 2024 the set is THORChain alone (Chainflip from 2024-06, NEAR Intents from 2024-12, Maya from 2025-08 in DefiLlama), so the older years measure one venue. Last year's growth is all Intents' own (its volume grew 9.0<!--n:ic_intents_vol_1y_x-->×): without Intents the venues changed by -53.4<!--n:ic_market_ex_intents_cagr_1y_pct-->% last year, -39.6<!--n:ic_market_ex_intents_cagr_2y_pct-->% a year over two years and 15.4<!--n:ic_market_ex_intents_cagr_4y_pct-->% a year over four. Part of last year's rise is DefiLlama's 2026-09-01 change in what it counts as Intents volume ([`leg-count.md`](leg-count.md)).

## 3. What would have to multiply

Required multiple 21.6<!--n:ic_required_multiple_x--> = market × share × take factors. Market at its last-year pace for five years: 1.87<!--n:ic_mult_market_x-->. Share from the 90 days to its twelve-month monthly high, 78.6<!--n:ic_share_max_pct-->% in 2026-06: 1.27<!--n:ic_mult_share_x-->. Left for the take: 9.1<!--n:ic_mult_take_x-->, so a take of 37.4<!--n:ic_take_needed_bp--> bp, 2.5<!--n:ic_take_needed_vs_gross_x-->× the gross fee. With NEAR taking the whole gross fee at the high share, the market would need 35.7<!--n:ic_market_cagr_needed_full_fee_pct-->% a year. Each factor is on DefiLlama's reported volume; only their product, the revenue, is unaffected by its basis, and because last year's market growth is all Intents' and partly the 2026-09-01 change, the market factor is generous and the take needed, if anything, understated.

## 4. Scenarios and sensitivity

Each scenario sets market growth, share, take and HSP-029 to values in the data, then computes 90-day captured revenue in 2031 against the 90-day USD value of net new supply on the rule's path at $3.67<!--n:price_usd-->.

| | Market a year | Share | Take | HSP-029 | Coverage, 2031-11-04 |
|---|---|---|---|---|---|
| Bear | two-year pace, -1.9<!--n:ic_bear_market_cagr_pct-->% | twelve-month low, 48.5<!--n:ic_bear_share_pct-->% | lowest month since the fee switch, 1.36<!--n:ic_bear_take_bp--> bp | no | 3.5<!--n:ic_bear_coverage_2031_pct-->% |
| Base | last year, 13.4<!--n:ic_base_market_cagr_pct-->% | 90 days, 61.7<!--n:ic_base_share_pct-->% | 90 days, 4.13<!--n:ic_base_take_bp--> bp | yes | 44.6<!--n:ic_base_coverage_2031_pct-->% |
| Bull | four-year pace, 47.1<!--n:ic_bull_market_cagr_pct-->% | twelve-month high, 78.6<!--n:ic_bull_share_pct-->% | highest month, 5.49<!--n:ic_bull_take_bp--> bp | yes | 277.5<!--n:ic_bull_coverage_2031_pct-->% |

The twelve months for the share are 2025-11 to 2026-10; the months for the take are the full months after the fee switch (2026-02-23), 2026-03 to 2026-10. The sensitivity moves one input of the base case at a time to its bear and bull value; for the price, to its 365-day high ($5.89<!--n:ic_price_365d_high_usd-->) and low ($0.96<!--n:ic_price_365d_low_usd-->). The anchors were chosen after the annual volumes in section 2, the monthly shares and the monthly take rates were computed (`PREREG-ADDENDUM.md`, 2026-11-14 entries). The bull case at the three-year pace instead would reach 136<!--n:ic_bull3y_vs_required_pct-->% of the revenue the price would assume (29.3<!--n:ic_bull3y_rev_multiple_x-->× today's); it counts some of Intents' share gains twice, because the whole peer set grows and Intents' share rises too. Coverage holds the price flat ($3.67<!--n:price_usd-->), as G_req does, and is what captured revenue would pay for: not all of it is bought-back NEAR, and none is burned.

## 5. Peer valuation

Market cap ÷ fees over the 365 days to 2026-11-04 (DefiLlama): NEAR on Intents' gross fees 89.2<!--n:ic_near_mcap_to_intents_fees_x-->×, THORChain (RUNE) 9.8<!--n:ic_peer_thorchain_mcap_to_fees_x-->×, Chainflip (FLIP) 1.8<!--n:ic_peer_chainflip_mcap_to_fees_x-->×; NEAR on captured revenue at the 90-day rate 245<!--n:ic_near_mcap_to_rev_90d_ann_x-->×. Maya's token (CACAO) is not listed on CoinGecko, so Maya is left out. NEAR's market cap prices the whole L1, and most of the peers' gross fees do not reach their tokens (DefiLlama counts as RUNE holders' revenue only the share of swap fees burned as RUNE): the comparison is context, not a valuation, and it is not on the basis of the multiples in section 1.

## 6. Staking float

The NEAR in staking pools (`data/raw/rpc/pool_endpoints_archival.json`, delegators' staked plus unstaked balances) at the two ends of H1a's window, against total supply at the same blocks (`data/raw/rpc/epoch_issuance.json`): 633.1<!--n:ic_staked_start_m-->M (48.6<!--n:ic_staked_share_start_pct-->%) and 592.8<!--n:ic_staked_end_m-->M (45.2<!--n:ic_staked_share_end_pct-->%). The NEAR outside the pools, not all of it liquid, grew by 48.2<!--n:ic_float_change_90d_m-->M, 6.1<!--n:ic_float_change_vs_net_supply_x-->× the net supply increase.

## 7. The Monte Carlo and the measured history

`pipeline/model.py`, whose main run is unchanged since its forecasts were dated (2026-11-13 23:50 UTC entry of the addendum): 10000<!--n:fwd_paths_n--> paths of 60<!--n:fwd_months_n--> months drawing the 11<!--n:fwd_boot_months_n--> monthly (volume, price) changes as pairs, price drift removed, take held at 4.13<!--n:fwd_take_bp--> bp. Full coverage by 2031-11-04 in 31.8<!--n:fwd_p_cov_ge100_2031_pct-->% of paths. The robustness check added on 2026-11-14, a stationary block bootstrap with a mean block of 3<!--n:fwd_block_mean_months--> months on its own seed, gives 25.6<!--n:fwd_block_p_cov_ge100_2031_pct-->% (median 37.8<!--n:fwd_block_cov_2031_p50_pct-->%). The main run's volume drift comes from one pair, 2026-08 to 2026-09, which spans DefiLlama's 2026-09-01 counting change; the run without that pair (same seed, price drift removed over the other ten) has volume changing by -4.5<!--n:fwd_exsep_vol_monthly_mean_pct-->% a month, a 2031 median of 1.5<!--n:fwd_exsep_cov_2031_p50_pct-->%, full coverage in 3.3<!--n:fwd_exsep_p_cov_ge100_2031_pct-->% of paths and 25% by 2027-11 in 19.4<!--n:fwd_exsep_p_cov_ge25_2027_pct-->%. The measured history is P3's quantity (revenue over 90 days ÷ the USD value of net new supply, priced daily) every 7 days back from 2026-11-04, to 2026-02-04, the first date with 90 days of prices: 11.8<!--n:ic_cov_hist_first_pct-->% then, 17.8<!--n:p3_quantity_90d_asof_pct-->% now, 40<!--n:ic_cov_hist_points_n--> points (series `cov_hist`).

## 8. Signposts

Today as a share of the line that would favour the upside: coverage against P3's and M1's 25%, 71<!--n:ic_sp_coverage_pct-->%; 90-day revenue against P2's $6M, 81<!--n:ic_sp_revenue_pct-->%; 365-day share against P1's 55%, 113<!--n:ic_sp_share_pct-->%; market growth against G_req, 40<!--n:ic_sp_market_pct-->%; take against what the price would need at the market's last-year pace and Intents' twelve-month-high share, 11<!--n:ic_sp_take_pct-->%; H1a's pass line (0.5×) against today's 6.56<!--n:h1a_ratio_as_written_x-->×, 8<!--n:ic_sp_staking_pct-->%.

## What this does not do

It does not value the L1, forecast NEAR's price, weight the scenarios, or model a new fee stream, a partner change or a regime the data have not seen. It does not compare NEAR with other fee-switch or buyback tokens, which would need hand-picked external data.
