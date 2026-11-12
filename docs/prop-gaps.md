# What we still cannot measure (and why it matters)

*Exploratory honesty checklist. As of 2026-11-12.*

| Gap | Why it blocks the multiple | What closes it |
|---|---|---|
| Per-stream escrow attestation | Capture is a **4.5–15.8%** band | NEAR publishes fee-stream → wallet map |
| Confidential Infrastructure Fee rate card | Cannot size partner-proof take | Public bp by route / asset |
| Commercial Agreement text (SwapKit/Ledger/…) | Cannot forecast renegotiation; leakage pool ~$50M/yr (`leakage_pool_size.json`) | Redacted schedules or on-chain defaults |
| Agent-originated Intents volume | AI narrative unmeasured; even 5% share ≈ ~$0.33M/yr at τ (`agent_volume_bounds.json`) | Named series in Explorer / Llama |
| Full peer holders-revenue like-for-like | Multiples not comparable | Aligned DefiLlama methodology window |
| HSP-007 emissions draw (NEAR/year) | Issuance opex vs fee coverage; 10% claim ≈ ~$12M/yr sketch (`hsp007_claim_bounds.json`) | Proposal body + execution reports |
| Solver P&L inside 8.5 bp excess | Rent vs gas unknown | Fee-evidence sample expansion |
| Selective-disclosure auditor tooling GA | Institutional diligence blocked | Product ship + docs |
| Longer census for relayer HHI stability | Ops risk may be window artifact | Multi-day census |

Until the top gaps close, the honest investment object is a **range with policy and partner risk**, not a closed fee→scarcity loop (`data/derived/investment_object.json`). The punch card still scores: attach, mix, attestation, HSP-029, then volume.

SwapKit↔escrow link unknown — exit ceilings span 2–74% (`data/derived/sk_exit_ceilings.json`).

Telegram (`intents.tg`) is a live referral surface in census (~20% of tagged) but fee attribution to buyback is not mapped (`census_tg_surface.json`).

### Closed-enough this sweep

- **Conversion measured**: appfees→buybacks at 9.2%; unexplained BB share ~68% (`appfees_to_buyback_conversion`, `buybacks_unexplained_share`).
- **Trust path sized**: SK→direct-20bp ~$1.7M/yr (`trust_path_bb_vs_tax`).
- **Attach path evidenced** inside sample 23.6→43 / 2.89→4.98 bp (`attach_path_evidenced`).

### Also closed-enough this sweep
- Channel BB density map + LI.FI/Rango dials
- H1b coverage quantified (~20–25%)
- near.com stated vs wallet-implied gap
- Peerset share softening (62→56→39 net)
- L1 actives −77% YoY vs Intents fee dominance
