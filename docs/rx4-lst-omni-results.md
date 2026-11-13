# RX4: who sends Intents NEAR to the liquid-staking pool and the Omni bridge: results

Method: the RX4 section of [research-extensions-method.md](research-extensions-method.md), committed at `94dcf81` (2026-11-13 03:04:51 UTC) before the query ran (`rx4_lst_omni`, 17.2 GB, `data/raw/rx/jobs.jsonl`). NEAR only; window 2026-07-07..2026-11-04. Computed by `pipeline/rx_analysis.py` (`rx4`); `data/derived/rx_results.json`.

## Coverage
The `ft_withdraw` events on `intents.near` account for **100.0%** of the wNEAR that FU10's `wrap.near` ledger shows leaving `intents.near` for each receiver (lst-pool.near 8,660,931 NEAR, omni.bridge.near 10,119,670 NEAR). So the initiating Intents account of every one of those transfers is known.

## `lst-pool.near` (liquid staking)
- **8.66M NEAR from 1,645 Intents accounts** in 3,537 events, by month (M NEAR): Jul 0.34, Aug 2.21, Sep 3.99, Oct 2.11. The median account sent 106 NEAR. **1,048 of the accounts are EVM-style (`0x…`) Intents accounts and carry 84% of the NEAR.** Together with FU10's 4.01M NEAR coming back from `lst-pool.near`, the net is about 4.65M NEAR moved from Intents into the pool (an Intents account staking, or unstaking, is the INFERRED reading; the receiver is a liquid-staking contract holding about 58M NEAR).
- **H-RX4a falsified:** the top 3 accounts carry 28.8% (rule 70%; falsified under 40%); the largest sent 1.30M NEAR. **H-RX4b falsified:** the solver family sent 0.0%.

## `omni.bridge.near` (cross-chain bridge)
- **10.12M NEAR from 1,254 accounts, none EVM-style,** essentially all of it from September: Sep 2.77M, Oct 6.93M, Nov 1 to 4 0.39M (July 0.02M, August about 0). Median 301 NEAR per account; several accounts sent exactly 100,000 NEAR (round amounts).
- **H-RX4a falsified:** the top 3 carry 3.5%. **H-RX4b falsified:** the solver family sent 0.0%.

## What it says
Both channels opened in the autumn and are made of many accounts, not the solver family: they are users (or the accounts of users) moving NEAR out of Intents, into a staking pool (mostly through EVM-style accounts) and to other chains through the Omni bridge, 8.66M and 10.12M NEAR from Aug to Oct. That is NEAR leaving the Intents float by choice, next to the 75.97M NEAR that came in through `bridge-mng.near` (FU2b) and the 68.89M that was unwrapped to native NEAR (FU10). It does not say these accounts are distinct people (RX1 shows accounts are cheap) or that the NEAR is new money.
