# near-flow-statement

**Who buys and who sells NEAR?** This is a re-runnable token flow statement and investment thesis for NEAR, built for the NEAR Hackathon (Investment Thesis track).

**Start here:** open [`dashboard/index.html`](dashboard/index.html) in a browser (one self-contained file, no network), and read [`REPORT.md`](REPORT.md).

> Status: **work in progress** (2026-11-11). Data pipeline, offline rebuild, dashboard and report are in place. The history sample is still being collected.

## Try it (offline, no keys, standard-library Python 3.10+)

| Do | See |
|---|---|
| `make reproduce` | Checks every raw snapshot against its SHA-256 in `data/MANIFEST.json`, recomputes `data/metrics.json`, then prints `check: PASS` |
| `make dashboard` | Rebuilds `dashboard/index.html` from committed data. A clean extract of the repository on a fresh machine produced a byte-identical file (SHA-256 `9ef2380cfa18…`), with all tests and `make check` passing |
| `make fetch` | Refreshes the keyless sources (DefiLlama, Nearblocks, CoinGecko, NEAR RPC) |
| `make explorer` | Pulls successful 1Click swaps from the NEAR Intents Explorer API and aggregates them by day into `data/raw/explorer/daily.json`. Needs an Explorer key from [partners.near-intents.org](https://partners.near-intents.org) as `NEAR_INTENTS_EXPLORER_JWT`, in your environment or in a git-ignored `.env`. The API allows 1 request per 5 s, so 30 days takes about 1h45m. Finished days are cached in `.cache/explorer/` |
| `make bq` | Re-runs `sql/*.sql` on `bigquery-public-data.crypto_near_mainnet_us`. Needs `gcloud` auth. Every query is dry-run first and capped with `--maximum_bytes_billed`. A full run scans about 230 GB, which costs roughly $1.50 at on-demand pricing (about $6.25 per TB) once a project is past BigQuery's free 1 TB a month. To refresh one query, run `python3 -m pipeline.bq_run <name>` |
| `python3 -m pipeline.fetch_fee_evidence trace` | Re-reads the NEAR transactions of 195 sampled 1Click swaps from FastNEAR (no key) and rewrites `data/raw/evidence/fee_sample_onchain.json`: every token movement, so anyone can check who was paid what. Drawing a new sample (`… sample`) needs the Explorer key |
| `python3 -m pipeline.fetch_escrow verify --sample 60` | Re-checks a random sample of revenue-wallet deliveries in `data/raw/escrow/deliveries.csv`, and their funding transfers from the Confidential Intents escrow, against FastNEAR and archival RPC. No key. `verify --all` checks every row |

## Findings so far

- [`docs/structural-thesis.md`](docs/structural-thesis.md): structural prop research (capture stack, Confidential Intents, capital markets, peer competition) — beyond what an RPC dump shows.
- [`docs/catalysts-and-path.md`](docs/catalysts-and-path.md): what has to happen next — attachment / issuance / inventory arithmetic and the near-term calendar.
- [`docs/fee-waterfall.md`](docs/fee-waterfall.md): who keeps the basis points — token-claimable bp, leakage, AITR, peer claim designs.
- [`docs/confidential-attestation.md`](docs/confidential-attestation.md): confidential rails raise economic take while thinning public proof — escrow-dependence and the CIF kill switch.
- [`docs/float-sink.md`](docs/float-sink.md): buyback quality — days-of-issuance covered, scarcity half-life, held vs burned.
- [`docs/prop-research-index.md`](docs/prop-research-index.md): index of proprietary notes and the scoreboard to read first.
- [`docs/prop-punch-card.md`](docs/prop-punch-card.md): one-page punch card of proprietary insights and falsifiers.
- [`REPORT.md`](REPORT.md): the written report. Intents share and volume, how fees reach the token, the issuance path, the market, and a compact risks section. Every figure is checked against `data/metrics.json`.
- [`THESIS.md`](THESIS.md): the investment thesis. It opens with the pre-registered scorecard (H1a fails; H1b and H1c inconclusive; the frozen rule rates NEAR **Hold**), then leads with an **exploratory, post-freeze** exhibit: how much of NEAR's value capture can be verified on chain (4.5-15.8% of net issuance).
- [`docs/intents-fee-flows.md`](docs/intents-fee-flows.md): who earns from NEAR Intents fees, and whether Intents volume touches the NEAR token. Covers 30 days of 1Click swaps reconciled against NEAR's revenue wallets on chain.
- [`docs/partner-concentration.md`](docs/partner-concentration.md): how much of NEAR's Intents revenue depends on SwapKit and a few other channels. Traces the buyback wallet's NEAR to its on-chain sources.
- [`docs/supply-side.md`](docs/supply-side.md): the pre-registered scorecard (H1a fails; H1b and H1c inconclusive; the frozen rating rule gives **Hold**) and where the largest unstakers' NEAR went.
- [`PREREG-ADDENDUM.md`](PREREG-ADDENDUM.md): every post-freeze result, method choice and correction, dated.

## Pre-registration

[`PREREG.md`](PREREG.md) was frozen at git tag `prereg-freeze` **before** any BigQuery flow query ran. Its SHA-256 is `19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240`. Anything added after the freeze is dated and goes in [`PREREG-ADDENDUM.md`](PREREG-ADDENDUM.md).

## License

MIT
