# Buyback quality — held float, not burned scarcity

*Exploratory. Numbers in `data/derived/float_sink.json`. As of 2026-11-11. Feeds no pre-registered test.*

The buyback wallet holds **2.187M NEAR** — **held, not burned**. Governance language is discretionary (“no specific mechanism is guaranteed”). About **59%** of recent buyback inflows arrived as escrow unshields. That stock covers about **25 days** of current net issuance (**DIC** = wallet ÷ 88,295 NEAR/day), or about **38 days** if mint scales to the 1.6% HSP path. If buys paused and governance recirculated holdings at the current capture rate (~18k NEAR/day), half the stock would be gone in about **60 days** (scarcity half-life).

## Soft sinks ranked by days of issuance

| Sink | Size | Days of issuance | Exit / recirculation |
|---|---|---|---|
| Buyback wallet | 2.187M NEAR | ~25 (today) / ~38 (1.6% cap) | Governance discretion |
| NRR in-house stake | ~subset of ~$56M AUM | soft | Unbond ~1–2 days |
| AI inference stake | >750k NEAR | ~8.5 | Unstake |
| Liquid staking TVL | LiNEAR/Meta/RHEA | large but liquid | Instant via LST secondary |

## Materiality without volume growth

Annualised capture is **~$24.2M**. Permanently removing **100%** of that from float would cover only about **20%** of today’s annual net issuance in USD (about **31%** after a 1.6% cap). Covering **half** of issuance by burn/lock at today’s mint would need about **~$59M**/year permanently removed — more than **2×** current capture. HSP-029 helps the ratio; it does not make today’s capture a full float sink.

## Policy that hardens the link

Burn, irrevocable lock, or vote-escrow of buyback NEAR would turn DIC from a *balance* into a *removal*. Without that, the token link is fee → discretionary hold → possible recirculation. Score **DIC, scarcity half-life, and burn/lock policy** before treating DefiLlama “holders revenue” as scarcity.

*Not investment advice.*
