# Relayer / solver operational concentration — NEAR Intents

*Prop note. As of November 2026. Census window ~**10.3 hours** / **343K** txs on our node (`census_usage.json`, `census_metrics.json`). Twin: `data/derived/relayer_risk.json`. Gaps labeled.*

Sources: `REPORT.md` §7 / risks / catalysts census bullets; `data/derived/census_{usage,metrics}.json`; `docs/structural-thesis.md` (solver-as-principal; vault-peer contrast); `docs/fee-waterfall.md` / `fee-waterfall-capture.md` (excess ~8.5 bp; gas/relayer layer).

---

## Census facts (measured)

| Fact | Value | Read |
|---|---|---|
| Relayer accounts on `execute_intents` | **25** | Thin operator set |
| Top-1 share of `execute_intents` | **83%** (0.825 raw) | Single-account choke |
| Top-5 share | **99.9%** (0.9986 raw) | Effective oligopoly |
| Chain txs relayed (gasless / delegate) | **43%** | End users skip NEAR gas |
| Intents share of txs / gas | **13.2% / 9.4%** | Largest compute peer with HOT |
| Solver model | Principal | Keeps bid-ask; not protocol counterparty |
| Realized excess over listed | **~8.5 bp** | Solver/gas/pip residual in user all-in |

`execute_intents` calls in window: **45,009** — almost all `intents.near` txs (**45,236**). Settlement is relayer-submitted, not user-submitted.

---

## Q1. Liveness risk, rent-extraction risk, or both?

**Both.** Concentration creates a liveness choke *and* a margin choke; they are not substitutes.

**Liveness.** Top-1 carries **~83%** of settlement submissions. If that account stalls and residual capacity does not fail over instantly, Intents `execute_intents` throughput collapses toward the residual **~17%**. Top-5 = **99.9%** means the long tail of 20 accounts is decorative for capacity. This is *operational* liveness, not L1 consensus liveness (validator HHI **0.022**, Nakamoto-9 — different layer).

**Rent extraction.** Solvers trade as principal and keep bid-ask; Explorer shows users pay **~8.5 bp** above listed on $1K–$50K swaps. A dominant relayer that also sits on the hot path can delay, reorder, or preferentially land competing solvers’ fills. Relayer concentration is therefore an *execution-governance* risk on top of distribution’s claim on listed bp. Token-claimable take stays ~**5 bp**; the user pays listed + excess. Concentration does not raise NEAR’s claim — it raises the chance that non-token agents capture or gate the flow that feeds the fee engine.

**Inference.** Treat “25 relayers” as a headline, not a diversification claim. Effective N for settlement is closer to **1–5**.

---

## Q2. Gasless / relayed share vs NEAR token demand for gas

**Second-order for the Intents thesis — and it cuts against a retail-gas demand story.**

- **43%** of *chain* txs are relayed: senders never needed NEAR for gas. Gas demand concentrates in operator working balances (relayers, games, bridges), not in Intents end-users.
- Intents is **13%** of txs and **9%** of gas. Relayers pay that gas as opex. Scaling Intents volume scales *operator* NEAR inventory for fees, not broad user balances.
- The investment scoreboard for Intents is **token-claimable bp / capture / attachment / attestation** (`fee-waterfall.md`), not L1 fee burn from user wallets. Intents revenue already runs **~11×** base-layer fees; the engine is distribution + buyback wallets, not gas scarcity.
- **Implication:** a thesis that “Intents adoption → NEAR demand via gas” is structurally weak while gasless share stays high. Gasless UX is product-positive and token-demand-dilutive on the L1-fee channel.

**Gap:** census does not split how much of the **8.5 bp** excess is destination gas vs solver margin vs pip; nor how often relayers buy NEAR spot vs recycle inventory.

---

## Q3. Proprietary metrics

### Relayer HHI (Herfindahl on `execute_intents` signer shares)

Full 25-share vector is **not** exported in `census_usage.json` (only top1 / top5 / distinct). Bound HHI from those aggregates:

| Bound | Assumption | HHI |
|---|---|---|
| Lower | Top-1 fixed; next 4 of top-5 equal; bottom 20 equal | **~0.688** |
| Upper | Top-1 fixed; #2 takes rest of top-5; bottom negligible | **~0.711** |

Antitrust “highly concentrated” is often **>0.25**. Validator-set HHI on the same node read is **0.022**. Relayer settlement is ~**30×** more concentrated than block production.

**Track:** `relayer_HHI`, `relayer_top1_pct`, `relayer_effective_N = 1/HHI` (~**1.4–1.5**).

### Single-relayer downtime impact (SRDI)

Define **SRDI** = expected share of Intents settlement calls lost if top-1 is offline with no failover:

\[
\mathrm{SRDI}_{top1} \approx top1\_share \approx 0.83
\]

Residual capacity proxy: **1 − top1 ≈ 17%** of current `execute_intents` rate. If top-5 jointly fail: residual ≈ **0.1%**.

**Throughput mapping (window arithmetic, not an incident):** Intents ≈ **13%** of chain txs; ~all of that method mass is `execute_intents`. A pure top-1 outage without failover ≈ **−83%** Intents settlement throughput, ≈ **−11 pp** of chain tx count if nothing else substitutes — *upper-bound impact*, assumes zero hot-spare.

**Track:** measured failover minutes; correlation of top-1 downtime windows with 1Click volume / captured NEAR; identity overlap relayer↔solver.

---

## Q4. What falsifies “operational risk is contained”?

Any durable claim that risk is contained needs **evidence of spare capacity and non-extractive operation**. The following would falsify containment (any one is enough to reopen the file):

1. **Persistence:** top-1 share stays **≥80%** (or HHI **≥0.65**) across multi-day / multi-week census windows — not a 10-hour artifact.
2. **No failover:** a documented top-1 outage with Intents settlement drop **≳50%** lasting **>15–30 minutes** without residual accounts absorbing flow.
3. **Margin spike under concentration:** realized excess over listed rises **materially above ~8.5 bp** in windows where top-1 share is elevated (rent channel opening).
4. **Identity collapse:** dominant relayer(s) are the same economic agents as dominant solvers / inventory desks — concentration compounds principal + submission power.
5. **Fee-engine hit:** captured bp or attachment falls when settlement ops glitch (volume narrative breaks *and* wallet inflows break together).
6. **Gasless thesis mismatch:** narrative continues to sell retail NEAR gas demand while delegate share stays **~40%+** and Intents remains relayer-submitted.

**What would support containment (not assumed):** top-1 **<40%**, HHI **<0.20**, measured hot-spare failover **<2 minutes**, published operator diversity with independent keys/infra, excess bp stable or falling as share disperses.

---

## Q5. Vs vault-peer bonded security — different failure mode

| | Intents (solver + relayer) | THOR / Maya / Chainflip (vault) |
|---|---|---|
| Asset underwriting | Per-trade **solver inventory** + bridges / MPC-TEE signing | Continuous **bond-to-TVL** threshold vaults |
| Concentration surface | **Off-chain operators** submitting settlement; thin relayer set | **Bonded node set**; economic security scales with bond |
| Primary failure | **Liveness / preferential execution / inventory refusal** | **Economic insolvency / slash / vault halt** under bond stress |
| User cost channel | Listed distribution bp + **~8.5 bp** excess (solver principal) | Network + slip / LP fee; affiliates / REVSHARE on the side |
| Token link | Discretionary wallets / buyback; **1 pip** on-chain | Rule-based splits (e.g. Maya holders cut; Chainflip burn path) |

Structural thesis already notes share came from **embeds and coverage**, not vault bake-offs. The census adds the operational corollary: Intents avoided bond-scaling constraints *by* pushing security and liveness into solver inventory and a concentrated relayer path. That is a **different risk**, not a smaller one. Vault peers fail when economic underwriting breaks; Intents fails when a handful of accounts stop submitting or extract on the hot path — while L1 validators keep producing blocks.

Do not score Intents safer because validator HHI is low. Score **relayer HHI / SRDI** for settlement risk and **bond-to-TVL** for vault peers separately.

---

## Fee-engine read

- Capture arithmetic (`τ ≈ 5 bp`, `C ≈ 32.5%`, AITR ≈ **9.5 bp**) assumes continuous settlement. Relayer concentration is a **silent dependency** under that numerator.
- Distribution already owns listed bp; solvers own excess; relayers own the submit gate. NEAR’s claim sits after all three.
- Gasless share weakens L1-fee demand as a second-order Intents → NEAR channel; do not lean on it.

---

## Gaps

- Full relayer share vector (accounts + counts) not in derived census export → HHI is **bounded**, not exact.
- No labeled outage / failover time series in repo.
- Relayer ↔ solver entity graph **Gap**.
- Split of **8.5 bp** excess into gas vs margin **Gap**.
- Chain-wide “43% relayed” vs Intents-only relayer set are related but not identical populations; catalysts bullet wording sometimes conflates them — metrics markers use `execute_intents` for the 83% figure.
- 10.3-hour window: levels are point-in-time; persistence untested.

---

## Proprietary punch

1. **Settlement is a single-account product:** top relayer **83%** of `execute_intents`; top-5 **99.9%**; N=25 is cosmetic.
2. **HHI ~0.69–0.71** vs validator HHI **0.022** — Intents ops are orders of magnitude more concentrated than consensus.
3. **SRDI ≈ 0.83:** top-1 downtime without failover ≈ **−83%** Intents settlement throughput.
4. Risk is **both** liveness and rent: principal solvers + submit monopoly sit on the same hot path as the **~8.5 bp** excess.
5. **43% gasless** means Intents growth does **not** scale retail NEAR gas demand; operators hold the gas float.
6. Fee-engine numerator (`τ` / attachment) **silently assumes** that concentrated submit path stays up and non-extractive.
7. Vault peers fail on **bond economics**; Intents fails on **operator continuity / preferential execution** — non-substitutable failure modes.
8. “Operational risk contained” is **falsified** by persistent top-1 ≥80%, slow failover, excess-bp spike with concentration, or relayer=solver identity collapse.
9. Score **relayer HHI + SRDI + excess bp** beside capture metrics; volume share without them overstates durability of the fee engine.
10. Effective operator count **1/HHI ≈ 1.4** — underwrite Intents settlement as a **near-monopoly relay**, not a decentralized solver mesh.
