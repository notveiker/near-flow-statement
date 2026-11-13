# RX11 and RX12 results: which assets drive the public swap volume, and which chains the dollars move between

Rules and falsifiers: [rx11-rx12-method.md](rx11-rx12-method.md), committed `abb6fad` (06:53:24 UTC, 2026-11-13) before the query ran (06:53:26 UTC). Query `sql/rx/rx11_rx12_flows.sql` (20.4 GB billed), same population as RX9 and RX10: 1.155M public simple swaps with a priced leg, $2.171B, 2026-08-07 to 2026-11-04. Eleven swaps ($11K) are excluded because the user leg was not one sold and one bought token. Numbers are computed by `python3 -m pipeline.rx_analysis` into `data/derived/rx_results.json` (keys `rx11`, `rx12`); the job ID and the output SHA-256 are in `data/raw/rx/jobs.jsonl`.

## Results

| Hypothesis | Rule (committed) | Result | Verdict |
|---|---|---|---|
| H-RX11a ZEC is a growth route | share of weekly volume involving ZEC, blocks 8 to 11, at least 1.5 times blocks 0 to 3 (falsified below 1.0) | 13.3% against 4.9%: 2.7 times | supported |
| H-RX11b BTC leads the volatile assets | largest non-stable asset in at least 11 of 12 complete weeks (falsified below 7) | 12 of 12 | supported |
| H-RX11c few volatile assets | top 3 non-stable assets cover at least 70% of swap dollars with a non-stable leg (falsified below 50%) | BTC, ETH, ZEC: 86.0% | supported |
| H-RX12a the NEAR chain is a small leg | swaps touching a NEAR-chain token at most 15% of volume (falsified above 30%) | 25.8% ($561M, 231,548 swaps) | **neither** |
| H-RX12b few destination chains | top 3 destination chains at least 60% (falsified below 40%) | Ethereum, Tron, NEAR: 86.2% | supported |
| H-RX12c users net buy volatile assets | bought exceeds sold over the window (falsified if sold exceeds bought) | users sold $36.9M more non-stable dollars than they bought | **falsified** |

## What drives the volume

- **Involved volume by asset** (share of all priced swap dollars that involve the asset; a swap counts for each asset in it): BTC 22.9%, ETH 12.8%, ZEC 10.3%, SOL 2.9%, XRP 2.0%, NEAR 1.5%, TRX 1.2%, BNB 0.8%, LTC 0.3%, DOGE 0.2% (stablecoins are the other side of most of these). The weekly series for the top ten are in `rx_results.json`.
- **ZEC went from 4.9% of weekly volume (first four weeks) to 13.3% (last four).** Weekly: 4.6%, 3.3%, 6.7%, 5.1%, 12.8%, 11.8%, 11.0%, 14.4%, 11.1%, 10.0%, 14.4%, 17.5% (blocks 0 to 11). Same comparison (first four weeks to last four, post hoc) for the others: BTC 18.1% to 27.4% (1.5 times), ETH 12.8% to 14.7%, SOL 2.0% to 4.6% (2.3 times). ZEC grew most in relative terms. The pre-registered test is about the share of volume; it does not show who trades it or why.
- **BTC is the largest volatile asset in every complete week.**
- **Users net sold volatile assets over the quarter** (RX12c): $36.9M net, about 3.6% of the non-stable dollars. Weekly net values are in the results file. This is one quarter and follows prices; it is not a reading of sentiment.

## Where the dollars go

- **Destination chains** (chain of the token the user bought, share of dollars): Ethereum 45.8%, Tron 27.1%, NEAR 13.2%, Zcash 4.9%, Arbitrum 2.6%, Base 1.8%, Solana 1.8%, XRP Ledger 1.0%, BNB Chain 0.9%, Litecoin 0.1%.
- **Largest chain-to-chain flows:** Ethereum to Tron 17.2%, Tron to Ethereum 16.3%, NEAR to Ethereum 8.8%, Ethereum to NEAR 8.8%, Ethereum to Ethereum 8.5%, Zcash to Ethereum 3.5%, BNB Chain to Ethereum 3.1%.
- **The NEAR chain is a leg in about a quarter of the dollars (25.8%)**, between the two committed bars, so no verdict. The big NEAR-chain flows are to and from Ethereum (8.8% each way) and Tron (2.1% and 1.6%). The token table labels these assets as living on NEAR; the NEAR token itself is on one side of only 1.5% of dollars (RX9c), so the NEAR-chain share is made of other tokens on NEAR (which ones was not itemised here). The NEAR chain is a real leg of the product; the NEAR token is a small one.
- **Post hoc (not pre-registered): net chain flows.** Counting the chain of the bought token minus the chain of the sold token, Ethereum (+$133M) and Tron (+$127M) take in value; BNB Chain (-$127M) and Solana (-$107M) give it up. The same-chain share (a swap between two tokens on the same chain) is 9.8%.

## What this does not show

Public swaps with priced legs only; complex receipts and confidential swaps are absent. "User" and "solver" are inferred. Chain labels come from the rebuild's token table, not from an independent check. Net flows are of swap legs, not of any wallet's holdings. A share of volume is not a share of NEAR's fee revenue (FU4, FU5). The ZEC increase is a share of the public priced population: it says nothing about total ZEC volume elsewhere.
