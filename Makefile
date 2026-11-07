# near-flow-statement: every target is plain Python 3.10+ (standard library only).
PY ?= python3

.PHONY: reproduce fetch explorer bq compute render render-check site check test all

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

render: ## Offline: rebuild the static dashboard site/index.html from the committed data
	$(PY) -m pipeline.render

render-check: ## Offline: fail unless the committed site/ equals a fresh render, byte for byte
	$(PY) -m pipeline.render --check

site: ## Offline, one command from raw data to every chart: the three reproduce steps, then render
	$(PY) -m pipeline.check --manifest
	$(PY) -m pipeline.compute
	$(PY) -m pipeline.check --numbers
	$(PY) -m pipeline.render

check:
	$(PY) -m pipeline.check --manifest --numbers

test:
	$(PY) -m unittest discover -s tests -v

all: fetch bq reproduce render test
