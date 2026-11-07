# Who earns from NEAR Intents, and does it touch the NEAR token?

Window: 30 days, 2026-10-06 → 2026-11-04 (UTC). Every number marked `<!--n:…-->` in this file is checked against `data/metrics.json` by `make reproduce`.

**Sources**
- **1Click swaps:** successful swaps from the NEAR Intents Explorer API (`pipeline/fetch_explorer.py`), aggregated per day into `data/raw/explorer/daily.json`.
- **Revenue wallets:** native NEAR arriving at NEAR's three Intents revenue wallets from outside that set (`sql/revenue_wallet_inflows.sql`, BigQuery). A wNEAR check (`sql/revenue_wallet_wnear_inflows.sql`) returned zero rows, but it reads `ft_events`, which appears not to record `wrap.near` transfers at all (no rows on a busy day), so that zero is uninformative. The evidence that wNEAR inflows are negligible is instead the reconciliation: our native-only total is 100.9% of DefiLlama's revenue, which counts native NEAR and wNEAR.
- **Benchmark:** DefiLlama's near-intents adapter, which defines revenue the same way ([source](https://github.com/DefiLlama/dimension-adapters/blob/master/fees/near-intents/index.ts)).
- **Fee rules:** [docs.near-intents.org/resources/fees](https://docs.near-intents.org/resources/fees) and [the 1Click fee-config page](https://docs.near-intents.org/integration/distribution-channels/1click-api/fee-config), read 2026-11-05.

## What we can conclude

### 1. NEAR's captured revenue is measured, and it reconciles

NEAR's revenue wallets received **418.8 <!--n:revwallets_near_k-->K NEAR** over the window, worth $2,009.7 <!--n:revwallets_usd_k-->K at daily prices. That is 100.9 <!--n:revwallets_vs_llama_rev_pct-->% of DefiLlama's reported revenue for the same days. Every inflow came from `intents.near` as a native withdrawal. **The buyback NEAR is held, not burned:** on 2026-11-06 `buybacks.multisignature.near` held 2,202,267.81 NEAR (block 223,382,146), none of it staked, and its all-time outflows total about 12,025 NEAR (25 to `nf-payments.near`, 12,000 that reached `bridge-mng.near`). Neither the balance nor the outflow total is in the committed snapshots, so `make reproduce` does not check them. The balance can be re-read without a key with `view_account` on FastNEAR's archival RPC at that block; the outflow total cannot be recomputed from the committed data.

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
- **Conclusion:** at most about a fifth of these partners' fees could be reaching NEAR's wallets. Per-swap evidence now shows why: partners are paid their **full** listed fee on chain (see [`partner-concentration.md`](partner-concentration.md)), so no 50/50 split is taken out of it. Any 1Click charge on these swaps would have to come on top of the listed fee, inside the execution cost in section 3, and whether Intents Technology forwards any of it to NEAR's wallets is not visible. The 1Click terms let it retain fees "for its own account" (Schedule 1 §6.2, for confidential swaps).

Over the window, partners kept between **1.75 <!--n:partners_kept_vs_near_rev_low_x-->×** and **2.22 <!--n:partners_kept_vs_near_rev_high_x-->×** NEAR's entire captured Intents revenue. That figure counts only the 1Click half of Intents.

Why it matters: the bull case treats Intents fee revenue as value flowing to NEAR. On this evidence, the distribution layer (hardware and mobile wallets) captures most of the fee economics. NEAR's take appears to depend on partner terms and on what Intents Technology forwards (an inference from the wallet arithmetic, not a documented policy), and SwapKit alone routes 38.2% of 1Click volume.

### 3. Users pay the listed fee plus an execution cost

On swaps of $1K–$50K, the realized cost (`amountInUsd − amountOutUsd`) exceeds the listed fees by **8.5 <!--n:explorer_excess_over_listed_bp-->bp** on average. That excess includes the solver or market-maker spread, destination-chain gas and the 1-pip protocol fee, so it is an execution cost, not a pure solver take. It appears in no one's revenue model. The per-bucket figures in `explorer_realized_cost_by_listed_bp` mostly reflect asset mix (BTC routes cost more to fill than stablecoin routes), not fee tier. Two details:
- **Swaps listing 81 bp or more** (mostly Ledger via SwapKit): the listed fee averages about 141 bp and the realized cost about 149 bp. The listed fee is the whole platform charge; no hidden 1Click fee is added on top.
- **Swaps listing under 2 bp** (mostly stablecoin routes): the listed fee averages under 1 bp and the realized cost about 2 bp.

### 4. Intents volume barely touches the NEAR token

| | Value |
|---|---|
| Share of 1Click volume in swaps with NEAR on one side (NEAR appears only as `nep141:wrap.near`; checked) | 3.5 <!--n:explorer_near_side_swap_share_pct-->% |
| NEAR's share of volume legs (each swap's value split half to each leg) | 2.2 <!--n:explorer_near_leg_share_pct-->% |
| Share of volume legs in stablecoins | 47.4 <!--n:explorer_stablecoin_leg_share_pct-->% |
| Swaps into NEAR, USD M | 14.6 <!--n:explorer_into_near_usd_m--> |
| Swaps out of NEAR, USD M | 24.0 <!--n:explorer_out_of_near_usd_m--> |
| Net NEAR sold through 1Click, USD M | 9.4 <!--n:explorer_net_near_sold_usd_m--> |

Intents is a cross-chain stablecoin, BTC and ZEC venue. Usage creates no direct demand for NEAR. The only link is the buyback, and NEAR is fungible, so we make no claim about who the sellers were. Still, 1Click was a net *exit* route for NEAR, about 4.7× NEAR's entire captured revenue (all three wallets) in the same window. This route is non-custodial, so PREREG's exchange-flow test (H1b), which counts only labelled centralized-exchange accounts, does not see it.

### 5. Volume is whale-driven

Swaps of $10K or more are 3.4 <!--n:explorer_swaps_10k_plus_n_pct-->% of swaps but 77.1 <!--n:explorer_swaps_10k_plus_vol_pct-->% of volume. The median swap is about $52. Revenue is therefore exposed to a small number of large users, whose fee rates vary by channel.

### 6. NEAR's take inside 1Click doubled over 90 days, and partners still keep ten to eighteen times more

Three 30-day blocks of 1Click swaps (Explorer API), 2026-08-07 → 11-04:

| | Aug 7 – Sep 5 | Sep 6 – Oct 5 | Oct 6 – Nov 4 |
|---|---|---|---|
| 1Click volume, USD M | 1,269 <!--n:take_b1_oneclick_usd_m--> | 1,442 <!--n:take_b2_oneclick_usd_m--> | 1,104 <!--n:take_b3_oneclick_usd_m--> |
| Explicit buyback fee, bp of volume | 1.83 <!--n:take_b1_bb_explicit_bp--> | 2.84 <!--n:take_b2_bb_explicit_bp--> | 4.08 <!--n:take_b3_bb_explicit_bp--> |
| Partner fees, bp of volume | 32.5 <!--n:take_b1_partner_bp--> | 43.7 <!--n:take_b2_partner_bp--> | 40.3 <!--n:take_b3_partner_bp--> |
| Share of volume with a buyback fee entry | 23.6 <!--n:take_b1_vol_with_bb_pct-->% | 39.0 <!--n:take_b2_vol_with_bb_pct-->% | 43.0 <!--n:take_b3_vol_with_bb_pct-->% |
| SwapKit's share of volume | 35.6 <!--n:take_b1_swapkit_vol_pct-->% | 37.9 <!--n:take_b2_swapkit_vol_pct-->% | 38.2 <!--n:take_b3_swapkit_vol_pct-->% |
| Captured revenue ÷ reported Intents volume (DefiLlama), bp | 2.89 <!--n:take_b1_captured_bp--> | 4.25 <!--n:take_b2_captured_bp--> | 4.98 <!--n:take_b3_captured_bp--> |

- **NEAR's explicit take rose mainly because more volume carries a buyback fee entry**, not because SwapKit's share fell. The share of volume with an entry nearly doubled.
- **Partners' fees stayed between about ten and eighteen times NEAR's explicit fee**: about 17.8, 15.4 and 9.9 times in the three blocks, from the two fee rows above.
- **Captured take on DefiLlama's basis rose too**, from 2.89 to 4.98 bp. The first block is not like-for-like: DefiLlama's volume series steps up on 2026-09-01. 1Click's share of it falls from 86.2 <!--n:oneclick_share_of_llama_week_before_0901_pct-->% in the week before to 60.8 <!--n:oneclick_share_of_llama_week_after_0901_pct-->% in the week from that day, with no matching change in 1Click's own volume. That is consistent with DefiLlama counting more of Intents' volume (for example confidential swaps) from that date. If so, pre-09-01 volume is understated and the first block's 2.89 bp overstated, so the true rise is, if anything, larger.
- **Scope.** This covers 90 days, not the whole period since the 2026-02-23 fee switch.

## What we cannot conclude yet

- **The other half of Intents.** 1Click is 55.2 <!--n:explorer_vs_llama_net_pct-->% of DefiLlama's volume on a one-sided basis. (DefiLlama's figure counts both sides of each swap: from January to August 2026 it matched an independent both-sides total at 1.004-1.017×, not 0.5×, so halving it is right and, for multi-hop swaps, slightly conservative. The Dune query behind it could not be read directly.) The rest (near.com, direct solver flow, other integrations) has a fee structure this API does not show. We do not extrapolate.
- **What makes up the $942K.** Partly answered in [`partner-concentration.md`](partner-concentration.md). About $109K is quote-improvement sharing. About $824K is NEAR unshielded from the Confidential Intents escrow (`PRIVATE_TREASURY_ACCOUNT_ID` in NEAR's docs) to fresh accounts; the fee stream behind it is private and unattested.
- **Partner payouts on chain (corrected 2026-11-07).** An earlier version said partner fees were settled off this ledger, because the named recipients (`ledgerswapkit.near` and so on) never appear in the logs. They are paid on chain to implicit accounts instead, at the listed rate. "Partner kept X" now rests on per-swap payouts in a sample, not only on wallet arithmetic.

## Open questions this raises

1. **Partner concentration risk.** If SwapKit renegotiates or leaves, how much of NEAR's captured revenue goes with it? This needs per-channel buyback attribution.
2. **Can NEAR raise its take?** Partly answered in section 6: over 90 days, NEAR's explicit take inside 1Click doubled, mostly because more volume carries a buyback fee entry. The period since the 2026-02-23 fee switch is not yet covered.
3. **Who are the net NEAR sellers on 1Click?** Origin addresses on NEAR→X swaps could be matched against unstaking accounts from the H1a analysis. That would be a market-wide overlap, not an attribution.
4. **Is ZEC volume (10.9% of legs) durable,** or a privacy-coin cycle?
