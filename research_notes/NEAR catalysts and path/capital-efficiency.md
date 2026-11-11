# Capital efficiency — solver inventory vs bonded vaults

*Exploratory prop research as of November 2026. Twin: `data/derived/capital_efficiency.json`. Sources: `docs/structural-thesis.md`, `research_notes/NEAR Intents structural thesis/competitive-structure.md`, `data/derived/catalyst_math.json` (inventory), `REPORT.md` peers, `docs/fee-waterfall.md`. No Akash/Cronos/Pi. No bull case.*

## Takeaway

Intents runs settlement with ~**$229M** sitting in `intents.near` against **$4.0B**/30d volume — about **17×** monthly turnover, or **~1.7 days** of volume as working capital. Vault peers (THOR / Chainflip / Maya) underwrite native assets continuously: LP TVL **plus** a bond stack that docs target near **2:1** (THOR) or scale stake with vault size (Chainflip / Maya). Capital-light wins coverage and long-tail onboarding; it does **not** create NEAR as a security bond. Token claim stays the fee-waterfall (discretionary wallets), not bond demand.

---

## 1. Inventory days and turnover vs bond-to-TVL

### Intents (measured)

| Metric | Value | Source |
|---|---|---|
| Contract inventory | **$229.2M** | `catalyst_math.json` / REPORT |
| Volume (30d to 2026-11-04) | **$4.0B** | peers / REPORT |
| Turnover | **~17.4×** per 30d | \(4000 / 229.2\) |
| Days of volume in inventory | **~1.7** | \(30 / 17.4\) |
| Daily vol (implied) | **~$133M** | \(4000/30\) |
| Month-start stock path | ~$0.5M (Jan 2025) → ~$180M (Nov 2026) | fixed-price holdings series |

This is **settlement float** (bridge / verifier balances in transit), not farm TVL and not a NEAR accumulation claim — mix is mostly non-NEAR (ZEC #2, stables, BTC; see `inventory_mix.json`).

### Vault peers (docs + proxies)

| Venue | Underwriting design (docs) | Measured capital proxy in repo | Bond-to-TVL live ratio |
|---|---|---|---|
| **THORChain** | Proof-of-Bond; Incentive Pendulum targets ~**2:1** bonded RUNE : non-RUNE vault liquidity; theft slash ~**1.5×** | **Gap** — active bond vs vault TVL not in `metrics.json` | **Gap** |
| **Chainflip** | FROST vaults; FLIP stake slashable; docs emphasize stake must **scale with vault liquidity** | **Gap** — no FLIP-bond / vault TVL snapshot | **Gap** |
| **Maya** | THOR fork; secondary vaults secured by **~1.5×** bond slash; liquidity-node design puts bonded CACAO into pools | DefiLlama TVL ~**$5.2M** on **$0.53B**/30d vol | **Gap** on CACAO bond : vault |

**Conceptual stack (THOR target applied to matched vault size).** For vault TVL \(V\), a 2:1 bond target implies bonded capital \(\approx 2V\) **on top of** LP capital \(V\) already in the vault — total economic underwriting on the order of **\(\sim 3V\)**. Against Intents’ **$229M** float, that conceptual peer stack is ~**$687M** for the same vault size — roughly **3×** denser *if* Intents inventory were replaced by a fully bonded vault book. That is a **docs-ratio thought experiment**, not a live peer measurement.

**Maya TVL proxy (not bond).** \(530 / 5.2 \approx 102×\) turnover / ~**0.3 days** of volume in DefiLlama TVL — reads as a **thin vault book**, not as “more capital-efficient than Intents.” Without bond, the Maya figure understates protocol capital intensity.

### What “no 2:1 bond” means for scaling

Intents can add chains / long-tail assets without growing an economic bond that must track vault TVL 2:1. Coverage (~39 chains / ~229 assets vs THOR’s ~14 L1s / Chainflip’s thinner set) is the measured consequence. The cost of that flexibility is trust concentrated in PoA transit, upgradeable verifier, 1Click agent surface, and solver/relayer ops — not in a public bond ratio.

---

## 2. Who bears inventory risk

| | Intents | THOR / Maya / Chainflip |
|---|---|---|
| **Liquidity / inventory** | **Solvers as principal** — quote spread kept by solvers; Intents Technology is not the counterparty | **LPs** hold pool inventory (IL / slip); JIT LPs on Chainflip |
| **Economic security** | Bridges / **11-of-17** MPC-TEE signing; no continuous token bond underwriting vault TVL | **Bonded nodes** — RUNE / FLIP / CACAO slashable against vault theft / malice |
| **Operational continuity** | Concentrated **relayers / solvers** (census: top relayer ~83% of `execute_intents`) | Bonded validator set; vault L1 can **halt** on solvency / signing risk (THOR Nov 2026 chain halts) |
| **User-visible cost** | Distribution `appFees` + ~**8.5 bp** excess (solver/gas/pip residual) | Network + slip / LP fee (+ affiliate / REVSHARE overlays) |

**Inference.** Intents externalizes market-making risk to private balance sheets (solver / CEX inventory — **Gap** on share). Vault peers socialize inventory into LP TVL and socialize security into bonded token supply. Failure modes are non-substitutable: Intents → liveness / preferential execution / inventory refusal; vaults → bond-to-TVL break / slash / vault halt (`relayer_risk.json`).

---

## 3. Proprietary metric — protocol capital intensity (PCI)

**Definition.**  
\(\mathrm{PCI}_{30d} = \frac{\text{protocol-controlled capital (\$)}}{\text{30d volume (\$)}}\)

Lower PCI ⇒ less protocol-visible capital per dollar of settled volume. Interpret with care: Intents’ denominator is large; numerator **excludes** off-balance solver/CEX floats; vault numerators should ideally be **TVL + effective bond**, which the repo does not have for THOR/Chainflip.

| Venue | Capital used in PCI | Vol 30d | \(\mathrm{PCI}_{30d}\) | Days of vol |
|---|---|---|---|---|
| **Intents** | Inventory **$229.2M** | $4.0B | **0.0573** (~**5.7¢** per $1 vol) | **1.7** |
| **Maya** | DefiLlama TVL ~$5.2M (**bond Gap**) | $0.53B | **~0.0098** (TVL-only; understates) | ~0.3 (TVL-only) |
| **THORChain** | Live bond+TVL **Gap** | $1.8B | **Gap** | **Gap** |
| **Chainflip** | Live stake+vault **Gap** | $0.85B | **Gap** | **Gap** |

**Conceptual THOR-matched PCI** (docs 2:1 on \(V = \$229M\)): capital stack \(\sim \$687M\) / $4.0B vol ⇒ \(\mathrm{PCI} \approx 0.17\) — about **3×** Intents’ inventory PCI for the same volume base. Label: **illustrative**, not observed.

**Related flow check (census window).** Deposits ~**$80M**/day and withdrawals ~**$75M**/day through the contract — inventory turns like a venue, not idle AMM TVL.

**Fee-waterfall link.** Capital-light design does **not** raise NEAR’s token claim. Gross take **15.3 bp**; token-claimable \(\tau \approx 4.98\) bp; capture share **32.5%**; on-chain protocol fee **1 pip**. Peers hard-wire more of *their* stacks to LPs/nodes/burns (Maya ~10% holder cut; Chainflip network fee → burn; THOR pendulum). Volume leadership with thin PCI can still sit next to a rich mcap/rev multiple (NEAR ~**217×** vs THOR ~**16×**, Chainflip ~**5×** on DefiLlama-style framing — not like-for-like claims).

---

## 4. When capital-light wins vs loses

### Wins (long-tail / coverage / embed)

- Adding an asset or chain is an **ops + solver inventory + signing** problem, not a **raise bond / churn vault clients / seed LP** problem at 2:1.
- Wallets optimize for one integration and max pairs — Intents’ breadth (~hundreds of assets) vs vault pair-depth constraints.
- Confidential / ZEC-class flow can sit as settlement stock (ZEC ~12% of inventory) without waiting for a bonded ZEC vault to clear a pendulum.

### Loses (trust / incident / principal refusal)

- **Deposit-path incident** (PoA bridge, upgradeable verifier, 1Click agent, confidential TEE/shard) hits trust without a bond-slash recovery script vault users are trained to read.
- **Solver inventory refusal** or CEX-sourced fills drying up: depth vanishes off-balance; vaults at least show on-chain TVL until halt.
- **Relayer / submit concentration**: settlement can fail open on L1 while Intents throughput collapses — different from vault fail-closed on bond stress.
- **Token-value asymmetry in stress:** vault tokens have a mechanical underwriting role (bond must exist for TVL); NEAR’s Intents link is **discretionary fee → wallet**, so capital-light scaling does not create a scarcity floor from security demand.

---

## Gaps

1. **Live** bonded RUNE / FLIP / CACAO vs vault TVL on the same as-of date as Intents inventory — not in repo metrics.
2. Off-balance **solver / CEX inventory** for Intents — true system PCI understated if only `intents.near` is counted.
3. Maya / Chainflip / THOR DefiLlama TVL methodologies differ from Intents contract holdings; Maya’s extreme vol/TVL is **thinness**, not a clean peer PCI.
4. Exact fraction of Intents inventory that is “idle float” vs “active settlement WIP” — Gap.
5. Conceptual 2:1 → 3V stack is docs arithmetic, not a THORChain Midgard pull for Nov 2026.

---

## Proprietary punch

1. Intents holds **~1.7 days** of volume (~**$229M** / **$4.0B** 30d) — **~17×** monthly turnover; settlement float, not farm TVL.
2. Vault docs bind security to continuous **bond-to-TVL** (THOR target ~**2:1**; Chainflip/Maya stake-scale / **1.5×** slash) — Intents has **no** equivalent NEAR bond.
3. **PCI₃₀d (Intents inventory)** ≈ **0.057** ($ capital per $ volume); peer **bond+TVL PCI** is a labeled **Gap**.
4. Conceptual THOR stack on matched $229M vault ≈ **$687M** (~**3×** denser) — thought experiment only.
5. Inventory risk sits with **solvers as principal**; vault risk sits with **LPs + bonded nodes**.
6. Capital-light is why long-tail / embed share scaled; it is **also** why NEAR does not earn RUNE-like underwriting demand from Intents growth.
7. Token value path remains waterfall \(\tau \approx 5\) bp / capture **32.5%** / **1 pip** on-chain — orthogonal to PCI.
8. Maya TVL-only PCI looks “lighter” (~0.01) because the book is **thin**, not because Maya escaped bonding.
9. Capital-light **wins** on coverage; **loses** when trust/incident or solver/relayer refusal hits — fail-open ops vs vault fail-closed.
10. Rich NEAR multiple vs peers shows volume + thin PCI ≠ cheap claim on cash flow.
11. Census ~$80M deposits / ~$75M withdrawals per day confirms venue-speed turns; still not a token sink inside the contract.
12. Score **PCI + who-bears-risk + τ** together; volume share alone misreads capital structure and token claim.
