# near-flow-statement

**Who buys and who sells NEAR?** This is a re-runnable token flow statement and investment thesis for NEAR, built for the NEAR Hackathon (Investment Thesis track).

> Status: **work in progress** (2026-11-05). The data pipeline and offline rebuild work. The dashboard, `THESIS.md` and CI come next.

## Try it (offline, no keys, standard-library Python 3.10+)

| Do | See |
|---|---|
| `make reproduce` | Checks every raw snapshot against its SHA-256 in `data/MANIFEST.json`, recomputes `data/metrics.json`, then prints `check: PASS` |
| `make fetch` | Refreshes the keyless sources (DefiLlama, Nearblocks, CoinGecko, NEAR RPC) |
| `make explorer` | Pulls successful 1Click swaps from the NEAR Intents Explorer API and aggregates them by day into `data/raw/explorer/daily.json`. Needs an Explorer key from [partners.near-intents.org](https://partners.near-intents.org) as `NEAR_INTENTS_EXPLORER_JWT`, in your environment or in a git-ignored `.env`. The API allows 1 request per 5 s, so 30 days takes about 1h45m. Finished days are cached in `.cache/explorer/` |
| `make bq` | Re-runs `sql/*.sql` on `bigquery-public-data.crypto_near_mainnet_us`. Needs `gcloud` auth. Every query is dry-run first and capped with `--maximum_bytes_billed`. A full run scans about 230 GB, which costs roughly $1.50 at on-demand pricing (about $6.25 per TB) once a project is past BigQuery's free 1 TB a month. To refresh one query, run `python3 -m pipeline.bq_run <name>` |
| `python3 -m pipeline.fetch_escrow verify --sample 60` | Re-checks a random sample of revenue-wallet deliveries in `data/raw/escrow/deliveries.csv`, and their funding transfers from the Confidential Intents escrow, against FastNEAR and archival RPC. No key. `verify --all` checks every row |

## Findings so far

- [`THESIS.md`](THESIS.md): the investment thesis. It opens with the pre-registered scorecard (H1a fails; H1b and H1c inconclusive; the frozen rule rates NEAR **Hold**), then leads with an **exploratory, post-freeze** exhibit: how much of NEAR's value capture can be verified on chain (4.5-15.8% of net issuance).
- [`docs/intents-fee-flows.md`](docs/intents-fee-flows.md): who earns from NEAR Intents fees, and whether Intents volume touches the NEAR token. Covers 30 days of 1Click swaps reconciled against NEAR's revenue wallets on chain.
- [`docs/partner-concentration.md`](docs/partner-concentration.md): how much of NEAR's Intents revenue depends on SwapKit and a few other channels. Traces the buyback wallet's NEAR to its on-chain sources.
- [`docs/supply-side.md`](docs/supply-side.md): the pre-registered scorecard (H1a fails; H1b and H1c inconclusive; the frozen rating rule gives **Hold**) and where the largest unstakers' NEAR went.
- [`PREREG-ADDENDUM.md`](PREREG-ADDENDUM.md): every post-freeze result, method choice and correction, dated.

## Pre-registration

[`PREREG.md`](PREREG.md) was frozen at git tag `prereg-freeze` **before** any BigQuery flow query ran. Its SHA-256 is `19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240`. Anything added after the freeze is dated and goes in [`PREREG-ADDENDUM.md`](PREREG-ADDENDUM.md).

## License

MIT
