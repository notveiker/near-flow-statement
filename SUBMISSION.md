# Submission package and November 14 runbook

**This is an internal runbook for the repository owner. It must not be merged into `main` or published**; section 3 gives the commands that keep it out, and the first thing to do is copy it out of the repository (Start here). Written on 2026-11-07 (UTC, a Saturday) and revised on 2026-11-08 and 2026-11-10, for NEAR HACKATHON 2026, track `thesis`. It holds no keys, none of your own account IDs and no forward-test result (none exists yet), but it does hold your time zone, your open decisions, draft answers to a judge and draft public statements. If you read only one part, read "Start here" below; the numbered sections are the detail.

**Three facts set the schedule.**

1. Submissions close on Saturday 2026-11-14 at 23:59 UTC. There is one submission per project, and it cannot be edited directly after it is sent: a mistake goes through a request that the organizers review by hand (`HACKATHON.md`, Procedure 4; section 6.2).
2. The forward tests F1-F4 can be scored from 2026-11-14 00:00 UTC. The scorer refuses to run earlier.
3. The repository is private (checked on 2026-11-08). A judge cannot see, clone or check anything until you make it public.

Judging starts on 2026-11-16 and results are announced by 2026-11-18 (`HACKATHON.md`, Facts). Claude Code and Codex screen every project (the organizers' README calls them AI judges), but humans decide and a low AI score alone cannot reject (Q-017).

**Reading the numbers.** Counts in this file (tests, commits, blobs, bytes) were true at the commit named next to them; yours will differ, and that is not an error: only `PASS`, `OK` and `RESULT: PASS` matter. UNVERIFIED means the assistant that wrote this file could not check the statement: test it yourself. Everything else was checked on 2026-11-07 or 2026-11-08 against the repository (by a command run in a scratch copy of it) or on a page fetched that day (list at the end), including the organizers' live `HACKATHON.md` (section 1).

| Section | Contents |
|---|---|
| [Start here](#start-here-the-owners-checklist) | The owner's checklist, by date, with the dangerous moments marked |
| [1](#1-status-against-the-organizers-checklist) | Status against the organizers' checklist, and what the history exposes |
| [2](#2-the-november-14-forward-test-runbook) | The November 14 forward-test runbook |
| [3](#3-making-the-repository-public-and-hosting-the-dashboard) | Making the repository public, and hosting the dashboard |
| [4](#4-optional-anchor-preregmd-on-near-mainnet) | Optional: anchor `PREREG.md` on NEAR mainnet |
| [5](#5-demo-assets) | Demo assets: posts, video shot list, screenshots |
| [6](#6-submission-payload) | Submission payload, sending it (6.1) and what to do after (6.2) |
| [7](#7-risks-and-weak-points-a-judge-may-raise) | Risks and weak points a judge may raise |
| [8](#8-open-decisions) | Open decisions |

## Start here: the owner's checklist

Dates are suggestions, not organizer deadlines; times are UTC. Every command in this file runs from the repository root, the folder that contains `README.md` and `PREREG.md` (`git rev-parse --show-toplevel` prints it). The working branch is `claude/near-hackathon-dashboard`. A fixture is a made-up input used only for a rehearsal. **Careful** marks the moments that overwrite work or cannot be undone.

**Before Monday 2026-11-09: decisions and prerequisites**

- [ ] Copy this file out of the repository now (`cp SUBMISSION.md ~/near-runbook.md`; if the file is not in your folder: `git show origin/claude/near-hackathon-dashboard:SUBMISSION.md > ~/near-runbook.md`) and read the copy; keep any draft video and screenshots you were given outside the repository too (3, step 2a; 5.3).
- [ ] Read the addendum entry of 2026-11-08 02:03 UTC, which the assistant wrote, and confirm each statement as you remember it (section 1).
- [ ] Decide section 8 items 1, 2, 11, 20, 21 (the squash variant) and 23 (DefiLlama's terms): they gate Monday (and 3 and 25 if you will not take the recommendation).
- [ ] Ask the assistant to say the working branch is final; you write down its tip when you squash (3, step 2a).
- [ ] GitHub, Settings, Emails: tick "Keep my email addresses private" and "Block command line pushes that expose my email" (section 1).
- [ ] Prerequisite: Python 3.10 or newer, and a GitHub credential that can push workflow files (3, step 0).
- [ ] Prerequisite: a public (not protected) X account that can upload the video length you choose (5.3, 6.1).
- [ ] Prerequisite: a NEAR mainnet account that you created yourself in a wallet; keep its recovery phrase offline (6, 6.1).
- [ ] Prerequisite: a private text file outside the repository for the payload values and the confirmation (6.1).
- [ ] Prerequisite: a Discord or Telegram handle, in case you must ask for a correction (6.2).
- [ ] Prerequisite: a screen recorder and a caption or video editor; a browser window logged out of GitHub and X (5.3; 3, step 8).
- [ ] Prerequisite: being awake at 06:00 UTC on Saturday, which is midnight in UTC-6 (2.4).

**Monday 2026-11-09: make the repository public** (section 3)

- [ ] Steps 0 and 1: tools, then your commit email.
- [ ] **Careful, step 2a, the squash:** once, only when the branch is final and your copy of this file exists. Afterwards never merge the working branch again; work on `main`.
- [ ] Step 2b: `git push origin main`; in the Actions tab CI should turn green, and a red Pages run is likely and harmless.
- [ ] **Careful, step 2c, deleting the branch:** hold a local copy first, then unset its upstream, and never run `git push` while it is checked out. Do the same for `claude/research-notes`, unless you decide to publish it (section 8, item 26).
- [ ] Steps 3, 3b and 4: rehearse as a judge, check the README's example outputs, scan the history.
- [ ] Section 8 items 23, 26 (the research-notes branch) and 27 (the 1Click terms) settled, and the branch's CI runs dealt with (2c), before step 5.
- [ ] **Careful, step 5, making it public:** assume everything in the history is copied from then on, including the personal email address in your first 29 commits (section 1).
- [ ] Steps 6 to 9: Pages source, first deployment, check as a stranger, the README's hosted line.

**Thursday 2026-11-12**

- [ ] Decide section 8 items 4 to 10 and 16; append Drafts 2, 3 and 4 (2.10) and read the disclosure entry that is already in the addendum (Draft 1); anchor `PREREG.md` (4a) or record that you did not (4b).
- [ ] Write the scoring-procedure entry (2.8a); commit and `git push origin main`; `git status -sb` must show no "ahead" (2.3, step 2).
- [ ] **Careful, the rehearsal (2.3, step 3):** paste the block exactly as shown, from the repository root; it clones your repository into /tmp/rehearsal and works only there. If a folder `data/forward/score_20261114T...` ever appears in your repository, delete it.

**Friday 2026-11-13**

- [ ] Decide section 8 items 13 and 14 (lead name, team size, email, payout account) and write them in your private file (6, 6.1).
- [ ] Record everything except the forward-test clip; write the post (section 5).
- [ ] Check that the payout account exists on chain (6.1); read the live `HACKATHON.md` again (section 1); run the machine check (2.3, step 4; read its dry-run warning first).

**Saturday 2026-11-14, scoring day** (the hour table is in 2.4)

- [ ] 05:30 pre-flight, 06:00 score, 06:10 verify, 07:00 write the entry, 09:00 checks, commit, push (2.5). Do not run `--dry-run` today (2.9).
- [ ] Re-record the forward-test clip with the result; post with the video attached; copy the post's address (section 5).
- [ ] **Careful, the single submission (6.1), about 16:00:** it cannot be edited directly; send it once, when the repository and the post both load logged out.
- [ ] 18:00: no more repository changes unless the build is broken. 23:59: submissions close.

**After you submit** (6.2)

- [ ] Save the confirmation; keep the repository public and the Pages site and the post up and unedited; push nothing; fix a mistake only through the request-changes page.

## 1. Status against the organizers' checklist

Sources: [`SUBMITTING.md`](https://github.com/nearai/near-hackathon-prompt-examples/blob/main/SUBMITTING.md) in `nearai/near-hackathon-prompt-examples` (fetched 2026-11-07) and the live rules, <https://nearhackathon.com/HACKATHON.md> (first read on 2026-11-08 at 01:53 UTC, see `docs/sources-checked.md`; read again at 02:51 and 03:32 UTC: 22,199 bytes, SHA-256 prefix `903794f4b656b456` each time). It says that dates and rules may change, so read it again before you submit. What it adds to the checklist below: the demo post must **tag @NEARProtocol and #NEARHackathon** (optionally also @NearLegion and @NearBuilders) and say the project was built at NEAR HACKATHON; Q-012 says **screenshots are not enough when judges cannot open the demo, so record the video**; the repository stays public through judging and needs a LICENSE file (Q-014; it has one, MIT); the submission is one form entry or one POST that only you may confirm (section 6). Q-001, Q-004 and Q-005 judge work from the 2026-10-19 announcement to 2026-11-14, treat earlier work as baseline and want AI-written code listed in the README: the first commit here is 2026-11-05 22:49:54 UTC and the README lists the AI assistance, so this file found no conflict.

| # | Organizers' item (verbatim) | State | Why |
|---|---|---|---|
| 1 | *The repository is public, and the README has "do X, see Y" steps an AI judge can follow* | **not done** | GitHub reported the repository as private, with no Pages site (API check, 2026-11-07 and again 2026-11-08). The README with its "do X, see Y" table is committed on the working branch, not on `main`. Owner action: section 3, then `bash scripts/fresh_clone_check.sh` to rehearse the judge's steps. |
| 2 | *Your demo post is live on X, says you built it at NEAR HACKATHON, and has a video or screenshots attached* | **owner action** | Nothing is posted. `HACKATHON.md` adds: tag **@NEARProtocol** and **#NEARHackathon**, and (Q-012) attach a video. Drafts, video plan and screenshot list: section 5. The post links the repository, so the repository must be public first. |
| 3 | *You have a mainnet NEAR account for the prize payout, either your own or the team's* | **owner action** | The sandbox cannot see your accounts. Prizes are paid in NEAR (organizers' README). Section 6 has a blank for the account ID: copy it from your wallet, do not retype it (a mistyped account is a common cause of irreversible token loss, [NEAR docs](https://docs.near.org/web3-apps/tutorials/account-validation.md)). If you have none, create one in a wallet yourself: `HACKATHON.md` says never to create or invent one on your behalf. |
| 4 | *You've selected every track your project fits* | **owner action** | At submission: `tracks` is an array of ids, each listed once. `thesis` (Investment Thesis: "Judged on the evidence, not the conviction") fits by the track brief. The API places no restriction on combining `open` with other ids; whether it fits is your call (section 6). |
| 5 | *There are no keys or secrets anywhere in the repo history* | **done as far as scanning can tell; re-run before going public** | Two manual passes over the history (the second on 2026-11-07, over every distinct file version and the current files) found none, and `python3 scripts/scan_secrets.py --history` passed on 2026-11-08 (exit status 0; the blob and commit counts it prints change with every commit and with the branches your clone holds, so only the PASS matters). It is a pattern scan, so a clean result is not proof. Re-run it on the final tree. |
| 6 | *You're submitting before Nov 14, 2026, 23:59 UTC* | **not done** | Plan with buffers: section 2.4. Submit by 20:00 UTC at the latest. |

### What the history exposes once the repository is public

- **Your email address.** The 29 commits up to `38e1c4c` carry your name and a personal email address as author and committer (`git log --format='%an <%ae>' | sort | uniq -c` lists them); the later commits from the Claude Code session carry the assistant's name and an Anthropic noreply address. Anyone who clones the public repository can read all of it. It is personal data, not a secret.
- **The old commits cannot be fixed.** Rewriting history would change every hash after the edit and break the tag `prereg-freeze` (`413d776`), the commits the addendum cites and the README. GitHub keeps commits made before you change your email tied to the old address ([source](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/setting-your-commit-email-address)).
- **New commits can be protected.** On GitHub, Settings, Emails: tick "Keep my email addresses private" and "Block command line pushes that expose my email" ([source](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/blocking-command-line-pushes-that-expose-your-personal-email-address)). For accounts created after 2017-07-18 the noreply address is `ID+USERNAME@users.noreply.github.com` ([source](https://docs.github.com/en/account-and-profile/reference/email-addresses-reference)). The first commit you will make is the squash commit of section 3, step 2 (the README edits of steps 3b and 9, the addendum entries and the scoring commit follow): set the address (section 3, step 1) before it and keep it set.
- **The trailers.** Every commit carries `Co-Authored-By: Claude`; the README discloses it, so the squash commit must carry it too (section 3, step 2), while later commits need not (the README's statement is dated 2026-11-08). **The 29 commits up to `38e1c4c` name a model version in that trailer** (`git log 38e1c4c --format=%B | grep -ic opus` prints 29); the README says so without naming it. They stay under both squash variants; only a new repository with rewritten history removes them, which would change every hash the documents cite (section 8, item 25). The commits made from the Claude Code session also carry a `Claude-Session:` trailer with a claude.ai link; who can open that page is UNVERIFIED, and the README says only that some commits carry such a trailer.
- **The three "never publish" lines in `.gitignore`** (`near-research.md`, `notes/`, `private/`) are in the first commit (`a2cb97c`); deleting them changes nothing in history, and the README and `THESIS.md` already say that prior work exists outside the repository. Leaving them is the recommendation (section 8, item 3).
- **The addendum entry of 2026-11-08 02:03 UTC was written by the assistant.** From `git log` and `data/MANIFEST.json` it records what the history shows against the earlier story: the ladder was built before two of the three pre-registered results were committed; five commits changed nine lines of an addendum called append-only; the H1a timing rests on the author's own clock; the 14-account work is undated; `PREREG.md` is not anchored. Read it before the repository goes public and confirm each statement as you remember it. Once public, an edit of it is an integrity problem: correct it with a new dated entry (also if you anchor, section 4a, which makes its item 6 untrue).
- **The tag is on GitHub:** `git ls-remote --tags origin 'prereg-freeze^{}'` prints `413d776164a42ddb2b1288bb02bd7bd112bc7f06`.
- **State of the work (2026-11-08).** The new work is committed on the branch `claude/near-hackathon-dashboard` and pushed to GitHub (check with `git ls-remote --heads origin`); `main` and `origin/main` are still at `38e1c4c`. A judge sees only what is on the public branches. **That branch's history contains this file (added in `552c63b`), the `Claude-Session:` trailers and its CI runs, and every branch becomes public with the repository, so the branch must come off GitHub first (section 3, step 2c).** Since 2026-11-10 a second branch is on GitHub: `claude/research-notes`, an orphan branch that holds only a `research/` folder (the research sweep of 2026-11-08, its synthesis and its checks). It shares no history with the working branch or `main`, the squash cannot carry it, and it has no workflow files. CI checks out every branch for its history secret scan, so the notes must keep passing `scripts/scan_secrets.py`; they do, and one line in them carries an allow marker for that reason. The branch must also come off GitHub before the repository goes public, unless you decide to publish it (2c; section 8, item 26).

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

Before that time it prints `refusing to score: it is <UTC now>, scoring opens 2026-11-14T00:00:00Z (PREREG.md).` to stderr, exits with status 2, makes no request and writes nothing. That refusal belongs to the live command: `--score --from-snapshot DIR` does not compare the clock with the cutoff (2.3 uses it for the rehearsal). After that time it fetches, one after another and with no key, five DefiLlama series, the Nearblocks supply chart and the NEAR archival RPC (the last is about two dozen RPC calls, by reading the code):

1. DefiLlama `dailyVolume` of `near-intents`, `thorchain-dex`, `chainflip-amm` and `maya-protocol`, and `dailyRevenue` of `near-intents` (host `api.llama.fi`): F3 uses near-intents only, F4 all four volumes.
2. Nearblocks charts, `total_supply` per day (`api.nearblocks.io`): F2.
3. NEAR archival RPC, FastNEAR first (`archival-rpc.mainnet.fastnear.com`), then near.org (`archival-rpc.mainnet.near.org`): F1, by a binary search over block heights for the first block whose header timestamp is at or after 2026-11-14T00:00:00Z, then `view_account` of `buybacks.multisignature.near` at that height.

It then writes two files into `data/forward/score_<stamp>/`, where `<stamp>` is the script's start time as `YYYYMMDDTHHMMSSZ`: `snapshot.json` (the raw fetches, about 2 MB) and `result.json`. It prints four lines, `F1:` to `F4:`, each with `PASS`, `MISS` or `not scorable` and the key values, then `wrote <path>`.

- **Exit status 0 only means the script finished.** It is 0 even when a test is `not scorable`. Read the four lines.
- **Runtime.** The normal case takes seconds to about a minute. In the code, each HTTP request is tried up to 5 times, with waits of 2 to 10 seconds and a 90-second limit per try, and each RPC call 3 times on each of the two endpoints, so a host that is down can hold the script for several minutes before the failure is recorded. If nothing has printed after 15 minutes, press Ctrl-C and run again.
- **Rate limits.** NEAR's provider table lists `archival-rpc.mainnet.near.org` as "Severely rate limited" and FastNEAR's free endpoint as archival "Paid Only" ([source](https://docs.near.org/api/rpc/providers.md)). The scorer tries `archival-rpc.mainnet.fastnear.com` first, which that table does not list. If both archival endpoints refuse on the day, F1 is `not scorable` (section 2.6).
- **Do not use `--out`.** The dashboard and the tests look only in `data/forward/score_*/`.

### 2.3 Before November 14

**Step 1. Bring the finished work to `main`, push it, and get CI green.** Section 3 has the order. The CI workflow has run on every push to the working branch since 2026-11-07 21:32 UTC, and every run that had finished when checked on 2026-11-08 (`gh run list`) had passed, each on Python 3.10 and 3.13; that is a private repository, and not yet `main`. The Pages workflow has never run: it triggers on a push of `site/` to `main`, or by hand, and needs the repository public (or a plan with Pages for private repositories) and Settings > Pages > Source set to GitHub Actions. Allow time to fix a first-run problem there.

**Step 2. Fix the scoring procedure now, then commit and push it** (`git push origin main`; `git status -sb` must show no "ahead"). PREREG leaves open when to run the scorer and whether to run it again after a failed fetch. Write the answer in an addendum entry before any window data is scored (template in 2.8a). Fixing it before you see a result removes the discretion, and the push matters: an unpushed commit carries only your own clock, while GitHub holds the push time.

**Step 3. Rehearse in a scratch clone.** This runs scoring from a fixture snapshot (a made-up input built from the repository's own committed snapshots, with a fake fetch time), the render, the checks and the tests, in a copy of your repository. Nothing it prints is a score.

**Run this block only as shown. If a folder `data/forward/score_20261114T...` ever appears in your real repository, delete it: the dashboard would draw it as a real score.** The brackets and `set -e` make the block stop at its first failure, so a failed clone cannot make the later lines run in your repository.

```
(
set -e
rm -rf /tmp/rehearsal
git clone -q . /tmp/rehearsal         # run from the repository root
cd /tmp/rehearsal
python3 - <<'PY'
import json, sys
from pathlib import Path
sys.path[:0] = [".", "tests"]
import test_score_forward as t        # the repository's own fixture builder
d = Path("data/forward/score_20261114T000000Z"); d.mkdir(parents=True)
(d / "snapshot.json").write_text(json.dumps(t.repo_snapshot(fetched_at="2026-11-14T06:00:00Z"), indent=1))
PY
python3 -m pipeline.score_forward --score --from-snapshot data/forward/score_20261114T000000Z
python3 -m pipeline.render
python3 -m pipeline.render --check
python3 - <<'PY'
# what 2.5 D2 asks of you on the day: README step 6 quotes the page's byte count, and a test compares it with the page
import re
from pathlib import Path
size = len(Path("site/index.html").read_bytes())
p = Path("README.md")
p.write_text(re.sub(r"site/index\.html \([\d,]+ bytes\)", f"site/index.html ({size:,} bytes)", p.read_text(encoding="utf-8")), encoding="utf-8")
PY
python3 -m unittest discover -s tests
)
rm -rf /tmp/rehearsal
```

The scoring command prints four lines. F1 says `MISS` (the fixture carries the committed 2026-11-04 balance, which is outside the band) and F2 to F4 say `not scorable` because the fixture ends on 2026-11-04. `render --check` prints `render: site/ matches a fresh render`. The next step of the block edits the byte count that README step 6 quotes, as 2.5 D2 asks of you on the day (without that edit the suite ends with exactly one failure, `test_the_byte_count_fingerprint_and_date_the_readme_quotes_are_the_pages`, whose message names the two numbers to write), and the suite then ends `OK`. In `--from-snapshot` mode the scorer does not compare the clock with the cutoff and takes a snapshot's recorded times on trust, and this fixture's fetch time is a made-up 2026-11-14, so the folder it writes counts as a real score (`is_score` true). The folder's stamp, `000000`, sorts before any real run.

**A scored result and the tests.** With a real score present the suite passes once the page is re-rendered and README step 6's byte count is edited. Until then `render --check`, `test_committed_site_is_current` and the README byte-count test fail, by design: they are the reminder to render and commit `site/index.html` with the score and to refresh the README (2.5 D and F). The other render tests build their own fixtures and do not depend on what is under `data/forward/`.

**Step 4. Check the machine you will use, on November 12 or 13.** Python 3.10 or newer, a correct clock, and the four hosts answering:

```
python3 --version
date -u
for u in "https://api.llama.fi/summary/dexs/near-intents?dataType=dailyVolume" https://api.nearblocks.io/v1/charts https://archival-rpc.mainnet.fastnear.com https://archival-rpc.mainnet.near.org; do curl -s -o /dev/null -m 25 -w "%{http_code} $u\n" "$u"; done
```

Any code other than `000` means the host answered. A plain GET to the two RPC roots returns `405`, and that is normal. `curl` does not use Python's network stack, so also run the scorer's own code path once, into a scratch folder:

```
python3 -m pipeline.score_forward --dry-run --out /tmp/dryrun_check > /dev/null
python3 -c "import json; print(json.load(open('/tmp/dryrun_check/DRY_RUN_result_NOT_A_SCORE.json'))['fetch_errors'])"
```

The first command hides everything the scorer prints. The second prints only its fetch errors: `{}` means every fetch worked. Hide the output on purpose: a dry run covers the last 8 complete UTC days and prints F1 to F4 lines, so on 12 or 13 November it reads 6 or 7 days of the real window (2.9), and the 2026-11-06 23:49 UTC addendum entry says the dry run read no such day. The addendum entry of 2026-11-08 05:04 UTC (2.10, Draft 1) discloses the reads the repository has had. Run this once, do not open the result file, delete `/tmp/dryrun_check`, and add this sentence to item 5 of the 2.8a entry: "On <date> the owner ran `--dry-run` once, with its output hidden, to check that the machine can fetch; it read <6 | 7> days of the window and nothing it printed was used." If every fetch fails with a certificate error, the machine's Python cannot verify TLS certificates; on macOS with a python.org installer, the `Install Certificates.command` that ships with it is the usual fix (UNVERIFIED here). To read nothing from live data, skip this command: the loop above checks the hosts and the rehearsal in step 3 checks the code. Do this only on a day before November 14 (see 2.9).

**Step 5. Check your push credential.** Both workflow files say that pushing `.github/workflows/*.yml` may need a credential with the `workflow` scope; section 3, step 0 says how to add it. If your first push is refused, that is the likely reason (not verified here).

**Step 6. Do not run `--dry-run` on November 14.** See 2.9.

### 2.4 The day, in UTC

If you are on UTC-6 (the commit timestamps show -06:00), subtract six hours: 06:00 UTC is 00:00 local and 18:00 UTC is 12:00 local. If midnight is a problem, start at 12:00 UTC (06:00 local). The 18:00 hard stop stays.

| UTC | Step | Done when |
|---|---|---|
| 00:00 | Scoring opens. Do not run the scorer yet: the sources may not have published 2026-11-13, and a day appears with a lag that differs by series (in the 2026-11-05 snapshot, fetched 22:51 UTC, the DefiLlama series for NEAR Intents, THORChain and Maya ended on 2026-11-04 while Chainflip's already had 2026-11-05; how long the lag is, is UNVERIFIED). | nothing to do |
| 05:30 | Pre-flight (2.5 A). | every check passes, tree clean |
| 06:00 | Run the scorer (2.5 B). Target start. Latest start 12:00. | four result lines and `wrote …` |
| 06:10 | Read and verify (2.5 C). | summary read; the offline re-score differs only in `scored_at`; F1 matches the RPC |
| 06:30 | Decide. All four scorable: scoring is finished. Any `not scorable` from a fetch error or a missing day: apply your rule from 2.8a (suggested: re-run no sooner than 60 minutes after the previous run; the last run starts by 14:00). | decision noted |
| 07:00 | Write the addendum entry (2.8b), update `README.md` and `THESIS.md`, render (2.5 D). | entry stamped with `date -u` at the time of writing |
| 09:00 | Checks, commit, push (2.5 E and F). Latest 16:00. | push done |
| 09:30 | CI green, Pages deploy finished, live address loads (section 3). | green check and HTTP 200 |
| 10:00 | Re-record the forward-test card from the live page with the result in its caption (5.3), export, check the length against X's limit, write the alt text (5.4). Target 11:30. | final video and alt text ready |
| 12:00 | Demo post live with the video attached (section 5; screenshots alone only if the hosted dashboard is live and loads, Q-012). Latest 17:00. | post URL copied |
| 16:00 | Submit (6.1), once the repository and the post both load logged out. Target. | confirmation shown |
| 18:00 | **Hard stop for repository changes.** After this, change nothing unless the build is broken. | |
| 20:00 | **Latest time to submit.** This leaves 3 hours 59 minutes of buffer. | |
| 23:59 | Submissions close (the API answers 403). | |

If you start at 12:00 UTC instead of 06:00, move the rows from 05:30 to 09:30 six hours later (11:30, 12:00, 12:10, 12:30, 13:00, 15:00, 15:30), re-record straight after, post by 17:00 and submit by 19:00. The latest times (push 16:00, hard stop 18:00, submit 20:00, last re-run start 14:00) do not move.

If a source never recovers by the last allowed run, the test stays `not scorable`. That is a result: publish it and carry on. Do not wait for the deadline to see whether a host comes back. `HACKATHON.md` says development ends at 2026-11-14T23:59:00Z and that the API refuses submissions outside the window (403). It says nothing more about commits made after that time, so make none.

### 2.5 Commands

**A. Pre-flight (05:30 UTC).**

```
date -u
git status -sb                                   # ## main...origin/main and nothing else
python3 -m pipeline.check --manifest             # check: PASS
python3 -m pipeline.check --numbers              # check: PASS
python3 -m unittest discover -s tests            # last line: OK (skipped=1) today; see below
sha256sum PREREG.md                              # 19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240
git diff prereg-freeze -- PREREG.md              # prints nothing
ls data/forward 2>/dev/null                      # prints nothing: no folder yet, and no dry-run_* folder
```

On macOS use `shasum -a 256 PREREG.md`. From 2026-11-14 00:00 UTC the test run ends `OK (skipped=1)`, because the refusal test skips itself. Other tests skip on some systems, so a different skip count on your machine is fine: only `FAILED` or `ERROR` is a problem.

**B. Score (06:00 UTC).**

```
python3 -m pipeline.score_forward --score
```

Copy the terminal output into your notes. It is also in `result.json`.

**C. Read and verify (06:10 UTC).** Replace `<stamp>` with the part of the folder name after `score_`. If the last line of the scorer says `wrote /home/you/near-flow-statement/data/forward/score_20261114T060000Z`, then `<stamp>` is `20261114T060000Z`.

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

`result.amount` divided by 10^24 must equal `balance_near`. `result.header.timestamp_nanosec` must be at least 1794614400000000000, which is 2026-11-14T00:00:00Z. `sources.rpc_f1.data.prev_block_timestamp_ns` in `snapshot.json` must be below it.

**D. Update the repository (07:00 UTC).**

*D1.* Append the entry from 2.8b to the end of `PREREG-ADDENDUM.md`. Take the heading time from `date -u '+%Y-%m-%d %H:%M'` at the moment you write, not from your local clock. An earlier heading used the local date and needed a correction entry.

*D2.* Replace the "pending" statements with the sentences of 2.8c (five places; find them with `grep -n -i -E "pending|F1-F4|forward" README.md THESIS.md`; the THESIS row "A pending resolver" resolves on 2026-11-16, not on the 14th, so leave it). Then refresh the numbers that the re-rendered page changes in the README's "Try it" table: step 6's byte count (the data fingerprint is the hash of `data/MANIFEST.json`, which scoring does not change), and the test count of step 4 and the history counts of step 9 if the table quotes them as exact numbers (section 3, step 3b). Keep the hedges: the scorer was written after the window opened, and a missing input is `not scorable`, never estimated. Do not edit existing addendum entries or `PREREG.md`.

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
python3 -m unittest discover -s tests            # OK, or OK (skipped=N)
git diff prereg-freeze -- PREREG.md              # prints nothing
git status --short                               # only: data/forward/score_*/, PREREG-ADDENDUM.md, README.md, THESIS.md, site/index.html
```

**F. Commit and push.** Add files by name, so that a stray folder cannot slip in.

```
ls data/forward                                  # delete any dry-run_* folder first
git add data/forward PREREG-ADDENDUM.md README.md THESIS.md site/index.html
git commit -m "Forward tests F1-F4 scored: results, addendum entry, dashboard"
git push origin main
git status -sb                                   # ## main...origin/main, with no "ahead"
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
| `render: data/forward/<folder>/result.json is a scored result … in a folder not named score_YYYYMMDDTHHMMSSZ` | A score sits in a folder the dashboard cannot read by name, so the page would say pending over it. | Rename the folder to `score_<UTC stamp>`, as the scorer writes it, or delete it if it is a rehearsal. |
| `render: … is a scored result … that holds no results object` | `result.json` says it is a score but holds no `results`: a run that ended early, or a hand edit. | Run again (see the traceback row); never write `result.json` by hand. |
| `render: F4.intents_share_pct is nan, not a finite number …` | Every venue's volume was zero: the scorer writes F4 as `MISS` with a share of NaN (its quirk: PREREG says missing data is `not scorable`). | Edit the scorer's own output: set F4's `result` to `not scorable` and give a `why` (the numbers of a test that is not scorable are not read), name the edit in a dated addendum entry, and render. |
| A test fails with `README.md step 6 quotes (N bytes) = …, the page is …` | README step 6 quotes the page's size and the page has changed, which it does when a score is rendered. | Edit those two numbers as the message says (2.5 D2). |
| The page still says pending after `render` | `render` draws only the newest `score_<stamp>/result.json` that has `is_score` true, `mode` `score` and a `results` object. | Check that you used `--score` (a dry run is not a score), and that no newer `score_<stamp>` folder is in the way. |

### 2.7 What to commit afterwards

| Path | Why |
|---|---|
| `data/forward/score_*/` (all of them) | The raw record and the results, errors included. |
| `PREREG-ADDENDUM.md` | The new dated entry. Append only. |
| `site/index.html` | The page rebuilt by `python3 -m pipeline.render`. CI fails if it is stale. |
| `README.md`, `THESIS.md` | The "pending" statements replaced, and README step 6 refreshed (page bytes); steps 4 and 9 only if they quote exact numbers. `python3 -m pipeline.check --numbers` must still pass. |
| `docs/ANCHOR.md` | Only if you anchor `PREREG.md` (section 4). |

### 2.8 Entry templates for `PREREG-ADDENDUM.md`

No numbers are pre-filled. Angle brackets are yours to fill. A number that exists in `data/metrics.json` needs its marker, an HTML comment `<!--n:…-->` that holds the metric key and sits directly after the number. The forward results do not exist there, so they take no marker.

**a. Before scoring (commit and push on November 12 or 13).**

```
## <YYYY-MM-DD HH:MM> UTC: how the forward tests will be scored on 2026-11-14 (written before any window data is scored)

This fixes the procedure before scoring opens. It changes no hypothesis, threshold, probability or rule in PREREG.md.

1. Command: `python3 -m pipeline.score_forward --score`, run on `main` with a clean working tree, no earlier than <06:00> UTC on 2026-11-14. The script allows 00:00 UTC. The later time is chosen so that the sources have had time to publish 2026-11-13. It is a choice about timing, not about the test.
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

**c. Sentences for `README.md` and `THESIS.md`.** Replace the "pending" sentences with these, filled from `result.json`. The pass, miss and not-scorable counts are not metrics, so they take no marker. Keep the label "pre-registered" for F1-F4 and keep the disclosure about the scorer. Five places change, and the templates replace a whole line or paragraph, so keep the text around the sentence that you do not replace.

```
README status line (near the top; it keeps its last sentence):
> Status, <YYYY-MM-DD>: the offline rebuild passes. H1a, H1b and H1c have results. The forward tests F1-F4 were scored on <YYYY-MM-DD> (UTC); see the addendum entry dated <YYYY-MM-DD HH:MM> UTC. This is research, not financial advice.

README Summary (the whole paragraph "Forward tests F1-F4 are pending."), and THESIS.md section 5, row "The forward tests" (replace only the cell's first sentence, "F1-F4 are scored after 2026-11-14 by ..., misses included.", and keep the sentence about F3 after it):
**Forward tests F1-F4 (pre-registered) were scored on <YYYY-MM-DD> (UTC).** <n> passed, <n> missed and <n> were not scorable. The window was 2026-11-06 to 2026-11-13. `python3 -m pipeline.score_forward --score` scored them as `PREREG.md` words them. The script was written after the window opened, which the addendum discloses. A test with missing data is "not scorable" and is never estimated. The raw fetches and the result are in `data/forward/score_<stamp>/`.

README "Trace a headline number", row "Forward tests F1-F4": replace "none until scored" by
`data/forward/score_<stamp>/result.json`

README "Integrity rules", the forward-tests bullet: replace "Every result will be published, misses included." by
Every result was published, misses included; see the addendum entry dated <YYYY-MM-DD HH:MM> UTC.
```

The status-line, "Trace" and "Integrity rules" edits were tried in a throwaway clone: `check --numbers` and the unit tests still passed.

### 2.9 A dry run is not a score

`python3 -m pipeline.score_forward --dry-run` writes `data/forward/dry-run_<stamp>/DRY_RUN_result_NOT_A_SCORE.json` with `is_score` false. The page and the tests ignore it, and it is never quoted as a score.

One trap: its window is "the last 8 complete UTC days" and its block target is 00:00 UTC today. **On 2026-11-14 that is exactly the real window and the real block.** A dry run that day computes the same quantities as the score, without the check that the data was fetched after the deadline. Do not run it that day, and do not use one to decide whether to score.

### 2.10 Draft addendum entries awaiting approval

Drafts 2, 3 and 4 have not been appended to `PREREG-ADDENDUM.md`; they await your decision. Draft 1 was appended on 2026-11-08 at 05:04 UTC (see below). The addendum is append-only: add an entry at the end, with its own dated heading, and do not edit an earlier one. (Five earlier commits did edit nine existing lines; its 2026-11-08 entry lists them, and the text above that entry is pinned by SHA-256 in `tests/test_integrity.py`, so an edit of it fails the tests while an appended entry does not.) After appending, run `python3 -m pipeline.check --numbers` and `python3 -m unittest discover -s tests`, then commit and `git push origin main` (an unpushed commit carries only your own clock). Draft 2 contains dates only, no metric values; Draft 3 is a template with blanks that only you can fill.

**Draft 1 (done on 2026-11-08, 05:04 UTC): later dry runs and in-window reads.** Item 7 of the 2026-11-06 23:49 UTC entry says the scorer's dry run read no day inside 2026-11-06..13 for F2-F4. That was true of the first dry run only. The assistant appended an entry to `PREREG-ADDENDUM.md` (heading "2026-11-08 05:04 UTC: disclosure: later dry runs and direct reads that touched the forward-test window"), because the dashboard's forward-test card already said "first dry run" and nothing public recorded a later one. It states five things, each checked against the session transcripts and `git log`: (1) a second dry run on 2026-11-07 at about 18:15 UTC read one in-window day, and the assistant saw all four printed readings; at about 18:22 UTC it told you in the chat that the run touched one window day and that F4's reading was well below the 50% line; (2) a third dry run at about 19:57 UTC, by a subagent testing this runbook, sent its output to a scratch file that nobody opened; (3) the buyback wallet's balance, which F1 is about, was read from the chain at least five times inside the window (two values are in `docs/intents-fee-flows.md` and `docs/sources-checked.md`, three more were made by checking tools and are listed in the entry with their blocks; the latest, about 04:33 UTC, was 2,210,686.84 NEAR, above F1's lower edge of 2.21M); (4) a mutation test started a copy of the scorer with its refusal removed, with the proxy variables unset; it was stopped after about 80 seconds, and this sandbox cannot resolve host names without its proxy, so it could not fetch anything; (5) nothing was changed because of these reads. The entry is not pinned, so you may edit it until the repository is public (the tests do not fail); afterwards correct it only with a new dated entry. **Before step 5 of section 3, read it and change anything that is wrong or that you remember differently**, in particular the 18:22 UTC chat message in item 1, which only you can confirm. The dashboard's forward-test card names the entry.

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

1. **The earlier analysis of the 14 accounts** (`docs/supply-side.md` section 2, `THESIS.md` section 4). It was done from <date time UTC> to <date time UTC>, which is <before | after> the freeze (2026-11-05 22:53:29 UTC) and <before | after> 2026-10-19, when the hackathon's code window opened (`HACKATHON.md`, Q-001). It used <RPC only | BigQuery | both>. It <did | did not> inform the prior of 0.70 for H1a.
2. **BigQuery jobs behind H1a.** The job history of the billing project shows the job behind `sql/staking_flows_daily.sql` as <job ID>, created <time UTC>, the job behind `sql/staking_pool_totals_endpoints.sql` as <job ID>, created <time UTC>, and the job behind `sql/spike_top_receivers_7d.sql` (the receivers probe quoted in the 2026-11-05 labelling entry, no output committed) as <job ID>, created <time UTC>, which is <before | after> the freeze. The earliest job on `crypto_near_mainnet_us` in that history is <job ID>, created <time UTC>, which is <before | after> the freeze. Retrieved on <date> with <command or console page>.
```

How to get item 2 (UNVERIFIED: not run, the sandbox has no BigQuery access): `bq ls -j -a -n 100 --format=prettyjson`, with `-n` raised until it reaches back to 2026-11-05, or the job history in the BigQuery console of the billing project. A job ID such as `bqjob_r140d347f6f05de25_000001a1b321c86a_1` embeds its creation time in the second hex field, in milliseconds since the Unix epoch. This prints `2026-11-06 23:11:38.090000+00:00` (run on 2026-11-08; that job is the sweep preview in the addendum entry of 2026-11-06 23:23 UTC):

```
python3 -c "import datetime,sys; print(datetime.datetime.fromtimestamp(int(sys.argv[1],16)/1000, datetime.timezone.utc))" 000001a1b321c86a
```

How long the job history reaches back is UNVERIFIED. If the earliest H1a job precedes 2026-11-05 22:53:29 UTC, the claim that `PREREG.md` was frozen before any BigQuery flow query had run is false and the README must say so: its Summary, "Integrity rules" and "Pre-registration" now say only that the freeze was two minutes before the first BigQuery result the repository records, which would stay literally true but mislead; the dashboard has similar wording; and `PREREG.md` line 20 ("We had not run any query on staking-pool flows, exchange deposits or Intents event logs") would be wrong and cannot be edited, so the entry itself must say so. If item 1 shows the earlier analysis preceded the freeze, say that too, for the same reason.

**Draft 4 (needs your approval): pages seen during the research sweep of 2026-11-08.** At your request the assistant ran a research sweep on 2026-11-08: seven subagent lanes, then its own checks. Every lane was told not to read or record any F1-F4 quantity for a date on or after 2026-11-05. Some pages they opened showed such data anyway, and each lane listed them under "Window exposure" (branch `claude/research-notes`, folder `research/2026-11-08-sweep/lanes/`). An independent audit on 2026-11-10 checked this draft against those lists. The research is exploratory and is not in the repository's write-up. This entry only discloses the exposure, as the 05:04 UTC entry did for the later dry runs. Its one metric number, the block in item 6, carries its marker. Append it before scoring if you approve it, and correct anything you know differently.

```markdown
## <YYYY-MM-DD HH:MM> UTC: disclosure: pages seen during a research sweep on 2026-11-08

On 2026-11-08, between about 19:05 and 19:50 UTC, research subagents run by the assistant surveyed existing work and public data for this thesis. They were told not to read or record any F1-F4 quantity for a date on or after 2026-11-05. Some pages they opened showed such data anyway:

1. revenue.near.org (read about 19:14 and 19:15 UTC). Its embedded data held:
   - daily NEAR Intents fee, volume and revenue series through 2026-11-08;
   - a monthly row for November;
   - 7-day and 30-day capture-share fields;
   - a table of amounts per revenue wallet, including `buybacks.multisignature.near`. One lane read these amounts as current, the other as all-time amounts received.

   One lane masked the digits. In the other, the buyback wallet's amount appeared once in a tool output before the page was deleted.
2. Three rival hackathon entries' write-ups:
   - NGZeggers/near-value-shift's `THESIS.md` (read about 19:09 UTC) states a balance of `buybacks.multisignature.near` fetched on 2026-11-07, and the wallet's inflows through 2026-11-07. A CSV in the same repository holds withdrawals to that wallet dated 2026-11-05 and 2026-11-06, and one total the lane computed before filtering included them.
   - nikolaskahris-png/near-thesis-data's README (about 19:10 UTC) quotes a 30-day DefiLlama NEAR Intents volume ending 2026-11-07.
   - ervhint/tideline-thesis's `THESIS.md` (about 19:14 UTC) gives DefiLlama-derived NEAR Intents volume and revenue figures through 2026-11-07.

   The last two periods include 2026-11-06 and 2026-11-07, days that F3 and F4 cover.
3. prices.intear.tech (about 19:13 UTC). Its entry for wrap.near carries a current total-supply field, close to the quantity F2 measures. Separately, a Nearblocks statistics endpoint, which may carry the current total supply, was called once to test reachability; its answer was discarded unread.
4. nearstats.org (about 19:27 UTC) and several web-search result summaries (about 19:21 to 19:33 UTC). They showed NEAR Intents volume, or DefiLlama revenue, fees or volume, for trailing periods that may include 2026-11-06 to 2026-11-13. One summary showed buyback-wallet balance figures of unknown date. One news snippet showed a "last 30 days" buyback figure of unknown date; that page was not opened.
5. A public export of a hack tracer (about 19:22 UTC). It lists swaps and deposits through NEAR Intents after 2026-11-05 by accounts the tracer attributes to the Binance hack. The lane's report recorded their count, and one cumulative exit total that includes them; that total was masked before the notes were committed.
6. Repository files read by one lane. `data/raw/rpc/` already holds the buyback wallet's balance and the total supply at block 223,230,811<!--n:rpc_block--> (2026-11-05 22:51 UTC). Both were committed in `e309b4c` before this sweep, and `THESIS.md` quotes the balance.

Apart from the tracer total, none of these values was recorded, used or passed on.
- The copies of revenue.near.org, prices.intear.tech and nearstats.org were deleted the same day.
- The rival repositories and the tracer export stayed in the session's scratch folder. They were never committed, and they were deleted on 2026-11-10 at 00:09 UTC.
- The assistant that wrote this entry read the lanes' reports. Those hold none of these values except the committed figures of item 6 and, before it was masked, the tracer total of item 5.
- The research lanes and the assistant's own checks read the access keys and the confirmation count of `buybacks.multisignature.near`, never its balance.

F1-F4, their bands and the scoring rule were fixed in `PREREG.md` before the window opened. Nothing in the repository was changed because of these pages.
```

## 3. Making the repository public and hosting the dashboard

Order matters: copy this file out, set the email, bring the work to `main` without this file, push, take the working branch off GitHub, rehearse, correct the README's example outputs, scan, then flip visibility, then enable Pages.

**Step 0. Tools and credentials** (before Monday). `python3 --version` must print 3.10 or newer; otherwise install a newer Python and use it (`PYTHON=python3.12 bash scripts/fresh_clone_check.sh` for the check script). The commands assume macOS or Linux (on Windows use WSL or Git Bash; UNVERIFIED). The first push adds `.github/workflows/*.yml`, which GitHub refuses unless your credential has the `workflow` scope: run `gh auth refresh -s workflow` with the GitHub CLI, or create a classic personal access token with the `repo` and `workflow` scopes (or a fine-grained token with the Workflows permission) and use it as the password. The refusal text was not seen here.

**Step 1. Email first** (section 1). Before the one commit you make in step 2, run `git config user.email "<your GitHub noreply address>"`. It applies to this clone only: repeat it in any new clone, or use `git config --global` (all your repositories). If a push is refused with an error about a private email address, run `git commit --amend --reset-author --no-edit` (it fixes the latest commit) and push again.

**Step 2. Bring the work to `main` without this file, push it, and take the working branch off GitHub.**

*2a. Merge.* **Three checks first.** (1) Copy this file out of the repository (`cp SUBMISSION.md ~/near-runbook.md`, or, if it is not in your folder, `git show origin/claude/near-hackathon-dashboard:SUBMISSION.md > ~/near-runbook.md`) and read the copy from now on: `git switch main` removes `SUBMISSION.md` from this folder, the squash writes back a git-ignored copy, and a later `git switch` between `main` and the working branch overwrites or deletes it without a warning, notes included (tested). (2) Do 2a only when the assistant says the working branch is final; the recipe prints its tip, which you write down. (3) After `git fetch origin`, `git rev-parse main origin/main` must print two identical lines that start with `38e1c4c`; if not, stop and ask (`--ff-only` below would refuse). Commit or stash any other change first.

The work is on the branch `claude/near-hackathon-dashboard`, and this file is in that branch's history (added in `552c63b`). A normal merge would put it into `main`'s history for good, so squash:

```
(
set -e
git fetch origin
git rev-parse --short origin/claude/near-hackathon-dashboard      # write this down: the tip you are squashing
git switch main
git merge --ff-only 32c3136
git merge --squash origin/claude/near-hackathon-dashboard
git rm -f --cached SUBMISSION.md
echo SUBMISSION.md >> .git/info/exclude
git commit -m "Dashboard, tooling, thesis and documentation (squashed from claude/near-hackathon-dashboard)" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
)
```

The brackets and `set -e` make the block stop at its first failure. If `git switch main` is refused (usually an uncommitted change in this folder), nothing after it has run: commit or stash the change and paste the block again from the top. Without them, the lines after a refused switch run on the working branch and commit a deletion of `SUBMISSION.md` there.

What each line does. `git merge --ff-only 32c3136` moves `main` forward to the last commit before this file existed (`c86a876` to `32c3136`, none touching it), so those hashes survive; every commit hash that the README, `THESIS.md`, the docs and the addendum cite is at or before `32c3136` (checked 2026-11-08). `git merge --squash` stages everything after it as one change. `git rm -f --cached SUBMISSION.md` takes this file out of that change and leaves your copy on disk. The `.git/info/exclude` line keeps it out of `git status` and `git add -A` on this machine only (`.gitignore` is committed and would publish the name). The commit carries the `Co-Authored-By: Claude` trailer because the README says every commit does.

**The squash is one-way.** Afterwards make every change on `main` (`git push origin main`) and tell the assistant to work on `main` only: squashing the branch again conflicts in every file where the later commits and your squash changed neighbouring lines (tested: a one-line append to each of `README.md`, `THESIS.md` and `PREREG-ADDENDUM.md` conflicted in `THESIS.md` and `PREREG-ADDENDUM.md`). If the branch gained commits after the tip you wrote down and you have not yet deleted it (2c), run `git fetch origin`, then bring them over as one patch and commit: `git diff <tip you wrote down> origin/claude/near-hackathon-dashboard -- . ':(exclude)SUBMISSION.md' | git apply --index` (tested; without the fetch it prints `error: No valid patches in input`).

What `main` loses: the per-commit history from `552c63b` to the branch tip, which becomes the one squash commit. Check the result:

```
git ls-files | grep -c SUBMISSION                                   # 0
git diff --name-status origin/claude/near-hackathon-dashboard main  # only: D  SUBMISSION.md
git log --format=%B | grep -ic '^co-authored-by: claude'            # equals the output of: git rev-list --count HEAD
git status -sb                                                      # ## main...origin/main [ahead 5]
```

Tested on 2026-11-08 in throwaway clones, with a local bare repository standing in for GitHub: the checks printed 0, only `D` and the file name, 34 equal to 34, and `[ahead 5]`. These four results do not change when the assistant adds commits to the branch, because the squash is one commit. On that `main` the manifest and numbers checks, `render --check`, the unit tests and `fresh_clone_check.sh` passed. Nothing was pushed to GitHub.

*Alternative: squash everything, no fast-forward.* Leave out the `git merge --ff-only 32c3136` line (also tested: the same four checks print 0, only `D`, 30 equal to 30 and `[ahead 1]`). Then no `Claude-Session:` trailer reaches `main` (the four commits that the fast-forward keeps are the only ones on `main` that carry one: 4 against 0), but `a2414f8`, which the 2026-11-08 addendum entry cites, does not exist in a clone of `main` (`git cat-file -t a2414f8` says "Not a valid object name"). Decide in section 8, item 21. Whatever you choose, cite only hashes at or before `32c3136` in anything you add later.

*2b. Push.* `git push origin main`. If GitHub refuses because the push adds `.github/workflows/*.yml`, your credential lacks the `workflow` scope (step 0). Check the tag too: `git ls-remote --tags origin 'prereg-freeze^{}'`. Then open the Actions tab: expect two runs. CI should turn green (it has passed on the working branch since 2026-11-07, section 2.3, step 1; its run on `main` has not been observed, and nothing in the repository claims a CI result). A red Pages run is normal here, because Pages is not switched on yet; step 7 starts a working one (not observed; the workflow's header says it fails until the setup is done).

*2c. Take the working branch off GitHub, before step 5.* When a repository becomes public, all its branches do, and this branch holds this file and every `Claude-Session:` trailer. **First make sure you hold your own, current copy:** run `git branch -f claude/near-hackathon-dashboard origin/claude/near-hackathon-dashboard` (you are on `main`, so it is allowed). It creates your local copy if you have none and moves an older one up to the current tip; `git rev-parse claude/near-hackathon-dashboard origin/claude/near-hackathon-dashboard` must then print two identical lines. If you ever committed on that local branch yourself, stop and ask first: `-f` drops those commits from the branch. Otherwise the next command deletes the per-commit history of every commit your copy lacks (this file itself is safe in the copy you made in 2a). Then:

```
git push origin --delete claude/near-hackathon-dashboard
git branch --unset-upstream claude/near-hackathon-dashboard     # "has no upstream information" is fine
git branch -vv                                                  # you are on main; the working branch shows no [origin/...]
```

Without the second command, a later plain `git push` made while that branch is checked out puts the branch, this file and the `Claude-Session:` links back on GitHub (tested). Stay on `main`, and push with `git push origin main`.

The research notes of 2026-11-08 live on a second branch, `claude/research-notes`. It holds only `research/` and shares no history with the working branch or `main`. Unless you decide to publish them (section 8, item 26), take them off GitHub too, after keeping a copy:

```
(
set -e
git fetch origin +refs/heads/claude/research-notes:refs/remotes/origin/claude/research-notes
git branch -f claude/research-notes origin/claude/research-notes     # your copy
git rev-parse claude/research-notes origin/claude/research-notes      # must print two identical lines
git push origin --delete claude/research-notes
git branch --unset-upstream claude/research-notes 2>/dev/null || true
)
```

The brackets and `set -e` stop the block before the delete if the copy cannot be made. Tested on 2026-11-10 against a local bare repository standing in for GitHub, from a normal clone and from a single-branch clone: the copy stays, and the branch is gone from the bare repository. That branch has no workflow files, so pushing it starts no CI run (UNVERIFIED until you look at the Actions tab).

Deleting the branch does not delete its CI runs (UNVERIFIED), and step 5 makes Actions history visible to everyone; each run shows a commit title and hash. Delete them before step 5 (Actions tab, open a run, the "..." menu, "Delete workflow run"; or `gh run list --branch claude/near-hackathon-dashboard --limit 100 --json databaseId --jq '.[].databaseId'` prints the ids and `gh run delete <id>` deletes one; deleting was not tried), or accept that those titles and hashes become public. Also UNVERIFIED: whether GitHub keeps serving a deleted branch's commits by hash. For certainty use a new repository (section 8, item 20): rename this one to `near-flow-statement-old`, create an empty `near-flow-statement` under the same account, and from the squashed `main` run `git push <new-repository-url> main prereg-freeze`, which sends `main` and the tag and nothing else (tested into an empty local repository) and keeps every address valid. The rename was not tried; set up Pages again (steps 6 and 7), and keep the old repository private or delete it.

**Step 3. Rehearse what a judge does.** From `main`, `bash scripts/fresh_clone_check.sh` clones your `HEAD` into a temporary folder, runs the offline steps with no network, and prints a PASS/FAIL table. Uncommitted work is not in it. Expect `RESULT: PASS`.

**Step 3b. Check that the README's example outputs still match what a judge sees.** The "Try it" table in `README.md` quotes the output of its step 4 (the test count) and step 6 (the page's byte count and data fingerprint, each shown twice) as captured at some commit; step 9 shows its history counts as `<n>`, so the squash does not change it. Clone what a judge clones, run the three steps, and edit only a number that differs. When the working branch is final, the table should already match what the squashed `main` prints, so expect to change nothing (the numbers are not quoted here because they move with every commit):

```
rm -rf /tmp/judge
git clone https://github.com/notveiker/near-flow-statement /tmp/judge
(cd /tmp/judge && python3 -m unittest discover -s tests)       # README step 4: the "Ran N tests" line
(cd /tmp/judge && python3 -m pipeline.render --check)          # README step 6: byte count and data fingerprint
(cd /tmp/judge && python3 scripts/scan_secrets.py --history)   # README step 9: <n> placeholders, nothing to compare
rm -rf /tmp/judge
```

Then run `python3 -m pipeline.check --numbers`, commit the README and `git push origin main`. If the table already matches, there is nothing to do. Only step 6's byte count, data fingerprint and date are pinned, by `test_the_byte_count_fingerprint_and_date_the_readme_quotes_are_the_pages`; the test count of step 4 is not.

**Step 4. Scan the history again,** after the last commit. `python3 scripts/scan_secrets.py --history`. Expect `scan_secrets: PASS`; the counts it prints depend on the branches your clone holds, and only the PASS matters.

**Step 5. Make it public.** **Careful: settle section 8, item 23 (DefiLlama's terms) and the branch's CI runs (2c) first, and accept that the personal email address in your first 29 commits (section 1) becomes readable by anyone; this cannot be undone in effect.** On the repository page open Settings; in the "Danger Zone" choose "Change repository visibility", then "Change visibility", pick public and confirm ([GitHub docs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility)). Those docs list what changes: the code is visible to everyone, anyone can fork it, and Actions history and logs become visible to everyone. They also say that making a repository private again unpublishes its Pages site and erases its stars and watchers, one more reason not to make it private again after you submit. After this, assume everything in the history is copied.

**Step 6. Enable Pages.** In Settings choose "Pages" (under "Code, planning, and automation"). Under "Build and deployment", set "Source" to **GitHub Actions** ([GitHub docs](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)). Pages is available for public repositories on a free plan. Whether your plan allows it for a private one is UNVERIFIED, so do this after step 5.

**Step 7. Start the first deployment.** `.github/workflows/pages.yml` runs on a push that changes `site/**`, and it has a manual trigger. If you enabled Pages after the push that added `site/`, nothing starts by itself: open the Actions tab, choose "Pages", then "Run workflow". GitHub says a change can take up to 10 minutes to appear. The run page links to the deployed site.

**Step 8. Check it as a stranger would.** In a private browser window (logged out of GitHub), open the repository, then the dashboard, and click one "Query" link on the dashboard: it opens a file on GitHub, which works only once the repository is public. Then run:

```
curl -s -o /dev/null -w '%{http_code}\n' https://github.com/notveiker/near-flow-statement    # 200 = public, 404 = still private
curl -s -o /dev/null -w '%{http_code}\n' https://notveiker.github.io/near-flow-statement/    # expect 200
git ls-remote --tags https://github.com/notveiker/near-flow-statement 'prereg-freeze^{}'      # expect 413d776164a4…
bash scripts/fresh_clone_check.sh https://github.com/notveiker/near-flow-statement            # expect RESULT: PASS
```

Only the first two lines and the private window test what a stranger sees: `git ls-remote` and the check script use whatever GitHub login your machine stores, so they also succeed on a private repository.

**Step 9. Add the README line** only after step 8 shows 200 for both addresses. In `README.md`, in the paragraph that starts **Dashboard.**, replace its last two sentences, "No hosted URL is claimed here. The Pages workflow (`.github/workflows/pages.yml`) can publish it once the repository is public.", with:

```
**Hosted dashboard:** <https://notveiker.github.io/near-flow-statement/>, the same file as `site/index.html`, published by `.github/workflows/pages.yml`.
```

Then run `python3 -m pipeline.check --numbers`, `git add README.md`, `git commit -m "README: hosted dashboard address"` and `git push origin main` (the public README has the line only after the push). The address has the form `https://<user>.github.io/<repository>/` ([GitHub docs](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)); confirm it from the link on the workflow run page before you publish it anywhere.

**What the organizers require of the repository and the demo** (section 1; `HACKATHON.md`: Start here, item 2; Procedure 1; Q-012; Q-014): the repository public by 2026-11-14T23:59:00Z and through judging (results by 2026-11-18), a LICENSE file (it has one: MIT), and a hosted demo, which is "a plus", kept up to 2026-11-18, ideally 2026-11-25. Do not make the repository private again after you submit. The MIT licence covers the code; the third-party data in `data/raw/` have their own terms, and `docs/sources-checked.md` records one restriction (DefiLlama's terms, clause 8) that you should settle before step 5 (section 8, item 23).

**Why make it public before November 14.** The demo post needs a working link, a judge's tooling may look early, and the scoring push on November 14 is then made in public: GitHub documents a public events feed for repositories that lists pushes ([GitHub docs](https://docs.github.com/en/rest/activity/events)), so GitHub, not your clock, would hold the push time. What that feed shows for a repository that was private earlier is UNVERIFIED.

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

**Step 4. Send one mainnet transaction that carries the digest in its function-call arguments.** The documented route is SocialDB, a contract at `social.near` that stores key-value data under the signer's account ([docs](https://docs.near.org/primitives/social.md), [contract README](https://raw.githubusercontent.com/NearSocial/social-db/master/README.md)): call its `set` method as your account with one argument, `data`, an object whose only top-level key is your account ID, holding string values (the digest, the tag name and the commit hash). `set` is payable, and a write under your own account needs permission or at least 1 yoctoNEAR attached (contract README); the amount is yours to choose, and no documented minimum was found.

**UNVERIFIED: the exact command was not run.** The form below is assembled from the NEAR CLI docs and from the SocialDB README. Its shape matches the `as-transaction` example in the CLI guide ([near-cli-rs](https://github.com/near/near-cli-rs/blob/main/docs/GUIDE.en.md)), which uses `testnet`; the same guide uses `network-config mainnet` in its read-only example, so `mainnet` is a valid name (list the names with `near config show-connections`). Check each part against the linked pages, and run it on testnet first.

```
near contract call-function as-transaction social.near set \
  json-args '{"data":{"<ACCOUNT>":{"near_flow_statement":{"prereg_sha256":"19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240","git_tag":"prereg-freeze","git_commit":"413d776164a42ddb2b1288bb02bd7bd112bc7f06"}}}}' \
  prepaid-gas '100.0 Tgas' attached-deposit '0.01 NEAR' \
  sign-as <ACCOUNT> network-config mainnet sign-with-keychain send
```

**Step 5. Copy the transaction hash.** The CLI guide's example output prints it as `Transaction ID`.

**Step 6. Check it as a stranger would.** This prints the method, the full arguments and the block time:

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

**Step 7. Record it.** Write `docs/ANCHOR.md` from the draft below and append the addendum entry under it. Change the last bullet under the README's "Integrity rules", the one that says no anchor exists. `python3 -m pipeline.check --numbers` also reads `docs/*.md`, so add no unmarked metric number there. **Two more things the transaction makes untrue:** the `idea` text in section 6 says "no transaction is signed" (use the 4a sentence in section 6, under "Which form to send"), and `README.md`, section "NEAR integration", says the project "deploys nothing" and that "no code here signs or sends a transaction" (still literally true, because you sign on your own machine, but incomplete: add a sentence about the anchor before you send the submission, which cannot be edited directly). Commit and `git push origin main`.

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

Append this to `PREREG-ADDENDUM.md`, then commit and `git push origin main`. Leave the README bullet as it is, since it already says there is no anchor, and nothing in the `idea` text changes.

```
## <YYYY-MM-DD HH:MM> UTC: PREREG.md was not anchored on NEAR mainnet

PREREG.md says its SHA-256 "is published on NEAR mainnet (see docs/ANCHOR.md once anchored)". That was not done. There is no docs/ANCHOR.md and no transaction is claimed. PREREG.md is frozen and that sentence cannot be edited, so this entry corrects the record. The hash is stated in README.md, and the git tag prereg-freeze (commit 413d776) points at the file itself. Nothing is published outside the repository. The evidence for the order of events around the freeze is the tag, the commit order and the manifest stamps (the freeze commit is 2026-11-05 22:53:29 UTC, and the first BigQuery result the repository records is stamped 22:55:37 UTC in data/MANIFEST.json). The repository owner controls all of them, and nothing outside the repository timestamps them.
```

**Which one.** 4a adds one narrow fact that anyone can check, and needs a testnet rehearsal, one mainnet transaction and a funded account. 4b is one paragraph of text and needs no key. Either is honest. Decide by 2026-11-12, because 4a is worth most before scoring. Note that item 6 of the 2026-11-08 addendum entry ("Not anchored") already records that no anchor is recorded in the repository and that there is no `docs/ANCHOR.md`, so 4b mostly repeats it (section 8, item 17).

## 5. Demo assets

**What the organizers require** (`HACKATHON.md`, read live on 2026-11-08; read it again before submitting, and before posting, because it says that dates and rules may change). The demo post is public on X, says the project was built at NEAR HACKATHON, **tags @NEARProtocol and #NEARHackathon** (optionally also @NearLegion and @NearBuilders, which bring more amplification), and has the demo video or screenshots attached; Q-012 adds that screenshots are not enough when judges cannot open the demo, so record the video (5.3). Their advice for the post: lead with the user problem so that the first line makes sense to someone who does not know the project; show one complete moment; say concretely what NEAR does in the product; give a next step, which is a link to the demo and the public repository and a genuine question or a request for specific feedback. Under Q-013 you keep all rights and the organizers get non-exclusive promotional rights to the name, screenshots, video and repository link. Still UNVERIFIED: X's current limits on post and video length for your account, and how X counts a link. Every claim in the drafts is in `THESIS.md` or the README. Add nothing about price, and do not call the result a signal. Say "will be scored" until the scores exist.

### 5.1 One post, at most 280 characters

The counts in this section were made by script on 2026-11-08 and include every character of each post, the `N/ ` prefix included: the raw count (the link written out in full, the safe count), and the count under the rule that X counts every link as 23 characters (UNVERIFIED: from memory, and the sandbox could not check it). Every post is plain ASCII and at most 280 characters on the raw count, tags included. The `[n]` marks are counted as they stand, and a digit is shorter than a mark.

**Variant A, before the forward tests are scored** (279 raw, 254 with a link counted as 23):

```
Who buys and who sells NEAR? Tests frozen in git before the first BigQuery result the repo records (own clock). H1a failed, H1b/H1c inconclusive, Hold (no view). Built at NEAR HACKATHON @NEARProtocol #NEARHackathon. Rerun offline: https://github.com/notveiker/near-flow-statement
```

The freeze claim is scoped to the first BigQuery result the repository records, with the clock hedge, as in the README: `PREREG.md` also lists results from keyless sources that it had already seen ("What we had already seen when we froze this"), so "before our first recorded result" would be wrong. There is no room for a question; post thread post 5's question ("Which exchange labels would you trust?") as a reply, since the organizers ask for one.

**Variant B, after scoring.** Replace each `[n]` from `result.json` (count the `PASS`, `MISS` and `not scorable` results). Do not fill it before scoring. (258 raw, 233 with a link counted as 23.)

```
Who buys and who sells NEAR? H1a failed, H1b/H1c inconclusive, rule says Hold (no view on NEAR). Pre-registered F1-F4: [n] pass, [n] miss, [n] not scorable. Built at NEAR HACKATHON @NEARProtocol #NEARHackathon https://github.com/notveiker/near-flow-statement
```

Attach the video from 5.3 (required in practice, see Q-012) and, if X allows it, one or two screenshots from 5.4.

### 5.2 Longer version: a thread of five

Characters per post, raw / with a link counted as 23: 1 = 273 / 273, 2 = 275 / 275, 3 = 272 / 272, 4 = 230 / 230, 5 = 277 / 252. Every post is at most 280 characters on the raw count. Post 1 carries the tags and the video, so that the thread shows up under the hashtag; its address is the `demoUrl` of section 6. Post 4 has a placeholder; write `pending` or the results.

```
1/ Who buys and who sells NEAR? Built at NEAR HACKATHON (Investment Thesis) @NEARProtocol #NEARHackathon. Tests frozen at commit 413d776, about two minutes before the first BigQuery result the repo records (times are the author's machine's). Failures are published. Thread:

2/ Pre-registered, 90 days to 2026-11-04. H1a (most staking rewards stay staked) fails: net staking outflow was 6.56x rewards. H1b/H1c (exchange flows) are inconclusive: only 20.0% of top-100 receivers carry an exchange label, 10.0% a cited one. Hold says nothing about NEAR.

3/ Exploratory, chosen after the freeze: over 30 days, NEAR's three Intents revenue wallets received NEAR equal to 15.81% of net issuance: 4.53 points from public fee collectors, 11.25 from the Confidential Intents escrow (fee stream unattested), 0.03 other. No valuation.

4/ Forward tests F1-F4 (window Nov 6-13) will be scored after Nov 14 00:00 UTC by a script that refuses a live run earlier. Misses will be published. Status: [pending | fill in from data/forward/score_*/result.json after scoring].

5/ No keys, no network, standard library only: python3 -m pipeline.check --manifest, then pipeline.compute, then pipeline.check --numbers, then open site/index.html. Built with Claude Code. https://github.com/notveiker/near-flow-statement Which exchange labels would you trust?
```

Post 4 after scoring (221 raw, 221 with a link counted as 23, before you replace the `[n]` marks):

```
4/ Pre-registered forward tests F1-F4 (window Nov 6-13), scored Nov 14 by a script that refuses a live run earlier: [n] passed, [n] missed, [n] not scorable. Misses are published. Details: the addendum, in the repository.
```

It does not name `PREREG-ADDENDUM.md`: `.md` is a country-code domain, so X might make the name a link (UNVERIFIED for X; it is the only file-like name in the posts that ends in a real top-level domain, checked against IANA's list of 2026-11-07).

Numbers in the thread, with their keys in `data/metrics.json`: 6.56<!--n:h1a_ratio_as_written_x-->× (post 2, written `x`), 20.0<!--n:h1b_coverage_count_pct-->% and 10.0<!--n:h1b_coverage_tier1_count_pct-->% (post 2), 15.81<!--n:ladder_all_wallets_pct_of_issuance-->%, 4.53<!--n:ladder_public_collectors_pct_of_issuance-->, 11.25<!--n:ladder_escrow_unshields_pct_of_issuance--> and 0.03<!--n:ladder_other_pct_of_issuance--> points (post 3; they add up to the 15.81). `python3 -m pipeline.check --numbers` does not read this file, so compare them with `data/metrics.json` before posting. "50%" is the threshold fixed in `PREREG.md`; 413d776 is the freeze commit; "two minutes" is the gap between its time (2026-11-05 22:53:29 UTC) and the manifest stamp of the first BigQuery result (22:55:37 UTC). "Built with Claude Code" matches the README's disclosure; whether to say it is your decision (section 8). The drafts carry the two required tags and not the optional `@NearLegion` and `@NearBuilders`.

### 5.3 Silent video, about two minutes ten

Built around `site/index.html`, opened from disk or from the hosted address. The page follows the system colour scheme, has no script, and each chart card has "What it shows", "What it does not show", and "Query" and "Data" blocks that open. The section and card names below are the ones on the page of 2026-11-08 (commit `720949f`). **Confirm them against the final page before you record.** Captions are burned-in text; there is no audio. The table is a plan of about 2 minutes 15 seconds. The assistant recorded a silent video from that page on 2026-11-08 (1280x720, no audio, 2:14, about 8 MB, file `near-flow-statement-demo-final.mp4`) and sent it to you in the chat; it is not in the repository, and whether it reached you is UNVERIFIED. Measure any video you are given (the player's duration, or `ffprobe`) against X's video limit for your account (UNVERIFIED; the free limit is commonly quoted as 2 minutes 20 seconds), cut it to fit, and re-record the parts that show the page from the final page: at least the forward-test scene, after scoring. Keep a copy of any draft media outside the repository now. Q-013 gives the organizers promotional rights to the video.

| Time | Show | Caption |
|---|---|---|
| 0:00-0:11 | Top of the page: the title, the two questions, the answer box and the five status chips. | "Who buys and who sells NEAR? Pre-registered: H1a fails, H1b and H1c are inconclusive. What can be verified instead is a range. Research, not financial advice." |
| 0:11-0:25 | Section "Scorecard (pre-registered)": the five tiles. | "Tests were frozen at commit 413d776, about two minutes before the first BigQuery result the repository records (times written by the author's own machine). These are the results as they came out." |
| 0:25-0:46 | Card "H1a: staking outflow". Open "Query" and "Data". | "H1a fails: net staking outflow was 6.56<!--n:h1a_ratio_as_written_x-->× staking rewards. A pass needed under 0.5×." |
| 0:46-1:03 | Cards "H1b: net exchange inflow" (both panels: the range, then coverage against 50%) and "H1c: identified buying". | "Inconclusive: 20.0<!--n:h1b_coverage_count_pct-->% of top receivers carry an exchange label, 10.0<!--n:h1b_coverage_tier1_count_pct-->% a cited one. The pre-registration needs 50%." |
| 1:03-1:14 | Card "Rating rule inputs". | "The frozen rule outputs Hold. That carries no view on NEAR." |
| 1:14-1:28 | Card "Forward tests F1-F4". | "F1-F4 will be scored after 2026-11-14 00:00 UTC by a script that refuses to run earlier. Earlier dry runs are disclosed. Misses will be published." Re-shoot after scoring and change the caption to the result. |
| 1:28-1:50 | Section "Exploratory (chosen after the freeze)": card "The value-capture ladder". | "Exploratory, chosen after the freeze: NEAR reaching the revenue wallets was 15.81<!--n:ladder_all_wallets_pct_of_issuance-->% of net issuance: 4.53<!--n:ladder_public_collectors_pct_of_issuance--> from public fee collectors, 11.25<!--n:ladder_escrow_unshields_pct_of_issuance--> from the escrow (unattested), 0.03<!--n:ladder_other_pct_of_issuance--> other. No valuation." |
| 1:50-2:05 | A terminal: `python3 -m pipeline.check --manifest`, `python3 -m pipeline.compute`, `git status --short`, `python3 -m pipeline.check --numbers`. | "Every number recomputes offline from committed snapshots. No keys, no network. (Refreshing the snapshots needs credentials.)" |
| 2:05-2:15 | End card: repository address, hosted dashboard address. | "Built at NEAR HACKATHON." |

Cards you can add if there is time: the network-usage card (`chart-usage`), "Escrow share by month", "NEAR's take in 1Click", "Partner concentration", "Partner fees against NEAR's revenue", "Share of the peer set", "Monthly revenue and take rate", "Supply and net issuance". Record at a fixed window size, and zoom the browser so captions are readable on a phone.

### 5.4 Screenshots to capture

1. The first screen (title, the two questions, the answer box and the five status chips), desktop width, light theme.
2. The same, dark theme.
3. The same at phone width (browser device mode).
4. The scorecard tiles, desktop width, and at phone width.
5. The H1a card: chart, "What it shows" and "What it does not show".
6. The H1b card: panel A, the range around the minted amount, and panel B, label coverage against the required 50%.
7. The "Forward tests F1-F4" card: pending before scoring, scored after.
8. The ladder card, with its "Exploratory, chosen after the freeze" label in view.
9. Any card with "Query" and "Data" open, to show that every chart names its source.
10. The partner-fee card, "Partner fees against NEAR's revenue", and the rating card.
11. A terminal with the three README commands (`check: PASS`, `wrote data/metrics.json …`, a clean `git status --short`), and one with `git tag -n` and `sha256sum PREREG.md`, showing the freeze.
12. After scoring: the new addendum entry on GitHub, or the scored forward-test card.
13. The public repository page with a green CI mark, and the hosted dashboard in a browser tab.

The assistant captured items 1 to 10 from the page of `720949f` (13 PNG files at twice the pixel density, named `01_first_screen_desktop_light.png` to `13_partner_fees_card.png`) and sent them to you in the chat; they are not in the repository.

Attach the video (required unless the hosted dashboard is live and judges can open it, Q-012). UNVERIFIED: whether X allows a video and images in one post; if not, put the screenshots on thread posts 2 to 5. Write alt text that states the finding in a sentence.

## 6. Submission payload

Source: the "Submission API" section of `HACKATHON.md`, read live on 2026-11-08 (last at 03:32 UTC; 22,199 bytes, SHA-256 prefix `903794f4b656b456`). It says `POST https://nearhackathon.com/api/applications` with `Content-Type: application/json`, a body of at most 12,000 bytes, exactly the fields below and no others. There is one submission per project; it **cannot be edited directly afterwards** (6.2). Submissions are accepted only until 2026-11-14T23:59:00Z, and the organizers advise sending it "when the repository is public and the demo post is up". The same fields are in the form at <https://nearhackathon.com/#apply>. You send the submission yourself, once, through the form (steps in 6.1). `HACKATHON.md` lets an agent send it through the API only after you confirm the exact payload: the agent must collect every value under its "What the human decides" (project name, lead name, email, size, tracks, payout account, repository link, demo link, description, consent) from you, never guess, generate or fill in placeholders, print the full payload and wait for your yes. The values marked "draft" below are proposals for you to accept or change in your own words, and this runbook treats the send itself as yours. Do not commit the payload: it contains personal data.

| Field | Rule in `HACKATHON.md` | Value | Who |
|---|---|---|---|
| `requestId` | UUID, generated once and reused on every retry | API route only: the form makes its own (commands below the table) | you, when sending by API |
| `projectName` | 2-80 characters | `near-flow-statement` | draft |
| `leadName` | 2-80 characters | _blank_ | you |
| `email` | valid, at most 160 characters, at most 2 submissions per email | _blank_ (the address the organizers should use; it need not be your git address) | you |
| `size` | exactly one of `1`, `2 - 4`, `4 - 6`, `6 - 8`, `8+` | _blank_ | you |
| `tracks` | array of ids, each once, from `defi`, `thesis`, `privacy`, `business`, `swarms`, `security`, `agents`, `realworld`, `games`, `nfts`, `memecoins`, `social`, `open` | `["thesis"]`; `open` as well is your call (below) | you decide |
| `nearAddress` | mainnet; 2-64 characters, lowercase, matching `^(([a-z\d]+[-_])*[a-z\d]+\.)*([a-z\d]+[-_])*[a-z\d]+$` (a named account such as `team.near`, or a 64-character implicit account) | _blank_ (copy it from your wallet; do not retype it) | you |
| `projectUrl` | http(s), at most 300 characters, unique | `https://github.com/notveiker/near-flow-statement` (must be public) | you confirm |
| `demoUrl` | http(s), at most 300 characters, the public demo post | _blank until the post is live; for a thread, the address of post 1/, which carries the tags and the video (check it logged out, 6.1)_ | you |
| `idea` | 20-2000 characters: the problem, the product, and how NEAR fits in | the draft below (1821 characters before scoring, 1883 after) | draft |
| `consent` | `true`, only after you agreed to: "I agree that the organizers may use these details to review our submission and contact us about this hackathon." | _blank_ | you |

Do not add any other field. In particular `website` is a spam trap: any non-empty value rejects the submission. Responses: 201 saved; 400 a field failed validation (fix the fields listed in `fields` and resend with the same `requestId`); 403 submissions are not open, or the request looked cross-site (do not retry); 409 the repository was already submitted or the email has 2 submissions (ask; do not change the link or the email to get around it); 413 the body is too large; 503 storage is unavailable (wait a minute and resend with the same `requestId`).

**Request id, API route only** (the form builds its own, read from its script on 2026-11-08). Make one and keep it for every retry: `python3 -c 'import uuid; print(uuid.uuid4())'` works everywhere, `uuidgen | tr A-Z a-z` on macOS, `node -e 'console.log(crypto.randomUUID())'` with Node.

**`idea` draft, for a submission before scoring** (1821 characters of the 2,000 allowed; it states the problem, the product and how NEAR fits in, as the field asks; the counts were made by script):

```
Problem: nobody can say who buys and who sells NEAR, and investment cases for NEAR quote headline figures (issuance, buybacks, Intents volume) that no one can re-run. Product: a pre-registered, re-runnable token flow statement for NEAR, and the investment thesis built on it. The tests were frozen at commit 413d776, about two minutes before the first BigQuery result the repository records (git and manifest times are the author's own machine's; nothing external attests them), and results are published as they come, misses included. H1a fails: net staking outflow was 6.56 times staking rewards. H1b and H1c are inconclusive: 20.0% of the top-100 NEAR receivers carry an exchange label (10.0% a cited one), and the pre-registration needs 50%. The frozen rating rule outputs Hold, which carries no view on NEAR. An exploratory ladder, labelled as chosen after the freeze, shows that the NEAR delivered to NEAR's three Intents revenue wallets equalled 15.81% of net issuance: 4.53 points trace to public fee collectors, 11.25 points arrived as unshields from the Confidential Intents escrow (whose fee stream is unattested), and 0.03 points came from one other recurring source. No valuation is made. How NEAR fits in: the data are NEAR's own (epoch-boundary block headers and account state from archival RPC, flows from the NEAR BigQuery public dataset and FastNEAR, the NEAR Intents Explorer API). Nothing is deployed on NEAR and no transaction is signed. Every number recomputes offline with the Python standard library from committed snapshots: python3 -m pipeline.check --manifest, python3 -m pipeline.compute, python3 -m pipeline.check --numbers, then open site/index.html. Forward tests F1-F4 are scored after 2026-11-14 00:00 UTC, and misses will be published. Built with Claude Code under the owner's direction.
```

**Which form to send.** The draft says the forward tests "are scored after 2026-11-14 00:00 UTC", true only if you submit before the scorer has run. The plan in 2.4 submits after scoring, and the submission cannot be edited directly, so then replace the sentence "Forward tests F1-F4 are scored after 2026-11-14 00:00 UTC, and misses will be published." with this one, filling each `[n]` from `result.json` (1883 characters, each `[n]` counted as three):

```
Forward tests F1-F4 were scored on 2026-11-14 (UTC): [n] passed, [n] missed, [n] not scorable. Misses are published, and the addendum lists every run.
```

If you chose 4a (section 4), also replace "Nothing is deployed on NEAR and no transaction is signed." with:

```
Nothing is deployed on NEAR; the owner signs one mainnet transaction that publishes the SHA-256 of PREREG.md (docs/ANCHOR.md).
```

(1890 characters before scoring, 1952 after scoring; the limit is 2,000.) With 4b nothing else changes.

The numbers in the draft are the ones in `data/metrics.json` (`h1a_ratio_as_written_x`, `h1b_coverage_count_pct`, `h1b_coverage_tier1_count_pct`, `ladder_all_wallets_pct_of_issuance`, `ladder_public_collectors_pct_of_issuance`, `ladder_escrow_unshields_pct_of_issuance`, `ladder_other_pct_of_issuance`); `python3 -m pipeline.check --numbers` does not read this file, so compare them before you send. Whether to say "Built with Claude Code" is your decision (section 8).

**Tracks.** The 13 ids and their one-line briefs are in the "Tracks" table of `HACKATHON.md`; the longer example prompts are in `nearai/near-hackathon-prompt-examples`. The `thesis` brief: "Build a long-term investment thesis for NEAR and back it with data: onchain analytics, live dashboards and models anyone can re-run. Judged on the evidence, not the conviction." Its hints are ONCHAIN DATA, DASHBOARDS, RESEARCH.

- `thesis` fits by construction. The README's "Track brief" table maps the brief line by line.
- `open` ("Have an idea that refuses to fit a category? Explore new ways for money, intelligence and ownership to work together."): `HACKATHON.md` tells you to list every track the project fits, and the API takes an array. A pre-registered research repository is a stretch for that wording. Adding it costs nothing if you think it fits, and a poor fit may cost credibility. Your decision.
- `privacy` (Privacy & Private AI): the escrow work concerns a privacy feature's auditability, but the project builds no private computation. Not recommended.
- The other ten tracks are build tracks (DeFi, agents, games and so on) and do not fit.

**One thing to keep in mind about "live".** The `thesis` brief says "live dashboards". This dashboard is static and as of 2026-11-04, by design (section 7). Q-012 says a local-only demo is acceptable (public repository, reproducible README, an X post with a video), and a hosted demo is a plus: enable Pages (section 3) and keep it up to 2026-11-18, ideally 2026-11-25.

### 6.1 Sending it

**Careful: this is the one action that cannot be repeated.** On 2026-11-14, about 16:00 UTC, you send the submission yourself, once, through the form at <https://nearhackathon.com/#apply>; it builds its own request id (read from its script on 2026-11-08; the form was not opened or tested).

1. In a private browser window (logged out of GitHub and X) open the repository address and the demo post's address (for a thread, post 1/'s); both must load. Do not delete or edit the post afterwards.
2. Check the payout account on chain: run the first `curl` command of 2.5 C (the one under "Read F1 independently from the chain") with `"finality":"final"` in place of `"block_id":<BLOCK_HEIGHT>` and your account in `account_id`. A `result` with an `amount` means it exists; `UNKNOWN_ACCOUNT` means the name is wrong or the account does not exist yet (a 64-character implicit account that never received funds answers the same: compare that one with your wallet character by character). The published rule for the field is only the form of the name, so a mistyped but well-formed name would probably pass. Both answers were seen on 2026-11-08.
3. Write every value in your private file and read it once more: project name, lead name, email, team size, tracks, payout account, repository address, post address, the `idea` text for the day (no `[n]` left) and the consent sentence.
4. Enter them in the form, tick the consent box only after reading its sentence, and press send once. Wait for the confirmation; on an error, fix the field it names and do not reload the page.
5. Save the confirmation (a screenshot) and your file outside the repository. If anything is wrong afterwards, do not submit again: see 6.2.

### 6.2 After you submit

- Keep the exact values you sent and the confirmation, outside the repository.
- Do not submit again: the same repository is rejected with 409, and a different link would count as another project.
- Keep the repository public, the Pages site and the X post up and unedited until the results (by 2026-11-18; the hosted demo ideally to 2026-11-25), and push nothing after 18:00 UTC on 2026-11-14 unless the build is broken.
- To fix a mistake use <https://nearhackathon.com/request-changes>. It asks for the project name, email, NEAR wallet address and repository link as you submitted them (what you remember best, if the mistake is in one of them), the fields to change with their new values, and a Discord or Telegram handle (read from the page on 2026-11-08). The organizers review each request by hand and may message you first, especially before a change of payout account or repository; until they apply it, the submission stays as sent.

## 7. Risks and weak points a judge may raise

Each row is a weak point visible in the repository itself, with the short answer and where the repository says it. The answers on the ladder's order, the escrow evidence, the forward-test disclosure, the freeze timing, the earlier analysis, the Hold and G_req were rewritten on 2026-11-08 after a review of the repository's own history; several are best said before a judge finds them.

| What a judge may say | Short answer | Where |
|---|---|---|
| Two of the three pre-registered flow tests are inconclusive, and the headline result is not pre-registered. | `THESIS.md` leads with the scorecard: H1a fails (6.56<!--n:h1a_ratio_as_written_x-->× rewards), H1b and H1c are inconclusive, the rule outputs Hold. The ladder is labelled exploratory (chosen after the freeze) and does not feed the rating rule. Do not say it was chosen after all three flow results. Its code was first committed at 2026-11-06 23:19:20 UTC (`51e396b`), before the H1b/H1c and H1a-as-written results were committed, and it became the headline at 2026-11-07 00:21 UTC. Say so first. | `THESIS.md`, first paragraph; `PREREG-ADDENDUM.md`, entries 2026-11-07 00:21 UTC and 2026-11-08 |
| Only 20.0<!--n:h1b_coverage_count_pct-->% of the top-100 receivers carry an exchange label, against 50% required. | That is why H1b and H1c are ranges. Only 10.0<!--n:h1b_coverage_tier1_count_pct-->% carry a cited label; the rest are labelled by our own sweep rule (say "carry an exchange label"; do not call the labels "citable"). The binding gap is labelling, not data: no citable NEAR address was found for OKX, Coinbase, Kraken, Bybit, HTX, Crypto.com, Upbit or Bithumb. More code does not close it; sourced labels would. | `docs/supply-side.md`; addendum, entry 2026-11-06 23:23 UTC |
| H1a fails, so what is the thesis? | H1a is reported as a fail, not hidden. The thesis in `THESIS.md` is about how much value capture can be verified, not about stakers holding. The scorecard says that, net of deposits, stakers withdrew far more than they earned (this includes exchange-owned stake moving, which is not a sale), in a price rally, and that NEAR is fungible, so nothing says who sold. Adding `lst-pool.near` gives 5.96<!--n:h1a_ratio_with_lst_pool_x-->× (post hoc), still a fail. | `docs/supply-side.md`; addendum, entry 2026-11-06 23:49 UTC |
| Partner and channel numbers rest on one key-gated source. | True. The Explorer API needs a partner key. The repository commits hash-checked daily aggregates and a sample of 195<!--n:fee_ev_swaps_n--> swaps, from 3<!--n:fee_ev_hours_with_swaps_n--> sampled hours, whose on-chain legs anyone can re-read without a key (`python3 -m pipeline.fetch_fee_evidence trace`). Nobody without a key can re-pull the aggregates. "Partners are paid their listed fee on chain" is a statement about that sample only. | `THESIS.md` Limits; README "What this does not show"; `docs/partner-concentration.md` Limits |
| The escrow story is inferred, and partly sampled. | Arrival is on chain and re-checkable: in the 30-day window all 909<!--n:escrow_funded_exact_30d_n--> deliveries are recorded as funded by the escrow for the exact amount. Which fee stream funds the escrow is unattested, so the headline is a range and the falsifier is named. Funding before 2026-10-06 is attributed from samples; from that date it is traced per delivery. Limits to state yourself: the committed on-chain re-check (`data/raw/escrow/verify_sample.json`) covers a seeded sample of 60 rows, not all 909 (`python3 -m pipeline.fetch_escrow verify --all` checks every row); and the SQL of the October funding scan is not committed. "909 of 909" (`escrow_funded_exact_30d_n` over `escrow_single_use_30d_n`) is computed by `escrow_ladder` from the delivery table's own `funder` and `exact_amount_flag` columns, and the table has no writer in `pipeline/`, so the 100.0% restates how the table was built and is not an independent test. The independent part is the on-chain re-check; `verify --all` on 2026-11-08 is recorded in `docs/sources-checked.md`, section 3 (ten rows differ from the chain in block height by 1 to 3 blocks, and nothing else fails). | `THESIS.md` sections 1-2 and Limits |
| The forward tests may miss, and the scorer was written after the window opened. | Both are disclosed. The predictions were frozen first. The scorer's operational readings were written before it was run on window data, and its first dry run read no day inside the window for F2-F4; a second dry run on 2026-11-07 read one such day, which the addendum entry of 2026-11-08 05:04 UTC discloses (section 2.10, Draft 1). A missing input is "not scorable", and misses will be published. F3's sensitivity was disclosed in advance. | addendum, entries 2026-11-06 01:11 UTC and 23:49 UTC (item 7); docstring of `pipeline/score_forward.py` |
| How do we know `PREREG.md` was frozen before the queries? | Do not say "before any BigQuery query". Say: frozen at commit `413d776` (2026-11-05 22:53:29 UTC), two minutes before the first BigQuery result the repository records (22:55:37 UTC in `data/MANIFEST.json`). The commit, tag and manifest times are written by the author's machine, and the tag has the same timestamp as its commit, so it adds no independent evidence. BigQuery job IDs, which embed their creation time, are recorded only for H1b/H1c and the October escrow scan, not for the H1a queries. No on-chain anchor exists yet (section 4). | README "Integrity rules"; addendum, entries 2026-11-06 23:23 UTC and 2026-11-08 (item 4) |
| Some supply-side statements rest on an earlier analysis that is not in the repository. | `docs/supply-side.md` section 2 and `THESIS.md` section 4 refer to an earlier analysis of 14<!--n:unstakers_a14_n--> accounts. Both label it exploratory and not a PREREG test. The repository holds its output, `data/raw/unstakers/account_set.json`, stamped 2026-11-06 23:50:01 UTC (after the freeze), and `pipeline/compute.py` computes the arithmetic from it: 42.87<!--n:unstakers_a14_net_outflow_m-->M NEAR, 90.7<!--n:unstakers_a14_share_of_net_outflow_pct-->% of the pools' 47.3<!--n:pool_net_outflow_90d_m-->M NEAR net outflow. The extraction behind its `net_diff` values is not in the repository, and the repository does not record when the analysis was done or whether it informed H1a's prior. Only you know (Draft 3, section 2.10). `THESIS.md` Limits says it is not reproduced here. | `docs/supply-side.md`; `THESIS.md` Limits; README "Timeline and disclosure"; addendum, entry 2026-11-08 (item 5) |
| The rating rule can never output Avoid at low label coverage, so the Hold is forced. | Recorded before the results: with coverage below 50%, H1b can come out pass or inconclusive, never fail, so Avoid is unreachable. Say the rest before a judge does: observed growth (619.0<!--n:rating_g_obs_pct-->% a year) is far above the Avoid line (16.6<!--n:rating_g_avoid_line_pct-->% a year), so even a failed H1b would have given Hold. The rule could only ever have output Buy or Hold, and the Hold carries no view on NEAR. | addendum, entry 2026-11-06 23:11 UTC, item 6; `THESIS.md`, first paragraph |
| G_req assumes HSP-029, whose timelock clears on 2026-11-16, after the deadline. | PREREG fixes the ramp's target and a constant price. The other constants (price level, 24-month ramp, activation date, horizon) were committed after the freeze, in the same commit as the as-written H1a result (`9ee9082`), and `THESIS.md` says so. The rule's output is Hold whatever G_req is, because H1b is inconclusive. Without HSP-029, G_req would be 46.8<!--n:rating_g_req_no_hsp029_pct-->% instead of 33.2<!--n:rating_g_req_pct-->%. | addendum, entry 2026-11-06 23:49 UTC, items 5-6; `THESIS.md` sections 4 and 5 |
| The brief says "live dashboards"; this one is static and as of 2026-11-04. | By design: no script, nothing loaded from another host, every number traces to committed data, and it opens from disk. Each card prints its as-of date. The README's track-brief table says it is not a live feed. | README "Track brief"; `site/index.html` |
| The repository was mostly written by an AI. | Disclosed in the README. Every commit carries the `Co-Authored-By: Claude` trailer (the squash commit you make carries it too). The numbers do not depend on who wrote the code: they recompute offline, and a script checks the marked prose against them. | README "Timeline and disclosure" |
| There is no hosted dashboard, no video and no X post yet. | True on 2026-11-08. They are owner actions (sections 3 and 5). Do not mention a hosted address, a video or a post before they exist, and do not call the Pages workflow "live" before its first deployment. | section 1, items 1 and 2 |
| The thesis headline is a bound, not a valuation. | Yes, and `THESIS.md` says so: "It is not a valuation." The usable result is a measured range: 4.53% to 15.81% of net issuance verifiably arrived from Intents in the window (if the three wallets are all of NEAR's Intents revenue wallets). The repository makes no valuation; `THESIS.md` section 3 gives one descriptive market-cap-to-revenue multiple, labelled as not a valuation. | `THESIS.md`, "Bottom line", "The thesis" and section 1 |
| The usage evidence is a Nearblocks aggregate with a step in it. | Daily active accounts averaged 61.6<!--n:active_accounts_30d_k-->K over the 30 days to 2026-11-04, -77.1<!--n:active_accounts_30d_yoy_pct-->% on the same 30 days a year earlier. Daily transactions are -84.8<!--n:tx_per_day_30d_yoy_pct-->% year on year, but most of that is one step between 2026-03-31 and 2026-04-02 that our data cannot explain. Contract usage is not computed, and the brief's BigQuery usage queries were not run: the figures come from Nearblocks charts. | `THESIS.md` section 3 and Limits; dashboard card `chart-usage` |
| Third-party documents are not committed. | The escrow account's identity (`PRIVATE_TREASURY_ACCOUNT_ID`), the Confidential Infrastructure Fee terms, near.com's statement about its fees and HSP-029 rest on pages that this repository does not commit. `docs/sources-checked.md` sets each such statement next to what the page said when it was read on 2026-11-08, with a verdict (match, partly, differs, not found); read it before a judge does, because it shows where the repository's wording is narrower or wider than its source. | `THESIS.md` Limits; README "Data sources and attribution" |
| The timing evidence for H1a is thinner than for H1b and H1c. | True. The H1b and H1c job IDs and times are in the addendum, written before their results; H1a's queries have no job ID, so the order rests on commit and manifest times (freeze 22:53:29 UTC, first result stamped 22:55:37 UTC). Draft 3 (section 2.10) is where you can add the job times, if the job history still shows them. | addendum, entry 2026-11-08 (item 4) |

## 8. Open decisions

One line each. Items 1, 2, 11, 20, 21 and 23 (and 3 and 25 if you will not take the recommendation) gate Monday 2026-11-09; items 26 and 27 must be settled before step 5 of section 3 (making the repository public); items 4 to 10 and 16 are due by Thursday 2026-11-12; items 13 and 14 by Friday 2026-11-13 (Start here lists them by date).

1. Make the repository public now (recommended, so the scoring push is public) or on November 13? Decide by 2026-11-09.
2. Which address will the new commits use: your GitHub noreply address (recommended)? Set it before the squash commit in section 3, step 2.
3. Keep or delete the three "never publish" lines in `.gitignore` (`near-research.md`, `notes/`, `private/`)? They name private files, they are in the first commit, and deleting them changes nothing in history; the recommendation is to keep them.
4. Anchor `PREREG.md` on mainnet (4a) or record that it was not (4b)? Decide by 2026-11-12.
5. If 4a: which account signs, and is it the payout account?
6. Adopt the scoring procedure in 2.8a, with these times (start 06:00 UTC, re-runs 60 minutes apart, last run by 14:00 UTC), and commit and push it before November 14? By 2026-11-12, before you write the 2.8a entry.
7. Start scoring at 06:00 UTC (midnight if you are on UTC-6) or at 12:00 UTC (2.4 has the shifted times)? By 2026-11-12.
8. Post the demo before scoring, with a reply on November 14, or once after scoring? By 2026-11-12.
9. Say in the post that it was built with Claude Code? The README already says so.
10. Select `open` as a second track? The API takes an array and `HACKATHON.md` says to list every track the project fits.
11. This file stays out of `main` (section 3, step 2). Keep your copy outside the repository (recommended): the squash leaves a git-ignored copy in the folder that a later `git switch` can overwrite or delete.
12. Leave the data as of 2026-11-04 (recommended) or refresh the snapshots? A refresh changes numbers that the prose quotes and needs the keys and tools listed in the README.
13. Who is team lead, what is the team size, and which email goes on the form? By 2026-11-13; write it in your private file (6.1).
14. Which mainnet account receives the payout? By 2026-11-13; check it on chain (6.1).
15. Resolved on 2026-11-08: `HACKATHON.md` requires the tags @NEARProtocol and #NEARHackathon and the demo video or screenshots (Q-012: screenshots are not enough when judges cannot open the demo, so the plan is a video); the drafts in 5.1 and 5.2 carry the tags. It adds no rule on commits after the deadline beyond "development ends" at 2026-11-14T23:59:00Z. Read the live file once more on November 13, because it says dates and rules may change.
16. Approve Drafts 2, 3 and 4 in section 2.10, and fill Draft 3's blanks only with what you know to be true? (Draft 1 is already in the addendum; read it and correct it before step 5 if needed.) Draft 3 is the only way the repository can learn when the earlier analysis was done and when the H1a queries ran.
17. Item 6 of the 2026-11-08 addendum entry ("Not anchored") says no anchor is recorded in the repository. If you anchor (4a) after the repository is public, do not edit that entry: the 4a addendum entry corrects the record. Before it is public you may reword it. Decide by 2026-11-12.
18. Media: the assistant made a silent captioned draft video and screenshots on 2026-11-08 from the page of that day; they are not in the repository, and the page changed afterwards. Keep a copy outside the repository now, measure the draft against X's video limit for your account (UNVERIFIED), and re-record the parts that show the page from the final page (5.3).
19. The brief's BigQuery usage queries (daily active accounts, transaction counts, contract usage) were not run, and the usage figures are Nearblocks aggregates. Run one cheap `block_date`-filtered query through `pipeline.bq_run` (a new file in `sql/`, a new addendum entry, new metrics with markers), or leave it as `THESIS.md` Limits states it?
20. The working branch is on GitHub and holds this file: delete it from origin before going public (section 3, step 2c, which also has the commands for a new repository), or make a new repository from `main`? Decide by 2026-11-09.
21. Which squash variant (section 3, step 2a): fast-forward to `32c3136` first (every cited hash survives; four `Claude-Session:` links stay in `main`'s history), or squash everything (no links; `a2414f8`, cited by the addendum, is missing from `main`)? Keep the `Claude-Session` links at all? Decide by 2026-11-09: it is final once you push.
22. Hosted demo: enable Pages (section 3) and keep it up to 2026-11-18, ideally 2026-11-25 (Q-012). Keep the repository public through judging and do not make it private again after you submit (Q-014).
23. DefiLlama's terms (clause 8) forbid mirroring or republishing their data without permission, and the repository commits DefiLlama API responses under the MIT licence. Settle it before step 5 of section 3 (making the repository public): ask DefiLlama, or document the exception in the README. `docs/sources-checked.md` has the quote. Not read: the terms of CoinGecko, Nearblocks and FastNEAR.
24. The SQL of the BigQuery job that traced the escrow funding hops is not in the repository (job `bqjob_r275b038b73d7c093_000001a1af3708a8_1`, in `data/MANIFEST.json`). If you have the Google Cloud project that ran it, `bq show --job=true --location=US --project_id=<PROJECT> --format=prettyjson bqjob_r275b038b73d7c093_000001a1af3708a8_1` prints it (metadata only, no bytes billed). Committing it under `sql/` closes the one reproducibility gap in the escrow table.
25. The 29 earliest commits name a model version in their `Co-Authored-By` trailer. Leave them (recommended), or publish from a new repository with rewritten history, which changes every hash that the README, `THESIS.md`, the docs and the addendum cite and breaks the `prereg-freeze` tag? The recommendation is to leave them.
26. The research notes of 2026-11-08 on `claude/research-notes`: delete that branch from GitHub before step 5 (recommended; 2c has the commands), or publish it? Their folder README lists what was verified, what was edited before committing, and the lane statements that would need rewording before publication. The notes hold the lane reports as written, with two known errors flagged in their README, and raw material on accounts linked to the NEAR Foundation. What is verified would reach the write-up only through the exploratory build its `SYNTHESIS.md` proposes, if you approve that build.
27. The 1Click (NEAR Intents) API terms, last updated 2026-10-07, are reported by the research notes (`lanes/peers.md`, not re-read by the assistant) to forbid, in §4.1(e), caching or storing API data for more than 24 hours. The repository commits daily Explorer aggregates (`data/raw/explorer/daily.json`) and a fee sample (`data/raw/evidence/fee_sample_explorer.json`). Settle it before step 5 of section 3, as item 23 does for DefiLlama: read the clause, then ask NEAR Intents, stop committing that data, or document why it does not apply.

## Sources and limits of this document

Fetched on 2026-11-07:

- Organizers: <https://github.com/nearai/near-hackathon-prompt-examples> (`README.md`, `SUBMITTING.md`, `00-setup.md`, `tracks/*.md`).
- NEAR docs (most are linked where they are used): [`llms.txt`](https://docs.near.org/llms.txt), [create an account](https://docs.near.org/getting-started/create-account.md), NEAR CLI, RPC providers, RPC transactions, the `tx` reference, Social and validating recipient accounts; the SocialDB README; the near-cli-rs guide. The NEAR Intents docs index (`llms.txt`) was reachable; no step here depends on it.
- GitHub docs: repository visibility, Pages publishing source, creating a Pages site, commit email address, blocking pushes that expose it, email addresses reference, events.

Run in a scratch copy of the repository (nothing in the repository was changed by it): the scorer's refusal before the date; an offline re-score from a fixture snapshot and a second re-score of it; a dry-run snapshot refused as a score; the render and the tests with a fixture score present. Run against the live network, read-only: one `view_account` and one `block` call at a block already in the repository, one `tx` call on an existing mainnet transaction, a `view_account` on an existing and on a non-existent account, and the four-host reachability loop.

Read live on 2026-11-08: <https://nearhackathon.com/HACKATHON.md> (22,199 bytes, SHA-256 prefix `903794f4b656b456`; at 01:53, 02:51 and 03:32 UTC), which sections 1, 2.4, 3, 5, 6 and 8 follow; it was not reachable on 2026-11-07. Also read as data: the organizers' `README.md` and `SUBMITTING.md`, the scripts of the submission form's page (it builds its own request id and posts the same fields to the API), the request-changes page, and, read-only through GitHub's API, the repository's visibility, workflow runs and Pages state.

Not verifiable from the sandbox: the submission form itself (its fields and script were read; nothing was sent or tested), X's rules, your GitHub plan, your accounts, when DefiLlama and Nearblocks publish a finished day, and the exact CLI command in 4a (its shape is checked against the CLI guide, but it was not run). The scripts, workflows and tests this file mentions were added in the same batch of work as this file. Re-run them yourself before you rely on them.

Revised on 2026-11-08 in throwaway clones with a local bare repository standing in for GitHub (nothing in the repository was changed, nothing was pushed to GitHub): both squash recipes and their offline checks; the branch deletion and the push that recreates it; the late-commit patch and a second squash; the push of `main` and the tag into an empty repository; the rehearsal block, also with a failing clone; the README edits of step 3b; the author, trailer and commit counts in section 1; the check that every commit hash cited in the documents is at or before `32c3136`; a script recount of every post and of the idea draft; the decode of a job-ID timestamp in 2.10. Not run: `git push` to GitHub, deleting anything on GitHub, `bq ls`, and anything that needs GitHub's web settings, BigQuery or X.
