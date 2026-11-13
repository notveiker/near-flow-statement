# RX5 and RX6: results

Method: the RX5 and RX6 sections of [research-extensions-method.md](research-extensions-method.md), committed at `0b09de6` (2026-11-13 03:13:47 UTC) before anything was computed (RX6 query `rx6_wrap_daily`, 0.1 GB; RX5 is local). NEAR only; cutoff respected. `pipeline/rx_analysis.py`; `data/derived/rx_results.json`.

## RX5: the repo's capture ladder replicates from the chain
- Over 2026-10-06..2026-11-04 the chain's `native_withdraw` deliveries to the three revenue wallets, priced at the daily NEAR price, are **\$2.010M**, which over the repo's net issuance of \$12.71M is **15.81%** against the repo's 15.81% (ratio 1.0001). **H-RX5a supported** (within 10%).
- Split: the escrow-funded group \$1.44M = 11.31% of issuance, the public accounts \$0.57M = 4.51% (repo: 11.25% and 4.53%). The escrow-funded share of delivered dollars is **71.5%** against 71.2% in the repo's ladder. **H-RX5b supported** (within 5 points).
- So the chain alone (no Explorer, no `deliveries.csv`, no DefiLlama) reproduces both the repo's 15.8% headline and its split between public collectors and escrow unshields. This is a consequence of Q2 equalling `deliveries.csv` exactly, but it is the first time the two ladder rungs are rebuilt from FU4's group definitions, and it holds at the second decimal. The denominator is the repo's, not re-derived.

## RX6: do Intents' NEAR flows follow the price?
Weekly contract-wide wNEAR flows (millions of NEAR) and the NEAR price return, 17 weeks from 2026-07-07:

| Week from | In | Out | Net | Of which unwrap | Price return |
|---|---|---|---|---|---|
| 2026-07-07 | 2.09 | 1.57 | +0.52 | 0.74 | -7% |
| 2026-07-14 | 0.96 | 0.94 | +0.03 | 0.79 | +3% |
| 2026-07-21 | 1.74 | 1.98 | -0.24 | 1.84 | -7% |
| 2026-07-28 | 1.93 | 2.05 | -0.12 | 1.15 | -6% |
| 2026-08-04 | 2.43 | 2.30 | +0.13 | 2.13 | -8% |
| 2026-08-11 | 2.56 | 3.17 | -0.61 | 3.03 | +0% |
| 2026-08-18 | 4.10 | 3.90 | +0.20 | 2.42 | +26% |
| 2026-08-25 | 4.23 | 3.87 | +0.36 | 3.54 | -10% |
| 2026-09-01 | 4.11 | 3.14 | +0.97 | 2.79 | +34% |
| 2026-09-08 | 4.67 | 4.35 | +0.32 | 2.67 | -6% |
| 2026-09-15 | 11.09 | 7.19 | +3.89 | 6.25 | +81% |
| 2026-09-22 | 24.29 | 15.82 | +8.48 | 12.88 | +29% |
| 2026-09-29 | 11.90 | 16.17 | -4.27 | 11.26 | -9% |
| 2026-10-06 | 7.87 | 9.30 | -1.43 | 6.44 | +20% |
| 2026-10-13 | 5.03 | 5.61 | -0.57 | 4.32 | -15% |
| 2026-10-20 | 4.88 | 5.28 | -0.39 | 4.32 | -8% |
| 2026-10-27 | 2.72 | 2.50 | +0.22 | 1.98 | -7% |

- **H-RX6a supported, narrowly:** Spearman rho of net flow with the same week's price return is **+0.45**, permutation p = 0.072 (rule: at least +0.30 and p at most 0.10). **H-RX6b not supported:** net flow of one week against the next week's return gives rho +0.19, p = 0.48: no sign that flows lead price. Net inflow in 59% of weeks; total net 7.49M NEAR (the 17 weeks end 2026-11-02; the +7.61M of FU10 runs to the cutoff, 11-04).
- **Post hoc (tagged): the same-week result comes from two weeks.** The weeks of 09-15 (price +81%) and 09-22 (+29%) carry 12.4M of net inflow and 58.4M of the 186M gross turnover (31%). Without them rho is +0.21 (p = 0.45, n = 15). So the evidence that net flows chase price is one episode, not a regular pattern.
- **Post hoc: turnover follows volatility.** Weekly gross flow (in plus out) against the absolute price return: rho = **+0.66**, p = 0.005. Intents' NEAR plumbing carries far more NEAR in weeks when the price moves a lot, in either direction; and the price spike of mid-September lifted gross weekly flow from 9M to 18M to 40M NEAR (weeks of 09-08, 09-15, 09-22) and it was back to 5M by the week of 10-27.
- **Reading (INFERRED).** The September episode is a burst of trading-driven NEAR passing through Intents (deposits and unwraps both high, net inflow at the peak, net outflow in the weeks after) rather than a lasting build-up of NEAR in the float: by the week of 10-27 gross turnover is about 5M NEAR (the July weeks averaged 3.3M, so about 1.6 times July, and the same as the weeks of 08-04 and 08-11) and net flow is about zero. Nothing here shows who the accounts were (RX1: accounts are not users) or a causal link to price.
