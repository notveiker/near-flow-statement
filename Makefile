# near-flow-statement: every target is plain Python 3.10+ (standard library only).
PY ?= python3

.PHONY: reproduce fetch explorer bq compute render check test all

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

check:
	$(PY) -m pipeline.check --manifest --numbers

test:
	$(PY) -m unittest discover -s tests -v

all: fetch bq reproduce test
