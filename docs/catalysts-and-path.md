# What has to happen next — and the arithmetic that matters

*Exploratory / post-freeze prop research (as of 2026-11-11). Not a pre-registered test. Scenarios are arithmetic on committed metrics in `data/derived/catalyst_math.json` and `data/derived/catalyst_calendar.json`, not forecasts. Do not read this as a guaranteed path.*

The investment-relevant path for NEAR is not “more L1 transactions.” It is a short list of dated events, policy choices NEAR controls, and mix shifts that raise **captured** take without a head-on fight with distribution. The numbers below show how large those levers are relative to today’s baseline.

## Dated events in the next week

**2026-11-14.** The frozen forward tests F1–F4 resolve (`PREREG.md`). F1 checks the buyback wallet’s NEAR balance band; F2 checks net supply growth per day; F3 predicts captured take **below 4.0 bp** (October’s 5.49 bp was treated as a high); F4 needs Intents’ peer-set volume share **≥ 50%** over the window. Misses are published. These do not change the Hold rating by themselves; they are a public check on whether the last month’s shape was a spike.

**2026-11-16.** HSP-029’s timelock ends. The proposal ramps the annual issuance cap from **2.5% to 1.6%** over 24 months, starting one quarter after ratification. The frozen rating rule’s required growth (**33.2%/yr**) already assumes that path. If the ramp activates and captured revenue only stays where it is, issuance offset moves from **15.81%** today to about **24%** (derived: 15.81 × 2.46 ÷ 1.6). That is the issuance lever alone — no volume growth required.

**HSP-007 (open / execution).** MPC node infrastructure financed via protocol emissions — a competing claim on the **same issuance pool** Intents fees try to offset (`data/derived/governance_catalysts.json`). Treat as opex on mint, not free Chain Signatures capacity. Magnitudes are a Gap without full proposal bodies in-repo.

## The cleanest NEAR-side lever: buyback-fee attachment

Across three consecutive 30-day blocks, the share of 1Click volume carrying an explicit buyback fee entry rose **23.6% → 43.0%**, and explicit buyback take rose **1.83 → 4.08 bp**, while SwapKit’s volume share stayed roughly flat. Implied take on the *attached* slice in the latest block is about **9.5 bp** (4.08 ÷ 0.43). Holding that rate on attached volume and raising attachment is arithmetic, not a new commercial deal with SwapKit.

| Attachment of volume | Explicit buyback bp (approx) | Captured bp (approx) | 30d revenue (approx) | Annualised run-rate | Issuance offset (approx) |
|---|---|---|---|---|---|
| 43% (today) | 4.08 | 4.98 | $1.99M | $24.2M | 15.8% |
| 50% | 4.74 | 5.64 | $2.26M | $27.5M | 17.9% |
| 60% | 5.69 | 6.59 | $2.64M | $32.1M | 20.9% |
| 70% | 6.64 | 7.54 | $3.02M | $36.7M | 23.9% |
| 80% | 7.59 | 8.49 | $3.40M | $41.3M | 27.0% |

If attachment reaches **60%** *and* the issuance cap is at **1.6%**, the same arithmetic puts issuance offset near **32%** of net issuance — still a minority of mint, but roughly double today’s share, without assuming any growth in Intents volume. The falsifier is the opposite path: attachment rolls over, or new Commercial Agreements zero out NEAR’s explicit line while partners keep 100+ bp.

## Inventory turns like a venue, not a farm

`intents.near` held about **$229M** of priced assets at the latest snapshot. Against **$4.0B** of 30-day volume that is about **17×** turnover in a month, or roughly **1.7 days** of volume sitting as working capital. Month-start supplies (fixed prices so the series is quantity, not mark-to-market) rose from about **$0.5M** in January 2025 to about **$180M** by November 2026. That is settlement inventory scaling with the venue — capital-efficient relative to bonded vault AMMs that must underwrite TVL continuously. It is also not a claim that NEAR the token is being accumulated inside the contract; most of the inventory is non-NEAR assets in transit.

## Policy choices that collapse the range

Two open choices sit above the dated calendar and above attachment arithmetic.

**Per-stream escrow attestation.** Measured capture of issuance is a **range of about 4.5–15.8%** until NEAR attests which fee streams fund confidential-escrow unshields. About **59%** of recent buyback-wallet NEAR arrived that way. Attestation does not create revenue; it decides whether the top of the range is believable. Without it, serious capital has to underwrite the floor.

**Exchange labels past 50% of the top-100 receivers.** The frozen rating rule already has observed growth far above required growth. The only missing Buy input is H1b, which is inconclusive because labelled coverage is **20%**. Labels that pass the method enter the primary measure only by dated addendum. This is a research and disclosure problem, not a product problem — but it is the difference between the rule’s Hold and Buy.

## Distribution mix as a quiet catalyst

near.com handled about a **quarter** of Intents volume in Q3 2026, with stated 100% fee direction to a NEAR revenue wallet. SwapKit still routes about **38%** of 1Click volume with almost no explicit buyback line. Every point of mix that moves from SwapKit-class deals toward near.com (or other 100%-fee fronts) raises capture share without raising the user’s all-in price on partner wallets. On today’s **$4.0B**/30d pace, **each percentage point** so moved is about **$80k**/30d ≈ **$0.97M**/year at a 20 bp 100%-fee front versus a 0 bp explicit line (`data/derived/mix_shift_math.json`). A +10 pp sketch lifts run-rate from about **$24M** toward about **$34M** before stacking attachment. Tokenized US stocks and ETFs on near.com (from late September 2026) widen that frontend’s reason to exist beyond crypto-crypto swaps. Because swaps ≥$10k are **77%** of 1Click volume, mix is desk-sensitive — leverage and concentration in the same number. The falsifier is the reverse mix: more volume concentrating in zero-buyback Commercial Agreements.

## What is second-order (and still worth watching)

**AI-agent stack.** Staking for NEAR AI inference (>750k NEAR), IronClaw enclaves, x402 Foundation membership, and roadmap items (near-kit 1.0, TEE enforcement) are real product moves. They matter for the *story* Bitwise and NEAR sell around NRR. They are not yet a measured fee engine comparable to Intents. Treat agent settlement as a call option on a second demand surface until agent-originated Intents volume or NEAR-denominated agent payments show up in public series.

**NRR / ETP path.** About **$56M** net assets (**1.2%** of mcap) after launch-week strength and later fade. Additive spot demand and a soft float sink via in-house staking (NEAR unbonds in ~1–2 days). First-order for the multiple only if the physical stack scales toward high-single-digit percent of mcap for a sustained period.

**Roadmap infrastructure (Q4 2026–Q1 2027).** near-kit, TEE enforcement, heterogeneous TEEs, single-block cross-shard — second-order for the Intents capture thesis; first-order only if they unlock measurable Intents or AI fee flow.

## What gets the multiple to 50×

At today’s market cap, about **$96M**/year of captured revenue is needed for a **50×** multiple (`data/derived/path_to_50x.json`). Attachment and mix alone — even attach **80%** or attach **60%** plus **+10 pp** near.com mix — land near **~$41–42M** run-rate, about **0.4×** of that need. The volume paths that clear 50× on arithmetic are familiar: about **4×** volume at ~5 bp, or **2×** volume at ~10 bp. Capture discipline raises the quality of the numerator; **volume still has to grow** for the multiple to compress without a price cut. A conservative stack of attach-60 plus half a +10pp near.com mix uplift lands near **~$37M** run-rate (`data/derived/controllable_stack.json`) — still about **0.4×** of the 50× need. That is why attachment and mix are scored first (they are NEAR-side and measurable) and volume second (it is larger but less controllable).

## How to score the path

Score **attachment %, capture share, escrow attestation, near.com mix, and HSP-029 activation** before you score AI roadmap slides or ETF AUM. Volume share without capture-rate discipline overstates what the token earns. The path that compounds is attachment + mix + issuance cut + attestation — the same commercial map as [`docs/structural-thesis.md`](structural-thesis.md), with dates and arithmetic attached.

## Dial rank (derived)

Ranked run-rate deltas vs the $24.2M baseline are in `data/derived/catalyst_dial_rank.json`. Attach and near.com mix dominate; partner-path and CIF sketches are low-single-digit $M/yr. **Volume remains the binding constraint** for 50× and for a THOR-like multiple.

Capture-share dial: `data/derived/capture_share_path.json`. Volume multiples from stack: `data/derived/volume_multiples_from_stack.json`.
