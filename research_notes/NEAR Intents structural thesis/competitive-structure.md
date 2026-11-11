# Competitive structure of native cross-chain venues — NEAR Intents vs THORChain vs Chainflip vs Maya

*As of November 2026. Industry-structure notes for prop research. Peer volumes/fees from repo metrics (`/tmp/nfs/data/metrics.json`) as of 2026-11-04 unless noted. No Akash/Cronos/Pi.*

Repo peer set (30d): NEAR Intents $4.0B vol / 15.3 bp fees / 55.7% share; THORChain $1.8B / 12.3 bp / 25.1%; Chainflip $0.85B / 31.5 bp / 11.8%; Maya $0.53B / 9.4 bp / 7.3%. 365d volumes: Intents $32.9B, THOR $13.1B, Chainflip $5.6B, Maya $1.3B. — [metrics.json peers](file:///tmp/nfs/data/metrics.json); [REPORT.md §1](file:///tmp/nfs/REPORT.md)

---

## How do settlement/security models differ (solver network + chain signatures vs L1 AMM vaults vs other)?

### Takeaway
Intents separates off-chain competitive fulfillment (solvers) from on-chain settlement on NEAR, with cross-chain signing via an 11-of-17 MPC/TEE network—but ingress still often depends on PoA bridges. THORChain, Maya, and Chainflip instead hold native assets in L1-controlled threshold vaults secured by bonded validators and slip-based or JIT AMMs, so security is continuous economic underwriting of vault TVL rather than per-trade solver inventory.

### Cited Findings
- NEAR Intents: users (or wallets) sign an outcome; solvers compete; settlement is enforced on NEAR via the Verifier contract (`intents.near`). Coordination can use an off-chain Message Bus; solvers can also index on-chain intents. — [NEAR blog: Unpacking NEAR Intents](https://www.near.org/blog/unpacking-near-intents-a-deep-dive); [HTW: What Are NEAR Intents](https://www.htw.tech/blog/what-is-near-and-near-intents)
- Chain Signatures MPC: required signing threshold 11 of 17 independent operators; key shares run in Intel TDX TEEs with on-chain attestation; operators include SVRN, Bitwise, Nansen, Greenfield, Everstake, Near One, Luganodes; Trail of Bits audits cited as public. Read MPC requires ≥3 of 5 whitelisted RPCs before threshold signing for foreign-chain deposits. — [NEAR: Chain Signatures Now Run Inside TEEs](https://www.near.org/blog/chain-signatures-tee); [SVRN on MPC network](https://svrn.net/news/svrn-led-build-out-mpc-network-near-intents); [NEAR docs: Chain Signatures](https://docs.near.org/chain-abstraction/chain-signatures)
- Intents trust map (independent research write-up, Feb 2026): most deposits still use PoA bridges (custodial during transit); OmniBridge (light clients / Wormhole / Chain Signatures) rolling out chain-by-chain; Verifier is upgradeable and pausable under security-council governance; 1Click adds a trusted swapping-agent surface. — [HTW: What Are NEAR Intents](https://www.htw.tech/blog/what-is-near-and-near-intents)
- THORChain: independent L1; native assets sit in Asgard vaults controlled by node TSS; Proof-of-Bond—validators bond RUNE that underwrites pool assets; theft attempt slashes bond (~1.5×); economic target ~2:1 bonded RUNE to non-RUNE vault liquidity (Incentive Pendulum). — [THORChain docs: Network Security and Governance](https://docs.thorchain.org/network-security-governance); [THORChain docs: RUNE](https://docs.thorchain.org/technical-documentation/understanding-thorchain/rune); [dev.thorchain.org: Incentive Pendulum](https://dev.thorchain.org/concepts/incentive-pendulum.html)
- THORChain operational reality (Nov 2026): after an Ethereum reorg / double-refund incident, multiple chains were halted; by 2026-11-04 BTC/ETH and others resumed on v3.21.1 while ATOM, BSC, SOL remained halted pending node upgrades—illustrating that vault L1s can pause trading when solvency/signing risk rises. — [CryptoTimes: THORChain resumes swaps](https://www.cryptotimes.io/2026/11/04/thorchain-resumes-bitcoin-and-ethereum-swaps-after-v3-21-1-update/); [THORWallet emergency cockpit](https://app.thorwallet.org/cockpit/emergency)
- Chainflip: application-specific Substrate State Chain; JIT AMM is virtual (account balances on State Chain, native assets in Vaults); Authority Set uses FROST threshold signatures—100 of 150 validators must sign vault moves; FLIP stake slashable for malicious behavior. — [Chainflip docs: Protocol Overview](https://docs.chainflip.io/protocol/protocol-overview); [Chainflip blog: 150 validators](https://chainflip.io/blog/chainflip-validator-network-decentralized-infrastructure); [Chainflip docs: How Swapping Works](https://docs.chainflip.io/protocol/how-swapping-works)
- Maya: friendly fork of THORChain (Tendermint + Cosmos-SDK + GG20 TSS); Asgard inbound vaults (e.g. 27-of-40) plus per-node outbound vaults; solvency checker can auto-halt a chain if >66% of nodes report insolvency; secondary vaults secured by 1.5× bond slash. Liquidity-node design deposits bonded CACAO into pools for capital efficiency vs pure idle bond. — [Maya docs: Security](https://docs.mayaprotocol.com/deep-dive/how-it-works/security); [Maya docs: Technology](https://docs.mayaprotocol.com/deep-dive/how-it-works/technology); [Maya blog: Why Maya is a friendly fork](https://www.mayaprotocol.com/blog-maya-academy/why-maya-is-a-friendly-fork-of-thorchain)
- DefiLlama TVL (context for vault vs inventory models, ~2026-11): Maya Protocol ~$5.2M; NEAR Intents verifier holdings cited across many chains with Near leg ~$93M in one DefiLlama snapshot and REPORT noting ~$229M held on the Intents contract in a node census window—different methodologies (locked-in-contract vs multi-chain vault). — [DefiLlama: Maya Protocol](https://defillama.com/protocol/maya-protocol); [DefiLlama: NEAR Intents](https://defillama.com/protocol/near-intents); [REPORT.md node census](file:///tmp/nfs/REPORT.md)

### Inferences
- Structural fork: **bonded vault AMMs** (THOR/Maya/Chainflip) make security a continuous function of staked token market cap vs vault TVL; **solver + MPC settlement** (Intents) makes per-swap liquidity an off-balance-sheet market-maker problem, while deposit/withdraw trust sits in bridges/MPC rather than in a single bond-to-TVL ratio.
- Intents can add chains/assets without growing an economic bond that must scale 2:1 with TVL—Read MPC / PoA onboarding is operationally lighter than Bifrost chain clients + vault churn—but that flexibility is exactly where trust assumptions concentrate (PoA, upgradeable verifier, 1Click agent).
- Peer halts (THORChain Nov 2026) show vault models fail closed on chain risk; Intents-style systems can fail open on bridge/agent assumptions unless OmniBridge-style paths fully replace PoA.

### Gaps
- No single audited public table comparing residual risk of PoA-bridged Intents deposits vs OmniBridge-only paths by chain as of Nov 2026.
- Active bonded RUNE / FLIP / CACAO vs vault TVL ratios at the same snapshot date were not pulled into the repo metrics; capital-efficiency comparisons below use fees/volume and DefiLlama TVL proxies rather than live bond ratios.
- Solver concentration / inventory sourcing (CEX vs on-chain) for Intents is not disclosed in primary docs with hard shares.

---

## Where does each venue's fee go (LPs, node operators, token buybacks, protocol)?

### Takeaway
Intents’ on-chain protocol take is near-zero (1 pip); almost all user-visible fee is distribution/1Click/partner take, with NEAR capturing a minority via buyback wallets. Vault AMMs send liquidity fees primarily to LPs and bonded nodes (THOR/Maya pendulum; Chainflip LP fee + FLIP buy/burn), so token value accrual is tighter to swap economics—but Intents still prices a higher blended fee on larger volume.

### Cited Findings
- **Peer blended fee (repo, 30d to 2026-11-04):** Intents 15.3 bp on $4.0B → $6.12M fees; THORChain 12.3 bp → $2.22M; Chainflip 31.5 bp → $2.66M; Maya 9.4 bp → $0.5M. — [metrics.json peers](file:///tmp/nfs/data/metrics.json); [REPORT.md §1](file:///tmp/nfs/REPORT.md)
- **NEAR Intents fee stack (docs):** protocol fee 0.0001% (1 pip) to `fee_collector` on `intents.near`; near-intents.org frontend 0.2% to `fefundsadmin.sputnik-dao.near`; 1Click defaults 20 bp (1 bp stables/same-asset) with API key, or +25 bp without; partners set `appFees` with default 50/50 rev-share and 20 bp 1Click floor. Solvers keep 100% of their quote spread (typical 10–100+ bp). — [NEAR Intents docs: Fees](https://docs.near-intents.org/resources/fees); [Become a Solver](https://intents.near.org/use-cases/solver)
- **NEAR capture vs gross (repo):** gross Intents fees $6.12M / 30d; captured holders revenue / revenue wallets $1.99M (≈4.98 bp captured vs 15.3 bp gross); capture share 32.5%; partners kept ≥1.81× NEAR’s captured revenue; explicit buyback fee inside 1Click rose 1.83 → 4.08 bp across three 30-day blocks as vol with buyback fee rose 23.6% → 43.0%. Buybacks purchase NEAR (held, not burned)—buyback wallet 2.187M NEAR. — [metrics.json](file:///tmp/nfs/data/metrics.json); [REPORT.md §2](file:///tmp/nfs/REPORT.md); [DefiLlama methodology: NEAR Intents](https://defillama.com/protocol/near-intents)
- **Intents fee concentration in NEAR L1 fee surface:** Intents was 87% of DefiLlama-attributed fees on NEAR over 30d (`fees_near.json` top_share_30d_pct). — [fees_near.json](file:///tmp/nfs/data/raw/prop/fees_near.json); [REPORT.md § prop](file:///tmp/nfs/REPORT.md)
- **THORChain:** swaps pay fixed network fee + dynamic slip-based liquidity fee; Incentive Pendulum splits block rewards + liquidity fees between node operators (bond) and LPs; system income also funds outbound gas, reserve, optional burn/dev/TCY/POL dials; affiliates can take up to 1,000 bp user-side and optionally REVSHARE of liquidity fees from reserve (capped 50%). — [THORChain economic model](https://dev.thorchain.org/concepts/economic-model.html); [LP docs](https://docs.thorchain.org/technical-documentation/understanding-thorchain/roles/liquidity-providers); [Affiliate fee guide](https://dev.thorchain.org/affiliate-guide/affiliate-fee-guide.html)
- **Chainflip:** LP fee 0.10–0.15% per pool to LPs; network fee 0.10% (0.01% internal stables, $0.5 min) buys FLIP from USDC-FLIP pool then burns; optional boost 0.05–0.3% to boost-pool LPs; validators earn emissions/stake rewards, not the network fee (fees burned, value socialized via supply). — [Chainflip: How Swapping Works](https://docs.chainflip.io/protocol/how-swapping-works); [Cryptoeconomics Series P4](https://chainflip.io/blog/cryptoecomonics-series-4)
- **Maya:** slip-based swap fees like THOR; network/outbound fees to protocol reserve; **10% of protocol fees to $MAYA holders** (paid in CACAO); ILP reserve funded with 10% of CACAO supply / fee inflows; dual-token model separates CACAO (bond/settlement) from MAYA (cash-flow claim). DefiLlama: Revenue = 10% of swap fees to MAYA holders. — [Maya comparative analysis](https://www.mayaprotocol.com/blog-maya-academy/thorchain-and-maya-a-comparative-analysis); [Maya FAQs](https://docs.mayaprotocol.com/deep-dive/faq); [DefiLlama: Maya Protocol](https://defillama.com/protocol/maya-protocol)

### Inferences
- Intents is a **distribution-fee protocol** more than an **AMM-fee protocol**: solvers + partners absorb most of the 15.3 bp blend; NEAR’s equity story is the rising buyback/app-fee share of that blend, not LP yield.
- Chainflip’s high 31.5 bp blend with smaller volume is consistent with stacking LP + network (buy/burn) fees on thinner JIT liquidity; Maya’s low 9.4 bp matches a smaller, ZEC-heavy vault book competing on price.
- Comparing “token revenue” across venues without adjusting for LP share vs protocol share mis-ranks the industry: DefiLlama “revenue” for Intents ≈ NEAR wallet capture; for Maya ≈ 10% fee claim; for Chainflip ≈ burn (holders revenue via supply); for THOR ≈ system income after LP/node split—not like-for-like.

### Gaps
- Exact slip-fee vs outbound-fee split for THOR/Maya in the same 30d window as metrics.json was not in the repo.
- Solver spread retained (not in DefiLlama “fees”) is opaque; true total user cost on Intents can exceed listed partner+protocol fees when quote margins are wide.
- Whether near-intents.org 0.2% and 1Click floors accrue entirely to the same buyback path as “holders revenue” is only partially reconciled in REPORT (escrow unshield share of buybacks rising to ~59%).

---

## Why might Intents win distribution (wallets, 1Click API, Brave, near.com) even if peers have different security assumptions?

### Takeaway
Intents won share by becoming the default embeddable any-to-any execution API for wallets and aggregators—not by winning a trust bake-off. 1Click collapses solver discovery into REST; asset/chain breadth (~39 chains / ~229 assets) plus ZEC/Solana/TON/XRP-class coverage lets a single integration replace multiple vault venues; partners monetize via `appFees`, so wallets prefer the rail that pays and quotes across the widest set.

### Cited Findings
- Share trajectory (repo): Intents 55.7% of peer-set 30d volume and 62.1% of 365d; January 2025 monthly volume ~$0.01B → $4.0B / 30d by late 2026. — [REPORT.md §1](file:///tmp/nfs/REPORT.md); [metrics.json](file:///tmp/nfs/data/metrics.json)
- **1Click API:** REST quote → unique deposit address → status tracking; automates solver discovery; fee collection via one parameter; explicitly positioned for distribution channels. — [1Click Swap API docs](https://docs.near-intents.org/integration/distribution-channels/1click-api/about-1click-api); [Fees docs](https://docs.near-intents.org/resources/fees)
- **Brave Wallet (v1.88):** NEAR Intents as first swap provider tying together Brave’s supported chains including BTC, SOL, ZEC (transparent/shielded), Cardano, and EVM; cites 35 chains / $14B+ all-time volume at announcement. — [Brave blog: Brave Wallet now supports NEAR Intents](https://brave.com/blog/near-intents/)
- **Integrator leaderboard (nearstats, live):** Trust Wallet via SwapKit ~11.7% of settled vol; Ledger Live via SwapKit ~10.3%; LI.FI ~8.4%; Rango ~6.7%; ZODL ~5.5%; THORSwap via SwapKit ~3.5%; plus Tangem, CoW, NEAR Mobile, Bitget, etc.—wallet/aggregator heavy, not destination-app heavy. — [nearstats.org/integrators](https://nearstats.org/integrators)
- Repo channel economics: SwapKit routes 38.2% of 1Click volume; volume-channel HHI 0.087 (diversified); Trust direct buyback 20 bp on 2.4% vol share; Trust via SwapKit partner fee 70 bp on 6.4% vol share—illustrates partner-first monetization. — [metrics.json](file:///tmp/nfs/data/metrics.json); [REPORT.md](file:///tmp/nfs/REPORT.md)
- Asset coverage: Intents ~229 usable assets / 39 chains (nearstats 2026-11-11); docs list Aleo, Aptos, Cardano, NEAR, Solana, Stellar, Sui, TON, Tron, XRP, Starknet, plus EVM set. THORChain lists ~14 L1s (BTC, ETH, BSC, XRP, SOL, TRX, ZEC, DOGE, BCH, LTC, AVAX, BASE, ATOM, RUNE) with pool-listed stables/tokens—not hundreds of long-tail assets. Chainflip: ~8 chains / ~20 listed assets (BTC, ETH, SOL, DOT/Assethub, Arb, Tron, BSC + stables/wBTC/cbBTC/FLIP). Maya: BTC, ETH, Arb, Dash, Kujira, THOR, Radix, ZEC + listed ERC-20/ARB pools; TVL skewed to ZEC. — [nearstats assets](https://nearstats.org/assets); [NEAR Intents chain support](https://docs.near-intents.org/resources/chain-support); [THORChain docs: supported chains](https://docs.thorchain.org/what-is-thorchain-and-rune); [Chainflip chains & assets](https://docs.chainflip.io/protocol/supported-chains-assets/chains-assets); [Maya getting started](https://docs.mayaprotocol.com/introduction/readme/getting-started)
- NEAR Protocol distribution narrative lists Ledger, SwapKit, Zodl, Trust, Brave, Infinex, ThorSwap, native NEAR wallets as volume unlocks after product-market fit. — [NEAR Protocol LinkedIn post on $20B volume](https://www.linkedin.com/posts/near-protocol-project_all-time-volume-on-near-intents-just-crossed-activity-7468037476306309121-RAu9)
- HTW (Feb 2026): referral breakdown dominated by SwapKit/Ledger/Trust/Electric Coin Co embeds—“default execution infrastructure rather than a destination app.” — [HTW: What Are NEAR Intents](https://www.htw.tech/blog/what-is-near-and-near-intents)

### Inferences
- Wallets optimize for **one integration, maximum pairs, partner fee**, not for bond-to-TVL security theater. Intents matches that objective function; vault AMMs require chain-client work per L1 and pool depth per pair.
- Security differentiation is weakly priced in retail wallet UX: Brave marketed any-to-any including ZEC, not MPC vs TSS. Users inherit PoA/1Click assumptions silently.
- SwapKit as a multi-venue router means Intents share can rise inside the same wallet shell that also offers THOR/Chainflip/Maya—share is quote-win rate × coverage, not exclusive distribution (except where a wallet hard-codes Intents, e.g. Brave’s framing).

### Gaps
- near.com / NEAR.com swap widget volume share is visible only as small SolSwap-via-NEAR.com rows on nearstats (~0.3%); no clean public split of “owned” vs partner distribution for Nov 2026.
- No public A/B of quote win-rate Intents vs THOR inside SwapKit at matched pairs (BTC↔ETH etc.) for the metrics window—only aggregate share.
- Brave’s incremental volume post-integration is not isolated in repo metrics.

---

## What is the credible threat from peers or from CEXes / RFQ networks?

### Takeaway
Peers threaten where vault security and native BTC/ETH depth still win large ticket flow or where aggregators reprice (THOR REVSHARE/SwapKit subsidies, Chainflip broker SDK). The larger structural threat is **order-flow capture by wallet/RFQ/CEX rails that treat Intents as one optional filler**—UniswapX/Across-style intents, LI.FI routing, and CEX inventory—because Intents’ moat is distribution embed, not exclusive liquidity.

### Cited Findings
- **Peer competitive levers:** THORChain ADR-029 REVSHARE pays affiliates a share of liquidity fees from reserve (up to 50%) to subsidize quotes without raising user fee; SwapKit exclusive REVSHARE program cited with early ~2× volume on discounted flow and THOR still only “single-digit %” of SwapKit trades—explicit fight for the same wallet pipe Intents dominates. — [THORChain ADR-029](https://blog.thorchain.org/adr-029-affiliate-revenue-share); [THORChain blog: SwapKit Rev-Share week one](https://blog.thorchain.ai/swapkit-rev-share-week-one-early-data-looks-promising-v321-and-monero-next)
- SwapKit monetization lists NEAR Intents alongside THOR, Maya, Chainflip, Garden, Mayan, 1inch, Jupiter as providers—wallets can fee across all. — [SwapKit Monetization](https://www.swapkit.dev/monetization/)
- Chainflip distribution: Trust Wallet guides, Xverse (via SwapKit), OrangeRock/Bitcoin.com, broker API; thinner asset set but native vault marketing aimed at BTC-native users. — [Chainflip Trust Wallet guide](https://chainflip.io/blog/chainflip-trust-wallet-swap-guide-2026); [Chainflip changelog](https://chainflip.io/changelog)
- Maya remains niche on TVL (~$5M) and share (7.3% of peer 30d vol) despite lower fee bp—credible as ZEC/secondary venue, weak as universal wallet default. — [DefiLlama Maya](https://defillama.com/protocol/maya-protocol); [metrics.json](file:///tmp/nfs/data/metrics.json)
- **RFQ / intent peers:** Cross-chain RFQ (Across, UniswapX) gives firm quotes from solver inventory with different settlement rails (Across: UMA optimistic oracle; UniswapX cross-chain often delegates to Across; ERC-7683 standardizes order format, not trust). — [Chainscore: RFQ vs AMM](https://chainscorelabs.com/differences/chain-abstraction-and-intent-routing/cross-chain-routing-strategies/cross-chain-rfq-systems-vs-cross-chain-amm-routing-key-differences); [QuillAudits: ERC-7683 solver risks](https://www.quillaudits.com/blog/web3-security/ERC-7683-Intent-Based-Bridges:-Solver-Security-Risks); [Anoma blog: UniswapX](https://anoma.net/blog/uniswapx)
- LI.FI appears both as Intents integrator (~8.4% nearstats) and as a meta-router that can send flow to bridges/intents/AMMs fill-by-fill—aggregator threat is reallocation, not a new L1. — [nearstats integrators](https://nearstats.org/integrators); [QuillAudits LI.FI note](https://www.quillaudits.com/blog/web3-security/ERC-7683-Intent-Based-Bridges:-Solver-Security-Risks)
- CoW appears as Intents integrator (~1.2%); CoW’s own batch-auction solvers are a same-chain RFQ paradigm that can internalize flow before it reaches cross-chain venues. — [Olympix: aggregators / CowSwap](https://olympix.security/blog/defi-aggregators-explained); [nearstats](https://nearstats.org/integrators)
- Repo stress signals (not bull/bear narrative—facts): Intents 30d vol $4.0B below prior 30d $4.56B; partners keep more than NEAR; 1Click share of llama week fell 86.2% → 60.8% around a Sep threshold; peer mcap/rev multiples much tighter for THOR (16×) and Chainflip (5×) than NEAR (~217× annualised 30d in REPORT prop). — [metrics.json](file:///tmp/nfs/data/metrics.json); [REPORT.md risks](file:///tmp/nfs/REPORT.md)
- CEX threat (structural): Intents solvers may source inventory from CEXes; if CEXes or prime brokers productize the same RFQ to wallets (or wallets route to CEX APIs), the venue earns only thin protocol pip. No primary source quantified CEX share of Intents fills in this research pass.

### Inferences
- **Most credible peer threat:** SwapKit/Ledger/Trust quote competition with THOR REVSHARE subsidies on overlapping pairs (BTC/ETH/stables)—not Maya scale-up.
- **Most credible non-peer threat:** meta-aggregators and standardized intent orders (ERC-7683) making settlement rail interchangeable; Intents becomes a backend among backends.
- **What could reverse Intents share (mechanism, not forecast):** (1) exclusive wallet deals flipping default provider; (2) OmniBridge/PoA incident destroying trust in deposit path; (3) sustained quote losses on high-volume pairs after peer fee subsidies; (4) solvers vertically integrating with their own frontends and bypassing NEAR settlement; (5) CEX/RFQ APIs matching any-to-any UX without NEAR.

### Gaps
- No public fill-source breakdown (CEX vs DEX vs inventory) for Intents solvers.
- Across/UniswapX cross-chain volume overlapping the same peer-set definition is not in metrics.json—peer set is native vault/intents venues only.
- Magnitude of THOR REVSHARE’s effect on Intents win-rate inside SwapKit after the first week of data is not yet in a long window study.

---

## Which metrics are the right scoreboard (volume share vs captured revenue vs capital efficiency)?

### Takeaway
Volume share measures distribution win; **captured revenue (and capture rate vs gross fees)** measures token take; **fees per unit capital / bond** measures vault-venue efficiency. Using only volume overstates Intents’ economic control because partners+solvers keep most of the spread; using only token mcap/revenue ignores that vault peers force capital lockup Intents externalizes to solvers.

### Cited Findings
- **Volume share (repo):** Intents 55.7% 30d / 62.1% 365d of {Intents, THOR, Chainflip, Maya}. Net share excluding some routes: 38.6% (`intents_share_peerset_30d_net_pct`). — [metrics.json](file:///tmp/nfs/data/metrics.json)
- **Gross fees vs captured:** Intents fees $6.12M vs revenue/holdersrev $1.99M (30d); capture_share_30d_pct 32.5%; take_gross_bp 15.3 vs take_captured_bp 4.98. — [metrics.json](file:///tmp/nfs/data/metrics.json); [REPORT.md](file:///tmp/nfs/REPORT.md)
- **Partner take as contra:** partners_kept_vs_near_rev ≥1.81×; SwapKit partner fees in explorer samples large vs buyback fees; buyback_fee_unreferred_share 45.8% of buyback-fee channel mix. — [metrics.json](file:///tmp/nfs/data/metrics.json)
- **Capital / efficiency proxies:** REPORT node census—Intents contract ~$229M held, ~$80M deposits and ~$75M withdrawals per day (high turnover vs idle AMM TVL). Maya TVL ~$5.2M on $0.53B 30d vol implies extreme volume/TVL if Midgard volume is comparable—vault thinness vs flow. Chainflip docs emphasize staked FLIP must scale with vault liquidity; THOR targets 2:1 bond:liquidity. — [REPORT.md](file:///tmp/nfs/REPORT.md); [DefiLlama Maya](https://defillama.com/protocol/maya-protocol); [THORChain security docs](https://docs.thorchain.org/network-security-governance); [Chainflip cryptoeconomics P4](https://chainflip.io/blog/cryptoecomonics-series-4)
- **Valuation scoreboard caution:** REPORT prop—NEAR ~217× annualised 30d DefiLlama revenue vs THOR ~16× and Chainflip ~5×; metrics mcap_to_rev_30d_annualized_x 199 and mcap_to_rev_365d_x 510—volume leadership ≠ cheap revenue multiple. — [REPORT.md](file:///tmp/nfs/REPORT.md); [metrics.json](file:///tmp/nfs/data/metrics.json)
- **DefiLlama definitions differ by venue** (fees vs revenue vs holders revenue)—Intents revenue = NEAR wallet sweeps/buybacks; Maya revenue = 10% to MAYA; Chainflip network fee → burn. — [DefiLlama NEAR Intents](https://defillama.com/protocol/near-intents); [DefiLlama Maya](https://defillama.com/protocol/maya-protocol); [Chainflip fee table](https://docs.chainflip.io/protocol/how-swapping-works)

### Inferences
- Right primary scoreboard for **industry structure / distribution:** peer volume share + integrator HHI + quote coverage (pairs/chains).
- Right primary scoreboard for **NEAR token claim:** captured bp, capture_share, buyback/escrow attestation quality—not gross DefiLlama “fees.”
- Right primary scoreboard for **vault peers’ sustainability:** effective security bond / vault TVL, halt frequency, and LP real yield after IL—not headline volume.
- Right primary scoreboard for **capital efficiency of the Intents design:** solver inventory turnover and volume per dollar of verifier float (deposits/withdrawals vs holdings), acknowledging float is bridge inventory not LP capital.
- A composite that misleads: ranking venues by gross fee bp alone (Chainflip “wins” on take rate while losing share).

### Gaps
- No standardized “volume per $ bonded” series in the repo across all four venues on one as-of date.
- Solver P&L / inventory capital for Intents is private—true system-wide capital efficiency is understated if only on-chain TVL is counted for Intents and overstated if CEX balance sheets are ignored.
- Net-of-refund / failed-swap adjusted volume not broken out in metrics.json peers.
