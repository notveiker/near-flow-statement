# Confidential Intents as NEAR's institutional and size wedge

*As of Nov 2026. Prop research notes for report synthesis. Marketing claims are labelled separately from evidenced behavior.*

## How does the private-shard model differ from ZK privacy systems and from CEX dark liquidity, and what tradeoffs does that create (trust, compliance, UX)?

### Takeaway
Confidential Intents hides execution (size, pair, route, counterparty link) inside a permissioned NEAR private shard with a TEE bridge and no client ZK proofs—closer to venue-style dark execution than to Zcash-style cryptographic anonymity, with destination settlement still public. The UX and compliance posture are strong relative to ZK mixers; the trust surface is a small validator set plus TEE/bridge operators, not pure cryptography.

### Cited Findings
- Confidential Intents is a confidentiality layer on NEAR Intents that executes deposits, withdrawals, swaps, and P2P transfers without exposing position data on the public chain; near.com ships this as “Confidential Mode.” — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works)
- Architecture: a dedicated NEAR private shard with restricted visibility, no public RPC/API/explorer, operated by independent permissioned validators using PBFT (~200ms finality), connected to mainnet via a bridge; tokens on the private shard are burned after withdrawal. — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works)
- NEAR’s protocol page states the private shard is operated by **seven permissioned validators** and connected to mainnet via a **TEE-based bridge**; it is the foundation for Confidential Intents. — [NEAR Blockchain](https://www.near.org/blockchain)
- Market-maker docs describe a two-chain model: public NEAR (`intents.near`) and FAR (a private NEAR fork / permissioned instance with no public networking); shield mints IMT tokens against a Treasury lock; unshield burns IMT and releases treasury backing; swaps settle on FAR via `token_diff`, invisible to public indexers. The treasury account is `PRIVATE_TREASURY_ACCOUNT_ID`, a shared production constant. — [Confidential Intents (MM docs)](https://docs.near-intents.org/integration/market-makers/confidential-intents)
- **Vs ZK:** NEAR’s own architecture note: ZK privacy systems require client-side proof generation per tx (overhead, wallet complexity, limited ops). Confidential Intents uses private-shard execution instead—encrypted onchain data and restricted validator access. NEAR explicitly calls the tradeoff “a trust-minimized model rather than a fully trustless one” for broader functionality and standard UX (no client proofs, state sync, or extra wallet setup). — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works); restated in [GA announcement](https://www.near.org/blog/announcing-general-availability-of-confidential-intents)
- **Vs mixing / pooled anonymity:** Individual encryption of each user’s history, not pooled obfuscation; confidentiality does not depend on anonymity-set size. Mixing accepts any source and pools funds; Confidential Intents screens at ingress then encrypts individually. — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works); [GA announcement](https://www.near.org/blog/announcing-general-availability-of-confidential-intents)
- **Vs CEX / dark-pool analogy (NEAR framing):** Blog compares the product to equity dark pools: keep pre-trade order flow confidential to avoid signaling, while arguing users retain asset control and settlement on “verifiable infrastructure.” Explicit claim that transparent order flow pushed institutional size to CEXes, and Confidential Intents aims to bring that property to cross-chain DeFi. — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works)
- **Scope of privacy (integrator docs):** Origin wallet, routing path, and source↔destination link are hidden; destination tx, asset, amount, and recipient remain public and verifiable. “Not private DeFi” that obscures destination settlement. — [Aurora Intents Confidential Intents](https://docs.intents.aurora.dev/confidential-intents)
- **1Click UX:** Foreign-to-foreign confidential swaps are a quote parameter (`confidentiality: basic|advanced`); quote→deposit→swap flow matches standard swaps. Embedded balances use `CONFIDENTIAL_INTENTS` types + signed intents (near.com-style). Public Intents: deposits/withdrawals can be matched; Confidential: they cannot. — [Confidential Swaps docs](https://docs.near-intents.org/integration/distribution-channels/1click-api/quickstart/confidential-swaps); [GA announcement](https://www.near.org/blog/announcing-general-availability-of-confidential-intents)
- **Compliance design:** Ingress screening against sanctions/flagged addresses before funds enter the private shard; once inside, NEAR says transactions are not continuously monitored. Selective disclosure of an account-level view key is on the **roadmap** (user-initiated, time-scoped); lawful disclosure framed like Signal/Zcash view-key posture. Risk & Compliance docs list AML sources (internal AML portal, Binance AML, AMLBot/PureFi, TRM Labs for non-dry quotes) with coverage varying by flow. — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works); [Risk & Compliance](https://docs.near-intents.org/security-compliance/risk-and-compliance)
- SHIELD is an application-layer incident/policy service (allow/delay, scoped pauses); Nansen reports SHIELD rejected >$50M in attempted transfers linked to the Bitget hack (rejected attempts, not recovered funds); protocol remains permissionless. — [Proactive Intents Security](https://docs.near-intents.org/security-compliance/proactive-intents-security); [Nansen NEAR Q3 2026](https://nansen.ai/post/near-q3-2026-report)
- Independent integrator note (LeoDex, July 2026): trust assumptions include permissioned validators whose composition is “not fully public,” TEE/hardware trust, attestation details not published, and no independent security audit seen as of that writing; destination settlement can still be public. — [LeoDex editorial](https://leodex.io/editorial/near-confidential-intents-july-2026)

### Inferences
- Structurally this is **restricted-visibility execution with public edge settlement**, not end-to-end cryptographic anonymity. Observers lose the deposit↔withdrawal link and internal swap detail; they still see money leaving origin chains and arriving on destination chains.
- Relative to ZK privacy stacks, Confidential Intents optimizes for **integrator adoption and size UX** (one API flag, no client proving) at the cost of trusting a **small permissioned set + TEE bridge + PoA mint/burn path**. That is a deliberate institutional/compliance trade: screen-then-execute, selective disclosure planned, vs opaque mixers that regulators target.
- Relative to CEX dark liquidity, users keep self-custody at the product layer (NEAR’s claim), but the **operational trust** (who can see private-shard state, who operates the bridge, who can pause via SHIELD) is closer to a **permissioned venue** than to mainnet NEAR’s open validator set. Size users who already trust CEX matching engines may accept that; trust-minimizing DeFi users may not.
- Privacy is **asymmetric by design**: good for hiding strategy and treasury routing; incomplete for users who need the *destination* or payout side fully obscured.

### Gaps
- No primary public roster of the seven private-shard validators, their independence criteria, or slashing/fault history as of this research pass.
- No published independent audit of FAR/private shard, TEE bridge attestations, or PoA bridge request-driven mint/burn (LeoDex noted absence as of July 2026; later audit status not confirmed here).
- Quantitative comparison of fill quality / MEV savings vs public Intents for large tickets is asserted by NEAR, not evidenced with independent trade-cost studies.

## What evidence exists that size/institutions prefer confidential mode (ZEC settlement, near.com confidential share, TVL claims)?

### Takeaway
Hard evidence shows **demand for privacy-linked flow and for confidential balances when the product defaults to them**—ZEC settlement, near.com confidential share, and Confidential TVL growth—not named institutional desks or measured size-quartile preference. “Institutions prefer confidential mode” remains largely a marketing frame supported by proxies.

### Cited Findings
**Evidenced / sourced metrics**
- GA blog (7 Jul 2026): “Over **$1.5B** in ZEC has settled across NEAR Intents”; within weeks of Confidential Mode, “over **40%**” / “roughly **42%**” of near.com volume used Confidential Mode; “Confidential balances currently hold over **$30 million**.” — [GA announcement](https://www.near.org/blog/announcing-general-availability-of-confidential-intents)
- Nansen Q3 2026 (20 Oct 2026): Confidential Intents GA 7 Jul 2026 “after more than **$2.6B** in ZEC settled across NEAR Intents”; Confidential Intents TVL “approximately **$160 million** at quarter-end,” “up roughly **463% QoQ**.” — [Nansen NEAR Q3 2026](https://nansen.ai/post/near-q3-2026-report); also captured in repo third-party facts — [/tmp/nfs/data/raw/web/third_party_facts.json](file:///tmp/nfs/data/raw/web/third_party_facts.json)
- Nansen: on **1 Sep 2026**, near.com made confidentiality the **default** across holdings, trades, payments, and yield; near.com processed ~**$2.57B** in Q3 (~**one quarter** of total Intents volume ~**$10.4B**). — [Nansen NEAR Q3 2026](https://nansen.ai/post/near-q3-2026-report)
- Repo 1Click analysis (30d to 2026-11-04): volume is whale-driven—swaps ≥$10K are **3.4%** of swaps but **77.1%** of volume; median swap ~$52; ZEC is **10.9%** of volume legs. Does not break out confidential vs public. — [/tmp/nfs/docs/intents-fee-flows.md](file:///tmp/nfs/docs/intents-fee-flows.md)
- DefiLlama Intents volume step-up around **2026-09-01** coincides with near.com confidentiality-default; 1Click’s share of Llama volume fell from **86.2%** the week before to **60.8%** the week after with no matching 1Click volume change—“consistent with DefiLlama counting more of Intents’ volume (for example confidential swaps) from that date.” Inference in repo, not a DefiLlama admission. — [/tmp/nfs/docs/intents-fee-flows.md](file:///tmp/nfs/docs/intents-fee-flows.md)
- Product surface for orgs: NEAR Business “Confidential Treasuries” are multisig contracts on the private shard; swaps/amounts/rates visible only to team members. — [Confidential Treasuries](https://docs.business.near.com/confidential-treasuries)
- Nansen lists integrations that extend confidential use cases (e.g. Splits for private payroll/contractors/treasury; Infinex, LeoDex, wallets). These are **integration announcements**, not volume attribution. — [Nansen NEAR Q3 2026](https://nansen.ai/post/near-q3-2026-report)

**Marketing / aspirational claims (not independent usage proof)**
- GA and product pages pitch trading desks, treasuries, enterprises, payroll, and AI agents as target users; cite a16z 2026 outlook that “Privacy will be the most important moat in crypto this year.” — [GA announcement](https://www.near.org/blog/announcing-general-availability-of-confidential-intents); [intents.near.org/confidential](https://intents.near.org/confidential)
- Defuse Labs / Intents GM manifesto (Sep 2026): cites “$2+ billion in Zcash… over NEAR Intents,” “$50+ million of Near Intents TVL… confidential,” near.com confidential-by-default; frames Confidential Intents as shared privacy infrastructure for institutional capital. TVL figure here is lower/earlier than Nansen’s Q3-end $160M. — [A manifesto on privacy](https://roundtable100.com/asset/near-protocol/a-manifesto-on-privacy)

### Inferences
- **ZEC settlement** proves Intents is a preferred venue for a privacy *asset*, and that privacy-seeking flow is large; it does **not** by itself prove that Confidential Mode (any-asset private shard) is what those users wanted, nor that the users are institutions.
- **near.com 40–42% confidential share within weeks** is the strongest behavioral evidence that, when UX friction is near-zero, users choose confidentiality. After 1 Sep 2026 default, share metrics become less informative (default ≠ revealed preference).
- **TVL $30M (Jul) → ~$160M (Q3-end)** is real product adoption of confidential balances, but TVL is inventory, not institutional AUM or desk volume. Relative to Q3 Intents volume (~$10.4B), confidential TVL is a thin float.
- Size preference is **plausible** (public Intents volume already whale-skewed; dark-execution thesis fits large tickets) but **not directly measured** in public confidential-vs-public size distributions as of Nov 2026.
- Named “institution” evidence is thin: product docs and payroll/treasury integrations, not disclosed Tier-1 trading-desk or fund flow.

### Gaps
- No public breakdown of confidential vs public volume by ticket size, counterparty type, or channel (1Click explorer vs near.com vs direct solvers).
- ZEC cumulative figures differ by source/date ($1.5B at GA vs $2.6B in Nansen Q3); methodology (gross, double-counted legs, time cut) not fully specified in either primary.
- No independent attestation that “institutions” (regulated funds, banks, market makers beyond Intents solvers) are a material share of confidential TVL or flow.
- Confidential TVL methodology (which assets, valuation, double-counting of IMT vs treasury) is Nansen-reported; raw on-chain public verification of private-shard balances is definitionally limited.

## Does confidentiality strengthen or weaken the public token-capture story (escrow unattested flows, opacity of fee streams)?

### Takeaway
Confidentiality **strengthens the product/volume narrative** (default privacy, sticky balances, possible fee retention on confidential rails) but **weakens the public attestation of token capture**: a majority of recent buyback-wallet NEAR arrives via escrow unshields whose underlying fee stream cannot be seen on chain.

### Cited Findings
- Over 30d to 2026-11-04, NEAR revenue wallets received **418.8K NEAR** (~$2.01M), **100.9%** of DefiLlama Intents revenue—so aggregate capture reconciles. — [/tmp/nfs/docs/intents-fee-flows.md](file:///tmp/nfs/docs/intents-fee-flows.md); [/tmp/nfs/REPORT.md](file:///tmp/nfs/REPORT.md)
- Value-capture ladder (exploratory): of issuance offset by revenue wallets (**15.81%**), only **4.53** points trace to public fee collectors; **11.25** points arrive as Confidential Intents escrow releases—fee stream unattested. Measured capture is therefore a **range 4.5–15.8% of issuance** pending per-stream attestation. — [/tmp/nfs/THESIS.md](file:///tmp/nfs/THESIS.md); [/tmp/nfs/REPORT.md](file:///tmp/nfs/REPORT.md)
- Escrow identity: account `51e8f94d…7cbe` is documented `PRIVATE_TREASURY_ACCOUNT_ID`. All **909** sampled/window deliveries were funded for the exact amount (to yoctoNEAR)—privacy feature working as designed. — [MM docs](https://docs.near-intents.org/integration/market-makers/confidential-intents); [/tmp/nfs/docs/partner-concentration.md](file:///tmp/nfs/docs/partner-concentration.md)
- Escrow unshields: **~$823.7K** of buyback-wallet inflow in the window (**~59%** of that wallet’s NEAR); same path feeds most of `fefundsadmin`. Two documented readings fit and cannot be distinguished on chain: (1) near.com confidential-mode fees (private ledger fee account); (2) **Confidential Infrastructure Fee**—1Click terms Schedule 1 §6.2/§6.4: Intents Technology “sets, charges, and retains” the fee on confidential swaps, no AppFee/share to integrator. — [/tmp/nfs/docs/partner-concentration.md](file:///tmp/nfs/docs/partner-concentration.md); [/tmp/nfs/docs/intents-fee-flows.md](file:///tmp/nfs/docs/intents-fee-flows.md)
- Escrow share of buyback NEAR rose: Jul (from 07-07) **17.5%**, Aug **28.6%**, Sep **53.0%**, Oct **57.4%**—opacity increasing as confidential product grows. — [/tmp/nfs/THESIS.md](file:///tmp/nfs/THESIS.md)
- Partners still keep more fee value than NEAR on the public 1Click half (≥**1.81×** NEAR captured revenue under tight ceiling); confidential rails may raise NEAR’s *economic* take (infrastructure fee retained) while lowering *observability*. — [/tmp/nfs/docs/partner-concentration.md](file:///tmp/nfs/docs/partner-concentration.md)
- Authenticated Partner JWT does **not** allow reading a user’s confidential data; private balances/history need a User-Session token—so third-party analytics cannot reconstruct confidential fee attribution from public APIs. — [API authentication docs](https://docs.near-intents.org/integration/distribution-channels/1click-api/authentication)
- Nansen still reports rising lifetime fee capture (**16.4%** lifetime; **28.4%** trailing 30d as of Oct 6 update) and >$8M captured for buybacks cumulative—third-party narrative of capture continues even as on-chain stream attribution thins. — [Nansen NEAR Q3 2026](https://nansen.ai/post/near-q3-2026-report)

### Inferences
- For investors who need **auditable fee→buyback causality**, confidentiality is a **net negative**: more of the “Intents earns NEAR” story becomes “NEAR arrived from the private treasury,” which is consistent with fees but not proof of which fees.
- For NEAR’s **commercial** interest, confidentiality can **strengthen** capture: retained Confidential Infrastructure Fee, near.com 100%-to-revenue-wallet posture, and sticky confidential balances that keep flow on NEAR-controlled rails rather than partner-split public AppFees.
- The token story therefore splits: **economic capture may improve with confidential mix; epistemic quality of the public capture proof deteriorates.** Prop judgment should treat escrow-funded buybacks as *received* but *unattested as to source*, not as fraud—privacy by design.
- Volume growth under confidentiality defaults can inflate third-party volume/TVL while making peer fee-bp comparisons harder (hidden spreads and private fee takes).

### Gaps
- No public per-stream attestation mapping escrow releases to near.com fees vs Confidential Infrastructure Fee vs other private settlements.
- No disclosed rate card for the Confidential Infrastructure Fee (bps by asset/route).
- Unclear whether DefiLlama “revenue” fully includes confidential-path economics the same way as public collectors; reconciliation to wallets holds in aggregate but not by stream.

## What would make Confidential Intents a durable moat vs a feature peers can copy?

### Takeaway
Durability rests less on the confidentiality *idea* (copyable) than on **protocol-native private execution + already-dominant Intents liquidity/distribution + compliance-shaped trust**. The moat is contingent: TEE/validator trust, regulatory acceptance of ingress-screened privacy, and continued volume share. Absent those, peers can ship “confidential parameter” UX on their own private or ZK rails.

### Cited Findings
- Integration moat claim (NEAR): confidential rail is “a parameter, not a rebuild” on the same 1Click API partners already use; GA opened the same infra near.com used to all integrators. — [GA announcement](https://www.near.org/blog/announcing-general-availability-of-confidential-intents)
- Protocol coupling: private shard launched with Nightshade 3.0 as protocol-layer confidential execution—not only an app-layer mixer. — [NEAR Blockchain](https://www.near.org/blockchain)
- Distribution already live: wallets/platforms (Infinex, Meteor, THORWallet, Stargate, Solflare, LeoDex, Aurora Intents flag, Splits, etc.) per Nansen Q3. — [Nansen NEAR Q3 2026](https://nansen.ai/post/near-q3-2026-report)
- Venue scale context (repo): Intents ~**55.7%** of peer-set cross-chain volume (30d) vs THORChain/Chainflip/Maya; ~$4.0B / 30d. Confidentiality layers on the largest venue in that set. — [/tmp/nfs/REPORT.md](file:///tmp/nfs/REPORT.md)
- Design differentiation NEAR stresses: no client ZK; ingress screening + planned selective disclosure; individual encryption vs pools—aimed at “durable privacy infrastructure” vs “temporary opacity.” — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works)
- Marketing moat language (a16z quote used by NEAR) is not evidence of exclusivity. — [GA announcement](https://www.near.org/blog/announcing-general-availability-of-confidential-intents)

### Inferences
**What could make it durable**
1. **Liquidity + solver network on the private relay**—solvers already quote IMT/FAR; cold-start cost for a peer confidential venue is high if Intents already aggregates cross-chain size.
2. **Default distribution**—near.com confidential-by-default plus 1Click parameter means confidentiality compounds with every partner without new privacy R&D.
3. **Compliance-shaped product**—screen-at-ingress + selective disclosure roadmap may be what regulated size *can* use, while pure ZK/mixer products face venue/off-ramp bans. If that regulatory niche holds, copycats need the same posture, not just privacy tech.
4. **Protocol private shard**—harder for pure app-layer bridges to match “no public mempool/explorer” execution without L1 cooperation; first-mover on Nightshade private shard is real but not exclusive forever.

**What peers can copy / what erodes the moat**
1. Any L1/L2 can add TEEs, permissioned shards, or ZK execution privacy and expose a swap API flag.
2. CEX dark books already offer size privacy with deeper capital and familiar compliance; Confidential Intents competes on self-custody narrative, not on proven institutional depth.
3. Trust assumptions (7 validators, TEE, PoA bridge) are a **weakness peers will attack in diligence**—if size demands trustlessness, ZK competitors win the narrative even with worse UX.
4. Partner concentration (e.g. SwapKit ~38% of 1Click) means distribution moat is partly rented. — [/tmp/nfs/docs/intents-fee-flows.md](file:///tmp/nfs/docs/intents-fee-flows.md)

**Prop judgment on moat durability vs trust assumptions**
- Treat Confidential Intents as a **conditional moat**: durable *if* (a) Intents keeps liquidity primacy, (b) permissioned/TEE trust remains acceptable to size users, and (c) regulators tolerate screened confidential venues. It is **not** a cryptographic moat.
- Most likely durable layer is **liquidity + API distribution + compliance story**, not uniqueness of private execution. Feature copy risk is high over a 2–3 year horizon; switching costs are moderate (API parameter) unless solver liquidity and confidential balances create lock-in.
- Upside case for durability is **regulatory bifurcation**: screened private shards become the only privacy rails that retain banking/off-ramp access, while anonymity pools are pushed off platforms—then NEAR’s architecture is hard to displace quickly. That scenario is plausible but not evidenced as settled policy as of Nov 2026.

### Gaps
- No competitor teardown of peer confidential-execution roadmaps (other L1 private shards, encrypted mempools, ZK intents) in this note set.
- No retention metrics (repeat confidential users, balance duration) to test lock-in beyond TVL snapshots.
- Unclear open-sourcing / operator decentralization roadmap for FAR validators that would change the trust-vs-moat balance.

## What are the main trust and regulatory risks?

### Takeaway
Core risks are **operator/TEE/bridge trust**, **incomplete privacy at the destination edge**, **application-layer freezes (SHIELD)**, **fee/treasury opacity**, and **regulatory pressure on privacy venues**—plus selective disclosure still being a roadmap item rather than shipped institutional audit tooling.

### Cited Findings
- Trust model admitted by NEAR: “trust-minimized… rather than… fully trustless” in exchange for UX/functionality. — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works)
- Seven permissioned validators; no public RPC; TEE bridge to mainnet. — [NEAR Blockchain](https://www.near.org/blockchain)
- PoA / Private bridge is **request-driven** (RPC requests, not passive on-chain event detection)—operational and key-compromise surface for mint/burn. — [MM docs](https://docs.near-intents.org/integration/market-makers/confidential-intents)
- Privacy incompleteness: destination settlement public (asset, amount, recipient). Chain analytics can still cluster large opaque inflows/outflows around bridge/solver addresses. — [Aurora docs](https://docs.intents.aurora.dev/confidential-intents)
- Ingress AML + SHIELD pauses/delays: compliance feature and censorship/availability risk; coverage “can vary by flow.” Law-enforcement portal via Kodex. — [Risk & Compliance](https://docs.near-intents.org/security-compliance/risk-and-compliance); [SHIELD docs](https://docs.near-intents.org/security-compliance/proactive-intents-security)
- Selective disclosure **planned**, not described as fully generally available in May/Jul 2026 architecture posts—institutions needing auditor view keys today may lack the shipped control NEAR markets. — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works); [GA announcement](https://www.near.org/blog/announcing-general-availability-of-confidential-intents)
- Independent caution (LeoDex): unpublished TEE attestations, opaque validator set, no independent audit as of July 2026. — [LeoDex editorial](https://leodex.io/editorial/near-confidential-intents-july-2026)
- Fee/treasury opacity risk for investors and possibly for partners: Confidential Infrastructure Fee retained by Intents Technology; escrow unshields unattested. — [/tmp/nfs/docs/partner-concentration.md](file:///tmp/nfs/docs/partner-concentration.md)
- Regulatory posture: NEAR positions product against mixers (screen then encrypt) and analogizes to regulated trading venues (eligibility at onboarding, not real-time order-flow surveillance). That may reduce mixer-style enforcement risk but creates **obligations** (sanctions screening accuracy, LE response, future view-key compulsion). Mis-screening (false negatives) is a sanctions risk; over-blocking is a product risk. — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works)

### Inferences
- **Trust risk hierarchy:** (1) private-shard validator collusion or compromise exposing order flow; (2) TEE break or bridge key failure enabling theft or false mint/burn; (3) SHIELD/operator policy freezing user funds; (4) analytics re-linking via public edges despite private mid-path.
- **Regulatory risk hierarchy:** (1) treatment of permissioned confidential venues as money-transmission / VASP activity; (2) pressure to expand monitoring *inside* the shard (breaking the “no continuous surveillance” promise); (3) association risk from any illicit flow that passes ingress screening; (4) uneven global rules—product may be fine in some jurisdictions and restricted in others.
- **Token/investor risk:** rising confidential mix increases reliance on operator honesty and NEAR attestations for the buyback narrative; a freeze or bridge incident would hit both TVL confidence and the fee-capture story simultaneously.
- Confidentiality as size wedge works only while **trust assumptions remain acceptable to the capital it courts**. If institutions demand proof systems or diversified operator sets, the current seven-validator + TEE design is a bottleneck, not a feature.

### Gaps
- No public incident history for private-shard downtime, bridge bugs, or false SHIELD blocks beyond the Bitget-linked rejection claim.
- Selective disclosure GA status and auditor tooling maturity as of Nov 2026 not confirmed in primary docs fetched for this note.
- Legal opinions / VASP licensing status of Intents Technology / Defuse for confidential flows not reviewed here.
- TEE vendor, attestation frequency, and hardware TCB details not in NEAR’s public product blogs.

---

## Cross-cutting: marketing vs evidenced behavior (cheat sheet)

| Claim class | Example | Status as of Nov 2026 |
|---|---|---|
| Architecture | Private shard, no client ZK, ingress screening, IMT/FAR shield-unshield | **Evidenced** in NEAR blogs + Intents MM docs |
| UX | 1Click `confidentiality` parameter; near.com confidential mode/default | **Evidenced** |
| Adoption proxies | ZEC $1.5B→$2.6B settled; near.com ~42% confidential early; TVL ~$30M→~$160M | **Evidenced** (source-dated; methods partly opaque) |
| Size/institution preference | Dark-pool for desks; institutions require this | **Mostly marketing**; proxies only |
| MEV/frontrun elimination at equal UX | Stated benefit | **Asserted**, not independently measured here |
| Selective disclosure | View keys for auditors | **Roadmap** in primary blogs |
| Token capture clarity | Fees → buybacks transparently | **Weakened**: escrow unshields large & unattested |
| Moat | “Privacy will be the most important moat” | **Slogan**; durability conditional on liquidity + trust + regulation |
