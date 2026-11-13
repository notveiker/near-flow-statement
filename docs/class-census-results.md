# Class C counted exactly on the full chain, and what else fell: results

Method: [class-census-method.md](class-census-method.md), committed at `711c189` (2026-11-13 02:46:03 UTC) before the queries ran. Post hoc, exploratory. `transactions` only; 337 GB billed in two jobs (`data/raw/april/jobs.jsonl`). Computed by `pipeline/class_census_analysis.py`; `data/derived/class_census.json`.

## Part 1: class C exactly
| Quarter | All (M tx/day) | Class C | Outside C | C share |
|---|---|---|---|---|
| 2023Q3 | 0.77 | 0.10 | 0.67 | 13% |
| 2023Q4 | 2.52 | 0.47 | 2.04 | 19% |
| 2024Q1 | 4.32 | 0.48 | 3.84 | 11% |
| 2024Q2 | 7.71 | 0.43 | 7.29 | 6% |
| 2024Q3 | 6.88 | 1.04 | 5.84 | 15% |
| 2024Q4 | 7.49 | 1.89 | 5.60 | 25% |
| 2025Q1 | 6.88 | 2.43 | 4.45 | 35% |
| 2025Q2 | 5.47 | 2.56 | 2.91 | 47% |
| 2025Q3 | 4.84 | 2.51 | 2.33 | 52% |
| 2025Q4 | 4.22 | 2.39 | 1.83 | 57% |
| 2026Q1 | 3.49 | 2.34 | 1.15 | 67% |
| 2026Q2 | 0.85 | 0.03 | 0.82 | 4% |
| 2026Q3 | 0.74 | 0.00 | 0.74 | 0% |
| 2026Q4 | 0.71 | 0.02 | 0.70 | 2% |

- **H-E1 neither supported nor falsified, and the sample under-measured the class.** C is **51.8%** of all transactions in 2025Q3 (the bar for support was 25% to 45%, for falsification under 15% or over 60%). The sample's estimate was 31% on 198 clusters and 43% on 268. C was 15% in 2024Q3, 25% in 2024Q4, 35% in 2025Q1, 47% in 2025Q2, 52% in 2025Q3, 57% in 2025Q4 and **67% in 2026Q1**; it is 4% in 2026Q2 (the first two days of April before the stop at 04-02 plus residue) and 0% in 2026Q3. Almost all of it is `hotwallet.kaiching` (2.2M to 2.3M of the 2.4M to 2.6M C transactions a day in 2025Q2 to Q4).
- **Onset:** the first month with C at 1% and the first at 10% are the same month, **2023-08**: the class starts abruptly in August 2023 at more than a tenth of all transactions (the sample said 2023Q3 and 2024Q3).
- **H-E2 mixed.** The exact ratio 2026Q3 / 2025Q3 outside C is **0.317**, inside the sample's interval (0.237 to 0.373): the sample was right about what is left. The exact raw ratio is **0.153**, just **outside** the sample's raw interval (0.157 to 0.272). So the sample's raw U1 interval missed the census value (the point estimate, 0.21, was close; the census value is just below the interval's lower bound, so the interval's bottom is a little too high), which is consistent with the narrow-interval finding in `history-sample-validation-results.md`.

## Part 2: what else fell, 2025Q3 to 2026Q3 (outside C)
Transactions outside C fell from 215M to 68M in the quarter, a ratio of 0.317. **The decline is concentrated: two signers carry 50% of it** (rule: at most 20 is "concentrated"; 500 or more is "broad"); 20,145 of 1,315,862 signers are needed for 80%. The top 1, 5 and 20 signers carry 32%, 70% and 73% of the gross decline.

| Signer | 2025Q3 (M tx) | 2026Q3 (M tx) | Decline (M) | Cumulative share | Most frequent receiver |
|---|---|---|---|---|---|
| `relay.tg` | 52.79 | 0.02 | 52.78 | 32% | `5248191285.tg` |
| `0-relay.hot.tg` | 53.09 | 3.10 | 49.98 | 61% | `i6934012862.tg` |
| `mytestapi.embr.playember_reserve.near` | 8.21 | 0.00 | 8.21 | 66% | `5271409f8301a85399e7f860f0c79f2fae5339ce8df8e67ed51ae6c3b264fe42` |
| `sweat-relayer.near` | 29.91 | 25.66 | 4.25 | 69% | `spin.sweat` |
| `intents.near` | 6.27 | 3.96 | 2.31 | 70% | `intents.near` |
| `relay.aurora` | 1.49 | 0.71 | 0.78 | 71% | `aurora` |
| `relay.0x4e454228.c.aurora` | 0.71 | 0.00 | 0.71 | 71% | `0x4e454228.c.aurora` |
| `watcher04.ref-watchdog.near` | 0.42 | 0.05 | 0.37 | 71% | `v2.ref-finance.near` |

`relay.tg` (52.8M transactions to 0.02M) and `0-relay.hot.tg` (53.1M to 3.1M) are 61% of the gross ex-C decline; both send to receivers in the `.tg` namespace (INFERRED: relayers for Telegram-linked accounts, a second automated class). `sweat-relayer.near` is still large (29.9M to 25.7M). Risers are small by comparison (the largest: `omni-relayer.bridge.near` 0.01M to 1.9M, `closemeat6237.near` 0 to 1.6M, `bridge-mng.near` 0.24M to 1.3M, `escrow.ai.near` 0 to 1.0M).

## Putting it together (exact, full chain)
Total transactions in 2025Q3 were 445M and in 2026Q3 68M, a fall of 377M. Class C accounts for 230M of it (61%) and the two `.tg` relay signers for 103M (27%): **88% of the whole fall is three automated classes** (two kaiching/sweat accounts and the `.tg` relays); the remaining 12% is spread over everyone else. This corrects the sample-based wording in `history-class-adjusted-results.md` ("not most of the year-on-year fall", "broad decline of everything else"): the ex-C fall is real but concentrated in two signers, not broad. Whether any of this traffic was organic use is not something the chain shows.
