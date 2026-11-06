# near-flow-statement

**Who buys and who sells NEAR?** This is a re-runnable token flow statement and investment thesis for NEAR, built for the NEAR Hackathon (Investment Thesis track).

> Status: **work in progress** (2026-11-05). The data pipeline and offline rebuild work. The dashboard, `THESIS.md` and CI come next.

## Try it (offline, no keys, standard-library Python 3.10+)

| Do | See |
|---|---|
| `make reproduce` | Checks every raw snapshot against its SHA-256 in `data/MANIFEST.json`, recomputes `data/metrics.json`, then prints `check: PASS` |
| `make fetch` | Refreshes the keyless sources (DefiLlama, Nearblocks, CoinGecko, NEAR RPC) |
| `make explorer` | Pulls successful 1Click swaps from the NEAR Intents Explorer API and aggregates them by day into `data/raw/explorer/daily.json`. Needs an Explorer key from [partners.near-intents.org](https://partners.near-intents.org) as `NEAR_INTENTS_EXPLORER_JWT`, in your environment or in a git-ignored `.env`. The API allows 1 request per 5 s, so 30 days takes about 1h45m. Finished days are cached in `.cache/explorer/` |
| `make bq` | Re-runs `sql/*.sql` on `bigquery-public-data.crypto_near_mainnet_us`. Needs `gcloud` auth. Every query is dry-run first and capped with `--maximum_bytes_billed` |

## Findings so far

- [`docs/intents-fee-flows.md`](docs/intents-fee-flows.md): who earns from NEAR Intents fees, and whether Intents volume touches the NEAR token. Covers 30 days of 1Click swaps reconciled against NEAR's revenue wallets on chain.
- [`PREREG-ADDENDUM.md`](PREREG-ADDENDUM.md): the H1a result (fails), plus corrections and scope notes.

## Pre-registration

[`PREREG.md`](PREREG.md) was frozen at git tag `prereg-freeze` **before** any BigQuery flow query ran. Its SHA-256 is `19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240`. Anything added after the freeze is dated and goes in [`PREREG-ADDENDUM.md`](PREREG-ADDENDUM.md).

## License

MIT
