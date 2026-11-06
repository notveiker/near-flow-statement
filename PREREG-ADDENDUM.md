# PREREG addendum (post-freeze, dated)

Entries here were written **after** `prereg-freeze`. They never change a hypothesis, threshold or probability in `PREREG.md`. They only disclose method choices and report results.

## 2026-11-05: method disclosures

1. **Liquid-staking contracts are excluded from the pool set.** `meta-pool.near` and `linear-protocol.near` stake through `*.poolv1.near` pools, so including them would double count. PREREG said the list would be "committed in `sql/`". The list is empty, and the reason is in the header of `sql/staking_flows_daily.sql`.
2. **Staking flows come from `account_changes`, not call arguments.** `unstake_all` and `withdraw_all` carry no amount, so parsing call arguments would undercount. Instead, each pool's balance (staked + non-staked) is differenced by `update_reason`:
   - `validator_accounts_update` is counted as rewards.
   - `receipt_processing` is counted as delegator flows.

## 2026-11-05: first result, H1a

H1a predicted that net staking outflow over 2026-08-07 → 2026-11-04 would be below 50% of staking rewards, with prior probability 0.70. **It fails.**

| Measure | Value |
|---|---|
| Rewards credited to pools | 7.04 M NEAR |
| Delegator inflow into pools | 188.0 M NEAR |
| Delegator outflow from pools | 235.3 M NEAR |
| Net outflow (daily flows) | 47.3 M NEAR, **6.7x rewards** |
| Pool totals, end of day | 625.1 M NEAR (2026-08-06) → 592.0 M NEAR (2026-11-04), **−33.1 M** |
| Unexplained residual between the two measures | 7.1 M NEAR (1.1% of pool total), under investigation |

Under either measure, stakers withdrew far more than they earned over the window. This was a price-rally window: NEAR went from about $1.9 to a $5.89 high and then $3.7.

Next steps, all reported here:
- Who withdrew: concentration by delegator.
- How much was liquid-staking rebalancing.
- Where withdrawn NEAR went: the exchange-flow tests H1b and H1c.

## 2026-11-05: exchange labelling feasibility

- **No labels from Nearblocks.** Its account API returns no labels.
- **The big receivers are anonymous.** 7 days of native-NEAR transfers (`sql/spike_top_receivers_7d.sql`, ~16.6 GB) show most of the top-100 receivers are 64-hex implicit accounts. Only a few are named (for example `binancecold3.near`).
- **So H1b and H1c will very likely be reported as ranges** under PREREG's labelled-coverage rule.
- **Planned method, disclosed before running:** cluster exchange deposit addresses (accounts that receive from many users and sweep to a single account), plus a committed list of named exchange accounts.

## 2026-11-05: corrections and scope notes, written before the forward-test window opens (2026-11-06 00:00 UTC)

1. **Correction to a pre-freeze observation.** PREREG's table says the buyback wallet balance is 68.5% of the NEAR implied by DefiLlama's holders revenue. That compares one wallet with a revenue series measured across three: DefiLlama counts NEAR arriving at `fefundsadmin.sputnik-dao.near`, `1csfundsadmin.sputnik-dao.near` and `buybacks.multisignature.near` ([adapter source](https://github.com/DefiLlama/dimension-adapters/blob/master/fees/near-intents/index.ts)). Over 2026-10-06 → 11-04, `fefundsadmin` received 30.7 <!--n:revwallets_frontend_share_pct-->% of those inflows. Our own three-wallet measure matches DefiLlama at 100.9 <!--n:revwallets_vs_llama_rev_pct-->% (`sql/revenue_wallet_inflows.sql`). The gap is therefore mostly in `fefundsadmin`, not missing. F1 concerns only the buyback wallet's balance and is unchanged.
2. **F3 sensitivity, disclosed in advance.** DefiLlama "revenue" is NEAR delivered to the wallets, not fees accrued. In the 30 days to 2026-11-04 no day had zero inflow, and 8-day sums ranged from about $422K to $757K. F3 will be scored exactly as written.
3. **H1b scope.** H1b counts only labelled centralized-exchange accounts. NEAR Intents' 1Click is a non-custodial route out of NEAR: over the same 30 days it swapped out of NEAR 24.0 <!--n:explorer_out_of_near_usd_m--> USD M and into NEAR 14.6 <!--n:explorer_into_near_usd_m--> USD M. We will report this next to H1b, never inside it. The test and its thresholds are unchanged. Details: `docs/intents-fee-flows.md`.
