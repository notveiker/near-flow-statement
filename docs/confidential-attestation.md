# Confidential rails — margin up, proof down

*Exploratory / post-freeze. Detail in [`research_notes/NEAR catalysts and path/confidential-trust-attestation.md`](../research_notes/NEAR%20catalysts%20and%20path/confidential-trust-attestation.md). Feeds no pre-registered test. As of 2026-11-11.*

Confidential Intents is a **permissioned private-shard venue** (seven validators, no public RPC, TEE bridge, ingress sanctions screen, SHIELD) with public destination settlement. NEAR’s own framing is trust-minimized, not trustless. Architecture is documented; **validator roster independence, TEE attestation freshness, and fee→wallet causality on the private vertical are not**.

## The investment split

Partners have **zero contractual claim** on confidential swaps (no AppFee; Confidential Infrastructure Fee set and retained by Intents Technology “for its own account”). That can raise NEAR’s *economic* take while destroying *public* proof of capture. Forwarding infrastructure fees to ecosystem wallets is a **permission in Schedule 1, not an obligation**.

In the 30 days to 2026-11-04, about **59%** of buyback-wallet NEAR arrived as escrow unshields. Aggregate wallets still reconcile to **100.9%** of DefiLlama Intents revenue — the money arrived; the **stream** is unattested. Measured issuance offset is therefore a **4.5–15.8%** band (attestation gap ~**11.3** points), not a single DefiLlama print. Escrow’s share of buyback NEAR climbed through the confidential rollout (mid-teens in July → high-50s by October).

## Score before “privacy moat”

| Metric | Approx | Read |
|---|---|---|
| Escrow-dependence of buyback | **~59%** | Rising without attestation → underwrite the floor |
| Attestation gap | **~11.3 pp** of issuance | Top ladder minus public collectors |
| Confidential share of wallet capture | **~71%** | Escrow pts / all-wallet pts |
| CIF forwarding | **unattested** | Kill switch if sweeps stop |

Confidential TVL (~$160M at Q3-end) and near.com’s privacy default are product signals. They are margin-positive for the token **only if** CIF continues to be swept. Peers need not copy Nightshade to pressure the wedge — dark-enough UX inside the same wallet embeds, or meta-routers that treat NEAR settlement as interchangeable, is enough.

*Not investment advice.*

Derived CIF sensitivity sketch: `data/derived/cif_sensitivity.json` (1 bp on TVL×~17×/30d proxy).

Escrow share climb Jul→Nov (~17.5%→~58.5%): `data/derived/escrow_share_climb.json`.

Buyback funding rails ($): `data/derived/bb_funding_rails.json` — collectors ~41% / escrow ~59%.

## Unexplained buyback funding

Beyond the 4.5–15.8% attestation band on escrow, ~**68%** of revwallet buyback dollars ($0.94M / $1.39M) lack a mapped fee-event in the evidence sample. Hold until H1b remains binding on funding provenance, not only escrow share.
