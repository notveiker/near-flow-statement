# MIX-SHIFT arithmetic — near.com-class vs SwapKit-class pipes

*Prop note for Investment Thesis track. As of November 2026. Window for measured capture: **2026-10-06 → 2026-11-04** unless noted. Machine-readable twin: [`data/derived/mix_shift_math.json`](../../data/derived/mix_shift_math.json). Scenarios are **arithmetic on committed metrics, not forecasts**. No path probability attached.*

---

## 1. Simple mix model

Denominators differ in the sources; the model keeps them explicit.

| Bucket | Share | Capture rate used | Label |
|---|---|---|---|
| **near.com-class** | ~**25%** of Intents (Q3 Nansen) | **20 bp**, 100% to NEAR wallet by stated policy / fee docs | Marketing + docs; **Gap:** Nov-window share |
| **SwapKit-class** | **38.2%** of 1Click = **21.1%** of Intents | **~0** explicit buyback ($159 / 30d vs $3.53M partner fees) | Measured |
| **Other** | residual ~**54%** of Intents if Q3 near.com holds | Residual identity; public AITR reference **9.49 bp** on *attached* slice only | Residual / Gap |

**Calibration stress (Gap, labeled):** Q3 near.com at 25% × 20 bp on current **$4.0B** Intents would alone imply ~**$2.00M**/30d — essentially the entire measured wallet print (**$1.99M**, **4.98 bp**). That identity forces “other + SwapKit” net capture ≈ **0** if both Q3 share and 20 bp fully land. Separately, `fefundsadmin` frontend inflows (**$616.9K**) at 20 bp imply only ~**7.7%** of Intents volume — so either Nov near.com share is below Q3, effective walleted rate is below 20 bp, and/or a large near.com / CIF slice sits in **unattested escrow** ($823.7K of buyback-wallet NEAR). Do not treat 25% × 20 bp as a reconciled Nov level; use it as the **policy differential** for mix moves.

**Measured venue blend (committed):** captured **4.98 bp**, gross **15.3 bp**, capture share **32.5%**, rev **$1.99M**/30d, run-rate **~$24.2M**, issuance offset **15.81%**.

---

## 2. Scenario table — SwapKit-class → near.com-class

**Mechanism (arithmetic only):** move \(x\) percentage points of **Intents** volume from **0 bp** explicit capture to **20 bp** full-fee front.

\[
\Delta \tau = x \times 0.20\ \text{bp},\quad
\Delta \text{rev}_{30d} = x \times \$80\text{K},\quad
\text{annualised} \approx \Delta\text{rev}_{30d}\times 365/30
\]

Headroom: SwapKit is **21.1** Intents pp; **+15** pp uses most of that pipe.

| Mix shift (Intents pp) | Captured bp | Δ bp | Capture share | 30d rev | Run-rate | Issuance offset |
|---|---|---|---|---|---|---|
| **0 (baseline)** | **4.98** | — | **32.5%** | **$1.99M** | **$24.2M** | **15.8%** |
| **+5** | **5.98** | +1.0 | 39.1% | $2.39M | $29.1M | 19.0% |
| **+10** | **6.98** | +2.0 | 45.6% | $2.79M | $34.0M | 22.2% |
| **+15** | **7.98** | +3.0 | 52.2% | $3.19M | $38.8M | 25.4% |

*Issuance offset scaled from ladder baseline 15.81% × (new rev / 1.99), same style as `catalyst_math.json`. Volume held flat at $4.0B. Not a forecast.*

**Alternate denominator:** if \(x\) is pp of **1Click** only ($1.104B), each pp adds ~**0.055** captured bp on Intents (~**$0.27M** annualised) — ~3.6× smaller than Intents-pp arithmetic.

Orthogonal lever (not double-counted here): attachment creep at AITR **9.49 bp** on contestable public flow (`catalyst_math.json`). Mix shift and attachment are different dials; stacking them without interaction terms overstates.

---

## 3. Whale concentration → mix fragility

Committed Explorer: swaps **≥ $10K** are **3.4%** of count and **77.1%** of 1Click volume.

**Read:** volume shares (and therefore mix) are **ticket-fragile**, not retail-stable. A small whale cohort can move several Intents pp between SwapKit-class and near.com-class without any change in swap *count* mix. Ledger-via-SwapKit alone is **13.7%** of 1Click (~**3.8%** of Intents) — one downstream wallet is already a multi-pp mix object. Capture that depends on frontend mix inherits the same fragility: order-flow reallocation, not gradual share drift, is the plausible path for both upside arithmetic and reverse-mix falsifiers.

---

## 4. Proprietary metric — capture per point of mix

**Definition:** dollars of **annualised** NEAR wallet capture per **one percentage point** of Intents volume moved from zero-buyback pipe → 100%-fee front at 20 bp.

| | Value |
|---|---|
| Δ captured bp / Intents pp | **+0.20 bp** |
| Δ revenue / 30d / pp | **$80,000** |
| **Capture per point of mix (annualised)** | **~$0.97M / pp** ($973K) |

So **+10 pp** ≈ **+$9.7M** annualised run-rate and **+2.0** captured bp on flat volume — the same order of magnitude as moving attachment from 43% → ~60% in `catalyst_math.json`, via a different commercial object (owned frontend mix vs buyback-line attachment).

1Click-pp alternate: **~$0.27M** annualised per pp of 1Click.

---

## 5. Falsifiers

1. **Mix reverses** — SwapKit-class / other zero-buyback share rises; near.com-class share falls. Arithmetic above runs with a minus sign; captured bp and offset compress.
2. **SwapKit exit (or Ledger-inside-SwapKit exit)** — volume narrative loses **38.2%** of 1Click / **21.1%** of Intents; traceable captured-revenue loss only **~2%**, but escrow-inclusive ceiling **43%** (all-escrow path **73.7%**). Mix-shift upside and exit risk are the same pipe.
3. **Confidential default stays near.com-only** — partner pipes remain public with explicit buyback ≈ 0; privacy-led capture does not migrate into SwapKit-class volume. Whale tickets can stay on hardware-wallet routes.
4. **Policy–wallet break** — near.com 20 bp / “100% to NEAR wallet” fails to appear in DefiLlama revenue wallets at that rate (CIF retained “for its own account”; escrow stream unattested). Differential 20−0 collapses toward 0−0 for token claim.
5. **Attachment rollover on non-SwapKit public flow** while mix stays aggregator-heavy — removes the parallel dial in `catalyst_math.json`.

---

## Gaps

- near.com **Nov 2026** share of Intents (Q3 ~25% only).
- Escrow unshield attribution: near.com vs CIF vs other private settlement.
- near.com presence inside vs outside Explorer 1Click channel table.
- Whale elasticity to confidential-default UX.
- SwapKit / Ledger / Trust / Tangem Commercial Agreement text.

---

## Proprietary punch (8–12 lines)

1. Venue capture **4.98 bp** coexists with a pipe that is **38% of 1Click at ~0** explicit NEAR buyback — mix is the missing term in the average.
2. Policy differential is brutal and simple: **0 → 20 bp** per dollar moved SwapKit-class → near.com-class; **+0.20 captured bp per Intents pp**.
3. **Capture per point of mix ≈ $0.97M annualised / pp** on $4.0B Intents — proprietary unit for scoring frontend share without a take-rate war.
4. **+10 pp** arithmetic: **6.98 bp** captured, **~$2.79M**/30d, **~$34M** run-rate, **~22%** issuance offset — flat volume, no SwapKit 50/50.
5. **+15 pp** uses most of SwapKit’s **21.1%** Intents headroom; treat as upper arithmetic, not a path.
6. Q3 **25% × 20 bp** nearly saturates the whole **$1.99M** wallet print — Nov level is **unreconciled** (fefunds implies ~**7.7%** at 20 bp; escrow may hide the rest).
7. Whales: **3.4%** of swaps → **77.1%** of 1Click vol ⇒ mix is **ticket-fragile**; Ledger-via-SK alone is multi-pp.
8. SwapKit exit: revenue traceable hit **~2%**, volume hit **~21%** Intents; escrow ceiling **43–74%** — same pipe that supplies mix upside.
9. Confidential default only on near.com leaves partner pipes at explicit **0**; privacy does not automatically fix aggregator capture.
10. Score **capture-per-mix-pp** and near.com share beside AITR×attachment; volume share without pipe capture overstates the token claim.

*Not investment advice. Exploratory prop research only. As of Nov 2026.*
