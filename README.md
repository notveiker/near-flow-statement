# near-flow-statement

A pre-registered, re-runnable token flow statement for NEAR (issuance, staking withdrawals, exchange inflows, identified buying) and the investment thesis built on it, for NEAR HACKATHON 2026, track Investment Thesis.

**The question: who buys and who sells NEAR?**

> Status, 2026-11-07: the offline rebuild passes. H1a, H1b and H1c have results. The forward tests F1-F4 are pending until 2026-11-14. This is research, not financial advice.

## Summary

Same order and caveats as [`THESIS.md`](THESIS.md): the pre-registered result first, then the exploratory one.

**Pre-registered scorecard.** [`PREREG.md`](PREREG.md) was frozen before any BigQuery flow query ran. Window: the 90 days 2026-08-07 to 2026-11-04.

- **H1a fails.** The hypothesis: most staking rewards stay staked. Net staking outflow was 6.56<!--n:h1a_ratio_as_written_x-->× staking rewards, and a pass needed under 0.5×.
- **H1b and H1c are inconclusive.** H1b: less NEAR reaches exchanges than is minted. H1c: identified buying is at least 25% of net exchange inflow. Only 20.0<!--n:h1b_coverage_count_pct-->% of the top-100 NEAR receivers carry a citable exchange label, below the 50% the pre-registration requires. So net exchange inflow is a range, 4.42<!--n:h1b_net_inflow_lower_m-->M to 152.45<!--n:h1b_net_inflow_upper_m-->M NEAR, against 8.0098<!--n:h1a_gross_issuance_90d_m-->M NEAR minted.
- **The frozen rating rule outputs Hold.** Buy needed H1b to pass. Avoid needed it to fail.

**Exploratory, chosen after the freeze (not pre-registered).** Over the 30 days to 2026-11-04, the NEAR delivered to NEAR's three Intents revenue wallets (`buybacks.multisignature.near`, `fefundsadmin.sputnik-dao.near`, `1csfundsadmin.sputnik-dao.near`) offset 15.81<!--n:ladder_all_wallets_pct_of_issuance-->% of net issuance (88,295<!--n:net_issuance_near_per_day_window--> NEAR a day). Only 4.53<!--n:ladder_public_collectors_pct_of_issuance--> points of that trace on chain to public fee collectors. Another 11.25<!--n:ladder_escrow_unshields_pct_of_issuance--> points arrive as unshields from the Confidential Intents escrow (`THESIS.md`, section 2, shows how it is identified), and the fee stream behind them is unattested. The last 0.03<!--n:ladder_other_pct_of_issuance--> points come from one other recurring source. So the value capture that can be verified is a range, 4.53<!--n:ladder_public_collectors_pct_of_issuance-->% to 15.81<!--n:ladder_all_wallets_pct_of_issuance-->% of net issuance. A per-stream attestation by NEAR of which fees fund which escrow releases would turn the range into one number. The ladder does not feed the rating rule.

**Forward tests F1-F4 are pending.** The predictions are fixed in `PREREG.md`. The window is 2026-11-06 to 2026-11-13. They are scored after 2026-11-14 00:00 UTC by `python3 -m pipeline.score_forward --score`, which refuses to run earlier. Every result will be published, misses included.

**What this does not show.**

- Who sold. NEAR is fungible, so every flow result is a market-wide balance, not an attribution to sellers.
- How much NEAR reached exchanges. Only 20.0<!--n:h1b_coverage_count_pct-->% of the top-100 receivers carry a citable exchange label, and no citable NEAR address was found for OKX, Coinbase, Kraken, Bybit, HTX, Crypto.com, Upbit or Bithumb.
- Which fee stream funds the escrow releases. Only NEAR can attest that.
- Partner and channel numbers rest on one key-gated source, the Explorer API. The repository commits its daily aggregates and a sample of swaps, not every swap.

## Where the results live

- [`THESIS.md`](THESIS.md): the investment thesis. It opens with the pre-registered scorecard, then the exploratory ladder, then the risks, what would change our mind, and its limits.
- [`docs/supply-side.md`](docs/supply-side.md): the pre-registered scorecard in detail, the staking-outflow reconciliation, and where the largest unstakers' NEAR went.
- [`docs/intents-fee-flows.md`](docs/intents-fee-flows.md): who earns from NEAR Intents fees, and whether Intents volume touches the NEAR token. 30 days of 1Click swaps reconciled against NEAR's revenue wallets on chain.
- [`docs/partner-concentration.md`](docs/partner-concentration.md): how much of NEAR's Intents revenue depends on SwapKit and a few other channels, and where the buyback wallet's NEAR comes from on chain.
- [`PREREG-ADDENDUM.md`](PREREG-ADDENDUM.md): every post-freeze result, method choice and correction, dated.
- `site/index.html`: the static dashboard (step 6 below).

## Try it (judges): do X, see Y

Needs Python 3.10+ and git. Standard library only: no `pip install`, no network, no keys. `make` is optional; each make target is a plain `python3 -m ...` command, shown below. Run everything from the root of a clean checkout (`git clone https://github.com/notveiker/near-flow-statement && cd near-flow-statement`). The outputs below were captured on 2026-11-07. Steps 1 to 5 take a few seconds in total.

| # | Do | See | What it shows |
|---|---|---|---|
| 1 | `python3 -m pipeline.check --manifest` | `check: PASS` | Every file under `data/raw/` matches the SHA-256 recorded in `data/MANIFEST.json`, and none is missing or unlisted. Change one byte and it prints, for example, `FAIL  hash mismatch: raw/llama/volume_maya-protocol.json` and exits with status 1. |
| 2 | `python3 -m pipeline.compute`<br>`git status --short` | `wrote data/metrics.json (237 metrics, as of 2026-11-04)`<br>then nothing: git reports no change | Every number in `data/metrics.json` and `data/series.json` is recomputed offline from the committed snapshots. The output is deterministic: both files come out byte-identical to the committed ones. |
| 3 | `python3 -m pipeline.check --numbers` | `check: PASS` | Every `<!--n:…-->` marker in `README.md`, `THESIS.md`, `PREREG-ADDENDUM.md` and `docs/*.md` sits directly after a number equal to `data/metrics.json[key]`. A wrong number prints `FAIL  <file>: <key> says <number in the text>, metrics.json says <metric value>` and exits with status 1. A number without a marker is not checked. |
| 4 | `python3 -m unittest discover -s tests` | `Ran 145 tests in 5.3s` (the count and time vary), a blank line, then `OK` | The H1a evidence and numbers, the rating rule and all its branches, the forward-test scorer (missing data is `not scorable`, band edges are inclusive, `--score` refuses to run before 2026-11-14), the dashboard (`tests/test_render.py`: each number the page prints in a data-attributed span equals the source it names, any other number in the text is a date, an identifier or a window length, each bar, column, band and dot is drawn to its value on the axis its chart declares, the page is checked as committed and with the forward tests pending and scored, and the committed `site/index.html` equals a fresh render), and repository integrity (`tests/test_integrity.py`: the frozen `PREREG.md` hash and tag, the raw-data manifest, the secret scanner and its rules, the fresh-clone script, and the CI and Pages workflows). From 2026-11-14 00:00 UTC the refusal test skips itself and the last line reads `OK (skipped=1)`. |
| 5 | `make reproduce` | `python3 -m pipeline.check --manifest`<br>`check: PASS`<br>`python3 -m pipeline.compute`<br>`wrote data/metrics.json (237 metrics, as of 2026-11-04)`<br>`python3 -m pipeline.check --numbers`<br>`check: PASS` | Steps 1, 2 and 3 in one command. It takes about a second. |
| 6 | `python3 -m pipeline.render` (or `make render`)<br>`python3 -m pipeline.render --check` (or `make render-check`)<br>then open `site/index.html` in a browser | `render: wrote site/index.html (416,999 bytes), data fingerprint d225c691341d6a25, data as of 2026-11-04`<br>`render: site/ matches a fresh render (site/index.html (416,999 bytes), data fingerprint d225c691341d6a25, data as of 2026-11-04)`<br>A page titled "NEAR flow statement dashboard". The byte count changes only when the page or its inputs change. | The dashboard is rebuilt offline from `data/metrics.json` and `data/series.json`, and `--check` exits with status 1 unless the committed `site/index.html` equals a fresh render byte for byte. The page has 13 chart cards, 5 pre-registered and 8 exploratory. Each card has a sentence on what it shows, one on what it does not show, a Query block and a Data table. The page has no JavaScript and loads nothing from another file or host. |
| 7 | `sha256sum PREREG.md`<br>`git rev-parse 'prereg-freeze^{}'`<br>`git diff prereg-freeze HEAD -- PREREG.md` | `19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240  PREREG.md`<br>`413d776164a42ddb2b1288bb02bd7bd112bc7f06`<br>nothing | The frozen pre-registration is unchanged since the tag `prereg-freeze`. Needs a git clone (a zip download has no tags). On macOS use `shasum -a 256 PREREG.md`. |
| 8 | `bash scripts/fresh_clone_check.sh` | A table of 13 steps, each `PASS`, then `RESULT: PASS (13 passed, 0 skipped, 0 failed; 12s)` (the time varies), and exit status 0 | Clones the repository's committed `HEAD` into a temporary directory and runs the offline checks there, not in the author's working tree: the Python version, the manifest, `compute` rewriting nothing, the numbers check, the unit tests, `render --check`, the `PREREG.md` hash and tag, `make reproduce`, and the secret scans. It needs no network or key, and removes its directory on exit. `--worktree` checks your working tree instead (the tag and history rows then skip), and a URL argument clones that URL. |
| 9 | `python3 scripts/scan_secrets.py --history` | `scan_secrets: PASS (working tree: 101 files, …; history: 204 blobs, 30 commits, 1 tags, …; 21 content rules, 7 file-name rules)` (the counts grow with the repository), and exit status 0 | No key or secret that the scanner can recognise in the working tree, in any commit or tag message, or in any file ever committed, deleted ones included. It is a pattern scan, not a proof: it cannot see a secret with no recognisable shape. Without `--history` it scans the working tree only. |

**Dashboard.** The dashboard is the committed file `site/index.html`, the output of `python3 -m pipeline.render`. It is one static file: no JavaScript, and nothing loaded from another file or host, so it opens from disk. No hosted URL is claimed here. The Pages workflow (`.github/workflows/pages.yml`) can publish it once the repository is public.

## Trace a headline number

| Result | Keys in `data/metrics.json` | Computed by | Raw inputs |
|---|---|---|---|
| H1a ratio | `h1a_ratio_as_written_x`, `h1a_ratio_endpoint_archival_x`, `h1a_ratio_with_lst_pool_x` | `pipeline/h1a.py` | `data/raw/rpc/epoch_issuance.json` (gross issuance from epoch-boundary block headers), `data/raw/rpc/pool_endpoints_archival.json`, `data/raw/bq/staking_flows_daily.json`, `data/raw/bq/staking_pool_totals_endpoints.json` |
| H1b range, label coverage and H1c | `h1b_net_inflow_lower_m`, `h1b_net_inflow_upper_m`, `h1b_coverage_count_pct`, `h1b_verdict`, `h1c_verdict` | `pipeline/h1b.py` | `data/raw/bq/h1b_a_native_flows.json`, `data/raw/bq/h1b_b_wnear_logs.json`, `data/raw/rpc/buyback_balance_endpoints.json`. The label list and its sources are in `data/raw/labels/exchange_accounts.json` |
| Rating rule | `rating_output`, `rating_g_req_pct`, `rating_g_obs_pct` | `pipeline/h1a.py` (function `rating`) | `data/raw/rpc/rating_assumptions.json`, `data/raw/rpc/epoch_issuance.json`, `data/raw/llama/dailyRevenue_near-intents.json` |
| Ladder (exploratory) | `ladder_all_wallets_pct_of_issuance`, `ladder_public_collectors_pct_of_issuance`, `ladder_escrow_unshields_pct_of_issuance` | `pipeline/compute.py` (function `escrow_ladder`) | `data/raw/escrow/deliveries.csv`, `data/raw/escrow/issuance_reads.json` |
| Forward tests F1-F4 | none until scored | `pipeline/score_forward.py` | fetched at scoring time; the result goes to `data/forward/score_<UTC stamp>/result.json` |

## Optional: needs the network, a key or gcloud

Nothing here is needed to check the results. These commands refresh or re-check the committed snapshots against the live sources. Run them in a throwaway clone. Several overwrite files in `data/raw/` and `data/MANIFEST.json`, and a refreshed snapshot can change a number that the prose quotes, which `python3 -m pipeline.check --numbers` would then report.

| Command | Needs | What it does |
|---|---|---|
| `make fetch`<br>(runs `python3 -m pipeline.fetch_keyless`) | Network, no key | Refreshes the keyless sources: DefiLlama, Nearblocks, CoinGecko and NEAR RPC (FastNEAR). Name a source to refresh only that one, for example `python3 -m pipeline.fetch_keyless coingecko_majors`. |
| `python3 -m pipeline.fetch_escrow verify --sample 60` | Network, no key | Re-checks a seeded sample of revenue-wallet deliveries in `data/raw/escrow/deliveries.csv`, and their funding transfers from the Confidential Intents escrow, against FastNEAR's transaction API and archival RPC. Prints a JSON summary, exits with status 1 if any check fails, and rewrites `data/raw/escrow/verify_sample.json`. `verify --all` checks every row (about 230 batched requests). |
| `python3 -m pipeline.fetch_fee_evidence trace` | Network, no key | Re-reads the NEAR transactions of the 195<!--n:fee_ev_swaps_n--> sampled 1Click swaps from FastNEAR and rewrites `data/raw/evidence/fee_sample_onchain.json`: every token movement, so anyone can check who was paid what. Drawing a new sample (`python3 -m pipeline.fetch_fee_evidence sample`) needs the Explorer key below. |
| `python3 -m pipeline.fetch_issuance --verify 10` | Network, no key | Re-reads 10 random committed epochs and the two window endpoints from archival RPC and compares them with `data/raw/rpc/epoch_issuance.json`. Writes nothing. Ends with `verify: PASS` if all match. |
| `python3 -m pipeline.score_forward --dry-run` | Network, no key | Exercises the forward-test scorer on the last 8 complete UTC days. Prints `DRY RUN ON CURRENT DATA - NOT A SCORE OF F1-F4` and writes `data/forward/dry-run_<UTC stamp>/DRY_RUN_result_NOT_A_SCORE.json`. **It is not a score of F1-F4** and is never quoted as one. |
| `python3 -m pipeline.score_forward --score` | None before 2026-11-14 00:00 UTC; network after | Before that time it prints `refusing to score: it is <UTC now>, scoring opens 2026-11-14T00:00:00Z (PREREG.md).` and exits with status 2, without any network call. From then on it fetches DefiLlama, Nearblocks and archival RPC data, scores F1-F4 as `PREREG.md` words them (missing data is `not scorable`, never estimated) and writes `data/forward/score_<UTC stamp>/result.json`. |
| `make explorer`<br>(runs `python3 -m pipeline.fetch_explorer`) | Explorer key | Pulls successful 1Click swaps from the NEAR Intents Explorer API and aggregates them by day into `data/raw/explorer/daily.json`. Needs an Explorer key from [partners.near-intents.org](https://partners.near-intents.org) as `NEAR_INTENTS_EXPLORER_JWT`, in your environment or in a git-ignored `.env`. The API allows 1 request per 5 s, so 30 days takes about 1h45m. Finished days are cached in `.cache/explorer/`. Takes optional start and end dates; the default is 2026-10-06 to 2026-11-04. |
| `make bq`<br>(runs `python3 -m pipeline.bq_run`) | gcloud auth (the `bq` CLI) | Re-runs `sql/*.sql` on `bigquery-public-data.crypto_near_mainnet_us`. Every query is dry-run first and capped with `--maximum_bytes_billed`. A full run scans about 230 GB, which costs roughly $1.50 at on-demand pricing (about $6.25 per TB) once a project is past BigQuery's free 1 TB a month. To refresh one query, run `python3 -m pipeline.bq_run <name>`. The three staged `h1b_*` queries are skipped by a plain `make bq`; run them by name, for example `NFS_BQ_MAX_GB=270 python3 -m pipeline.bq_run h1b_a`. |

## Track brief: where to find it

The organizers' brief for the Investment Thesis track is `tracks/02-thesis.md` in the repository `nearai/near-hackathon-prompt-examples`. The quotes below are from it.

| Brief | Where it is here |
|---|---|
| "Build a long-term investment thesis for NEAR and back it with onchain analytics, live dashboards and models anyone can re-run." | Thesis: `THESIS.md`. Onchain analytics: `docs/` and the queries in `sql/`, with results in `data/raw/bq/`. Dashboard: `site/index.html`, static and built from committed snapshots, not a live feed. Models: `pipeline/h1a.py`, `pipeline/h1b.py`, `pipeline/compute.py`. Re-run: `make site`. |
| "The score depends on evidence someone else can reproduce." | The "Try it" table above. `data/MANIFEST.json` hashes every raw file. The on-chain re-checks in the optional table need no key. |
| "SQL queries against the NEAR BigQuery public dataset (bigquery-public-data.crypto_near_mainnet_us) for daily active accounts, transaction counts and contract usage. Always filter on block_date to keep query costs down." | `sql/*.sql` and `sql/unstakers/*.sql`. Every file filters on `block_date`: `grep -L block_date sql/*.sql sql/unstakers/*.sql` prints nothing. Results are committed in `data/raw/bq/`, so reading them needs no gcloud; `make bq` re-runs the queries. The brief's example topics are daily active accounts, transaction counts and contract usage. These queries cover staking-pool flows, exchange flows, the Intents revenue wallets and the escrow deliveries instead. Daily active accounts and transaction counts come from the Nearblocks charts snapshot, not from BigQuery. |
| "A pull from the NEAR Intents Explorer API for swap volume. It needs a JWT from the partner dashboard; I'll put it in .env." | `pipeline/fetch_explorer.py` (`make explorer`), which reads the key from `NEAR_INTENTS_EXPLORER_JWT` or a git-ignored `.env`. Output: `data/raw/explorer/daily.json`, daily aggregates of successful 1Click swaps for the 90 days 2026-08-07 to 2026-11-04. Used in `docs/intents-fee-flows.md` and `docs/partner-concentration.md`. |
| "One command that rebuilds every chart from raw data." | `make site`: one offline command from the raw data to every chart. It runs the three `make reproduce` steps (hash check, `python3 -m pipeline.compute`, numbers check) and then `python3 -m pipeline.render`, with no network and no key. `make reproduce` alone stops before the charts. `make all` chains `fetch`, `bq`, `reproduce`, `render` and `test`, and needs the network and gcloud. |
| "A static dashboard page: each chart, the query behind it, and one plain sentence on what it shows." | `site/index.html`: 13 chart cards. Each has a sentence on what it shows, one on what it does not show, a Query block (the SQL file, or the API call and the fetcher where the source is an API) and a Data table. Cards built from committed snapshots list those files with their SHA-256. |
| "THESIS.md with the claim, the evidence for it, the evidence against it, and what result would change my mind." | `THESIS.md`. The claim is "The thesis in one paragraph". The evidence is sections 1 to 4. Evidence against is in sections 3 and 4 (partners keep more than NEAR, H1a fails, H1b and H1c are inconclusive). What would change our mind is section 5. "Limits" closes the file. |
| "Never invent numbers. If a metric can't be computed from these sources, write that in THESIS.md." | `python3 -m pipeline.check --numbers` (step 3) checks every marked number against `data/metrics.json`. `THESIS.md` says what cannot be computed: H1b and H1c are inconclusive for lack of exchange labels, the escrow fee stream is unattested, and its "Limits" section lists the rest. |

## Repo map

| Path | What it is |
|---|---|
| `README.md`, `AGENTS.md`, `CLAUDE.md` | This file, and instructions for AI agents (`CLAUDE.md` only imports `AGENTS.md`). |
| `THESIS.md` | The investment thesis. |
| `PREREG.md` | The frozen pre-registration. Never edited. |
| `PREREG-ADDENDUM.md` | Dated, append-only record of post-freeze results, method choices and corrections. |
| `docs/` | `supply-side.md`, `intents-fee-flows.md`, `partner-concentration.md`. |
| `data/raw/` | Committed snapshots of every source, hashed in `data/MANIFEST.json`. |
| `data/metrics.json`, `data/series.json` | Every published number, and the chart series. Written only by `pipeline/compute.py`. |
| `pipeline/` | `fetch_*.py` (live fetchers), `bq_run.py` (BigQuery runner), `compute.py` (metrics), `h1a.py` and `h1b.py` (the pre-registered tests and the rating rule), `check.py` (integrity checks), `score_forward.py` (forward tests), `render.py` (dashboard). |
| `sql/` | BigQuery queries. `sql/unstakers/` holds the unstaker tracing queries. |
| `tests/` | Offline tests: the pipeline logic, the dashboard (`test_render.py`) and repository integrity (`test_integrity.py`). |
| `site/index.html` | The static dashboard, built by `python3 -m pipeline.render`. |
| `scripts/` | `fresh_clone_check.sh`, `scan_secrets.py`. |
| `.github/workflows/` | `ci.yml`, `pages.yml`. |
| `Makefile`, `LICENSE` | Make targets (`site`, `reproduce`, `render`, `render-check`, `check`, `test`, `fetch`, `explorer`, `bq`), and the MIT licence. |

Note on `sql/`: the headers of `h1b_a_native_flows.sql`, `h1b_b_wnear_logs.sql` and `h1b_c_sweep_clusters.sql` say "NOT run" because they were written before their runs. Their job IDs and run times are in `PREREG-ADDENDUM.md` (entry 2026-11-06 23:23 UTC) and their results are in `data/raw/bq/`. The files are left byte-identical because the addendum cites the committed versions. `h1b_b_alt_wnear_ft_events.sql` is an alternative whose result is not committed.

## Data sources and attribution

| Source | Used for | Access | Snapshot date (UTC, from `data/MANIFEST.json`) | Committed in |
|---|---|---|---|---|
| [DefiLlama](https://defillama.com) API (`api.llama.fi`) | NEAR Intents daily volume, fees, revenue and holders revenue; NEAR chain fees; volume and fees of the peers THORChain, Chainflip and Maya | Keyless | 2026-11-05 | `data/raw/llama/` |
| DefiLlama adapters (source code on [GitHub](https://github.com/DefiLlama)) | The `near-intents` fee adapter defines which wallets count as revenue. The exchange-transparency adapters, at a pinned commit, supply some exchange account labels | Keyless, read on GitHub | 2026-11-06 (labels) | `data/raw/labels/exchange_accounts.json` (each account carries its source URL) |
| [Nearblocks](https://nearblocks.io) API (`/v1/charts`) | Daily transactions, active accounts, total supply and fees | Keyless | 2026-11-05 | `data/raw/nearblocks/` |
| [CoinGecko](https://www.coingecko.com) API | NEAR price history and market snapshot; 90 days of daily prices for the tokens that reach NEAR's fee collectors | Keyless | 2026-11-05 (NEAR), 2026-11-06 (other tokens) | `data/raw/coingecko/` |
| NEAR RPC: [FastNEAR](https://fastnear.com) and near.org endpoints, and FastNEAR's transaction API | Final block, protocol config, validators, wallet balances, archival block headers and balances at fixed heights, per-transaction traces | Keyless | 2026-11-05 and 2026-11-06 | `data/raw/rpc/`, `data/raw/escrow/`, `data/raw/evidence/` |
| NEAR Intents Explorer API (`explorer.near-intents.org`) | Successful 1Click swaps, aggregated per day, and the evidence sample of swaps | Key-gated (partner key) | 2026-11-07 | `data/raw/explorer/daily.json`, `data/raw/evidence/` |
| [NEAR BigQuery public dataset](https://docs.near.org/data-infrastructure/big-query) (`bigquery-public-data.crypto_near_mainnet_us`) | Staking-pool flows, revenue-wallet and fee-collector inflows, escrow deliveries, exchange flows, unstaker tracing | Needs gcloud; the query results are committed | 2026-11-05 to 2026-11-06 | `data/raw/bq/`, `data/raw/escrow/deliveries.csv`, `data/raw/unstakers/`; queries in `sql/` |
| Binance proof-of-reserves address endpoint (`www.binance.com/bapi/apex/v1/public/apex/market/por/address`) | Exchange labels: the NEAR-network addresses Binance lists | Keyless | 2026-11-06 | `data/raw/labels/binance_por_address_2026-11-06.json` |
| NEAR Intents documentation (`docs.near-intents.org`) | Fee rules and the Confidential Intents treasury account (`PRIVATE_TREASURY_ACCOUNT_ID`), cited in `docs/` and `THESIS.md` | Read by the author; no data is taken from it | not applicable | not applicable |

Attribution: Data by [CoinGecko](https://www.coingecko.com). DeFi data by [DefiLlama](https://defillama.com). Network data by [Nearblocks](https://nearblocks.io). RPC and transaction data by [FastNEAR](https://fastnear.com). This repository does not restate the terms of use of these sources.

## Integrity rules

- **The pre-registration is frozen.** `PREREG.md` sits at git tag `prereg-freeze` (commit `413d776`) with SHA-256 `19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240`. It is never edited. Step 7 checks all three.
- **The addendum is append-only and dated.** Every post-freeze result, method choice and correction is a dated entry in `PREREG-ADDENDUM.md`. Entries never change a hypothesis, threshold or probability. Corrections are shown, not overwritten: the 2026-11-06 entry "correction to the timing of the entry above" records that an earlier entry's heading gave the wrong timing.
- **Numbers in prose are machine-checked.** A number that exists in `data/metrics.json` carries a `<!--n:…-->` marker, and `python3 -m pipeline.check --numbers` fails if the marked number differs from the metric (step 3). It does not check unmarked numbers.
- **Raw snapshots are hash-checked.** `data/MANIFEST.json` records the SHA-256 of every file in `data/raw/`, and `python3 -m pipeline.check --manifest` fails on any mismatch, missing file or unlisted file (step 1).
- **Pre-registered and exploratory results are labelled.** The ladder was chosen after the freeze and after all three flow results. The addendum records this (entry 2026-11-07 00:21 UTC), and `THESIS.md` labels it wherever it appears.
- **Forward tests are scored by a script that refuses to run early.** `pipeline/score_forward.py` scores F1-F4 exactly as `PREREG.md` words them and refuses to run before 2026-11-14 00:00 UTC. It was written after the forward window opened, which the addendum discloses. A test with missing data is `not scorable`, never estimated. Every result will be published, misses included. Output of its `--dry-run` mode is never a score.
- **What these checks do not show.** Git timestamps are written by the committing machine. `PREREG.md` says its hash "is published on NEAR mainnet (see `docs/ANCHOR.md` once anchored)"; no `docs/ANCHOR.md` is committed, so there is no on-chain anchor to check here.

## Pre-registration

[`PREREG.md`](PREREG.md) was frozen at git tag `prereg-freeze` **before** any BigQuery flow query ran. Its SHA-256 is `19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240`. Anything added after the freeze is dated and goes in [`PREREG-ADDENDUM.md`](PREREG-ADDENDUM.md).

## Timeline and disclosure

- **Hackathon dates:** the organizers' README (`nearai/near-hackathon-prompt-examples`) gives development from 2026-11-01 00:00 UTC to 2026-11-14 23:59 UTC. Every commit in this repository is dated 2026-11-05 or later.
- **First commit:** `a2cb97c`, 2026-11-05 22:49:54 UTC. `git log --reverse --format='%h %aI %s' | head -1` prints `a2cb97c 2026-11-05T16:49:54-06:00 Initial commit: license and gitignore`.
- **Pre-registration frozen:** commit `413d776`, tag `prereg-freeze`, 2026-11-05 22:53:29 UTC.
- **After the freeze:** the BigQuery flow queries (results dated 2026-11-05 to 2026-11-06 in `data/MANIFEST.json`), the forward-test window (2026-11-06 to 2026-11-13) and the exploratory ladder (chosen 2026-11-07; see the addendum).
- **Earlier work:** [`docs/supply-side.md`](docs/supply-side.md) refers to prior research that is not part of this repository, and `THESIS.md` (Limits) says other earlier work is not reproduced here. The repository does not record when that work was done.
- **AI assistance:** this repository was built with AI coding assistance (Claude Code, Anthropic) under the direction of the repository owner. As of 2026-11-07 every commit carries a `Co-Authored-By: Claude` trailer (`git log --format=%B | grep -i co-authored | sort | uniq -c`). The numbers that carry a marker are computed by committed code from committed snapshots (steps 1 to 5). The code is Python standard library only; no third-party code or library is included.

## License

MIT. See [`LICENSE`](LICENSE).
