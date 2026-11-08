# Supply side: who sold, and did it reach exchanges?

Window: 90 days, 2026-08-07 → 2026-11-04 (UTC). Every number marked with an `n:` comment is checked against `data/metrics.json` by `make reproduce`. The pre-registered tests (H1a, H1b, H1c) are scored in [`PREREG-ADDENDUM.md`](../PREREG-ADDENDUM.md). This page puts them together, with two exploratory follow-ups. NEAR is fungible, so nothing here says which coins were sold.

## The scorecard

| Test (PREREG) | Result | Key numbers |
|---|---|---|
| H1a: most staking rewards stay staked (pre-registered) | **Fails** | Net staking outflow was 6.56<!--n:h1a_ratio_as_written_x-->× staking rewards (90% of 8.0098<!--n:h1a_gross_issuance_90d_m-->M NEAR gross issuance, read from 297<!--n:h1a_epochs_in_window--> epoch-boundary headers) |
| H1b: less NEAR reaches exchanges than is minted (pre-registered) | **Inconclusive** | Net exchange inflow 4.42<!--n:h1b_net_inflow_lower_m-->M to 152.45<!--n:h1b_net_inflow_upper_m-->M NEAR; only 20.0<!--n:h1b_coverage_count_pct-->% of the top-100 receivers carry an exchange label (10.0<!--n:h1b_coverage_tier1_count_pct-->% a cited one; the rest are labelled by our own sweep rule), below the 50% the pre-registration requires |
| H1c: identified buyers absorb ≥ 25% of exchange-bound supply (pre-registered) | **Inconclusive** | Buyback-wallet growth of 1.48<!--n:h1c_identified_buying_m-->M NEAR is 33.48<!--n:h1c_ratio_lower_pct-->% of the lower bound and 0.97<!--n:h1c_ratio_upper_pct-->% of the upper |
| Rating rule (pre-registered) | **Hold** | G_req 33.2<!--n:rating_g_req_pct-->% a year, G_obs 619.0<!--n:rating_g_obs_pct-->% a year (71.4<!--n:rating_g_obs_near_pct-->% in NEAR terms), Avoid line 16.6<!--n:rating_g_avoid_line_pct-->% a year (half of G_req) |

**What the scorecard says plainly.** Net of deposits, stakers withdrew far more than they earned (this includes exchange-owned stake moving, which is not a sale). Whether that NEAR reached exchanges cannot be settled from public labels: the lower bound is about half a quarter's issuance, the upper bound about 19 quarters'. The binding gap is labelling. No citable NEAR address was found for OKX, Coinbase, Kraken, Bybit, HTX, Crypto.com, Upbit or Bithumb.

**What the Hold means.** The frozen rating rule outputs Hold. That carries no view on NEAR: below 50% label coverage H1b can come out pass or inconclusive but never fail, and observed revenue growth (619.0<!--n:rating_g_obs_pct-->% a year; 71.4<!--n:rating_g_obs_near_pct-->% in NEAR terms) is far above the Avoid line (16.6<!--n:rating_g_avoid_line_pct-->% a year), so the rule could only ever have output Buy or Hold; had H1b failed it would also have been Hold. G_req rests on constants that were committed after the freeze, in the same commit as the as-written H1a result, and G_obs compares the last 180 days with the 180 before, a base window that straddles the 2026-02-23 fee switch. Neither changes the output.

## 1. The staking outflow, measured two ways, now agrees

- Daily pool flows give a net outflow of 47.3<!--n:pool_net_outflow_90d_m-->M NEAR.
- The endpoint measure first disagreed by about 7.1<!--n:pool_flow_residual_m-->M. The cause was a query artifact: the endpoint query only summed pools whose balance changed that day, and `flipside.pool.near` (7.1<!--n:h1a_residual_flipside_m-->M NEAR) did not change on 08-06 but was withdrawn inside the window. Summed over all 550 pools from archival state, the two measures agree to within about 12K NEAR (the residual is -12.1<!--n:h1a_residual_left_k-->K, 0.03%).
- `lst-pool.near` is the only validator the pool-name filter misses. Adding it gives 5.96<!--n:h1a_ratio_with_lst_pool_x-->× (post hoc; the test is not redefined). H1a fails either way.

## 2. Where the largest unstakers' NEAR went (exploratory; not a pre-registered test)

This page and `THESIS.md` refer to an earlier analysis (exploratory, not reproduced here). The repository does not record when it was done; the committed data derived from it (`data/raw/unstakers/`) is stamped 2026-11-06 23:50:01 UTC, after the freeze. Whether it preceded the freeze, or informed the prior for H1a, is not something this repository can show. What the repository holds is its output. `data/raw/unstakers/account_set.json` lists 14<!--n:unstakers_a14_n--> accounts that it labels hub-lineage withdrawers: by the earlier analysis, each reaches one unlabelled hub (`466222f1…`) within two hops. Their `net_diff` values add up to an outflow of 42.87<!--n:unstakers_a14_net_outflow_m-->M NEAR over the 90 days, which is 90.7<!--n:unstakers_a14_share_of_net_outflow_pct-->% of the pools' 47.3<!--n:pool_net_outflow_90d_m-->M NEAR net outflow: most of it, not all. It compares a subset's net with the all-account net: other large net withdrawers appear in the same file, so the 90.7<!--n:unstakers_a14_share_of_net_outflow_pct-->% is not a share of a partition of the outflow. The arithmetic is computed from that file by `pipeline/compute.py` (the `unstakers_a14_*` metrics); the file does not define `net_diff`, and the extraction that produced it, and the tracing of the hub lineage, are not in this repository. The rest of this section is what the committed event-level data shows.

- **Two accounts elsewhere in the top-30 withdrawals now carry a sourced Binance label. Neither is on the hub trail.** Both are on Binance's own proof-of-reserves address list (snapshot committed at `data/raw/labels/binance_por_address_2026-11-06.json`), as is `binancecold3.near`.
  - `7e6e17fc…` is itself a top-30 withdrawer: Binance's delegator unstaking from `binancenode1` and moving 2.5M NEAR to `binancecold3.near`. That is an exchange moving its own or its customers' stake, not a user selling.
  - `5c33c621…` is a destination: part of the ~0.92M NEAR that one top-30 withdrawal (from a `kiln` pool) reached through one-hop relays.
  - These are reserve addresses, not proof of a sale.
- **The hub lineage did not route NEAR through Intents.** The 14 withdrawers, the hub, its relays, and every downstream account that received ≥ 100K NEAR moved no NEAR into `intents.near` by any route we could see. Four smaller top-50 withdrawers did: 1.46<!--n:unstakers_into_intents_m-->M NEAR, mostly between 09-11 and 09-20, via `bridge-mng.near` and the Confidential Intents treasury rather than 1Click.
- **Against 1Click's selling.** In the 30 days where we have 1Click data, 1Click users sold 4.95<!--n:oneclick_near_sold_30d_m-->M NEAR for other assets. The unstaker set moved 72.8<!--n:unstakers_into_intents_overlap_k-->K NEAR into Intents over the same days, a size ratio of 1.5<!--n:unstakers_overlap_pct_of_1click_near_sold-->%. None of it matched a 1Click deposit address.

Evidence: `data/raw/unstakers/results.json` (event-level rows with tx hashes) and the six queries in `sql/unstakers/` (BigQuery; no runner in `pipeline/` and no job ID is recorded for them; the note on that file in `data/MANIFEST.json` gives the scan as 63.9 GB, a figure this repository cannot check). These numbers are not a PREREG test.

## Limits

- **Labels are snapshots** dated 2026-11-06. Exchange addresses retired before then may be missing, which biases the lower bound down.
- **The 100% bound is mechanical.** It treats every unlabelled top-100 receiver as an exchange, including accounts that are probably not.
- **Unstaker tracing** covers two hops, misses meta-transactions, and checks Intents logs only for the 30-day overlap; earlier months are checked through the accounts' own transactions.
- **Validator sets** behind the name-filter check were sampled: the addendum (entry 2026-11-06 23:49 UTC, item 4) records 71 sampled validator sets. How they were drawn, and why they were sampled rather than read for every epoch, is not recorded in the repository.
