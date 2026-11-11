# Who owns the margin between a NEAR Intents user and the NEAR token (capture stack)

*Prop research note, as of Nov 2026. Synthesis of primary fee docs, 1Click terms, DefiLlama methodology, NEAR tokenomics, Nansen Q3 2026, Bitwise, and the project's 30-day window (2026-10-06 → 2026-11-04) that reconciles to DefiLlama revenue.*

## How is the stack layered (frontend / affiliate, aggregators, solvers, confidential escrow, revenue wallets, buyback)?

### Takeaway
The user pays a layered price — affiliate/app fee + 1Click infrastructure take (or confidential infrastructure fee) + solver/execution spread + a 1-pip protocol fee — and only the fraction that lands in three named NEAR revenue wallets is what DefiLlama counts as holders revenue for buybacks; most gross fee value stops at the distribution layer.

### Cited Findings
- **Protocol fee (base layer):** 0.0001% (1 pip) per transfer/swap, collected on-chain by `intents.near` and sent to `fee_collector`. — [NEAR Intents Fees](https://docs.near-intents.org/resources/fees)
- **Native frontend fee:** near-intents.org / near.com charges 0.2% on swaps through that channel, sent to `fefundsadmin.sputnik-dao.near`. — [NEAR Intents Fees](https://docs.near-intents.org/resources/fees)
- **1Click public-swap defaults (authenticated):** no `appFees` → 20 bps (1 bp on stablecoin / same-asset multichain); with `appFees` → documented 50/50 split with 1Click keeping ≥20 bps (1 bp on stables), subject to partner-specific configuration; unauthenticated adds 25 bps on top of the developer's full fee. — [Fees](https://docs.near-intents.org/resources/fees); [Fee Configuration](https://docs.near-intents.org/integration/distribution-channels/1click-api/fee-config)
- **Custom agreements override the default:** "Better fee sharing and custom conditions are available"; "That split is the default, not a universal rule. Exceptions and custom agreements exist." — [Fees](https://docs.near-intents.org/resources/fees)
- **Quote-improvement share:** if fill beats quote within ~30 minutes on real cross-asset swaps, improvement is split 50/50 between integrator and protocol. — [Fees](https://docs.near-intents.org/resources/fees)
- **Legal framing of AppFee vs Infrastructure Fee:** AppFee is the developer's pricing config; Intents Technology's Infrastructure Fee is consideration for 1Click access; "revenue share" in docs is only mechanical allocation, not a partnership or income participation. Commercial Agreements control where they conflict with Schedule 1. — [1ClickSwap API Terms of Use](https://docs.near-intents.org/security-compliance/terms-of-service)
- **Confidential swaps:** no AppFee and no developer entitlement; Intents Technology "sets, charges, and retains" the Confidential Infrastructure Fee "for its own account"; rates can vary by route/asset/developer and can be changed prospectively. Intents Technology also "determines which mode applies by default." — [1Click Terms §6.8 / Schedule 1 §6](https://docs.near-intents.org/security-compliance/terms-of-service)
- **Infrastructure fees may be directed to NEAR ecosystem recipients:** Schedule 1 §1.7 allows Infrastructure Fees to be directed to a designated fee recipient for ecosystem infrastructure/development/growth. That is a permission, not a public obligation to buybacks. — [1Click Terms Schedule 1](https://docs.near-intents.org/security-compliance/terms-of-service)
- **Solvers trade as principal:** Intents Technology relays quotes and settlement; it is never the trading counterparty; solvers provide their own liquidity and keep the bid-ask / inventory economics (subject to optional Solver Access Fee, which "may be zero"). Auction selection uses quoted price, latency, reliability; no best-execution duty. — [Solver Terms of Use](https://partners.near-intents.org/legal/solver-terms)
- **Confidential escrow identity:** `PRIVATE_TREASURY_ACCOUNT_ID` = `51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe`, a production constant; shield/unshield moves value between public `intents.near` and private FAR (`intents.far`). — [Confidential Intents](https://docs.near-intents.org/integration/market-makers/confidential-intents); [Confidential Example](https://docs.near-intents.org/integration/market-makers/confidential-example)
- **DefiLlama revenue definition (authoritative for "captured"):** Revenue = NEAR/wNEAR swept into three wallets — `fefundsadmin.sputnik-dao.near`, `1csfundsadmin.sputnik-dao.near`, `buybacks.multisignature.near` — excluding inter-wallet hops. Fees = gross protocol + affiliate fees across integrators. SupplySideRevenue = gross fees − captured revenue ("affiliate fees kept by solvers and third-party distribution channels (e.g. SwapKit)"). HoldersRevenue since **2026-02-23** = captured revenue used to buy back $NEAR **(not burned)**. — [DefiLlama near-intents adapter](https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/fees/near-intents/index.ts); [DefiLlama NEAR Intents](https://defillama.com/protocol/near-intents)
- **Official dashboard wallet split (all-time):** `fefundsadmin` 46.5%, `buybacks.multisignature.near` 40.5%, `1csfundsadmin` 12.9%. Capture mechanics (30D rates shown on dashboard): Front-end Fees 20.3%, Quote Improvement 3.6%, B2B Partners 10.4%. FAQ: near.com swaps "direct 100% of fees to a NEAR revenue wallet"; third-party "split 50/50" is the public marketing default. — [revenue.near.org](https://revenue.near.org/); also mirrored on [DefiLlama x NEAR FAQ](https://investors.defillama.com/near)
- **Fee switch / buyback program (primary):** Feb 2026 Intents fee switch live; distribution fees shared with partners; payouts denominated in $NEAR; revenue *can* be deployed for buybacks / buyback-and-earn / other supply tools at governance discretion — "No specific mechanism is guaranteed." — [Evolving NEAR Tokenomics](https://www.near.org/blog/evolving-near-tokenomics)
- **Windowed stack measurement (reconciles to DefiLlama):** over 2026-10-06→11-04, three revenue wallets received **418.8K NEAR (~$2.01M)**, **100.9%** of DefiLlama's reported Intents revenue for the same days; of buyback-wallet inflows, ~$460K via explicit buyback collector, ~$109K via quote-improvement collector, ~$824K (59%) via confidential-escrow unshields to fresh accounts (fee stream unattested). 1Click Explorer listed ~$4.45M partner app fees (ex-buyback), of which ~$4.21M had **no** buyback fee entry. — Methodology and wallet list: [DefiLlama adapter](https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/fees/near-intents/index.ts); escrow constant: [Confidential Intents](https://docs.near-intents.org/integration/market-makers/confidential-intents); fee-list semantics: [Fees](https://docs.near-intents.org/resources/fees)
- **Layer picture (judgment, ordered by where user margin is first claimed):**
  1. **Frontend / affiliate / hardware wallet** sets the listed `appFees` the user sees (often 50–145+ bps on wallet channels).
  2. **Aggregator (SwapKit, LI.FI, Rango, ZODL, etc.)** owns the commercial relationship that decides whether that fee is shared with 1Click or kept whole under a custom deal.
  3. **1Click / Intents Technology** takes Infrastructure Fee (or Confidential Infrastructure Fee) and may forward some of it to NEAR wallets under Schedule 1 §1.7 — forwarding is not fully visible for confidential flow.
  4. **Solvers** earn the residual execution spread (realized cost above listed fees averaged ~8.5 bp on $1K–$50K 1Click swaps in the window).
  5. **Protocol** takes 1 pip — economically negligible vs distribution fees.
  6. **Revenue wallets → buyback holding** — only the DefiLlama "Revenue" slice; held, not burned per adapter.

### Inferences
- The economically important stack is **distribution → Intents Technology → (optional) NEAR wallets**, not L1 gas. Protocol fee is a rounding error; pricing power lives where the user chooses a wallet/UI.
- Confidential mode creates a **second opaque vertical** inside the stack: same settlement brand, different fee ownership (100% Intents Technology by contract) and different auditability (unshields arrive on chain; attribution does not).
- Marketing "50/50 with partners" describes the **default public policy**, not the observed SwapKit-heavy reality (see next section).

### Gaps
- Exact Commercial Agreement terms with SwapKit / Ledger / Trust / Tangem are not public.
- Whether Confidential Infrastructure Fee is contractually or operationally forwarded to `buybacks.multisignature.near` vs retained by Intents Technology is not attested per stream.
- Solver-level P&L (who captures how much of the ~8.5 bp excess) is not disclosed; Solver Access Fee level as of Nov 2026 is not published beyond "may be zero."

## Who keeps most of the gross fee today, and why is that structurally sticky?

### Takeaway
Distribution channels — especially SwapKit-routed hardware/mobile wallets — keep the majority of gross Intents fees today; that is sticky because they own user attention and can negotiate custom fee schedules that pay them their full listed fee on chain while attaching little or no explicit buyback fee to NEAR.

### Cited Findings
- **Gross vs captured (DefiLlama / Nansen):** Gross fees and captured revenue are deliberately separate. DefiLlama: SupplySideRevenue = fees kept by solvers and third-party channels. Nansen (post-Q3 update dated Oct 6): lifetime fee capture ~**16.4%**; trailing 30-day capture **28.4%** (down from 30.5% prior). Cumulative fees >$52M with >$8M captured. — [DefiLlama adapter methodology](https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/fees/near-intents/index.ts); [Nansen NEAR Q3 2026](https://nansen.ai/post/near-q3-2026-report); [DefiLlama NEAR Intents](https://defillama.com/protocol/near-intents)
- **Blended venue fee vs peers (30d):** NEAR Intents ~15.3 bp of volume; THORChain 12.3 bp; Maya 9.4 bp; Chainflip 31.5 bp — Intents prices above most peers while holding ~55.7% peer-set volume share. — Peer metrics as compiled against DefiLlama venue series in project window; methodology for Intents fees: [DefiLlama NEAR Intents](https://defillama.com/protocol/near-intents)
- **Partners vs NEAR in 1Click window:** Partner-listed fees ~$4.45M; NEAR captured revenue across three wallets ~$2.01M; on partner swaps with no buyback entry, at most ~**19.6%** of those fees could reach NEAR wallets under the tightened escrow attribution; partners kept at least ~**1.81×** NEAR's entire captured Intents revenue (1Click half only). Partner fees stayed ~**10×** NEAR's explicit buyback fee across three consecutive 30-day blocks. — Fee-list rules: [Fees](https://docs.near-intents.org/resources/fees); revenue definition: [DefiLlama adapter](https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/fees/near-intents/index.ts)
- **On-chain partner payout evidence:** sampled swaps paid listed partner fees at the listed rate to implicit accounts (Ledger ~145 bp → `c4d748df…`, Trust via SwapKit 70 bp → `2f09a4dc…`, ZODL 67 bp → `d78abd…`); no 50/50 haircut taken out of the listed partner line. — Fee parameter semantics: [Fee Configuration](https://docs.near-intents.org/integration/distribution-channels/1click-api/fee-config); exception language: [Fees](https://docs.near-intents.org/resources/fees)
- **SwapKit concentration:** ~**38.2%** of 1Click volume (~21% of one-sided Intents); SwapKit partners listed ~$3.53M fees while explicit buyback fees from SwapKit were ~**$159** over 30 days. Trust Wallet routes most volume via SwapKit (70 bp to Trust, **0** bp explicit buyback) vs a smaller direct route (20 bp buyback, 0 partner bp). — Channel fee behavior under custom vs default: [Fees](https://docs.near-intents.org/resources/fees); [Fee Configuration](https://docs.near-intents.org/integration/distribution-channels/1click-api/fee-config)
- **NEAR's explicit 1Click take is rising from a low base:** buyback fee entry share of volume 23.6% → 43.0% across Aug→Nov 2026 blocks; explicit buyback bp of volume 1.83 → 4.08; captured take on DefiLlama volume basis 2.89 → 4.98 bp. Rise came mainly from **more volume carrying a buyback entry**, not from SwapKit share falling (SwapKit stayed ~36–38%). — Capture definition: [DefiLlama adapter](https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/fees/near-intents/index.ts)
- **Volume structure:** swaps ≥$10K are 3.4% of count but **77.1%** of 1Click volume; median swap ~$52 — fee revenue is whale- and channel-sensitive. Asset mix is stables/BTC/ZEC-heavy; NEAR on one side only **3.5%** of 1Click volume; 1Click was a net **exit** for NEAR (~$24M out vs ~$14.6M in). — Asset/venue context: [Nansen Q3 2026](https://nansen.ai/post/near-q3-2026-report) (ZEC >$2.6B settled pre-confidential GA); Intents as product: [Bitwise NRR launch](https://bitwiseinvestments.com/newsroom/the-bitwise-near-etf-nrr-launches-as-first-spot-near-etp-in-the-us)
- **near.com share:** Nansen: near.com ~$2.57B in Q3 (~**one quarter** of Intents volume) — the high-capture vertical, but not the majority of volume. — [Nansen NEAR Q3 2026](https://nansen.ai/post/near-q3-2026-report)
- **Conflict — marketing vs chain:** Public FAQ language says third-party swaps are split 50/50. Observed SwapKit economics and on-chain full payout of listed partner fees contradict treating 50/50 as the effective take on the largest channel. DefiLlama investors page also claims "100% of NEAR Intents volume triggers $NEAR purchases" — that overstates relative to ~5 bp captured take / ~30% of gross fees. — [revenue.near.org FAQ](https://revenue.near.org/); [DefiLlama x NEAR](https://investors.defillama.com/near); contradicted on mechanics by [Fees](https://docs.near-intents.org/resources/fees) ("exceptions exist") and on capture share by [Nansen](https://nansen.ai/post/near-q3-2026-report) / [DefiLlama protocol page](https://defillama.com/protocol/near-intents)

### Inferences
- **Gross fee ownership today:** distribution + solvers (supply side) > NEAR wallets. NEAR's share of gross is real and rising, but still the minority (~16% lifetime, high-20s trailing 30d per Nansen).
- **Stickiness reasons (structural, not cyclical):**
  1. **User ownership:** Ledger/Trust/Tangem own the interface; NEAR is interchangeable settlement rails unless default routing or exclusive features force otherwise.
  2. **Contractual flexibility:** docs and terms explicitly allow Commercial Agreements that break the default 50/50 — volume partners will demand and get those terms.
  3. **Price discrimination:** high listed fees on hardware wallets (100+ bp) are paid by users who don't comparison-shop cross-chain venues; NEAR capturing that surplus would mean renegotiating with the gatekeeper, not raising a protocol parameter users never see.
  4. **Confidential opacity:** a growing share of buyback-wallet NEAR arrives via unattested escrow unshields — good for privacy product, bad for proving partner-share economics.
- **Why NEAR still has a foothold:** default (no-referrer) and some direct integrations (e.g. Trust direct) attach meaningful buyback fees; near.com is 100% capture by policy; confidential fee is 100% Intents Technology by contract (forwarding discretionary).

### Gaps
- Full Intents (non-1Click) fee split is only partially visible; 1Click is ~55% of DefiLlama one-sided volume in the latest block — the other half's partner economics are not in the Explorer fee lists.
- No public disclosure of which Commercial Agreements waive the 50/50.
- Whether "held not burned" buybacks create lasting float reduction depends on treasury policy; revenue.near.org's "permanently remove from circulation" wording conflicts with DefiLlama's "not burned" and with observed wallet balances. — Conflict: [revenue.near.org](https://revenue.near.org/) vs [DefiLlama adapter](https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/fees/near-intents/index.ts)

## What levers does NEAR actually control vs what partners control?

### Takeaway
NEAR / Intents Technology control fee *parameters*, confidential defaults, buyback *policy*, and native-frontend mix; partners control user acquisition, listed `appFees`, and — via Commercial Agreements — whether the documented 50/50 ever binds. Token holders do not have a hard claim on either side's take.

### Cited Findings
- **NEAR / Intents Technology levers (documented):**
  - Set and change Infrastructure Fee rates, minimums, and parameters prospectively via Fee Documentation without amending Terms. — [1Click Terms §6.3, Schedule 1 §1.8](https://docs.near-intents.org/security-compliance/terms-of-service)
  - Set Confidential Infrastructure Fee unilaterally; no partner share. — [1Click Terms §6.8](https://docs.near-intents.org/security-compliance/terms-of-service)
  - Determine default confidentiality mode. — [1Click Terms §2.9](https://docs.near-intents.org/security-compliance/terms-of-service)
  - Direct Infrastructure Fees to a designated ecosystem recipient (Schedule 1 §1.7). — [1Click Terms](https://docs.near-intents.org/security-compliance/terms-of-service)
  - Switch a developer to the unregistered (worse) fee schedule for circumvention or breach. — [1Click Terms Schedule 1 §3](https://docs.near-intents.org/security-compliance/terms-of-service)
  - Solver access controls: performance standards, throttling, deselection, optional access fee, filters including `ONE_CLICK_API_ONLY`; no PFOF. — [Solver Terms §6, §9](https://partners.near-intents.org/legal/solver-terms)
  - Native frontend pricing (0.2% to `fefundsadmin`) and product defaults (near.com made confidentiality default Sept 1, 2026 per Nansen). — [Fees](https://docs.near-intents.org/resources/fees); [Nansen Q3 2026](https://nansen.ai/post/near-q3-2026-report)
  - Buyback / treasury deployment is **governance-discretionary**, not automatic entitlement. — [Evolving NEAR Tokenomics](https://www.near.org/blog/evolving-near-tokenomics)
- **Partner levers (documented + observed):**
  - Set `appFees` recipient and bps (user-facing price). — [Fee Configuration](https://docs.near-intents.org/integration/distribution-channels/1click-api/fee-config)
  - Negotiate Commercial Agreements that override Schedule 1 defaults. — [1Click Terms §6.1](https://docs.near-intents.org/security-compliance/terms-of-service)
  - Choose Public vs Confidential availability in their product (within whitelist rules). — [1Click Terms §2.9](https://docs.near-intents.org/security-compliance/terms-of-service)
  - Route users to competing venues (THORChain, Chainflip, Maya, CEX) — NEAR has no exclusive claim on wallet order flow. Peer set exists and prices differently. — [DefiLlama NEAR Intents](https://defillama.com/protocol/near-intents) (peer competition implicit in venue metrics)
- **What NEAR does *not* clearly control:**
  - Forcing SwapKit-class volume onto a 50/50 without volume risk — docs admit exceptions exist. — [Fees](https://docs.near-intents.org/resources/fees)
  - Burning buyback NEAR — adapter and holdings show hold, not burn. — [DefiLlama adapter](https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/fees/near-intents/index.ts)
  - Compelling attestation of confidential fee streams — privacy design makes external attribution impossible without NEAR cooperation. — [How Confidential Intents Works](https://www.near.org/blog/how-confidential-intents-works); [Confidential Intents](https://docs.near-intents.org/integration/market-makers/confidential-intents)
- **Issuance lever (adjacent, not Intents):** Bitwise/Nansen note governance discussion to cut annual issuance 2.5% → 1.6%; Bitwise NRR (0.75% fee, stakes NEAR) is demand-side access, not Intents take-rate. — [Nansen Q3 2026](https://nansen.ai/post/near-q3-2026-report); [Bitwise NRR](https://bitwiseinvestments.com/newsroom/the-bitwise-near-etf-nrr-launches-as-first-spot-near-etp-in-the-us)

### Inferences
- **Pricing power map:** End-user willingness-to-pay is largely harvested by **wallets**; NEAR's controllable levers are (a) grow high-capture mix (near.com / default buyback attachment), (b) confidential take (fully owned by Intents Technology), (c) raise floors on partners who lack exit alternatives, (d) issuance/buyback policy. Lever (c) is constrained by SwapKit exit optionality.
- **Default routing** is a soft lever: making confidential the near.com default grew escrow-path economics; forcing confidential (and thus no AppFee) on aggregator volume would be a partner fight and a volume risk.
- **Buyback fee attachment** (share of volume with an explicit buyback line) is the cleanest *observable* NEAR-side lever inside 1Click public flow — and it is the one that actually moved over 90 days.

### Gaps
- Governance process and legal entity boundary between "NEAR Protocol," NEAR Foundation, and "Intents Technology" for fee retention vs wallet forwarding is not fully spelled out in public fee docs.
- No public SLA on what fraction of Infrastructure / Confidential Infrastructure Fee must reach buyback wallets.

## What would a path to higher token capture look like without killing volume (scenarios, not forecasts)?

### Takeaway
Higher token capture without a volume collapse most plausibly comes from mix shift and attachment (more near.com / more buyback-tagged public volume / more confidential volume whose fees are actually forwarded), not from a blunt take-rate hike on SwapKit-class channels; each path has a different auditability and partner-friction profile.

### Cited Findings
- **Path materials already in motion:**
  - Explicit buyback attachment nearly doubled (23.6% → 43% of 1Click volume) while SwapKit share held ~flat — evidence that attachment can rise without immediately ejecting the aggregator. — Fee mechanics: [Fees](https://docs.near-intents.org/resources/fees); capture tracked as HoldersRevenue: [DefiLlama adapter](https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/fees/near-intents/index.ts)
  - near.com is ~25% of volume with 100% fee direction to a NEAR wallet by stated policy — scaling this mix raises capture without renegotiating SwapKit. — [Nansen Q3 2026](https://nansen.ai/post/near-q3-2026-report); [revenue.near.org FAQ](https://revenue.near.org/)
  - Confidential GA + near.com confidential-default expands the fee vertical where partners have **zero** contractual claim. — [1Click Terms §6.8](https://docs.near-intents.org/security-compliance/terms-of-service); [Nansen Q3 2026](https://nansen.ai/post/near-q3-2026-report)
  - Tokenomics blog explicitly names "expanding native front-end usage for higher direct value capture" as a near-term driver alongside revenue share. — [Evolving NEAR Tokenomics](https://www.near.org/blog/evolving-near-tokenomics)
- **Arithmetic context (not a forecast):** project window captured take ~5 bp of reported volume; gross ~15 bp; partners keep the wedge. Raising captured take toward partner-like rates (~10 bp) at constant volume would roughly double holders revenue; doing it only via mix shift (more 100%-capture frontend) avoids repricing aggregator users. Valuation framing on REPORT: multiple compression toward lower revenue multiples requires large numerator growth. — Revenue definition: [DefiLlama](https://defillama.com/protocol/near-intents); peer fee context via same methodology
- **Issuance interaction:** if issuance cap falls 2.5% → 1.6%, the *same* captured NEAR offsets a larger share of net issuance — a supply-side assist that does not require higher Intents take. — [Nansen Q3 2026](https://nansen.ai/post/near-q3-2026-report); [Evolving NEAR Tokenomics](https://www.near.org/blog/evolving-near-tokenomics)

### Inferences — scenarios (directional only)

| Scenario | Mechanism | Volume risk | Capture effect | Auditability |
|---|---|---|---|---|
| **A. Attachment creep** | More public 1Click volume carries explicit buyback fee / fewer zero-buyback custom deals on *new* partners | Low if grandfathered whales kept | Gradual; already observed | High (Explorer fee lists) |
| **B. Mix shift to near.com** | Consumer/agent UX pulls share from wallets | Medium (must win users, not just price) | High per dollar of shifted volume (100% policy) | Medium (frontend vs escrow) |
| **C. Confidential share ↑ with forwarding** | More volume in confidential mode; Infrastructure Fee retained then swept to wallets | Low–medium (privacy demand helps) | Potentially high; partner-proof by contract | **Low** unless attested |
| **D. Renegotiate SwapKit to true share** | Move Ledger/Trust/Tangem toward 50/50 or buyback line | **High** — exit hits ~38% of 1Click volume / narrative share vs peers | Large if successful | High |
| **E. Raise protocol / floor fees** | Lift 1-pip or universal floors | Medium–high on price-sensitive whale flow (77% of volume in ≥$10K swaps) | Small unless large hike | High |
| **F. Burn / lock buybacks** | Change hold → burn or buyback-and-earn | None on volume | Improves *quality* of capture, not fee take | High if on-chain |

- **Preferred path under "don't kill volume":** A + B + C(with attestation), treating D as optional and risky, E as last resort. C without attestation improves the *reported* DefiLlama revenue number but does not strengthen the investment case's auditability.
- **What would *not* work cleanly:** assuming documented 50/50 already applies to SwapKit; assuming volume growth alone fixes capture (partners scale with volume under custom deals); assuming buybacks equal burns.

### Gaps
- No public elasticity study of Intents volume vs take rate.
- No disclosed target capture rate from NEAR governance.
- Agent-commerce volume (Bitwise/NEAR narrative) is forward-looking positioning, not a measured capture channel yet. — [Bitwise NRR](https://bitwiseinvestments.com/newsroom/the-bitwise-near-etf-nrr-launches-as-first-spot-near-etp-in-the-us)

## What falsifiers would break the capture thesis?

### Takeaway
The capture thesis fails if gross fees stay with partners while NEAR's measurable wallet inflows stall or become discretionary/unattested, if major distribution exits, if buybacks stop or recirculate, or if Intents volume proves non-durable (ZEC/privacy cycle, whale flight) — any one of these severs the user→token link even if headline volume remains large.

### Cited Findings
- **Thesis hinge (as framed by primary sources):** Intents fee switch → NEAR-denominated revenue share → discretionary buybacks as the token link. Governance explicitly retains discretion; mechanism is not guaranteed. — [Evolving NEAR Tokenomics](https://www.near.org/blog/evolving-near-tokenomics)
- **Measured hinge today:** captured revenue ≈ wallet sweeps (DefiLlama); ~15.8% of net issuance offset in the 30-day window at the top of the ladder; only ~4.5 points traceable to public collectors, ~11.3 points escrow-unattested. Buyback NEAR is held. — [DefiLlama adapter](https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/fees/near-intents/index.ts); issuance/tokenomics context: [Evolving NEAR Tokenomics](https://www.near.org/blog/evolving-near-tokenomics)
- **Partner exit sensitivity:** SwapKit exit would remove ~38% of 1Click volume (~21% of Intents); traceable revenue loss ~2%, but ceiling including unattributable escrow path up to ~43% of buyback-wallet inflows (higher if frontend escrow counted) — the uncertainty *is* the risk. — Volume/fee structure: [Fees](https://docs.near-intents.org/resources/fees); escrow: [Confidential Intents](https://docs.near-intents.org/integration/market-makers/confidential-intents)
- **Capture rate already soft on the margin:** Nansen trailing 30-day capture 28.4% vs prior 30.5% even as lifetime rose to 16.4% — lifetime improvement can coexist with near-term softening. — [Nansen NEAR Q3 2026](https://nansen.ai/post/near-q3-2026-report)
- **Buyback tracker:** ~$8.01M recorded since 2026-02-23; recent 30d ~$1.82M (through ~Nov 10) — program is live but small vs ~$4.8B mcap. — [tokenbuybacks / DefiLlama holders revenue framing](https://www.tokenbuybacks.app/token/near/); methodology origin: [DefiLlama adapter](https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/fees/near-intents/index.ts)
- **Product concentration risk:** Intents dominates NEAR's fee surface vs base-layer and other DeFi; base-layer activity far below 2024 peaks (Nansen: ~739k tx/day, ~79k daily signers in Q3). If Intents fee capture fails, there is little else. — [Nansen Q3 2026](https://nansen.ai/post/near-q3-2026-report)

### Inferences — falsifiers (what would break it)

1. **Attestation falsifier:** Per-stream disclosure shows escrow unshields are *not* recurring fee revenue (one-offs, discretionary top-ups, or non-fee transfers) → collapse capture toward the ~4.5% of issuance public-collector floor.
2. **Partner falsifier:** SwapKit (or Ledger within it) leaves or re-routes to THORChain/CEX; volume narrative and any hidden escrow-linked economics gap down together.
3. **Take-rate falsifier:** Share of volume with buyback fee entries rolls over and falls; or new Commercial Agreements further zero out NEAR's explicit line while partners keep 100+ bp.
4. **Policy falsifier:** Governance pauses buybacks, spends wallet NEAR on opex, or recycles holdings into liquid supply — breaking the "holders revenue" interpretation DefiLlama uses since 2026-02-23.
5. **Forwarding falsifier:** Confidential Infrastructure Fee is retained by Intents Technology "for its own account" and **stops** being swept to NEAR revenue wallets — contractually allowed today.
6. **Volume-composition falsifier:** ZEC/privacy-led volume mean-reverts; whale cohort leaves; remaining flow is low-fee stablecoin routes (1 bp world) → revenue falls faster than headline "Intents still works."
7. **Competition falsifier:** Peers match confidentiality + wallet distribution at lower all-in user cost; Intents keeps volume only by giving away capture (race to the supply side).
8. **Demand falsifier (token side):** Intents remains a net NEAR exit venue and buybacks stay << issuance even after HSP-style cuts → fee capture never becomes economically material to float.

### Gaps
- No public commitment on minimum buyback duration or burn.
- No independent auditor report on confidential fee → wallet mapping.
- Exchange-label coverage for broader NEAR flow tests remains too thin to confirm whether buybacks absorb issuance-driven sell pressure (orthogonal but often bundled into "capture" narratives).

---

## Research judgment (for the report writer)

**Structural answer:** Today the **distribution layer owns most of the margin** between user and token. NEAR owns a minority but rising claim, exercised through (1) native frontend, (2) buyback-fee attachment on some public routes, (3) confidential infrastructure fees that *may* be forwarded, and (4) discretionary buybacks of held NEAR. That claim is **contractually soft** (Commercial Agreements, Schedule 1 discretion, governance discretion) and **partially unobservable** (confidential unshields).

**Sticky why:** wallets set price and own demand; docs invite custom deals; forcing a higher take on those deals trades directly against the volume story used to justify the venue multiple.

**To get more value to NEAR holders without killing volume:** win mix (near.com), keep lifting buyback attachment on *contestable* public flow, grow confidential volume **with** attestation that fees reach wallets, and improve buyback quality (lock/burn). Renegotiating SwapKit is high-upside and high-fragility.

**Honesty check:** Intents is a real fee engine and DefiLlama revenue reconciles to on-chain wallets — that part is solid. The leap from "Intents volume" to "NEAR token scarcity" still depends on partner terms, unattested escrow economics, and non-guaranteed buyback policy. Treat capture as a **range with policy risk**, not a closed loop.
