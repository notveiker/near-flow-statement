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

## 2026-11-11 03:10 UTC: dashboard and report added; what we already knew about the history sample

Post-freeze. It changes no hypothesis, threshold, probability or the rating rule, and the rule's output, Hold, stands.

1. **`dashboard/index.html` and `REPORT.md` are exploratory presentation of data already in the repository.** Both are built only from committed files (`make dashboard`, `make check`). Their scenario explorer is arithmetic on measured baselines and makes no forecast.
2. **We saw the independent daily series before the sample returned any block.** `data/raw/nearblocks/charts.json` was committed before the history sample was frozen. It shows transactions a day, active accounts a day and fees burnt a day well below their 2024 peaks. The sample's hypotheses U1, U2, U4 and U5 (`docs/history-sample-prereg.md`) are therefore likely to fail, and we keep them as registered and report each verdict as it falls. The dashboard lists the base-layer decline in its risks section for the same reason.
3. **Market and ecosystem snapshots** (`data/raw/market/`, `data/raw/ecosystem/`, `data/raw/governance/`) were pulled on 2026-11-10 and 2026-11-11, are hashed in `data/MANIFEST.json`, and feed no pre-registered test.

## 2026-11-11 06:20 UTC: node-census products and other collectors added after the freeze

Post-freeze and exploratory. They change no hypothesis, threshold, probability or the rating rule, and the rule's output, Hold, stands. None of them feeds U1-U5, H1a-H1c or F1-F4.

1. **Block-by-block census from our own node** (`pipeline/near_node_archive.py`, summaries in `pipeline/census_*.py`). It reads every transaction and receipt from the node as it syncs, so it starts at block 223,963,000 and runs forward; it cannot look back. Derived files: `data/derived/census_usage.json`, `census_hourly.json`, `census_metrics.json`, `hub_trail.json`. The report quotes `census_metrics.json` through census markers (an HTML comment starting `c:`) that `make check` verifies.
2. **Hub trail** (`docs/hub-trail-method.md`) reported a tier-4 side result only. With the census window available it labelled one of 80 unlabelled receivers, below the method's own drop rule of 10, so H1b stays inconclusive. A tier-4 label may enter the primary measure only if the repository owner accepts it by a dated addendum.
3. **Chain-measured Intents flows.** Deposits (`mt_mint`), withdrawals (`mt_burn`), public swap legs and relayer counts come from the logs and signers of receipts on `intents.near`. A window of hours is short, the sign of net deposits over it is not a trend, and unlisted token ids (NFTs, memecoins) are left out because they have no price in the 1Click list.
4. **Contract holdings, builder downloads, peer revenue to holders, third-party facts** (`pipeline/fetch_intents_holdings.py`, `fetch_builder_activity.py`, `fetch_peers.py`, `fetch_web_facts.py`). Each fetched fact keeps its source URL and an exact quote re-checked by `fetch_web_facts verify`.
5. **Exploratory counts on the sampled clusters** (`pipeline/sample_extras.py`): `intents_executed` events, deposits, withdrawals and Chain Signatures requests per quarter. They use the same frozen clusters and design as U1-U5 and are labelled exploratory wherever they appear.
6. **Source notes.** `archival-rpc.mainnet.near.org` is deprecated and answers 429 to every request, so archival reads go to FastNEAR's archival host. Archival `validators` calls for old epochs return "Unknown epoch", so no monthly validator series was possible and none is shown.

## 2026-11-11 06:30 UTC: preliminary history-sample rows; prop extras; second sampler IP

Post-freeze. Changes no hypothesis, threshold, probability or the rating rule.

1. **Preliminary sample rows.** 43 sealed clusters (of 268 under the amended round caps) were copied from the collector and scored offline. `data/derived/history_results.json` and `data/derived/sample_extras.jsonl` are stamped `preliminary: true`. Provisional verdicts: U1, U2, U4, U5 fail; U3 is not scorable yet (2025Q1 sample had no intents receipts). The Intents receipts series is rising; base-layer series are not. Final verdicts wait for the stopping rule.
2. **Prop extras.** `pipeline/fetch_prop_extras.py` pulls DefiLlama fee and DEX hierarchy on NEAR, liquid-staking TVL and public GitHub metadata into `data/raw/prop/`. None of it feeds a pre-registered test.
3. **Second sampler.** A second NEARDATA collector runs on a different provider (one polite IP per provider) against the same frozen plan, writing to its own root. Clusters are merged by id when sealed.

## 2026-11-11 06:35 UTC: Bitwise NRR ETF assets observed; sampler rate-limit floor lowered

Post-freeze. Changes no hypothesis, threshold, probability or the rating rule.

1. **ETF assets.** `data/raw/prop/etf_nrr.json` records a point-in-time reading of the SoSoValue NEAR spot ETF dashboard (ticker NRR): about $55.9M net assets and about $80.5M cumulative net inflow on 2026-11-11. The page is dynamic; the file states that.
2. **Sampler polite floor.** `Bucket.slow_down` previously could not go below 20 requests a minute, which sped up runs that had been started slower than that after the first 429. The floor is now 5/min so a polite collector can actually back off.

## 2026-11-11 20:10 UTC: structural prop research note (exploratory)

Post-freeze. Changes no hypothesis, threshold, probability or the rating rule.

1. **`docs/structural-thesis.md`** synthesises four research tracks (capture stack, Confidential Intents, capital markets, competitive structure) from primary sources and from numbers already in this repository. It is labelled exploratory wherever it appears and feeds no pre-registered test.
2. Working notes sit under `research_notes/NEAR Intents structural thesis/`; the judge-facing copy is the docs file.
