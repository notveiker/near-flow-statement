# Partner concentration: how much of NEAR's Intents revenue depends on a few channels?

Window: 30 days, 2026-10-06 → 2026-11-04 (UTC). Every number marked with an `n:` comment is checked against `data/metrics.json` by `make reproduce`. **Everything in this file is exploratory (chosen after the freeze); none of it is a pre-registered test.** A number that was already in `PREREG.md`'s "What we had already seen" table is marked as a pre-freeze observation where it appears.

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
| Traceable streams (explicit fees + quote-improvement share, pro rata) | 2.0<!--n:swapkit_exit_traceable_pct-->% |
| Ceiling (also counting all NEAR unshielded from the Confidential Intents escrow to the buyback wallet, fee stream unattested) | 43.0<!--n:swapkit_exit_ceiling_pct-->% |
| Wider ceiling (the same logic applied to the escrow-path NEAR that reached `fefundsadmin` too) | 73.7<!--n:swapkit_exit_ceiling_all_escrow_pct-->% |

SwapKit routes 38.2<!--n:swapkit_vol_share_pct-->% of 1Click volume, about 21.1<!--n:swapkit_share_of_intents_net_pct-->% of all Intents volume (one-sided). Its share of NEAR's revenue is between 2.0<!--n:swapkit_exit_traceable_pct-->% (what traces to it) and 43.0<!--n:swapkit_exit_ceiling_pct-->% (the ceiling; 73.7<!--n:swapkit_exit_ceiling_all_escrow_pct-->% if the escrow NEAR reaching the front-end fund is counted too), so the revenue line may be exposed to a similar or larger degree; the data cannot say.

## 1. Volume is spread out, but NEAR's explicit fees are concentrated elsewhere

- **Volume:** with SwapKit counted as one channel, as it is one exit risk, volume concentration is moderate to high: HHI 0.200<!--n:volume_channel_hhi_swapkit_merged-->. Split into its downstream wallets it looks spread out (HHI 0.087<!--n:volume_channel_hhi-->), but that split hides the dependency.
- **SwapKit fees:** SwapKit's partners listed $3,528.9<!--n:swapkit_partner_fees_usd_k-->K of fees. NEAR's buyback wallet got **$159<!--n:swapkit_buyback_fees_usd-->** explicitly over 30 days.
- **NEAR's explicit 1Click fees** are concentrated in different channels, with an HHI of 0.244<!--n:buyback_fee_hhi-->:
  - **No referrer:** 45.8<!--n:buyback_fee_unreferred_share_pct-->% comes from swaps with no referral, meaning integrators on the default fee.
  - **Top three channels:** the top three account for 65.0<!--n:buyback_fee_top3_share_pct-->%. They are no-referrer swaps, Trust Wallet's direct integration, and one unnamed integrator charging 71 bp on 0.4% of volume.

**One wallet, two integrations.** A referral labelled `trustwallet` and the fee account `trustswapkit.near` look like two routes for the same wallet:

| Route | Share of 1Click volume | To Trust | To NEAR's buyback wallet |
|---|---|---|---|
| Direct (`trustwallet` referral) | 2.4<!--n:trust_direct_vol_share_pct-->% | 0.0<!--n:trust_direct_partner_bp--> bp | 20.0<!--n:trust_direct_buyback_bp--> bp |
| Via SwapKit (`trustswapkit.near`) | 6.4<!--n:trust_via_swapkit_vol_share_pct-->% | 70.0<!--n:trust_via_swapkit_partner_bp--> bp | 0.0<!--n:trust_via_swapkit_buyback_bp--> bp |

Most of Trust's volume goes through the route that pays NEAR nothing.

## 2. Where the buyback wallet's NEAR actually comes from

Every NEAR inflow to `buybacks.multisignature.near` in the window was a `native_withdraw` from `intents.near`. There are three sources:

| Source | Delivered, USD K | What it is | Check |
|---|---|---|---|
| Collector A (`5880ad2b…`) | 460.4<!--n:bb_from_collector_a_usd_k--> | Receives the explicit buyback appFee. In the in-window sample it received the listed rate (within 0.6%) on 59<!--n:fee_ev_bb_paid_exact_n--> of 61<!--n:fee_ev_bb_listed_n--> swaps listing a buyback fee, and nothing on any of the 134<!--n:fee_ev_unlisted_n--> swaps without one (0<!--n:fee_ev_unlisted_collector_a_paid_n-->). The other two swaps listing a buyback fee are the swaps whose tokens went into the Confidential Intents escrow, where the public chain shows no fee movement: unseen there, not shown unpaid | Its 30-day token inflows, valued at daily prices, total $435.0<!--n:collector_a_inflow_usd_k-->K. That is 96.5<!--n:collector_a_vs_explicit_fees_pct-->% of the explicit fees in the Explorer fee lists, with 87.8<!--n:collector_a_valued_transfers_pct-->% of transfers priced |
| Collector B (`143f2bb4…`) | 108.6<!--n:bb_from_collector_b_usd_k--> | Receives a variable cut of the output on a minority of swaps across all channels: 43<!--n:fee_ev_collector_b_swaps_n--> of the 195<!--n:fee_ev_swaps_n--> sampled, including 9<!--n:fee_ev_collector_b_swapkit_swaps_n--> SwapKit swaps, at a median 1.13<!--n:fee_ev_collector_b_bp_median--> bp of output (up to 30.5<!--n:fee_ev_collector_b_bp_max--> bp). This fits the documented 50/50 split of quote improvement, which is paid only when a fill beats its quote; that role is inferred, since the Explorer API does not report the quote | Inflows valued at $104.2<!--n:collector_b_inflow_usd_k-->K |
| Unshields from the Confidential Intents escrow (`51e8f94d…`) | 823.7<!--n:bb_from_escrow_unshield_usd_k--> | `51e8f94d…7cbe` is the Confidential Intents treasury, which NEAR's docs list as `PRIVATE_TREASURY_ACCOUNT_ID`, "a production constant shared by all participants". On chain, an unshield (private → public) shows as the escrow releasing the exact amount to a fresh account, which withdraws it to the wallet (an observation: the documentation describes the release from the Treasury, not this pattern). The same path delivers nearly all of `fefundsadmin`'s inflows. In the window, all 909<!--n:escrow_funded_exact_30d_n--> single-use deliveries were funded by the escrow for the exact amount, to the yocto (100.0<!--n:escrow_funded_exact_30d_pct-->%). Every delivery is listed in `data/raw/escrow/deliveries.csv`, with its funding transfer for every delivery in the 30-day window and for a traced sample before it, and `python3 -m pipeline.fetch_escrow verify` re-checks them against the chain. This is consistent with a privacy feature working as documented | Arrival is on chain; the fee stream behind it is not |

Escrow unshields are 59.1<!--n:bb_from_escrow_unshield_share_pct-->% of the buyback wallet's inflow. The NEAR arrives on chain, but which fee stream it comes from happens in private mode and cannot be seen from outside. Two candidate readings fit, and the public chain cannot tell them apart:
- **near.com front-end fees.** NEAR's Confidential Intents docs say near.com keeps two balances per account, Main (on `intents.near`) and Confidential (on `intents.far`). revenue.near.org says near.com swaps "direct 100% of fees to a NEAR revenue wallet", without naming which one; the same answer says swaps through third-party partners are "split 50/50 between NEAR and the partner", which the arithmetic in this file tests. near.com's live code names three fee-related accounts, of which we discuss two (the third, `APP_FEE_DISTRIBUTOR`, is not discussed): `APP_FEE_RECIPIENT` (`176121bd…`), which withdrew to `fefundsadmin` in every delivery of it in our table and to the buyback wallet in none, and `CONFIDENTIAL_FEE_RECIPIENT` (`60a0d43b…`), which appears nowhere in FastNEAR's public index of the chain, so where its fees go cannot be seen. Calling them the public-mode and confidential-mode accounts is our reading of the names.
- **The Confidential Infrastructure Fee.** The 1Click terms (Schedule 1 §6.2 and §6.4) say Intents Technology "sets, charges, and retains" this fee on confidential swaps, with no AppFee and no share to the integrator.

Neither reading ties this stream to SwapKit. The ledger still cannot exclude a partner settlement routed through private mode, which is why the ceiling above is a ceiling.

**What changed from the first fee-flow note.** `docs/intents-fee-flows.md` treated the $942K the buyback wallet received beyond explicit fees as possibly hidden partner fees. Most of it ($824K) arrives as unshields from the Confidential Intents escrow, and about $109K is quote-improvement sharing (an inferred role), which would not be a fee share. That tightens the ceiling on NEAR's share of fees on partner swaps with no buyback entry from 22.4<!--n:near_share_of_partner_fees_max_pct-->% to **19.6<!--n:near_share_of_partner_fees_max_tight_pct-->%**. On that basis partners kept at least 1.81<!--n:partners_kept_vs_near_rev_low_tight_x-->× NEAR's captured revenue.

**Two readings of one bound.** The wide reading (at most 22.4<!--n:near_share_of_partner_fees_max_pct-->% of those partners' fees reaches NEAR's buyback wallet; partners kept at least 1.75<!--n:partners_kept_vs_near_rev_low_x-->× NEAR's captured revenue) counts all of the $942.2<!--n:buybacks_unexplained_usd_k-->K that the explicit buyback entries do not explain as possibly coming out of partner fees. The tight reading (19.6<!--n:near_share_of_partner_fees_max_tight_pct-->%; 1.81<!--n:partners_kept_vs_near_rev_low_tight_x-->×) also treats collector B's $108.6<!--n:bb_from_collector_b_usd_k-->K as quote improvement rather than a fee share, so only the $823.7<!--n:bb_from_escrow_unshield_usd_k-->K of escrow NEAR could be partner money. Collector B's role is inferred, not proven (see the Collector B row above), so the wide reading is the one to quote. Neither reading counts the front-end fund's NEAR (`fefundsadmin`, fed by the same escrow path) as partner money; counting it would loosen both bounds.

Neither candidate reading of the escrow stream (near.com's fees, the Confidential Infrastructure Fee) is established: NEAR does not name the wallet that near.com's fees go to, and the Terms say who would keep a Confidential Infrastructure Fee, not that one is charged or forwarded to NEAR's wallets. `fefundsadmin` (NEAR's own front-end fund) is fed by the same escrow path. No public source ties the $824K to near.com or to any named fee stream, so we offer no likeliest reading. The ledger cannot tell 0% from about 20% for SwapKit. For ZODL it can: the next paragraph shows no hidden split.

**Partners are paid their listed fee on chain, in the per-swap sample.** The sample is 195<!--n:fee_ev_swaps_n--> swaps from 3<!--n:fee_ev_hours_with_swaps_n--> sampled hours (see Limits), so it says nothing about the other hours. A listed partner fee counts as paid when some token movement in the swap carries the input amount times the listed rate (within 0.6%, and at least two raw units) to an account that is neither collector. That holds for 102<!--n:fee_ev_swapkit_fees_paid_onchain_n--> of 112<!--n:fee_ev_swapkit_fees_listed_n--> SwapKit fee entries, 9<!--n:fee_ev_zodl_fees_paid_onchain_n--> of 9<!--n:fee_ev_zodl_fees_listed_n--> ZODL entries and 79<!--n:fee_ev_other_partner_fees_paid_onchain_n--> of 83<!--n:fee_ev_other_partner_fees_listed_n--> entries of other channels. The entries that do not match are not unpaid fees:
- 10<!--n:fee_ev_swapkit_fees_zero_rate_n--> SwapKit entries and 3<!--n:fee_ev_other_partner_fees_zero_rate_n--> entries of other channels list a zero rate (13 in all; ZODL has 0<!--n:fee_ev_zodl_fees_zero_rate_n-->). Nothing is owed on them, and a zero amount can never match a payment.
- 1<!--n:fee_ev_partner_fees_nonzero_unmatched_n--> entry lists a non-zero rate and is unmatched. It is in a swap whose tokens went into the Confidential Intents escrow (`51e8f94d…`; 1<!--n:fee_ev_partner_fees_nonzero_unmatched_escrow_n--> of the unmatched non-zero entries is escrow-routed), where the public chain shows no fee movement. The fee is unseen there, not shown unpaid.

So, outside the escrow route, every listed partner fee with a non-zero rate is matched in this sample, and in this sample no split is taken out of a listed partner fee. This does not show what 1Click charges on top of the listed fee, and whether it forwards any of that to NEAR is not visible. Nor does it show who owns the receiving account. Partners are usually paid to an implicit account, not the name in the fee list: Ledger's 145 bp goes to `c4d748df…`, Trust's 70<!--n:trust_via_swapkit_partner_bp--> bp to `2f09a4dc…`, ZODL's 67 bp to `d78abd…`. Each such account is the destination that most often received a payment matching that partner's fee (shown in `data/metrics.json` under `fee_ev_partner_fee_accounts` for partners with at least three matches), which is an inference from amounts, not a public statement.

## Limits

- **Sampling:** fee mechanics come from `data/raw/evidence/` (195<!--n:fee_ev_swaps_n--> swaps sampled from hours inside the window, re-traced keylessly with `python3 -m pipeline.fetch_fee_evidence trace`) plus the 30-day aggregates. The 30-day totals reconcile, but three hours of swaps (3<!--n:fee_ev_hours_with_swaps_n--> of the four sampled hours returned swaps) across 55<!--n:fee_ev_channels_n--> channels is a small sample.
- **How the sample was drawn** (`pipeline/fetch_fee_evidence.py`): one page of up to 1,000 successful swaps for each of four fixed hours, keeping only swaps of at least $200 that carry a NEAR transaction, and at most 3 per channel per hour. It is not volume-weighted, so counts and shares in it (for example how many swaps pay collector B) are not rates.
- **Scope of "paid on chain":** it is a statement about the sample above, not about every swap or every hour, and not about 1Click's own charge on top of a listed fee. A listed fee counts as paid when some token movement in the swap is within 0.6% of the input amount times the listed rate (never less than a two-unit tolerance) and goes to an account that is neither collector; the token is not checked, and who owns the receiving account is not shown.
- **Pro-rata assumption:** we allocate collector B's quote improvement to SwapKit by volume share. SwapKit swaps do pay collector B (9<!--n:fee_ev_collector_b_swapkit_swaps_n--> of the 67<!--n:fee_ev_swapkit_swaps_n--> sampled), so the allocation has support, but its size is not measured.
- **Correction (2026-11-07).** An earlier version said SwapKit's fees were invisible on this ledger. That came from searching for the named fee accounts (`ledgerswapkit.near` and so on), which never receive anything: the fees go to implicit accounts, as above.
- **Unpriced tokens:** they are left out of the collector values (12% of collector A's transfers by count, 9% of collector B's), so both figures are lower bounds.
