# Pre-registration: NEAR token flow statement

Frozen: 2026-11-05 (UTC), before any BigQuery flow query was run. The git tag `prereg-freeze` marks this commit, and the SHA-256 of this file is published on NEAR mainnet (see `docs/ANCHOR.md` once anchored). Nothing below may be edited after the freeze. Additions go in `PREREG-ADDENDUM.md`, dated and labelled as post-freeze.

## What we had already seen when we froze this

These are keyless sources, pulled 2026-11-05 and committed in `data/raw/`. Values are from `data/metrics.json` at commit `e309b4c`.

| Metric | Value |
|---|---|
| Net supply growth, 365 days | 2.48% (~88.2K NEAR/day over the last 30 days) |
| NEAR Intents reported volume, 30 days to 2026-11-04 | $4.00B (DefiLlama, leg-sum) |
| Captured revenue, 30 days | $1.99M (4.98 bp of volume; 32.5% of gross fees) |
| Captured take rate, by month | Oct 2026 5.49 bp. Daily Nov 1-4 2026: 3.52, 2.16, 3.12, 3.35 bp |
| Captured revenue ÷ USD value of net new supply, 30 days | 15.7% |
| Buyback wallet balance ÷ NEAR implied by DefiLlama "holders revenue" since 2026-02-23 | 68.5% |
| Intents share of the native cross-chain peer set (Intents, THORChain, Chainflip, Maya) by reported volume | 55.7% (30d), 62.1% (365d) |
| Gas burn share, protocol v87 | 100% |

We had **not** run any query on staking-pool flows, exchange deposits or Intents event logs.

## The question

The common framing compares buybacks with gross issuance, and finds about 10-20% coverage. Our question is market-wide: **how much NEAR actually flows to exchanges, and how much of that do identified buyers absorb?**

NEAR is fungible, so we make **no claim about which coins are sold**. Every flow result below is a market-wide balance.

## Hypotheses on flows

These are measured with BigQuery `bigquery-public-data.crypto_near_mainnet_us` over the 90 days 2026-08-07 → 2026-11-04 inclusive.

**Definitions**
- *Gross issuance:* the NEAR minted over the window, measured from epoch-boundary block headers, or from daily total supply plus burn if headers are unavailable.
- *Staking rewards:* 90% of gross issuance. The other 10% goes to `treasury.near`.
- *Net staking outflow:* NEAR withdrawn from staking pools minus NEAR deposited into them. Pools are `*.poolv1.near`, `*.pool.near` and the liquid-staking contracts we list in `sql/`, with the list committed before the query runs.
- *Labelled exchange accounts:* a committed, cited list of centralized-exchange deposit and hot-wallet accounts on NEAR. We always report labelled coverage, meaning the share of the top-100 native-NEAR receivers by inflow that we were able to label.
- *Net exchange inflow:* native NEAR plus wNEAR transferred into labelled exchange accounts, minus transfers out of them.
- *Identified buying:* the NEAR balance increase of `buybacks.multisignature.near` over the window. We also report ETF and treasury-company holdings where we can measure them, but they are not part of the tests below.

**Tests**

| ID | Hypothesis | Pass if | Our prior probability |
|---|---|---|---|
| H1a | Most staking rewards stay staked | Net staking outflow < 50% of staking rewards | 0.70 |
| H1b | Less NEAR reaches exchanges than is minted | Net exchange inflow < gross issuance (90d) | 0.55 |
| H1c | Identified buyers absorb a larger share of exchange-bound supply than of issuance | Identified buying ÷ net exchange inflow ≥ 25% | 0.40 |

**Decision rules**
- If **H1b fails**, the supply-side leg of the thesis is rejected and THESIS.md says so in its first paragraph.
- If labelled coverage is below 50%, H1b and H1c are reported as ranges, with the unlabelled share assumed to be 0% or 100% exchange-bound. A test passes only if it passes under both bounds. Otherwise it is "inconclusive".

## Forward tests (resolve before judging)

**Window:** 2026-11-06 00:00 UTC → 2026-11-13 23:59 UTC. Scoring uses DefiLlama data fetched on or after 2026-11-14 and the first final RPC block after 2026-11-14 00:00 UTC.

| ID | Prediction | Probability |
|---|---|---|
| F1 | `buybacks.multisignature.near` balance at the first final block after 2026-11-14 00:00 UTC is in **[2.21M, 2.40M] NEAR** | 0.70 |
| F2 | Mean net supply increase per day (Nearblocks `total_supply`, daily deltas for 2026-11-06 → 2026-11-13) is in **[86.0K, 89.5K] NEAR/day** | 0.75 |
| F3 | Captured take rate (DefiLlama `dailyRevenue` ÷ `dailyVolume`, summed over the window) is **below 4.0 bp**. October's 5.49 bp was a high, not a new level | 0.65 |
| F4 | NEAR Intents' share of the peer-set volume (reported basis) over the window is **≥ 50%** | 0.70 |

**Scoring rules**
- A forward test with missing data is scored "not scorable". It is never estimated.
- Every result is published, including misses.

## Longer-dated predictions

| ID | Resolution date | Prediction | Probability |
|---|---|---|---|
| P1 | 2027-05-04 | Intents' 365-day share of the peer set ≥ 55% | 0.65 |
| P2 | 2027-05-04 | 90-day captured Intents revenue ≥ $6.0M. It was $4.84M for the 90 days to 2026-11-04 | 0.50 |
| P3 | 2027-11-04 | 90-day captured revenue ÷ USD value of net new supply ≥ 25% | 0.35 |

## Rating rule (fixed before modelling)

**Inputs**
- **G_req** is the annual growth in captured Intents revenue needed for captured revenue to equal the USD value of net issuance by 2031-11-04. It assumes HSP-029's ramp to 1.6% after the 90-day grace period, a constant price, and starts from the last 90 days of captured revenue.
- **G_obs** is the annualized growth of captured revenue over the last 180 days vs the 180 days before. Pre-switch revenue counts as captured, as DefiLlama labels it.

**Rating**
- **Buy:** G_obs ≥ G_req, and H1b passes.
- **Avoid:** G_obs < G_req / 2, and H1b fails.
- **Hold:** anything else.

We publish the rating that this rule produces, including when it contradicts our priors.
