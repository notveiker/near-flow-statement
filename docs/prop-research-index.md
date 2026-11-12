> One-pager: [prop-punch-card.md](prop-punch-card.md) · Topline: [prop-topline.md](prop-topline.md) · What is proprietary: [prop-what-is-proprietary.md](prop-what-is-proprietary.md)

# Proprietary research index

*Exploratory / post-freeze. Judge-facing notes first; working detail under `research_notes/NEAR catalysts and path/`. As of 2026-11-12.*

## Judge-facing

| Note | Punch |
|---|---|
| [structural-thesis.md](structural-thesis.md) | Distribution owns the margin; confidential raises take while thinning proof; ETF small soft float |
| [catalysts-and-path.md](catalysts-and-path.md) | Attachment, mix, HSP-029, attestation calendar; path-to-50× needs volume beyond attach/mix (~0.4× alone) |
| [fee-waterfall.md](fee-waterfall.md) | τ≈5 bp, C=32.5%, L≈10×, AITR≈9.5 bp; SwapKit pipe-level ~0; excess ~$0.94M solver/gas residual |
| [confidential-attestation.md](confidential-attestation.md) | Escrow-dependence ~59%; CIF forwarding is the kill switch |
| [float-sink.md](float-sink.md) | Buyback DIC ~25 days; held not burned; scarcity half-life ~60d |

## Working notes + machine JSON

| Topic | Files | Punch |
|---|---|---|
| Mix shift | `mix_shift_math.json`, mix-shift-arithmetic.md | ~$1M/year per pp to 100%-fee fronts |
| Path to 50× | `path_to_50x.json` | Attach/mix ~0.4× of $96M need |
| Prop scores | `prop_scores.json` | τ, C, L, AITR, attestation gap |
| Contestability | `contestability.json` | REVSHARE / SwapKit embed risk |
| Relayer risk | `relayer_risk.json` | HHI ≫ 0.25; top1 ~83% |
| Inventory mix | `inventory_mix.json` | ZEC #2 (~12%) in settlement stock |
| NEAR exit | `near_exit_vs_capture.json` | Net exit ~4.7× same-window capture |
| Chain Signatures | `chain_signatures_link.json` | Intents infra, not separate τ |
| Perps / concentration / L1 flow | `perps_positioning.json`, `concentration_overlays.json`, `intents_vs_l1_flow.json` | OI −42%; conf TVL ~70% inventory; deposits ~6× stables |
| npm pulse | `builder_npm_pulse.json` | 1Click SDK ~37× vs near-api-js ~2.6× |
| Builder pulse | `builder_pulse.json` | Soft: nearcore/intents/mpc fresh pushes |
| AI agents | ai-agents-evidence.md | >750k NEAR inference stake — second-order |

**Scoreboard before narrative:** attachment %, capture share, leakage L, AITR, attestation gap, near.com mix, DIC / burn policy, HSP-029, relayer HHI — then AI slides and ETF AUM.

History sample: preliminary **133** sealed clusters (primary) with payloads; dual sampler still filling early rounds.

## Latest derived JSON (machine)

`buyback_channel_map`, `ledger_swapkit_tax`, `swapkit_tax_total`, `volume_capture_index`, `dual_concentration`, `capital_efficiency`, `inventory_mix`, `near_exit_vs_capture`, `perps_positioning`, `concentration_overlays`, `intents_vs_l1_flow`, `float_sink`, `path_to_50x`, `mix_shift_math`, `prop_scores`, `catalyst_math`, `aurora_residual`, `lst_vs_buyback`, `rhea_lst_growth`, `builder_npm_pulse`, `governance_catalysts`, `hsp007_mpc`, `relayer_risk`, `solver_excess`, `contestability`, `fee_per_download`.
- `data/derived/issuance_fee_coverage.json` — fee run-rate vs net mint $; volume multiple for 1× coverage
- `data/derived/controllable_stack.json` — NEAR-controllable attach+mix stack vs 50× need
- `data/derived/partner_path_uplift_stack.json` — Trust/no-ref/LI.FI dial inventory
- `data/derived/thor_multiple_bridge.json` — Rev/vol need for THOR-like 16×
- `data/derived/attestation_band_compression.json` — Disclosure collapses capture-share band
- `data/derived/bitwise_vs_intents.json` — Institutional NRR vs Intents fee surface
- `data/derived/zec_inventory_uplift.json` — ZEC inventory 2× fee sketch
- `data/derived/agent_volume_bounds.json` — AI agent vol fee upper bounds
- `data/derived/whale_attach_prize.json` — +10pp attach on ≥$10k tranche
- `data/derived/rent_map_ratios.json` — Solver+partner vs NEAR capture
- `data/derived/exit_vs_buyback_stock.json` — Net NEAR exit vs buyback wallet stock
- `data/derived/noreferrer_mix_uplift.json` — +5pp no-referrer at 10 bp
- `data/derived/trust_path_uplift.json` — Trust SwapKit→direct 20 bp path
- `data/derived/attach_ceiling_50x.json — full-venue AITR ceiling vs 50× need`
- `data/derived/capture_share_path.json — leakage compression scenarios`
- `data/derived/catalyst_dial_rank.json — dials ranked by run-rate delta`
- `data/derived/cif_sensitivity.json — CIF bp sensitivity on conf TVL`
- `data/derived/cs_density_proxy.json — deposit notional per CS signature`
- `data/derived/dial_inventory_summary.json — dial inventory rollup`
- `data/derived/etf_aum_vs_intents_fee.json — ETF NRR vs Intents fee RR`
- `data/derived/intents_vs_near_dex.json — Intents share of NEAR DEX vol`
- `data/derived/noref_dollar_concentration.json — no-ref buyback-$ concentration`
- `data/derived/npm_growth_vs_fee.json — SDK downloads vs fee vanity`
- `data/derived/pmf_flow_dominance.json — deposits vs stablecoin flow`
- `data/derived/swapkit_exit_share_impact.json — peerset share if SK exits`
- `data/derived/swapkit_prize_extremes.json — SK full AITR vs exit`
- `data/derived/swapkit_to_noref_uplift.json — 10pp SK→no-ref`
- `data/derived/volume_multiples_from_stack.json — vol× needed from $37M stack`
- `data/derived/calendar_ordering.json — submit vs HSP-029 ordering`
- `data/derived/hsp007_claim_bounds.json — illustrative emissions claims`
- `data/derived/lst_vs_issuance.json — LST vs annual mint $`
- `data/derived/oi_vs_fee_decouple.json — perps OI vs fee print`
- `data/derived/leakage_pool_size.json — ~$50M/yr non-NEAR claims`
- `data/derived/leakage_then_volume.json — 60% capture still needs vol`
- `data/derived/capture_ceiling_50x.json — 50× needs >gross bp at current vol`
- `data/derived/sk_exit_fee_asymmetry.json — vol risk ≫ buyback risk on SK`
- `data/derived/hsp029_alone.json — denominator help only`
- `data/derived/peerset_share_path.json — share at 2×/4× Intents vol`
- `data/derived/soft_sink_ladder.json — LST≫NRR≫buyback DIC`
- `data/derived/burn_materiality.json — 25% mint burn needs >100% fees`
- `data/derived/pitch_sequence.json — judge pitch order`
- `data/derived/escrow_share_climb.json — Jul→Nov escrow % of buyback`
- `data/derived/attach_vs_partner_race.json — attach up, partner bp up`
- `data/derived/oneclick_coverage_shrink.json — 1Click/Llama coverage fall`
- `data/derived/partner_bb_ratio_trend.json — partner/bb ratio improving`
- `data/derived/growth_usd_vs_near.json — 619% USD vs 71% NEAR growth`
- `data/derived/full_capture_extreme.json — zero leakage path`
- `data/derived/fee_evidence_fidelity.json — BB/SK payment fidelity`
- `data/derived/near_side_swap_share.json — 3.5% NEAR-sided swaps`
- `data/derived/stake_dominant_float.json — 44.5% supply staked`
- `data/derived/prop_falsifiers.json — pitch falsifiers`
