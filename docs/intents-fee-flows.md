# Who earns from NEAR Intents, and does it touch the NEAR token?

Window: 30 days, 2026-10-06 → 2026-11-04 (UTC). Every number marked `<!--n:…-->` in this file is checked against `data/metrics.json` by `make reproduce`.

**Sources**
- **1Click swaps:** successful swaps from the NEAR Intents Explorer API (`pipeline/fetch_explorer.py`), aggregated per day into `data/raw/explorer/daily.json`.
- **Revenue wallets:** native NEAR arriving at NEAR's three Intents revenue wallets from outside that set (`sql/revenue_wallet_inflows.sql`, BigQuery). wNEAR inflows were checked too (`sql/revenue_wallet_wnear_inflows.sql`) and were zero.
- **Benchmark:** DefiLlama's near-intents adapter, which defines revenue the same way ([source](https://github.com/DefiLlama/dimension-adapters/blob/master/fees/near-intents/index.ts)).
- **Fee rules:** [docs.near-intents.org/resources/fees](https://docs.near-intents.org/resources/fees) and [the 1Click fee-config page](https://docs.near-intents.org/integration/distribution-channels/1click-api/fee-config), read 2026-11-05.

## What we can conclude

### 1. NEAR's captured revenue is measured, and it reconciles

NEAR's revenue wallets received **418.8 <!--n:revwallets_near_k-->K NEAR** over the window, worth $2,009.7 <!--n:revwallets_usd_k-->K at daily prices. That is 100.9 <!--n:revwallets_vs_llama_rev_pct-->% of DefiLlama's reported revenue for the same days. Every inflow came from `intents.near`: purchased NEAR, withdrawn natively.

| Wallet | USD K | Share |
|---|---|---|
| `buybacks.multisignature.near` (1Click, partner shares, other) | 1,392.8 <!--n:revwallets_buybacks_usd_k--> | |
| `fefundsadmin.sputnik-dao.near` (NEAR's own front ends) | 616.9 <!--n:revwallets_frontend_usd_k--> | 30.7 <!--n:revwallets_frontend_share_pct-->% |

This corrects one of our own pre-freeze observations. "Buyback wallet = 68.5% of implied buybacks" compared one wallet with revenue measured across three wallets. The rest is mostly sitting in `fefundsadmin`, not missing. See `PREREG-ADDENDUM.md`.

### 2. Distribution channels keep more Intents fee value than NEAR does

- **Total fees listed:** 1Click swaps listed $4,454.2 <!--n:explorer_partner_fees_all_usd_k-->K of app fees to partner accounts, meaning wallets and front ends. NEAR's buyback wallet is excluded from that total.
- **Swaps with no buyback entry:** most of those fees, $4,212.6 <!--n:explorer_partner_fees_no_bb_usd_k-->K, came on swaps whose fee list had no buyback entry at all. These are SwapKit (Ledger, Trust, Tangem), ZODL and Vizor.

The fee docs say an integrator's fee is split 50/50 with 1Click by default, but "exceptions and custom agreements exist." So a fee list like `[ledgerswapkit.near: 145]` could mean Ledger keeps all 145 bp, or keeps about 72 and NEAR gets about 72.

The revenue wallets settle which reading holds:
- **Explicit entries:** they account for $450.6 <!--n:explorer_appfees_to_buybacks_usd_k-->K of the buyback wallet's inflow.
- **Unexplained:** this leaves $942.2 <!--n:buybacks_unexplained_usd_k-->K. Even if all of it came from partners with no buyback entry, NEAR's share of their fees is at most **22.4 <!--n:near_share_of_partner_fees_max_pct-->%**. A default 50/50 split would have added about $2.1M on top of the explicit entries, but the buyback wallet received only $1.39M in total. (Update: [`partner-concentration.md`](partner-concentration.md) tightens this ceiling to 19.6 <!--n:near_share_of_partner_fees_max_tight_pct-->%.)
- **Conclusion:** the default split does not apply to these partners.

Over the window, partners kept between **1.75 <!--n:partners_kept_vs_near_rev_low_x-->×** and **2.22 <!--n:partners_kept_vs_near_rev_high_x-->×** NEAR's entire captured Intents revenue. That figure counts only the 1Click half of Intents.

Why it matters: the bull case treats Intents fee revenue as value flowing to NEAR. On this evidence, the distribution layer (hardware and mobile wallets) captures most of the fee economics. NEAR's take is set by negotiation with a handful of partners, and SwapKit alone routes 38.2% of 1Click volume.

### 3. Users pay the listed fee plus an execution cost

On swaps of $1K–$50K, the realized cost (`amountInUsd − amountOutUsd`) exceeds the listed fees by **8.5 <!--n:explorer_excess_over_listed_bp-->bp** on average. That excess includes the solver or market-maker spread, destination-chain gas and the 1-pip protocol fee, so it is an execution cost, not a pure solver take. It appears in no one's revenue model. The per-bucket figures in `explorer_realized_cost_by_listed_bp` mostly reflect asset mix (BTC routes cost more to fill than stablecoin routes), not fee tier. Two details:
- **Swaps listing 81 bp or more** (mostly Ledger via SwapKit): the listed fee averages about 141 bp and the realized cost about 149 bp. The listed fee is the whole platform charge; no hidden 1Click fee is added on top.
- **Swaps listing under 2 bp** (mostly stablecoin routes): the listed fee averages under 1 bp and the realized cost about 2 bp.

### 4. Intents volume barely touches the NEAR token

| | Value |
|---|---|
| Share of 1Click volume with NEAR as one leg (NEAR appears only as `nep141:wrap.near`; checked) | 2.2 <!--n:explorer_near_leg_share_pct-->% |
| Share of volume legs in stablecoins | 47.4 <!--n:explorer_stablecoin_leg_share_pct-->% |
| Swaps into NEAR, USD M | 14.6 <!--n:explorer_into_near_usd_m--> |
| Swaps out of NEAR, USD M | 24.0 <!--n:explorer_out_of_near_usd_m--> |
| Net NEAR sold through 1Click, USD M | 9.4 <!--n:explorer_net_near_sold_usd_m--> |

Intents is a cross-chain stablecoin, BTC and ZEC venue. Usage creates no direct demand for NEAR. The only link is the buyback, and NEAR is fungible, so we make no claim about who the sellers were. Still, 1Click was a net *exit* route for NEAR, about 4.7× NEAR's entire captured revenue (all three wallets) in the same window. This route is non-custodial, so PREREG's exchange-flow test (H1b), which counts only labelled centralized-exchange accounts, does not see it.

### 5. Volume is whale-driven

Swaps of $10K or more are 3.4 <!--n:explorer_swaps_10k_plus_n_pct-->% of swaps but 77.1 <!--n:explorer_swaps_10k_plus_vol_pct-->% of volume. The median swap is about $52. Revenue is therefore exposed to a small number of large users, whose fee rates vary by channel.

## What we cannot conclude yet

- **The other half of Intents.** 1Click is 55.2 <!--n:explorer_vs_llama_net_pct-->% of DefiLlama's volume on a one-sided basis. The rest (near.com, direct solver flow, other integrations) has a fee structure this API does not show. We do not extrapolate.
- **What makes up the $942K.** Partly answered in [`partner-concentration.md`](partner-concentration.md). About $109K is quote-improvement sharing. About $824K is NEAR delivered by a market maker through single-use accounts, and it is paid for off this ledger.
- **Partner payouts on chain.** Fee recipients such as `ledgerswapkit.near` never appear in `intents.near` event logs over 2026-10-28 → 11-04. Partner fees are settled some other way, so "partner kept X" is an inference from the revenue wallets, not a direct payout trace.

## Open questions this raises

1. **Partner concentration risk.** If SwapKit renegotiates or leaves, how much of NEAR's captured revenue goes with it? This needs per-channel buyback attribution.
2. **Can NEAR raise its take?** Trace NEAR's take rate over time against partner fee lists, since the fee switch on 2026-02-23. Explorer history makes this possible.
3. **Who are the net NEAR sellers on 1Click?** Origin addresses on NEAR→X swaps could be matched against unstaking accounts from the H1a analysis. That would be a market-wide overlap, not an attribution.
4. **Is ZEC volume (10.9% of legs) durable,** or a privacy-coin cycle?
