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

## Pitch sequence (derived)

See `data/derived/pitch_sequence.json`: lead with attach/AITR, capture share, no-ref dollar concentration, Intents≈NEAR DEX, fee÷mint$, then volume as the binding closer. Do not lead with AI/ETF/npm.

Leakage→volume: `data/derived/leakage_then_volume.json` — 60% capture ≈ $45M still needs ~2.2× volume for 50×.

Capture ceiling: `data/derived/capture_ceiling_50x.json` — 50× needs ~19.8 bp at current volume (above 15.3 gross).

Full-capture extreme: `data/derived/full_capture_extreme.json` — zero leakage + HSP-029 ≈ 1× mint coverage; 50× needs ~1.3× volume.

Judge sheet of proprietary arithmetics: [`docs/prop-what-is-proprietary.md`](prop-what-is-proprietary.md).

Quality on cool: `data/derived/quality_on_cool.json` — attach/τ up while 1Click notional peaked then fell.

50× vs cooling: `data/derived/50x_vs_cooling.json` — path needs ~4× vol while latest print is −12% MoM.

## Controllable dial ROI (exploratory)

Ranked by approximate annualised uplift **without** requiring ~4× volume:

| Dial | ~$/yr uplift | Needs volume? |
|---|---|---|
| SK partner-tax 25% renegotiation | ~$10M | No |
| ZEC inventory 2× same turnover | ~$2.8M | Inventory |
| Whale +10pp attach (≥$10k) | ~$1.0M | No |
| +5pp mix to no-referrer @10bp | ~$0.7M | Mix only |
| Peer share →70% (fixed peerset) | ~+$6M fee if take flat | 1.26× vol |
| Agent origin 5% bound | ~$0.33M | Labeled |

Leakage renegotiation is the bridge; volume is the last mile. Peer-share and AI narrative are not the path alone.

## Conversion dial (appfees → buybacks)

Explorer lists ~$4.90M appfees / 30d but only **~9.2%** ($0.45M) become buybacks. Partners keep ~$4.21M with no BB line. Capture share is a **conversion** problem as much as an attach problem.

Trust Wallet path is a concrete dial: Trust-via-SK (6.4% vol) pays ~70 bp partner tax and 0 explicit BB; Trust-direct pays 20 bp BB. Moving SK Trust to direct-20bp is ~**$1.7M/yr** BB uplift arithmetic — one distribution conversation.

Observed take windows already moved attach 23.6→43 pp and captured bp 2.89→4.98 (~1.72×) — the quality path is evidenced inside the sample.

## HSP-007 vs HSP-029 (issuance pool tension)

HSP-029 ramps the issuance cap 2.5%→1.6% (timelock 2026-11-16). HSP-007 (forum title-level) proposes financing MPC/CS nodes from **protocol emissions** — a competing claim on the same mint pool that fee capture is trying to offset. Chain Signatures has **no holders-revenue line** in committed metrics. Score HSP-007 as opex-on-mint until a NEAR/year figure is published. Pitch HSP-029 as pending-not-live; do not net it against an unsized HSP-007.

## near.com mix: stated share vs wallet print

Q3 Nansen near.com-class volume share (~25%) does not match the Nov frontend wallet print ($616.9k / 20 bp ⇒ ~7.7% of Intents $4B). Mix-shift to near.com still sizes at ~+$9.7M/yr per +10pp in the arithmetic model, but the 25% anchor is not the live fee-touching share — upside exists *and* the headline distribution share is overstated. Exploratory.

## Peerset share softening

Intents peerset share prints 62.1% (365d) → 55.7% (30d gross) → **38.6% (30d net)**. Do not pitch rising peer dominance; leakage/conversion dials dominate.

## Trust-template expansion

High-density fronts (Trust/Arbie/Enot/Leodex) print ~20 bp on thin volume. LI.FI is 10% of 1Click at 2.8 bp — lifting to the Trust template is ~**$2.31M/yr** arithmetic. Commercial path: make dilutive aggregators look like high-density fronts.

## Marginal share vs volume

+1pp of capture-share of gross ≈ **$0.7M/yr**; +1pp of Intents volume at today’s ~5 bp ≈ **$0.2M/yr**. Capture-share renegotiation is ~3.1× more valuable per percentage point than volume growth at flat take.

## Quality-on-cool context

MoM vol −12% is real, but 30d daily notional is still ~1.5× the year average — quality improved on a cool-off from an elevated print.

## No-BB partner set

~94.6% of listed partner fees have no buyback line ($4.21M of $4.45M). Conversion dials target that set — not diffuse attach rhetoric.

## Three ~$10M magnitudes

SK-tax 25% ≈ $10M, attest escrow ≈ $8.4M, HSP-007 illustrative 10% emissions claim ≈ $11.8M. Capture and trust are upsides; HSP-007 competes for mint. Budget Gap on HSP-007.

## LST DIC

LST ~$196M ≈ ~611 DIC days (~25× buyback) but only ~9.3% of stake — size ≠ stake share.

<!-- AUTO:SOLVER_TG -->
### Contestable rent + TG attach (new)

- **Solver residual** ~8.5 bp ≈ **$11.4M/yr** sits beside the three ~$10M magnitudes; ADR-029 can redirect ≤50% (~$5.7M/yr) without user-fee hike — contest is P&L on residual, not BB $.
- **Telegram** (`intents.tg`) ~20% of tagged census with **unmapped** fee attribution — conservative half@10bp ≈ **$1.37M/yr** attach upside if labeled.
- **SK exit resilience split**: lose ~38% 1Click distribution, only ~2% traceable BB — fee engine already in no-ref; protect distribution surface separately from fee resilience.
<!-- /AUTO:SOLVER_TG -->

<!-- AUTO:DENSITY_PEER -->
### Fee density + peerset recovery honesty

- Intents ~**11×** L1 fees on ~**9%** gas — product is fee density, not activity.
- Peerset recovery to 365d 62% from 30d gross needs ~+$0.46B/30d — expensive vs SK-tax ~$10M with zero vol. Do not lead peer-share.
- Full gross+HSP still ~74% coverage — residual gap is volume/issuance.
<!-- /AUTO:DENSITY_PEER -->

<!-- AUTO:UNDERWRITE_CIF -->
### Underwriting + CIF + burn honesty

- **Attestation disclosure** compresses capture uncertainty ~5.7× without raising τ — institutional underwriting dial beside the ~$8.4M escrow dollar bridge.
- **CIF rate card** Gap: 1 bp ≈ **$3.3M/yr**, 5 bp ≈ **$16.6M/yr** on confidential proxy — could rival SK-tax if published/captured.
- **50×**: capture-alone impossible (~19.8 bp > 15.3 gross). Leakage then volume.
- **Burn ≠ BB wallet**: hard-burn for 25% mint needs >100% of capture; held buybacks are a ~25d DIC buffer with ~60d half-life.
<!-- /AUTO:UNDERWRITE_CIF -->

<!-- AUTO:PRIVACY -->
### Privacy / confidential surface

- Confidential TVL ~70% of inventory. Dials on that surface: ZEC 2× ~$2.8M · CIF 1bp ~$3.3M · attest ~$8.4M · CIF 5bp ~$16.6M.
- Rate card + attestation dominate inventory doubling. Gap: CIF unpublished.
<!-- /AUTO:PRIVACY -->

<!-- AUTO:LEDGER_DENSE -->
### Ledger-first + dense fronts

- Within-SK fee HHI ~0.41; **Ledger ~60%** of SK listed fees ≈ NEAR capture — SK-tax 25% (~$10.2M) is primarily a Ledger commercial conversation.
- Dense fronts portfolio ~**$1.59M/yr** at ~20bp template — protect Arbie/Enot/Leodex/Trust; extend to LI.FI.
- ADR-029 threat proxy ~$2.2M/yr sits inside solver residual (~$11.4M) — defend residual, contest is P&L.
<!-- /AUTO:LEDGER_DENSE -->

<!-- AUTO:HSP007_ENG -->
### HSP-007 engagement risk

HSP-007 forum likes ~**2.1×** HSP-029 — emissions-claim politics may compete with the mint-cut narrative. Illustrative 10% claim ~$11.8M/yr (Gap on actual draw).
<!-- /AUTO:HSP007_ENG -->

<!-- AUTO:OVERLAP -->
### Overlap discipline

Do not double-count SK-tax with no-BB redirect or gross-share pp; CIF with attestation (same confidential surface); ADR defense with full solver residual. Conservative capture board ~$18M. See `dial_overlap_map.json`.
<!-- /AUTO:OVERLAP -->

<!-- AUTO:NEAR_TERM -->
### Near-term board (before volume)

Ledger SK-tax ~$10.2M · attest ~$8.4M · ADR defense ~$5.7M · conversion ~$5.5M · CIF Gap ~$3.3M. Quality already 1.72× on cool. 50× still needs ~1.3× vol after full gross+HSP.
<!-- /AUTO:NEAR_TERM -->

<!-- AUTO:HOLD -->
### What moves Hold

Frozen rule: **H1b labels past 50%** flips Hold→Buy. Capture dials (Ledger SK-tax, attest, CIF, conversion, ADR defense) improve the object under Hold. Peer-share/volume/AI/npm/ETF do not flip stance.
<!-- /AUTO:HOLD -->

<!-- AUTO:ELASTICITY_OPACITY -->
## Dial elasticity and opacity-as-product (exploratory)

Marginal arithmetic in `dial_elasticity_board.json`: **+1pp capture-share ≈ $0.74M/yr** vs **+1pp volume ≈ $0.24M/yr** (×**3.07**). SK-tax ~$10.2M is roughly **~42.5 volume percentage points** of run-rate — renegotiation dominates cheerleading on the same dollar board. Do not double-count mutex pairs in `dial_overlap_map.json`.

Opacity is inventory, not a side risk: ~**71%** of measured capture arrives unattested (`confidential_share_of_capture.json`). The product stack is attestation (**~$8.4M** trust) plus a published CIF rate card (**~$3.3M** at 1bp Gap) — institutional underwriting of dollars already in the print (`opacity_product_stack.json`).

No-volume coverage path (`coverage_path_no_vol.json`): today ~**15.8%** → HSP-029 alone ~**24.7%** → attach 60% + HSP ~**32.7%** → conservative capture stack + HSP ~**42.8%**. Still short of full issuance offset; **volume remains the last mile for 50×**. Pitch HSP-029 as **pending-not-live** until the 16 Nov timelock.

History honesty (`history_fee_engine_vs_l1.json`, `history_counter_evidence_board.json`): L1 YoY activity ~0.18–0.26× while intents.near receipts ~100× vs 2025Q1 — the investable object is the Intents fee engine on a cooling base layer. Overall pre-registered usage growth remains **not supported**.
<!-- /AUTO:ELASTICITY_OPACITY -->

<!-- AUTO:THOR_TWO_STEP -->
## THOR two-step and rating-window honesty (exploratory)

`thor_two_step_bridge.json`: peer multiple parity (~217× → ~16×) needs ~13.6× fees at fixed price. **Step 1** is leakage close (~**3.1×**) via renegotiation/mix/conversion/CIF — no volume. **Step 2** is the remaining ~**4.4×** volume/price. Full-capture extreme after HSP still only needs ~**1.3×** volume for a 50× revenue path — leakage is the bridge; volume is the last mile.

`rating_window_fragility.json`: frozen rating rides ~$4.84M trailing-90d (~$19.6M annualised) against ~$24.2M 30d run-rate (**~1.23×** acceleration). If Intents cool persists, the Hold→Buy path compresses with the slower window — do not treat 30d RR as locked.

`submit_vs_hsp029_sequence.json`: submit is ~24h before the HSP-029 timelock — pitch the issuance cut as **pending-not-live**.
<!-- /AUTO:THOR_TWO_STEP -->

<!-- AUTO:RAILS_RESILIENCE -->
## Foreign rails and resilience split (exploratory)

`foreign_rail_vs_near_flow.json`: only ~**3.5%** of 1Click swaps are NEAR-sided; net NEAR exit in-window is ~**4.7×** captured revenue. Venue dominance is foreign-asset routing on NEAR rails — not a NEAR-pair demand story.

`fee_resilience_vs_surface_risk.json`: SwapKit exit costs ~**2%** traceable buyback dollars but ~**38%** of 1Click volume; relayer top1 ~**83%** is UX/share risk (~2000× vol/fee), not fee P&L. USD fee growth is ~**8.7×** NEAR-unit growth — price-heavy; NEAR-unit growth still clears G_req.
<!-- /AUTO:RAILS_RESILIENCE -->
<!-- AUTO:OPACITY_ACC -->
## Opacity is accelerating (exploratory)

Escrow share of buyback NEAR climbed ~**17.5%→58.5%** Jul→Nov (`opacity_accelerating.json`). Confidential funding is becoming the dominant rail without stream attestation — the underwriting band widens as the share rises. Attestation is time-sensitive trust inventory, not a nice-to-have.

ETF/NRR implied fee ~**$0.42M/yr** is ~**0.017×** Intents RR (`etf_immaterial_vs_intents.json`) — below even the AI 5% bound on the immaterial ladder. Do not open on ETF.

Inventory turns ~**17×**/30d (PCI ~0.057) — capital-light; binding constraint remains capture/leakage (`capital_light_fee_engine.json`). Even 60% capture share reaches only ~**0.46×** of a 50× revenue need (`capture_alone_insufficient_50x.json`).
<!-- /AUTO:OPACITY_ACC -->

<!-- AUTO:FIDELITY_DENSITY -->
## Payment fidelity and settlement density (exploratory)

`fee_payment_fidelity_board.json`: on the fee-evidence slice, buyback listed→paid exact ~**97%** and SwapKit listed→on-chain ~**91%**. Leakage is commercial terms / attach, not unpaid invoices.

`settlement_fee_density.json`: HOT carries ~3× the tx share of Intents at matched gas share — Intents is heavier per tx. Fee density lives in settlement weight.

`hsp007_vs_intents_tension.json`: an illustrative **20%** emissions claim is about **1×** Intents fee RR on the same issuance pool HSP-029 tries to shrink — treat as mint opex Gap until proposal bodies land.
<!-- /AUTO:FIDELITY_DENSITY -->

<!-- AUTO:HSP_LAG -->
## HSP-029 is pending-then-lagged (exploratory)

Timelock ends **2026-11-16**; float-sink path puts ramp activation around **2027-02-14**, then **24 months** to the 1.6% cap (`hsp029_activation_lag.json`). Submit materials must not imply a near-term mint cliff — the denominator dial is real but slow.

Chain Signatures sits under Intents execution (execute ≫ respond ≫ sign) — not a separate holders-revenue line (`cs_under_intents_not_separate_fee.json`).
<!-- /AUTO:HSP_LAG -->

<!-- AUTO:COMPOUND_SWEEP -->
### Compound sweep (exploratory)

- **Coverage wall:** no-vol stack tops ~**42.8%** — remaining gap is volume/price.
- **Opacity × elasticity:** escrow BB ~**58.5%** (+41.0 pp); attest urgency scales; capture dials still ~**3.07×** vs volume.
- **Fidelity:** BB~**96.7%** listed→paid — leakage is **commercial terms**, not collections.
- **Three scoreboards:** intents ~**189×** vs L1 ~**0.21×** vs NEAR-sided ~**3.5%**.
- **50× residual:** full-capture+HSP still ~**1.29×** vol. Order: leakage → HSP scenario → volume.
- **Delivery:** ~**59h**; repo still **private**; X dry-run pending.
<!-- /AUTO:COMPOUND_SWEEP -->

<!-- AUTO:MUTEX_HOURS -->
### Mutex + hours burn (exploratory)

- Capture dials naive-sum ~**$25.4M** / ~**105.8 vol-pp** — **do not sum**; call-order SK-tax→mix→conversion→attach.
- Soft sinks do not raise the ~42.8% coverage wall; leakage ~$50M does.
- ~**59h** left: burn hours on **public flip + X dry-run**. Delivery readiness ≠ Hold→Buy (H1b).
<!-- /AUTO:MUTEX_HOURS -->

<!-- AUTO:DOUBLE_OPACITY -->
### Quality-on-cool + double opacity (exploratory)

- **Quality-on-cool proof:** vol **-12.3%** MoM / fees **-31.64%** while attach/τ rose — capture dials work without volume growth.
- **Double opacity:** escrow BB ~**58.5%** AND unknown surface ~**33.2%** — attest + label in parallel.
- **Immaterial vs leakage:** SK-tax ~**$10.2M** vs ~**$50.2M** prize; ETF/AI immaterial.
- **Settlement≠spam:** HOT tx-heavy; Intents settlement-heavy — coverage wall is capture, not L1 tx recovery.
<!-- /AUTO:DOUBLE_OPACITY -->

<!-- AUTO:WHALE_DESK -->
### Whale desk + scarce capture (exploratory)

- **Whale desk = SK-tax:** 3.4% of swaps = 77.1% vol; SK partner tax pool ~**$40.9M**/yr.
- **Peerset recovery** ≪ SK-tax — share leadership is not the scarce resource.
- **Capital-light:** WC not binding; leakage terms are.
- **Trust SK→direct** nests under the Ledger/SK conversation (~17% of SK-tax dial).
- **Price-heavy:** USD fee ~619% vs NEAR-unit ~71% (~8.7×) — check NEAR-unit.
<!-- /AUTO:WHALE_DESK -->

<!-- AUTO:ATTACH_MOM -->
### Attach momentum (exploratory)

- Attach **23.6%→43.0%** (+**19.4** pp across three 30d blocks) **on a volume cool**.
- ~**17.0** pp remains to 60% — roughly the same distance already traveled → ~**$7.9M**/yr RR uplift at AITR.
- Lives under the ~**42.8%** no-vol coverage wall; still not 50× alone.
<!-- /AUTO:ATTACH_MOM -->

<!-- AUTO:D12_DONE -->
### Dense `_12` complete (exploratory)

- Contest-year denser `_12` through **2026Q4** sealed — **204 clusters**; overall still **not supported**.
- History is **not** a submit blocker. Remaining hours (~**59**) burn on **public repo + X dry-run**.
<!-- /AUTO:D12_DONE -->

<!-- AUTO:DIMINISH -->
### Diminishing strata vs delivery (exploratory)

- Fee≠L1 holds under densification (intents ~**181×** vs L1 ~**0.20×**; was ~189× @201).
- Entering `_13` — history still **not** a submit blocker.
- Marginal seals are **low EV** vs ~**59h** for **public flip + X dry-run**.
<!-- /AUTO:DIMINISH -->

<!-- AUTO:RENT_RELAY -->
### Solver rent + relayer ops + embed contest (exploratory)

- **Solver residual** ~**$11.41M**/yr is SK-tax-league **contestable rent** — separate ledger from capture.
- **Relayer top1** ~**83%**; outage vol/fee ~**2004.0×** — ops/UX catalyst, not a τ dial.
- **Multi-venue embeds** ~**54.0%** of 1Click can fill away — SK-tax/attach must clear exit threat.
<!-- /AUTO:RENT_RELAY -->

<!-- AUTO:CONV_AFF -->
### Conversion + affiliate contest + single-venue fee (exploratory)

- **Conversion:** only ~**9.2%** of appfees become buybacks — quiet capture dial (~**$5.5M** / ~**22.9** vol-pp).
- **Affiliate P&L contest:** SK exit ~**38.2%** vol / ~**2.0%** BB — fight is affiliate margin, not user fee.
- **Single-venue fee power:** Intents ~**87.0%** of NEAR fees; BB dollars more concentrated than volume.
<!-- /AUTO:CONV_AFF -->

<!-- AUTO:DEFAULT_RAIL -->
### Default rail + judge call-order (exploratory)

- Unreferred/default path ≈**45.8%** of BB $ — that rail **is** the fee engine.
- Call-order: **SK-tax → mix → attest(parallel) → conversion → attach**. Do not sum. Hold until H1b.
- Delivery: **public + X** (~58h).
<!-- /AUTO:DEFAULT_RAIL -->

<!-- AUTO:MINT_NOT -->
### Mint ledger ≠ fee upside (exploratory)

- HSP-007 ~**$11.8M**/yr claim competes on the **issuance pool** — opex on mint, not Intents fee growth.
- HSP-029 alone → ~**24.7%** coverage; with stack wall ~**42.8%** — still pending-then-lagged at submit (~**58h** before deadline).
<!-- /AUTO:MINT_NOT -->

<!-- AUTO:D13_2025 -->
### Dense `_13` through 2025 (exploratory)

- **208 clusters**; overall still **not supported**.
- Prefer burning ~**58h** on **public repo + X dry-run** over finishing contest-year `_13` seals.
<!-- /AUTO:D13_2025 -->
