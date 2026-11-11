# Buyback quality & float sink — NEAR

*Prop note. As of **2026-11-11**. Window metrics through **2026-11-04**. Exploratory / not a pre-registered test. No volume-growth assumption. Derived arithmetic in `data/derived/float_sink.json`.*

---

## Proprietary punch

1. What is measured is a **balance**, not a burn: `buybacks.multisignature.near` holds **2.187M NEAR**, held under governance discretion (“no specific mechanism is guaranteed”).
2. Annualised capture (**$24.2M**) is real wallet inflow; scarcity is not — stock can recirculate via opex/spend.
3. **Days-of-issuance covered (DIC)** = wallet ÷ net mint = **24.8 days** at 88,295 NEAR/day; ~**38 days** if mint scales to the 1.6% HSP-029 cap.
4. **Scarcity half-life** ≈ **60.5 days**: time to recirculate half the stock if spends run at today’s capture NEAR rate with buys paused.
5. Permanently removing **100%** of $24.2M offsets only **~20.5%** of annual net issuance today (~**31.5%** at 1.6% cap) — still a minority of mint.
6. To cover **25% / 50% / 100%** of today’s mint as a hard sink needs **~1.2× / 2.4× / 4.9×** current capture; HSP helps the denominator, not the quality of the sink.
7. Soft sinks ranked by DIC: AI inference floor (**~8.5d**) < buyback wallet (**~25d**) ≪ NRR holdings (**~178d**, unbond **1–2d**) ≪ LST TVL (**~611d**, LST-liquid).
8. NRR (~**$56M**, **1.2%** mcap) and LST (~**$196M**) are larger *bonded* sleeves than buybacks, but both are **soft** exits — not substitutes for fee→burn.
9. HSP-029 raises held-offset arithmetic from **15.8% → ~24%** of issuance with flat capture; it does **not** harden recirculation risk.
10. Without volume growth, the token link hardens only via **policy**: programmatic burn, irrevocable lock, or vote-escrow / auto-split that removes spend discretion.
11. Escrow path funds **~59%** of recent buyback NEAR — capture *magnitude* and capture *attestation* are separate soft spots.
12. Score **DIC + scarcity half-life + % of capture permanently removed** before ETF AUM or AI stake headlines.

---

## Q1. What is measured: wallet balance, held not burned, discretion

### Takeaway
The observable “buyback” series is NEAR landing in named revenue wallets and accumulating in `buybacks.multisignature.near`. It is **inventory under policy**, not float destruction.

### Cited findings
- Buyback wallet balance **2.187M NEAR**; explicitly **held, not burned** (`REPORT.md`; `metrics.json` `buyback_wallet_near_m`).
- Three wallets DefiLlama counts (`fefundsadmin`, `1csfundsadmin`, `buybacks.multisignature.near`); buyback wallet alone is **68.5%** of NEAR implied by holders-revenue framing (`buyback_wallet_vs_implied_pct`; PREREG-ADDENDUM gap check vs `fefundsadmin`).
- Governance language: “no specific mechanism is guaranteed” — discretion retained (`docs/structural-thesis.md` citing *Evolving NEAR Tokenomics*).
- ~**58.8–59.1%** of recent buyback-wallet NEAR arrived as confidential-escrow unshields (`escrow_share_of_buyback_near_30d_pct`); public collectors alone are **4.53%** of issuance vs **15.81%** all wallets.
- F1 forward test (resolves **2026-11-14**) checks the buyback wallet **balance band** — stock path, not burn path (`docs/catalysts-and-path.md`).

### Inferences
- DefiLlama “holders revenue” prices a **claim on policy**, not a closed burn loop.
- Treating wallet growth as scarcity double-counts if the same coins later fund opex, grants, or market-making inventory.

### Gaps
- No published spend schedule for the multisig; no observed programmatic burn of fee NEAR in-repo.
- Whether Confidential Infrastructure Fee must reach buybacks is contractual permission, not obligation (**Gap**: live forwarding rule).

---

## Q2. How much of $24.2M must be permanently removed to matter vs ~88k NEAR/day?

### Takeaway
At committed metrics price **$3.67**, $24.2M ≈ **6.59M NEAR/year** ≈ **18.1k NEAR/day**. That is **~20.5%** of annual net issuance if *every* dollar is permanently removed — and **less** as a *held* offset (**15.81%** of daily mint already counted as wallet inflows). “Matters” as a hard float sink at ≥25% of mint already requires **more than today’s entire capture**.

### Arithmetic (no volume growth)

| Permanent removal target | NEAR/year needed @ 88,295/day | USD @ $3.67 | Share of $24.2M capture | After HSP 1.6% mint (~57.4k/day) |
|---|---|---|---|---|
| 25% of net issuance | 8.06M | $29.6M | **122%** | 79% of capture |
| 50% of net issuance | 16.1M | $59.1M | **244%** | 159% of capture |
| 100% of net issuance | 32.2M | $118.3M | **489%** | 318% of capture |
| 100% of *today’s* capture burned | 6.59M | $24.2M | 100% | covers **~31.5%** of post-HSP mint |

Held-path comparison: same capture flat + HSP ramp moves **held** issuance offset **15.81% → ~24.3%** (`15.81 × 2.46 / 1.6`) — denominator shrink, not sink hardening (`REPORT.md`; `catalysts-and-path.md`).

### Inferences
- HSP-029 is an issuance lever; burn/lock is a quality lever. Stacking both still leaves capture a **minority** of mint unless take or attachment rises (out of scope here if volume/attach assumed flat at today’s run-rate).
- “Buybacks offset issuance” as marketed is closer to **soft ~16%** (held inflows) than to a supply sink that clears net mint.

### Gaps
- Net issuance 88,295/day is window-measured; post-HSP daily mint is a **scaled approximation** (2.46%→1.6%), not an epoch schedule print (`float_sink.json` note).
- USD conversion uses `metrics.json` **$3.67**; ETF snapshot **$3.56** — price path moves the USD thresholds, not the NEAR ratios.

---

## Q3. Soft sinks compared

| Sink | Size | Days of issuance (DIC) | Exit / recirculation | Quality |
|---|---|---|---|---|
| AI inference stake | **>750k** NEAR | **~8.5** | Unstake / product churn | Collateral demand, not fee sink |
| Buyback wallet | **2.187M** NEAR | **24.8** | Governance spend / opex | Discretionary inventory |
| NRR (Bitwise) | ~**15.7M** NEAR / **$55.9M** (1.2% mcap) | **~178** | Unbond **~1–2 days** (~4 epochs) | Soft institutional stake |
| LST (LiNEAR+Meta+RHEA) | **~$196M** / ~**54M** NEAR | **~611** | LST tradeable | Bonded underlying, liquid claim |

Sources: `REPORT.md`; `catalysts-and-path.md`; `capital-markets.md`; `etf_nrr.json`; `lst_vs_stake.json` (LiNEAR ~$47M, Meta Pool ~$80M, RHEA LST ~$69M; LST **9.27%** of stake).

### Inferences
- By stock size, buybacks are **small** vs ETF+LST sleeves; by *policy hardness*, buybacks are the only fee-linked line — and they are the softest of the fee-linked claims because they are unburned and discretionary.
- NRR in-house staking converts creations into bonded NEAR, but NEAR’s short unlock makes ETF stake a **soft float sink**; sponsor fee (~**$0.42M/yr** at current AUM) is a thin mechanical sell (~**1.3 days** of mint) — second-order (`capital-markets.md`).
- AI stake >750k is smaller than the buyback wallet and is not a DefiLlama revenue line (`ai-agents-evidence.md`).

### Gaps
- Exact NRR staked vs unstaked split after mid-Oct **Gap** (early-Oct ~98% staked reported; not primary-confirmed later).
- Live AI inference stake above the **>750k** floor **Gap**.
- Exchange hot-wallet float vs these sinks **Gap** (H1b label coverage **20%**).

---

## Q4. Proprietary metrics: DIC & scarcity half-life; recirculation risk

### Definitions
- **DIC (days-of-issuance covered)** = `buyback_wallet_NEAR / net_issuance_NEAR_per_day` → **24.8** today; **38.1** at approximate 1.6% mint.
- **Scarcity half-life** = days to recirculate **half** the buyback stock if governance spends/opex at the current annualised-capture NEAR rate (**~18.1k NEAR/day**) with **buys paused** → **~60.5 days**; full exhaustion **~121 days**.

### Recirculation risk (governance spends / opex)
Structural thesis falsifier already states it: governance pauses buybacks, spends wallet NEAR on opex, or recycles holdings into liquid supply — breaking the holders-revenue interpretation used since **2026-02-23** (`structural-thesis.md`). Under that path:
- DIC collapses as stock falls even if trailing “revenue” looks fine.
- HSP-029 does not protect against recirculation; it only slows the competing mint.
- ETF redemptions can return bonded NEAR to venues inside **1–2 days**, so capital-markets “sink” and buyback “sink” can both soften in the same stress window.

### Inferences
- A rising wallet balance with a short scarcity half-life is **fragile scarcity**.
- Score **% of capture permanently removed** and **DIC trend** alongside attachment %; do not equate DefiLlama revenue with float reduction.

---

## Q5. Policy changes that harden the token link without volume growth

| Policy | What it does | Hardness | Volume growth needed? |
|---|---|---|---|
| **Programmatic burn** of fee/buyback NEAR | Converts $24.2M path into ~20.5% (today) / ~31.5% (HSP 1.6%) of annual mint removed | Hard | No |
| **Irrevocable time-lock** (multi-year) | Blocks opex recirculation for tenor | Medium–hard until unlock | No |
| **Vote-escrow (veNEAR)** of buyback stock | Delays recirculation; binds to governance | Soft–medium | No |
| **Auto-split rule** (contract: X% burn / Y% lock / Z% discretionary) | Removes “no mechanism guaranteed” | Depends on X | No |

### Inferences
- Attachment/mix raise the *numerator* without volume growth but still leave coins **held** unless paired with burn/lock.
- The minimum credible hardening is a **published, automatic** disposal rule on wallet inflows; discretionary multisig accumulation alone does not clear a scarcity underwrite.
- HSP-029 + burn of flat capture is the cleanest no-volume stack in the repo’s own arithmetic — and still leaves mint majority-uncovered.

### Gaps
- No drafted HSP-style proposal for buyback burn/lock observed in this pass (**Gap**).
- Peer comparison of burn vs holders claim (e.g. Chainflip-style) is structural only here — not a prediction that NEAR adopts it.

---

## Interaction: HSP-029 × ETF staking × buyback quality

- **HSP-029** (timelock **2026-11-16**; ramp starts ~one quarter later): shrinks issuance; lifts *held* offset % if capture flat; **does not** change held→burned status.
- **NRR staking**: larger soft DIC than buybacks; narrative competitor; mechanical demand orthogonal to Intents fees; unlock fast enough that outflows transmit.
- **Buyback quality**: sole fee→token inventory link; quality bottleneck is **discretion + no burn**, not AUM headlines.

**Falsifiers for “fees create scarcity.”** Wallet drawdown without matching burn; opex financing from buyback stock; CIF retained “for its own account” and not swept; escrow unshields reclassified as non-fee; HSP ramp delayed/cancelled while recirculation continues.

---

## Gaps (register)

1. Spend/opex policy for `buybacks.multisignature.near` unpublished; no burn observed.
2. Escrow / CIF fee-stream attestation incomplete (~59% of buyback NEAR).
3. NRR staked share after mid-Oct 2026 not primary-confirmed.
4. AI inference stake live total above >750k floor unknown.
5. Exchange-float share of circulating unpinned (labels 20%).
6. Post-HSP daily mint is scaled from 2.46%→1.6%, not epoch-level.

*Not investment advice. Prop research only.*
