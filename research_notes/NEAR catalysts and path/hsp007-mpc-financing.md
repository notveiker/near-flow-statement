# HSP-007 — MPC financing as opex claim on issuance

*Prop note. As of **November 2026**. Twin: `data/derived/hsp007_mpc.json`. Gaps labeled.*

Sources: `data/raw/governance/top_yearly.json` (topic titles / engagement); `data/derived/governance_catalysts.json`; `REPORT.md`; `research_notes/NEAR catalysts and path/chain-signatures-value-link.md` + `data/derived/chain_signatures_link.json`; `docs/float-sink.md` / `data/derived/float_sink.json`; `docs/catalysts-and-path.md`; `docs/structural-thesis.md`; `research_notes/NEAR catalysts and path/buyback-quality-float.md`.

---

## Verdict

**HSP-007** frames MPC / Chain Signatures node infrastructure as something to finance from **protocol emissions**. That is a **competing claim on the same issuance pool** that Intents fee capture (and HSP-029’s cut) are trying to shrink relative to holders. Score it as **opex on mint**, not as free reliability for the Intents thesis.

---

## Q1. What does HSP-007 propose?

**From committed repo evidence (title + context only):**

| Topic | id | Created | Likes / views / posts |
|---|---|---|---|
| *HSP-007: Establish a Sustainable MPC Node Infrastructure Financing Program Funded via Protocol Emissions* | 41984 | 2026-01-23 | 212 / 2392 / 70 |
| *HSP-007 Execution: MPC Node Infrastructure Financing Program* | 42147 | 2026-04-09 | 23 / 1297 / 25 |

Title-level claim: a **sustainable financing program** for **MPC node infrastructure**, funded via **protocol emissions** (not via a measured per-signature NEAR tariff). An **execution** thread exists months later — engagement lower than the establishing thread.

Chain Signatures context in-repo: CS is the **11-of-17** TEE threshold rail for Intents cross-chain legs; census ~**16K** `respond`/day; sample `sign` series rose then printed ~**16K**/day in 2026Q4 exploratory draw. Fee waterfall has **no CS signature-fee layer**; token touch in committed metrics is **L1 gas** on `v1.signer` (~**2.8%** gas share).

**Gap:** full HSP-007 proposal body (budget size, % of emissions, recipient set, duration, clawbacks, relation to validator rewards) is **not** in this repo — only forum titles/engagement in `top_yearly.json` / `topics.json`. Do not invent magnitudes.

---

## Q2. Does financing MPC via emissions compete with HSP-029 / buyback narrative?

**Yes — same pool, opposite direction of claim.**

| Lever | What it does to issuance ↔ fees | Dated / measured? |
|---|---|---|
| **HSP-029** | Ramps annual issuance cap **2.5% → 1.6%** over 24 months; timelock **2026-11-16**; activation ~one quarter later | In frozen rating path; flat capture lifts held offset **15.81% → ~24%** |
| **Buyback / float-sink** | Captured revenue (~**$24.2M**/yr) held in wallet; DIC ~**25** days; **held not burned** | Measured; recirculation risk remains |
| **HSP-007** | Diverts / earmarks **emissions** to MPC node opex | Title-level only; **Gap** on NEAR/year claimed |

HSP-029 improves the **coverage ratio** of a given fee dollar against mint. HSP-007, if funded from emissions, is an **additional (or redirected) mint claim** that keeps Intents-critical infra running. Narrative tension: market can read “issuance cut + fee offset” while governance simultaneously **pays CS reliability out of mint**. That does not cancel HSP-029 arithmetically unless the MPC slice is large enough to offset the cut — **Gap** on size — but it **does** mean “net mint available after policy” is not the headline 1.6% alone until MPC financing is netted.

Buyback quality note already flags governance **opex / recirculation** of buyback stock as a falsifier. HSP-007 is the **emissions-side** twin: opex financed upstream of (or beside) fee→wallet, not only from wallet spend.

---

## Q3. Is CS/MPC opex a hidden cost that fee capture must cover?

**Structurally yes; dollar amount Gap.**

Committed read from CS value-link note:

- No paid signature API / DefiLlama CS line / signature-tied burn / stake-to-sign fee claim in committed metrics.
- CS is a **necessary condition** for Intents cross-chain volume; outage is an **Intents reliability kill switch**, not a missed P&L line.
- Operator commercial terms **off-chain** are unattested (**Gap**).

So the cost stack for “Intents works cross-chain” is at least:

1. **L1 gas** on `v1.signer` (visible, small vs net mint of ~**88k NEAR/day**).
2. **MPC operator economics** — if not fully covered by off-book integrator payments, HSP-007 says the residual is an **emissions claim**.
3. **Fee capture** (~**15.8%** held offset of issuance today; band **4.5–15.8%** until escrow attestation) trying to offset the **same** mint.

Until a signature tariff routes to holders, fee capture does **not** pay MPC opex directly; either emissions (HSP-007), treasury/discretionary spend, or opaque off-chain deals do. Holders-revenue math that ignores (2) overstates how much of the Intents stack is “self-funding” from attachable fees.

---

## Q4. Proprietary cut

**Score MPC financing as an opex claim on the same issuance pool Intents fees are trying to offset.**

- Do **not** treat CS reliability as free infrastructure when forum policy points at **emissions-funded** MPC nodes.
- Stack HSP-029 (cut mint) and HSP-007 (claim mint for MPC) as **gross vs earmarked** issuance — net free float after policy is unknown without the proposal body (**Gap**).
- Keep CS on the **reliability / kill-switch** scoreboard; keep HSP-007 on the **issuance-offset** scoreboard as a **negative or competing claim**, not a catalyst for capture %.
- Path-to-offset arithmetic (15.8% → ~24% post-HSP flat capture; ~32% at 60% attach + 1.6% cap) is **gross** until MPC emissions are netted — do not present those ratios as “all-in after infra.”

---

## Proprietary punch

1. HSP-007 title = **MPC node financing from protocol emissions** — subsidy direction, not a CS fee product.
2. Full budget / % of mint / recipients = **Gap** (repo has titles + engagement only; execution thread 42147 exists).
3. CS has **no** holders-revenue line; fee waterfall ends at Intents → three wallets; buybacks **held**.
4. HSP-029 **shrinks** mint; HSP-007 **claims** mint for the rail Intents needs — same pool.
5. Fee offset % is **gross** until MPC emissions are netted; today’s ~15.8% / post-HSP ~24% are not all-in after infra.
6. Score HSP-007 as **opex on issuance**, not a free reliability upgrade.
7. CS outage remains Intents **volume kill risk**; emissions financing is how governance may **pay** to avoid that — at holders’ dilution cost.
8. Off-chain MPC commercial terms unattested — emissions may be residual or primary (**Gap**).
9. Buyback recirculation *and* emissions MPC opex are twin ways “fees cover issuance” softens.
10. Falsifier for “hidden opex zero”: published NEAR/year MPC emissions schedule that is material vs ~88k NEAR/day net mint — or a paid signature tariff that replaces subsidy.
