#!/usr/bin/env bash
# fresh_clone_check.sh: rehearse what a judge does after cloning this repository.
#
# It copies the repository into a temporary directory, runs the offline judge steps there, prints a PASS/FAIL table,
# deletes the copy and exits non-zero if any step failed. Nothing runs in your own working tree. The steps need no
# network and no keys: the Python steps are pointed at a dead proxy, so a stray request fails instead of succeeding.
#
#   bash scripts/fresh_clone_check.sh              git clone --local of this repository's HEAD: what a judge sees.
#                                                  Uncommitted work is NOT in it, so a file you forgot to commit
#                                                  shows up as a FAIL in the "files a judge needs" step.
#   bash scripts/fresh_clone_check.sh --worktree   copy of the working tree instead, for a rehearsal before you commit:
#                                                  tracked and untracked files, minus what .gitignore excludes
#                                                  (.env, .cache, __pycache__ ...) and minus .git. Outside a git
#                                                  checkout it copies everything except .git and cache folders.
#   bash scripts/fresh_clone_check.sh URL          clone URL instead (the clone is the only step that needs the network).
#                                                  Use it on the public GitHub URL after pushing.
#                                                  If this folder is not a git checkout (a zip download) the
#                                                  default falls back to copying the folder, as --worktree does.
#   --keep                                         do not delete the temporary directory (to look at a FAIL)
#   PYTHON=python3.10 bash scripts/fresh_clone_check.sh    use another interpreter (default: python3)
#
# Exit status: 0 every step PASS or SKIP, 1 at least one FAIL, 2 the check could not start.
# Needs bash, git, python3 (3.10 or newer) and the usual tools: cat, cp, cut, env, find, grep, head, mkdir, mktemp, rm,
# sed, tail. make is used if present, and sha256sum or shasum (else python3 hashes).
set -euo pipefail

FROZEN_PREREG_SHA256=19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240
FREEZE_TAG=prereg-freeze
# Files a judge needs: named in the README or run by the checks. A copy without one of them is not ready to submit.
REQUIRED_FILES="README.md AGENTS.md CLAUDE.md THESIS.md PREREG.md PREREG-ADDENDUM.md LICENSE Makefile .gitignore .gitattributes
data/MANIFEST.json data/metrics.json data/series.json pipeline/check.py pipeline/compute.py pipeline/render.py
site/index.html tests/test_integrity.py scripts/fresh_clone_check.sh scripts/scan_secrets.py
.github/workflows/ci.yml .github/workflows/pages.yml"
# .gitignore keeps these private; none may be in a clone.
FORBIDDEN_PATHS="near-research.md notes private .env"
PY=${PYTHON:-python3}
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)

usage() {
  cat <<'EOF'
usage: bash scripts/fresh_clone_check.sh [--worktree | URL] [--keep]
  (no argument)  git clone --local of HEAD into a temporary directory (what a judge sees)
  --worktree     copy the working tree (tracked and untracked, not git-ignored) instead; for a rehearsal before committing
  URL            clone this URL instead
  --keep         keep the temporary directory
  PYTHON=...     interpreter to use (default python3)
exit status: 0 all steps PASS or SKIP, 1 a step FAILED, 2 could not start
EOF
}

die() { echo "fresh_clone_check: $*" >&2; exit 2; }

MODE=clone
SRC=
KEEP=0
WANT_WORKTREE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --worktree) WANT_WORKTREE=1 ;;
    --keep) KEEP=1 ;;
    -h | --help) usage; exit 0 ;;
    -*) usage >&2; die "unknown option: $1" ;;
    *) [ -z "$SRC" ] || die "only one URL is accepted"; SRC=$1 ;;
  esac
  shift
done
if [ "$WANT_WORKTREE" -eq 1 ] && [ -n "$SRC" ]; then die "use either --worktree or a URL, not both"; fi
if [ "$WANT_WORKTREE" -eq 1 ]; then MODE=worktree; elif [ -n "$SRC" ]; then MODE=url; fi

command -v "$PY" >/dev/null 2>&1 || die "$PY not found (set PYTHON=/path/to/python3)"
command -v git >/dev/null 2>&1 || die "git not found"
case "$PY" in */*) PY=$(cd "$(dirname "$PY")" && pwd)/$(basename "$PY") ;; esac # the steps run in another directory

# Keep the environment a judge would have: no keys, no inherited import path.
unset NEAR_INTENTS_EXPLORER_JWT PYTHONPATH

WORK=
CHECKOUT=
cleanup() {
  if [ -z "$WORK" ]; then return 0; fi
  if [ "$KEEP" -eq 1 ]; then echo "kept: $WORK"; return 0; fi
  case "${WORK##*/}" in near-fresh.*) rm -rf "$WORK" ;; esac
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

WORK=$(mktemp -d "${TMPDIR:-/tmp}/near-fresh.XXXXXX") || die "mktemp failed"
CHECKOUT=$WORK/repo

# ------------------------------------------------------------------------------------------ get the copy
# True if ROOT is itself the top of a git checkout that has a commit (not a zip download, and not a folder that merely
# sits inside some other repository).
own_git_checkout() {
  local top
  top=$(git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null) || return 1
  [ "$top" = "$ROOT" ] && git -C "$ROOT" rev-parse --verify -q HEAD >/dev/null 2>&1
}

copy_worktree() {
  mkdir -p "$CHECKOUT"
  if own_git_checkout; then
    git -C "$ROOT" -c core.quotepath=off ls-files -z --cached --others --exclude-standard >"$WORK/files.lst"
    local f
    while IFS= read -r -d '' f; do
      [ -f "$ROOT/$f" ] || continue # deleted in the working tree, or a submodule
      case "/$f" in */.git/* | */.cache/* | */__pycache__/*) continue ;; esac # never copied, even if not git-ignored
      mkdir -p "$CHECKOUT/$(dirname "$f")"
      cp -p "$ROOT/$f" "$CHECKOUT/$f"
    done <"$WORK/files.lst"
  else
    local e
    for e in "$ROOT"/* "$ROOT"/.[!.]*; do
      [ -e "$e" ] || continue
      case "${e##*/}" in .git | .cache | .ruff_cache | .pytest_cache | .mypy_cache | __pycache__) continue ;; esac
      cp -R "$e" "$CHECKOUT/"
    done
    find "$CHECKOUT" -name __pycache__ -type d -prune -exec rm -rf {} +
  fi
}

if [ "$MODE" = clone ] && ! own_git_checkout; then
  echo "fresh_clone_check: $ROOT is not a git checkout with a commit, so there is nothing to clone: copying the folder instead" >&2
  MODE=copy
fi

case "$MODE" in
  clone)
    SOURCE="git clone --local $ROOT (committed HEAD only)"
    git clone --quiet --local "$ROOT" "$CHECKOUT" || die "git clone failed"
    ;;
  url)
    SOURCE="git clone $SRC"
    git clone --quiet "$SRC" "$CHECKOUT" || die "git clone of $SRC failed"
    ;;
  worktree)
    SOURCE="copy of the working tree $ROOT (uncommitted work included, git-ignored files left out)"
    copy_worktree
    ;;
  copy)
    SOURCE="copy of the folder $ROOT (not a git checkout)"
    copy_worktree
    ;;
esac

# ---------------------------------------------------------------------------------------------- helpers
sha256_stdin() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum | cut -d' ' -f1
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 | cut -d' ' -f1
  else
    "$PY" -c 'import hashlib, sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())'
  fi
}

# Run a command in the copy with no network: any Python urllib request goes to a dead local proxy and fails.
in_copy() {
  (
    cd "$CHECKOUT" || exit 97
    env PYTHONDONTWRITEBYTECODE=1 \
      http_proxy=http://127.0.0.1:9 https_proxy=http://127.0.0.1:9 all_proxy=http://127.0.0.1:9 \
      HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 ALL_PROXY=http://127.0.0.1:9 \
      no_proxy=localhost,127.0.0.1,::1 NO_PROXY=localhost,127.0.0.1,::1 \
      "$@"
  )
}

# One line that changes if any file in the copy (except .git and __pycache__) is added, removed or edited.
tree_digest() {
  (
    cd "$CHECKOUT" || exit 97
    "$PY" -c '
import hashlib, os
h = hashlib.sha256()
for d, dirs, files in os.walk("."):
    dirs[:] = sorted(x for x in dirs if x not in (".git", "__pycache__"))
    for f in sorted(files):
        p = os.path.join(d, f)
        h.update(p.encode() + b"\0")
        with open(p, "rb") as fh:
            h.update(hashlib.sha256(fh.read()).digest())
print(h.hexdigest())
'
  )
}

in_git_copy() { [ -d "$CHECKOUT/.git" ]; }
shallow_copy() { [ "$(cd "$CHECKOUT" && git rev-parse --is-shallow-repository 2>/dev/null)" = true ]; }

NROWS=0
NFAIL=0
NPASS=0
NSKIP=0
ROW_NAME=()
ROW_RES=()
ROW_DETAIL=()
ROW_LOG=()

# step "name" command...   (a command or a function; it returns 0 = PASS, 99 = SKIP, anything else = FAIL).
# The table shows the last output line that starts with "detail: ", else (for a FAIL) the first line that starts with
# "FAIL", else the last non-empty line.
step() {
  local name=$1 rc=0
  shift
  NROWS=$((NROWS + 1))
  local log=$WORK/step.$NROWS.log
  if "$@" >"$log" 2>&1; then rc=0; else rc=$?; fi
  local res=PASS
  if [ "$rc" -eq 99 ]; then res=SKIP; NSKIP=$((NSKIP + 1)); elif [ "$rc" -ne 0 ]; then res=FAIL; NFAIL=$((NFAIL + 1)); else NPASS=$((NPASS + 1)); fi
  local detail
  detail=$(grep '^detail: ' "$log" | tail -n 1 | cut -c9-) || true
  if [ -z "$detail" ] && [ "$res" = FAIL ]; then detail=$(grep '^FAIL' "$log" | head -n 1) || true; fi
  if [ -z "$detail" ]; then detail=$(grep -v '^[[:space:]]*$' "$log" | tail -n 1) || true; fi
  detail=$(printf '%s' "$detail" | cut -c1-76)
  ROW_NAME[NROWS]=$name
  ROW_RES[NROWS]=$res
  ROW_DETAIL[NROWS]=$detail
  ROW_LOG[NROWS]=$log
}

# ----------------------------------------------------------------------------------------------- steps
s_python() {
  in_copy "$PY" -c 'import sys; print("Python %d.%d.%d, %s" % (sys.version_info[:3] + (sys.executable,))); sys.exit(0 if sys.version_info >= (3, 10) else 1)'
}

s_files() {
  local f bad=0 n=0
  for f in $REQUIRED_FILES; do
    n=$((n + 1))
    if [ ! -f "$CHECKOUT/$f" ]; then echo "not in this copy (not committed?): $f"; bad=$((bad + 1)); fi
  done
  for f in $FORBIDDEN_PATHS; do
    if [ -e "$CHECKOUT/$f" ]; then echo "private path is in this copy: $f"; bad=$((bad + 1)); fi
  done
  if [ "$bad" -gt 0 ]; then echo "detail: $bad problem(s): files missing or private paths present"; return 1; fi
  echo "detail: all $n files the README and the checks rely on are here; no private paths"
}

s_manifest() { in_copy "$PY" -m pipeline.check --manifest; }

s_compute() {
  local before after
  before=$(tree_digest)
  in_copy "$PY" -m pipeline.compute || return 1
  after=$(tree_digest)
  if [ "$before" != "$after" ]; then
    echo "compute changed files in the copy, so it is not deterministic or the committed output is stale"
    in_git_copy && (cd "$CHECKOUT" && git status --short && git diff --stat)
    return 1
  fi
  if in_git_copy; then
    local status
    status=$(cd "$CHECKOUT" && git status --porcelain)
    if [ -n "$status" ]; then
      printf 'git status is not clean after compute:\n%s\n' "$status"
      return 1
    fi
    echo "detail: rewrote nothing; git status is clean"
  else
    echo "detail: rewrote nothing (file digest unchanged)"
  fi
}

s_numbers() { in_copy "$PY" -m pipeline.check --numbers; }

s_unittest() {
  local out rc=0
  out=$(in_copy "$PY" -m unittest discover -s tests 2>&1) || rc=$?
  printf '%s\n' "$out"
  printf 'detail: %s; %s\n' "$(printf '%s\n' "$out" | grep '^Ran ' | tail -n 1 || true)" "$(printf '%s\n' "$out" | tail -n 1)"
  return "$rc"
}

s_render() {
  if [ ! -d "$CHECKOUT/site" ] && [ ! -f "$CHECKOUT/pipeline/render.py" ]; then
    echo "no site/ and no pipeline/render.py in this copy"
    return 99
  fi
  in_copy "$PY" -m pipeline.render --check || return 1
  echo "detail: site/ equals a fresh render, byte for byte"
}

s_prereg_hash() {
  local got
  got=$(sha256_stdin <"$CHECKOUT/PREREG.md")
  echo "PREREG.md sha256 $got"
  [ "$got" = "$FROZEN_PREREG_SHA256" ] || { echo "detail: PREREG.md sha256 is $got, not the frozen value"; return 1; }
  echo "detail: sha256 $(printf '%s' "$got" | cut -c1-16)... is the frozen value"
}

s_prereg_tag() {
  if ! in_git_copy; then
    echo "no .git in this copy, so the tag cannot be checked"
    return 99
  fi
  if ! (cd "$CHECKOUT" && git rev-parse -q --verify "refs/tags/$FREEZE_TAG" >/dev/null); then
    if shallow_copy; then
      echo "detail: shallow clone without the tag (git fetch --unshallow --tags)"
      return 99
    fi
    echo "detail: tag $FREEZE_TAG is missing from this clone (git push origin $FREEZE_TAG)"
    return 1
  fi
  local tagged
  tagged=$(cd "$CHECKOUT" && git cat-file blob "$FREEZE_TAG:PREREG.md" | sha256_stdin)
  [ "$tagged" = "$FROZEN_PREREG_SHA256" ] || { echo "detail: PREREG.md at tag $FREEZE_TAG has sha256 $tagged"; return 1; }
  (cd "$CHECKOUT" && git diff --exit-code "$FREEZE_TAG" HEAD -- PREREG.md) || { echo "detail: PREREG.md differs from tag $FREEZE_TAG"; return 1; }
  echo "detail: git diff $FREEZE_TAG HEAD -- PREREG.md is empty (tag commit $(cd "$CHECKOUT" && git rev-parse --short "$FREEZE_TAG^{commit}"))"
}

s_make() {
  if ! command -v make >/dev/null 2>&1; then
    echo "make is not installed (README step 5 is optional)"
    return 99
  fi
  local before after
  before=$(tree_digest)
  in_copy make reproduce PY="$PY" || return 1 # the Makefile's own interpreter variable, so PYTHON= reaches make too
  after=$(tree_digest)
  [ "$before" = "$after" ] || { echo "make reproduce changed files in the copy"; return 1; }
  echo "detail: passed and rewrote nothing"
}

s_scan_tree() {
  if [ ! -f "$CHECKOUT/scripts/scan_secrets.py" ]; then echo "scripts/scan_secrets.py is not in this copy"; return 99; fi
  local out
  out=$(in_copy "$PY" scripts/scan_secrets.py 2>&1) || { printf '%s\n' "$out"; return 1; }
  printf '%s\n' "$out"
  echo "detail: no findings, $(printf '%s' "$out" | sed -n 's/.*working tree: \([0-9]* files\).*/\1/p' | head -n 1)"
}

s_scan_history() {
  if [ ! -f "$CHECKOUT/scripts/scan_secrets.py" ]; then echo "scripts/scan_secrets.py is not in this copy"; return 99; fi
  if ! in_git_copy; then echo "no .git in this copy, so there is no history to scan"; return 99; fi
  if shallow_copy; then echo "detail: shallow clone, older history is not here (git fetch --unshallow)"; return 99; fi
  local out
  out=$(in_copy "$PY" scripts/scan_secrets.py --history 2>&1) || { printf '%s\n' "$out"; return 1; }
  printf '%s\n' "$out"
  echo "detail: no findings, $(printf '%s' "$out" | sed -n 's/.*history: \([0-9]* blobs, [0-9]* commits\).*/\1/p' | head -n 1)"
}

s_clean() {
  local now
  now=$(tree_digest)
  [ "$now" = "$START_DIGEST" ] || {
    echo "the steps left files behind or edited files in the copy"
    in_git_copy && (cd "$CHECKOUT" && git status --short)
    return 1
  }
  echo "detail: the copy is byte-for-byte what it was before the steps"
}

# ------------------------------------------------------------------------------------------------- run
HEADLINE=$(cd "$CHECKOUT" && git log -1 --format='%h %s' 2>/dev/null | cut -c1-70 || true)
printf 'fresh-clone check\n'
printf '  source : %s\n' "$SOURCE"
[ -z "$HEADLINE" ] || printf '  commit : %s\n' "$HEADLINE"
printf '  python : %s\n' "$PY"
printf '  workdir: %s (%s)\n\n' "$WORK" "$([ "$KEEP" -eq 1 ] && echo 'kept because of --keep' || echo 'removed on exit')"

START_DIGEST=$(tree_digest)
SECONDS=0
step "python is 3.10 or newer" s_python
step "files a judge needs are present" s_files
step "check --manifest" s_manifest
step "compute rewrites nothing" s_compute
step "check --numbers" s_numbers
step "unittest discover -s tests" s_unittest
step "render --check" s_render
step "PREREG.md sha256 is the frozen value" s_prereg_hash
step "PREREG.md equals tag $FREEZE_TAG" s_prereg_tag
step "make reproduce" s_make
step "secret scan, working tree" s_scan_tree
step "secret scan, git history" s_scan_history
step "steps left the copy untouched" s_clean

printf '%-3s %-40s %-6s %s\n' '#' 'step' 'result' 'detail'
printf '%-3s %-40s %-6s %s\n' '---' '----------------------------------------' '------' '------------------------------------------------------------------------'
i=1
while [ "$i" -le "$NROWS" ]; do
  printf '%-3s %-40s %-6s %s\n' "$i" "${ROW_NAME[$i]}" "${ROW_RES[$i]}" "${ROW_DETAIL[$i]}"
  i=$((i + 1))
done
printf '\n'

if [ "$NFAIL" -gt 0 ]; then
  i=1
  while [ "$i" -le "$NROWS" ]; do
    if [ "${ROW_RES[$i]}" = FAIL ]; then
      printf -- '---- step %s FAILED: %s (last 25 lines of its output)\n' "$i" "${ROW_NAME[$i]}"
      tail -n 25 "${ROW_LOG[$i]}" | sed 's/^/  | /'
    fi
    i=$((i + 1))
  done
  printf '\nRESULT: FAIL (%s passed, %s skipped, %s failed; %ss)\n' "$NPASS" "$NSKIP" "$NFAIL" "$SECONDS"
  exit 1
fi
printf 'RESULT: PASS (%s passed, %s skipped, 0 failed; %ss)\n' "$NPASS" "$NSKIP" "$SECONDS"
