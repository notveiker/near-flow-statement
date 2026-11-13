# NEAR capital-markets stack and float dynamics

*As of 2026-11-11. Prop note: connect regulated product structure to token supply pressure vs Intents fee capture — not a product brochure. Honest about small AUM and recent outflows.*

## What products exist (US/EU/other), who sponsors them, fees, staking policy?

### Takeaway
The regulated NEAR stack is small and Bitwise-dominated: one US spot ETF (NRR) that stakes, one tiny US OTC trust (GSNR) that does not stake, and four European/Nordic ETPs of which three stake and one (Valour) is a synthetic tracker. Combined tracked AUM is about $123M — roughly 2.5% of NEAR market cap — not a structural float vacuum.

### Cited Findings
- Bitwise NEAR ETF (NRR) launched as the first US spot NEAR ETP, trading NYSE Arca from 29 Sep 2026, management fee 0.75%; Bitwise intends to stake the Fund’s NEAR in-house — [Bitwise launch release](https://bitwiseinvestments.com/newsroom/the-bitwise-near-etf-nrr-launches-as-first-spot-near-etp-in-the-us); corroborated by [third_party_facts.json](../../data/raw/web/third_party_facts.json) (`etf_launch`, `etf_date`, `etf_fee`, `etf_staking`).
- NRR prospectus economics: unitary Sponsor Fee 0.75% p.a. of NEAR holdings (paid in NEAR monthly); secondary objective is staking; Staking Expenses equal **33%** of additional NEAR generated; Trust retains ~**67%** of staking rewards — [424B3 / Public supplemental prospectus summary](https://ebs.publicnow.com/view/478DFB20F19227709A142ECC607A6D2012D0BAE3); [StockTitan 424B3 summary](https://www.stocktitan.net/sec-filings/NRR/424b3-bitwise-near-etf-prospectus-filed-pursuant-to-rule-424-b-3-1bf9972638aa.html).
- As of ~2 Oct 2026, Bitwise’s US fund page showed ~4.90% gross network rate, ~3.28% after reward split, **~98% of assets staked**; ETF.net arithmetic net of fee ≈ 2.46% (not a fund yield promise). Custodian/staking stack includes Coinbase Custody; sponsor may favor affiliate Attestant as staking agent. Creation/redemption in 10,000-share baskets for cash or token; prospectus cites ~48-hour unlock under ordinary conditions and possible redemption delay/pause while locked — [ETF.net, 5 Oct 2026](https://etf.net/news/bitwise-s-near-fund-charges-more-and-keeps-less-of-the-rewards-than-its-other-us-staking-etfs-2026-10-05).
- NRR fee is the highest among Bitwise’s US staking single-asset funds (BSOL 0.20%, BHYP/BAVA 0.34%) and keeps the smallest reward share (67% vs 94%/75%/88%) — [ETF.net](https://etf.net/news/bitwise-s-near-fund-charges-more-and-keeps-less-of-the-rewards-than-its-other-us-staking-etfs-2026-10-05).
- Bitwise Europe NEAR Staking ETP (ISIN DE000A4A5GV2; tickers NEAR/NEAS on Xetra): BaFin prospectus, physical 100% backed, TER **0.85%** p.a., inception 1 Jul 2025; issuer retains **33%** of staking rewards (67% to investors); target benchmark stake share 90%; AUM **$49.27M** and **13,219,481 NEAR** in custody as of 11 Nov 2026; staking provider Attestant, custodian BitGo Europe — [Bitwise Europe product page](https://bitwiseinvestments.eu/products/bitwise-near-staking-etp/).
- Grayscale Near Trust (GSNR): OTC, TER **2.50%**, public inception 29 Sep 2025, AUM **$2.21M**, 441,100 shares, 1.41018924 NEAR/share as of 10 Nov 2026; private placement closed; market price can diverge from NAV — [Grayscale product page](https://www.grayscale.com/funds/grayscale-near-trust).
- GSNR Trust Agreement allows staking only if a “Staking Condition” is satisfied; as of the June 2026 S-1/A, the condition had **not** been met and the Trust was **prohibited from staking** — [SEC S-1/A](https://www.sec.gov/Archives/edgar/data/2025000/000119312526269337/gsnr_s-1_amendment_1.htm); ETF.net restates the Jan 2026 filing prohibition — [ETF.net](https://etf.net/news/bitwise-s-near-fund-charges-more-and-keeps-less-of-the-rewards-than-its-other-us-staking-etfs-2026-10-05). Shareholders later approved staking-related Trust Agreement amendments (OTC Markets notice), but that is authorization conditional on the Staking Condition, not evidence staking is live — [OTC Markets notice](https://www.otcmarkets.com/stock/GSNR/news/Grayscale-Investments-Enters-intothe-Third-Amended-and-Restated-Trust-Agreement-of-Grayscale-Near-Trust-NEAR?id=512229).
- 21Shares NEAR Protocol Staking ETP (ISIN CH1162108893): physical, staking rewards reinvested, fee **2.50%**, AUM ~**$8.7–9.0M**, inception 25 Nov 2024; from 25 Aug 2026 staking commission on rewards “up to 35%” for this ISIN — [21Shares product page](https://www.21shares.com/en-eu/product/near); [SIX staking-cut notice PDF](https://cdn.21shares.com/uploads/current-documents/products/notices/SIXOfficialNotice_StakingCutIncrease.pdf).
- Virtune Staked NEAR ETP (VIRNEAR, ISIN SE0025837735): 100% physically backed, fee **1.49%**, AUM ~**$1.69M** (as of 6 Nov 2026), inception 18 Aug 2025, Nasdaq Stockholm — [Virtune product page](https://www.virtune.com/en/product/near).
- Valour Near SEK (ISIN CH1213604577): open-ended SEK tracker certificate that **synthetically** tracks NEAR USD price less **1.9%** management fee and FX; issuer hedges by buying corresponding NEAR 1:1 — product is not a staking ETP — [Valour KID](https://api.kneip.com/v1/documentdata/permalinks/PRP_CH1213604577_en_SE.pdf).
- Aggregator snapshot (11 Nov 2026 ~04:15 UTC): six tracked NEAR ETFs/ETPs, combined AUM **$122.78M**, 7-day net flows **−$591K**, Bitwise **85.3%** of known AUM — [ETF Llama NEAR list](https://etfllama.com/crypto/near-protocol).

| Product | Sponsor | Venue / form | Fee | Staking | AUM (≈11 Nov 2026) |
|---|---|---|---|---|---|
| NRR | Bitwise | NYSE Arca spot ETF | 0.75% + 33% of rewards | Yes (~98% reported early Oct) | ~$55.9M |
| Bitwise NEAR Staking ETP | Bitwise Europe | Xetra ETP (DE) | 0.85% + 33% of rewards | Yes (target 90% in index) | ~$49.3M |
| 21Shares NEAR Staking ETP | 21Shares AG | Euronext etc. | 2.50% + ≤35% of rewards | Yes | ~$8.7M |
| Valour Near SEK | Valour | SEK tracker cert. | 1.90% | No (synthetic/hedged) | ~$5.5M |
| GSNR | Grayscale | OTC trust | 2.50% | No (condition unmet) | ~$2.2M |
| VIRNEAR | Virtune | Nasdaq Stockholm | 1.49% | Yes | ~$1.6–1.7M |

### Inferences
- For float analysis, treat **physical staking products** (NRR + Bitwise EU + 21Shares + Virtune) as the relevant “locked by wrappers” set; Valour hedges with NEAR but does not stake; GSNR holds unstaked NEAR in custody at tiny size.
- Bitwise’s US+EU franchise (~$105M, ~85% of tracked AUM) is the only product pair large enough to move exchange float in a meaningful way; the rest is noise relative to daily spot liquidity.
- NRR’s 0.75% fee without a published waiver, plus a 33% staking cut, makes it a relatively expensive “staked spot” wrapper versus Bitwise’s own SOL product — relevant if comparing wrappers as capital sinks, not as alpha vehicles.

### Gaps
- No primary issuer holdings file was retrieved for NRR on 11 Nov 2026 beyond secondary aggregators (~15.7M NEAR earlier in Nov); exact staked vs unstaked split for NRR after mid-October is not confirmed from Bitwise’s site in this pass.
- Whether GSNR’s Staking Condition has been satisfied after the Trust Agreement amendment is not confirmed on the live product page (still no staking disclosure as active).
- VanEck and other large US/EU issuers: no NEAR single-asset ETP found in this pass (VanEck appears in Celestia, not NEAR).

---

## What is known about NRR AUM, flows, and share of NEAR mcap?

### Takeaway
NRR is a launch-then-fade product: cumulative net inflow still ~$80.5M, but net assets have fallen to ~$56M (~1.2% of NEAR mcap) after multi-million-dollar late-October/early-November outflows and a sharp NEAR price drawdown. At current size it is a visible ticker, not a dominant holder.

### Cited Findings
- Prop snapshot from SoSoValue US NEAR spot dashboard, asof 2026-11-11T06:30Z: ticker NRR, sponsor Bitwise, NYSE, fee 0.75%, market price $18.54, NEAR $3.56, **total net assets $55.86M**, **cumulative net inflow $80.45M**, daily net inflow $0, total value traded $3.15M, **share of NEAR mcap 1.2%** — [`etf_nrr.json`](../../data/raw/prop/etf_nrr.json); source URL [SoSoValue US NEAR spot](https://sosovalue.com/assets/etf/us-near-spot).
- Recent daily points in the same prop file: 21 Oct net assets **$91.38M** (value traded $15.86M); 27 Oct net inflow **−$4.84M**; 3 Nov **−$3.6M**; 5 Nov **−$0.774M**; 10 Nov net assets **$55.86M**, inflow $0 — [`etf_nrr.json`](../../data/raw/prop/etf_nrr.json).
- Independent tracker table (NEAR Catalog / SoSoValue): first day +$35.99M; week-one cumulative ~$50–58M; mid-October cumulative peak ~$79–83M range across sources; net assets $55.86M as of 10 Nov 2026 — [NEAR Catalog NRR](https://nearcatalog.xyz/project/bitwise-near-etf-nrr); ChainCatcher/SoSoValue mid-Oct: cumulative inflow ~$83.05M and NAV ~$82.36M with NEAR ETF share of mcap 1.26% on 17 Oct — [ChainCatcher](https://www.chaincatcher.com/en/article/2296965).
- Outflow narrative: BSCN/SoSoValue report ~$773.8K outflow on 5 Nov with cumulative inflows still $80.45M and AUM ~$58M; gap between cumulative inflow and AUM attributed to redemptions **and** NEAR price decline from launch-period highs — [BSCN](https://bsc.news/news/bitwise-near-etf-nrr-outflows).
- ETF Explorer (quote as of 11 Nov): AUM ~$57.0M; holdings disclosure ~**15.69M NEAR** (100% weight, retrieved 7 Nov); estimated 1-week net flow **−$785K** — [ETF Explorer NRR](https://etfexplorer.com/etf/NRR).
- Repo REPORT exploratory note matches the prop read: ~$55.9M net assets, 1.2% of mcap, ~$80.5M cumulative inflow, assets ~$91M on 21 Oct then lower — [REPORT.md §8](../../REPORT.md).
- Context mcap/liquidity from the same research tree: market cap ~$4.76–4.82B; Binance spot about **$112M**/day — [nearblocks_stats.json](../../data/raw/prop/nearblocks_stats.json); [REPORT.md §4](../../REPORT.md).
- Full tracked stack AUM ~$122.78M on ETF Llama vs NEAR mcap ~$4.76B ⇒ stack ≈ **2.6%** of mcap (derived: 122.78 / 4762) — [ETF Llama](https://etfllama.com/crypto/near-protocol); [nearblocks_stats.json](../../data/raw/prop/nearblocks_stats.json).

### Inferences
- **Price mark-to-market, not just redemptions, explains most of the AUM drop** from ~$91M (21 Oct) to ~$56M (10 Nov): cumulative inflow only slipped from the low-$80Ms into the high-$70Ms/low-$80Ms while AUM fell ~39%. Treating AUM decline as pure “ETF rejection” overstates the flow story.
- NRR’s 1.2% of mcap is real but modest next to ~46.6% of circulating supply already staked on-chain (~582M of ~1.25B circulating; derived from validators + nearblocks) — [validators_summary.json](../../data/raw/prop/validators_summary.json); [nearblocks_stats.json](../../data/raw/prop/nearblocks_stats.json).
- At ~15.7M NEAR, NRR alone is ~**1.3% of circulating** and ~**2.7% of all staked NEAR** if nearly fully staked (derived). Bitwise EU’s 13.2M NEAR adds another ~1.1% of circulating. Bitwise combo ≈ **2.3% of circulating** — material for a single sponsor, still small vs liquid exchange inventory and vs native stake.

### Gaps
- SoSoValue is a dynamic dashboard; prop file is a point-in-time reading without a hashed static document (explicitly noted in `etf_nrr.json`).
- Complete day-by-day creation/redemption series from Bitwise itself was not obtained; secondary trackers disagree slightly on mid-October cumulative peaks ($79M vs $83M).
- Exchange-float (CEX hot-wallet) share of circulating is not pinned in local prop data; H1b exchange-label coverage in the thesis remains only 20%, so “ETF vs exchange float” cannot be tightly measured from labelled on-chain receivers alone — [REPORT.md §6](../../REPORT.md).

---

## How does in-house staking of ETF holdings change the supply story vs pure spot exposure?

### Takeaway
Staking inside the ETF converts wrapper demand into **bonded stake** rather than exchange-tradable inventory, but NEAR’s short unbonding (~4 epochs / ~1–2 days) means the lock is shallow compared with ETH/SOL-style multi-day/week exits. The structurally important effects are: (1) creations pull NEAR off venues into custody+stake; (2) the sponsor fee continuously sells a thin stream of NEAR; (3) staking rewards add NEAR to NAV while taking a 33% cut that never reaches shareholders.

### Cited Findings
- Pure spot objective vs staking secondary objective is explicit in the NRR prospectus: hold NEAR for price exposure; stake a portion with the custodian; NAV reflects NEAR entitled after Staking Expenses — [424B3 summary](https://ebs.publicnow.com/view/478DFB20F19227709A142ECC607A6D2012D0BAE3).
- Staking risks disclosed by Bitwise: loss of rewards, slashing, operational uncertainty; **staking could impair timely redemption** — [Bitwise launch release risk section](https://bitwiseinvestments.com/newsroom/the-bitwise-near-etf-nrr-launches-as-first-spot-near-etp-in-the-us).
- Protocol unbonding: reference staking pool waits **4 epochs** before withdrawal; mainnet epoch length 43,200 blocks, ideally ~7.2 hours ⇒ ~**28.8 hours** design time (variable with block production) — [NEAR staking docs](https://docs.near.org/protocol/tutorials/staking-tokens); [epoch docs](https://docs.near.org/protocol/network/epoch); pool constant `NUM_EPOCHS_TO_UNLOCK = 4` — [near/core-contracts staking-pool](https://github.com/near/core-contracts/blob/master/staking-pool/src/lib.rs). ETF.net paraphrases the prospectus as ~48 hours across 2–4 ~12-hour stretches — [ETF.net](https://etf.net/news/bitwise-s-near-fund-charges-more-and-keeps-less-of-the-rewards-than-its-other-us-staking-etfs-2026-10-05).
- European Bitwise product: rewards credited daily to crypto entitlement; investor can trade the ETP daily even though underlying is staked; private keys remain in cold storage while staking provider stakes from custody — [Bitwise Europe](https://bitwiseinvestments.eu/products/bitwise-near-staking-etp/).
- Sponsor Fee accrues daily and is payable **in NEAR** monthly — a mechanical sell/transfer of underlying out of the trust regardless of price path — [424B3](https://ebs.publicnow.com/view/478DFB20F19227709A142ECC607A6D2012D0BAE3). At $55.86M AUM, 0.75% ≈ **$0.42M/year** ≈ **~118K NEAR/year** at $3.56 (derived).
- Network stake context: ~582.1M NEAR staked, 351 validators — [validators_summary.json](../../data/raw/prop/validators_summary.json). Liquid staking TVL ~$196M (~9.3% of stake) across LiNEAR/Meta Pool/RHEA — [lst_vs_stake.json](../../data/raw/prop/lst_vs_stake.json). ETF-staked NEAR sits **alongside** LST and native stake as another institutional bonded sleeve, not instead of them.
- GSNR contrast: unstaked custody means creations (when open) remove NEAR from float **without** earning rewards or bonding; currently tiny and private placement closed — [Grayscale](https://www.grayscale.com/funds/grayscale-near-trust); [S-1/A](https://www.sec.gov/Archives/edgar/data/2025000/000119312526269337/gsnr_s-1_amendment_1.htm).

### Inferences
- **Vs pure spot ETF:** staking does **not** change the primary flow identity (creations buy NEAR; redemptions sell/return NEAR). It changes the **inventory state** of those coins: bonded vs CEX-available. For NEAR, the bonding delay is short enough that redemptions are an operational friction, not a multi-week supply dam.
- **Vs on-chain free float:** ETF-staked coins are economically similar to other delegated stake — they earn issuance-funded rewards and are temporarily non-transferable — but they are **owned by a redeemable wrapper**, so persistent outflows can recycle them back to exchanges within ~1–2 days. That makes ETF stake a **soft** float sink, not a hard lockup cohort.
- **Reward path vs Intents buybacks:** staking rewards are **issuance recirculation** to stakers (minus 33% wrapper cut). Intents revenue that reaches buyback wallets is **fee capture from activity**. Mixing “ETF staking yield” into an Intents revenue thesis double-counts nothing mechanically, but narratively confuses two different NEAR demand/supply channels.
- **Fee drag is real but small:** ~118K NEAR/year of sponsor fee from NRR alone is ~1.3 days of protocol net issuance at 88,295 NEAR/day (derived from REPORT’s daily mint figure) — [REPORT.md §2](../../REPORT.md). Not a thesis-level supply leak at current AUM; scales linearly if AUM grows.

### Gaps
- Exact share of NRR/EU holdings delegated to which validators (concentration / Nakamoto impact of ETF stake) was not mapped on-chain in this pass.
- Whether Authorized Participant creations are predominantly cash or in-kind affects whether flow hits spot order books immediately; prospectus allows both, but the mix is unpublished here.
- No clean public series for “ETF-custodied NEAR as % of exchange balances.”

---

## Is the ETF stack additive to the Intents thesis, a substitute narrative, or both?

### Takeaway
**Both, on different layers.** Mechanically, ETF creations are additive spot demand orthogonal to Intents fee capture. Narratively, Bitwise sold NRR explicitly as an Intents/AI-agent proxy — a substitute *story* that can crowd attention and multiple expansion without proving capture. At today’s AUM, the stack is too small to be a substitute *cash-flow* for the Intents revenue engine.

### Cited Findings
- Bitwise CIO framing at launch: NEAR Intents as settlement infrastructure for AI agents; Intents “processed $32B+ in volume, up from under $1B just a year ago”; NRR as “straightforward way to get exposure to that build-out” — [Bitwise launch release](https://bitwiseinvestments.com/newsroom/the-bitwise-near-etf-nrr-launches-as-first-spot-near-etp-in-the-us).
- On-chain/economic Intents facts from the research tree (not ETF facts): 30d Intents volume $4.0B; captured revenue $1.99M / ~$24.2M annualised; mcap ~199× that run-rate; Intents ~87% of NEAR fee surface — [REPORT.md](../../REPORT.md). Nansen Q3: Intents ~$10.4B quarterly volume; Confidential Intents TVL ~$160M — [third_party_facts.json](../../data/raw/web/third_party_facts.json) / [Nansen Q3 2026](https://nansen.ai/post/near-q3-2026-report).
- BSCN notes launch-period NEAR rally (~160% in the month before ETF) was “tied to activity on NEAR’s cross-chain Intents system,” then ETF flow momentum cooled as crypto markets weakened — [BSCN](https://bsc.news/news/bitwise-near-etf-nrr-outflows).
- Size comparison (derived): NRR AUM $56M ≈ **2.3 days** of annualised 30d Intents revenue ($24.2M/365 ≈ $66K/day is wrong scale — better: $56M is **2.3×** annualised revenue, or ~**28×** one month’s $1.99M). Full ETP stack $123M ≈ **5.1×** annualised captured revenue. Stack is large vs *today’s* fee take, tiny vs *mcap* and vs *spot turnover*.

### Inferences
- **Additive (capital structure):** New regulated sleeves can bring brokerage/RIA capital that never touches Binance. Creations still settle into NEAR purchases. That is additive to any fundamental bid from buybacks — same token, different buyer cohorts.
- **Substitute (narrative/multiple):** Launch marketing and secondary coverage treat NRR as the institutional expression of the Intents story. When flows are the headline, price can trade as an ETF-sentiment ticker even while Intents volume/take are the actual cash-flow drivers. That is narrative substitution risk, especially while the multiple is ~200× annualised fees.
- **Not a substitute for fee capture:** ETF AUM does not accrue Intents revenue to shareholders; shareholders get spot + (net) staking issuance. If Intents volume fell while ETF AUM held, the wrapper would still exist — proof the products are not the same thesis.
- **Honest sizing:** With NRR at 1.2% of mcap and the full stack ~2.5%, capital-markets structure is a **second-order** overlay on the Intents thesis today. It becomes first-order only if AUM scales by roughly an order of magnitude (toward mid/high single-digit % of mcap) *or* if creations become a large fraction of daily spot volume for a sustained period.

### Gaps
- No public attribution of what share of NRR holders are “new” vs rotated from GBTC-style crypto trust buyers or from European Bitwise NEAR ETP.
- No causal study of NEAR ETF flows → NEAR returns analogous to Bitcoin ETF literature yet (sample since 29 Sep 2026 is ~6 weeks).

---

## What would make ETF flows matter for price vs noise at current AUM?

### Takeaway
At ~$56M NRR AUM and ~$123M stack AUM against ~$112M/day Binance spot, **single-day flows in the low single millions are noise**; they mattered more as a **launch impulse** (first-day ~$36M ≈ one-third of a busy spot day) than as an ongoing tape. Flows become price-relevant if they are large vs spot volume, persistent across weeks, or large enough to change bonded float by a non-trivial share of liquid supply.

### Cited Findings
- Prop recent flows: −$4.84M (27 Oct), −$3.6M (3 Nov), −$0.77M (5 Nov), $0 (10 Nov) vs AUM $56M — [`etf_nrr.json`](../../data/raw/prop/etf_nrr.json). −$4.84M is ~**4.3%** of ~$112M Binance daily spot (derived) — [REPORT.md](../../REPORT.md).
- Launch day ~+$36M net inflow and multi-day early October positive prints; mid-October AUM near $80–91M before fade — [NEAR Catalog](https://nearcatalog.xyz/project/bitwise-near-etf-nrr); [`etf_nrr.json`](../../data/raw/prop/etf_nrr.json).
- ETF Llama: NEAR products −$591K net over past 7 days — [ETF Llama](https://etfllama.com/crypto/near-protocol).
- Method lessons from Bitcoin ETF literature (analogy, not NEAR estimate): absolute dollars mislead as AUM grows; normalize by AUM; individual flow shocks can reverse once future flows are controlled; persistence of flows creates the appearance of permanent impact — [SSRN Lim](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6592830); [CryptoQuant EFIS note](https://cryptoquant.com/insights/quicktake/690c6e6daa0ab11ed4f8f8ad-ETF-Flow-Impact-Score-EFIS-Quantifying-Institutional-Bitcoin-Demand); [cryptoetf.today explainer](https://cryptoetf.today/en/blog/how-to-read-bitcoin-etf-flows) (one-day flow mostly noise; weekly/monthly more informative; secondary-market volume ≠ primary creations).
- Secondary trading ≠ primary flow: NRR value traded $15.86M on 21 Oct and $3.15M on the prop asof day does **not** equal creations — [`etf_nrr.json`](../../data/raw/prop/etf_nrr.json); general ETF mechanics — [cryptoetf.today](https://cryptoetf.today/en/blog/how-to-read-bitcoin-etf-flows).

### Inferences
Practical thresholds for **this** market (heuristic, not fitted betas):
1. **Noise:** |daily net flow| ≲ **$1–2M** (~1–2% of Binance spot day, ~2–4% of NRR AUM) — matches most post-launch sessions including recent outflows’ smaller days.
2. **Tape-relevant day:** |flow| ≳ **$10–15M** (~10%+ of a $112M spot day) or ≳ **20% of NRR AUM** in a short window — launch week cleared this; late-October’s −$4.8M day is borderline-modest, not launch-scale.
3. **Structurally relevant:** sustained multi-week net creations that lift the **physical stack** from ~2.5% toward **high-single-digit % of mcap**, or that absorb a large share of **unstaked liquid supply**, while Intents fee take is still the cash-flow anchor. Until then, ETF flow headlines are mostly sentiment/liquidity microstructure.
4. **False signal to avoid:** AUM falling while cumulative inflow is flat-to-down slightly — that is mostly **mark-to-market**, as in Oct→Nov 2026. Price impact analysis should use **net creations**, not AUM charts.
5. **Interaction with staking:** because unbonding is ~1–2 days, outflow shocks can hit spot with only short delay — unlike a long-lock PoS ETF that might mute redemption sell pressure. That raises the chance that **outflows transmit**, but current outflow sizes are still small vs spot.

### Gaps
- No NEAR-specific Kyle’s lambda / flow-impact regression in the public sources reviewed; Bitcoin coefficients should not be pasted onto a $5B asset with one US ETF.
- Full CEX+DEX aggregated spot volume (not just Binance) would lower the flow/volume ratio further; using Binance alone is a conservative (higher-impact) benchmark.
- Unknown AP hedging behaviour (pre-hedge vs create-then-buy) can shift intraday impact even when daily net flow is identical.

---

## Cross-cutting prop conclusion (for the report writer)

- The regulated NEAR stack exists and is real, but **small, Bitwise-heavy, and currently leaking at the margin** after a strong launch.
- Staking-inside-ETF is a **soft float sink** given NEAR’s short unbond; it is not a substitute for Intents fee capture and should not be modelled as one.
- Relative to the Intents structural thesis: treat capital-markets products as a **potential incremental demand/float channel** and a **competing narrative**, not as evidence that the fee thesis is working — and not as a reason to ignore outflows or the ~200× revenue multiple.
