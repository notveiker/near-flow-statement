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

Under either measure, stakers withdrew far more than they earned over the window. This was a price-rally window: NEAR went from about $1.70 (low $1.59 on 08-19) to a $5.89 high on 10-12 and $3.83 at window end (CoinGecko daily).

Next steps, all reported here:
- Who withdrew: concentration by delegator.
- How much was liquid-staking rebalancing.
- Where withdrawn NEAR went: the exchange-flow tests H1b and H1c.

## 2026-11-05: exchange labelling feasibility

- **No labels from Nearblocks.** Its account API returns no labels.
- **The big receivers are anonymous.** 7 days of native-NEAR transfers (`sql/spike_top_receivers_7d.sql`, ~16.6 GB) show most of the top-100 receivers are 64-hex implicit accounts. Only a few are named (for example `binancecold3.near`).
- **So H1b and H1c will very likely be reported as ranges** under PREREG's labelled-coverage rule.
- **Planned method, disclosed before running:** cluster exchange deposit addresses (accounts that receive from many users and sweep to a single account), plus a committed list of named exchange accounts.

## 2026-11-06 01:11 UTC: corrections and scope notes, written after the forward-test window opened (see the 2026-11-06 correction below)

1. **Correction to a pre-freeze observation.** PREREG's table says the buyback wallet balance is 68.5% of the NEAR implied by DefiLlama's holders revenue. That compares one wallet with a revenue series measured across three: DefiLlama counts NEAR arriving at `fefundsadmin.sputnik-dao.near`, `1csfundsadmin.sputnik-dao.near` and `buybacks.multisignature.near` ([adapter source](https://github.com/DefiLlama/dimension-adapters/blob/master/fees/near-intents/index.ts)). Over 2026-10-06 → 11-04, `fefundsadmin` received 30.7 <!--n:revwallets_frontend_share_pct-->% of those inflows. Our own three-wallet measure matches DefiLlama at 100.9 <!--n:revwallets_vs_llama_rev_pct-->% (`sql/revenue_wallet_inflows.sql`). The gap is therefore mostly in `fefundsadmin`, not missing. As a rough check: 2.187M NEAR / 0.685 ≈ 3.19M NEAR implied, a gap of about 1.0M. A 30.7% front-end share of 3.19M is about 0.98M. That share was measured over 30 days, not since the switch, so this is consistency, not proof. F1 concerns only the buyback wallet's balance and is unchanged.
2. **F3 sensitivity, disclosed in advance.** DefiLlama "revenue" is NEAR delivered to the wallets, not fees accrued. In the 30 days to 2026-11-04 no day had zero inflow, and 8-day sums ranged from about $417K to $757K on the DefiLlama series F3 is scored on. F3 will be scored exactly as written.
3. **H1b scope.** H1b counts only labelled centralized-exchange accounts. NEAR Intents' 1Click is a non-custodial route out of NEAR: over the same 30 days it swapped out of NEAR 24.0 <!--n:explorer_out_of_near_usd_m--> USD M and into NEAR 14.6 <!--n:explorer_into_near_usd_m--> USD M. We will report this next to H1b, never inside it. The test and its thresholds are unchanged. Details: `docs/intents-fee-flows.md`.

## 2026-11-06: correction to the timing of the entry above

The entry above was headed "2026-11-05 … written before the forward-test window opens (2026-11-06 00:00 UTC)". That was wrong. `git log` shows it was committed at 2026-11-06 01:11:49 UTC (`e202d78`) and edited at 01:14:25 UTC (`e0edac8`), and the revenue-wallet data it cites was fetched at 01:08:10 UTC (`data/MANIFEST.json`). The date was the author's local date (UTC−6). It was therefore written about 71 minutes after the window opened. Its content changes no test: F3 is scored exactly as written, and H1b's scope note only adds context beside the test. Two numbers in it are also corrected in place: the F3 8-day range ($422K quoted the wallet series; DefiLlama's, which F3 uses, gives $417.3K–$756.8K) and the price path in the H1a entry ($1.70 at the window start, not $1.9). An outside review of a fresh clone found all three.


## 2026-11-06 23:15 UTC: H1b/H1c method, fixed before any H1b/H1c flow query runs

Committed together with the exchange-account list (`data/raw/labels/exchange_accounts.json`) and the four queries (`sql/h1b_*.sql`). No H1b/H1c query had run for real when this was committed; only dry runs (byte estimates) had. The BigQuery job IDs and creation times of the real runs will be added below, so the order can be checked against this commit.

**Labelled exchange accounts (tier 1).** 40 accounts across 10 exchanges, each with a cited source and each confirmed to exist on chain:
- 19 Binance accounts from Binance's own proof-of-reserves address endpoint, filtered to the NEAR network (high confidence). Snapshot: `data/raw/labels/binance_por_address_2026-11-06.json`.
- 21 accounts of Bitget, Gate, KuCoin, Bitfinex, MEXC, SwissBorg, Flipster, Gate.US and Bitlo from DefiLlama's exchange-transparency adapters at a pinned commit (medium confidence).
- No citable NEAR address was found for OKX, HTX, Bybit, Crypto.com, Kraken, Coinbase, Upbit or Bithumb. Nothing is labelled from its name alone.

**Clustering (tiers 2-3), the method disclosed on 2026-11-05.** Rules are fixed in the SQL headers:
- Tier 2, deposit-like accounts that sweep to a tier-1 account: inflow ≥ 1 NEAR; outflow 0.9-1.5× inflow; the top destination gets ≥ 90% of the outflow; at most 3 destinations; not itself tier 1.
- Tier 3, unlabelled hubs: fan-in ≥ 25 deposit-like accounts and ≥ 80% of the hub's outflow to tier-1 accounts, plus the deposit-like accounts feeding them.
- "Receive from many users" is applied to the hub (fan-in), not to each deposit address, because exchanges give each user a separate deposit address.
- Tier 1 alone is reported as the strictly cited result. Tiers 2-3 are reported beside it, never merged silently.

**How the frozen definitions are implemented (disclosed departures in wording; no test, threshold or probability changes).**
1. Net exchange inflow is measured at the boundary of the labelled set: transfers into the set from outside, minus transfers out of it. Sweeps and transfers inside the set, including exchange-to-exchange, cancel.
2. Native NEAR = `TRANSFER` actions. NEAR attached to function calls is reported separately (it includes exchanges restaking). Wrapping NEAR into wNEAR is a change of form, not an exit, and is netted out.
3. wNEAR (`wrap.near`) emits legacy `Transfer … from … to` log lines, not EVENT_JSON; the wNEAR query parses those. The cheaper `ft_events` version is used only if a one-day check shows it records the same wrap.near transfers as the logs.
4. **Labelled coverage, primary measure:** the count share of the top-100 native-NEAR receivers by inflow that are labelled exchange accounts in tiers 1-3. Accounts with a sourced non-exchange identity (staking pools, `intents.near`, `wrap.near`, named DAOs) count as unlabelled under this primary measure, which is the conservative reading. Reported beside it, not instead of it: tier 1 alone, the inflow-weighted share, and the 100% bound with those sourced non-exchange accounts excluded.
5. **The 100% bound** treats every unlabelled top-100 receiver as an exchange account and measures the net boundary inflow of that enlarged set. Flows to unlabelled accounts outside the top 100 are in neither bound.
6. **Reading of the range rule, recorded before results.** PREREG says that below 50% coverage "a test passes only if it passes under both bounds. Otherwise it is inconclusive." Read as written, a low-coverage H1b can come out pass or inconclusive, never fail. So the rating rule's Avoid branch, which needs H1b to fail, cannot be reached in that case. H1c follows the same rule, with identified buying = the change in `buybacks.multisignature.near`'s balance between the window's endpoint blocks.
7. Exchange labels are snapshots dated 2026-11-06. Addresses retired before then may be missing.

**Budget.** Dry runs: sweep preview (`h1b_c`) 24.0 GB, native flows (`h1b_a`) 262.4 GB, wNEAR 117.0 GB from logs or 8.4 GB from `ft_events`. Planned total about 295 GB (about $1.70 on demand). The H1b queries run only when named explicitly, e.g. `NFS_BQ_MAX_GB=270 python3 -m pipeline.bq_run h1b_a`; a plain `make bq` skips them.
