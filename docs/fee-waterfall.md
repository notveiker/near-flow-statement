# Fee waterfall — who keeps the basis points

*Exploratory / post-freeze prop research (as of 2026-11-11). Working detail in [`research_notes/NEAR catalysts and path/fee-waterfall-capture.md`](../research_notes/NEAR%20catalysts%20and%20path/fee-waterfall-capture.md). Feeds no pre-registered test.*

DefiLlama’s **15.3 bp** gross fee on Intents is not the user’s all-in cost and is not the token’s claim. Wallet routes list **40–140+ bp** of partner `appFees`, realized cost runs about **8.5 bp** above listed on $1K–$50K swaps, and NEAR revenue wallets receive about **4.98 bp** of DefiLlama volume. The on-chain protocol fee is **1 pip**. Economically Intents is a **distribution-fee venue** with a discretionary buyback sidecar.

## Scoreboard that matches the token claim

| Metric | Value | Read |
|---|---|---|
| Token-claimable take \(τ\) | **4.98 bp** | What the three revenue wallets receive |
| Capture share \(C\) | **32.5%** | Captured / DefiLlama gross |
| Distribution tax \(D\) | **67.5%** of DefiLlama gross | Gross that does not reach NEAR wallets |
| Leakage ratio \(L\) | **~9.9×** | Partner listed bp / explicit buyback bp on 1Click (block3) |
| Attachment-implied token rate (AITR) | **9.49 bp** | Explicit buyback bp ÷ attach share |
| All-in token claim \(α\) | **~21%** | 4.98 / (15.3 + 8.5) — still too high on SwapKit paths where explicit NEAR ≈ 0 |
| SwapKit NEAR share of SK partner fees | **~0.0045%** | $159 buyback vs $3.53M partner fees |

Venue-average capture **masks pipe-level zero**: SwapKit is **38.2%** of 1Click volume and pays NEAR almost nothing on the explicit buyback line, while on-chain partner payouts are the **full listed** rate. Marketing **50/50** is not the SwapKit reality.

## Peers are not like-for-like

| Venue | Vol (30d) | Gross bp | Token claim design |
|---|---|---|---|
| Intents | $4.0B | 15.3 | Discretionary wallet / buyback (held, not burned) |
| THORChain | $1.8B | 12.3 | Bond / pendulum; REVSHARE can subsidize affiliates without raising user fee |
| Chainflip | $0.85B | 31.5 | ~10 bp network fee → FLIP buy/burn by design |
| Maya | $0.53B | 9.4 | Hard **10%** of protocol fees to holders (~**0.94 bp** of volume if applied to gross) |

Intents leads on volume and extracts more gross bp than THOR/Maya; peers with vault designs hard-wire more of *their* fee stack to LPs, nodes, or burns. The investment-relevant comparison is **token-claimable bp and claim stickiness**, not DefiLlama “revenue” alone.

## What moves the waterfall without a take-rate war

Attachment rose **23.6% → 43.0%** of 1Click volume while SwapKit share stayed roughly flat — AITR × attach is the dial NEAR can turn on contestable public flow. Mix toward near.com (stated 100% fee direction) raises capture share without lifting user all-in on partner wallets. Attesting escrow unshields collapses the **4.5–15.8%** issuance-offset range; it does not create revenue. Forcing SwapKit 50/50 is high arithmetic upside and high exit risk on **38%** of 1Click volume. THOR’s REVSHARE is structured to steal that flow **without** cutting the user’s fee — the race-to-zero risk sits on NEAR’s **buyback line**, not on partner bp.

Channel map detail: about **46%** of explicit buyback fee dollars come from **no-referrer** flow (18.7% of volume at 10 bp). LI.FI is 10% of volume at only 2.8 bp. Trust *direct* is 20 bp on 2.4% volume. SwapKit subchannels keep high partner bp with ~0 explicit buyback (`data/derived/buyback_channel_map.json`). Chase defaults and high-bp directs for attach — not the wallet logos inside SwapKit.

Score **τ, C, L, AITR, attachment %** before peer volume share. Volume share without those overstates NEAR’s claim on the waterfall.

*Not investment advice.*

## Solver / excess residual (1Click Explorer)

Realized cost runs about **8.5 bp** above listed appFees on the Explorer sample. On ~**$1.10B** of Explorer notional that is about **$0.94M** in the window — solver/gas/pip residual, **not** NEAR wallet capture. Listed partner fees were about **$4.45M**; buybacks from appFees about **$0.45M**. Exact solver P&L split inside the excess is a Gap (`data/derived/solver_excess.json`).

No-referrer dollar concentration: `data/derived/noref_dollar_concentration.json` (~2.45× buyback-$ vs vol share).
