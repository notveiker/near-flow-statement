# Supply side: who sold, and did it reach exchanges?

Window: 90 days, 2026-08-07 → 2026-11-04 (UTC). Every number marked with an `n:` comment is checked against `data/metrics.json` by `make reproduce`. The pre-registered tests (H1a, H1b, H1c) are scored in [`PREREG-ADDENDUM.md`](../PREREG-ADDENDUM.md). This page puts them together, with two exploratory follow-ups. NEAR is fungible, so nothing here says which coins were sold.

## The scorecard

| Test (PREREG) | Result | Key numbers |
|---|---|---|
| H1a: most staking rewards stay staked | **Fails** | Net staking outflow was 6.56 <!--n:h1a_ratio_as_written_x-->× staking rewards (90% of 8.0098 <!--n:h1a_gross_issuance_90d_m-->M NEAR gross issuance, read from 297 epoch-boundary headers) |
| H1b: less NEAR reaches exchanges than is minted | **Inconclusive** | Net exchange inflow 4.42 <!--n:h1b_net_inflow_lower_m-->M to 152.45 <!--n:h1b_net_inflow_upper_m-->M NEAR; only 20.0 <!--n:h1b_coverage_count_pct-->% of the top-100 receivers carry a citable exchange label |
| H1c: identified buyers absorb ≥ 25% of exchange-bound supply | **Inconclusive** | Buyback-wallet growth of 1.48 <!--n:h1c_identified_buying_m-->M NEAR is 33.48 <!--n:h1c_ratio_lower_pct-->% of the lower bound and 0.97 <!--n:h1c_ratio_upper_pct-->% of the upper |
| Rating rule | **Hold** | Buy needs H1b to pass; Avoid needs it to fail. G_req 33.2 <!--n:rating_g_req_pct-->%/yr, G_obs 619.0 <!--n:rating_g_obs_pct-->%/yr (71.4 <!--n:rating_g_obs_near_pct-->% in NEAR terms) |

**What the scorecard says plainly.** Stakers withdrew far more than they earned. Whether that NEAR reached exchanges cannot be settled from public labels: the lower bound is about half a quarter's issuance, the upper bound about 19 quarters'. The binding gap is labelling. No citable NEAR address was found for OKX, Coinbase, Kraken, Bybit, HTX, Crypto.com, Upbit or Bithumb.

## 1. The staking outflow, measured two ways, now agrees

- Daily pool flows give a net outflow of 47.3 <!--n:pool_net_outflow_90d_m-->M NEAR.
- The endpoint measure first disagreed by about 7.1M. The cause was a query artifact: the endpoint query only summed pools whose balance changed that day, and `flipside.pool.near` (7.1 <!--n:h1a_residual_flipside_m-->M NEAR) did not change on 08-06 but was withdrawn inside the window. Summed over all 550 pools from archival state, the two measures agree to within about 12K NEAR (0.03%).
- `lst-pool.near` is the only validator the pool-name filter misses. Adding it gives 5.96 <!--n:h1a_ratio_with_lst_pool_x-->×. H1a fails either way.

## 2. Where the largest unstakers' NEAR went (exploratory)

Prior research found that 14 accounts in three pools made almost all of the net outflow, and that each reaches one unlabelled hub (`466222f1…`) within two hops. Two new facts:

- **Part of that trail reaches a sourced exchange reserve.** `5c33c621…` and `7e6e17fc…`, which the earlier trace left unlabelled, are on Binance's own proof-of-reserves address list (snapshot committed at `data/raw/labels/binance_por_address_2026-11-06.json`). `7e6e17fc…` is the `binancenode1` delegator that sent 2.5M NEAR to `binancecold3.near`. This is a reserve address, not proof of a sale.
- **The hub lineage did not route NEAR through Intents.** The 14 withdrawers, the hub, its relays, and every downstream account that received ≥ 100K NEAR moved no NEAR into `intents.near` by any route we could see. Four smaller top-50 withdrawers did: 1.46 <!--n:unstakers_into_intents_m-->M NEAR, mostly between 09-11 and 09-20, via `bridge-mng.near` and the Confidential Intents treasury rather than 1Click.
- **Against 1Click's selling.** In the 30 days where we have 1Click data, 1Click users sold 4.95 <!--n:oneclick_near_sold_30d_m-->M NEAR for other assets. The unstaker set moved 72.8 <!--n:unstakers_into_intents_overlap_k-->K NEAR into Intents over the same days, a size ratio of 1.5 <!--n:unstakers_overlap_pct_of_1click_near_sold-->%. None of it matched a 1Click deposit address.

Evidence: `data/raw/unstakers/results.json` (event-level rows with tx hashes) and `sql/unstakers/` (BigQuery, 63.9 GB). These numbers are not a PREREG test.

## Limits

- **Labels are snapshots** dated 2026-11-06. Exchange addresses retired before then may be missing, which biases the lower bound down.
- **The 100% bound is mechanical.** It treats every unlabelled top-100 receiver as an exchange, including accounts that are probably not.
- **Unstaker tracing** covers two hops, misses meta-transactions, and checks Intents logs only for the 30-day overlap; earlier months are checked through the accounts' own transactions.
- **Validator sets** behind the name-filter check were sampled in 71 of 298 epochs, because archival RPC rate limits were tight.
