# Chain rebuild of NEAR Intents: method, fixed before any result

Committed at the minute in the addendum heading (2026-11-12 23:30 UTC), before any query that returns chain data. Only dry runs (byte estimates), one self-test on synthetic JSON and local file builds had run. Changes no hypothesis, threshold, probability or the rating rule in PREREG.md.

**Source.** BigQuery `bigquery-public-data.crypto_near_mainnet_us`, billed to a personal project, every query dry-run and capped (`pipeline/rebuild.py`). Archival RPC (`pipeline/rebuild_rpc.py`) for `mt_balance_of` only. Akash cannot supply this window in time (about 17M blocks; the keyless collector manages ~22 blocks/min). Raw outputs, job IDs and SHA-256 are copied to an Akash VM after the run.
**Cutoff.** Block 223,088,015 / 2026-11-04, enforced in code (every public-table scan must carry `block_height <= 223088015`; no later date may appear; result rows are checked). The node census (from block 223,963,000) is not used. `buybacks.multisignature.near`: transfers to it are counted; its balance is never read (banned tables `account_changes`, `ft_balances_daily`, `circulating_supply`; the RPC reader refuses the account).
**Windows.** Q1, Q2: 2026-07-07..2026-11-04. Q3, Q4: 2026-08-07..2026-11-04 (90 days, the span of `data/raw/explorer/daily.json`).
**Staging.** S0 flattens every `intents.near` EVENT_JSON log in the window (failed receipts, status containing FAIL, dropped) to one row per data element. S1 resolves each `mt_mint` to its originating transaction signer and receiver. S2 builds one row per `token_diff` receipt. S3 assigns the solver side. Parsing is tested on synthetic input first (`data/raw/rebuild/selftest_synthetic.json`).

## Q1. Escrow mass balance (wNEAR, `51e8f94d…7cbe`)
- **Ledger.** Daily wNEAR in and out of the escrow from `mt_mint`, `mt_burn`, `mt_transfer` and `token_diff` events where the escrow is owner, old owner, new owner or account. In: by sender (`mt_transfer` old owner; `mt_mint` transaction signer, tagged "indirect" when the transaction's receiver is not `wrap.near`). Out: by receiver. Any other event type that names the escrow is reported, not dropped.
- **Balances.** `mt_balance_of` at the last block before 2026-07-07 and at block 223,088,015. **Mass balance:** (end - start) must equal in - out. If the residual exceeds 1% of the larger of in and out, the event ledger is incomplete and every Q1 number is tagged so.
- **Classes of sender.** single-use (64-hex account with at most 2 events in the ledger); `bridge-mng.near`; named DAO (`*.sputnik-dao.near`); member of `data/raw/unstakers/account_set.json`; everyone else. Top-10 concentration of in and of out, by amount.
- **Visibility rule (stop condition).** Coverage C = public wNEAR inflow / wNEAR released. If C < 0.5 the finding is "deposits are not visible on a public ledger; the top rung cannot be audited even in principle", and attribution stops there. If C >= 0.5 the attack test runs.
- **Attack on "releases to revenue wallets are fee revenue".** Falsified if a set S of at most 10 non-user accounts (not single-use) deposits at least 80% of the window's releases to the revenue wallets by amount, AND weekly deposits from S correlate with weekly releases at r >= 0.7 at a lag of 0 to 2 days. Whether S's deposits are themselves fees is not observable and is tagged INFERRED. Release amounts are the escrow-funded deliveries in `data/raw/escrow/deliveries.csv`, re-derived from chain in Q2.

## Q2. When the public fee stream moved into the escrow
- Series S1(d) = NEAR delivered by `176121bd…e3e8` to the revenue wallets (`native_withdraw` events); S2(d) = deliveries from single-use accounts (every source other than S1's account and the two collectors). Cross-check: chain totals must match `deliveries.csv` by day; differences are reported.
- **Switch day** = the single change point minimising the sum of squared errors of a two-level fit to S1 (at least 7 days each side). Significance: 10,000 permutations, seed 20261112. **Abrupt** if at least 80% of the pre/post drop falls within 3 days of the change point.
- **Replacement.** With Δ = post-mean minus pre-mean over 14-day windows around the switch day, re-routed fraction = min(1, -ΔS1 / ΔS2) when ΔS1 < 0 < ΔS2. The claim "growth on the unattested path is new revenue" is **falsified if the fraction is >= 0.5**; reported as a null if < 0.2. Also reported: the combined stream S1+S2 before and after, against the Explorer 1Click volume as control.

## Q3. Who fills the orders
- **Fill** = one `token_diff` leg. **Simple swap** = a receipt with exactly 2 legs from 2 distinct accounts. **Complex** = every other receipt: counted, never valued.
- **Solver (INFERRED)** = the participant of a simple swap with more distinct counterparties across all simple swaps in the window. Ties are unclassified. Sensitivity: the participant with more fills.
- **Reported:** share of fills and of priced volume by solver, top-1/5/10 shares, HHI, share unclassified and share of receipts that are complex. Daily series for the top 30.
- **Volume** = the largest priced token amount in the swap. Stable tokens (1Click token-list symbol containing USD or equal to DAI, snapshot price within 3% of 1; `data/raw/rebuild/tokens_1click_20261112.json`) at 1.00; BTC, ETH, SOL, ZEC, XRP, TRX, DOGE, LTC, BNB, NEAR (and their wrapped symbols, alias table in `pipeline/rebuild.py`) at that day's CoinGecko close (nearest day if missing); anything else unpriced and reported as coverage.
- **Funding of the top 20 solvers.** Inbound `mt_transfer` counterparties and `mt_mint` signers inside the window, matched against the unstakers set and the exchange list. `docs/actors.md` does not exist in this repository, so it cannot be used; this is stated, not worked around.

## Q4. The non-1Click share
- Chain daily volume (simple swaps, priced) against `data/raw/explorer/daily.json` `usd_in` (1Click) and DefiLlama `volume_near-intents`. Remainder = chain minus 1Click, INFERRED, with the share of simple swaps priced stated beside it. Chain volume is a lower bound: confidential swaps leave no public leg and complex receipts are not valued.
- Remainder split by the `referral` tag on the swap legs (INFERRED to identify the front end; near.com versus direct versus untagged).
- **DefiLlama step on 2026-09-01.** Weekly sums for 08-25..08-31 and 09-01..09-07. With L = Llama after/before and C = chain after/before: **the step shows on chain** if C >= 1 + 0.5(L - 1); **absent** if C <= 1 + 0.1(L - 1); otherwise ambiguous. Also the chain/Llama ratio before and after.

## Everything
- Numbers come from scripts reading saved files; each output file's SHA-256 and each BigQuery job ID, creation time and bytes billed go in `data/raw/rebuild/jobs.jsonl`. Nulls are reported. Anything that is a reading rather than an observation is tagged INFERRED.
- Code fixes made after this commit and before a result are disclosed in the addendum; a change after a result is disclosed with the result it changed.

## F1 (follow-up to Q1, added after the Q1 to Q4 results; fixed before it runs)
Question: Q1 found the escrow's wNEAR is mostly the inventory of a small solver family (`solver-priv-liq.near`, `solver-multichain-asset.near`, `solver-multichain-asset-escrow.near`, `solver-multichain-asset-2.near`; chosen because they are the escrow's largest counterparties in Q1 and Q3). Where does that inventory come from, and where does it go?
- **Gross recycling ratio** = wNEAR the family sent to the escrow (Q1 ledger) / the family's net external deposits (external mint deposits minus external withdrawals, window). Reported with the family's share of escrow inflow and outflow.
- **Hypothesis H-F1: the escrow is a solver liquidity pool, not a user deposit venue.** Supported if recycling ratio >= 5 and external deposits are under 25% of the family's gross inflow to the escrow. **Falsified** if external deposits (mint, by transaction signer) are at least 50% of that gross inflow.
- **Depositor concentration:** top-5 share of external deposits by signer, and whether any signer is in the unstakers set or the exchange list. A named link to staking exits or exchanges is reported either way; a signer is the initiator, not proof of ownership (INFERRED).
- Queries: `sql/rebuild/rb_f1a_family_deposits.sql`, `rb_f1b_family_withdrawals.sql`. Outputs, job IDs and hashes follow the same rules as above.

## F2 (follow-up to F1; fixed before it runs)
Question: F1 found 30.8M NEAR of wNEAR deposited into the solver family by one signer, `bridge-mng.near`. Who funds that account?
- Source: `ft_events` for `wrap.near` with `bridge-mng.near` as the affected account, window 2026-07-07..2026-11-04: inflows by counterparty and cause (`MINT` = native NEAR wrapped by the account itself, origin not visible in this table; otherwise a transfer from the counterparty), and outflows.
- **Hypothesis H-F2: the funding is concentrated and not from staking exits or exchanges.** Supported if the top 5 counterparties are at least 80% of transfer inflow and none is in the unstakers set or the exchange list. **Falsified** (as "not from staking/exchanges") if counterparties in either list supply at least 10% of inflow. If `MINT` is more than half of inflow the origin is not resolvable from this table and the question stays open (reported, not guessed).
- Output tagged INFERRED where it reads ownership from a counterparty.
