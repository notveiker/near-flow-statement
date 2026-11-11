# near-flow-statement: every target is plain Python 3.10+ (standard library only).
PY ?= python3

.PHONY: reproduce fetch explorer bq compute render check test all sample sample-verify sample-rows history-results dashboard census-metrics

reproduce: ## Offline: verify raw-data hashes, then recompute every number into data/metrics.json
	$(PY) -m pipeline.check --manifest
	$(PY) -m pipeline.compute
	$(PY) -m pipeline.check --numbers

fetch: ## Live, keyless: refresh DefiLlama, Nearblocks, CoinGecko and NEAR RPC snapshots
	$(PY) -m pipeline.fetch_keyless

explorer: ## Live: NEAR Intents Explorer API (needs NEAR_INTENTS_EXPLORER_JWT in env or .env)
	$(PY) -m pipeline.fetch_explorer

bq: ## Live BigQuery (needs gcloud auth; every query is capped with --maximum_bytes_billed)
	$(PY) -m pipeline.bq_run

compute:
	$(PY) -m pipeline.compute

render: ## (dashboard renderer: next step)
	@echo 'render: not built yet'

sample: ## Live, keyless, about 60 h at a polite 13 blocks a minute: pull the frozen history sample (resumable)
	$(PY) -m pipeline.near_sample run --root data/sample --per-min 13

sample-verify: ## Re-hash every sealed cluster and check the plan, the block chain inside each cluster and the strata
	$(PY) -m pipeline.near_sample verify --root data/sample

sample-rows: ## Raw clusters -> one small row per cluster (committed in data/derived/)
	$(PY) -m pipeline.sample_metrics rows --root data/sample --out data/derived/sample_clusters.jsonl

history-results: ## Offline: committed cluster rows -> quarter series, U1-U5 verdicts and the counter-evidence table
	$(PY) -m pipeline.sample_metrics results --plan data/sample/plan.json --rows data/derived/sample_clusters.jsonl --out data/derived/history_results.json --issuance-near-per-day 88295

dashboard: ## Offline: committed data -> dashboard/index.html (self-contained, no network)

prop-extras: ## Live, keyless: LST TVL, fee/DEX hierarchy, GitHub pulse, Nearblocks stats
	$(PY) -m pipeline.fetch_prop_extras
	$(PY) -m pipeline.build_dashboard

census-metrics: ## Offline: committed census files -> data/derived/census_metrics.json
	$(PY) -m pipeline.census_metrics

check:
	$(PY) -m pipeline.check --manifest --numbers

test:
	$(PY) -m unittest discover -s tests -v

all: fetch bq reproduce test
