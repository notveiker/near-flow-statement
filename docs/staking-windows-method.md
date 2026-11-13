# Ask A: is H1a's staking outflow unusual? Method, fixed before any earlier window is run

Committed 2026-11-13 02:11 UTC (2026-11-13), before any job on an earlier window. **H1a is not re-scored**: its result and rule (`PREREG.md`) are untouched. This file is descriptive context for one number. Data cutoff 2026-11-04 / block 223,088,015, enforced in `pipeline/windows.py`; every window below ends before 2026-08-07. The buyback wallet is never named in a query.

## Question
H1a failed with net staking outflow about 6.6 times staking rewards over 2026-08-07..2026-11-04. Is that unusual against the 90-day windows before it, and does net outflow move with NEAR's price?

## Windows
The H1a window is 2026-08-07..2026-11-04 (its saved output, `data/raw/bq/staking_flows_daily.json`, is re-read, not re-run). The earlier windows are the eight non-overlapping 90-day windows ending 2026-08-06, 2026-05-08, 2026-02-07, ... (`python3 -m pipeline.windows plan`: W1 2026-05-09..08-06 back to W8 2024-08-17..2024-11-14). `sql/windows/staking_flows_window.sql.tpl` is `sql/staking_flows_daily.sql` with only the two dates and the seed day replaced, plus a `block_height <= 223088015` cap on the scan (which cannot change rows before the cutoff). `staking_endpoints_window.sql.tpl` is `sql/staking_pool_totals_endpoints.sql` the same way, used for the pool total at each window's seed day.

**Quirks kept exactly as they are** (my reading of "the query's two known quirks", to be corrected if Victor means others): (1) the first change of a pool inside the window has no delta unless the pool also changed on the seed day, so it is dropped; (2) `receipt_processing` deltas mix delegator deposits/withdrawals with each pool's own gas, and are all counted as inflow or outflow. Pools are `*.poolv1.near` and `*.pool.near` only; liquid-staking contracts are excluded. The endpoint query also sees only pools that changed on that day.

## Cost rule
Each window's dry-run bytes are recorded first. Windows are run most recent first while the running total stays at or under **1.5 TB**; the first window that would pass it, and every earlier one, is not run and is reported as not run (no partial runs, no cheaper variant substituted). Each run is capped, given an explicit job id, and logged with its SQL hash, bytes billed and output SHA-256 in `data/raw/windows/jobs.jsonl`.

## Numbers per window (computed by `pipeline/staking_analysis.py` from the saved files)
- inflow, outflow = sums of `inflow_near`, `outflow_near`; **net outflow** = outflow minus inflow; **pool-credited rewards** = sum of `rewards_near` (`validator_accounts_update`); **net over rewards** = net outflow / rewards (the repo's `pool_net_outflow_to_rewards_x`, which is 6.7 for the H1a window; the 6.56 in the report uses a rewards figure of 7.21M NEAR, 90% of gross, a different denominator; both are stated).
- **net as a share of total stake** = net outflow / pool total (staked plus nonstaked) at the seed day.
- **price change** = NEAR USD price on the window's last day over its seed day minus 1 (DefiLlama `coins.llama.fi` daily series, fetched once and saved with SHA-256; nearest day within two days if one is missing).

## Rules for the readings
- **Where this window ranks** among the windows run plus itself, by net over rewards (1 = highest), and also by net outflow and by net share of stake.
- **"Unusual"** only if its net-over-rewards rank is 1 or 2 **and** its ratio is at least 1.5 times the median of the earlier windows. **"Typical"** if its rank is 4 or worse **or** its ratio is at most 1.2 times that median. Anything else is "borderline". A window with net over rewards below zero (net inflow) counts as the lowest.
- **Rank correlation (Spearman) of net outflow with price change**, across the windows run plus the H1a window, for net outflow in NEAR and for net as a share of stake, with an exact permutation p-value (all orderings). **"Associated"** if |rho| is at least 0.6 and p is at most 0.10; **"no association"** if |rho| is under 0.3; otherwise "weak". With about 7 to 9 points this is a coarse check and is stated as such.
- What would show the ratio is **not** unusual: a rank of 4 or worse, or several earlier windows with a ratio within 20% of 6.7. What would show it **is** unusual: every earlier window under about 4.5 (1.5 times a median near 3 or under).
