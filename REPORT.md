# NEAR: where intents settle, and what that earns the token

*Investment Thesis track. Window for value capture: the 30 days to 2026-11-04. Window for supply: the 90 days 2026-08-07 to 2026-11-04. The interactive version is [`dashboard/index.html`](dashboard/index.html); this is the same story in prose. Every figure with an `n:` marker is recomputed from committed data by `make reproduce` and checked by `make check`. Figures marked (derived) show their arithmetic. The longer methods note is [`THESIS.md`](THESIS.md), and the pre-registration is [`PREREG.md`](PREREG.md).*

**Rating from the frozen rule: Hold, with Buy one input away.** The rule was fixed on 2026-11-05 before any flow query. Observed growth in captured revenue, 619.0 <!--n:rating_g_obs_pct-->% a year in USD (about **71%** in NEAR terms — `data/derived/growth_usd_vs_near.json`), is far above the 33.2 <!--n:rating_g_req_pct-->% the rule requires. The rule returns Buy if H1b passes, and H1b is inconclusive for a single reason: only 20.0 <!--n:h1b_coverage_count_pct-->% of the top-100 NEAR receivers carry a citable exchange label, and the rule needs 50%.

## 1. NEAR Intents is the largest venue in its peer set

NEAR Intents carries 55.7 <!--n:intents_share_peerset_30d_pct-->% of the reported volume among the four native cross-chain venues over 30 days, and 62.1 <!--n:intents_share_peerset_365d_pct-->% over 365 days, against THORChain, Chainflip and Maya. Reported volume was $4.0 <!--n:intents_vol_30d_b-->B in the last 30 days and $32.9 <!--n:intents_vol_365d_b-->B over the trailing year. In January 2025 the same series read about $0.01B a month. The venue went from a rounding error to the largest of its peers in under two years. On DefiLlama's NEAR DEX composite, Intents is about **99%** of 30-day volume (`data/derived/intents_vs_near_dex.json`) — the chain's DEX story *is* Intents.

It also prices above the others. Its blended fee was 15.3 bp of volume, against 12.3 bp for THORChain and 9.4 bp for Maya, on more than twice THORChain's volume. Chainflip charges more, 31.5 bp, on a fraction of the volume.

## 2. The fees reach the token, exactly

Over the 30 days NEAR's revenue wallets received 418.8 <!--n:revwallets_near_k-->K NEAR. That total is 100.9 <!--n:revwallets_vs_llama_rev_pct-->% of the Intents revenue DefiLlama reports for the same days, so an independent source reproduces it. Of the deliveries that came out of the confidential escrow, all 909 <!--n:escrow_funded_exact_30d_n--> were funded for the exact amount, to the yoctoNEAR.

Captured revenue was $1.99 <!--n:intents_rev_30d_m-->M in the last 30 days against $9.44 <!--n:intents_rev_365d_m-->M in the trailing 365. Annualised, the last 30 days is about $24.2M (derived: 1.99 × 365 ÷ 30), 2.6 times the trailing year (derived: 24.2 ÷ 9.44). NEAR's explicit take inside 1Click rose from 1.83 <!--n:take_b1_bb_explicit_bp-->bp of volume to 4.08 <!--n:take_b3_bb_explicit_bp-->bp across three consecutive 30-day blocks, as the share of volume carrying a buyback fee went from 23.6 <!--n:take_b1_vol_with_bb_pct-->% to 43.0 <!--n:take_b3_vol_with_bb_pct-->%. Intents revenue was 11.2 <!--n:intents_rev_vs_l1fees_30d_x-->× the base layer's own transaction fees in the same window.

**What it offsets.** NEAR mints 88,295 <!--n:net_issuance_near_per_day_window-->NEAR a day. The NEAR that verifiably reached the three revenue wallets equals 15.81 <!--n:ladder_all_wallets_pct_of_issuance-->% of that, and the buyback wallet alone holds 2.187 <!--n:buyback_wallet_near_m-->M NEAR. It is held, not burned.

## 3. Issuance is scheduled to fall

HSP-029 ramps the annual issuance cap from 2.5% to 1.6% over 24 months, starting one quarter after its timelock ends on 2026-11-16. Net supply growth is 2.46 <!--n:net_supply_growth_30d_annualized_pct-->% a year today. If captured revenue only stays where it is, and issuance falls to the 1.6% cap, the share of issuance that revenue offsets moves from 15.81% to about 24% (derived: 15.81 × 2.46 ÷ 1.6). That is arithmetic on one scenario and ignores any growth in revenue. The dashboard lets you move volume, take, cap and price and see all of it recomputed.

## 4. The market has started to price a different NEAR

Against the majors, NEAR's trailing returns on Binance daily closes to 2026-11-11 are below (from `data/raw/market/`).

| Window | NEAR | ETH | SOL | BTC |
|---|---|---|---|---|
| 90 days | +124.6% | +9.1% | +9.1% | +15.9% |
| 180 days | +138.3% | -7.5% | -6.7% | -7.0% |
| 365 days | +44.5% | -39.8% | -46.2% | -28.6% |

The last 30 days were a pullback for the whole group, NEAR -27.7% against -15.9% for ETH, -21.3% for SOL and -10.1% for BTC. NEAR's perpetual futures funding averaged about 0.006% per eight hours over 90 days, the long-short account ratio is 1.36, and open interest is $163M (down about **42%** from ~$280M thirty daily points earlier — deleveraging into the pullback; `data/derived/perps_positioning.json`). Binance spot trades about $112M of NEAR a day. The market capitalisation is $4.82 <!--n:mcap_usd_b-->B at $3.67.

## 5. What the price has to believe

At $4.82B the market pays 199 <!--n:mcap_to_rev_30d_annualized_x-->× annualised 30-day captured revenue (the frozen rating window’s trailing-90d revenue is only ~$4.84M — ~0.2× the 30d run-rate; `data/derived/r90_vs_run_rate.json`). The valuation question is therefore about the numerator. For the multiple to fall to 50×, captured revenue has to reach about $96M a year (derived: 4,820 ÷ 50), 4.0 times today's run-rate. Two levers get there without a new venue: volume at four times the last 30 days' pace with the take at about 5 bp, or volume at twice the pace with the take near 10 bp, a rate partner channels already charge. Volume has been the faster-moving lever; in nine months monthly volume rose from $1.9B (2026-04) to a peak of $4.8B (2026-09).

## 6. Where the rule goes from Hold to Buy

Pre-registered result: H1a, that most staking rewards stay staked, fails, with net staking outflow at 6.56 <!--n:h1a_ratio_as_written_x-->× rewards. H1b and H1c are inconclusive. H1b's lower bound for net exchange inflow, 4.42 <!--n:h1b_net_inflow_lower_m-->M NEAR, is already below the 8.0098 <!--n:h1a_gross_issuance_90d_m-->M NEAR minted in the 90 days, and its upper bound is 152.45 <!--n:h1b_net_inflow_upper_m-->M. More citable exchange labels narrow that range. We are tracing where the unlabelled top receivers send their NEAR using a block-by-block census from our own node ([`docs/hub-trail-method.md`](docs/hub-trail-method.md)). Any label found that way is reported as a separate tier and enters the rule only if the repository owner accepts it by dated addendum.

## 7. What our own node sees

We run a NEAR node and read every transaction it processes ([`pipeline/census_usage.py`](pipeline/census_usage.py), [`pipeline/census_summary.py`](pipeline/census_summary.py)). Over 10.3 <!--c:census_hours--> hours that is 343 <!--c:census_txs_k-->K transactions, and no aggregator sits between the chain and these counts.

NEAR Intents is the largest single user of the chain's compute: it burns 9.4 <!--c:intents_gas_share_pct-->% of all gas, level with the HOT game contract (HOT has ~3× the tx share — Intents is heavier per tx; `data/derived/hot_vs_intents_gas.json`), and it is the target of 13.2 <!--c:intents_tx_share_pct-->% of transactions, second only to HOT. Counting any transaction whose receipts touch the contract, the share is 16 <!--c:intents_touch_share_pct-->%. The contract holds $229.2 <!--c:held_total_usd_m-->M of assets on chain, 27 <!--c:held_wnear_share_pct-->% of it wrapped NEAR, and 11859 <!--c:intents_accounts_window--> distinct accounts appear in executed intents in the window, solvers included.

Deposits into the contract ran at $79.7 <!--c:deposits_per_day_m-->M a day and withdrawals at $74.8 <!--c:withdrawals_per_day_m-->M a day over the window, a net $4.9 <!--c:net_deposits_per_day_m-->M a day in, valued at the 1Click prices. A window of hours is not a trend, and the dashboard says so; the point is that the flows are measured at the contract rather than reported by a third party. Around it, the chain's threshold-signature network delivered about 15.7 <!--c:signatures_per_day_k-->K signatures a day, and USDC and USDT moved 58.4 <!--c:stablecoin_transfers_per_day_k-->K times a day for $13.2 <!--c:stablecoin_usd_per_day_m-->M. 43 <!--c:delegate_share_pct-->% of transactions are relayed, so their senders never needed NEAR for gas.

## 8. What is observable on the chain over time

[`docs/history-sample-prereg.md`](docs/history-sample-prereg.md) freezes a stratified random sample of blocks across 26 quarters, with hypotheses and pass rules fixed before any sampled block was read. Its results, with 90% intervals, are in `data/derived/history_results.json` and in section 6 of the dashboard when the build includes them. They are published whichever way each hypothesis falls.



## 8. What else the chain shows (exploratory)

The contract's own inventory tells the same story in quantities, not just in reported volume. Month-start supplies of the largest assets inside `intents.near`, valued at a fixed price list so the series measures deposits rather than mark-to-market, rose from about $0.5M in January 2025 to about $180M by November 2026 (`data/raw/intents/holdings_history.json`). That is working capital sitting in the settlement venue, not TVL in a farm.



These figures are from keyless snapshots under `data/raw/prop/` and from a **preliminary** read of the history sample (**142** clusters with both seal and payload as of 2026-11-12, including sample2 fill for some missing primary payloads; more seals still syncing). Exploratory extras show intents intensity ~**23.5×** from first nonzero quarter to latest (`data/derived/history_intents_growth.json`). With more clusters, sampled Intents receipts in 2025Q3 read about **281K**/day (was ~51K on a one-cluster draw), and the 2026Q4 draw (now three clusters) reads about **441K**/day (was ~886K on one cluster). They feed no pre-registered test. Buyback quality / float-sink metrics are in [`docs/float-sink.md`](docs/float-sink.md); the prop-research index is [`docs/prop-research-index.md`](docs/prop-research-index.md).

- **Intents is most of NEAR's fee surface.** Over 30 days, NEAR Intents was 87% of all fees DefiLlama attributes to protocols and the chain on NEAR, and 93% of reported DEX volume on NEAR. The next venue, Rhea Dex, was about a tenth of Intents' fees.
- **Intents receipts are rising in the sampled history.** On the preliminary **142**-cluster read (early strata still sealing; five clusters per recent quarter where available), receipts executed on `intents.near` per day run about **281K → 191K → 155K → 134K → 299K → 435K** from 2025Q3 through 2026Q4 — a mid-path dip then recovery, not a straight line. Earlier one-cluster draws had overstated 2026Q4 (~886K). In the 2026Q4 draw, `intents.near` itself was the single busiest receiver on sampled blocks. Base-layer growth tests U1, U2, U4 and U5 fail on the same sample; that is the base-layer decline already visible in Nearblocks.
- **Chain Signatures show up in the same sample.** Exploratory counts of `sign` receipts on `v1.signer` (five clusters per recent quarter) run about **1.4K → 2.5K → 8.0K → 26K → 37K → 16K** a day from 2025Q3 through 2026Q4. Treat CS as infrastructure for Intents cross-chain, not a separate holders-revenue line until a paid signature fee appears (`data/derived/chain_signatures_link.json`).
- **Settlement inventory mix.** Of the ~$229M held in `intents.near`, **wNEAR ~27%**, **ZEC ~12% (#2)**, USDC+USDT in the top slice ~**17%+**, BTC/WBTC ~**10%+** (`data/derived/inventory_mix.json`). ZEC as working-capital #2 is a privacy-asset signal inside the venue, not farm TVL. Nansen confidential TVL (~$160M at Q3-end) is about **70%** of that inventory stock.
- **Intents dwarfs L1 stablecoin flow in the census window.** Deposits into `intents.near` ~**$80M/day** vs ~**$13M/day** stablecoin transfers (~**6×**) (`data/derived/intents_vs_l1_flow.json`). Hours-long window — not a trend.
- **Builder npm shape matches the fee locus.** From mid-2025 to Oct 2026, `@defuse-protocol/one-click-sdk-typescript` monthly downloads grew about **37×** and `@near-wallet-selector/core` about **9×**, while `near-api-js` grew about **2.6×** (`data/derived/builder_npm_pulse.json`). Soft signal — CI-inflated levels; does not raise capture by itself.
- **Liquid staking is live next to Intents.** LiNEAR about $47M, Meta Pool about $80M, RHEA LST about $69M of TVL (DefiLlama). RHEA LST is about 4× its level a year ago.
- **Bitwise NEAR ETF (NRR).** On 2026-11-11 the SoSoValue dashboard showed about $55.9M of net assets (1.2% of NEAR market cap; down ~39% from a ~$91M late-Oct print) and about $80.5M of cumulative net inflow since launch, with a 0.75% fee — implied NRR ~$0.4M/yr vs Intents ~$24M run-rate (`data/derived/etf_aum_vs_intents_fee.json`). Assets were about $91M on 2026-10-21 and have since drifted lower (`data/raw/prop/etf_nrr.json`).
- **Validator set.** 351 validators, Nakamoto coefficient (one-third of stake) of 9, top validator 5.7% of stake, HHI 0.022, block uptime 99.98% in the latest epoch on our node (`data/raw/prop/validators_summary.json`).
- **Aurora is not the story.** Aurora chain TVL is about $3.8M against a peak above $1.3B; its fees are negligible next to Intents (`data/raw/prop/aurora.json`). The thesis does not rest on Aurora.
- **The node census (about 10 hours).** Intents is 13% of transactions and 9% of gas; 43% of transactions are relayed (gasless); about 16K Chain Signatures a day; about $13M a day of stablecoin transfers; about $80M of deposits and $76M of withdrawals a day into and out of Intents, for a net about +$4.6M a day. Relayer concentration is high: one account sends 83% of relayed transactions.


The structural layer — who owns the margin, what Confidential Intents changes, what the ETF stack does to float, and why Intents won share — is in [`docs/structural-thesis.md`](docs/structural-thesis.md). The fee waterfall (user all-in vs token-claimable bp, leakage ~10× on 1Click, AITR ~9.5 bp) is in [`docs/fee-waterfall.md`](docs/fee-waterfall.md). Confidential margin vs attestation (escrow-dependence ~59%, CIF forwarding as kill switch) is in [`docs/confidential-attestation.md`](docs/confidential-attestation.md). All three are exploratory prop research, not pre-registered tests.

## 9. What has to happen next (path arithmetic)

The path that compounds is not “more L1 transactions.” It is attachment, mix, issuance cut, and attestation — dated where known in [`docs/catalysts-and-path.md`](docs/catalysts-and-path.md) and `data/derived/catalyst_{math,calendar}.json`.

- **Buyback-fee attachment** rose 23.6% → 43.0% of 1Click volume across three 30-day blocks while SwapKit share stayed roughly flat. Implied take on the *attached* slice is about **9.5 bp**. Holding that rate and lifting attachment to **60%** raises run-rate from about **$24M** to about **$32M** and issuance offset from **15.8%** to about **21%**; at the **1.6%** issuance cap that same attach-60 path is about **32%** of net issuance — still a minority of mint, roughly double today’s share, with no volume growth assumed.
- **Inventory turns like a venue.** `intents.near` held about **$229M** against **$4.0B** of 30-day volume — about **17×** monthly turnover, or **1.7 days** of volume as working capital. Month-start supplies (fixed prices) rose from about **$0.5M** (Jan 2025) to about **$180M** (Nov 2026).
- **Dial inventory (derived).** Attach-60 + half a +10pp near.com mix stack lands near **~$37M** run-rate — still ~0.4× of the ~$96M needed for a 50× multiple, and fees cover only ~**0.21×** of net mint dollars today (~0.48× at HSP-029+stack). THOR-like ~16× at current mcap needs ~**$301M** rev (~12× today). Partner-path sketches (Trust→direct, no-ref, LI.FI→AITR, SwapKit→no-ref) sum to low-single-digit $M/yr — useful dials, not the volume gap. SwapKit exit would cut ~38% of 1Click volume but only ~**2%** of traceable buyback dollars — the fee engine already lives in no-referrer (`data/derived/sk_exit_fee_asymmetry.json`). Punch card: [`docs/prop-punch-card.md`](docs/prop-punch-card.md); summary: `data/derived/dial_inventory_summary.json`. Pitch lead order: `data/derived/pitch_sequence.json`.
- **Dated near-term.** Forward tests F1–F4 resolve **2026-11-14**. HSP-029’s timelock ends **2026-11-16**. Open policy items that collapse the investment range: per-stream escrow attestation (today’s capture is a **4.5–15.8%** band) and exchange labels past **50%** of the top-100 receivers (the only frozen input still separating Hold from Buy).
- **Volume without capture.** Peer volume share **55.7%** vs capture share **32.5%** — volume/capture index ~**1.7×**; NEAR’s DefiLlama-style revenue multiple is ~**14×** richer than THORChain’s (`data/derived/volume_capture_index.json`).
- **Score first.** Attachment %, capture share, escrow attestation, near.com mix, HSP-029 activation — before AI roadmap slides or ETF AUM. AI staking for inference (>750k NEAR) and NRR (~$56M / 1.2% mcap) are real but second-order to the fee engine until agent-originated volume or sustained high-single-digit % of mcap shows up.
- **Multiple math.** About **$96M**/year of captured revenue is needed for a **50×** multiple at today’s mcap. Attach/mix alone top out near **~$42M** (~**0.4×** of that need); clearing 50× on arithmetic still wants about **4×** volume at ~5 bp or **2×** at ~10 bp (`data/derived/path_to_50x.json`). Capture levers raise numerator quality; volume still has to grow for the multiple to compress without a price cut.

## Reproduce

```
make reproduce      # rebuild every metric offline from committed raw snapshots
make check          # manifest hashes and every n: marker in this file
make test           # unit tests
make dashboard      # rebuild dashboard/index.html
```


### Controllable dials (fresh arithmetic)

Partner-tax renegotiation dominates controllable upside without new volume: SwapKit-listed fees alone annualise ~$41M vs ~$24M NEAR capture; a 25% take is ~$10M/yr (~20% of the ~$50M leakage pool). Whale +10pp attach is ~$1M/yr (margin quality). Peer-share to 70% is only ~1.26× volume. Agent/npm leads are fee-immaterial on current bounds. Quality rose on a cooling −12% MoM volume print. Hold until H1b; HSP-029 pending-not-live.



### Conversion and Trust path

Only ~9.2% of Explorer appfees become buybacks; ~68% of revwallet buybacks are unmapped to fee-events. Trust-via-SK→direct-20bp is ~$1.7M/yr BB arithmetic. Attach already rose 23.6→43 pp inside the sample (captured bp 1.72×). Intents fees ~11.2× L1 — the fee engine is Intents.



### Issuance-pool tension (HSP-007)

HSP-029 cuts the mint fees must cover; HSP-007 (title-level) claims emissions for MPC/CS opex — same pool, opposite direction. CS is necessary Intents infrastructure without a holders-revenue line. Gap on HSP-007 magnitude.



### Channel density

No-ref and Trust dominate buyback-fee dollars per unit volume; LI.FI is ~10% of 1Click vol at only 2.8 bp (density 0.69×). H1b still covers only ~20–25% of streams/inflows.


### L1 attention vs Intents fee

Active accounts −77% YoY while Intents fees ~11× L1 fee print; NEAR-side swaps only 3.5%. The investment object is Intents capture, not L1 activity.


### Quality-on-cool context

Attach/τ rose on −12% MoM volume, but 30d daily notional is still ~1.5× the year average — cool-off from an elevated print. DefiLlama Intents fees −31.6% MoM (absolute cool faster than vol).


### Three ~$10M magnitudes

SK-tax ~$10M (capture), attest escrow ~$8.4M (trust), HSP-007 illustrative 10% emissions claim ~$11.8M (mint opex, Gap). Net the issuance narrative.

<!-- AUTO:LATEST_SWEEP -->
### Latest proprietary sweep (exploratory)

- **~587 commits / 210 clusters** (210 milestone). Contest-year `_13`; overall still **not supported**.
- **Fee≠L1 OoM** intents ~**147×** vs L1 ~**0.21×**.
- Two bridges · whale desk · default rail · attest≠τ · peerset gross−net gap · coverage wall~42.8%.
- **LIVE (~58h):** repo still **private** + X TODO. Hold until H1b.
<!-- /AUTO:LATEST_SWEEP -->

## Risks and context

- **Unattested escrow dollars.** Even at 15.8% attestation high, ~$8.4M/yr of escrow-funded BB (if sustained) sits outside the band (`escrow_unattested_dollars.json`).
- **Distribution owns the fee print.** Listed partners ~$4.45M > NEAR capture ~$1.99M; only 9.2% of appfees become buybacks; H1b covers ~20–25% of streams (`fee_stack_identity`, `appfees_to_buyback_conversion`, `h1b_coverage_still_binding`).
- **HSP-007 vs HSP-029.** MPC emissions claim competes with mint cut on the same issuance pool (magnitude Gap).
- **Relayer top1 ~83%.** Ops left-tail beside fee math (`relayer_hhi_floor`).
- **Volume is binding.** Attach/mix/leakage dials raise run-rate toward ~$37–45M; even full-venue AITR is ~$46M — 50× still needs ~2–4× volume (`data/derived/attach_ceiling_50x.json`). Full capture of 15.3 gross bp + HSP-029 ≈ 1× mint; 50× then needs ~1.3× vol (`full_capture_extreme.json`).
- **USD fee growth is price-heavy.** ~619%/yr USD vs ~71%/yr NEAR (`growth_usd_vs_near.json`).
- **Base-layer activity is far below its 2024 peak.** Nearblocks counts about 739K transactions a day in 2026Q3 against 7.7M in 2024Q2, and 79K active accounts a day against 1.86M. Stablecoins on NEAR are $131M, against $651M at the 2024Q3 peak. Chain TVL is $169M, against $274M in 2022Q3.
- **The multiple is high.** 199 <!--n:mcap_to_rev_30d_annualized_x-->× annualised 30-day captured revenue (`data/derived/multiple_on_cooling_vol.json`), and 510 <!--n:mcap_to_rev_365d_x-->× over the trailing year. NEAR is down 27.7% over the last 30 days, and the last 30 days' Intents volume was below the prior 30 days' ($4.0B against $4.56 <!--n:intents_vol_prior30d_b-->B) — capture quality rose on a **cooling** volume print (`data/derived/vol_deceleration.json`).
- **Capture is partly unattested.** Only 4.53 <!--n:ladder_public_collectors_pct_of_issuance-->% of issuance traces to public fee collectors. The other 11.25 <!--n:ladder_escrow_unshields_pct_of_issuance-->% arrives as releases from the confidential escrow, and 58.8 <!--n:escrow_share_of_buyback_near_30d_pct-->% of the buyback wallet's NEAR came that way.
- **Settlement runs through few relayers.** In the census window one account submitted 83 <!--c:relayer_top1_pct-->% of `execute_intents` calls and five submitted 99.9 <!--c:relayer_top5_pct-->%, out of 25 <!--c:relayer_accounts--> accounts in all.
- **Peers cost less per dollar of revenue.** On DefiLlama's revenue definition, the token market capitalisation is 217 <!--c:peer_mult_near-->× annualised 30-day revenue for NEAR, 16 <!--c:peer_mult_thorchain-->× for THORChain and 5 <!--c:peer_mult_chainflip-->× for Chainflip.
- **Partners keep more than NEAR does.** At least 1.81 <!--n:partners_kept_vs_near_rev_low_tight_x-->× NEAR's captured revenue. SwapKit routes 38.2 <!--n:swapkit_vol_share_pct-->% of 1Click volume. **Ledger via SwapKit alone** (~13.7% of 1Click vol at ~133 bp listed partner fee) extracts about **$2.0M** in the window — roughly **matching** NEAR's entire captured revenue (`data/derived/ledger_swapkit_tax.json`).
- **1Click was a net route out of NEAR**: $24.0 <!--n:explorer_out_of_near_usd_m-->M out against $14.6 <!--n:explorer_into_near_usd_m-->M in — net about **$9.4M**, roughly **4.7×** the same window’s captured revenue ($1.99M). Fee capture and NEAR-asset flow are different scoreboards (`data/derived/near_exit_vs_capture.json`). Only ~3.5% of 1Click swaps are NEAR-sided (`data/derived/near_side_swap_share.json`) — the venue is mostly foreign-asset routing on NEAR rails.
- **Pending.** HSP-029 clears its timelock after this is written, and the forward tests F1 to F4 are scored after 2026-11-14. The rating moves to Avoid if observed growth falls below about 17% a year with H1b failing.

*Not investment advice.*

Judge one-pager: [`docs/pitch-spine.md`](docs/pitch-spine.md).

Proprietary edge list: [`docs/prop-what-is-proprietary.md`](docs/prop-what-is-proprietary.md).
