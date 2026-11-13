# Chain Signatures — necessary for Intents, not a separate cash-flow

*Prop note. As of November 2026. Twin: `data/derived/chain_signatures_link.json`. Gaps labeled.*

Sources: `REPORT.md` §7–8; `data/derived/census_{usage,metrics}.json`; `data/derived/sample_extras_results.json` + `pipeline/sample_extras.py`; `docs/structural-thesis.md`; `docs/intents-fee-flows.md` / `docs/fee-waterfall.md`; `research_notes/NEAR Intents structural thesis/competitive-structure.md` (cites [Chain Signatures in TEEs](https://www.near.org/blog/chain-signatures-tee)).

---

## Verdict

Chain Signatures (MPC/TEE on `v1.signer`) are **measured infrastructure for Intents cross-chain settlement**. They do **not** show up as a separate NEAR holders-revenue, burn, or staking-claim line in committed metrics. Treat CS as a **necessary condition** for Intents volume — not an additive fee engine — unless a paid signature API or NEAR-denominated signature fee appears.

---

## Q1. What is measured?

### Census (~10.3 h / 343K txs)

| Metric | Value | Definition in pipeline |
|---|---|---|
| `signatures_per_day_k` | **15.7** | Annualized from `v1.signer` method **`respond`** counts (`census_metrics.py`) |
| Window raw | `respond` **6,755**; `sign` **285**; also `submit_participant_info` 166, `respond_verify_foreign_tx` 122 | Same census `methods.v1.signer` |
| `v1.signer` gas / tx share | **2.8%** gas; **2.1%** txs | Operator/compute opex, not a fee product |
| Contract context | Intents **13.2%** txs / **9.4%** gas; deposits/withdrawals ~$80M / ~$75M per day | CS sits *beside* Intents flows, not as a priced line |

**Do not conflate methods.** Headline “~16K signatures/day” is **`respond`**. History-sample “signs” are **`sign`** FunctionCalls. In the same census window, `respond` annualizes ~15.7K/day while `sign` annualizes only ~0.66K/day — different stages of the signing protocol, not interchangeable series.

### History sample (`sample_extras`)

Exploratory (post-freeze; **not** U1–U5). Counts receipts executed on `v1.signer` with method `sign` (Chain Signatures **requests**), scaled to per-day with the same cluster bootstrap as the history sample (`sample_extras_results.json`, five clusters per recent quarter):

| Quarter | Point signs/day | 90% interval |
|---|---|---|
| 2025Q3 | **1,411** | degenerate (1,411–1,411) |
| 2025Q4 | 2,516 | 1,398–3,635 |
| 2026Q1 | 7,974 | 3,973–13,954 |
| 2026Q2 | 25,731 | 23,158–28,590 |
| 2026Q3 | **36,633** | 26,207–47,905 |
| 2026Q4 | **16,400** | 12,886–19,329 |

REPORT’s shorthand: **1.4K → 2.5K → 8.0K → 26K → 37K → 16K**/day (2025Q3–2026Q4). Rise through 2026Q3; 2026Q4 print is lower — intervals still wide; exploratory only.

**Not the same as U4 `signers_per_100`.** That metric is distinct *transaction* signers per 100-block cluster (base-layer activity). `sample_extras.signs` is CS request volume on `v1.signer`. Do not read CS into the failed U4 “more users” test.

### 11-of-17 TEE network (architecture, not a census count)

Repo structural notes (citing NEAR’s TEE blog / SVRN / docs): required threshold **11 of 17** independent operators; key shares in **Intel TDX** with on-chain attestation; named operators include SVRN, Bitwise, Nansen, Greenfield, Everstake, Near One, Luganodes; Trail of Bits audits cited as public; Read MPC needs ≥3 of 5 whitelisted RPCs before threshold signing for foreign-chain deposits.

**Gap:** this repo does **not** independently census operator uptime, key-share liveness, or attestation freshness. The 11-of-17 figure is **documented architecture**, not a measured node metric here. Distinct from Confidential Intents’ **seven** permissioned private-shard validators — do not conflate.

---

## Q2. Fee / burn / staking claim — or only gas?

**Only gas (plus any off-book operator subsidy), on committed evidence.**

| Claim type | Evidence in repo | Status |
|---|---|---|
| Signature fee → revenue wallets | Fee waterfall / Intents fee docs list appFees, 1Click/CIF, solver spread, **1 pip** on `intents.near` — **no CS signature fee layer** | Absent |
| Holders revenue / DefiLlama CS line | Three wallets reconcile to DefiLlama Intents revenue; all inflows from `intents.near` native withdraw | No CS adapter line |
| NEAR burn tied to signatures | Buyback NEAR is **held, not burned**; no signature-burn mechanic in metrics | Absent |
| Staking claim for signing | No “stake NEAR → earn signature fees” series in committed raw/derived | Absent |
| L1 gas | `v1.signer` burns ~**2.8%** of census gas | Present (opex) |

Governance context (not a fee product): forum topic **HSP-007** discusses MPC node infrastructure financing via **protocol emissions** — financing direction is emissions/subsidy, not a measured per-signature NEAR tariff (`data/raw/governance/top_yearly.json`).

**Gap:** no on-chain accounting in this repo of what MPC operators charge off-chain, if anything; no proof that `sign`/`respond` attachable deposits are zero beyond gas. Absence of a wallet line ≠ proof of zero commercial agreements with integrators — it means **no separate token-claimable cash-flow** is attested the way Intents capture is.

---

## Q3. How CS enables Intents without being a separate cash-flow

Intents separates off-chain solver fulfillment from on-chain settlement on NEAR. Cross-chain legs need threshold signatures so NEAR-side accounts can authorize foreign-chain moves without bonded vault TVL scaling 2:1 (peer contrast: THOR/Maya/Chainflip). CS is the **signing rail** that makes “any-to-any” coverage operable under the solver+MPC model; wallets buy coverage and partner fees, not MPC vs TSS.

Cash-flow path that reaches the token is still: **listed/app fees + CIF/1Click takes → (fraction) three revenue wallets → held buybacks**. CS volume rising is consistent with more cross-chain Intents activity using the rail. It does **not** add a second τ in the fee waterfall. Double-counting CS growth as “another fee engine” overstates token claim.

Ingress still often depends on **PoA bridges** while OmniBridge-style paths roll out chain-by-chain — CS is necessary for the signing model, not sufficient for trustless deposit paths on every chain (**Gap:** no audited chain-by-chain residual-risk table in-repo).

---

## Q4. Proprietary cut

**Score CS as a necessary condition for Intents volume, not an additive revenue line.**

- Rising `signs` / census `respond` → evidence that the **cross-chain rail is in use**, co-moving with Intents exploratory activity.
- Token investment scoreboard stays: **token-claimable bp, capture share, attachment, attestation, mix** (`fee-waterfall.md` / `prop_scores.json`).
- CS failure (threshold outage, attestation break, operator collusion) is an **Intents volume / trust kill switch**, not a missed P&L line item.
- Do not add “CS fee optionality” into path-to-50× math until falsifiers fire.

---

## Q5. Falsifiers

Treat the “infrastructure only” read as **falsified** if any of the following show up in committed public series:

1. **Paid signature API** with published NEAR (or stable) tariff per `sign`/`respond`, routing to a named collector.
2. **NEAR-denominated signature fees** landing in DefiLlama holders-revenue wallets or a new adapter line distinct from Intents appFees/CIF.
3. **Mandatory stake-to-sign** with slashable bond earning signature fees (Chainflip/THOR-style claim rewritten onto CS operators).
4. Protocol **burn** mechanically tied to signature count (not merely L1 gas burn).

Until then: CS growth ≠ second cash-flow; CS outage risk = first-order for Intents volume durability.

---

## Proprietary punch

1. Census ~**16K**/day is `respond`; sample ~**1.4K→37K→16K**/day is `sign` — same contract, **different methods**; do not merge into one τ.
2. **11-of-17 TEE** is documented architecture cited in-repo; this census does not re-prove operator set or attestation freshness.
3. Fee waterfall has **no CS layer**; capture still ends at Intents → three wallets; buybacks **held, not burned**.
4. `v1.signer` is ~**2.8%** gas — opex footprint, not holders revenue.
5. CS is a **necessary condition** for Intents cross-chain volume under the solver+MPC model; not an additive revenue line.
6. Rising signs co-move with Intents exploratory use; that supports **rail utilization**, not a second fee engine.
7. Double-counting CS into path/issuance-offset math overstates token claim.
8. CS outage / threshold failure is an **Intents volume kill risk**, scored under operational trust — not under missed P&L.
9. Distinct from Confidential Intents’ **7-validator** private shard; conflating TEE stacks muddies diligence.
10. Falsifiers: paid signature API, NEAR-denominated signature fees, stake-to-sign fee claim, or signature-tied burn in public adapters.
11. **Gap:** off-chain MPC operator commercial terms and per-chain OmniBridge vs PoA residual risk are not attested here.
12. Until falsifiers fire, proprietary scoreboard ignores CS as cash-flow and keeps **attach / capture / attestation / mix**.

Census method asymmetry: `data/derived/cs_method_asymmetry.json`.
