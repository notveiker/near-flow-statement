# 14 November runbook: scoring first, then the cross-section

Written 2026-11-13 02:48 UTC (2026-11-13). Nothing here runs before **2026-11-14 00:00 UTC** (18:00 on 13 Nov US Central). Order matters and is enforced in code.

1. **Forward tests F1 to F4 (PREREG.md).** From the repo root, at or after 00:00 UTC: `python3 -m pipeline.score_forward --score`. It refuses to run earlier, fetches DefiLlama, Nearblocks and RPC data stamped at or after 14 Nov 00:00 UTC, and writes `data/forward/score_<stamp>/result.json` and the raw snapshot. A test with missing data is "not scorable", never estimated; every result is published, misses included. Do not re-score afterwards. **Note:** F1 reads the buyback wallet's balance at the first final block after 00:00 UTC. That is the pre-registered test and it happens only inside `score_forward`; the Intents rebuild's rule never to read that balance is about the rebuild and is not touched (no rebuild code reads it).
2. **Record it.** Commit the `data/forward/score_*` directory and add a dated entry to `PREREG-ADDENDUM.md` with the four verdicts and the commit hash. Update `docs/f1-f4-scorecard.md` only by appending the result (do not edit the pre-registered text).
3. **Cross-section (only after step 1's `result.json` exists).** `python3 -m pipeline.fetch_cross_section --held` (the guard checks the clock and the score result), then fill `data/raw/cross_section/partner_share.json` from each venue's own public series (value and source URL per venue; leave null if no public source), then `python3 -m pipeline.cross_section_analysis`. Comparators in `COMPARATORS` are fetched only once each has a mechanism citation. Report all three hypotheses, including a "not scorable".
4. **Rebuild stays frozen** (tag `rebuild-frozen`); the asks A and B and the history sample are separate. Pending decisions that are not mine: W7 and W8 of the staking windows (693 GB), which cut of the history sample is the headline (198 by the rule or 268), and the node census for the sampler validation.
5. **Human items before 2026-11-14 23:59 UTC:** flip the repository public (see the checklist below), record the X video, submit the form.

## Before the public flip
- Merge PR #1 with a **merge commit, not a squash**: the commit times and hashes of the method commits are the evidence that every rule was fixed before its run. Do not rewrite or squash the branch.
- `make rebuild-check` passes; `python3 -m pipeline.check --manifest --numbers` prints PASS.
- Search for stray local paths, personal names and notes: `grep -rn "/Users/\|/tmp/" --exclude-dir=.git .` (raw third-party data excluded).
- The raw history-sample clusters (3.6 GB) are not in git by design; the seal list and plan are (`data/sample/`).
