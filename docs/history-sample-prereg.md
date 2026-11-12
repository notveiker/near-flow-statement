# History sample: design and hypotheses, frozen before any sampled block is read

Frozen: 2026-11-11 (UTC), at the commit that adds this file. The only NEAR data read before the freeze is block timestamps, used to find quarter boundaries (see "Plan"). This file extends, and does not replace, [`PREREG.md`](../PREREG.md). The frozen rating rule in `PREREG.md` is untouched: it stays the scorecard, and this file is a separate, labelled, exploratory addendum. Nothing here can change that rating. It can only add evidence about whether the rule's inputs are moving the right way.

## Why a sample, and why this sample

The first-pass work looked at 30 and 90 days. That cannot say whether NEAR is growing, because a recent window has no past to compare with. The chain has about 214 million blocks. Reading all of them is not possible from one IP in the time available (NEARDATA gives us about 22 blocks a minute; a whole-chain pull would take about 18 years). A well-designed sample can answer the growth question with stated uncertainty, which is how institutional work handles populations too large to census.

## Design

- **Population.** Every final block from the first one NEARDATA serves (height 9,820,210, 2020-07-21) to the plan date.
- **Strata.** UTC calendar quarters. Weights are the stratum's share of chain time, taken from the boundary block timestamps in the plan.
- **Units.** Clusters of 100 contiguous blocks (about 1.7 minutes). Contiguity keeps transaction-to-receipt links and the `prev_hash` chain intact, so every cluster verifies on its own.
- **Allocation.** 18 clusters per quarter before 2025, 30 per quarter from 2025-Q1 (NEAR Intents and most of the activity we care about are recent). About 600 clusters, 60,000 blocks.
- **Draw.** Cluster starts are uniform at random within each stratum, without overlap. The seed is the hash of the final NEAR block at plan time, recorded in `plan.json`. We could not pick it in advance.
- **Order of collection.** Rounds: cluster 1 of every stratum, then cluster 2, and so on. If collection stops early, the sample is still balanced.
- **Integrity.** `plan.json` is frozen with a SHA-256; every sealed cluster has a SHA-256 manifest; `verify` re-hashes everything and checks the block hash chain inside each cluster and that each block lies inside its stratum.
- **Politeness.** One process, one IP, about 22 requests a minute, backs off on HTTP 429, identifies itself in the User-Agent. We do not add IPs to go faster.
- **Allocation is not tuned to the answer.** The recent-heavy allocation is set by where the activity is, and the weights correct for it.

## Estimators

For each quarter: the mean of each metric per block over clusters, multiplied by blocks per day (stratum height span over stratum time span) to give a per-day figure. Uncertainty is a cluster bootstrap within the quarter (2,000 resamples, fixed seed), reported as a 90% interval. Ratios between quarters use the same resamples, so intervals on ratios are honest about both ends. All estimates are of totals and rates; distinct-count metrics are reported per 100 blocks, never scaled up to a day.

## Metrics (all computed from the sampled blocks only)

| Metric | Definition |
|---|---|
| `tx_per_day` | Transactions per day |
| `ok_share` | Share of transactions whose outcome is success |
| `tx_per_day_ex_top` | `tx_per_day` after removing transactions sent to the single receiver account with the most transactions in that quarter's sample |
| `signers_per_100` | Distinct transaction signers per 100-block cluster |
| `burn_near_per_day` | NEAR burnt as transaction and receipt fees per day (`tokens_burnt`) |
| `intents_receipts_per_day` | Receipts executed on `intents.near` per day |
| `top_receiver_share` | Share of transactions sent to the most-used receiver account |

## Hypotheses

Each is directional and written so it can fail. "Pass" requires the stated ratio **and** that the 90% interval of the ratio excludes 1 in the stated direction. The prior is our probability before seeing any sampled block.

| ID | Hypothesis | Pass if | Prior |
|---|---|---|---|
| U1 | NEAR usage has grown | `tx_per_day` 2026-Q3 ÷ 2025-Q3 ≥ 1.5 | 0.60 |
| U2 | The growth is not one contract | `tx_per_day_ex_top` 2026-Q3 ÷ 2025-Q3 ≥ 1.25 and `top_receiver_share` in 2026-Q3 ≤ 2025-Q3 | 0.45 |
| U3 | Intents has become a real share of activity | `intents_receipts_per_day` 2026-Q3 ÷ 2025-Q1 ≥ 2 | 0.70 |
| U4 | More distinct users | `signers_per_100` 2026-Q3 ÷ 2025-Q3 ≥ 1.2 | 0.50 |
| U5 | Fee burn has grown | `burn_near_per_day` 2026-Q3 ÷ 2025-Q3 ≥ 1.25 | 0.50 |

**Decision rules**
- The usage record is worded as *supported by sampled history* only if **U1, U2 and U3** all pass. U2 is there so that a spam or single-contract spike cannot carry the thesis.
- If U2 fails, the thesis paragraph says activity growth is concentrated, and U1 is quoted only together with the ex-top figure.
- If U1 fails, the thesis paragraph says NEAR's usage has not grown over the sampled period. We do not move the comparison quarters afterwards.
- U4 and U5 are reported either way. U5 is always shown next to issuance: gas burn is small against the roughly 88,000 NEAR a day of net issuance, and we say so whatever the result.
- A counter-evidence table is always printed beside the results: burn as a share of issuance, top-receiver share, success share, and the quarters where each metric fell.

## Validation of the sampler itself

We hold a census (every block, from our own node) of a window of recent days. We draw the same kind of clusters from that census, 200 times, and report how often the 90% interval covers the census value for each metric. If coverage is below 80% for a metric, the metric's intervals are labelled "too narrow" in the report and we do not rely on them.

## Plan

`python3 -m pipeline.near_sample plan --root data/sample --per-stratum 18 --recent-from 2025-01-01 --recent-per 30`. The plan step reads only the block timestamps it needs to find quarter boundaries (about 100 requests). `plan.json` and `plan.sha256` are committed before any cluster is fetched.

## What would change our mind

- **Toward stronger evidence of growth:** U1, U2 and U3 pass, ratios well above their thresholds, and the ex-top series and signers rise together in the last four quarters.
- **Toward weaker evidence:** U2 fails, or `top_receiver_share` is rising, or usage is flat after 2025, or burn is a vanishing share of issuance with no upward trend.
- **Out of scope:** price, which this sample says nothing about.

## Post-freeze notes

- **2026-11-11, at plan time.** The plan's boundary timestamps show that block production sped up in 2025: about 76,000 blocks a day in 2025-Q1 and about 141,000 a day from 2025-Q3 (roughly 1.6 blocks a second), against about 70,000 to 110,000 a day before. A 100-block cluster is therefore about 1 minute of chain time recently and up to 1.5 minutes earlier, not the "about 1.7 minutes" written above. No design parameter changed. This is exactly why the estimators multiply per-block rates by each quarter's own blocks per day, and why comparisons across quarters are per day and not per block.
- **Plan.** `data/sample/plan.json`, SHA-256 `8786271ac0f5af7f2525e1f378b53b5e99149a949461cfae86776326dfb7f283`, seed = hash of the final NEAR block at height 223,994,076, 26 strata, 564 clusters, 56,400 blocks.
- **2026-11-11, collection rate and stopping rule (set before any cluster beyond the first was read).** NEARDATA answers about 13 blocks a minute from one IP without HTTP 429, so the 56,400 blocks take about 60 hours, not 43. We collect in the frozen round order and **stop at 2026-11-13 12:00 UTC**. The analysis uses every cluster sealed by then. Quarters can differ by one cluster, and the quarter weights do not depend on the cluster count.
- **2026-11-11, `ok_tx` definition.** `ok_share` is the share of transactions whose own outcome is not a Failure, which means a receipt was created. Receipt-level failures are reported separately as `ok_receipt_share` and are not tested.
- **2026-11-11, amended stopping rule (only 3 clusters had been read; all were from the earliest quarters).** To finish with time to write, collection stops each stratum after a draw round: **round 6 for the quarters before 2025-Q1 and round 20 for 2025-Q1 onward** (268 clusters, 26,800 blocks, about 34 hours at 13 blocks a minute), or at **2026-11-12 12:00 UTC**, whichever comes first. The clusters of one stratum are independent uniform draws, so the first k of them are themselves a uniform random sample of that stratum. No cluster is skipped or chosen. If a higher request limit is granted by the data provider, the caps will be lifted and the remaining rounds collected in the frozen order.

*Progress stamp: 160 clusters through 2025Q4_07 (_07 dense); entering 2026 strata; overall still not supported.*
