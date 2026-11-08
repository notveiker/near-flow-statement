# Submission package and November 14 runbook

**This is an internal runbook for the repository owner. It must not be merged into `main` or published**; section 3 gives the commands that keep it out. Written on 2026-11-07 (UTC, a Saturday) and revised on 2026-11-08, for NEAR HACKATHON 2026, track `thesis`. It holds no keys, none of your own account IDs and no forward-test result (none exists yet), but it does hold your time zone, your open decisions, draft answers to a judge and draft public statements, so it is not something to publish.

**Three facts set the schedule.**

1. Submissions close on Saturday 2026-11-14 at 23:59 UTC. There is one submission per team, and it cannot be edited after it is sent (organizers' `SUBMITTING.md`).
2. The forward tests F1-F4 can be scored from 2026-11-14 00:00 UTC. The scorer refuses to run earlier.
3. The repository is private today. A judge cannot see, clone or check anything until you make it public.

Judging runs from 2026-11-16 to 2026-11-18, and the jury includes Claude Code and Codex as AI judges (organizers' README).

**Order of work.** The dates are suggestions, not organizer deadlines.

| By | What | Where |
|---|---|---|
| Mon 2026-11-09 | Set your commit email. Bring the work to `main` without this file, push it, take the working branch off GitHub. Scan. Make the repository public. Enable Pages. | sections 1 and 3 |
| Thu 2026-11-12 | Decide on Drafts 1 to 3 (2.10). Anchor `PREREG.md` (4a) or record that you did not (4b). Rehearse. Commit the scoring-procedure entry. | 2.3, 2.8, 2.10 and 4 |
| Fri 2026-11-13 | Record the video. Draft the post. Have the payout account ID ready. Read `HACKATHON.md`. Run the final checks. | sections 5 and 6 |
| Sat 2026-11-14 | Score, verify, commit, push, post, submit. | section 2 |

**Marks.** UNVERIFIED means the sandbox (the restricted environment this file was written in) could not check it. Everything else was checked on 2026-11-07, or on 2026-11-08 for the parts revised then: against the repository, by a command run in a scratch copy of it, or on a page fetched that day (list at the end). Statements about the state of the work and about counts describe the commit named next to them and go stale with the next commit.

| Section | Contents |
|---|---|
| [1](#1-status-against-the-organizers-checklist) | Status against the organizers' checklist, and what the history exposes |
| [2](#2-the-november-14-forward-test-runbook) | The November 14 forward-test runbook |
| [3](#3-making-the-repository-public-and-hosting-the-dashboard) | Making the repository public, and hosting the dashboard |
| [4](#4-optional-anchor-preregmd-on-near-mainnet) | Optional: anchor `PREREG.md` on NEAR mainnet |
| [5](#5-demo-assets) | Demo assets: posts, video shot list, screenshots |
| [6](#6-submission-payload-draft) | Submission payload draft |
| [7](#7-risks-and-weak-points-a-judge-may-raise) | Risks and weak points a judge may raise |
| [8](#8-open-decisions) | Open decisions |

## 1. Status against the organizers' checklist

Source: [`SUBMITTING.md`](https://github.com/nearai/near-hackathon-prompt-examples/blob/main/SUBMITTING.md) in `nearai/near-hackathon-prompt-examples`, fetched 2026-11-07. The live rules, <https://nearhackathon.com/HACKATHON.md>, were not reachable from the sandbox and may differ. Read them before you submit (UNVERIFIED: anything they add).

| # | Organizers' item (verbatim) | State | Why |
|---|---|---|---|
| 1 | *The repository is public, and the README has "do X, see Y" steps an AI judge can follow* | **not done** | GitHub reported the repository as private, with no Pages site (API check, 2026-11-07; not repeated since). The README with its "do X, see Y" table is committed on the working branch `claude/near-hackathon-dashboard`, not on `main`. Owner action: section 3. After the merge to `main`, run `bash scripts/fresh_clone_check.sh` to rehearse the judge's steps in a clean clone. |
| 2 | *Your demo post is live on X, says you built it at NEAR HACKATHON, and has a video or screenshots attached* | **owner action** | Nothing is posted. Drafts, shot list and screenshot list: section 5. The post links the repository, so the repository must be public first. |
| 3 | *You have a mainnet NEAR account for the prize payout, either your own or the team's* | **owner action** | The sandbox cannot see your accounts. The organizers' README says all prizes are paid in NEAR. Section 6 has a blank for the account ID. Copy it from your wallet; do not retype it. A mistyped account is a common cause of irreversible token loss ([NEAR docs](https://docs.near.org/web3-apps/tutorials/account-validation.md)). |
| 4 | *You've selected every track your project fits* | **owner action** | At submission. `thesis` fits by the track brief. `open` is allowed alongside any track, per its brief, and whether it fits is your call (section 6). The live form is UNVERIFIED. |
| 5 | *There are no keys or secrets anywhere in the repo history* | **done as far as scanning can tell; re-run before going public** | A manual regex pass over the full history found none. A second pass on 2026-11-07, over every distinct file version in the history at that time and over the current files, also found none. `python3 scripts/scan_secrets.py --history` passed on 2026-11-08 at `a1fe2e6` (exit status 0; it prints the blob and commit counts, 218 blobs and 39 commits there, which grow with every commit). It is a pattern scan, so a clean result is not proof. Re-run it on the final tree. |
| 6 | *You're submitting before Nov 14, 2026, 23:59 UTC* | **not done** | Plan with buffers: section 2.4. Submit by 20:00 UTC at the latest. |

### What the history exposes once the repository is public

- **Your email address.** The 29 commits up to `38e1c4c` carry your name and a personal email address as author and committer. `git log --format='%an <%ae>' | sort | uniq -c` prints them. The 10 commits since, made from the Claude Code session (`c86a876` to `a1fe2e6`), carry the assistant's name and an Anthropic noreply address, not yours (`git log --format='%ae' | sed 's/.*@/@/' | sort | uniq -c` counts them by domain). Anyone who clones the public repository can read all of it. Your address is not a secret, but it is personal data.
- **The old commits cannot be fixed.** Rewriting history changes every hash after the edit. That would break the tag `prereg-freeze` (commit `413d776`), the commits the addendum cites (`51e396b`, `b1861cd` and others) and the README. GitHub's docs say commits made before you change your email stay associated with the old address ([source](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/setting-your-commit-email-address)).
- **New commits can be protected.** On GitHub open Settings, then Emails. Tick "Keep my email addresses private" and "Block command line pushes that expose my email" ([source](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/blocking-command-line-pushes-that-expose-your-personal-email-address)). In the repository run `git config user.email "<your GitHub noreply address>"`. For accounts created after 2017-07-18 that address has the form `ID+USERNAME@users.noreply.github.com` ([source](https://docs.github.com/en/account-and-profile/reference/email-addresses-reference)). The new work is already committed under the assistant's identity, so the one commit that will carry yours is the squash commit you make on `main` in section 3, step 2: set the address before you make it.
- **The trailers.** Every commit carries `Co-Authored-By: Claude` with Anthropic's noreply address; the README discloses this and says "every commit", so the squash commit you make must carry it too (section 3, step 2). The commits made from the Claude Code session since 2026-11-07 (10 up to `a1fe2e6`) also carry a `Claude-Session:` trailer holding a claude.ai link to that session. Who can open that page is UNVERIFIED. The README says only that some commits carry such a trailer.
- **The three "never publish" lines in `.gitignore`** (`near-research.md`, `notes/`, `private/`) are in the first commit (`a2cb97c`) and have never changed. Deleting them now changes nothing in history. The README and `THESIS.md` already say that prior work exists outside the repository. Leaving them is harmless, and that is the recommendation.
- **The tag is on GitHub.** `git ls-remote --tags origin 'prereg-freeze^{}'` prints `413d776164a42ddb2b1288bb02bd7bd112bc7f06` and the ref `refs/tags/prereg-freeze^{}`.
- **State of the work (2026-11-08).** The new work is committed on the branch `claude/near-hackathon-dashboard` (tip `a1fe2e6`), and `git branch -vv` shows `origin/claude/near-hackathon-dashboard` at the same commit, so it was pushed (check with `git ls-remote --heads origin`). `main` and `origin/main` are still at `38e1c4c`. A judge sees only what is on the public branches. **That branch's history contains this file (added in `552c63b`) and the `Claude-Session:` trailers, and every branch of a repository becomes public with it, so the branch must come off GitHub before the repository goes public (section 3, step 2).** Re-check with `git status -sb` and `git log --oneline origin/main..HEAD`.

## 2. The November 14 forward-test runbook

**A dry run is not a score.** Only the output of `--score` is a score. Section 2.9 says why a dry run on November 14 is a trap.

### 2.1 The rules that bind the scoring

From the frozen `PREREG.md`, section "Forward tests":

> Scoring uses DefiLlama data fetched on or after 2026-11-14 and the first final RPC block after 2026-11-14 00:00 UTC.
>
> A forward test with missing data is scored "not scorable". It is never estimated.
>
> Every result is published, including misses.

`pipeline/score_forward.py` implements these. Its docstring holds the operational readings of F1-F4 (which field, which rows, which convention), and `python3 -m pipeline.score_forward --help` prints it. The rating rule does not use F1-F4, so no forward result can change the rating (`PREREG.md`, "Rating rule").

### 2.2 What the command does

Run it from the repository root, on or after 2026-11-14 00:00 UTC:

```
python3 -m pipeline.score_forward --score
```

Before that time it prints `refusing to score: it is <UTC now>, scoring opens 2026-11-14T00:00:00Z (PREREG.md).` to stderr, exits with status 2, makes no request and writes nothing (run on 2026-11-07 in a scratch copy). That refusal belongs to the live command: `--score --from-snapshot DIR` does not read the clock (2.3 uses it for the rehearsal). After that time it fetches seven sources, one after another, with no key (the seventh is about two dozen RPC calls, by reading the code):

| # | Source | Used for | Address |
|---|---|---|---|
| 1-4 | DefiLlama `dailyVolume` of `near-intents`, `thorchain-dex`, `chainflip-amm`, `maya-protocol` | F3 (near-intents only), F4 (all four) | `https://api.llama.fi/summary/dexs/<slug>?dataType=dailyVolume&excludeTotalDataChartBreakdown=true` |
| 5 | DefiLlama `dailyRevenue` of `near-intents` | F3 | `https://api.llama.fi/summary/fees/near-intents?dataType=dailyRevenue&excludeTotalDataChartBreakdown=true` |
| 6 | Nearblocks charts (`total_supply` per day) | F2 | `https://api.nearblocks.io/v1/charts` |
| 7 | NEAR archival RPC, FastNEAR first, then near.org | F1: a binary search over block heights for the first block whose header timestamp is at or after 2026-11-14T00:00:00Z, then `view_account` of `buybacks.multisignature.near` at that height | `https://archival-rpc.mainnet.fastnear.com`, `https://archival-rpc.mainnet.near.org` |

It then writes two files into `data/forward/score_<stamp>/`, where `<stamp>` is the script's start time as `YYYYMMDDTHHMMSSZ`: `snapshot.json` (the raw fetches, about 2 MB) and `result.json`. It prints four lines, `F1:` to `F4:`, each with `PASS`, `MISS` or `not scorable` and the key values, then `wrote <path>`.

- **Exit status 0 only means the script finished.** It is 0 even when a test is `not scorable`. Read the four lines.
- **Runtime.** The normal case takes seconds to about a minute. A dry run on 2026-11-07, which makes the same requests, reached every host from a cloud sandbox and took only a few seconds. In the code, each HTTP request is tried up to 5 times, with waits of 2, 4, 6, 8 and 10 seconds and a 90-second limit per try. Each RPC call is tried 3 times on each of the two endpoints. A host that is down can hold the script for several minutes before the failure is recorded. If nothing has printed after 15 minutes, press Ctrl-C and run again.
- **Rate limits.** NEAR's provider table lists `archival-rpc.mainnet.near.org` as "Severely rate limited" and FastNEAR's free endpoint as archival "Paid Only" ([source](https://docs.near.org/api/rpc/providers.md)). The scorer tries `archival-rpc.mainnet.fastnear.com` first, which that table does not list. It answered test calls on 2026-11-07. If both archival endpoints refuse on the day, F1 is `not scorable` (section 2.6).
- **Do not use `--out`.** The dashboard and the tests look only in `data/forward/score_*/`.

### 2.3 Before November 14

**Step 1. Bring the finished work to `main`, push it, and get CI green.** Section 3 has the order. The two workflows have never run on GitHub: the first run has not been observed, so allow time to fix a first-run problem (a missing permission, a version) before you rely on a green mark.

**Step 2. Fix the scoring procedure now, and commit it.** PREREG leaves open when to run the scorer and whether to run it again after a failed fetch. Write the answer in an addendum entry before any window data is scored (template in 2.8a). Fixing it before you see a result removes the discretion.

**Step 3. Rehearse in a scratch clone.** This runs scoring from a fixture snapshot, the render, the checks and the tests, without touching your repository. The input is the repository's own committed snapshots with a fake fetch time. Nothing it prints is a score. Delete the folder afterwards.

```
git clone . /tmp/rehearsal            # run from the repository root
cd /tmp/rehearsal
python3 - <<'PY'
import json, sys
from pathlib import Path
sys.path[:0] = [".", "tests"]
import test_score_forward as t        # the repository's own fixture builder
d = Path("data/forward/score_20261114T060000Z"); d.mkdir(parents=True)
(d / "snapshot.json").write_text(json.dumps(t.repo_snapshot(fetched_at="2026-11-14T06:00:00Z"), indent=1))
PY
python3 -m pipeline.score_forward --score --from-snapshot data/forward/score_20261114T060000Z
python3 -m pipeline.render
python3 -m pipeline.render --check
python3 -m unittest discover -s tests
```

The scoring command prints four lines. F1 says `MISS` (the fixture carries the committed 2026-11-04 balance, which is outside the band) and F2 to F4 say `not scorable` because the fixture ends on 2026-11-04. `render --check` should print `render: site/ matches a fresh render`. Run this only in the scratch clone and delete it afterwards: in `--from-snapshot` mode the scorer does not read the clock, and the fixture's fetch time is a made-up 2026-11-14, so the folder it writes has `is_score` true and the dashboard draws it as a real score. Rehearsed again on 2026-11-08 in a throwaway clone of `a1fe2e6`: the four lines above, `render --check` failing before `python3 -m pipeline.render` and passing after it, and the suite ending `Ran 145 tests` and `OK` with the fixture score present. The scorer takes a snapshot's recorded times on trust, which is why a rehearsal folder must never stay in your real checkout.

**What a scored result does to the tests (checked 2026-11-08).** The render tests no longer depend on what is under `data/forward/`: `test_page_sections_and_scorecard` runs over fixture variants, `test_pending_without_a_scored_result` builds from an empty forward directory, and `test_the_live_page_ties_to_the_committed_score_if_there_is_one` follows whichever state is committed. So with a real score present the suite passes once the page is re-rendered. Until then `render --check` and `test_committed_site_is_current` fail, by design: that is the reminder to render and commit `site/index.html` with the score (2.5 D and F).

**Step 4. Check the machine you will use, on November 12 or 13.** Python 3.10 or newer, a correct clock, and the four hosts answering:

```
python3 --version
date -u
for u in "https://api.llama.fi/summary/dexs/near-intents?dataType=dailyVolume" https://api.nearblocks.io/v1/charts https://archival-rpc.mainnet.fastnear.com https://archival-rpc.mainnet.near.org; do curl -s -o /dev/null -m 25 -w "%{http_code} $u\n" "$u"; done
```

Any code other than `000` means the host answered. A plain GET to the two RPC roots returns `405`, and that is normal. `curl` does not use Python's network stack, so also run the scorer's own code path once, into a scratch folder:

```
python3 -m pipeline.score_forward --dry-run --out /tmp/dryrun_check
```

It prints `DRY RUN ON CURRENT DATA - NOT A SCORE OF F1-F4`. Its values are not a score and are never quoted. If every fetch fails with a certificate error, the machine's Python cannot verify TLS certificates; on macOS with a python.org installer, the `Install Certificates.command` that ships with it is the usual fix (UNVERIFIED here). Delete `/tmp/dryrun_check` afterwards. Do this only on a day before November 14 (see 2.9).

**Step 5. Check your push credential.** Both workflow files say that pushing `.github/workflows/*.yml` may need a credential with the `workflow` scope (a classic personal access token with that scope, or a fine-grained token with the Workflows permission). If your first push is refused, that is the likely reason (not verified here).

**Step 6. Do not run `--dry-run` on November 14.** See 2.9.

### 2.4 The day, in UTC

If you are on UTC-6 (the commit timestamps show -06:00), subtract six hours: 06:00 UTC is 00:00 local and 18:00 UTC is 12:00 local. If midnight is a problem, start at 12:00 UTC (06:00 local). The 18:00 hard stop stays.

| UTC | Step | Done when |
|---|---|---|
| 00:00 | Scoring opens. Do not run the scorer yet: the sources may not have published 2026-11-13. In the 2026-11-05 snapshot (fetched 22:51 UTC) the DefiLlama series for NEAR Intents, THORChain and Maya ended on 2026-11-04, while the Chainflip series already had a row for 2026-11-05. So a day appears with a lag, and the lag differs by series. How long it is, is UNVERIFIED. | nothing to do |
| 05:30 | Pre-flight (2.5 A). | every check passes, tree clean |
| 06:00 | Run the scorer (2.5 B). Target start. Latest start 12:00. | four result lines and `wrote …` |
| 06:10 | Read and verify (2.5 C). | summary read; the offline re-score differs only in `scored_at`; F1 matches the RPC |
| 06:30 | Decide. All four scorable: scoring is finished. Any `not scorable` from a fetch error or a missing day: apply your rule from 2.8a (suggested: re-run no sooner than 60 minutes after the previous run; the last run starts by 14:00). | decision noted |
| 07:00 | Write the addendum entry (2.8b), update `README.md` and `THESIS.md`, render (2.5 D). | entry stamped with `date -u` at the time of writing |
| 09:00 | Checks, commit, push (2.5 E and F). Latest 16:00. | push done |
| 09:30 | CI green, Pages deploy finished, live address loads (section 3). | green check and HTTP 200 |
| 12:00 | Demo post live with video or screenshots (section 5). Latest 19:00. | post URL copied |
| 16:00 | Submit (section 6). Target. | confirmation shown |
| 18:00 | **Hard stop for repository changes.** After this, change nothing unless the build is broken. | |
| 20:00 | **Latest time to submit.** This leaves 3 hours 59 minutes of buffer. | |
| 23:59 | The form closes. | |

If a source never recovers by the last allowed run, the test stays `not scorable`. That is a result: publish it and carry on. Do not wait for the deadline to see whether a host comes back. Whether commits after 23:59 UTC count is UNVERIFIED; read `HACKATHON.md`.

### 2.5 Commands

**A. Pre-flight (05:30 UTC).**

```
date -u
git status -sb                                   # ## main...origin/main and nothing else
python3 -m pipeline.check --manifest             # check: PASS
python3 -m pipeline.check --numbers              # check: PASS
python3 -m unittest discover -s tests            # ends with: OK (skipped=1)
sha256sum PREREG.md                              # 19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240
git diff prereg-freeze -- PREREG.md              # prints nothing
ls data/forward 2>/dev/null                      # prints nothing: no folder yet, and no dry-run_* folder
```

On macOS use `shasum -a 256 PREREG.md`. The test run ends `OK (skipped=1)` from 2026-11-14 00:00 UTC, because the refusal test skips itself.

**B. Score (06:00 UTC).**

```
python3 -m pipeline.score_forward --score
```

Copy the terminal output into your notes. It is also in `result.json`.

**C. Read and verify (06:10 UTC).** Replace `<stamp>` with the folder name that `wrote` printed.

```
ls data/forward/score_<stamp>                    # result.json  snapshot.json
python3 - data/forward/score_<stamp>/result.json <<'PY'
import datetime, glob, json, sys
path = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob("data/forward/score_*/result.json"))[-1]
r = json.load(open(path))
print("file:", path)
print("mode:", r["mode"], "| is_score:", r["is_score"], "| scored_at:", r["scored_at"], "| snapshot_fetched_at:", r["snapshot_fetched_at"])
print("fetch_errors:", json.dumps(r["fetch_errors"]))
for k in ("F1", "F2", "F3", "F4"):
    x = r["results"][k]
    line = f"{k}: {x['result']}"
    if x["result"] != "not scorable":
        if k == "F1":
            t = datetime.datetime.fromtimestamp(x["block_timestamp_ns"] / 1e9, tz=datetime.timezone.utc).isoformat()
            line += f" | balance {x['balance_near']:,.2f} NEAR | block {x['block_height']} {x['block_hash']} at {t}"
        elif k == "F2":
            line += f" | mean {x['mean_near_per_day']:,.1f} NEAR/day over {x['n_deltas']} daily deltas"
        elif k == "F3":
            line += f" | {x['take_rate_bp']:.3f} bp | revenue ${x['revenue_usd']:,.0f} / volume ${x['volume_usd']:,.0f}"
        else:
            line += f" | Intents share {x['intents_share_pct']:.2f}% | " + ", ".join(f"{v} ${s:,.0f}" for v, s in x["volume_usd_by_venue"].items())
    else:
        line += f" | why: {x['why']}"
    print(line)
PY
```

This prints the values to copy into the addendum. Copy them from this output, not from memory. The forward results are not in `data/metrics.json`, so `check --numbers` cannot catch a mistyped one.

Re-score offline from the saved snapshot, in a copy. `--from-snapshot` writes `result.json` into the folder you give it and ignores `--out`, so never point it at the committed folder:

```
cp -r data/forward/score_<stamp> /tmp/rescore_check
python3 -m pipeline.score_forward --score --from-snapshot /tmp/rescore_check
diff data/forward/score_<stamp>/result.json /tmp/rescore_check/result.json    # one line differs: scored_at
```

Read F1 independently from the chain. It needs no key. `<BLOCK_HEIGHT>` is the block height in the F1 line of the summary:

```
curl -s -X POST https://archival-rpc.mainnet.fastnear.com -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":"x","method":"query","params":{"request_type":"view_account","block_id":<BLOCK_HEIGHT>,"account_id":"buybacks.multisignature.near"}}'
curl -s -X POST https://archival-rpc.mainnet.fastnear.com -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":"x","method":"block","params":{"block_id":<BLOCK_HEIGHT>}}'
```

`result.amount` divided by 10^24 must equal `balance_near`. `result.header.timestamp_nanosec` must be at least 1794614400000000000, which is 2026-11-14T00:00:00Z. `sources.rpc_f1.data.prev_block_timestamp_ns` in `snapshot.json` must be below it. Both calls ran on 2026-11-07 against a block already in the repository, and the balance matched the committed value.

**D. Update the repository (07:00 UTC).**

*D1.* Append the entry from 2.8b to the end of `PREREG-ADDENDUM.md`. Take the heading time from `date -u '+%Y-%m-%d %H:%M'` at the moment you write, not from your local clock. An earlier heading used the local date and needed a correction entry.

*D2.* Replace the "pending" statements. Find them with `grep -n -i -E "pending|F1-F4|forward" README.md THESIS.md`. On 2026-11-08 they are: in `README.md`, the status line near the top, the "Forward tests F1-F4 are pending" paragraph in its Summary, the "Forward tests F1-F4" row of its "Trace a headline number" table and the forward-test bullet under "Integrity rules"; in `THESIS.md`, the row "The forward tests" in the table of section 5 (the row "A pending resolver" resolves on 2026-11-16, not on the 14th). Then refresh the outputs that the re-rendered page and the new commit change in the README's "Try it" table: step 6 (the page's byte count; the data fingerprint is the hash of `data/MANIFEST.json`, which scoring does not change) and step 9 (the blob and commit counts), and step 4's test count if the number of tests changed. Keep the hedges: the scorer was written after the window opened, and a missing input is `not scorable`, never estimated. Do not edit existing addendum entries or `PREREG.md`.

*D3.* Rebuild the page:

```
python3 -m pipeline.render
python3 -m pipeline.render --check
```

The page reads only the newest `data/forward/score_*/result.json` whose `is_score` is true and whose `mode` is `score`. Dry-run output is never read.

**E. Check (09:00 UTC).**

```
python3 -m pipeline.check --manifest             # check: PASS
python3 -m pipeline.check --numbers              # check: PASS
python3 -m unittest discover -s tests            # OK (skipped=1)
git diff prereg-freeze -- PREREG.md              # prints nothing
git status --short                               # only: data/forward/score_*/, PREREG-ADDENDUM.md, README.md, THESIS.md, site/index.html
```

**F. Commit and push.** Add files by name, so that a stray folder cannot slip in.

```
ls data/forward                                  # delete any dry-run_* folder first
git add data/forward PREREG-ADDENDUM.md README.md THESIS.md site/index.html
git commit -m "Forward tests F1-F4 scored: results, addendum entry, dashboard"
git push
```

Commit every `score_*` folder, including a run with errors. Then watch the Actions tab: the CI workflow runs on every push, and the Pages workflow runs when `site/**` changes.

### 2.6 When something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| `refusing to score: it is …` and exit status 2 | The clock is before 2026-11-14 00:00 UTC. Nothing was fetched or written. | Check `date -u`. Wait. |
| `snapshot F1 target is not 2026-11-14T00:00:00Z; refusing` (only with `--from-snapshot`) | The snapshot was not made for the real target. A dry-run snapshot always lands here (tested). | Use the folder of a real `--score` run. |
| A test says `not scorable` with `missing days {…}` or `Nearblocks total_supply missing for […]` | A source has no row for some window days. F2 needs 2026-11-05 to 2026-11-13. F3 needs revenue and near-intents volume for 2026-11-06 to 2026-11-13. F4 needs all four volume series for the same days. | PREREG: not scorable, never estimated. Apply your rule from 2.8a. If you have none, publish it as is. |
| F3 or F4 says `not scorable` with `DefiLlama fetch missing or fetched before 2026-11-14` or `a DefiLlama peer fetch is missing…` | A DefiLlama request failed after its retries. The error text is in `fetch_errors`. | Same. |
| F1 says `not scorable` with an RPC error | Both archival endpoints failed or were rate limited, or the final head was not yet past the target time. | Same. Do not add RPC endpoints to the script without writing it into the addendum first. |
| A traceback, exit status 1, or you pressed Ctrl-C | No `result.json`. A `score_<stamp>` folder may exist, empty or with only `snapshot.json`. | Delete an empty folder. Keep a folder that has `snapshot.json` and no `result.json` (it is the raw record), say so in the addendum, and never write `result.json` by hand. Run again. |
| All four lines say `not scorable` and the exit status is 0 | Exit 0 means only that the script ended. Typical cause: no network. | Fix the network. Run again under your rule. |
| A value sits exactly on a band edge | Bands are inclusive and compared on unrounded values. | Publish as printed. |
| The page still says pending after `render` | `render` reads only the newest `score_*/result.json` with `is_score` true and `mode` `score`. | Check that the folder name starts with `score_`, that you used `--score`, and that no newer folder is in the way. |

### 2.7 What to commit afterwards

| Path | Why |
|---|---|
| `data/forward/score_*/` (all of them) | The raw record and the results, errors included. |
| `PREREG-ADDENDUM.md` | The new dated entry. Append only. |
| `site/index.html` | The page rebuilt by `python3 -m pipeline.render`. CI fails if it is stale. |
| `README.md`, `THESIS.md` | The "pending" statements replaced, and README steps 6 and 9 refreshed (page bytes; blob and commit counts). `python3 -m pipeline.check --numbers` must still pass. |
| `docs/ANCHOR.md` | Only if you anchor `PREREG.md` (section 4). |

### 2.8 Entry templates for `PREREG-ADDENDUM.md`

No numbers are pre-filled. Angle brackets are yours to fill. A number that exists in `data/metrics.json` needs its marker, an HTML comment `<!--n:…-->` that holds the metric key and sits directly after the number. The forward results do not exist there, so they take no marker.

**a. Before scoring (commit on November 12 or 13).**

```
## <YYYY-MM-DD HH:MM> UTC: how the forward tests will be scored on 2026-11-14 (written before any window data is scored)

This fixes the procedure before scoring opens. It changes no hypothesis, threshold, probability or rule in PREREG.md.

1. Command: `python3 -m pipeline.score_forward --score`, run from a clean checkout of `main`, no earlier than <06:00> UTC on 2026-11-14. The script allows 00:00 UTC. The later time is chosen so that the sources have had time to publish 2026-11-13. It is a choice about timing, not about the test.
2. If a test is "not scorable" because a request failed or a source had not yet published a window day, the command may be run again, no sooner than <60> minutes after the previous run, and no run starts after <14:00> UTC. If all four tests are scorable, scoring stops. A test that is still "not scorable" at the last run stays "not scorable". It is never estimated.
3. Every run is committed under data/forward/score_<stamp>/, including runs with errors. The newest run is the result of record, and the entry that reports it lists every run.
4. pipeline/score_forward.py is not edited before scoring. If it must be, the change is disclosed in an entry before the next run.
5. A dry run is not a score and is not used to decide whether or when to score.
6. Results are published whatever they are.
```

**b. After scoring.**

```
## <date -u '+%Y-%m-%d %H:%M'> UTC: forward tests F1-F4 scored

Written at the time in the heading, after the run(s) below and after the results were read. It changes no hypothesis, threshold, probability or rule in PREREG.md. The rating rule does not use F1-F4.

**Runs.** The newest is the result of record.
- data/forward/score_<stamp>/: started <scored_at>, sources fetched <snapshot_fetched_at>. Fetch errors: <none | paste fetch_errors>. Result of record: <yes | no>.
- <one line per further run>

**Procedure.** <As committed in the entry dated <date time> UTC: every rule followed | list each deviation and why>.

| Test | Prediction as frozen (PREREG.md, verbatim) | Prior | Result | Observed |
|---|---|---|---|---|
| F1 | <paste> | <p> | <PASS / MISS / not scorable> | <balance> NEAR at block <height>, hash <hash>, block time <UTC> |
| F2 | <paste> | <p> | <PASS / MISS / not scorable> | mean <value> NEAR a day over <n> daily deltas |
| F3 | <paste> | <p> | <PASS / MISS / not scorable> | <value> bp = revenue $<sum> / volume $<sum> |
| F4 | <paste> | <p> | <PASS / MISS / not scorable> | Intents share <value>% of the four-venue volume |

Not scorable, and why: <paste "why" from result.json | none>.

**Re-checks.** Offline re-score from snapshot.json: <identical except scored_at | differed: describe>. F1 read independently by RPC at the recorded block: <matched | differed>. pipeline/score_forward.py unchanged since commit <git log -1 --format=%h -- pipeline/score_forward.py>. PREREG.md SHA-256 unchanged: <yes>.

**What changed in the write-up.** <Name the sentences in README.md and THESIS.md that moved from "pending" to the result.> Misses are published as misses. No calibration score is pre-registered; if you add one, label it exploratory.

**Disclosures that still apply.** The predictions were frozen on 2026-11-05. The scorer was written on 2026-11-06, after the window opened (entry 2026-11-06 23:49 UTC, item 7).
```

**c. Sentences for `README.md` and `THESIS.md`.** Replace the "pending" sentences with these, filled from `result.json`. The pass, miss and not-scorable counts are not metrics, so they take no marker. Keep the label "pre-registered" for F1-F4 and keep the disclosure about the scorer.

```
README status line:
> Status, <YYYY-MM-DD>: the offline rebuild passes. H1a, H1b and H1c have results. The forward tests F1-F4 were scored on <YYYY-MM-DD> (UTC); see the addendum entry dated <YYYY-MM-DD HH:MM> UTC.

README Summary, and THESIS.md section 5 (row "The forward tests"):
**Forward tests F1-F4 (pre-registered) were scored on <YYYY-MM-DD> (UTC).** <n> passed, <n> missed and <n> were not scorable. The window was 2026-11-06 to 2026-11-13. `python3 -m pipeline.score_forward --score` scored them as `PREREG.md` words them. The script was written after the window opened, which the addendum discloses. A test with missing data is "not scorable" and is never estimated. The raw fetches and the result are in `data/forward/score_<stamp>/`.
```

### 2.9 A dry run is not a score

`python3 -m pipeline.score_forward --dry-run` writes `data/forward/dry-run_<stamp>/DRY_RUN_result_NOT_A_SCORE.json` with `is_score` false. The page and the tests ignore it, and it is never quoted as a score.

One trap: its window is "the last 8 complete UTC days" and its block target is 00:00 UTC today. **On 2026-11-14 that is exactly the real window and the real block.** A dry run that day computes the same quantities as the score, without the check that the data was fetched after the deadline. Do not run it that day, and do not use one to decide whether to score.

The dry run of 2026-11-07 ran outside the repository, so there is no dry-run folder to delete. Its numbers are not quoted in this document.

### 2.10 Draft addendum entries awaiting approval

Nothing below has been appended to `PREREG-ADDENDUM.md`; the three drafts await your decision. The addendum is append-only: add an entry at the end, with its own dated heading, and do not edit an earlier one. (Five earlier commits did edit nine existing lines; its 2026-11-08 entry lists them, and the text above that entry is pinned by SHA-256 in `tests/test_integrity.py`, so an edit of it fails the tests while an appended entry does not.) After appending, run `python3 -m pipeline.check --numbers` and `python3 -m unittest discover -s tests`. Drafts 1 and 2 contain dates only, no metric values; Draft 3 is a template with blanks that only you can fill.

**Draft 1 (recommended): a second scorer dry run read one day of the forward window.** Item 7 of the 2026-11-06 23:49 UTC entry says the scorer's dry run read no day inside 2026-11-06..13 for F2-F4. That was true of the first dry run. A second dry run, on 2026-11-07, did read one such day. The dashboard's forward-test card repeats the item 7 wording, so once you approve the entry, ask for the card's sentence to be reworded to point at both entries.

```markdown
## 2026-11-07 18:15 UTC: disclosure: a second scorer dry run read one day of the forward window

On 2026-11-07, at about 18:15 UTC, an AI coding assistant working in this repository ran `python3 -m pipeline.score_forward --dry-run` once, to check that the scorer works end to end against the live sources. A dry run covers the last 8 complete UTC days. On that date that was 2026-10-30 to 2026-11-06, which includes 2026-11-06, the first day of the pre-registered window (2026-11-06 to 2026-11-13). So, unlike the dry run described in item 7 of the 2026-11-06 23:49 UTC entry, this one read one day inside the window for F2 to F4. Its F1 reading was the buyback wallet balance at the first block after 2026-11-07 00:00 UTC, which is also inside the window. The scored F1 quantity is the balance at the first final block after 2026-11-14 00:00 UTC.

The output was written outside the repository and was not committed. It is not a score of F1-F4 and is not quoted anywhere in this repository. The assistant read it and told the owner, in summary form, that the F4 reading was below the 50% line over those 8 days. Seven of those 8 days precede the window.

After the run nothing was changed: no band, probability, threshold, rating rule, test or script. Scoring is unchanged: `python3 -m pipeline.score_forward --score`, on or after 2026-11-14 00:00 UTC. A dry run is never used to decide whether or when to score.
```

Check before appending: the run time (18:15 UTC is the file time of the dry-run output) and that the sentence about what the owner was told matches what you remember. Edit freely; it is your record.

**Draft 2 (optional): F2 depends on how many epoch starts fall in the window.** This is an observation made after the freeze. It changes no test. Disclosing it before scoring shows the band was not reverse-engineered, and it explains the likely outcome either way.

```markdown
## 2026-11-0X: note on F2 (no change to the test)

F2's frozen band is 86.0K to 89.5K NEAR a day, 3.5K wide. Over the 8-day window that is about 28K NEAR in total, roughly one epoch's mint. NEAR mints once per epoch, and a UTC day holds three or four epoch starts (committed data: `data/raw/rpc/epoch_issuance.json`). The 8-day mean net supply increase therefore moves in steps of about one epoch's mint, depending on how many epoch starts fall inside 2026-11-06 to 2026-11-13. F2 can pass only if that count lands in a narrow range. This was noticed on 2026-11-07, after the freeze and after the window opened. It changes no band, probability or rule, and F2 will be scored exactly as PREREG.md words it.
```

Replace `0X` with the real date. If you want a number in it (for example the share of historical 8-day windows whose mean fell inside the band), a committed script must compute it from the committed data, so that `check --numbers` and a judge can reproduce it. Ask for that first and it can be added to `pipeline/compute.py`.

**Draft 3 (needs your knowledge): when the earlier analysis was done, and the BigQuery jobs behind H1a.** The 2026-11-08 entry says only that the repository cannot show these two things. You can. This draft states nothing for you: every blank is yours, fill one only if it is true, and delete a bullet you cannot support instead of guessing. If a blank turns out to contradict the README or `THESIS.md`, correct them in the same commit.

```markdown
## <YYYY-MM-DD HH:MM> UTC: dates the repository could not record (owner's statement)

Written by the repository owner from their own records, at the time in the heading. It changes no hypothesis, threshold, probability or rule.

1. **The earlier analysis of the 14 accounts** (`docs/supply-side.md` section 2, `THESIS.md` section 4). It was done from <date time UTC> to <date time UTC>, which is <before | after> the freeze (2026-11-05 22:53:29 UTC). It used <RPC only | BigQuery | both>. It <did | did not> inform the prior of 0.70 for H1a.
2. **BigQuery jobs behind H1a.** The job history of the billing project shows the job behind `sql/staking_flows_daily.sql` as <job ID>, created <time UTC>, and the job behind `sql/staking_pool_totals_endpoints.sql` as <job ID>, created <time UTC>. The earliest job on `crypto_near_mainnet_us` in that history is <job ID>, created <time UTC>, which is <before | after> the freeze. Retrieved on <date> with <command or console page>.
```

How to get item 2 (UNVERIFIED: not run, the sandbox has no BigQuery access): `bq ls -j -a -n 100 --format=prettyjson`, with `-n` raised until it reaches back to 2026-11-05, or the job history in the BigQuery console of the billing project. A job ID such as `bqjob_r140d347f6f05de25_000001a1b321c86a_1` embeds its creation time in the second hex field, in milliseconds since the Unix epoch. This prints `2026-11-06 23:11:38.090000+00:00` (run on 2026-11-08; that job is the sweep preview in the addendum entry of 2026-11-06 23:23 UTC):

```
python3 -c "import datetime,sys; print(datetime.datetime.fromtimestamp(int(sys.argv[1],16)/1000, datetime.timezone.utc))" 000001a1b321c86a
```

How long the job history reaches back is UNVERIFIED. If the earliest H1a job precedes 2026-11-05 22:53:29 UTC, the claim that `PREREG.md` was frozen before any BigQuery flow query had run is false and the README must say so: its Summary, "Integrity rules" and "Pre-registration" now say only that the freeze was two minutes before the first BigQuery result the repository records, which would stay literally true but mislead; the dashboard has similar wording; and `PREREG.md` line 20 ("We had not run any query on staking-pool flows, exchange deposits or Intents event logs") would be wrong and cannot be edited, so the entry itself must say so. If item 1 shows the earlier analysis preceded the freeze, say that too, for the same reason.

## 3. Making the repository public and hosting the dashboard

Order matters: set the email, bring the work to `main` without this file, push, take the working branch off GitHub, rehearse, scan, then flip visibility, then enable Pages.

**Step 1. Email first** (section 1). The new work is already committed, so set the address before the one commit you make in step 2: `git config user.email "<your GitHub noreply address>"`.

**Step 2. Bring the work to `main` without this file, push it, and take the working branch off GitHub.**

*2a. Merge.* The work is on the branch `claude/near-hackathon-dashboard`, and this file is in that branch's history (added in `552c63b`; no other commit touched it before 2026-11-08). A normal merge would put it into `main`'s history for good, so squash. Commit or stash any change on the branch first, then:

```
git fetch origin
git switch main
git merge --ff-only 32c3136
git merge --squash origin/claude/near-hackathon-dashboard
git rm -f --cached SUBMISSION.md
echo SUBMISSION.md >> .git/info/exclude
git commit -m "Dashboard, tooling, thesis and documentation (squashed from claude/near-hackathon-dashboard)" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

What each line does. `git merge --ff-only 32c3136` moves `main` forward to the last commit before this file existed (`c86a876` to `32c3136`, none touching it), so those hashes survive; every commit hash that the README, `THESIS.md`, the docs and the addendum cite is at or before `32c3136` (checked 2026-11-08). `git merge --squash` stages everything after `32c3136` as one change. `git rm -f --cached SUBMISSION.md` takes this file out of that change and leaves your copy on disk. The `.git/info/exclude` line keeps it out of `git status` and `git add -A` on this machine only; do not use `.gitignore` for it, which is committed and would publish the name. The commit carries the `Co-Authored-By: Claude` trailer because the README says every commit does.

What `main` loses: the per-commit history from `552c63b` to the branch tip, which becomes the one squash commit. Check the result:

```
git ls-files | grep -c SUBMISSION                                   # 0
git diff --name-status origin/claude/near-hackathon-dashboard main  # only: D  SUBMISSION.md
git log --format=%B | grep -ic '^co-authored-by: claude'            # equals the output of: git rev-list --count HEAD
git status -sb                                                      # ## main...origin/main [ahead 5]
```

Tested on 2026-11-08 in a throwaway clone of the real repository at `a1fe2e6`, with these commands: the first printed 0, the second printed only `D` and the file name `SUBMISSION.md`, the trailer count equalled the commit count (34), and on that `main` the manifest check, the numbers check, `render --check`, the 145 tests and `fresh_clone_check.sh` (13 of 13) all passed. `git push` and the rest of this section were not run.

*Alternative: squash everything, no fast-forward.* Leave out the `git merge --ff-only 32c3136` line (also tested). Then no `Claude-Session:` trailer reaches `main` (the four commits that the fast-forward keeps are the only ones on `main` that carry one: 4 against 0), but `a2414f8`, which the 2026-11-08 addendum entry cites, does not exist in a clone of `main` (`git cat-file -t a2414f8` says "Not a valid object name"). Decide in section 8, item 21. Whatever you choose, cite only hashes at or before `32c3136` in anything you add later.

*2b. Push.* `git push origin main`. If GitHub refuses because the push adds `.github/workflows/*.yml`, your credential probably lacks the `workflow` scope (section 2.3, step 5). Check that the tag is there too: `git ls-remote --tags origin 'prereg-freeze^{}'`. Then open the Actions tab and read the result of `ci.yml`: its first run on GitHub has not been observed, and nothing in the repository claims a CI result.

*2c. Take the working branch off GitHub, before step 5.* `git push origin --delete claude/near-hackathon-dashboard`. When a repository becomes public, all its branches do, and this branch holds this file and every `Claude-Session:` trailer in its history. Keep your local branch. UNVERIFIED: whether GitHub keeps serving the commits of a deleted branch by their hash for a while. If you need certainty, make a new repository from `main` and push the tag `prereg-freeze` to it: every hash cited in the documents survives, but the address in the README, on the dashboard and in this file changes.

**Step 3. Rehearse what a judge does.** From `main`, `bash scripts/fresh_clone_check.sh` clones your `HEAD` into a temporary folder, runs the offline steps with no network, and prints a PASS/FAIL table. Uncommitted work is not in it. Expect `RESULT: PASS`.

**Step 4. Scan the history again.** `python3 scripts/scan_secrets.py --history`. Expect `scan_secrets: PASS`.

**Step 5. Make it public.** On the repository page open Settings. In the "Danger Zone" section choose "Change repository visibility", then "Change visibility", pick public and confirm ([GitHub docs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility)). Those docs list what changes: the code is visible to everyone, anyone can fork it, Actions history and logs become visible to everyone, and stars and watchers are erased. After this, assume everything in the history is copied.

**Step 6. Enable Pages.** In Settings choose "Pages" (under "Code, planning, and automation"). Under "Build and deployment", set "Source" to **GitHub Actions** ([GitHub docs](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)). Pages is available for public repositories on a free plan. Whether your plan allows it for a private one is UNVERIFIED, so do this after step 5.

**Step 7. Start the first deployment.** `.github/workflows/pages.yml` runs on a push that changes `site/**`, and it has a manual trigger. If you enabled Pages after the push that added `site/`, nothing starts by itself: open the Actions tab, choose "Pages", then "Run workflow". GitHub says a change can take up to 10 minutes to appear. The run page links to the deployed site.

**Step 8. Check it as a stranger would.** In a private browser window, open the repository, then the dashboard. Then run:

```
curl -sI https://notveiker.github.io/near-flow-statement/ | head -1                    # expect a 200 status line
git ls-remote --tags https://github.com/notveiker/near-flow-statement 'prereg-freeze^{}'   # expect 413d776164a4…
bash scripts/fresh_clone_check.sh https://github.com/notveiker/near-flow-statement
```

If `git ls-remote` asks for a password, the repository is still private. On the dashboard, click one "Query" link. It opens a file on GitHub, which works only once the repository is public.

**Step 9. Add the README line** only after step 8 shows a 200, and delete the README sentence that says no hosted address is claimed:

```
**Hosted dashboard:** <https://notveiker.github.io/near-flow-statement/>, the same file as `site/index.html`, published by `.github/workflows/pages.yml`.
```

The address has the form `https://<user>.github.io/<repository>/` ([GitHub docs](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)), so with the account and repository names unchanged it is `https://notveiker.github.io/near-flow-statement/`. Confirm it from the link on the workflow run page before you publish it anywhere.

**Why make it public before November 14.** The demo post needs a working link. A judge's tooling may look early. And the scoring push on November 14 would then be made in public. GitHub documents a public events feed for repositories that lists pushes ([GitHub docs](https://docs.github.com/en/rest/activity/events)), so GitHub, not your clock, would hold the push time. What that feed shows for a repository that was private earlier is UNVERIFIED.

## 4. Optional: anchor `PREREG.md` on NEAR mainnet

**The problem.** The frozen `PREREG.md` says: "the SHA-256 of this file is published on NEAR mainnet (see `docs/ANCHOR.md` once anchored)". `docs/ANCHOR.md` does not exist and nothing was published. The README already says so. A reader of `PREREG.md` alone meets a claim that is not met. Leaving that unaddressed is the one wrong choice. Two honest ones follow.

**What an anchor can and cannot show.**

- It can show that the file existed with exactly these bytes no later than the anchor's block time, as published by the holder of the signing key. Anyone can check that without trusting you.
- It cannot show that the file existed before the BigQuery queries. An anchor made now comes after H1a (2026-11-05), after H1b and H1c (2026-11-06 23:23 UTC), and after the ladder was built (2026-11-06) and made the headline (2026-11-07). For the order before the queries, the evidence is the git tag `prereg-freeze` (which has the same timestamp as its commit), the commit order and the manifest stamps. You control all of them: git timestamps are written by the committing machine, and nothing outside the repository timestamps the freeze. Say so plainly.
- It does add one thing if made before 2026-11-14 00:00 UTC: the text of F1-F4 and of the rating rule is fixed before scoring, independent of git. It does not predate the forward-test window, which opened on 2026-11-06.

### 4a. Anchor it now

You sign on your own machine. No private key, seed phrase or keychain content goes through an agent, a chat or the repository.

**Step 1. Confirm the digest.** `sha256sum PREREG.md` (macOS: `shasum -a 256 PREREG.md`) must print `19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240`.

**Step 2. Choose the signing account.** It is a mainnet account. The transaction is public and links that account to this project. Using the payout account is allowed, and is your call.

**Step 3. Rehearse on testnet.** Install the NEAR CLI ([docs](https://docs.near.org/tools/cli.md)). Use SocialDB's testnet contract `v1.social08.testnet` ([docs](https://docs.near.org/primitives/social.md)).

**Step 4. Send one mainnet transaction that carries the digest in its function-call arguments.** The documented route is SocialDB, a contract deployed at `social.near` that stores key-value data under the signer's account ([docs](https://docs.near.org/primitives/social.md), [contract README](https://raw.githubusercontent.com/NearSocial/social-db/master/README.md)). In words: call its `set` method as your account, with one argument, `data`, an object whose only top-level key is your account ID. Under that key put any nested keys you like, with string values: the digest, the tag name and the commit hash. Attach a small deposit. The contract README says `set` is payable and that a write under your own account needs permission or at least 1 yoctoNEAR attached. The amount is yours to choose; no documented minimum was found.

**UNVERIFIED: the exact command was not run.** The form below is assembled from the NEAR CLI docs and from the SocialDB README. Its shape matches the `as-transaction` example in the CLI guide ([near-cli-rs](https://github.com/near/near-cli-rs/blob/main/docs/GUIDE.en.md)), which uses `testnet`; the same guide uses `network-config mainnet` in its read-only example, so `mainnet` is a valid name (list the names with `near config show-connections`). Check each part against the linked pages, and run it on testnet first.

```
near contract call-function as-transaction social.near set \
  json-args '{"data":{"<ACCOUNT>":{"near_flow_statement":{"prereg_sha256":"19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240","git_tag":"prereg-freeze","git_commit":"413d776164a42ddb2b1288bb02bd7bd112bc7f06"}}}}' \
  prepaid-gas '100.0 Tgas' attached-deposit '0.01 NEAR' \
  sign-as <ACCOUNT> network-config mainnet sign-with-keychain send
```

The same docs page describes the `near-social-js` SDK in TypeScript. Configuring its signer is not covered there (UNVERIFIED).

**Step 5. Copy the transaction hash.** The CLI guide's example output prints it as `Transaction ID`.

**Step 6. Check it as a stranger would.** This code ran on 2026-11-07 against a different mainnet transaction and printed the method, the arguments and the block time. Here it prints the full arguments:

```
python3 - <<'PY'
import base64, datetime, json, urllib.request
RPC = "https://archival-rpc.mainnet.fastnear.com"
def call(method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": "x", "method": method, "params": params}).encode()
    req = urllib.request.Request(RPC, body, {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))["result"]
TX, SIGNER = "<TX_HASH>", "<ACCOUNT>"
r = call("tx", {"tx_hash": TX, "sender_account_id": SIGNER, "wait_until": "FINAL"})
for a in r["transaction"]["actions"]:
    if "FunctionCall" in a:
        print("method:", a["FunctionCall"]["method_name"])
        print("args:", base64.b64decode(a["FunctionCall"]["args"]).decode())
b = call("block", {"block_id": r["transaction_outcome"]["block_hash"]})
t = datetime.datetime.fromtimestamp(int(b["header"]["timestamp_nanosec"]) / 1e9, tz=datetime.timezone.utc)
print("block height:", b["header"]["height"], "| block time (UTC):", t.isoformat())
PY
```

The `tx` method and its parameters are in the NEAR RPC docs ([transactions](https://docs.near.org/api/rpc/transactions.md)). The response fields used here (`transaction.actions[].FunctionCall.args`, base64, and `transaction_outcome.block_hash`) are in the [schema](https://docs.near.org/api-reference/post-tx.md).

**Step 7. Record it.** Write `docs/ANCHOR.md` from the draft below and append the addendum entry under it. Change the last bullet under the README's "Integrity rules", the one that says no anchor exists. `python3 -m pipeline.check --numbers` also reads `docs/*.md`, so add no unmarked metric number there. Commit and push.

**Draft `docs/ANCHOR.md`.** Fill the blanks after the transaction is final.

```
# On-chain anchor of PREREG.md

**What was anchored.** The SHA-256 of `PREREG.md`:
`19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240`.
This is the file at git tag `prereg-freeze` (commit `413d776`).

**Where.** NEAR mainnet. Signing account: `<ACCOUNT>`. Transaction: `<TX_HASH>`.
Block height: `<HEIGHT>`. Block time (UTC): `<TIME>`. Anchored on <DATE> UTC.

**Check it yourself** (no key needed).
1. `sha256sum PREREG.md` (macOS: `shasum -a 256 PREREG.md`) prints the hash above.
2. Ask a mainnet RPC node for the transaction: method `tx`, parameters `tx_hash`,
   `sender_account_id` and `wait_until` ("FINAL"). The function-call arguments
   (base64) contain the hash. See https://docs.near.org/api/rpc/transactions.md.
3. Ask for the block named in `transaction_outcome.block_hash` (method `block`)
   and read `header.timestamp_nanosec`. That is the block time.

**What this proves.** `PREREG.md` existed with exactly these bytes no later than
the block time above, and the holder of the signing key published its hash.

**What this does not prove.** It does not prove that `PREREG.md` was frozen before
the first BigQuery query ran. The anchor was made on <DATE>, after the H1a result
(2026-11-05), after the H1b and H1c results (2026-11-06) and after the exploratory
ladder was built (2026-11-06) and made the headline (2026-11-07). The evidence for
the order of events before that is the git tag `prereg-freeze`, the commit order and
the manifest stamps. The repository owner controls all of them: git timestamps are
written by the committing machine, and nothing outside the repository timestamps them.

**Why it is still useful.** <If made before 2026-11-14 00:00 UTC:> It fixes the text
of the forward-test predictions F1-F4 and of the rating rule before the forward tests
were scored. It does not predate the forward-test window, which opened on 2026-11-06.

`PREREG.md` is frozen. Its sentence "the SHA-256 of this file is published on NEAR
mainnet (see docs/ANCHOR.md once anchored)" was written on 2026-11-05, before any
anchor existed. This page and the addendum entry dated <DATE> record when it was done.
```

**Addendum entry for 4a.**

```
## <YYYY-MM-DD HH:MM> UTC: PREREG.md anchored on NEAR mainnet

The SHA-256 of PREREG.md, 19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240, was published in mainnet transaction <TX_HASH> (block <HEIGHT>, <TIME> UTC) from account <ACCOUNT>. docs/ANCHOR.md says how to check it and what it does and does not show. It was done after the H1a, H1b and H1c results, so it does not show that PREREG.md was frozen before the first BigQuery query ran. It changes no hypothesis, threshold, probability or rule.
```

### 4b. Record that it was not done

Append this to `PREREG-ADDENDUM.md`. Leave the README bullet as it is, since it already says there is no anchor.

```
## <YYYY-MM-DD HH:MM> UTC: PREREG.md was not anchored on NEAR mainnet

PREREG.md says its SHA-256 "is published on NEAR mainnet (see docs/ANCHOR.md once anchored)". That was not done. There is no docs/ANCHOR.md and no transaction is claimed. PREREG.md is frozen and that sentence cannot be edited, so this entry corrects the record. The hash is stated in README.md, and the git tag prereg-freeze (commit 413d776) points at the file itself. Nothing is published outside the repository. The evidence for the order of events around the freeze is the tag, the commit order and the manifest stamps (the freeze commit is 2026-11-05 22:53:29 UTC, and the first BigQuery result the repository records is stamped 22:55:37 UTC in data/MANIFEST.json). The repository owner controls all of them, and nothing outside the repository timestamps them.
```

**Which one.** 4a adds one narrow fact that anyone can check, and needs a testnet rehearsal, one mainnet transaction and a funded account. 4b is one paragraph of text and needs no key. Either is honest. Decide by 2026-11-12, because 4a is worth most before scoring. Note that item 6 of the 2026-11-08 addendum entry already records that `PREREG.md` "has not been anchored" and that there is no `docs/ANCHOR.md`, so 4b mostly repeats it (section 8, item 17).

## 5. Demo assets

The organizers' item is: "Your demo post is live on X, says you built it at NEAR HACKATHON, and has a video or screenshots attached". UNVERIFIED: any hashtag or handle that `HACKATHON.md` asks for, X's current limits on length and media, and how X counts a link. Every claim here is in `THESIS.md` or the README. Add nothing about price, and do not call the result a signal. Say "will be scored" until the scores exist.

### 5.1 One post, at most 280 characters

The counts in this section were made by script on 2026-11-08 and include every character of each post, the `N/ ` prefix included. Each post is given as: the raw count, with the link written out in full (the safe count), and the count under the rule that X counts every link as 23 characters (UNVERIFIED: the rule is from memory and the sandbox could not check it). All posts are plain ASCII. The `[n]` marks are counted as they stand, and a digit is shorter than a mark.

**Variant A, before the forward tests are scored** (271 raw, 246 with a link counted as 23):

```
Built at NEAR HACKATHON: a pre-registered flow statement for NEAR. So far: H1a failed, H1b and H1c inconclusive, the frozen rule says Hold. Forward tests will be scored Nov 14. The checks run offline. Not financial advice. https://github.com/notveiker/near-flow-statement
```

**Variant B, after scoring.** Replace each `[n]` from `result.json` (count the `PASS`, `MISS` and `not scorable` results). Do not fill it before scoring. (267 raw, 242 with a link counted as 23.)

```
Built at NEAR HACKATHON: a pre-registered flow statement for NEAR. H1a failed, H1b and H1c inconclusive, the frozen rule says Hold. Forward tests F1-F4: [n] passed, [n] missed, [n] not scorable. The checks run offline. https://github.com/notveiker/near-flow-statement
```

Attach the video from 5.3 or at least three screenshots from 5.4.

### 5.2 Longer version: a thread of five

Characters per post, raw / with a link counted as 23: 1 = 271 / 271, 2 = 275 / 275, 3 = 276 / 276, 4 = 230 / 230, 5 = 276 / 251. Every post is at least 4 characters under 280 on the raw count. Post 4 has a placeholder; write `pending` or the results.

```
1/ Built at NEAR HACKATHON (Investment Thesis). Who buys and who sells NEAR? Tests frozen at commit 413d776, two minutes before the first BigQuery result the repo records (git and manifest times are the author's own). Failures are published. Research, not advice. Thread:

2/ Pre-registered, 90 days to 2026-11-04. H1a (most staking rewards stay staked) fails: net staking outflow was 6.56x rewards. H1b/H1c (exchange flows) are inconclusive: only 20.0% of top-100 receivers carry an exchange label, 10.0% a cited one. Hold says nothing about NEAR.

3/ Exploratory, chosen after the freeze: over 30 days, the NEAR delivered to NEAR's three Intents revenue wallets equalled 15.81% of net issuance. 4.53 points trace to public fee collectors; 11.25 come from the Confidential Intents escrow, fee stream unattested. No valuation.

4/ Forward tests F1-F4 (window Nov 6-13) will be scored after Nov 14 00:00 UTC by a script that refuses a live run earlier. Misses will be published. Status: [pending | fill in from data/forward/score_*/result.json after scoring].

5/ Check it, no keys or network: python3 -m pipeline.check --manifest, then python3 -m pipeline.compute, then python3 -m pipeline.check --numbers, then open site/index.html. Python standard library only. Built with Claude Code. https://github.com/notveiker/near-flow-statement
```

Post 4 after scoring (211 raw, 211 with a link counted as 23, before you replace the `[n]` marks):

```
4/ Forward tests F1-F4 (window Nov 6-13), scored Nov 14 by a script that refuses a live run earlier: [n] passed, [n] missed, [n] not scorable. Misses are published. Details: PREREG-ADDENDUM.md in the repository.
```

Numbers in the thread, with their keys in `data/metrics.json`: 6.56<!--n:h1a_ratio_as_written_x-->× (post 2, written `x`), 20.0<!--n:h1b_coverage_count_pct-->% and 10.0<!--n:h1b_coverage_tier1_count_pct-->% (post 2), 15.81<!--n:ladder_all_wallets_pct_of_issuance-->%, 4.53<!--n:ladder_public_collectors_pct_of_issuance--> and 11.25<!--n:ladder_escrow_unshields_pct_of_issuance--> points (post 3). `python3 -m pipeline.check --numbers` does not read this file, so compare them with `data/metrics.json` before posting. "50%" is the threshold fixed in `PREREG.md`; 413d776 is the freeze commit; "two minutes" is the gap between its time (2026-11-05 22:53:29 UTC) and the manifest stamp of the first BigQuery result (22:55:37 UTC). "Built with Claude Code" matches the README's disclosure; whether to say it is your decision (section 8).

### 5.3 Silent video, about three minutes

Built around `site/index.html`, opened from disk or from the hosted address. The page follows the system colour scheme, has no script, and each chart card has "What it shows", "What it does not show", and "Query" and "Data" blocks that open. The section and card names below are the ones on the page of 2026-11-07. **Confirm them against the final page before you record.** Captions are burned-in text; there is no audio.

| Time | Show | Caption |
|---|---|---|
| 0:00-0:12 | Top of the page: the title and the scorecard heading. | "Who buys and who sells NEAR? Pre-registered. Checkable offline. Research, not financial advice." |
| 0:12-0:35 | Section "Scorecard (pre-registered)": the five tiles. | "Tests were frozen at commit 413d776, two minutes before the first BigQuery result the repository records (git and manifest times are the author's own). These are the results as they came out." |
| 0:35-1:00 | Card "H1a: staking outflow". Open "Query" and "Data". | "H1a fails: net staking outflow was 6.56<!--n:h1a_ratio_as_written_x-->× staking rewards. A pass needed under 0.5×." |
| 1:00-1:25 | Cards "H1b: net exchange inflow" (both panels: the range, then coverage against 50%) and "H1c: identified buying". | "Inconclusive: 20.0<!--n:h1b_coverage_count_pct-->% of top receivers carry an exchange label, 10.0<!--n:h1b_coverage_tier1_count_pct-->% a cited one. The pre-registration needs 50%." |
| 1:25-1:40 | Card "Rating rule inputs". | "The frozen rule outputs Hold. That carries no view on NEAR." |
| 1:40-2:00 | Card "Forward tests F1-F4". | "Will be scored after 2026-11-14 00:00 UTC by a script that refuses a live run earlier. Misses will be published." Re-shoot after scoring and change the caption to the result. |
| 2:00-2:30 | Section "Exploratory (chosen after the freeze)": card "The value-capture ladder". | "Exploratory. The NEAR delivered to the revenue wallets equalled 15.81<!--n:ladder_all_wallets_pct_of_issuance-->% of net issuance. 4.53<!--n:ladder_public_collectors_pct_of_issuance--> points trace to public fee collectors; 11.25<!--n:ladder_escrow_unshields_pct_of_issuance--> come from the escrow, unattested." |
| 2:30-2:45 | A terminal: `python3 -m pipeline.check --manifest`, `python3 -m pipeline.compute`, `git status --short`. | "Every number recomputes offline from committed snapshots. No keys, no network. (The snapshots themselves need credentials to refresh.)" |
| 2:45-3:00 | End card: repository address, hosted dashboard address. | "Built at NEAR HACKATHON." |

Cards you can add if there is time: the network-usage card (`chart-usage`: Nearblocks active accounts and transactions, with the 2026-04-02 step), "Escrow share by month", "NEAR's take in 1Click", "Partner concentration", "Who keeps the fees", "Share of the peer set", "Monthly revenue and take rate", "Supply and net issuance". Record at a fixed window size, and zoom the browser so captions are readable on a phone. Check X's current video limits for your account (UNVERIFIED).

### 5.4 Screenshots to capture

1. The scorecard row at the top, desktop width, light theme.
2. The same, dark theme.
3. The scorecard at phone width (browser device mode).
4. The H1a card: chart, "What it shows" and "What it does not show".
5. The H1b card: panel A, the range around the minted amount, and panel B, label coverage against the required 50%.
6. The "Forward tests F1-F4" card: pending before scoring, scored after.
7. The ladder card, with its "Exploratory, chosen after the freeze" label in view.
8. Any card with "Query" and "Data" open, to show that every chart names its source.
9. A terminal with the three README commands, showing `check: PASS`, `wrote data/metrics.json …` and a clean `git status --short`.
10. A terminal with `git tag -n` and `sha256sum PREREG.md`, showing the freeze.
11. After scoring: the new addendum entry on GitHub, or the scored forward-test card.
12. The public repository page with a green CI mark, and the hosted dashboard in a browser tab.

Attach the video, or at least three of these. Write alt text that states the finding in a sentence.

## 6. Submission payload draft

The field names are a draft of what a submission needs, taken from `SUBMITTING.md` and the checklist. **The form (<https://nearhackathon.com/#apply>) and the submission API (in `HACKATHON.md`) were not reachable from the sandbox. Every field name, length limit and format below is UNVERIFIED.** Read <https://nearhackathon.com/HACKATHON.md> before you submit and fix this table to match it. This document contains no step that sends the payload, and none should be taken by an agent: `SUBMITTING.md` says an agent "must show you the full payload and wait for your OK before it sends anything". There is one submission per team and it cannot be edited after it is sent.

| Field | Draft | State |
|---|---|---|
| Project name | `near-flow-statement` | UNVERIFIED |
| One line | A pre-registered token flow statement for NEAR, recomputable offline from committed snapshots, and the investment thesis built on it. H1a failed, H1b and H1c were inconclusive, and the frozen rating rule outputs Hold, which carries no view on NEAR. | UNVERIFIED (limit unknown) |
| Short description | Question: who buys and who sells NEAR? The tests were frozen at commit 413d776, two minutes before the first BigQuery result the repository records (git and manifest times are the author's own; nothing external attests them), and results are published as they come, misses included. H1a fails (6.56<!--n:h1a_ratio_as_written_x-->× staking rewards), H1b and H1c are inconclusive (20.0<!--n:h1b_coverage_count_pct-->% of top receivers carry an exchange label, 10.0<!--n:h1b_coverage_tier1_count_pct-->% a cited one; 50% required), and the frozen rule outputs Hold, which carries no view on NEAR. An exploratory ladder, labelled as chosen after the freeze, shows that the NEAR delivered to NEAR's Intents revenue wallets equalled 15.81<!--n:ladder_all_wallets_pct_of_issuance-->% of net issuance: 4.53<!--n:ladder_public_collectors_pct_of_issuance--> points trace to public fee collectors and 11.25<!--n:ladder_escrow_unshields_pct_of_issuance--> points arrived as unshields from the Confidential Intents escrow, whose fee stream is unattested. No valuation is made. The checks and the recomputation of every number run offline from committed snapshots with the Python standard library; the snapshots themselves need credentials to refresh. | UNVERIFIED (limit unknown) |
| Track(s) | `thesis` (Investment Thesis). Possibly `open` (Open Innovation). See below. | UNVERIFIED (form) |
| Repository URL | <https://github.com/notveiker/near-flow-statement> (must be public) | owner action |
| Dashboard URL | <https://notveiker.github.io/near-flow-statement/> (after section 3) | owner action |
| Demo post URL | _blank_ | owner action |
| Team lead | _blank_ | owner fills |
| Contact email | _blank_ (the address the organizers should use; it need not be your git address) | owner fills |
| Team size | _blank_ | owner fills |
| Payout mainnet account | _blank_ (copy from your wallet) | owner fills |
| AI assistance | Built with Claude Code under the owner's direction; disclosed in the README ("Timeline and disclosure"). | UNVERIFIED (whether the form asks) |
| Try-it steps, if asked | `git clone https://github.com/notveiker/near-flow-statement`, then `python3 -m pipeline.check --manifest` (expect `check: PASS`), `python3 -m pipeline.compute` (expect `wrote data/metrics.json …` and no change in `git status --short`), `python3 -m pipeline.check --numbers` (expect `check: PASS`), then open `site/index.html`. | matches the README |

**Tracks.** The organizers' track ids and briefs are in `nearai/near-hackathon-prompt-examples` (fetched 2026-11-07); there are 13.

- `thesis` fits by construction. The README's "Track brief" table maps the brief line by line.
- `open` ("Something we haven't seen"): its brief says you can enter it alongside any other track, since the form lets you pick every track your project fits. The brief asks for "new ways for money, intelligence and ownership to work together". A pre-registered research repository is a stretch for that wording. Adding it costs nothing if the form allows it, and a poor fit may cost credibility. Your decision.
- `privacy` (Privacy & Private AI): the escrow work concerns a privacy feature's auditability, but the project builds no private computation. Not recommended.
- The other ten tracks are build tracks (DeFi, agents, games and so on) and do not fit.

The owner decides. UNVERIFIED: whether the live form lets you select more than one.

## 7. Risks and weak points a judge may raise

Each row is a weak point visible in the repository itself, with the short answer and where the repository says it. The answers on the ladder's order, the escrow evidence, the forward-test disclosure, the freeze timing, the earlier analysis, the Hold and G_req were rewritten on 2026-11-08, because a review of the repository's own history showed that the earlier answers claimed more than the history supports. The last five rows are weak points that review added. Several are best said before a judge finds them.

| What a judge may say | Short answer | Where |
|---|---|---|
| Two of the three pre-registered flow tests are inconclusive, and the headline result is not pre-registered. | `THESIS.md` leads with the scorecard: H1a fails (6.56<!--n:h1a_ratio_as_written_x-->× rewards), H1b and H1c are inconclusive, the rule outputs Hold. The ladder is labelled exploratory (chosen after the freeze) and does not feed the rating rule. Do not say it was chosen after all three flow results. Its code was first committed at 2026-11-06 23:19:20 UTC (`51e396b`), before the H1b/H1c and H1a-as-written results were committed, and it became the headline at 2026-11-07 00:21 UTC. Say so first. | `THESIS.md`, first paragraph; `PREREG-ADDENDUM.md`, entries 2026-11-07 00:21 UTC and 2026-11-08 |
| Only 20.0<!--n:h1b_coverage_count_pct-->% of the top-100 receivers carry an exchange label, against 50% required. | That is why H1b and H1c are ranges. Only 10.0<!--n:h1b_coverage_tier1_count_pct-->% carry a cited label; the rest are labelled by our own sweep rule (say "carry an exchange label"; do not call the labels "citable"). The binding gap is labelling, not data: no citable NEAR address was found for OKX, Coinbase, Kraken, Bybit, HTX, Crypto.com, Upbit or Bithumb. More code does not close it; sourced labels would. | `docs/supply-side.md`; addendum, entry 2026-11-06 23:23 UTC |
| H1a fails, so what is the thesis? | H1a is reported as a fail, not hidden. The thesis in `THESIS.md` is about how much value capture can be verified, not about stakers holding. The scorecard says that, net of deposits, stakers withdrew far more than they earned (this includes exchange-owned stake moving, which is not a sale), in a price rally, and that NEAR is fungible, so nothing says who sold. Adding `lst-pool.near` gives 5.96<!--n:h1a_ratio_with_lst_pool_x-->× (post hoc), still a fail. | `docs/supply-side.md`; addendum, entry 2026-11-06 23:49 UTC |
| Partner and channel numbers rest on one key-gated source. | True. The Explorer API needs a partner key. The repository commits hash-checked daily aggregates and a sample of 195<!--n:fee_ev_swaps_n--> swaps, from 3<!--n:fee_ev_hours_with_swaps_n--> sampled hours, whose on-chain legs anyone can re-read without a key (`python3 -m pipeline.fetch_fee_evidence trace`). Nobody without a key can re-pull the aggregates. "Partners are paid their listed fee on chain" is a statement about that sample only. | `THESIS.md` Limits; README "What this does not show"; `docs/partner-concentration.md` Limits |
| The escrow story is inferred, and partly sampled. | Arrival is on chain and re-checkable: in the 30-day window all 909<!--n:escrow_funded_exact_30d_n--> deliveries are recorded as funded by the escrow for the exact amount. Which fee stream funds the escrow is unattested, so the headline is a range and the falsifier is named. Funding before 2026-10-06 is attributed from samples; from that date it is traced per delivery. Limits to state yourself: the committed on-chain re-check (`data/raw/escrow/verify_sample.json`) covers a seeded sample of 60 rows, not all 909 (`python3 -m pipeline.fetch_escrow verify --all` checks every row); and the SQL of the October funding scan is not committed. "909 of 909" (`escrow_funded_exact_30d_n` over `escrow_single_use_30d_n`) is computed by `escrow_ladder` from the delivery table's own `funder` and `exact_amount_flag` columns, and the table has no writer in `pipeline/`, so the 100.0% restates how the table was built and is not an independent test. The independent part is the on-chain re-check; `verify --all` on 2026-11-08 is recorded in `docs/sources-checked.md`, section 3 (ten rows differ from the chain in block height by 1 to 3 blocks, and nothing else fails). | `THESIS.md` sections 1-2 and Limits |
| The forward tests may miss, and the scorer was written after the window opened. | Both are disclosed. The predictions were frozen first. The scorer's operational readings were written before it was run on window data, and its first dry run read no day inside the window for F2-F4; a second dry run on 2026-11-07 read one such day, which Draft 1 in section 2.10 discloses once you approve it. A missing input is "not scorable", and misses will be published. F3's sensitivity was disclosed in advance. | addendum, entries 2026-11-06 01:11 UTC and 23:49 UTC (item 7); docstring of `pipeline/score_forward.py` |
| How do we know `PREREG.md` was frozen before the queries? | Do not say "before any BigQuery query". Say: frozen at commit `413d776` (2026-11-05 22:53:29 UTC), two minutes before the first BigQuery result the repository records (22:55:37 UTC in `data/MANIFEST.json`). The commit, tag and manifest times are written by the author's machine, and the tag has the same timestamp as its commit, so it adds no independent evidence. BigQuery job IDs, which embed their creation time, are recorded only for H1b/H1c and the October escrow scan, not for the H1a queries. No on-chain anchor exists yet (section 4). | README "Integrity rules"; addendum, entries 2026-11-06 23:23 UTC and 2026-11-08 (item 4) |
| Some supply-side statements rest on an earlier analysis that is not in the repository. | `docs/supply-side.md` section 2 and `THESIS.md` section 4 refer to an earlier analysis of 14<!--n:unstakers_a14_n--> accounts. Both label it exploratory and not a PREREG test. The repository holds its output, `data/raw/unstakers/account_set.json`, stamped 2026-11-06 23:50:01 UTC (after the freeze), and `pipeline/compute.py` computes the arithmetic from it: 42.87<!--n:unstakers_a14_net_outflow_m-->M NEAR, 90.7<!--n:unstakers_a14_share_of_net_outflow_pct-->% of the pools' 47.3<!--n:pool_net_outflow_90d_m-->M NEAR net outflow. The extraction behind its `net_diff` values is not in the repository, and the repository does not record when the analysis was done or whether it informed H1a's prior. Only you know (Draft 3, section 2.10). `THESIS.md` Limits says it is not reproduced here. | `docs/supply-side.md`; `THESIS.md` Limits; README "Timeline and disclosure"; addendum, entry 2026-11-08 (item 5) |
| The rating rule can never output Avoid at low label coverage, so the Hold is forced. | Recorded before the results: with coverage below 50%, H1b can come out pass or inconclusive, never fail, so Avoid is unreachable. Say the rest before a judge does: observed growth (619.0<!--n:rating_g_obs_pct-->% a year) is far above the Avoid line (16.6<!--n:rating_g_avoid_line_pct-->% a year), so even a failed H1b would have given Hold. The rule could only ever have output Buy or Hold, and the Hold carries no view on NEAR. | addendum, entry 2026-11-06 23:11 UTC, item 6; `THESIS.md`, first paragraph |
| G_req assumes HSP-029, whose timelock clears on 2026-11-16, after the deadline. | PREREG fixes the ramp's target and a constant price. The other constants (price level, 24-month ramp, activation date, horizon) were committed after the freeze, in the same commit as the as-written H1a result (`9ee9082`), and `THESIS.md` says so. The rule's output is Hold whatever G_req is, because H1b is inconclusive. Without HSP-029, G_req would be 46.8<!--n:rating_g_req_no_hsp029_pct-->% instead of 33.2<!--n:rating_g_req_pct-->%. | addendum, entry 2026-11-06 23:49 UTC, items 5-6; `THESIS.md` sections 4 and 5 |
| The brief says "live dashboards"; this one is static and as of 2026-11-04. | By design: no script, nothing loaded from another host, every number traces to committed data, and it opens from disk. Each card prints its as-of date. The README's track-brief table says it is not a live feed. | README "Track brief"; `site/index.html` |
| The repository was mostly written by an AI. | Disclosed in the README. Every commit carries the `Co-Authored-By: Claude` trailer (39 up to `a1fe2e6`; the squash commit you make carries it too). The numbers do not depend on who wrote the code: they recompute offline, and a script checks the marked prose against them. | README "Timeline and disclosure" |
| There is no hosted dashboard, no video and no X post yet. | True on 2026-11-08. They are owner actions (sections 3 and 5). Do not mention a hosted address, a video or a post before they exist, and do not call the Pages workflow "live" before its first deployment. | section 1, items 1 and 2 |
| The thesis headline is a bound, not a valuation. | Yes, and `THESIS.md` says so: "It is not a valuation." The usable result is that the NEAR that verifiably arrived from Intents was at most about a sixth of issuance. No valuation is made anywhere in the repository. | `THESIS.md`, "The thesis in one paragraph" and section 1 |
| The usage evidence is a Nearblocks aggregate with a step in it. | Daily active accounts averaged 61.6<!--n:active_accounts_30d_k-->K over the 30 days to 2026-11-04, -77.1<!--n:active_accounts_30d_yoy_pct-->% on the same 30 days a year earlier. Daily transactions are -84.8<!--n:tx_per_day_30d_yoy_pct-->% year on year, but most of that is one step between 2026-03-31 and 2026-04-02 that our data cannot explain. Contract usage is not computed, and the brief's BigQuery usage queries were not run: the figures come from Nearblocks charts. | `THESIS.md` section 3 and Limits; dashboard card `chart-usage` |
| Third-party documents are not committed. | The escrow account's identity (`PRIVATE_TREASURY_ACCOUNT_ID`), the Confidential Infrastructure Fee terms, near.com's statement about its fees and HSP-029 rest on pages that this repository does not commit. `docs/sources-checked.md` sets each such statement next to what the page said when it was read on 2026-11-08, with a verdict (match, partly, differs, not found); read it before a judge does, because it shows where the repository's wording is narrower or wider than its source. | `THESIS.md` Limits; README "Data sources and attribution" |
| The timing evidence for H1a is thinner than for H1b and H1c. | True. The H1b and H1c job IDs and times are in the addendum, written before their results; H1a's queries have no job ID, so the order rests on commit and manifest times (freeze 22:53:29 UTC, first result stamped 22:55:37 UTC). Draft 3 (section 2.10) is where you can add the job times, if the job history still shows them. | addendum, entry 2026-11-08 (item 4) |

## 8. Open decisions

One line each. The first four have a date because later answers lose value.

1. Make the repository public now (recommended, so the scoring push is public) or on November 13? Decide by 2026-11-09.
2. Which address will the new commits use: your GitHub noreply address (recommended)? Set it before the squash commit in section 3, step 2.
3. Keep or delete the three "never publish" lines in `.gitignore` (`near-research.md`, `notes/`, `private/`)? They name private files, they are in the first commit, and deleting them changes nothing in history; the recommendation is to keep them.
4. Anchor `PREREG.md` on mainnet (4a) or record that it was not (4b)? Decide by 2026-11-12.
5. If 4a: which account signs, and is it the payout account?
6. Adopt the scoring procedure in 2.8a, with these times (start 06:00 UTC, re-runs 60 minutes apart, last run by 14:00 UTC), and commit it before November 14?
7. Start scoring at 06:00 UTC (midnight if you are on UTC-6) or at 12:00 UTC?
8. Post the demo before scoring, with a reply on November 14, or once after scoring?
9. Say in the post that it was built with Claude Code? The README already says so.
10. Select `open` as a second track, if the form allows it?
11. This file stays out of `main` (section 3, step 2). Where do you keep your copy: untracked on this machine, or in the working branch only?
12. Leave the data as of 2026-11-04 (recommended) or refresh the snapshots? A refresh changes numbers that the prose quotes and needs the keys and tools listed in the README.
13. Who is team lead, what is the team size, and which email goes on the form?
14. Which mainnet account receives the payout?
15. After you read `HACKATHON.md`: does it add a hashtag, a handle, a form field, or a rule on commits after the deadline? Then update this file.
16. Approve Drafts 1, 2 and 3 in section 2.10, and fill Draft 3's blanks only with what you know to be true? Draft 3 is the only way the repository can learn when the earlier analysis was done and when the H1a queries ran.
17. Item 6 of the 2026-11-08 addendum entry says `PREREG.md` "has not been anchored". Keep it, or reword it if you anchor (4a) before that entry is committed? Once committed, the text above a later entry is pinned, so a later anchor needs its own entry.
18. Media: record the video and take the screenshots (5.3, 5.4). The repository has none, and the post needs a video or screenshots.
19. The brief's BigQuery usage queries (daily active accounts, transaction counts, contract usage) were not run, and the usage figures are Nearblocks aggregates. Run one cheap `block_date`-filtered query through `pipeline.bq_run` (a new file in `sql/`, a new addendum entry, new metrics with markers), or leave it as `THESIS.md` Limits states it?
20. The working branch is on GitHub and holds this file: delete it from origin before going public (section 3, step 2c), or make a new repository from `main`?
21. Which squash variant (section 3, step 2a): fast-forward to `32c3136` first (every cited hash survives; four `Claude-Session:` links stay in `main`'s history), or squash everything (no links; `a2414f8`, cited by the addendum, is missing from `main`)? Keep the `Claude-Session` links at all?

## Sources and limits of this document

Fetched on 2026-11-07:

- Organizers: <https://github.com/nearai/near-hackathon-prompt-examples> (`README.md`, `SUBMITTING.md`, `00-setup.md`, `tracks/*.md`).
- NEAR docs: [`llms.txt`](https://docs.near.org/llms.txt), [create an account](https://docs.near.org/getting-started/create-account.md), [NEAR CLI](https://docs.near.org/tools/cli.md), [RPC providers](https://docs.near.org/api/rpc/providers.md), [RPC transactions](https://docs.near.org/api/rpc/transactions.md), [`tx` reference](https://docs.near.org/api-reference/post-tx.md), [Social](https://docs.near.org/primitives/social.md), [validating recipient accounts](https://docs.near.org/web3-apps/tutorials/account-validation.md); the SocialDB [README](https://raw.githubusercontent.com/NearSocial/social-db/master/README.md); the near-cli-rs [guide](https://raw.githubusercontent.com/near/near-cli-rs/main/docs/GUIDE.en.md). The NEAR Intents docs index ([`llms.txt`](https://docs.near-intents.org/llms.txt)) was reachable; no step here depends on it.
- GitHub docs: repository visibility, Pages publishing source, creating a Pages site, commit email address, blocking pushes that expose it, email addresses reference, events.

Run in a scratch copy of the repository (nothing in the repository was changed by it): the scorer's refusal before the date; an offline re-score from a fixture snapshot and a second re-score of it; a dry-run snapshot refused as a score; the render and the tests with a fixture score present. Run against the live network, read-only: one `view_account` and one `block` call at a block already in the repository, one `tx` call on an existing mainnet transaction, and the four-host reachability loop.

Not verifiable from the sandbox: `HACKATHON.md`, the submission form and API, X's rules, your GitHub plan, your accounts, when DefiLlama and Nearblocks publish a finished day, and the exact CLI command in 4a (its shape is checked against the CLI guide, but it was not run). The scripts, workflows and tests this file mentions were added in the same batch of work as this file. Re-run them yourself before you rely on them.

Revised on 2026-11-08, in throwaway clones of the repository at `a1fe2e6` (nothing in the repository was changed by it): the two squash recipes in section 3 and the offline checks on the result; the 2.3 rehearsal with a fixture score present; a script recount of every post in section 5; the decode of a job-ID timestamp in 2.10; the author, trailer and commit counts in section 1; and a check that every commit hash cited by the README, `THESIS.md`, the docs and the addendum is at or before `32c3136`. Not run: `git push`, `bq ls`, and anything that needs GitHub, BigQuery or X.
