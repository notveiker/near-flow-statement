# RX11 and RX12: which assets drive the public swap volume, and which chains the dollars move between: method fixed before the query runs

Committed 2026-11-13 (UTC time in the addendum entry). NEAR-only follow-ups to RX9 and RX10, on the same population: **public simple swaps with a priced leg**, 2026-08-07..2026-11-04, block 223,088,015, staged tables (`swaps_solver`, `intents_events`, `tokens`), roughly 20 GB read. The rebuild stays frozen (tag `rebuild-frozen`). Query: `sql/rx/rx11_rx12_flows.sql`; analysis: `pipeline/rx_analysis.py` (`rx11`, `rx12`).

**What was already seen before this method was written:** RX9 showed the top symbol pairs by volume (including that ZEC pairs are among the top ten and that BTC/USDT and BTC/USDC are large) and the stable-to-stable weekly share. The thresholds below were written with that in mind; the weekly asset series, the chain pairs and the user-side direction of each swap were not looked at.

**Direction.** The user is the participant that is not the inferred solver (the Q3 rule, as in RX1). In the user's `token_diff` leg, the token with a negative amount is what the user sold and the token with a positive amount is what the user bought. Swaps whose user leg does not have exactly one negative and one positive token are excluded and counted with their dollars. **Chain** is the `blockchain` field of the token in the rebuild's `tokens` table; a token not in the table is `unknown` and excluded from chain results. **Asset groups:** the symbol with `(DEPRECATED)` removed; `USDT0` is USDT, `WBTC` is BTC, `wNEAR` is NEAR. A swap counts once per distinct asset group it involves. **Weeks:** 7-day blocks from 2026-08-07; blocks 0 to 11 are complete (to 2026-10-29); block 12 is partial (6 days) and is shown but not used in a verdict.

## RX11: which assets drive the volume
- **H-RX11a (ZEC is a growth route):** the share of weekly priced volume that involves ZEC, averaged over blocks 8 to 11, is at least **1.5 times** its average over blocks 0 to 3. Falsified if it is below **1.0 times**.
- **H-RX11b (BTC leads the volatile assets):** BTC (including WBTC) is the largest non-stable asset group by volume involved in at least **11 of the 12** complete weeks. Falsified below **7 of 12**.
- **H-RX11c (few volatile assets):** the top 3 non-stable asset groups by volume involved over the whole window account for at least **70%** of the dollars of swaps that have a non-stable leg. Falsified below **50%**. The numerator is the dollars of swaps that involve at least one of the three groups on a non-stable leg; the denominator is the dollars of all swaps with at least one non-stable leg, so the share cannot exceed 100%.
- Also reported: the weekly volume involving each of the top 10 non-stable groups; per asset, user-sold dollars and user-bought dollars.

## RX12: which chains the dollars move between, and how much touches NEAR
- **H-RX12a (the NEAR chain is a small leg):** swaps with at least one token on the NEAR blockchain carry at most **15%** of priced volume. Falsified above **30%**. This is the share of public swap volume that touches an asset living on NEAR; it says nothing about fees, which are taken in several ways (FU4, FU5).
- **H-RX12b (destination chains are few):** the 3 chains with the most dollars bought by users carry at least **60%** of dollars. Falsified below **40%**.
- **H-RX12c (users net buy volatile assets):** over the window, dollars of non-stable tokens bought by users exceed dollars of non-stable tokens sold by users (a swap between two non-stable tokens adds to both and cancels). Falsified if sold exceeds bought. This is a direction over one quarter and follows prices; weekly values are reported and no reading about sentiment is drawn.
- Also reported: the 10 largest chain-to-chain flows (from the chain of the sold token to the chain of the bought token), net dollars by chain (bought minus sold), the same-chain share of dollars.

## What this does not show
Public swaps with priced legs only (complex receipts and confidential swaps are absent). "User" and "solver" are inferred. Chain labels are what the Explorer-style token table says, not an independent check of where the asset sits. The net direction is of the swap legs, not of any wallet's holdings.
