# History sample, class-adjusted (post hoc): how much of the transaction series is the April-2026 class?

Committed 2026-11-13 02:42 UTC (2026-11-13), before the per-cluster class counts were computed. **Post hoc and exploratory:** it uses a finding (`docs/april-drop-results.md`) made after the history sample's tests U1 to U5 were frozen, so it never replaces them and does not change any verdict; U1 to U5 stay as pre-registered and are reported next to it. Same sample, same stratified cluster design, same estimators and cluster bootstrap as `pipeline/sample_metrics.py` (2,000 resamples, the seed already fixed there).

## The class
A transaction belongs to **class C** if its signer is `hotwallet.kaiching`, `users.kaiching` or `sweat-migration.near`, or its receiver ends in `.users.kaiching`. (The three signers and the receiver family are the ones the April result found; no other account is added, and none is added after seeing sample counts.) Per cluster the code counts: transactions in C, transactions in C by part (signer `hotwallet.kaiching`, signer `sweat-migration.near`, signer `users.kaiching`, receiver family), and distinct signers outside C.

## Cuts
Primary: the **198 clusters sealed by the stopping-rule time** (`data/sample/final_cut.json`). Sensitivity: all 268. Both are reported; the primary is the one that follows the written rule.

## Quantities (per quarter)
C share of transactions; `tx_per_day` and `tx_per_day_exC` (transactions outside C per day); `signers_per_100` outside C; the ratio 2026Q3 / 2025Q3 of each with its 90% interval, and of the raw `tx_per_day` (the U1 quantity).

## Predictions, written to fail (none is a pre-registered test)
- **H-C1 (the class is large before April and gone after).** C carries at least **30%** of sampled transactions in 2025Q3 and at most **5%** in 2026Q3. **Falsified** if its share in 2025Q3 is under 15% or in 2026Q3 over 10%.
- **H-C2 (the raw fall is mostly the class).** The ex-C ratio 2026Q3 / 2025Q3 of `tx_per_day` is at least **2 times** the raw ratio. **Falsified** if it is under 1.5 times the raw ratio.
- **H-C3 (what is left grew).** The ex-C ratio is at least 1.0 with its 90% lower bound above 0.8; the same test as U1 (at least 1.5 with the lower bound above 1) is also reported, labelled "ex-C, not U1".
- **Onset.** The first quarter in which C is at least 1% and the first at least 10% of sampled transactions.
- Counts come from the sealed blocks only; a quarter with fewer than 5 clusters is shown but not used for a ratio. If the class's signers are absent from a sampled cluster the count is 0, never imputed.
