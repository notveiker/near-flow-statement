# NEAR Intents rebuilt from the chain: results

Window and rules: [chain-rebuild-method.md](chain-rebuild-method.md), committed (`047b429`, 23:30:41 UTC) before the first job (23:30:46 UTC). Cutoff block 223,088,015 (2026-11-04). All numbers come from `python3 -m pipeline.rebuild_analysis` reading saved BigQuery outputs (`data/raw/rebuild/`, job IDs and SHA-256 in `jobs.jsonl` and `data/MANIFEST.json`); results in `data/derived/rebuild_results.json`. Nothing here is a forward test. **INFERRED** marks a reading, not an observation.

## Q1. Escrow mass balance (wNEAR)

| | NEAR |
|---|---|
| Balance, block 205,869,621 (last before 2026-07-07), `mt_balance_of` | 5,731,342 |
| Balance, block 223,088,015 | 12,568,570 |
| Ledger inflow (226,172 `mt_transfer` into the escrow, 20,749 senders) | 81,490,197 |
| Ledger outflow (70,146 `mt_transfer` out, 28,495 receivers) | 74,652,968 |
| Residual (balance change minus ledger net) | -2.8e-9 |

- **The ledger is complete.** The balance change equals the event ledger to the yoctoNEAR scale. Every wNEAR movement in or out of the escrow is a public `mt_transfer` between Intents accounts. Deposits by `mt_mint` into the escrow: 0 rows. The only other event type that names the escrow, `transfer` (22,107 grouped rows), carries no amount and mirrors the transfers.
- **Deposits are visible, so the top rung can be audited.** Visibility C = inflow / outflow = 1.09 (rule: below 0.5, stop). The stop condition did not trigger.
- **What goes in is mostly one solver's inventory.** `solver-priv-liq.near` is 48.1% of inflow (39.2M NEAR) and 34.0% of outflow (25.4M); its net contribution is +13.8M, 2.0x the escrow's whole balance change. Top-10 senders hold 56.0% of inflow, top-10 receivers 42.7% of outflow. Its funding counterparties are mostly the escrow itself and sibling solver accounts (Q3). Class split of inflow: "other" (named accounts) 50.4%, single-use 49.6%; no inflow from `bridge-mng.near`, named DAOs or the unstakers set. Outflow: single-use 65.2%, other 34.8%. A single-use pair moves 1.73M NEAR in and the same 1.73M out (`7bb16411…` in, `bf20691c…` out): a round trip.
- **Attack on "releases to the revenue wallets are fee revenue": not falsified, narrowly.** Releases to the three revenue wallets are 910,990 NEAR (1.2% of escrow outflow). The top-10 non-single-use depositors supplied 40.4M NEAR (44x the releases), so the size criterion is met trivially. The timing criterion, weekly correlation of their deposits with releases at a lag of 0 to 2 days, is r = 0.64, 0.57, 0.56 (17 weeks), below the 0.7 bar. The rule as written needs both, so the claim stands. The size criterion cannot discriminate here, so the test rests on one correlation of 17 weekly points. Whether any depositor's wNEAR is itself fee income is not observable (**INFERRED**: the escrow is chiefly a solver liquidity pool, and the releases are a small fraction of it).

## Q2. When the public fee stream moved into the escrow

- Chain `native_withdraw` deliveries to the three wallets equal `deliveries.csv` exactly: 1,669,164.77 NEAR, 0 days differing by more than 1 NEAR.
- **Switch day for `176121bd…`: 2026-08-29** (2,739 NEAR the day before, 0 on the day), abrupt, 65.7% of the series' variance removed by one step, permutation p = 0.0001. Mean per day 14 days either side: 2,508 NEAR before, 351 after; monthly 58.2K (Aug), 5.2K (Sep), 1.0K (Oct), 0 (Nov to the cutoff).
- **Single-use deliveries stepped up ten days earlier, 2026-08-19** (21.9K NEAR that day), then again in early September. Monthly, all three wallets: 46.9K (Jul), 149.5K (Aug), 365.2K (Sep), 323.8K (Oct). To `fefundsadmin` alone (post hoc, matching the series in the brief): 69.1K (Aug), 154.7K (Sep), 153.3K (Oct).
- **Replacement: partial.** Re-routed fraction = 0.35 (the fee-account fall is 35% of the single-use rise around the switch), between the 0.2 null bar and the 0.5 falsification bar. So the claim that growth on the unattested path is new revenue is not falsified, and it is not clean either: about a third of the step is a move from the public account, two thirds is not explained by it. The combined stream rose from 8.8K to 12.7K NEAR/day (x1.45) while the Explorer 1Click volume over the same 14-day windows fell 10.6% ($700M to $626M).

## Q3. Who fills the orders

- 1,222,666 simple swaps (exactly two public legs) in the 90 days; 1,140,800 receipts are complex (48.3% of receipts, 67.2% of legs) and are not attributed or valued. **Every share below is for simple swaps only (INFERRED solver side: the participant with more distinct counterparties).** Unclassified: 0.004%.
- **61 solver accounts.** Top 1 / 5 / 10 hold 37.4% / 80.3% / 93.5% of fills (HHI 0.20) and 21.0% / 75.5% / 95.2% of priced volume (HHI 0.14). The alternative rule (more fills) gives the same top solver and top-10 of 93.5%.
- By fills: `blockzen-1-main.near` 37.4% (17.3% of volume), `kipseli.near` 17.5% (7.6%), `crux-solver.near` 15.9% (21.0%), `solver-multichain-asset.near` 5.2%, `111-testing-funds.near` 4.3% of fills and $783 of volume (test traffic), `solver-priv-liq.near` 4.1% (10.2%). By volume the largest is `crux-solver.near` 21.0%, then `0x8c60fa34…` 19.4%, `blockzen-1-main.near` 17.3%.
- **Funding of the top 20 (inside the window only).** None has an inbound counterparty in the unstakers set or the exchange list. Their inbound transfers come from each other and from the escrow: the top three counterparties of `solver-priv-liq.near` are the escrow (412K transfers), `solver-multichain-asset.near` and its escrow sibling; `solver-multichain-asset.near` is funded mainly by the escrow too. `docs/actors.md` is not in this repository, so it could not be used.

## Q4. The non-1Click share

- Chain-visible priced volume of simple swaps: $2.17B (94.5% of simple swaps priced). Explorer 1Click `usd_in`: $3.81B. DefiLlama: $11.71B. Chain / 1Click 0.57, chain / Llama 0.19, 1Click / Llama 0.33.
- **The remainder cannot be measured as chain minus 1Click.** The chain figure is a lower bound (complex receipts, 67% of legs, are not valued; confidential swaps leave no public leg), and it falls below the 1Click total, so the subtraction is negative (-$1.64B). What can be said: 93.1% of the valued chain volume carries a `1click-*` referral tag, 4.1% has none, 2.8% has another tag. Public-mode simple swaps are therefore overwhelmingly 1Click flow (**INFERRED** from the tag). The ~45% of volume outside 1Click that the brief asks about is not visible in public swap legs.
- **DefiLlama's 2026-09-01 step does not show on chain.** Week after / week before: Llama x1.32, chain simple-swap volume x1.03, 1Click x0.93. By the pre-registered rule the step is absent from chain. Post hoc, complex receipts also show none (receipt count x1.02, legs x1.00; simple swaps count x1.16). Chain / Llama falls from 0.23 (7 to 31 Aug) to 0.17 (8 Sep to 4 Nov). Whatever Llama added on 1 September is not in public swap events; whether it is confidential flow or a counting change is not observable here.

## F1. Where the solver family's wNEAR comes from (follow-up, method committed before the run)

- Family = `solver-priv-liq.near`, `solver-multichain-asset.near`, `-escrow`, `-2`. Gross inflow to the escrow from the family: 39.24M NEAR, 99.9% of it from `solver-priv-liq.near`.
- External wNEAR deposits into the family (`mt_mint`): 30.80M NEAR, **78.5% of that gross inflow**; recycling ratio 2.4. **H-F1 (the escrow is a solver-internal liquidity pool) is falsified** by its pre-registered rule (50%; support needed 5x and under 25%). Deposits by month: 0.8M (Jul), 5.4M (Aug), 19.3M (Sep), 5.3M (Oct). Out of the family: 14.4M `mt_burn`, 13.6M native NEAR to one account (`d6b77389…`).
- **Read with care (post hoc, INFERRED).** Every one of those deposits was signed by `bridge-mng.near`, but that account signs 53% of all 3.04M `mt_mint` events in the window (1.62M events for 1.44M different owners; 53% of wNEAR mints too). It is the deposit relayer, not the owner of the funds. "External" therefore means "arrived through the deposit path", not "from a named holder".

## F2. Who funds `bridge-mng.near` (follow-up): not resolvable from `ft_events`

`ft_events` has no `wrap.near` rows at all (checked on 2026-09-20: 0 rows), because `wrap.near` writes legacy log lines instead of NEP-297 events. The pre-registered query therefore returned 0 rows, which says nothing about the account. The question stays open; answering it needs the legacy `wrap.near` log lines (a full `execution_outcomes` scan of about 180 GB, roughly $1) and would also be a change of source to disclose.

## Deviations and corrections (disclosed)

1. **Pricing bug, found on seeing zero priced swaps in the first Q4 output.** The staging step stored each event as a string, so the diff was wrapped in a second layer of quotes and the token regex matched nothing. The synthetic self-test passed because it used a JSON-typed value. Fixed in `rb_s2_swaps.sql`, self-test extended to the production form, stages 2 and 3 and the Q3/Q4 queries rerun at 23:36 UTC. First-run outputs are kept in `data/raw/rebuild/superseded/`. No volume number from the first run was used; fill counts and solver assignment were unaffected.
2. **Q3d hit the 1,000,000-row output cap** on first run; rewritten to keep the 50 most frequent counterparties per solver and rerun.
3. The `fefundsadmin`-only series, the complex-receipt step check and the single-use round-trip note are post hoc and tagged so.

## Reproduce

`python3 -m pipeline.rebuild load-aux`, then `run` each `sql/rebuild/rb_s*.sql` then `rb_q*.sql` (about 383 GB billed over all jobs), `python3 -m pipeline.rebuild_rpc 205869621 223088015`, `python3 -m pipeline.rebuild_analysis`.
