# near-flow-statement: every target is plain Python 3.10+ (standard library only).
PY ?= python3

.PHONY: reproduce fetch bq compute render check test all

reproduce: ## Offline: verify raw-data hashes, recompute every number, rebuild THESIS.md and the dashboard
	$(PY) -m pipeline.check --manifest
	$(PY) -m pipeline.compute
	$(PY) -m pipeline.render
	$(PY) -m pipeline.check --numbers

fetch: ## Live, keyless: refresh DefiLlama, Nearblocks, CoinGecko and NEAR RPC snapshots
	$(PY) -m pipeline.fetch_keyless

bq: ## Live BigQuery (needs gcloud auth; every query is capped with --maximum_bytes_billed)
	$(PY) -m pipeline.bq_run

compute:
	$(PY) -m pipeline.compute

render:
	$(PY) -m pipeline.render

check:
	$(PY) -m pipeline.check --manifest --numbers

test:
	$(PY) -m unittest discover -s tests -v

all: fetch bq reproduce test
