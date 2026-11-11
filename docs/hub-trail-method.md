# Tier 4: labelling top-100 receivers by where their NEAR goes

Written 2026-11-11 (UTC), before any tier-4 label is assigned. **Disclosure:** a first look at six hours of census (blocks 223,963,000 to 224,000,999) was taken to see whether the idea could work at all. It showed that the largest unlabelled hubs forward NEAR through chains of intermediate accounts, and that most of the 100 accounts have no transfers in so short a window. The rules below were written after that look, and before any label was decided.

## Source and window

The node census (`pipeline/near_node_archive.py`): every block and the full result of every transaction. Edges come from `pipeline/census_graph.py`: successful receipts with a Transfer action, predecessor to receiver. Gas refunds from `system`, failed receipts and NEAR attached to function calls are excluded, as in PREREG's definition of native NEAR.

The census starts on 2026-11-10, after the H1b window (2026-08-07 to 11-04). A label found here is an inference that an account's role persisted. It is stated that way wherever it is used.

## Rule

An unlabelled top-100 receiver gets **tier 4** if, in the census window:
1. it sent at least **1,000 NEAR** in total, and
2. **at least 80%** of the NEAR it sent went to accounts that are already tier 1, 2 or 3 (the 40 cited accounts and the BigQuery sweep clusters) or tier 4, and
3. the trail reaches a tier-1 account within **3 hops**, with each hop passing the 80% test.

Tier 4 is computed to a fixed point. An account with too little activity to test stays unlabelled. Accounts with a sourced non-exchange identity (staking pools, `intents.near`, `wrap.near`, named DAOs) are never labelled.

## What is reported

- Coverage with tiers 1-3 (the primary measure, unchanged), and beside it coverage with tiers 1-4.
- H1b recomputed under tier 4 as a **side report labelled "if tier 4 is accepted"**. The frozen rating rule is not changed, and nothing in `PREREG.md` is edited. Whether tier 4 may enter the primary measure is a decision for an addendum by the repo owner.
- The same rule run with a stricter 95% threshold and with a 1-hop limit, so the result's sensitivity to the thresholds is visible.
- Every label with its trail (accounts, amounts, hops), so anyone can re-check it against the census or an RPC.

## What would make us drop it

If fewer than 10 of the 80 unlabelled accounts reach tier 4, we say the census could not resolve the labelling and keep H1b as inconclusive.
