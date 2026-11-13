# Fee waterfall & token capture — NEAR Intents vs THORChain / Chainflip / Maya

*Prop note for Investment Thesis track. As of November 2026. Window for measured Intents capture: **2026-10-06 → 2026-11-04** unless noted. Figures from committed repo metrics, fee docs, DefiLlama adapters, and peer primary docs cited in-repo. **Marketing** = public FAQ / blog policy language. **Measured** = Explorer, wallet inflows, or DefiLlama series reconciled in-repo. Where unsupported: **Gap**.*

---

## Q1. Full fee waterfall for a typical 1Click / Intents swap

### Takeaway
User all-in cost is **listed appFees + ~8.5 bp excess execution** (solver/gas/pip), not DefiLlama “fees” alone. NEAR’s token claim is only what lands in three revenue wallets (~**4.98 bp** of DefiLlama volume); the on-chain protocol fee is **1 pip**. Distribution (esp. SwapKit wallets) keeps most listed bp; marketing 50/50 is not the SwapKit reality.

### Cited Findings

**Layer stack (commercial order of claim)**

| Layer | Who | Rate / role | Label | Source |
|---|---|---|---|---|
| 1. Frontend / affiliate `appFees` | Wallet / aggregator (Ledger, Trust, Tangem, LI.FI, Rango, ZODL, …) | User-visible listed bp; SwapKit subchannels **13.8–132.6 bp** partner fee by channel; Ledger-heavy bucket listed avg **~140.7 bp** | Measured (Explorer) | `metrics.json` `swapkit_subchannels`, `explorer_realized_cost_by_listed_bp`; [Fee Configuration](https://docs.near-intents.org/integration/distribution-channels/1click-api/fee-config) |
| 2. 1Click Infrastructure Fee | Intents Technology | Authenticated default: **20 bp** (1 bp stables/same-asset); with `appFees` marketing default **50/50** and 1Click floor ≥20 bp; unauthenticated **+25 bp** on developer fee; Commercial Agreements override | Marketing default / docs; measured exceptions | [Fees](https://docs.near-intents.org/resources/fees); [1Click Terms Schedule 1](https://docs.near-intents.org/security-compliance/terms-of-service) |
| 3. Native frontend | near-intents.org / near.com | **0.2% (20 bp)** → `fefundsadmin.sputnik-dao.near`; FAQ: near.com directs **100%** of fees to a NEAR revenue wallet | Docs + marketing FAQ | [Fees](https://docs.near-intents.org/resources/fees); [revenue.near.org](https://revenue.near.org/) |
| 4. Explicit buyback appFee | Named buyback collector → `buybacks.multisignature.near` | Block3: **4.08 bp** of 1Click volume; **43.0%** of volume carries an entry; channel examples: no-referrer **10 bp**, Trust direct **20 bp**, LI.FI **2.8 bp**, Rango **4.1 bp**; SwapKit Trust route **0 bp** | Measured | `metrics.json` take_b3_*, buyback_fee_by_channel; `docs/intents-fee-flows.md` |
| 5. Quote-improvement share | Collector B → buybacks | When fill beats quote (~30 min), **50/50** integrator/protocol; window **~$108.6K** to buybacks; sample median **1.13 bp** of output (max 30.5) | Docs + measured | [Fees](https://docs.near-intents.org/resources/fees); `partner-concentration.md` |
| 6. Solver / MM spread | Solvers as principal | Residual inside realized excess; solvers keep bid-ask; optional Solver Access Fee “may be zero” | Docs; excess measured, solver P&L Gap | [Solver Terms](https://partners.near-intents.org/legal/solver-terms); `explorer_excess_over_listed_bp` **8.5** |
| 7. Protocol fee | `intents.near` → `fee_collector` | **0.0001% = 1 pip** | Docs | [Fees](https://docs.near-intents.org/resources/fees) |
| 8. Confidential Infrastructure Fee | Intents Technology “for its own account”; no AppFee | Rate route-dependent; may be directed to ecosystem recipients (permission, not obligation) | Docs | [1Click Terms §6.8 / Schedule 1](https://docs.near-intents.org/security-compliance/terms-of-service) |
| 9. Revenue wallets / holders | Three wallets DefiLlama counts | **418.8K NEAR (~$2.01M)** = **100.9%** of DefiLlama Intents revenue; **~4.98 bp** captured take; NEAR **held, not burned** | Measured | `metrics.json`; DefiLlama near-intents adapter |
| 10. Gas / relayer | NEAR L1 + relayers | Excess includes destination gas; census: **43%** of chain txs relayed; Intents **9.4%** of gas; top relayer **83%** of `execute_intents` | Measured (gas share); bp split of excess Gap | `REPORT.md` census; `docs/intents-fee-flows.md` |

**Composition of user all-in (measured windows)**

- **Listed app fees on 1Click:** Explorer **44.4 bp** blended (`explorer_appfees_bp`); partner-only line **40.3 bp** in block3 (`take_b3_partner_bp`); partner fees **$4.45M**, of which **$4.21M** had **no** buyback entry.
- **Excess over listed ($1K–$50K):** **+8.5 bp** average realized (`amountIn − amountOut` vs listed). Ledger-class (≥81 bp listed): listed **~140.7** → realized **~149.3**. Stable routes (<2 bp listed): listed **~0.7** → realized **~1.9**.
- **NEAR captured (DefiLlama volume basis):** **4.98 bp** (`take_captured_bp_30d`); gross DefiLlama fees **15.3 bp** / **$6.12M** on **$4.0B**.
- **Buyback wallet source split (USD K):** explicit collector A **460.4**; quote-improvement B **108.6**; confidential-escrow unshields **823.7 (59.1%)**.
- **On-chain partner payout:** sampled SwapKit/ZODL/other partner fees paid at **full listed rate** to implicit accounts (Ledger ~145 bp → `c4d748df…`, Trust 70 bp → `2f09a4dc…`) — no 50/50 haircut inside the listed line (`partner-concentration.md`).
- **SwapKit:** **38.2%** of 1Click volume; partner fees **$3.53M**; explicit buyback fees **$159** (~**0.0045%** of those partner fees).

**Illustrative waterfalls (not forecasts — channel templates)**

1. **Trust via SwapKit (~6.4% of 1Click vol):** user ≈ **70 bp** partner + **~8.5 bp** excess + **1 pip**; NEAR explicit buyback **0 bp**. Partner keeps listed 70 on chain.
2. **Trust direct (~2.4%):** partner **0 bp**; buyback **20 bp**; + excess.
3. **Ledger via SwapKit (~13.7%):** partner ~**133 bp** channel avg (bucket ~**141** listed); buyback typically **0**; realized ~**149**.
4. **No-referrer / default (~18.7% vol among buyback-fee channels’ vol_share):** buyback **10 bp** dominates that channel’s NEAR line; **45.8%** of *explicit buyback fee dollars* come from no-referrer.
5. **near.com (marketing):** **20 bp** frontend, **100%** to NEAR wallet by FAQ; confidential mode → Infrastructure Fee retained by Intents Technology (forwarding unattested). Q3 near.com ~**25%** of Intents volume (Nansen; marketing share claim).

### Inferences
- DefiLlama “15.3 bp fees” understates **user** cost on wallet routes (listed 40–140+ bp) and overstates **token** claim (~5 bp wallets). The investment-relevant waterfall is **user all-in → distribution → (optional) NEAR wallets**, not L1 gas.
- 1Click Infrastructure Fee on SwapKit-class deals is either zeroed by Commercial Agreement or buried inside the 8.5 bp excess / confidential path — it does **not** appear as a haircut on the listed partner line.
- Protocol pip is economically irrelevant next to distribution bp.

### Gaps
- Exact per-swap split of the **8.5 bp** excess into solver margin vs destination gas vs pip.
- Solver Access Fee level as of Nov 2026 (docs: “may be zero”).
- Full fee composition on the **non-1Click** half of Intents (~**44.8%** of DefiLlama one-sided volume) — Explorer does not show it.
- Commercial Agreement text with SwapKit / Ledger / Trust / Tangem (not public).
- Whether Confidential Infrastructure Fee is operationally swept to buybacks vs retained (unattested).

---

## Q2. Peers: who captures what, and how much reaches native token / buyback / LP

### Takeaway
Vault peers (THOR / Maya / Chainflip) push a large share of swap economics to **LPs and bonded nodes**, with a smaller, rule-based **token claim** (Maya 10% holders; Chainflip network fee → FLIP buy/burn). Intents pushes economics to **distribution + solvers**, with a **discretionary wallet/buyback** claim. DefiLlama “revenue” is **not like-for-like** across the four.

### Cited Findings

**Peer blended take (measured, 30d to 2026-11-04)** — `metrics.json` peers:

| Venue | Vol | Gross fee bp | Fees $ | Peer vol share |
|---|---|---|---|---|
| NEAR Intents | $4.0B | **15.3** | $6.12M | 55.7% |
| THORChain | $1.8B | **12.3** | $2.22M | 25.1% |
| Chainflip | $0.85B | **31.5** | $2.66M | 11.8% |
| Maya | $0.53B | **9.4** | $0.5M | 7.3% |

**THORChain (docs + ADR; measured blend only)**

- User pays fixed **network fee** + dynamic **slip-based liquidity fee**.
- **Incentive Pendulum** splits system income / liquidity fees between **node operators (bond)** and **LPs**.
- **Affiliates** may take up to **1,000 bp** user-side; **REVSHARE** can pay affiliates a share of liquidity fees from reserve (**capped 50%**) without raising user fee — explicit fight for SwapKit order flow ([ADR-029](https://blog.thorchain.org/adr-029-affiliate-revenue-share); affiliate guide).
- Token link: RUNE demand via **bond underwriting** + pendulum, optional burn/dev/TCY/POL dials — not a NEAR-style wallet sweep of affiliate fees.
- **RUSH:** **Gap** in repo primary notes (no committed RUSH fee table). Treat affiliate + REVSHARE as the documented distribution layer; do not invent RUSH bp.

**Chainflip (docs)**

- **LP fee 0.10–0.15%** (10–15 bp) to LPs per pool.
- **Network fee 0.10%** (10 bp; **0.01%** internal stables, $0.5 min) → buys FLIP from USDC-FLIP pool → **burns** (holders via supply).
- Optional **boost 0.05–0.3%** to boost-pool LPs.
- Validators earn emissions/stake, **not** the network fee.
- Measured blend **31.5 bp** = LP + network + boost/other stacked on thinner JIT book — **Gap** on exact 30d LP vs burn split inside that blend.

**Maya (docs + DefiLlama)**

- Slip-based fees like THOR; network/outbound to reserve; **ILP** funded partly from fees/supply.
- **10% of protocol fees to $MAYA holders** (paid in CACAO) — DefiLlama Revenue ≈ that 10% claim.
- Dual-token: CACAO (bond/settlement) vs MAYA (cash-flow claim).
- Implied **token-claimable bp ≈ 0.10 × 9.4 = 0.94 bp** if the 10% rule applies to the DefiLlama fee base (structural × measured gross).

**Intents (measured capture vs peers’ structural claim)**

- Gross **15.3 bp** → captured wallets **4.98 bp** → **capture share 32.5%**.
- Nansen (Oct 2026 post-Q3): lifetime capture ~**16.4%**; trailing 30d ~**28.4%** (down from 30.5%) — **measured third-party**, not RPC.
- HoldersRevenue since **2026-02-23** = wallet NEAR used to buy NEAR (**held, not burned**).

### Inferences
- Rank by **gross fee bp** (Chainflip > Intents > THOR > Maya) is not rank by **token-claimable bp**.
- Rank by **token design tightness**: Chainflip burn and Maya 10% are **harder claims** than Intents’ discretionary buyback + Commercial Agreement exceptions; THOR’s claim is **bond/pendulum**, not fee→buyback.
- Affiliates on THOR are **subsidizable from reserve (REVSHARE)**; Intents affiliates are paid from **user-listed appFees**. Different distribution tax incidence.

### Gaps
- 30d LP / node / affiliate / burn split for THOR and Chainflip inside `metrics.json` fee_bp (not in repo).
- RUSH product fee schedule (not in committed research notes).
- DefiLlama holders-revenue series for THOR/Chainflip/Maya aligned to the same window as Intents wallet reconciliation (**Gap** for peer $ holders figures here).

---

## Q3. Where Intents is advantaged / disadvantaged on capture share — and what flips the disadvantage

### Takeaway
**Advantaged** on **gross fee extraction per dollar of volume** vs THOR/Maya and on **volume share**, and on a **partner-proof confidential fee vertical**. **Disadvantaged** on **captured bp / gross bp quality and stickiness**: ~**1/3** of DefiLlama gross reaches NEAR wallets; partners keep **≥1.81×** that on the 1Click half; largest pipe (SwapKit) pays NEAR ~**$159** explicit vs **$3.53M** partner fees. The commercial move that flips disadvantage **without** a take-rate war is **attachment + mix**, not SwapKit 50/50.

### Cited Findings

| Metric | Intents | Implication |
|---|---|---|
| Capture share (captured÷gross) | **32.5%** | Minority of DefiLlama gross |
| Captured bp | **4.98** | Token claim per $ volume |
| Gross bp | **15.3** | Above THOR 12.3 / Maya 9.4; below Chainflip 31.5 |
| Partners kept vs NEAR rev (1Click half) | **≥1.81×** | Distribution owns margin |
| Partner bp / explicit bb bp (block3) | **40.3 / 4.08 ≈ 9.9×** | Explicit lines favor partners ~10× |
| Buyback attachment | **23.6% → 43.0%** of 1Click vol | Rising without SwapKit share fall (35.6→38.2%) |
| AITR (bb bp ÷ attach) | **4.08 / 0.43 = 9.49 bp** | Rate *on attached* volume (`catalyst_math.json`) |
| near.com mix | ~**25%** Q3 Intents vol, 100% fee direction (marketing) | High-capture vertical still minority |
| Confidential | No AppFee; fee “for its own account” | Structural max claim; attestation Gap |
| Peer mcap/rev (REPORT) | NEAR ~**217×** vs THOR ~**16×**, Chainflip ~**5×** | Volume leadership ≠ cheap capture multiple |

**Structural advantage**
- Can price **15+ bp gross** at majority share while vault peers either price lower (THOR/Maya) or take high fees on less volume (Chainflip).
- Confidential mode removes partner contractual claim on that fee line.
- Attachment can rise with SwapKit share flat — NEAR-side lever exists inside public 1Click.

**Structural disadvantage**
- Capture share is **contractually soft** (Commercial Agreements, Schedule 1 discretion, governance “no mechanism guaranteed”).
- **Distribution tax** on DefiLlama gross: supply-side **10.32 bp / 15.3 = 67.5%** stays with affiliates/solvers (DefiLlama SupplySideRevenue framing).
- Token quality: **held not burned**; **~59%** of buyback-wallet NEAR is escrow-unattested.
- Same SwapKit shell hosts THOR REVSHARE / Chainflip / Maya — settlement is contestable.

**Commercial moves that flip disadvantage (ordered by volume risk)**

| Move | Mechanism | Capture arithmetic (committed) | Volume risk |
|---|---|---|---|
| **A. Attachment creep** | More vol carries buyback entry at ~9.5 bp AITR | Attach 60% → ~**5.69** explicit bb bp, ~**6.59** captured bp, ~$2.64M /30d (`catalyst_math.json`) | Low if whales grandfathered |
| **B. Mix → near.com / 100% fronts** | Shift $ from SwapKit-class to 100% NEAR wallet | Each $ shifted raises capture share without repricing wallet users | Medium (must win UX) |
| **C. Confidential + attested forward** | Grow no-AppFee vertical; prove sweeps | Raises economic take; today epistemic Gap | Low–medium |
| **D. True SwapKit share** | Force 50/50 or buyback line on Ledger/Trust/Tangem | Half of $3.53M SK partner fees ≈ **+$1.76M** ≈ **+16 bp** on $1.104B 1Click vol if fully shared — large | **High** (38% 1Click / ~21% Intents net) |
| **E. Raise floors / pip** | Universal take hike | Small unless large; hits whale **77%** of 1Click vol | Medium–high |

Preferred flip under “don’t kill volume”: **A + B + C(with attestation)**. D is the blunt fix and the fragile one.

### Inferences
- Disadvantage is not “low fees” — Intents already extracts more gross bp than THOR/Maya. Disadvantage is **who keeps the extracted bp**.
- Advantage on share is **rented distribution**; advantage on confidential claim is **real but opaque**.

### Gaps
- Elasticity of SwapKit volume to a forced 50/50 (not measured).
- near.com exact Nov 2026 share of Intents (Q3 Nansen only).
- Target capture rate from governance (none published).

---

## Q4. Race-to-zero risk on the NEAR buyback line vs partner lines

### Takeaway
Race-to-zero risk is **asymmetric**: the **NEAR buyback line** is the contestable residual that Commercial Agreements already zero on the largest pipe; **partner lines** stay fat (50–145 bp) because wallets own attention and users don’t cross-venue shop. THOR REVSHARE attacks Intents by **subsidizing affiliates without cutting user fees** — pressure lands on NEAR’s attachment/buyback, not on Ledger’s 145 bp.

### Cited Findings
- SwapKit: partner fees **$3.53M** vs buyback **$159** — buyback already ≈ zero on that pipe while partners do not race down.
- Trust dual route: SwapKit path **70 bp partner / 0 bp buyback** vs direct **0 / 20** — same wallet, NEAR line competes with partner monetization, partner line does not collapse.
- Attachment rose **23.6→43.0%** while partner bp stayed **32.5→43.7→40.3** — partners did not give back take as NEAR attached more.
- Partners kept ~**10×** NEAR explicit fee across three blocks (`docs/intents-fee-flows.md`).
- THOR ADR-029 REVSHARE: affiliate subsidy from **reserve**, user fee unchanged — designed to win SwapKit share against Intents without a user-fee race.
- Nansen trailing capture **28.4% vs prior 30.5%** while lifetime rose — soft on the margin even as attachment rose (composition / volume-definition effects possible; Sep 1 DefiLlama volume step noted in fee-flows).
- Docs invite exceptions to 50/50; forcing floors trades against volume narrative used for venue multiple.

### Inferences
- **Buyback line** faces race-to-zero / race-to-exception risk under aggregator competition and REVSHARE.
- **Partner lines** face little race-to-zero while hardware/mobile wallets remain price-makers for non-comparing users.
- NEAR’s observable defense is **attachment on contestable non-SwapKit flow** and **owned frontend mix**, not matching partner bp downward.
- A “race to zero” that matters for the token is **capture share and attachment rolling over**, not Intents’ blended 15.3 bp gross falling to Maya’s 9.4.

### Gaps
- Win-rate Intents vs THOR inside SwapKit after REVSHARE (only early THOR blog week-one data cited; no long window in repo).
- Whether new Commercial Agreements further zero buyback on LI.FI/Rango-class channels that still attach small bp.

---

## Q5. Proprietary metrics (from committed the repository numbers only)

### Definitions

1. **Capture share** \(C\) = `take_captured_bp / take_gross_bp`  
2. **Token-claimable bp** \(τ\) = captured bp for Intents; structural rule × gross for Maya; structural network fee for Chainflip (upper bound on burn claim, not measured split)  
3. **Distribution tax** \(D\) = `1 − C` = supply-side fraction of DefiLlama gross  
4. **Distribution leakage ratio** \(L\) = `partner_bp / explicit_buyback_bp` on 1Click (block3)  
5. **Attachment-implied token rate (AITR)** = `explicit_bb_bp / attach_share`  
6. **All-in token claim** \(α\) = `captured_bp / (gross_bp + excess_bp)` — token claim vs user cost proxy that adds measured excess to DefiLlama gross  

### Computed (committed inputs)

| Metric | Value | Inputs |
|---|---|---|
| \(C\) Capture share | **32.5%** | 4.98 / 15.3 |
| \(τ\) Intents token-claimable bp | **4.98 bp** | `take_captured_bp_30d` |
| \(D\) Distribution tax | **67.5%** | (15.3 − 4.98) / 15.3 |
| \(L\) Leakage ratio (1Click listed) | **9.88×** | 40.3 / 4.08 |
| AITR | **9.49 bp** | 4.08 / 0.43 (`catalyst_math.json`) |
| \(α\) All-in token claim | **20.9%** | 4.98 / (15.3 + 8.5) |
| 1Click listed-line tax | **90.8%** | 40.3 / (40.3 + 4.08) to partners |
| SwapKit NEAR share of SK fees | **0.0045%** | 159 / 3,528,900 |
| Maya \(τ\) (structural) | **0.94 bp** | 0.10 × 9.4 |
| Chainflip burn claim (structural network) | **~10 bp** of user stack; **~44%** of (10 + 12.5) LP+network mid | Docs; measured blend split **Gap** |
| THOR \(τ\) | **Gap** | Pendulum/affiliate split of 12.3 bp not in repo |

**Read:** Intents’ \(C\) (32.5%) looks similar to a mid Chainflip LP+network structural burn share (~44% of that sub-stack) and far above Maya’s hard **10%** fee claim — but Intents’ \(τ\) in **bp of volume** (4.98) still exceeds Maya’s (0.94) because Intents’ gross take is higher and volume larger. The proprietary tell is \(L ≈ 10×\) and SwapKit NEAR share ≈ **0**: capture share at the venue level masks a **pipe-level capture of ~0** on the dominant aggregator.

**Scenario arithmetic (not forecasts)** — `catalyst_math.json`: attach 60% → ~6.59 captured bp, ~$2.64M/30d, ~32.1% issuance offset if also at 1.6% cap; attach 80% → ~8.49 captured bp. Baseline issuance offset today **15.81%**.

### Inferences
- Judges reading only DefiLlama fees see 15.3 bp and 55% share. \(C\), \(L\), AITR, and SwapKit NEAR share show the token earns a **thin, unevenly attached** claim on a distribution-priced venue.
- Commercial success without \(L\) compression is still possible via AITR×attachment and mix — that path is in the committed scenario table.

### Gaps
- Peer \(C\) and \(L\) on identical DefiLlama definitions for the same 30d window.
- α using true user all-in on SwapKit (listed 70–140 bp) would show **much lower** token claim of all-in than the 20.9% proxy that uses venue gross 15.3 — Ledger realized ~149 bp with ~0 NEAR explicit ⇒ α ≈ **0** on that path.

---

## Proprietary punch (8–12 lines)

1. User all-in ≠ DefiLlama fees: wallet routes add **40–140+ bp** listed plus **~8.5 bp** excess; token claim is **~5 bp** wallets.
2. Marketing **50/50** fails the largest pipe: SwapKit partners take **$3.53M** vs NEAR buyback **$159**; on-chain payouts are **full listed** partner bp.
3. Protocol take is **1 pip**; economically Intents is a **distribution-fee venue** with a discretionary buyback sidecar.
4. Capture share **32.5%** coexists with leakage **L ≈ 9.9×** — venue-average masks pipe-level zero.
5. AITR **9.49 bp** on attached volume is the clean NEAR-side dial; attachment **23.6→43%** moved without SwapKit share falling.
6. Peers: Maya hard-wires **~0.94 bp** to holders; Chainflip burns ~**10 bp** network by design; THOR pays LPs/nodes and can **REVSHARE** affiliates — Intents alone routes most gross to wallets/aggregators.
7. Race-to-zero hits the **buyback line**, not partner bp; REVSHARE is structured to steal flow **without** cutting user fees.
8. Flip disadvantage with **attachment + near.com mix + attested confidential forward**; SwapKit 50/50 is +~**16 bp** on 1Click arithmetic and high exit risk (**38%** 1Click vol).
9. **~59%** of buyback-wallet NEAR is escrow-unattested — capture is a **4.5–15.8% of issuance range**, not a single DefiLlama print.
10. Scoreboard for the token is **τ, C, L, AITR, attachment %** — not peer volume share alone; volume share without those overstates NEAR’s claim on the waterfall.

*Not investment advice. Exploratory prop research only. As of Nov 2026.*
