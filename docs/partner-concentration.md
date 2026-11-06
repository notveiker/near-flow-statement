# Partner concentration: how much of NEAR's Intents revenue depends on a few channels?

Window: 30 days, 2026-10-06 → 2026-11-04 (UTC). Every number marked with an `n:` comment is checked against `data/metrics.json` by `make reproduce`.

**Sources**
- **1Click swaps:** `data/raw/explorer/daily.json`, broken down by channel. SwapKit is split by its downstream wallet (Ledger, Trust, Tangem and others).
- **On-chain events:** three BigQuery queries over `intents.near` events:
  - `sql/buyback_withdraw_sources.sql`: who delivers NEAR to the revenue wallets.
  - `sql/collector_inflows.sql`: what NEAR's two fee collectors receive.
  - `sql/revenue_wallet_inflows.sql`: the revenue-wallet totals.
- **Token prices:** CoinGecko daily (`data/raw/coingecko/majors_90d.json`).

## Answer

**The 1Click fee revenue we can trace barely depends on the channel with the most volume. Most of the NEAR the buyback wallet receives cannot be traced to any channel on chain, so that part of the exposure is unknown, not zero.**

| If SwapKit stopped routing through 1Click | Share of NEAR's captured Intents revenue lost |
|---|---|
| Traceable streams (explicit fees + quote-improvement share, pro rata) | 2.0 <!--n:swapkit_exit_traceable_pct-->% |
| Ceiling (also counting all NEAR delivered by the market maker, source unknown) | 43.0 <!--n:swapkit_exit_ceiling_pct-->% |

The volume exposure is larger and certain. SwapKit routes 38.2 <!--n:swapkit_vol_share_pct-->% of 1Click volume, about 21.1 <!--n:swapkit_share_of_intents_net_pct-->% of all Intents volume (one-sided). Every bull case cites Intents' volume share against THORChain, Chainflip and Maya, so losing SwapKit would hit the volume narrative much harder than the revenue line.

## 1. Volume is spread out, but NEAR's explicit fees are concentrated elsewhere

- **Volume:** concentration across channels is low, with an HHI of 0.087 <!--n:volume_channel_hhi-->. SwapKit's sub-channels are the largest single block.
- **SwapKit fees:** SwapKit's partners listed $3,528.9 <!--n:swapkit_partner_fees_usd_k-->K of fees. NEAR's buyback wallet got **$159 <!--n:swapkit_buyback_fees_usd-->** explicitly over 30 days.
- **NEAR's explicit 1Click fees** are concentrated in different channels, with an HHI of 0.244 <!--n:buyback_fee_hhi-->:
  - **No referrer:** 45.8 <!--n:buyback_fee_unreferred_share_pct-->% comes from swaps with no referral, meaning integrators on the default fee.
  - **Top three channels:** the top three account for 65.0 <!--n:buyback_fee_top3_share_pct-->%. They are no-referrer swaps, Trust Wallet's direct integration, and one unnamed integrator charging 71 bp on 0.4% of volume.

**One wallet, two integrations.** Trust Wallet routes through 1Click two ways:

| Route | Share of 1Click volume | To Trust | To NEAR's buyback wallet |
|---|---|---|---|
| Direct (`trustwallet` referral) | 2.4 <!--n:trust_direct_vol_share_pct-->% | 0.0 <!--n:trust_direct_partner_bp-->bp | 20.0 <!--n:trust_direct_buyback_bp-->bp |
| Via SwapKit (`trustswapkit.near`) | 6.4 <!--n:trust_via_swapkit_vol_share_pct-->% | 70.0 <!--n:trust_via_swapkit_partner_bp-->bp | 0.0 <!--n:trust_via_swapkit_buyback_bp-->bp |

Most of Trust's volume goes through the route that pays NEAR nothing.

## 2. Where the buyback wallet's NEAR actually comes from

Every NEAR inflow to `buybacks.multisignature.near` in the window was a `native_withdraw` from `intents.near`. There are three sources:

| Source | Delivered, USD K | What it is | Check |
|---|---|---|---|
| Collector A (`5880ad2b…`) | 460.4 <!--n:bb_from_collector_a_usd_k--> | Receives the explicit buyback appFee on each 1Click swap. On sampled LI.FI swaps it received exactly the listed 5.0 bp | Its 30-day token inflows, valued at daily prices, total $435.0 <!--n:collector_a_inflow_usd_k-->K. That is 96.5 <!--n:collector_a_vs_explicit_fees_pct-->% of the explicit fees in the Explorer fee lists, with 87.8 <!--n:collector_a_valued_transfers_pct-->% of transfers priced |
| Collector B (`143f2bb4…`) | 108.6 <!--n:bb_from_collector_b_usd_k--> | Receives a variable cut (sampled: 44 bp, 11 bp and 1.5 bp of output). This is consistent with the documented 50/50 split of quote improvement, and it applies to partner swaps too, including ZODL | Inflows valued at $104.2 <!--n:collector_b_inflow_usd_k-->K |
| Single-use accounts, funded almost entirely by one market maker (`51e8f94d…`) | 823.7 <!--n:bb_from_mm_singleuse_usd_k--> | One account (it traded with solvers about 200K times in the window) sends wNEAR to a fresh account, which withdraws it to the wallet. The same path delivers nearly all of `fefundsadmin`'s inflows. Of the 298.8K NEAR that single-use accounts sent to the two wallets, this account had funded 298.0K. Payment for this NEAR is not visible on `intents.near` | Not attributable on chain |

The single-use path is 59.1 <!--n:bb_from_mm_singleuse_share_pct-->% of the buyback wallet's inflow. Its funding sits off this ledger. Candidates are near.com fees (NEAR says near.com sends 100% of fees to buybacks), 1Click platform fees collected outside the appFees list, and partner revenue-share settlements. Only the last would tie this stream to SwapKit, which is why the ceiling above is a ceiling.

**What changed from yesterday's note.** `docs/intents-fee-flows.md` treated the $942K the buyback wallet received beyond explicit fees as possibly hidden partner fees. Most of it ($824K) arrives by a separate purchase path, and about $109K is quote-improvement sharing that NEAR earns on every 1Click swap, partner swaps included. The 22.4% ceiling on NEAR's share of partner fees still holds, but the real figure is probably far lower.

**On-chain confirmation for ZODL.** On a sampled $13.0K ZODL swap, ZODL's own account received exactly 67 bp of the input. NEAR received a quote-improvement cut and no fee share.

## Limits

- **Sampling:** collector identities and fee behaviour come from about 180 sampled swaps on 2026-11-05/06 plus the 30-day aggregates. The 30-day totals reconcile, but the sample is small.
- **Pro-rata assumption:** we allocate collector B's quote improvement to SwapKit by volume share. A real allocation needs a per-swap join; Explorer `intentHashes` match on-chain events for only part of the sample.
- **Unpriced tokens:** they are left out of the collector values (12% of collector A's transfers by count, 9% of collector B's), so both figures are lower bounds.
