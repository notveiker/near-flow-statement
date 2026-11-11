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
| npm pulse | `builder_npm_pulse.json` | 1Click SDK ~37× vs near-api-js ~2.6× |
| Builder pulse | `builder_pulse.json` | Soft: nearcore/intents/mpc fresh pushes |
| AI agents | ai-agents-evidence.md | >750k NEAR inference stake — second-order |

**Scoreboard before narrative:** attachment %, capture share, leakage L, AITR, attestation gap, near.com mix, DIC / burn policy, HSP-029, relayer HHI — then AI slides and ETF AUM.

History sample: preliminary **133** sealed clusters (primary) with payloads; dual sampler still filling early rounds.
