# Capital efficiency — 1.7 days of inventory vs bonded vaults

*Exploratory. Twin: `data/derived/capital_efficiency.json`.*

## Takeaway

Intents holds ~**$229M** against **$4.0B**/30d volume — **~17×** monthly turnover / **~1.7 days** of volume as working capital. Protocol-controlled capital intensity ≈ **$57M per $1B** of 30d volume. Vault peers (THOR/Maya/Chainflip) underwrite with bonded native assets continuously — exact bond-to-TVL ratios are a Gap here. Solvers bear principal inventory risk; the contract holds transit balances. Capital-light wins for long-tail listings; it loses when trust assumptions (PoA, TEE, relayer concentration) fail.

## Punch

1. Do not confuse inventory with protocol “TVL moat” — most of it is non-NEAR in transit.
2. Token claim is still τ / capture share, not ownership of the $229M.
3. Scaling another $1B of monthly volume at constant turns needs ~$57M more working capital somewhere in the solver/contract stack — not a 2:1 bond wall, but not free either.
4. Peers’ bonded capital is a different failure mode (insolvency/bond) vs Intents’ (trust/ops).
