#!/usr/bin/env python3
"""Scan this repository for committed secrets. Standard library only (Python 3.10+), no network.

  python3 scripts/scan_secrets.py            working tree: tracked files plus untracked files that git does not ignore
  python3 scripts/scan_secrets.py --history  the same, then every blob, commit message and tag message reachable from
                                             any ref (branches, tags, remote-tracking refs), including deleted files
  python3 scripts/scan_secrets.py --rules    list what it looks for

Exit status: 0 nothing found, 1 at least one finding, 2 the scan could not run (for example --history outside git).

It looks for JSON Web Tokens, AWS access keys, Google API keys, GitHub and Slack tokens, PEM private keys, NEAR ed25519
private keys ("ed25519:" followed by 80 or more base58 characters; 44-character public keys are fine), assignments of
long values to names such as api_key, secret, token or password, credentials inside URLs, seed phrases, and file names
such as .env or *.key. It is a pattern scan: it finds what it has a pattern for, and a clean result is not a proof.

It never prints a whole suspected secret. A finding shows the rule, file:line:column, the text around the match with the
value masked (a few leading characters and the length), and a 12-character SHA-256 fingerprint of the value.

Allowing a known-safe value (the allowlist):
  * `scan-secrets: allow` anywhere on the same line (working-tree files; old history cannot be edited);
  * --allow VALUE, or an entry in ALLOW_VALUES below: a 64-hex hash (case does not matter, 0x is ignored) or the
    fingerprint printed with a finding (8 to 63 hex characters). This is how a known-safe 64-hex hash is allowed;
  * --allow-path GLOB, or an entry in ALLOW_PATHS below: skips a whole file (matched against the path in the repo).
The PREREG.md hash and every SHA-256 recorded in data/MANIFEST.json are allowed automatically.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent

PRAGMA = "scan-secrets: allow"
FROZEN_PREREG_SHA256 = "19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240"
# Known-safe values: 64-hex hashes or finding fingerprints. Add one here only after checking that it is public.
ALLOW_VALUES: frozenset[str] = frozenset({FROZEN_PREREG_SHA256})
# Repo-relative globs of files to skip entirely (fnmatch syntax, "/" separators).
ALLOW_PATHS: tuple[str, ...] = ()
MAX_BYTES = 32 * 1024 * 1024  # bigger files are reported as skipped, not scanned
MAX_FINDINGS_PER_TEXT = 100  # a file with more than this many hits needs a rule or allowlist fix, not a longer list
MAX_LINES_PRINTED = 200


# --------------------------------------------------------------------------------------------- value checks
PLACEHOLDER = re.compile(
    r"(?i)example|sample|placeholder|change[_-]?me|dummy|fake|redacted|your[_-]|insert|replace|todo|test|"
    r"[<>]|\*{3}|x{6,}|\.{3}|\$\{|\{\{|%s"
)
ENV_NAME = re.compile(r"[A-Z][A-Z0-9_]*")  # an environment variable name, not a value
DOTTED_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+")  # a.b.c in code
SNAKE_IDENT = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+")  # some_function_name_v2
SUFFIX_DENY = re.compile(
    r"(?i)hash|digest|sha|checksum|crc|id$|ids$|_id|url|uri|name|path|file|count|len|size|type|addr|env|label|symbol|"
    r"decimal|expir|ttl|header|prefix|regex|pattern|index|ref$"
)


def entropy(s: str) -> float:
    """Shannon entropy in bits per character."""
    counts = Counter(s)
    n = len(s)
    return -sum(c / n * math.log2(c / n) for c in counts.values()) if n else 0.0


def random_like(v: str) -> bool:
    """True if v could be a generated secret: long, has letters and digits, not a path or identifier, high entropy."""
    if len(v) < 20 or PLACEHOLDER.search(v):
        return False
    if not (re.search(r"[A-Za-z]", v) and re.search(r"[0-9]", v)):
        return False
    if v[0] in "/~." or ENV_NAME.fullmatch(v) or DOTTED_IDENT.fullmatch(v):
        return False
    if SNAKE_IDENT.fullmatch(v) and sum(ch.isdigit() for ch in v) <= 2:
        return False
    return entropy(v) >= 3.2


def _bearer_ok(value: str, m: re.Match[str], text: str) -> bool:
    return random_like(value)


def _credential_ok(value: str, m: re.Match[str], text: str) -> bool:
    """Generic name = value assignment: the name's suffix, the value's shape, and what follows it."""
    if SUFFIX_DENY.search(m.group(1)):
        return False  # token_id, secret_path, password_hash ...: a name that says it is not the secret itself
    if text[m.end(2):m.end(2) + 1] in ("(", "["):
        return False  # a call or an index expression, not a literal
    return random_like(value)


PLACEHOLDER_WORDS = frozenset({"password", "passwd", "pass", "pwd", "secret", "token", "user", "username", "changeme"})


def _url_password_ok(value: str, m: re.Match[str], text: str) -> bool:
    return not (PLACEHOLDER.search(value) or value[0] in "$%{<" or ENV_NAME.fullmatch(value)
                or value.lower() in PLACEHOLDER_WORDS)


def _not_signature(value: str, m: re.Match[str], text: str) -> bool:
    """An ed25519 signature has the same shape as a secret key. In NEAR JSON it sits under a key named signature."""
    return "signature" not in text[max(0, m.start() - 48):m.start()].lower()


def _not_doc_key(value: str, m: re.Match[str], text: str) -> bool:
    return "EXAMPLE" not in value  # AWS documents AKIA...EXAMPLE as its sample key


class Rule(NamedTuple):
    name: str
    doc: str
    pattern: re.Pattern[str]
    needles: tuple[str, ...] = ()  # lowercase; the rule only runs on text that contains one of them (speed)
    group: int = 0  # capture group that holds the secret (0 = the whole match)
    check: Callable[[str, re.Match[str], str], bool] | None = None  # (value, match, text) -> keep the finding?
    public: bool = False  # the matched text is a fixed public string, so it is printed as is


B58 = r"[1-9A-HJ-NP-Za-km-z]"
SECRET_NAME = (
    r"(?:api[_-]?key|apikey|api[_-]?secret|secret(?:[_-]?key)?|client[_-]?secret|password|passwd|passphrase|"
    r"(?:access|auth|bearer|refresh|session|private)[_-]?(?:token|key)|token|jwt)"
)

RULES: tuple[Rule, ...] = (
    Rule("private-key-block", "PEM, OpenSSH or PGP private key header",
         re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----"), ("private key",), public=True),
    Rule("jwt", "JSON Web Token: three base64url parts, the first two starting eyJ",
         re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*"), ("eyj",)),
    Rule("aws-access-key-id", "AWS access key id (AKIA..., ASIA... and related prefixes)",
         re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA)[A-Z0-9]{16}(?![A-Z0-9])"),
         ("akia", "asia", "agpa", "aida", "aroa", "aipa", "anpa", "anva"), check=_not_doc_key),
    Rule("aws-secret-access-key", "AWS secret access key assigned to aws_secret_access_key",
         re.compile(r"(?i)aws[_-]?secret[_-]?(?:access[_-]?)?key[\"']?[ \t]*[:=][ \t]*[\"']?([A-Za-z0-9/+=]{40})(?![A-Za-z0-9/+=])"),
         ("aws",), group=1, check=_not_doc_key),
    Rule("google-api-key", "Google API key (AIza + 35 characters)",
         re.compile(r"\bAIza[0-9A-Za-z_-]{35}(?![0-9A-Za-z_-])"), ("aiza",)),
    Rule("google-oauth-token", "Google OAuth access token (ya29.)",
         re.compile(r"\bya29\.[0-9A-Za-z_-]{20,}"), ("ya29.",)),
    Rule("gcp-service-account-file", "Google Cloud service-account key file",
         re.compile(r'"type"[ \t]*:[ \t]*"service_account"'), ("service_account",), public=True),
    Rule("github-token", "GitHub personal, OAuth, app or fine-grained token",
         re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,251}|github_pat_[A-Za-z0-9_]{22,255})(?![A-Za-z0-9_])"),
         ("ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_")),
    Rule("slack-token", "Slack bot, user or app token (xox...)",
         re.compile(r"\bxox[abeoprs]-[0-9A-Za-z-]{10,}"), ("xox",)),
    Rule("slack-webhook", "Slack incoming-webhook URL",
         re.compile(r"https://hooks\.slack\.com/(?:services|workflows|triggers)/[A-Za-z0-9/_-]{20,}"),
         ("hooks.slack.com",)),
    Rule("stripe-live-key", "Stripe live secret or restricted key",
         re.compile(r"\b[rs]k_live_[0-9A-Za-z]{16,}"), ("_live_",)),
    Rule("anthropic-api-key", "Anthropic API key (sk-ant-)",
         re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"), ("sk-ant-",)),
    Rule("openai-api-key", "OpenAI-style secret key (sk-...)",
         re.compile(r"\bsk-(?!ant-)(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{32,}"), ("sk-",),
         check=lambda v, m, t: random_like(v)),
    Rule("npm-token", "npm access token (npm_ + 36 characters)",
         re.compile(r"\bnpm_[A-Za-z0-9]{36}(?![A-Za-z0-9])"), ("npm_",)),
    Rule("pypi-token", "PyPI upload token",
         re.compile(r"\bpypi-AgE[A-Za-z0-9_-]{50,}"), ("pypi-",)),
    Rule("near-ed25519-private-key", "NEAR ed25519 secret key: ed25519: + 80 or more base58 characters (not a public key, not a signature)",
         re.compile(r"\bed25519:(" + B58 + r"{80,})"), ("ed25519:",), group=1, check=_not_signature),
    Rule("hex-private-key", "64-hex value assigned to private_key, secret_key, signing_key or seed",
         re.compile(r"(?i)(?:(?:private|secret|priv|signing)[_-]?key|seed)[a-z0-9_.-]{0,12}[\"']?[ \t]*[:=][ \t]*[\"']?(?:0x)?([0-9a-f]{64})(?![0-9a-f])"),
         ("private", "secret", "priv", "signing", "seed"), group=1),
    Rule("url-with-password", "user and password before the @ of a URL",
         re.compile(r"\b[a-z][a-z0-9+.-]{1,15}://[^\s/:@\"'<>]{1,64}:([^\s/@\"'<>]{4,})@[^\s/\"'<>]+"),
         ("://",), group=1, check=_url_password_ok),
    Rule("seed-phrase", "12 to 24 lowercase words assigned to mnemonic, seed phrase or recovery phrase",
         re.compile(r"(?i)(?:mnemonic|seed[ _-]?phrase|recovery[ _-]?phrase|secret[ _-]?phrase)[\"']?[ \t]*[:=][ \t]*[\"']?((?:[a-z]{3,8}[ \t]+){11,23}[a-z]{3,8})\b"),
         ("mnemonic", "phrase"), group=1),
    Rule("bearer-token", "Authorization: Bearer <long random value>",
         re.compile(r"(?i)\bbearer[ \t]+([A-Za-z0-9._~+/-]{24,}=*)"), ("bearer",), group=1, check=_bearer_ok),
    Rule("credential-assignment", "api_key, secret, token, password ... assigned a long random-looking value",
         re.compile(r"(?i)" + SECRET_NAME + r"([A-Za-z0-9_.-]{0,20})[\"']?[ \t]*(?::=|=>|:|=)[ \t]*[\"']?([A-Za-z0-9+/=_~.-]{20,})"),
         ("api", "secret", "passw", "token", "credential", "jwt"), group=2, check=_credential_ok),
)

# File names that should not be committed. (pattern, what it is)
NAME_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?:^|/)\.env(?:\.(?!(?:example|sample|template|dist|defaults|tpl|schema)$)[^/]+)?$"), "environment file (.env)"),
    (re.compile(r"\.(?:pem|key|p12|pfx|jks|keystore|ppk|kdbx)$", re.IGNORECASE), "key or keystore file"),
    (re.compile(r"(?:^|/)id_(?:rsa|dsa|ecdsa|ed25519)(?:_[^/.]*)?$"), "SSH private key"),
    (re.compile(r"\.key\.json$|(?:^|/)(?:service[-_]?account|client_secret|credentials|application_default_credentials)[^/]*\.json$", re.IGNORECASE), "credentials JSON"),
    (re.compile(r"(?:^|/)\.near-credentials(?:/|$)"), "NEAR credentials directory"),
    (re.compile(r"(?:^|/)secrets?(?:/|$)"), "secrets directory"),
    (re.compile(r"(?:^|/)\.(?:netrc|pgpass|git-credentials|pypirc)$"), "credentials file"),
)


class Finding(NamedTuple):
    where: str  # "path" or "history <oid10> path"
    line: int  # 0 for a file-name finding
    col: int
    rule: str
    shown: str  # masked excerpt
    fp: str  # 12 hex characters of SHA-256(value)


class ScanError(Exception):
    """The scan could not run (exit status 2)."""


# ---------------------------------------------------------------------------------------------------- allowlist
class Allow:
    def __init__(self, values: frozenset[str] | set[str] | list[str] | tuple[str, ...] = (), paths: tuple[str, ...] = ()):
        self.values = {v.strip().lower().removeprefix("0x") for v in values if v.strip()}
        self.paths = tuple(paths)

    def value(self, v: str, fp: str) -> bool:
        n = v.lower().removeprefix("0x")
        return n in self.values or (fp != "n/a" and any(8 <= len(a) < 64 and fp.startswith(a) for a in self.values))

    def path(self, rel: str) -> bool:
        return any(fnmatch.fnmatchcase(rel, g) for g in self.paths)


def manifest_hashes(root: Path) -> set[str]:
    """Every SHA-256 recorded in data/MANIFEST.json: public file hashes, never secrets."""
    try:
        data = json.loads((root / "data" / "MANIFEST.json").read_text(encoding="utf-8"))
        return {e["sha256"] for e in data["files"].values() if isinstance(e.get("sha256"), str)}
    except (OSError, ValueError, KeyError, AttributeError, TypeError):
        return set()


def default_allow(root: Path, values: list[str] | tuple[str, ...] = (), paths: list[str] | tuple[str, ...] = ()) -> Allow:
    return Allow(set(ALLOW_VALUES) | manifest_hashes(root) | set(values), tuple(ALLOW_PATHS) + tuple(paths))


# ----------------------------------------------------------------------------------------------------- masking
NO_PREFIX = frozenset({"seed-phrase", "url-with-password"})  # rules whose value is never shown, not even its first characters


def mask(value: str, show_prefix: bool = True) -> str:
    keep = min(4, len(value) // 10) if show_prefix else 0
    return f"{value[:keep]}***[{len(value)} chars]"


def fingerprint(value: str) -> str:
    """12 hex characters of SHA-256(value), for allowlisting. Only for long, high-entropy values: the hash of a short
    or guessable value (a weak password) could be reversed by a dictionary, so those get "n/a"."""
    if len(value) < 20 or entropy(value) < 3.0:
        return "n/a"
    return hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()[:12]


_LONG_RUN = re.compile(r"[A-Za-z0-9+/=_~.-]{16,}")


def _shorten(m: re.Match[str]) -> str:
    run = m.group(0)
    # a long name such as aws_secret_access_key stays readable; anything with a digit, or very long, may be a secret
    return run[:3] + "***" if len(run) > 24 or re.search(r"[0-9]", run) else run


def _tidy(context: str) -> str:
    """Context around a match: shorten any other long token-like run, flatten whitespace."""
    return re.sub(r"\s+", " ", _LONG_RUN.sub(_shorten, context))


# ------------------------------------------------------------------------------------------------ text scanning
def scan_text(where: str, text: str, allow: Allow) -> list[Finding]:
    """All findings in one text. `where` is only used to label them."""
    low = text.lower()
    found: list[Finding] = []
    spans: list[tuple[int, int]] = []  # a specific rule listed earlier wins over a generic one on the same text
    for rule in RULES:
        if rule.needles and not any(n in low for n in rule.needles):
            continue
        for m in rule.pattern.finditer(text):
            start, end = m.span(rule.group)
            value = m.group(rule.group)
            if rule.check is not None and not rule.check(value, m, text):
                continue
            fp = fingerprint(value)
            if allow.value(value, fp):
                continue
            line_start = text.rfind("\n", 0, start) + 1
            line_end = text.find("\n", end)
            line_end = len(text) if line_end < 0 else line_end
            if text.find(PRAGMA, line_start, line_end) >= 0:
                continue
            if any(start < b and a < end for a, b in spans):
                continue
            spans.append((start, end))
            before = text[max(line_start, start - 28):start]
            after = "" if rule.public else text[end:min(line_end, end + 16)]
            shown = _tidy(before) + (value if rule.public else mask(value, rule.name not in NO_PREFIX)) + _tidy(after)
            found.append(Finding(where, text.count("\n", 0, line_start) + 1, start - line_start + 1, rule.name, shown, fp))
            if len(found) >= MAX_FINDINGS_PER_TEXT:
                found.append(Finding(where, 0, 0, "too-many-findings", f"stopped after {MAX_FINDINGS_PER_TEXT} findings in this text", "n/a"))
                return found
    return found


def name_findings(where: str, rel: str) -> list[Finding]:
    """Findings for a file name alone (where is the label, rel is the repo path)."""
    return [Finding(where, 0, 0, "secret-file-name", f"{why}: {rel}", fingerprint(rel))
            for pat, why in NAME_RULES if pat.search(rel)]


def is_binary(data: bytes) -> bool:
    return b"\0" in data[:8192]


# ---------------------------------------------------------------------------------------------------------- git
def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", "-C", str(root), "-c", "core.quotepath=off", *args], capture_output=True, check=False)
    except FileNotFoundError as exc:
        raise ScanError("git is not installed") from exc


def list_tree_files(root: Path) -> tuple[list[str], str]:
    """Repo-relative paths of the files to scan, and how they were listed ('git' or 'walk')."""
    if (root / ".git").exists():
        try:
            p = _git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
        except ScanError:
            p = None
        if p is not None and p.returncode == 0:
            names = {n for n in p.stdout.decode("utf-8", "surrogateescape").split("\0") if n}
            return sorted(names), "git"
    names = []
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in (".git", "__pycache__", ".cache", ".venv", "venv", "node_modules"))
        names += [Path(d, f).relative_to(root).as_posix() for f in sorted(files)]
    return sorted(names), "walk"


class TreeResult(NamedTuple):
    findings: list[Finding]
    files: int
    nbytes: int
    how: str
    skipped: list[str]


def scan_tree(root: Path, allow: Allow) -> TreeResult:
    names, how = list_tree_files(root)
    findings: list[Finding] = []
    skipped: list[str] = []
    files = nbytes = 0
    for rel in names:
        if allow.path(rel):
            continue
        findings += name_findings(rel, rel)
        p = root / rel
        if p.is_symlink() or not p.is_file():
            continue
        if p.stat().st_size > MAX_BYTES:
            skipped.append(f"{rel} (larger than {MAX_BYTES} bytes)")
            continue
        data = p.read_bytes()
        files += 1
        nbytes += len(data)
        if not is_binary(data):
            findings += scan_text(rel, data.decode("utf-8", "replace"), allow)
    return TreeResult(findings, files, nbytes, how, skipped)


class HistoryResult(NamedTuple):
    findings: list[Finding]
    blobs: int
    commits: int
    tags: int
    nbytes: int
    shallow: bool
    skipped: list[str]


def scan_history(root: Path, allow: Allow) -> HistoryResult:
    """Every blob, commit message and tag message reachable from any ref, plus every path any commit ever touched."""
    inside = _git(root, "rev-parse", "--git-dir")
    if inside.returncode != 0:
        raise ScanError(f"{root} is not a git repository, so there is no history to scan: "
                        + inside.stderr.decode("utf-8", "replace").strip())
    shallow = _git(root, "rev-parse", "--is-shallow-repository").stdout.strip() == b"true"
    rl = _git(root, "rev-list", "--objects", "--all")
    if rl.returncode != 0:
        raise ScanError("git rev-list failed: " + rl.stderr.decode("utf-8", "replace").strip())
    paths: dict[str, str] = {}
    order: list[str] = []
    for ln in rl.stdout.decode("utf-8", "surrogateescape").splitlines():
        oid, _, rel = ln.partition(" ")
        if oid and oid not in paths:
            paths[oid] = rel
            order.append(oid)

    findings: list[Finding] = []
    # every path ever touched (deleted and renamed files too), checked by name
    lg = _git(root, "log", "--all", "--no-renames", "--name-only", "--format=", "-z")
    for rel in sorted({n for n in lg.stdout.decode("utf-8", "surrogateescape").split("\0") if n}):
        if not allow.path(rel):
            findings += name_findings(f"history {rel}", rel)

    blobs = commits = tags = nbytes = missing = 0
    skipped: list[str] = []
    with tempfile.TemporaryFile() as feed:
        feed.write(("\n".join(order) + "\n").encode() if order else b"")
        feed.flush()
        feed.seek(0)
        proc = subprocess.Popen(["git", "-C", str(root), "cat-file", "--batch"], stdin=feed, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL)
        assert proc.stdout is not None
        try:
            while True:
                head = proc.stdout.readline()
                if not head:
                    break
                parts = head.split()
                if len(parts) < 3:  # "<oid> missing": nothing follows
                    missing += 1
                    continue
                oid, kind, size = parts[0].decode(), parts[1].decode(), int(parts[2])
                if size > MAX_BYTES:  # read it in pieces and drop it: never hold a huge blob in memory
                    body, left = b"", size
                    while left:
                        chunk = proc.stdout.read(min(left, 1 << 20))
                        if not chunk:
                            raise ScanError("git cat-file stopped in the middle of an object")
                        left -= len(chunk)
                else:
                    body = proc.stdout.read(size)
                    if len(body) != size:
                        raise ScanError("git cat-file stopped in the middle of an object")
                proc.stdout.read(1)  # the newline git prints after each object
                rel = paths.get(oid, "")
                if kind == "blob":
                    blobs += 1
                    nbytes += size
                    label = f"history {oid[:10]} {rel}"
                    if allow.path(rel):
                        continue
                    if size > MAX_BYTES:
                        skipped.append(f"{label} (larger than {MAX_BYTES} bytes)")
                    elif not is_binary(body):
                        findings += scan_text(label, body.decode("utf-8", "replace"), allow)
                elif kind in ("commit", "tag"):
                    commits += kind == "commit"
                    tags += kind == "tag"
                    findings += scan_text(f"history {oid[:10]} ({kind} message)", body.decode("utf-8", "replace"), allow)
        finally:
            proc.stdout.close()
            proc.wait()
        if proc.returncode != 0:
            raise ScanError(f"git cat-file exited with status {proc.returncode}")
    if missing:
        skipped.append(f"{missing} object(s) that git could not read (a partial or shallow clone?)")
    return HistoryResult(findings, blobs, commits, tags, nbytes, shallow, skipped)


# ------------------------------------------------------------------------------------------------------ CLI
def show(f: Finding) -> str:
    where = f.where if not f.line else f"{f.where}:{f.line}:{f.col}"
    return f"{where}  [{f.rule}]  {f.shown}  fp={f.fp}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Scan the working tree (and with --history, all git history) for secrets.")
    ap.add_argument("--history", action="store_true", help="also scan every blob and message reachable from any ref")
    ap.add_argument("--root", type=Path, default=ROOT, help="repository to scan (default: the one this script is in)")
    ap.add_argument("--allow", action="append", default=[], metavar="VALUE",
                    help="a known-safe 64-hex hash or finding fingerprint (repeatable)")
    ap.add_argument("--allow-path", action="append", default=[], metavar="GLOB",
                    help="skip files whose repo path matches GLOB (repeatable)")
    ap.add_argument("--rules", action="store_true", help="list the rules and exit")
    a = ap.parse_args(argv)

    if a.rules:
        for r in RULES:
            print(f"{r.name:26} {r.doc}")
        for pat, why in NAME_RULES:
            print(f"{'secret-file-name':26} {why}: {pat.pattern}")
        return 0

    root = a.root.resolve()
    allow = default_allow(root, a.allow, a.allow_path)
    try:
        tree = scan_tree(root, allow)
        hist = scan_history(root, allow) if a.history else None
    except ScanError as exc:
        print(f"scan_secrets: cannot scan: {exc}", file=sys.stderr)
        return 2

    findings = tree.findings + (hist.findings if hist else [])
    for note in tree.skipped + (hist.skipped if hist else []):
        print(f"note: skipped {note}", file=sys.stderr)
    if hist and hist.shallow:
        print("warning: this is a shallow clone, so older history was not scanned (git fetch --unshallow)", file=sys.stderr)
    for f in findings[:MAX_LINES_PRINTED]:
        print(f"FAIL  {show(f)}", file=sys.stderr)
    if len(findings) > MAX_LINES_PRINTED:
        print(f"... and {len(findings) - MAX_LINES_PRINTED} more finding(s) not shown", file=sys.stderr)

    scope = f"working tree: {tree.files} files, {tree.nbytes / 1e6:.1f} MB (listed by {tree.how})"
    if hist:
        scope += (f"; history: {hist.blobs} blobs, {hist.commits} commits, {hist.tags} tags, "
                  f"{hist.nbytes / 1e6:.1f} MB" + ("; SHALLOW CLONE, older history not scanned" if hist.shallow else ""))
    if findings:
        print(f"scan_secrets: FAIL, {len(findings)} finding(s) ({scope})")
        if hist:
            print("scan_secrets: a history hit stays reachable until the history is rewritten and the key is revoked; "
                  "find the commit with: git log --all --oneline --find-object=<oid shown after 'history'>")
        print("scan_secrets: a known-safe value can be allowed with --allow <fingerprint or 64-hex>, or the line can carry "
              f"'{PRAGMA}' (see the top of scripts/scan_secrets.py)")
        return 1
    print(f"scan_secrets: PASS ({scope}; {len(RULES)} content rules, {len(NAME_RULES)} file-name rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
