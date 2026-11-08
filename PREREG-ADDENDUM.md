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


## 2026-11-06 23:11 UTC: H1b/H1c method, fixed before any H1b/H1c flow query runs

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

## 2026-11-06 23:23 UTC: H1b and H1c results (both inconclusive)

Run exactly as fixed in the 23:11 UTC entry. Jobs, all created after that commit: `bqjob_r140d347f6f05de25_000001a1b321c86a_1` (sweep preview, 23:11:38Z, 23.9 GB), `bqjob_r3eccfeb9d7486d84_000001a1b322482a_1` (native flows, 23:12:11Z, 262.4 GB) and `bqjob_r58d81aa5f1fb52b1_000001a1b3297c9d_1` (wNEAR, 23:20:04Z, 117.0 GB, run on the query committed in `b1861cd` at 23:19:42Z). Numbers are recomputed by `pipeline/h1b.py` from the committed outputs.

**Coverage.** 20.0 <!--n:h1b_coverage_count_pct-->% of the top-100 native-NEAR receivers are labelled exchange accounts (tiers 1-3), below PREREG's 50%. Side measures: tier 1 alone 10.0 <!--n:h1b_coverage_tier1_count_pct-->%; inflow-weighted 24.6 <!--n:h1b_coverage_inflow_pct-->%. So both tests are ranges and pass only under both bounds.

| Net exchange inflow, 2026-08-07 → 11-04 (native + wNEAR) | NEAR, M |
|---|---|
| Lower bound (unlabelled = 0% exchange-bound) | 4.42 <!--n:h1b_net_inflow_lower_m--> |
| Upper bound (unlabelled top-100 = 100% exchange-bound) | 152.45 <!--n:h1b_net_inflow_upper_m--> |
| Side: tier 1 (cited list) only | 3.31 <!--n:h1b_net_inflow_tier1_m--> |
| Side: upper bound with sourced non-exchange accounts excluded (larger, because once `intents.near` and a DAO leave the enlarged set, their payouts into it count as boundary inflow) | 190.71 <!--n:h1b_net_inflow_upper_ex_nonexchange_m--> |

- **H1b (net exchange inflow < gross issuance): inconclusive.** The lower bound is below any plausible 90-day gross issuance (about 8M NEAR); the upper bound is far above it.
- **H1c (identified buying ÷ net exchange inflow ≥ 25%): inconclusive.** Identified buying, the buyback wallet's balance increase between the endpoint blocks, is 1.48 <!--n:h1c_identified_buying_m-->M NEAR: 33.48 <!--n:h1c_ratio_lower_pct-->% of the lower bound, 0.97 <!--n:h1c_ratio_upper_pct-->% of the upper.
- Under PREREG's decision rule, an inconclusive H1b neither rejects nor supports the supply-side leg. Under the rating rule, Buy needs H1b to pass and Avoid needs it to fail, so the rule's output is Hold whatever G_obs and G_req turn out to be.
- **The binding gap is labelling, not data.** 80 of the top 100 receivers carry no citable label. No citable NEAR address was found for OKX, Coinbase, Kraken, Bybit, HTX, Crypto.com, Upbit or Bithumb.

## 2026-11-06 23:49 UTC: H1a scored as written; the 7.1M residual explained; rating-rule inputs and the rule's output

Written after the forward-test window opened. It changes no test; it finishes H1a exactly as PREREG defines it and computes the frozen rating rule. Numbers are recomputed by `pipeline/h1a.py` from `data/raw/rpc/`.

1. **Gross issuance from epoch-boundary headers (PREREG's primary method; the fallback was not needed).** 297 <!--n:h1a_epochs_in_window--> epochs start inside 2026-08-07 → 11-04. No header field reports the amount minted, so each epoch's mint is read from the identity that holds to the yoctoNEAR on every block: an epoch-start block's `total_supply` equals the previous block's, plus the mint, minus the `balance_burnt` of its chunks. Gross minted: 8.0098 <!--n:h1a_gross_issuance_90d_m-->M NEAR. Net supply change: 7.933 <!--n:h1a_net_supply_change_90d_m-->M. Burn: 76.84 <!--n:h1a_burn_90d_k-->K. `python3 -m pipeline.fetch_issuance --verify N` re-reads random epochs from archival RPC.
2. **H1a as written fails.** Staking rewards (90% of gross) are 7.2088 <!--n:h1a_staking_rewards_90d_m-->M NEAR. Net staking outflow is **6.56 <!--n:h1a_ratio_as_written_x-->×** that on daily flows and 6.56 <!--n:h1a_ratio_endpoint_archival_x-->× on full archival pool state; passing needed under 0.5×. This confirms the 2026-11-05 result (6.71× against pool-credited rewards).
3. **The 7.1M residual is explained.** `sql/staking_pool_totals_endpoints.sql` sums only pools whose balance changed that day. `flipside.pool.near` held 7.1 <!--n:h1a_residual_flipside_m-->M NEAR that did not change on 08-06, so the 08-06 total left it out, while the daily flows counted its withdrawal inside the window. Summed over all 550 pools at both endpoint blocks, archival state agrees with the flows to within 12.1K NEAR (0.03%; the residual is -12.1 <!--n:h1a_residual_left_k-->K). The flow figure stands; the repo's endpoint figure understated the outflow.
4. **Name-filter sensitivity (post hoc; the test is not redefined).** `lst-pool.near` is the only validator the `*.poolv1.near` / `*.pool.near` filter misses (71 sampled validator sets). With its +4.26M net inflow added, the ratio is 5.96 <!--n:h1a_ratio_with_lst_pool_x-->×. H1a still fails.
5. **Rating-rule inputs.**
   - **G_req = 33.2 <!--n:rating_g_req_pct-->% a year:** the growth needed for 90-day captured revenue ($4.84 <!--n:rating_r90_usd_m-->M, DefiLlama `dailyRevenue`, 2026-08-07..11-04) to equal the USD value of 90 days of net new supply by 2031-11-04. It assumes HSP-029's ramp (cap 2.5% falling linearly to 1.6% over 24 months), activated one quarter after the timelock ends on 2026-11-16, and a constant $3.67 price (constants in `data/raw/rpc/rating_assumptions.json`). Without HSP-029 it would be 46.8 <!--n:rating_g_req_no_hsp029_pct-->%.
   - **G_obs = 619.0 <!--n:rating_g_obs_pct-->% a year:** captured revenue over the last 180 days vs the 180 before, annualized, with pre-switch revenue counted as DefiLlama labels it. In NEAR terms it is 71.4 <!--n:rating_g_obs_near_pct-->%; most of the USD growth is the NEAR price.
   - **The rule's output: Hold.** Buy needs H1b to pass and Avoid needs H1b to fail. H1b is inconclusive (2026-11-06 results entry), so the rule outputs Hold. Had H1b passed it would have been Buy, since G_obs ≥ G_req.
6. **HSP-029's timelock (2026-11-16) resolves after the deadline.** G_req assumes the ramp, as PREREG specifies. We state it as a pending resolver and do not predict it.
7. **Forward tests.** `pipeline/score_forward.py` will score F1-F4 exactly as PREREG words them and refuses to run before 2026-11-14 00:00 UTC. It was written on 2026-11-06, after the window opened. Its dry run read no day inside 11-06..11-13 for F2-F4 and only the window-opening block for F1. Any missing day or failed fetch is "not scorable". `make test` runs its tests.

## 2026-11-07 00:21 UTC: exploratory headline chosen after the freeze and after all three flow results

The thesis (`THESIS.md`) leads with an exhibit that was not pre-registered: the value-capture "ladder", which splits the NEAR arriving in NEAR's revenue wallets into NEAR traceable to public fee collectors and NEAR released from the Confidential Intents escrow, each as a share of net issuance. The author chose it on 2026-11-07, which is:
- after the freeze (tag `prereg-freeze`, commit `413d776`, 2026-11-05 22:53:29 UTC);
- after H1a's first result (2026-11-05) and its as-written result (2026-11-06 23:49 UTC);
- after H1b and H1c came out inconclusive (2026-11-06 23:23 UTC).

It changes no hypothesis, threshold, probability or the rating rule. The rule's output, Hold, stands, and the ladder does not feed it. `THESIS.md` reports the pre-registered scorecard in its first paragraph, before any exploratory result, and labels the ladder exploratory wherever it appears. The escrow dataset the ladder rests on was committed on 2026-11-06 (`51e396b`).

## 2026-11-08 02:03 UTC: corrections to this record

Written after an independent review of the repository's own history and a re-read of the external sources it cites (`docs/sources-checked.md`). It changes no hypothesis, threshold, probability or rating-rule output. Every time below is UTC and comes from `git log` or `data/MANIFEST.json`.

1. **The ladder was built before two of the three pre-registered results were committed.** The 2026-11-07 00:21 UTC entry says the author chose the ladder on 2026-11-07, "after H1b and H1c came out inconclusive". The history does not support that. The ladder's code and metrics (`escrow_ladder` in `pipeline/compute.py`; the `ladder_*` metrics) and its escrow dataset were first committed in `51e396b` at 2026-11-06 23:19:20, 4 minutes before the H1b and H1c results (`1c032a0`, 23:23:40) and 30 minutes before H1a as written (`9ee9082`, 23:49:26). The relabelling of `51e8f94d…7cbe` as the Confidential Intents escrow (`62a6d6c`, 2026-11-06 14:54:48) is earlier still. What happened at 2026-11-07 00:21:24 (`3bf67c3`) is that `THESIS.md` was first committed with the ladder as its headline. The ladder stays exploratory and does not feed the rating rule, but it was developed alongside the pre-registered tests, not after them.
2. **Five commits changed existing lines of this file.** It is described as append-only. In fact `e0edac8` (2026-11-06 01:14:25), `8e59a3f` (23:02:31), `5188f5a` (23:11:07), `01187d5` (23:49:38) and `15f2859` (23:53:47) each replaced lines of earlier entries, nine lines in all: four entry headings (corrected to the date or time of their commit) and five body lines (the 68.5<!--n:buyback_wallet_vs_implied_pct-->% check, the H1a price path, the F3 range, the sign of the H1a residual, and the explanation on the 190.71<!--n:h1b_net_inflow_upper_ex_nonexchange_m-->M row). Only the price path and the F3 range were disclosed, in the 2026-11-06 timing correction above. From this entry on, the text above it is pinned by SHA-256 in `tests/test_integrity.py`, so a later edit of it fails the tests. A correction is a new entry.
3. **Corrections made outside this file.** `62a6d6c` relabelled the escrow account (item 1). `12948a4` (2026-11-07 03:26:34) reversed an earlier statement that SwapKit's fees were invisible on this ledger: partner fees are paid on chain, to implicit accounts (per-swap sample). `38e1c4c` (03:28:50) counted each collector-B payment once; it had been counted twice. `a2414f8` (21:31:39) corrected three statements in `THESIS.md` and `docs/intents-fee-flows.md`: the funding hop of an escrow delivery is traced for every delivery only from 2026-10-06 (earlier deliveries are attributed from samples); partner fees were about ten times NEAR's explicit fee in the last block, not in every block; and an outflow total for the buyback wallet that is not in the committed data was marked as such. On 2026-11-08 the summary sentences in `README.md`, `THESIS.md`, `docs/supply-side.md` and the dashboard that said 20.0<!--n:h1b_coverage_count_pct-->% of the top-100 receivers "carry a citable exchange label" were corrected: 20.0<!--n:h1b_coverage_count_pct-->% is tiers 1 to 3, and only the 10.0<!--n:h1b_coverage_tier1_count_pct-->% in tier 1 carry a cited label (this file's 2026-11-06 23:23 UTC wording was right).
4. **Timing evidence for H1a is thinner than for H1b and H1c.** The freeze (`413d776`) is 2026-11-05 22:53:29. The first BigQuery result the manifest records, `bq/staking_flows_daily.json`, is stamped 22:55:37 (the pool-totals endpoints 22:56:05), and the first commit holding BigQuery code or results is `950e221` at 22:57:05. BigQuery job IDs, which embed their creation time, are recorded for the H1b and H1c runs (2026-11-06 23:23 UTC entry) and for the October escrow funding scan, not for the H1a queries. "Frozen before any BigQuery flow query ran" therefore rests on commit and manifest times that the author's machine wrote, and nothing external attests them.
5. **Earlier work.** `docs/supply-side.md` and `THESIS.md` refer to an earlier analysis of 14 accounts that reach one unlabelled hub. This repository does not record when it was done. The committed data derived from it (`data/raw/unstakers/`) is stamped 2026-11-06 23:50:01, after the freeze, and `PREREG.md` says that at the freeze no query on staking-pool flows had been run. The repository cannot show whether that analysis preceded the freeze or informed H1a's prior of 0.70. It is labelled exploratory, and its arithmetic is now computed from the committed file (the `unstakers_a14_*` metrics in `data/metrics.json`).
6. **Not anchored.** `PREREG.md` says its hash "is published on NEAR mainnet (see `docs/ANCHOR.md` once anchored)". As of this entry it has not been anchored, and there is no `docs/ANCHOR.md`.
7. **Implementation readings that this record had not stated.** `pipeline/h1a.py` and `pipeline/h1b.py` apply three rules that go beyond the words of `PREREG.md`. None changes a result, because the data do not reach the branch it decides. (a) H1a as written passes only if both measures of net staking outflow, the daily flows and the archival pool state, are under 50% of staking rewards (strictly); they are 6.56<!--n:h1a_ratio_as_written_x-->× and 6.56<!--n:h1a_ratio_endpoint_archival_x-->×. (b) At labelled coverage of 50% or more, H1b and H1c are decided on the lower bound alone (tiers 1 to 3, the unlabelled share taken as 0% exchange-bound). `PREREG.md` describes only the below-50% case, and coverage is 20.0<!--n:h1b_coverage_count_pct-->%. (c) H1c passes under a bound only if that bound's net exchange inflow is positive and identified buying is at least 25% of it. Both bounds are positive (4.42<!--n:h1b_net_inflow_lower_m-->M and 152.45<!--n:h1b_net_inflow_upper_m-->M NEAR). `tests/test_h1a.py`, `tests/test_h1b.py` and `tests/test_prereg_spec.py` now pin these rules and compare the constants in the code with the frozen text.
8. **Corrections after re-reading the sources.** `docs/sources-checked.md` lists each statement, its source, the time it was read and a verdict. Four statements in this repository were stronger than their source or their evidence. (a) HSP-029: the 2026-11-06 23:49 UTC entry (items 5 and 6) treats the end of the on-chain timelock, 2026-11-16, as the one step still pending. That date is our sum of the on-chain proposal's voting start and its two periods; no published text gives it. The proposal text puts activation "one full quarter after ratification" without defining ratification, and says the issuance cap is a protocol parameter whose change "requires validator adoption through the standard upgrade process", a second step this record did not name. (b) `THESIS.md` and the dashboard called both candidate NEAR-side fee streams "documented". The 1Click terms say who would keep a Confidential Infrastructure Fee but state no rate, so that stream is a candidate, not a documented charge. (c) The 100.0<!--n:escrow_funded_exact_30d_pct-->% of single-use deliveries funded "by the escrow for the exact amount" tallies two columns of `data/raw/escrow/deliveries.csv` (`funder` and `exact_amount_flag`) over the window's single-use deliveries. That set does not depend on the columns (it follows from the committed BigQuery output), and a full re-read against the chain on 2026-11-08, committed as `data/raw/escrow/verify_all.json`, confirms the recorded funding transfer of each: all 1,051<!--n:escrow_recheck_funding_hops_n--> funding transfers pass, 909<!--n:escrow_recheck_window_funding_ok_n--> of them in the window, and 3,587<!--n:escrow_recheck_rows_ok_n--> of 3,597<!--n:escrow_recheck_rows_n--> delivery rows pass every check, the other 10<!--n:escrow_recheck_failed_n--> failing on block height alone (one to three blocks). The funding-scan SQL and the code that assigned the table's labels are not in this repository, and funding hops before 2026-10-06 are sampled. (d) `THESIS.md` and the dashboard stated as fact that DefiLlama counts both legs of an Intents swap. DefiLlama's adapter states no methodology; the halving is an inference, with the evidence in `docs/intents-fee-flows.md`.
