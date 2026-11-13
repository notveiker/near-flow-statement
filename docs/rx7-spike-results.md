# RX7: who made the September spike: results

Method: the RX7 section of [research-extensions-method.md](research-extensions-method.md), committed at `d9f6527` (2026-11-13 03:15:11 UTC) before it was computed. Local, from saved outputs (`rb_fu2b_a_daily`, `rb_fu7_a_summary`, `rx6_wrap_daily`); `pipeline/rx_analysis.py` (`rx7`).

- **H-RX7a supported:** in the two spike weeks (2026-09-15 to 09-28) **90%** of the 35.4M NEAR transferred into `intents.near` came from `bridge-mng.near` (rule: at least 60%). So the burst is the deposit path (native NEAR wrapped and deposited), not returns from Ref, the LST pool or Omni.
- **H-RX7b supported:** the Binance relay of FU7 (`1244d552…`) supplied **14.5M NEAR, 46%** of what `bridge-mng.near` wrapped in those two weeks (rule: at least 40%; falsified under 15%). One operator's pipeline is nearly half of the deposits in the burst; the relay is between 11% and 61% of the deposit path in every week of the window (median 38%).
- Together with RX6: the price-linked spike in NEAR flowing through Intents is mostly deposits, and close to half of those deposits are NEAR coming from Binance wallets through one forwarding account. The other half is spread over the 55,000 funders of FU2b. Whether that operator was trading the price move or doing its normal inventory work is not visible.

| Week from | Transfers in (M NEAR) | From `bridge-mng.near` | Share | Relay `1244d552…` | Relay share of bridge deposits |
|---|---|---|---|---|---|
| 2026-07-07 | 2.09 | 1.74 | 83% | 0.19 | 11% |
| 2026-07-14 | 0.96 | 0.72 | 75% | 0.15 | 21% |
| 2026-07-21 | 1.74 | 1.43 | 82% | 0.18 | 13% |
| 2026-07-28 | 1.93 | 1.54 | 80% | 0.87 | 56% |
| 2026-08-04 | 2.43 | 2.17 | 89% | 1.11 | 51% |
| 2026-08-11 | 2.56 | 2.24 | 88% | 0.44 | 19% |
| 2026-08-18 | 4.10 | 3.48 | 85% | 2.11 | 61% |
| 2026-08-25 | 4.23 | 3.77 | 89% | 1.15 | 31% |
| 2026-09-01 | 4.11 | 3.48 | 85% | 0.77 | 22% |
| 2026-09-08 | 4.67 | 3.69 | 79% | 1.94 | 53% |
| 2026-09-15 | 11.09 | 9.39 | 85% | 4.21 | 45% |
| 2026-09-22 | 24.29 | 22.32 | 92% | 10.31 | 46% |
| 2026-09-29 | 11.90 | 6.23 | 52% | 2.29 | 37% |
| 2026-10-06 | 7.83 | 5.57 | 71% | 1.78 | 32% |
| 2026-10-13 | 4.98 | 3.30 | 66% | 1.24 | 38% |
| 2026-10-20 | 4.83 | 3.01 | 62% | 1.44 | 48% |
| 2026-10-27 | 2.69 | 1.57 | 58% | 0.62 | 40% |
