# Confidential Intents — trust, attestation, regulatory surface

*Prop research sub-note for NEAR investment thesis. As of November 2026. Window metrics: 30 days to **2026-11-04** unless dated otherwise.  Marketing claims labelled separately from measured facts.*

Sources: primary Intents / 1Click terms, NEAR blogs, MM docs, LeoDex integrator note, Nansen Q3 2026, DefiLlama adapter, and committed repo series (`REPORT.md`, `structural-thesis.md`, `confidential-intents.md`, `capture-stack.md`, `competitive-structure.md`, `partner-concentration.md`, `catalyst_math.json`).

---

## Q1. Map the trust set precisely: what is attested vs asserted?

### Takeaway
The confidential trust set is a **permissioned private-shard venue** (seven validators, no public RPC, TEE bridge, ingress sanctions screen, SHIELD pause layer) with **public destination settlement**. NEAR admits “trust-minimized, not trustless.” Primary docs **attest** architecture and fee ownership; they **assert** independence of validators, TEE attestation quality, and institutional readiness of selective disclosure (still roadmap). Independent notes flag unpublished TEE attestation detail and opaque validator roster.

### Cited Findings

**Attested in primary docs (architecture / product surface)**
- Private shard: restricted visibility, **no public RPC/API/explorer**, PBFT ~200ms finality, tokens burned after withdrawal; connected to mainnet via bridge. — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works)
- Protocol page: **seven permissioned validators** + **TEE-based bridge** as foundation for Confidential Intents. — [NEAR Blockchain](https://www.near.org/blockchain)
- Two-chain MM model: public `intents.near` + FAR private instance; shield mints IMT vs Treasury lock; unshield burns IMT / releases treasury; swaps via `token_diff` invisible to public indexers. Treasury = `PRIVATE_TREASURY_ACCOUNT_ID` (`51e8f94d…7cbe`), production constant. — [Confidential Intents MM docs](https://docs.near-intents.org/integration/market-makers/confidential-intents)
- PoA / private bridge is **request-driven** (RPC requests, not passive event detection). — same MM docs
- Scope of privacy (integrator): origin wallet, route, source↔destination link hidden; **destination tx, asset, amount, recipient remain public**. — [Aurora Confidential Intents](https://docs.intents.aurora.dev/confidential-intents)
- Explicit tradeoff language: “trust-minimized… rather than… fully trustless” in exchange for UX (no client ZK proofs). — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works); [GA announcement](https://www.near.org/blog/announcing-general-availability-of-confidential-intents)
- Ingress sanctions / flagged-address screening before funds enter; once inside, NEAR says txs are **not continuously monitored**. AML stack cited (internal portal, Binance AML, AMLBot/PureFi, TRM for non-dry quotes); coverage “can vary by flow.” — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works); [Risk & Compliance](https://docs.near-intents.org/security-compliance/risk-and-compliance)
- SHIELD: application-layer allow/delay / scoped pauses; Nansen reports >$50M Bitget-linked attempted transfers **rejected** (rejected attempts ≠ recovered funds); protocol remains permissionless at base. — [Proactive Intents Security](https://docs.near-intents.org/security-compliance/proactive-intents-security); [Nansen NEAR Q3 2026](https://nansen.ai/post/near-q3-2026-report)
- Selective disclosure (account-level view key, user-initiated, time-scoped): **roadmap** in May/Jul 2026 architecture posts — not described as generally shipped auditor tooling. — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works)

**Asserted / marketing / incomplete attestation**
- Validator “independence,” full public roster, slashing/fault history — **not published** in primary docs reviewed. — gap noted across [LeoDex editorial](https://leodex.io/editorial/near-confidential-intents-july-2026) and repo confidential note
- TEE attestation frequency, vendor TCB, hardware proofs — LeoDex (Jul 2026): attestation details **not published**; no independent security audit seen as of that writing. Later audit status **not confirmed** in this pass. — [LeoDex](https://leodex.io/editorial/near-confidential-intents-july-2026)
- “Verifiable infrastructure” / dark-pool analogy bringing institutional size from CEXes — NEAR framing; fill-quality / MEV savings vs public Intents **asserted**, not independently measured. — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works)
- Distinct from **public** Intents MPC: Chain Signatures **11-of-17** in Intel TDX with named operators and Trail of Bits audits cited — that attestation stack covers cross-chain signing, **not** the seven-validator private shard. Do not conflate. — [Chain Signatures in TEEs](https://www.near.org/blog/chain-signatures-tee)

**Measured (repo, not DefiLlama scrape alone)**
- Escrow identity and exact-funded unshields: all **909** window deliveries funded to yoctoNEAR — privacy path working as designed; fee *stream* still unattested. — [REPORT.md](file:///tmp/nfs/REPORT.md); [partner-concentration.md](file:///tmp/nfs/docs/partner-concentration.md)

### Inferences
- Trust surface hierarchy for diligence: (1) private-shard validator collusion/compromise of order flow; (2) TEE break / bridge key failure (false mint-burn); (3) SHIELD/operator policy freeze; (4) public-edge re-linking despite private mid-path.
- What is “attested” for an investment underwrite is thinner than what is “documented”: architecture is clear; **operator identity, TEE proofs, and fee→wallet causality on the private vertical are not**.
- Compliance design (screen-then-encrypt) is intentional product differentiation vs mixers — and creates obligations (sanctions accuracy, LE response, future view-key compulsion) that pure ZK stacks often avoid until enforcement hits.

### Gaps
- No primary public roster of the seven validators or independence criteria as of Nov 2026.
- No confirmed post-Jul-2026 independent audit of FAR / TEE bridge / PoA mint-burn.
- Selective disclosure GA status and auditor tooling maturity as of Nov 2026 not confirmed in primary docs fetched for this note.
- Legal / VASP licensing status of Intents Technology for confidential flows not reviewed here.

---

## Q2. Economic take: confidential volume vs public; escrow share of buyback NEAR

### Takeaway
Confidential rails are the only fee vertical where partners have **zero contractual claim** (AppFee off; Confidential Infrastructure Fee set/retained by Intents Technology). That can raise NEAR’s *economic* take while destroying *public* attestation of capture. In the 30d window, ~**59%** of buyback-wallet NEAR arrived as escrow unshields (~$824K); measured issuance offset is a **4.5–15.8%** range until per-stream attestation exists. Forwarding to wallets is a **permission, not an obligation**.

### Cited Findings

**Contract / fee ownership (primary — not marketing)**
- Confidential swaps: **no AppFee**, no developer entitlement; Intents Technology “sets, charges, and retains” the Confidential Infrastructure Fee “for its own account”; rates vary by route/asset/developer; Intents Technology “determines which mode applies by default.” — [1Click Terms §6.8 / Schedule 1 §6](https://docs.near-intents.org/security-compliance/terms-of-service)
- Schedule 1 §1.7: Infrastructure Fees **may** be directed to ecosystem recipients — permission, **not** a public obligation to buybacks. — same Terms
- Public path contrast: partners set `appFees`; documented default 50/50 with 1Click floor; Commercial Agreements override Schedule 1. Observed SwapKit-class channels pay listed partner fees in full with near-zero explicit buyback. — [Fees](https://docs.near-intents.org/resources/fees); [capture-stack.md](file:///tmp/nfs/research_notes/NEAR%20Intents%20structural%20thesis/capture-stack.md)

**Measured window (30d to 2026-11-04)**
- Three revenue wallets: **418.8K NEAR (~$2.01M)** = **100.9%** of DefiLlama Intents revenue — aggregate capture reconciles. — [REPORT.md](file:///tmp/nfs/REPORT.md)
- Buyback-wallet composition: ~$460K explicit buyback collector; ~$109K quote-improvement; **~$823.7K (~59.1%)** escrow unshields. Same path feeds most of `fefundsadmin`. — [partner-concentration.md](file:///tmp/nfs/docs/partner-concentration.md); REPORT marker `escrow_share_of_buyback_near_30d_pct` **58.8%**
- Issuance ladder (exploratory): all-wallets offset **15.81%** of net issuance; public collectors **4.53** pts; escrow unshields **11.25** pts → underwrite as **4.5–15.8%** pending attestation. — [THESIS.md](file:///tmp/nfs/THESIS.md); [REPORT.md](file:///tmp/nfs/REPORT.md)
- Escrow share of buyback NEAR climbed with rollout: Jul (from 07-07) **17.5%**, Aug **28.6%**, Sep **53.0%**, Oct **57.4%** (then ~59% in latest 30d block). — [confidential-intents.md](file:///tmp/nfs/research_notes/NEAR%20Intents%20structural%20thesis/confidential-intents.md) citing THESIS
- Gross venue take ~**15.3 bp**; captured ~**4.98 bp**; capture share ~**32.5%**; partners kept ≥**1.81×** NEAR captured revenue on visible 1Click half. — [catalyst_math.json](file:///tmp/nfs/data/derived/catalyst_math.json); [REPORT.md](file:///tmp/nfs/REPORT.md)
- Two documented readings for escrow NEAR (chain cannot distinguish): (1) near.com confidential-mode fees; (2) Confidential Infrastructure Fee retained then swept. — [partner-concentration.md](file:///tmp/nfs/docs/partner-concentration.md)
- Authenticated Partner JWT cannot read user confidential data — third-party analytics cannot reconstruct confidential fee attribution from public APIs. — [API authentication](https://docs.near-intents.org/integration/distribution-channels/1click-api/authentication)

**Marketing vs measured**
- Marketing: near.com “100% of fees to a NEAR revenue wallet”; FAQ “50/50” with third parties. — [revenue.near.org](https://revenue.near.org/)
- Measured: SwapKit ~38% of 1Click volume with ~$159 explicit buyback fees vs ~$3.53M partner fees; DefiLlama investors page “100% of volume triggers $NEAR purchases” **overstates** vs ~5 bp captured / high-20s% of gross. — [capture-stack.md](file:///tmp/nfs/research_notes/NEAR%20Intents%20structural%20thesis/capture-stack.md); [Nansen](https://nansen.ai/post/near-q3-2026-report) capture 28.4% trailing 30d (down from 30.5%)

### Inferences
- **High-margin condition for confidential volume:** CIF stays partner-proof *and* continues to be swept into the three DefiLlama revenue wallets at rates that support (or raise) captured bp — without that sweep, confidential mix is a product win that can be a token **null**.
- **What kills margin quality:** (a) Intents Technology retains CIF as opex (“for its own account”) and stops wallet sweeps — contractually allowed; (b) attestation shows unshields are discretionary top-ups / non-fee transfers → collapse to ~4.5% issuance floor; (c) confidential share rises while public attachment rolls over → reported DefiLlama “revenue” becomes mostly opaque.
- Economic take *can* improve with confidential mix relative to SwapKit-class public deals; epistemic quality of the token link deteriorates on the same path. Treat escrow-funded buybacks as **received, source-unattested**.

### Gaps
- No disclosed rate card (bps) for Confidential Infrastructure Fee by asset/route.
- No per-stream attestation mapping escrow releases → near.com fees vs CIF vs other private settlements.
- Unclear whether DefiLlama volume/revenue fully includes confidential-path economics the same way as public collectors (aggregate wallet reconciliation holds; stream split does not).

---

## Q3. Institutional / compliance: when is “trust-minimized not trustless” a feature vs a risk?

### Takeaway
For desks that want **dark pre-trade + public settlement + ingress screening + eventual selective disclosure**, the permissioned design can be a *feature* (CEX-like operational trust without pooled mixer stigma). For auditors, risk, or capital that requires **cryptographic exclusivity, public operator sets, or shipped view keys today**, the same design is a *refusal risk*. Named institutional desk flow remains mostly marketing; evidenced demand is privacy-asset flow, sticky confidential balances, and default-driven mix.

### Cited Findings

**Feature posture (documented design intent)**
- Screen-at-ingress then encrypt individually (not anonymity-set pooling); framed against mixers regulators target. — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works)
- Dark-pool analogy: hide pre-trade order flow / signaling; destination settlement still verifiable. — same; [Aurora docs](https://docs.intents.aurora.dev/confidential-intents)
- SHIELD + AML vendors + Kodex LE portal: operational controls desks recognize. — [Risk & Compliance](https://docs.near-intents.org/security-compliance/risk-and-compliance); [SHIELD](https://docs.near-intents.org/security-compliance/proactive-intents-security)
- Product surface for orgs: Confidential Treasuries (multisig on private shard). — [Confidential Treasuries](https://docs.business.near.com/confidential-treasuries)
- UX: 1Click `confidentiality: basic|advanced` parameter — no client proving. — [Confidential Swaps docs](https://docs.near-intents.org/integration/distribution-channels/1click-api/quickstart/confidential-swaps)

**Risk / auditor refusal surface**
- Selective disclosure still **roadmap** in primary architecture posts — auditor view keys not evidenced as generally available tooling. — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works)
- LeoDex: unpublished TEE attestations, opaque validator set, no independent audit as of Jul 2026. — [LeoDex](https://leodex.io/editorial/near-confidential-intents-july-2026)
- Incomplete privacy: destination amount/recipient public → chain analytics can still cluster opaque bridge/solver edges. — [Aurora docs](https://docs.intents.aurora.dev/confidential-intents)
- Regulatory bifurcation risk: permissioned confidential venue may be treated as VASP / money-transmission activity; pressure to expand monitoring *inside* the shard would break the “no continuous surveillance” promise; false-negative screening = sanctions risk; over-blocking = product risk. — inferred from [Risk & Compliance](https://docs.near-intents.org/security-compliance/risk-and-compliance) + architecture blogs

**Evidenced adoption proxies vs marketing**
- **Measured / sourced:** ZEC settled across Intents $1.5B (GA Jul) → >$2.6B (Nansen Q3); near.com ~40–42% confidential share *before* default; Confidential TVL ~$30M (Jul) → ~$160M Q3-end (+463% QoQ); near.com confidential-by-default **1 Sep 2026**, ~$2.57B Q3 (~¼ of Intents). — [GA](https://www.near.org/blog/announcing-general-availability-of-confidential-intents); [Nansen Q3 2026](https://nansen.ai/post/near-q3-2026-report)
- **Mostly marketing:** “trading desks / institutions require this”; a16z privacy-moat slogan used in GA materials. — labelled in [confidential-intents.md](file:///tmp/nfs/research_notes/NEAR%20Intents%20structural%20thesis/confidential-intents.md)
- Public 1Click already whale-skewed (≥$10K = 3.4% of count, **77.1%** of volume) — size preference for dark mode is **plausible, not ticket-distributed**. — [intents-fee-flows.md](file:///tmp/nfs/docs/intents-fee-flows.md)

### Inferences
- **Feature regime:** capital that already trusts CEX matching engines / dark pools and wants self-custody narrative + wallet embed + sanctions hygiene — trust-minimized is sellable.
- **Risk regime:** fund auditors / crypto-native mandates that score “trustless settlement” or require reproducible TEE attestations and named operators — seven-validator + unpublished attestation is a diligence fail, not a footnote.
- Bifurcation that would *entrench* the wedge: screened private shards retain banking/off-ramp access while anonymity pools are pushed off platforms. Plausible; **not settled policy** as of Nov 2026.
- Investor risk couples to product risk: a bridge/SHIELD incident hits TVL confidence and the escrow-funded buyback narrative simultaneously.

### Gaps
- No public confidential-vs-public volume by ticket size or counterparty type.
- No independent attestation that regulated funds/banks are a material share of confidential TVL.
- No public incident history for private-shard downtime / false SHIELD blocks beyond Bitget-linked rejection claim.
- Legal opinions on entity perimeter (NEAR Protocol / Foundation / Intents Technology) for confidential fee retention not in fee docs.

---

## Q4. Competitive copy risk: can peers commoditize dark execution + wallet embed?

### Takeaway
The confidentiality *idea* is copyable; the current wedge is **liquidity + 1Click embed + compliance-shaped trust on the largest peer-set venue**, not cryptographic exclusivity. THOR/Chainflip/Maya can (and do) fight inside the same SwapKit pipe on price/subsidy without dark mode. Peers that ship “confidential parameter + enough pairs + partner fee” commoditize the UX wedge; meta-routers (LI.FI, ERC-7683 RFQ) commoditize settlement itself. Durability is contingent — feature-copy risk is high over a 2–3 year horizon unless solver liquidity and confidential balances create lock-in.

### Cited Findings

**What Intents has that peers must match**
- Peer-set leadership: Intents **$4.0B / 15.3 bp / 55.7%** share vs THOR $1.8B / 12.3 bp, Chainflip $0.85B / 31.5 bp, Maya $0.53B / 9.4 bp (30d to 2026-11-04). — [REPORT.md](file:///tmp/nfs/REPORT.md); [competitive-structure.md](file:///tmp/nfs/research_notes/NEAR%20Intents%20structural%20thesis/competitive-structure.md)
- 1Click REST collapses solver discovery; ~39 chains / ~229 assets vs vault venues’ thinner sets. — [1Click API](https://docs.near-intents.org/integration/distribution-channels/1click-api/about-1click-api); nearstats cited in competitive note
- Confidentiality as API parameter on rails partners already use (GA opened near.com infra to integrators). — [GA announcement](https://www.near.org/blog/announcing-general-availability-of-confidential-intents)
- Protocol-layer private shard (Nightshade) — harder for pure app-layer bridges to match “no public mempool/explorer” without L1 cooperation; first-mover, not forever exclusive. — [NEAR Blockchain](https://www.near.org/blockchain)

**What peers already do / can do**
- Security model difference: THOR/Maya/Chainflip = bonded threshold vaults (economic underwriting); Intents = solver inventory + bridges/MPC. Peers do **not** need private shards to underwrite native BTC/ETH depth. — [THOR security](https://docs.thorchain.org/network-security-governance); [Chainflip overview](https://docs.chainflip.io/protocol/protocol-overview)
- THOR ADR-029 REVSHARE subsidizes affiliates inside SwapKit without raising user fee — explicit fight for the same wallet pipe; early data: THOR still single-digit % of SwapKit trades. — [ADR-029](https://blog.thorchain.org/adr-029-affiliate-revenue-share)
- SwapKit monetizes Intents **beside** THOR, Maya, Chainflip, Garden, Mayan, etc. — share is quote-win × coverage, not exclusive distribution. — [SwapKit Monetization](https://www.swapkit.dev/monetization/)
- Any L1/L2 can add TEEs, permissioned shards, encrypted mempools, or ZK execution privacy and expose a swap flag; CEX dark books already offer size privacy with deeper capital. — inference in [confidential-intents.md](file:///tmp/nfs/research_notes/NEAR%20Intents%20structural%20thesis/confidential-intents.md); [structural-thesis.md](file:///tmp/nfs/docs/structural-thesis.md)
- RFQ / ERC-7683 / Across-UniswapX paths make settlement rails interchangeable — Intents as one backend among backends. — [competitive-structure.md](file:///tmp/nfs/research_notes/NEAR%20Intents%20structural%20thesis/competitive-structure.md)

**Marketing vs measured on moat**
- Marketing: “privacy will be the most important moat” (a16z quote in GA). — slogan
- Measured: durability rests on liquidity primacy + API distribution + compliance niche — repo judgment: **conditional moat, not cryptographic moat**. — [confidential-intents.md](file:///tmp/nfs/research_notes/NEAR%20Intents%20structural%20thesis/confidential-intents.md); [structural-thesis.md](file:///tmp/nfs/docs/structural-thesis.md)

### Inferences
- **Commoditization path that kills the wedge:** peer ships dark-enough UX *and* wins/keeps SwapKit-Ledger-Trust default quotes at lower all-in cost → Intents keeps volume only by giving away capture (race to supply side). That is the competition falsifier in the capture stack.
- **What peers cannot instantly copy:** solver network already quoting IMT/FAR + confidential TVL stickiness + near.com default mix. Cold-start cost is real; switching cost for wallets is moderate (parameter / provider swap) unless balances lock users in.
- Trust assumptions (7 validators, TEE, PoA) are a diligence attack surface peers will use even when they cannot match product UX.
- Scoreboard split: peer volume share + integrator HHI for industry structure; **captured bp + escrow attestation quality** for the NEAR token claim — not gross fees alone.

### Gaps
- No competitor teardown of peer confidential-execution roadmaps in this note set (other L1 private shards, encrypted mempools, ZK intents).
- No public A/B of Intents vs THOR quote win-rate inside SwapKit at matched pairs for the metrics window.
- No retention metrics (repeat confidential users, balance duration) beyond TVL snapshots.
- Across/UniswapX volume overlapping this peer-set definition not in `metrics.json`.

---

## Q5. Proprietary metric ideas (DefiLlama-blind)

### Takeaway
The investment-relevant confidential metrics are about **attestation quality and fee ownership**, not headline volume or TVL. Three core constructs already have repo numerators: escrow-dependence, confidential share of capture (range), and attestation gap. Additional constructs below turn primary-doc trust assumptions into a scoreboard.

### Cited Findings (anchors already measured)
- **Escrow-dependence ratio:** escrow unshields / buyback-wallet NEAR inflows ≈ **58.8–59.1%** in latest 30d; climbed 17.5% → 57.4% Jul→Oct. — REPORT; partner-concentration; confidential-intents
- **Attestation gap:** issuance offset top (**15.81%**) − public-collector floor (**4.53%**) = **11.28 pts** unattested; underwrite as **4.5–15.8%** band. — THESIS / REPORT ladder markers
- **Confidential share of capture (proxy):** escrow pts / all-wallet pts ≈ **11.25 / 15.81 ≈ 71%** of *measured wallet capture* arrives unattested; vs capture_share of gross fees **32.5%** (different denominator — do not conflate). — catalyst_math baselines; ladder
- **Forwarding optionality:** CIF retained “for its own account” + Schedule 1 §1.7 discretionary direction — binary policy risk not visible on DefiLlama. — 1Click Terms
- **Attachment vs escrow opacity:** public buyback attachment 23.6% → 43.0% while escrow share of buybacks also rose — both can rise together; only attachment is Explorer-auditable. — catalyst_math; partner-concentration

### Inferences — metric definitions to track

| Metric | Definition | Why DefiLlama misses it | Kill / keep signal |
|---|---|---|---|
| **Escrow-dependence ratio** | Escrow unshield USD (or NEAR) ÷ buyback-wallet inflows (30d) | Llama reports wallet totals, not funding path | Rising without attestation → underwrite floor |
| **Attestation gap** | Ladder top − public-collector floor (pts of issuance) | Llama has one “revenue” number | Gap close via attestation = range collapse; gap widen = opacity |
| **Confidential share of capture** | Escrow-funded wallet NEAR ÷ all revenue-wallet NEAR | No stream tags | High + unattested = economic take opaque |
| **CIF forwarding rate** | NEAR swept to revenue wallets attributed to confidential fees ÷ estimated confidential fee pool | Private ledger; needs NEAR attestation | →0 kills high-margin thesis for confidential mix |
| **Partner-proof fee share** | Volume on rails with zero AppFee (confidential) ÷ total Intents vol | Volume scrape lacks fee-ownership flag | Rising is margin-positive *only if* CIF forwards |
| **Trust-set concentration** | 1/N private validators; named roster coverage; TEE attestation freshness | Off-chain / unpublished | Roster opacity + incident = diligence kill |
| **Selective-disclosure readiness** | Binary: view-key tooling GA for auditors (Y/N) + time-to-disclose SLA | Product blog roadmap only | N → auditor refusal risk for “institution” narrative |
| **Dark-embed copy index** | Count of peer venues offering confidential/dark flag *inside* overlapping wallet aggregators | Not in fee adapters | Rising → commoditization |
| **Edge-reidentifiability** | Share of confidential flow with public destination clustering risk (amount/recipient visible) | Privacy blogs omit | High → “dark” incomplete for true stealth demand |

### Gaps
- CIF rate card and confidential volume by channel not public → “partner-proof fee share” and “CIF forwarding rate” need NEAR disclosure or private data room.
- Confidential-vs-public ticket distribution unpublished.
- No standardized peer “dark flag in SwapKit” tracker in repo yet.

---

## Proprietary punch (what has to be true / what kills it)

1. Confidential volume stays high-margin for NEAR only if the Confidential Infrastructure Fee remains partner-proof **and** is actually swept into the three revenue wallets — retention “for its own account” is the contractual kill switch.
2. The trust set that sells the product (7 validators, TEE bridge, no public RPC, ingress screen, SHIELD) is the same set that caps how “trustless” diligence can rate it; selective disclosure is still roadmap, so auditor refusal is a live regime, not a hypothetical.
3. Aggregate capture is real (wallets ≈ 100.9% of Llama revenue); **source** capture is not — ~59% of buyback NEAR is escrow-unattested by design, and escrow-dependence climbed through the confidential rollout.
4. Underwrite issuance offset as **4.5–15.8%** until per-stream attestation exists; the attestation gap (~11.3 pts) is the investment object DefiLlama flattens into one revenue print.
5. Economic take can improve with confidential mix (AppFee zero); epistemic quality of the token link deteriorates on the same path — treat that split as structural, not temporary noise.
6. “Institutions prefer confidential” is mostly marketing; measured signals are ZEC/privacy-asset flow, TVL stickiness, and near.com default mix — size preference is plausible given 77% whale volume, not ticket-proven.
7. Peers need not reinvent Nightshade to commoditize the wedge: match dark-enough UX + wallet embed + lower all-in cost inside SwapKit, or let meta-routers treat NEAR settlement as interchangeable filler.
8. What kills it fast: CIF stops forwarding; attestation shows unshields are non-fee; SwapKit/Ledger re-routes; TEE/validator/SHIELD incident; auditors refuse the trust set; peers ship confidential parameter at scale.
9. What has to stay true for the margin story: liquidity primacy on IMT/FAR, near.com / confidential mix rising *with* attestation, public attachment not rolling over, and regulators tolerating screened private shards rather than forcing in-shard surveillance.
10. Score escrow-dependence, attestation gap, CIF forwarding, and dark-embed copy before scoring Confidential TVL or “privacy moat” slogans — those are the proprietary surface a DefiLlama scrape cannot give.
