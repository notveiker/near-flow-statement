# near-flow-statement

**Who buys and who sells NEAR?** This is a re-runnable token flow statement and investment thesis for NEAR, built for the NEAR Hackathon (Investment Thesis track).

> Status: **work in progress** (2026-11-05). The data pipeline and offline rebuild work. The dashboard, `THESIS.md` and CI come next.

## Try it (offline, no keys, standard-library Python 3.10+)

| Do | See |
|---|---|
| `make reproduce` | Checks every raw snapshot against its SHA-256 in `data/MANIFEST.json`, recomputes `data/metrics.json`, then prints `check: PASS` |
| `make fetch` | Refreshes the keyless sources (DefiLlama, Nearblocks, CoinGecko, NEAR RPC) |
| `make bq` | Re-runs `sql/*.sql` on `bigquery-public-data.crypto_near_mainnet_us`. Needs `gcloud` auth. Every query is dry-run first and capped with `--maximum_bytes_billed` |

## Pre-registration

[`PREREG.md`](PREREG.md) was frozen at git tag `prereg-freeze` **before** any BigQuery flow query ran. Its SHA-256 is `19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240`. Anything added after the freeze is dated and goes in [`PREREG-ADDENDUM.md`](PREREG-ADDENDUM.md).

## License

MIT
