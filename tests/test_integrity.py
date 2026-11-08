"""Integrity tests, offline and fast: the frozen pre-registration, the append-only addendum, the secret-handling files, the
raw-data manifest and line endings, the secret scanner (scripts/scan_secrets.py), what the fetchers may write into committed
files, and the CI / Pages workflows.

Run: python3 -m unittest discover -s tests   (or make test)

Tests that need git skip themselves when the folder is not a git checkout (a zip download, or the copy that
scripts/fresh_clone_check.sh --worktree makes) or when the prereg-freeze tag is missing (a shallow clone).
Secret-shaped sample text is built at run time from non-secret pieces, so this file contains no literal that the
scanner would flag.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import common as C  # noqa: E402
from pipeline import fetch_issuance as FI  # noqa: E402
from pipeline.check import check_manifest  # noqa: E402

FROZEN_PREREG_SHA256 = "19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240"
FREEZE_TAG = "prereg-freeze"
FREEZE_COMMIT = "413d776164a42ddb2b1288bb02bd7bd112bc7f06"   # the commit the tag must name: the freeze time claims attach to it

ALNUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
HEX = "0123456789abcdef"
UPPER_DIGITS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


def fake(n: int, alphabet: str, seed: str) -> str:
    """Deterministic random-looking text of length n, built at run time."""
    out: list[str] = []
    i = 0
    while len(out) < n:
        out.extend(alphabet[b % len(alphabet)] for b in hashlib.sha256(f"{seed}/{i}".encode()).digest())
        i += 1
    return "".join(out[:n])


def scanner():
    """scripts/scan_secrets.py as a module (scripts/ is not a package)."""
    if "scan_secrets" not in sys.modules:
        spec = importlib.util.spec_from_file_location("scan_secrets", ROOT / "scripts" / "scan_secrets.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["scan_secrets"] = module
        spec.loader.exec_module(module)
    return sys.modules["scan_secrets"]


def own_git() -> bool:
    """True if ROOT is itself a git checkout (not a copy without .git, not a folder inside some other repository)."""
    if shutil.which("git") is None:
        return False
    p = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"], capture_output=True, text=True, encoding="utf-8", check=False)
    return p.returncode == 0 and Path(p.stdout.strip()).resolve() == ROOT.resolve()


def git(*args: str, cwd: Path = ROOT, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, **kw, check=False)


# ----------------------------------------------------------------------------------- the frozen pre-registration
class FrozenPrereg(unittest.TestCase):
    def test_prereg_sha256_is_the_frozen_value(self):
        got = hashlib.sha256((ROOT / "PREREG.md").read_bytes()).hexdigest()
        self.assertEqual(got, FROZEN_PREREG_SHA256,
                         "PREREG.md differs from the frozen file. It must never be edited: add a dated entry to "
                         "PREREG-ADDENDUM.md instead.")

    def test_readme_prints_the_same_hash(self):
        """The README prints the frozen SHA-256, and no other hash next to the words PREREG and SHA-256."""
        readme = ROOT / "README.md"
        self.assertIn(FROZEN_PREREG_SHA256, readme.read_text(encoding="utf-8"), "README.md no longer prints the SHA-256 of PREREG.md")
        self.assertEqual(self._hashes_printed_next_to_prereg(readme) - {FROZEN_PREREG_SHA256}, set(),
                         "README.md prints a different PREREG.md hash")

    def test_agents_file_prints_the_same_hash(self):
        agents = ROOT / "AGENTS.md"
        if not agents.exists():
            self.skipTest("no AGENTS.md")
        self.assertEqual(self._hashes_printed_next_to_prereg(agents) - {FROZEN_PREREG_SHA256}, set())

    @staticmethod
    def _hashes_printed_next_to_prereg(path: Path) -> set[str]:
        found: set[str] = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            if "PREREG" in line and re.search(r"sha-?256", line, re.IGNORECASE):
                found |= set(re.findall(r"\b[0-9a-f]{64}\b", line))
        return found

    def test_the_scripts_carry_the_same_constant(self):
        for rel in ("scripts/fresh_clone_check.sh", "scripts/scan_secrets.py"):
            self.assertIn(FROZEN_PREREG_SHA256, (ROOT / rel).read_text(encoding="utf-8"), rel)

    def test_freeze_tag_still_matches_the_file(self):
        if not own_git():
            self.skipTest("not a git checkout")
        if git("rev-parse", "-q", "--verify", f"refs/tags/{FREEZE_TAG}").returncode != 0:
            self.skipTest(f"tag {FREEZE_TAG} is not in this clone (shallow clone?)")
        tagged = git("cat-file", "blob", f"{FREEZE_TAG}:PREREG.md")
        self.assertEqual(tagged.returncode, 0, tagged.stderr)
        self.assertEqual(hashlib.sha256(tagged.stdout).hexdigest(), FROZEN_PREREG_SHA256,
                         f"PREREG.md at tag {FREEZE_TAG} is not the frozen file")
        for other in (["HEAD"], []):  # committed history, then the working tree
            diff = git("diff", FREEZE_TAG, *other, "--", "PREREG.md", text=True, encoding="utf-8")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertEqual(diff.stdout, "", f"PREREG.md differs from tag {FREEZE_TAG}:\n{diff.stdout[:500]}")
        named = git("rev-parse", f"{FREEZE_TAG}^{{commit}}", text=True)
        self.assertEqual(named.stdout.strip(), FREEZE_COMMIT,
                         f"tag {FREEZE_TAG} names {named.stdout.strip()}, not the freeze commit {FREEZE_COMMIT}")
        ancestor = git("merge-base", "--is-ancestor", FREEZE_TAG, "HEAD")
        self.assertEqual(ancestor.returncode, 0, f"tag {FREEZE_TAG} is not an ancestor of HEAD")


# -------------------------------------------------------------------------------------- the addendum is append-only
# PREREG-ADDENDUM.md as committed at the end of the 2026-11-07 00:21 UTC entry: 9 entries, 17,033 bytes, ending in a newline.
# Five earlier commits (e0edac8, 8e59a3f, 5188f5a, 01187d5, 15f2859) edited 9 existing lines in place; nothing enforced the
# rule that the file is append-only until this pin. Nothing before this prefix may change. A new entry goes after it.
ADDENDUM_PINNED_BYTES = 17033
ADDENDUM_PINNED_SHA256 = "e5bc81bf4922f9cbf04ce39688c2cc8d6bc6793e9046927489967e7349dcf95d"


class AddendumIsAppendOnly(unittest.TestCase):
    """The first ADDENDUM_PINNED_BYTES bytes of PREREG-ADDENDUM.md are what they were when they were pinned. Appending a
    dated entry after them is allowed and needs no change here; editing, deleting or reordering anything inside them fails.

    To re-pin legitimately (only when the owner decides that entries added since are final and must never change):
        wc -c < PREREG-ADDENDUM.md        and        sha256sum PREREG-ADDENDUM.md
    (or `git show <commit>:PREREG-ADDENDUM.md | wc -c`, `... | sha256sum`), take the byte count to the end of a line, put
    both numbers above in the same commit as the entry, and say so in the commit message. Never re-pin to cover a change
    to a line that was already pinned: add a new dated entry that states the correction (AGENTS.md). A pin kept in the same
    repository is a deterrent that makes an edit visible in review, not proof against someone who edits both."""

    def setUp(self):
        self.data = (ROOT / "PREREG-ADDENDUM.md").read_bytes()

    def test_the_file_is_at_least_as_long_as_the_pinned_prefix(self):
        self.assertGreaterEqual(len(self.data), ADDENDUM_PINNED_BYTES,
                                "PREREG-ADDENDUM.md is shorter than its pinned prefix: something was deleted")

    def test_the_pinned_prefix_is_unchanged(self):
        prefix = self.data[:ADDENDUM_PINNED_BYTES]
        self.assertEqual(hashlib.sha256(prefix).hexdigest(), ADDENDUM_PINNED_SHA256,
                         "text that was already in PREREG-ADDENDUM.md has changed. The addendum is append-only: undo the edit "
                         "and add a new dated entry for a correction (see the docstring of this test to re-pin on purpose).")

    def test_the_prefix_ends_on_a_line_boundary_so_appended_entries_start_on_a_new_line(self):
        self.assertEqual(self.data[ADDENDUM_PINNED_BYTES - 1:ADDENDUM_PINNED_BYTES], b"\n")


# ----------------------------------------------------------------------------------------------- .gitignore
class GitignoreCoversSecrets(unittest.TestCase):
    PATTERNS = (".env", ".env.*", "secrets/", "*.key.json")

    def test_patterns_are_listed(self):
        lines = {ln.strip() for ln in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.lstrip().startswith("#")}
        for pattern in self.PATTERNS:
            self.assertIn(pattern, lines, f".gitignore must list {pattern}")

    @staticmethod
    def ignored(path: str) -> subprocess.CompletedProcess:
        """git check-ignore with the machine's global ignore file switched off, so the answer comes from this repository's rules only."""
        return git("-c", f"core.excludesFile={os.devnull}", "check-ignore", "-q", "--no-index", path)

    def test_git_agrees(self):
        if not own_git():
            self.skipTest("not a git checkout")
        for path in (".env", ".env.local", ".env.production", "secrets/anything.txt", "deep/secrets/a.json",
                     "wallet.key.json", "service-account-prod.json",
                     # key material that scripts/scan_secrets.py also flags by name
                     "tls/server.key", "keys/a.pem", "id_rsa", ".near-credentials/mainnet/me.json",
                     "client_secret_123.json", "application_default_credentials.json"):
            self.assertEqual(self.ignored(path).returncode, 0, f"{path} is not ignored")
        # Files that must be committed are not swallowed by an ignore rule.
        for path in ("README.md", "data/MANIFEST.json", "data/raw/escrow/deliveries.csv", "site/index.html",
                     "scripts/scan_secrets.py", ".github/workflows/ci.yml", "data/forward/score_x/result.json"):
            self.assertEqual(self.ignored(path).returncode, 1, f"{path} is ignored")


# ------------------------------------------------------------------------------------------- raw-data manifest
class RawDataManifest(unittest.TestCase):
    def test_every_raw_file_is_listed_and_matches_its_hash(self):
        self.assertEqual(check_manifest(), [], "data/raw and data/MANIFEST.json disagree (python3 -m pipeline.check --manifest)")

    def test_manifest_lists_only_raw_files_with_full_hashes(self):
        files = json.loads((ROOT / "data" / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
        self.assertGreater(len(files), 40)
        for rel, entry in files.items():
            self.assertTrue(rel.startswith("raw/"), rel)
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$", rel)


# ------------------------------------------------------------------------------------ line endings survive a checkout
class LineEndings(unittest.TestCase):
    """data/MANIFEST.json, PREREG.md and site/index.html are byte-hashed. A checkout with core.autocrlf=true (commonly set
    by a Git for Windows install) turns LF into CRLF: 44 of the 46 manifest hashes, the PREREG.md hash and the page then
    fail although nobody edited anything. `* -text` in .gitattributes switches that conversion off for every path."""

    BYTE_HASHED = ("PREREG.md", "PREREG-ADDENDUM.md", "data/MANIFEST.json", "data/metrics.json", "data/series.json",
                   "site/index.html", "scripts/fresh_clone_check.sh", "scripts/scan_secrets.py", "pipeline/check.py",
                   "data/raw/llama/volume_maya-protocol.json", "data/raw/escrow/deliveries.csv")

    def test_gitattributes_switches_line_ending_conversion_off_for_every_path(self):
        rules = [ln.split("#")[0].strip() for ln in (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([r for r in rules if r], ["* -text"])

    def test_git_reports_text_unset_for_the_byte_hashed_files(self):
        if not own_git():
            self.skipTest("not a git checkout")
        out = git("check-attr", "text", "--", *self.BYTE_HASHED, text=True, encoding="utf-8")
        self.assertEqual(out.returncode, 0, out.stderr)
        lines = out.stdout.splitlines()
        self.assertEqual(len(lines), len(self.BYTE_HASHED))
        for ln in lines:
            self.assertTrue(ln.endswith(": text: unset"), ln)

    def test_no_tracked_file_is_stored_with_carriage_returns(self):
        """The blobs themselves are LF (or have no newline at all): a CRLF blob would fail the hash tests for good."""
        if not own_git():
            self.skipTest("not a git checkout")
        out = git("ls-files", "--eol", text=True, encoding="utf-8")
        self.assertEqual(out.returncode, 0, out.stderr)
        listed = [ln for ln in out.stdout.splitlines() if ln.strip()]
        self.assertGreater(len(listed), 90)
        bad = [ln for ln in listed if re.match(r"i/(crlf|mixed)\b", ln.strip())]
        self.assertEqual(bad, [], "files stored with CRLF: " + "; ".join(bad[:5]))

    @unittest.skipUnless(shutil.which("git"), "git is not installed")
    def test_a_clone_with_autocrlf_true_keeps_every_hash_only_because_of_gitattributes(self):
        """Check out the committed tree with core.autocrlf=true, as Git for Windows would, once with this repository's
        .gitattributes and once without any. The first must pass `check --manifest` and keep the frozen PREREG.md hash;
        the second must fail it (so the test cannot pass for the wrong reason)."""
        if not own_git():
            self.skipTest("not a git checkout")
        env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1"}
        env.pop("PYTHONPATH", None)

        def sh(cwd: Path, *cmd: str) -> subprocess.CompletedProcess:
            p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=env, check=False)
            if p.returncode != 0 and cmd[0] == "git":
                self.skipTest(f"git could not set up the clone ({' '.join(cmd[:3])}): {p.stderr.strip()[:200]}")
            return p

        outcome: dict[bool, tuple[int, str, str]] = {}
        with tempfile.TemporaryDirectory() as tmp:
            for with_attributes in (True, False):
                clone = Path(tmp) / ("with" if with_attributes else "without")
                sh(Path(tmp), "git", "clone", "-q", "--local", "--no-checkout", str(ROOT), str(clone))
                sh(clone, "git", "config", "core.autocrlf", "true")
                sh(clone, "git", "read-tree", "HEAD")
                sh(clone, "git", "rm", "-q", "--cached", "--ignore-unmatch", ".gitattributes")   # what HEAD holds does not matter
                if with_attributes:
                    shutil.copyfile(ROOT / ".gitattributes", clone / ".gitattributes")           # the working tree's file
                sh(clone, "git", "-c", f"core.attributesFile={os.devnull}", "checkout-index", "-a", "-f")
                chk = subprocess.run([sys.executable, "-m", "pipeline.check", "--manifest"], cwd=clone, capture_output=True,
                                     text=True, encoding="utf-8", env=env, check=False)
                outcome[with_attributes] = (chk.returncode, chk.stdout + chk.stderr,
                                            hashlib.sha256((clone / "PREREG.md").read_bytes()).hexdigest())
        rc, out, prereg = outcome[True]
        self.assertEqual((rc, prereg), (0, FROZEN_PREREG_SHA256), out[-500:])
        self.assertIn("check: PASS", out)
        rc, out, prereg = outcome[False]
        self.assertEqual(rc, 1, "without .gitattributes the CRLF checkout should break the hashes: " + out[-300:])
        self.assertIn("hash mismatch", out)
        self.assertNotEqual(prereg, FROZEN_PREREG_SHA256)


# --------------------------------------------------------------------------------------------- secret scanner
class SecretScannerOnThisRepo(unittest.TestCase):
    def test_working_tree_has_no_secrets(self):
        p = subprocess.run([sys.executable, "scripts/scan_secrets.py"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        self.assertIn("scan_secrets: PASS", p.stdout)
        scanned = int(re.search(r"working tree: (\d+) files", p.stdout).group(1))
        self.assertGreater(scanned, 50, "the scan looked at too few files to mean anything")

    def test_rules_can_be_listed(self):
        p = subprocess.run([sys.executable, "scripts/scan_secrets.py", "--rules"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(p.returncode, 0, p.stderr)
        for name in ("jwt", "aws-access-key-id", "near-ed25519-private-key", "credential-assignment", "secret-file-name"):
            self.assertIn(name, p.stdout)

    def test_manifest_hashes_and_the_prereg_hash_are_allowed(self):
        ss = scanner()
        allow = ss.default_allow(ROOT)
        self.assertIn(FROZEN_PREREG_SHA256, allow.values)
        manifest = json.loads((ROOT / "data" / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
        for entry in manifest.values():
            self.assertIn(entry["sha256"], allow.values)


class SecretScannerDetects(unittest.TestCase):
    """Synthetic secrets, built at run time: each rule must fire, and the look-alikes in the repo must not."""

    @classmethod
    def setUpClass(cls):
        cls.ss = scanner()

    def rules(self, text: str) -> set[str]:
        return {f.rule for f in self.ss.scan_text("sample.txt", text, self.ss.Allow())}

    def samples(self) -> list[tuple[str, str, str]]:
        """(expected rule, secret value, text containing it)."""
        jwt = "ey" + "J" + fake(20, ALNUM, "jwt-h") + "." + "ey" + "J" + fake(30, ALNUM, "jwt-p") + "." + fake(43, ALNUM + "-_", "jwt-s")
        aws_id = "AK" + "IA" + fake(16, UPPER_DIGITS, "aws-id")
        aws_secret = fake(40, ALNUM + "/+", "aws-secret")
        google = "AI" + "za" + fake(35, ALNUM + "_-", "google")
        gh = "gh" + "p_" + fake(36, ALNUM, "gh")
        slack = "xo" + "xb-" + "1234567890-" + fake(24, ALNUM, "slack")
        near_sk = "ed25519:" + fake(88, B58, "near-secret-key")
        hex_key = fake(64, HEX, "hex-key")
        generic = fake(40, ALNUM, "generic")
        phrase = "apple bridge candle dragon engine forest garden harbor island jungle kitten lemon"  # ordinary words, not a wallet
        pem = "-----BEGIN " + "RSA PRIVATE" + " KEY-----"
        ant = "sk-" + "ant-" + fake(40, ALNUM + "_-", "anthropic")
        stripe = "sk_" + "live_" + fake(24, ALNUM, "stripe")
        npm = "npm_" + fake(36, ALNUM, "npm")
        bearer = fake(40, ALNUM, "bearer")
        openai = "sk" + "-" + fake(48, ALNUM, "openai")
        oauth = "ya" + "29." + fake(40, ALNUM + "_-", "oauth")
        hook = "https://hooks." + "slack.com/services/T" + fake(8, UPPER_DIGITS, "t") + "/B" + fake(8, UPPER_DIGITS, "b") + "/" + fake(24, ALNUM, "w")
        pypi = "pypi-" + "AgE" + fake(60, ALNUM + "_-", "pypi")
        return [
            ("jwt", jwt, f'Authorization = "{jwt}"'),
            ("aws-access-key-id", aws_id, f"key id: {aws_id}"),
            ("aws-secret-access-key", aws_secret, "aws_secret_" + f"access_key = {aws_secret}"),
            ("google-api-key", google, f"url?key={google}"),
            ("github-token", gh, f"token {gh}"),
            ("slack-token", slack, f"SLACK_BOT={slack}"),
            ("private-key-block", pem, pem),
            ("near-ed25519-private-key", near_sk[len("ed25519:"):], '"private_key": "' + near_sk + '"'),
            ("hex-private-key", hex_key, "PRIVATE" + f"_KEY={hex_key}"),
            ("url-with-password", "hunter2x", "postgres://app:" + "hunter2x" + "@db.internal:5432/x"),
            ("seed-phrase", phrase, "mnemonic: " + phrase),
            ("bearer-token", bearer, f"Authorization: Bearer {bearer}"),
            ("credential-assignment", generic, "api_" + f'key = "{generic}"'),
            ("credential-assignment", generic, f"secret: {generic}"),
            ("credential-assignment", generic, '{"access_' + f'token": "{generic}"}}'),
            ("credential-assignment", generic, "password = " + generic),
            ("credential-assignment", generic, "NEAR_INTENTS_EXPLORER_JWT=" + generic),
            ("anthropic-api-key", ant, f"ANTHROPIC={ant}"),
            ("stripe-live-key", stripe, f"STRIPE={stripe}"),
            ("npm-token", npm, f"//registry.npmjs.org/:_authToken={npm}"),
            ("openai-api-key", openai, f"OPENAI={openai}"),
            ("google-oauth-token", oauth, f"access {oauth}"),
            ("slack-webhook", hook, f"notify {hook}"),
            ("pypi-token", pypi, f"password = {pypi}"),
            ("gcp-service-account-file", '"type": "service_' + 'account"', '{"type": "service_' + 'account", "project_id": "x"}'),
        ]

    def test_each_rule_fires(self):
        for rule, value, text in self.samples():
            with self.subTest(rule=rule, shape=text[:12]):
                self.assertIn(rule, self.rules(text))

    def test_every_rule_in_the_list_has_a_sample(self):
        covered = {rule for rule, _, _ in self.samples()}
        for r in self.ss.RULES:
            self.assertIn(r.name, covered, f"rule {r.name} has no test sample")

    def test_a_whole_secret_is_never_printed(self):
        for rule, value, text in self.samples():
            if rule in ("private-key-block", "gcp-service-account-file"):
                continue  # a fixed public string, printed as is
            for f in self.ss.scan_text("sample.txt", text, self.ss.Allow()):
                for out in (f.shown, self.ss.show(f)):
                    with self.subTest(rule=rule):
                        self.assertNotIn(value, out)
                        self.assertNotIn(value[:6], out, "more than the first few characters were printed")
                self.assertLess(len(f.shown), 120)

    def test_look_alikes_are_not_flagged(self):
        public_key = "ed25519:" + fake(44, B58, "pubkey")
        signature = "ed25519:" + fake(88, B58, "signature")
        account = fake(64, HEX, "implicit-account")
        tx_hash = "4yh" + "eyJ" + fake(30, B58, "tx")  # a base58 transaction hash that happens to contain the letters
        quiet = [
            f'"public_key": "{public_key}"',
            f'"signature": "{signature}"',
            f'"account_id": "{account}"',
            f'"sha256": "{account}"',
            f"PRIVATE_TREASURY_ESCROW = \"{account}\"",
            f"tx {tx_hash}",
            "jwt = env(\"NEAR_INTENTS_EXPLORER_JWT\")",
            "api_key = os.environ[\"NEAR_INTENTS_EXPLORER_JWT\"]",
            "jwt_var = NEAR_INTENTS_EXPLORER_JWT_VALUE_NAME",
            "token: ${{ secrets.GITHUB_TOKEN }}",
            '"token_id": "nep141:wrap.near"',
            '"tokenIn": "nep141:eth-0xdac17f958d2ee523a2206206994597c13d831ec7.omft.near"',
            "password_hash = " + fake(40, ALNUM, "pwhash"),
            'api_key = "YOUR_API_KEY_GOES_HERE_12345"',
            "AK" + "IA" + "IOSFODNN7" + "EXAMPLE",
            "https://github.com/notveiker/near-flow-statement",
            "http://127.0.0.1:8080/path@x",
            "token = get_access_token_from_the_environment_v2(arg)",
            "secret = self.config.secrets.some_long_attribute_name2",
            "token = fetch_new_access_token_v2_for_user",
            "The token: a short word, and the secret is that nothing here is secret.",
        ]
        for text in quiet:
            with self.subTest(text=text[:40]):
                self.assertEqual(self.rules(text), set(), text)

    def test_file_names(self):
        flagged = [".env", ".env.local", "config/.env.production", "keys/server.pem", "id_rsa", "wallet.key.json",
                   "secrets/a.txt", "x/secrets/a.txt", ".near-credentials/mainnet/me.json", "service-account-prod.json",
                   "tls/site.key", "application_default_credentials.json"]
        fine = [".env.example", ".env.sample", "README.md", "id_rsa.pub", "data/raw/llama/volume_near-intents.json",
                "pipeline/common.py", "docs/secrets-policy.md"]
        for rel in flagged:
            self.assertTrue(self.ss.name_findings(rel, rel), f"{rel} should be flagged by name")
        for rel in fine:
            self.assertEqual(self.ss.name_findings(rel, rel), [], f"{rel} should not be flagged by name")

    def test_inline_pragma_and_value_allowlist(self):
        value = fake(64, HEX, "allowlisted")
        text = "PRIVATE" + f"_KEY={value}"
        self.assertIn("hex-private-key", self.rules(text))
        self.assertEqual(self.rules(text + "  # " + self.ss.PRAGMA), set(), "the pragma silences its own line")
        self.assertIn("hex-private-key", self.rules(text + "\nsecond line\n"), "other lines are unaffected")
        # a known-safe 64-hex hash, by value (with or without 0x, in either case)
        for allowed in (value, value.upper(), "0x" + value):
            self.assertEqual({f.rule for f in self.ss.scan_text("s", text, self.ss.Allow({allowed}))}, set())
        # ... and by the fingerprint a finding prints
        fp = self.ss.scan_text("s", text, self.ss.Allow())[0].fp
        self.assertRegex(fp, r"^[0-9a-f]{12}$")
        self.assertEqual({f.rule for f in self.ss.scan_text("s", text, self.ss.Allow({fp}))}, set())
        # a different hash is still flagged
        other = fake(64, HEX, "someone-else")
        self.assertIn("hex-private-key", {f.rule for f in self.ss.scan_text("s", text, self.ss.Allow({other}))})

    def test_a_placeholder_password_in_a_url_is_quiet_and_a_random_one_is_not(self):
        """Removing the placeholder rule (is_placeholder) from _url_password_ok would make every example URL a finding."""
        quiet = self.ss.scan_text("s", "DATABASE_URL = postgres://svc:your_password_here_1234@db.example/x", self.ss.Allow())
        self.assertEqual([f.rule for f in quiet], [])
        loud = self.ss.scan_text("s", "DATABASE_URL = postgres://svc:" + fake(20, ALNUM, "url-pw") + "@db.example/x", self.ss.Allow())
        self.assertEqual([f.rule for f in loud], ["url-with-password"])

    def test_weak_values_get_no_fingerprint(self):
        f = self.ss.scan_text("s", "postgres://app:" + "hunter2x" + "@db.internal/x", self.ss.Allow())[0]
        self.assertEqual(f.fp, "n/a", "the hash of a guessable password could be reversed with a dictionary")

    def test_a_flood_of_hits_in_one_file_is_cut_off(self):
        text = "\n".join("api_" + f'key = "{fake(40, ALNUM, str(i))}"' for i in range(150))
        found = self.ss.scan_text("big.txt", text, self.ss.Allow())
        self.assertEqual(len(found), self.ss.MAX_FINDINGS_PER_TEXT + 1)
        self.assertEqual(found[-1].rule, "too-many-findings")

    def test_tree_scan_in_a_plain_folder(self):
        ss = self.ss
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "notes.md").write_text("api_" + f'key = "{fake(40, ALNUM, "tree")}"\n', encoding="utf-8")
            (root / ".env").write_text("X=1\n", encoding="utf-8")
            (root / "ok.txt").write_text("nothing to see\n", encoding="utf-8")
            (root / "blob.bin").write_bytes(b"\0" + fake(40, ALNUM, "binary").encode())
            res = ss.scan_tree(root, ss.Allow())
            self.assertEqual(sorted((f.where, f.rule) for f in res.findings),
                             [(".env", "secret-file-name"), ("notes.md", "credential-assignment")])
            self.assertEqual(res.how, "walk")
            skipped = ss.scan_tree(root, ss.Allow(paths=("notes.md", ".env")))
            self.assertEqual(skipped.findings, [])

    def test_a_link_to_a_file_outside_the_tree_is_not_read(self):
        """A symlink is listed but not followed: what it points at is not part of this checkout, and following it could read
        any file the user can read."""
        ss = self.ss
        with tempfile.TemporaryDirectory() as d:
            outside, root = Path(d, "outside"), Path(d, "tree")
            outside.mkdir()
            root.mkdir()
            (outside / "leak.md").write_text("api_" + f'key = "{fake(40, ALNUM, "link")}"\n', encoding="utf-8")
            (root / "plain.txt").write_text("nothing to see\n", encoding="utf-8")
            try:
                os.symlink(outside / "leak.md", root / "link.md")
            except (OSError, NotImplementedError) as err:
                self.skipTest(f"this system cannot make a symbolic link: {err}")
            res = ss.scan_tree(root, ss.Allow())
            self.assertEqual(res.findings, [])
            self.assertEqual(res.files, 1, "only plain.txt was read; link.md was passed over")
            self.assertEqual(res.skipped, [])

    def test_a_file_over_the_size_limit_is_reported_as_skipped_not_read(self):
        ss = self.ss
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "big.md").write_text("api_" + f'key = "{fake(40, ALNUM, "big")}"\n', encoding="utf-8")
            (root / "small.md").write_text("fine\n", encoding="utf-8")
            size = (root / "big.md").stat().st_size
            with mock.patch.object(ss, "MAX_BYTES", size - 1):
                res = ss.scan_tree(root, ss.Allow())
            self.assertEqual(res.findings, [], "a file too large to read is not scanned")
            self.assertEqual(res.skipped, [f"big.md (larger than {size - 1} bytes)"], "but it is named, so the gap is visible")
            self.assertEqual(res.files, 1)
            with mock.patch.object(ss, "MAX_BYTES", size):
                again = ss.scan_tree(root, ss.Allow())
            self.assertEqual([f.rule for f in again.findings], ["credential-assignment"], "a file at the limit is still read")
            self.assertEqual(again.skipped, [])


class SecretScannerBlindSpotsThatWereClosed(unittest.TestCase):
    """Three ways a secret used to pass the scanner unseen, found by experiment and closed: a file with a NUL byte in its
    first 8 KB was skipped as binary (so UTF-16 text, which is what a Windows PowerShell `>` writes, and a text file that
    merely starts with a NUL, were never read); and any value that contained the letters test, fake or todo anywhere was
    taken for a placeholder. The fake keys are built at run time."""

    @classmethod
    def setUpClass(cls):
        cls.ss = scanner()

    @staticmethod
    def assignment(value: str) -> str:
        return "api_" + f'key = "{value}"\n'

    def scan_files(self, files: dict[str, bytes], allow=None):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name, data in files.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_bytes(data)
            return self.ss.scan_tree(root, allow or self.ss.Allow())

    # ---- (a) UTF-16 / UTF-32
    def test_utf16_and_utf32_text_is_decoded_and_scanned(self):
        text = self.assignment(fake(40, ALNUM, "wide"))
        for codec in ("utf-16", "utf-16-le", "utf-16-be", "utf-32", "utf-32-le", "utf-32-be", "utf-8-sig"):
            with self.subTest(codec=codec):   # "utf-16" and "utf-32" write a byte-order mark, the -le and -be forms do not
                res = self.scan_files({"notes.md": text.encode(codec)})
                self.assertEqual([(f.where, f.rule) for f in res.findings], [("notes.md", "credential-assignment")])

    def test_utf16_text_that_is_mostly_not_ascii_needs_its_byte_order_mark(self):
        """Without a mark, ASCII text in UTF-16 is recognised by its NUL bytes. Text with many CJK letters is not, so the mark
        decides: with it the key is found, without it the file is reported as unscannable (loud, not skipped)."""
        text = "密码密码密码密码密码密码密码密码 " + self.assignment(fake(40, ALNUM, "cjk"))
        with_mark = self.scan_files({"notes.md": text.encode("utf-16")})
        self.assertEqual([f.rule for f in with_mark.findings], ["credential-assignment"])
        for codec in ("utf-16-le", "utf-16-be"):
            without = self.scan_files({"notes.md": text.encode(codec)})
            self.assertEqual([f.rule for f in without.findings], ["unscannable-file"], codec)

    def test_a_utf16_file_with_a_few_non_ascii_letters_and_a_key_is_still_scanned(self):
        text = "Zugangsdaten für Ärzte: " + self.assignment(fake(40, ALNUM, "umlaut"))
        res = self.scan_files({"notes.md": text.encode("utf-16")})
        self.assertEqual([f.rule for f in res.findings], ["credential-assignment"])

    def test_the_utf16_finding_never_prints_the_whole_secret(self):
        value = fake(40, ALNUM, "wide-print")
        res = self.scan_files({"notes.md": self.assignment(value).encode("utf-16")})
        shown = " ".join(self.ss.show(f) for f in res.findings)
        self.assertNotIn(value, shown)
        self.assertNotIn(value[:8], shown)

    def test_binary_files_without_a_text_name_are_still_skipped_quietly(self):
        res = self.scan_files({"blob.bin": b"\0" + fake(40, ALNUM, "bin").encode(), "image.png": b"\x89PNG\r\n\x1a\n\0\0\0",
                               "dump.gz": b"\x1f\x8b\0\0", "data.parquet": b"PAR1\0\0"})
        self.assertEqual(res.findings, [])

    # ---- (b) NUL-prefixed text
    def test_a_text_file_that_starts_with_a_nul_is_reported_not_skipped(self):
        body = b"\0" + self.assignment(fake(40, ALNUM, "nul")).encode()
        names = ("notes.md", "run.sh", "Makefile", ".gitignore", ".env.production", "config.yaml", "config.yml", "x.txt", "d.csv",
                 "p.html", "pyproject.toml", "setup.cfg", "q.json", "m.py", "dir/sub/notes.MD")
        for name in names:
            with self.subTest(name=name):
                found = [(f.where, f.rule) for f in self.scan_files({name: body}).findings if f.rule == "unscannable-file"]
                self.assertEqual(found, [(name, "unscannable-file")])

    def test_an_unscannable_file_fails_the_cli_and_an_allow_path_silences_it(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "notes.md").write_bytes(b"\0 hello\n")
            script = str(ROOT / "scripts" / "scan_secrets.py")
            run = lambda *extra: subprocess.run([sys.executable, script, "--root", d, *extra], capture_output=True,  # noqa: E731
                                                text=True, encoding="utf-8", check=False)
            p = run()
            self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
            self.assertRegex(p.stderr, r"FAIL  notes\.md  \[unscannable-file\]")
            self.assertIn("scan_secrets: FAIL, 1 finding(s)", p.stdout)
            allowed = run("--allow-path", "notes.md")
            self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)

    def test_which_names_count_as_text(self):
        for rel in ("a.md", "a/b.PY", "x.json", "x.sh", "x.yml", "x.yaml", "x.txt", "x.csv", "x.html", "x.toml", "x.cfg",
                    "Makefile", "LICENSE", ".gitignore", ".gitattributes", ".env", ".env.local", "dir/.env.production"):
            self.assertTrue(self.ss.looks_like_text(rel), rel)
        for rel in ("a.bin", "a.png", "a.zip", "a.gz", "a.pdf", "a.parquet", "a.so", "", "dir/"):
            self.assertFalse(self.ss.looks_like_text(rel), rel)

    # ---- (c) placeholders
    def test_a_real_looking_key_that_contains_test_fake_or_todo_is_still_flagged(self):
        key = fake(40, ALNUM, "embedded")
        for word in ("test", "fake", "todo", "dummy", "sample", "insert", "replace"):
            value = key[:14] + word + key[14:]
            with self.subTest(word=word):
                self.assertIn("credential-assignment", {f.rule for f in self.ss.scan_text("s", self.assignment(value), self.ss.Allow())})

    def test_documentation_placeholders_stay_quiet(self):
        key = fake(30, ALNUM, "doc")
        quiet = ["YOUR_API_KEY_GOES_HERE_12345", "your-token-here-1234567890", "my-test-key-1234567890abcdef12",
                 "test_" + key, "example_" + key, "TODO_replace_this_secret_1234567", "changeme_" + key, "xxxxxxxxxxxxxxxxxxxxxxxx",
                 "<your-token-goes-here-1234>", "${NEAR_INTENTS_EXPLORER_JWT}_1234567890", "myTestKeyFromTheDocs12345",
                 "dummy-secret-value-1234567890", "sample.token.value.1234567890"]
        for value in quiet:
            with self.subTest(value=value):
                self.assertEqual({f.rule for f in self.ss.scan_text("s", self.assignment(value), self.ss.Allow())}, set())

    def test_is_placeholder_unit(self):
        ss = self.ss
        for v in ("test", "my_test_key", "my-test-key", "my.test.key", "test/key", "TEST", "MyTestKey", "a1_Fake_b2", "todo",
                  "YOUR_KEY", "example", "EXAMPLEKEY", "changeme", "ChangeMe", "change-me", "redacted", "<token>", "***", "xxxxxx",
                  "${X}", "{{ x }}", "%s", "aaa...bbb"):
            self.assertTrue(ss.is_placeholder(v), v)
        for v in ("atestb", "contestant", "latest1234", "mistodoes", "Fakery", "tested", "testing", "unsampled", "x1testy2",
                  fake(40, ALNUM, "plain")):
            self.assertFalse(ss.is_placeholder(v), v)

    # ---- (d) the limits are written down
    def test_the_module_docstring_lists_what_the_scanner_cannot_see(self):
        doc = self.ss.__doc__
        for phrase in ("What it cannot see", "split over several lines", "base64", "no recognisable shape", "UTF-16",
                       "unscannable-file", "not a proof"):
            self.assertIn(phrase, doc)

    def test_the_rule_counts_the_readme_quotes_are_unchanged(self):
        self.assertEqual((len(self.ss.RULES), len(self.ss.NAME_RULES)), (21, 7))


@unittest.skipUnless(shutil.which("git"), "git is not installed")
class SecretScannerHistory(unittest.TestCase):
    """A secret that was committed and then deleted is still in history, and --history must find it."""

    def commit(self, repo: Path, message: str) -> None:
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false",
                        "commit", "-q", "--allow-empty", "-m", message], cwd=repo, check=True, capture_output=True)

    def make_repo(self, repo: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
        (repo / "keep.txt").write_text("harmless\n", encoding="utf-8")
        (repo / "oops.md").write_text("api_" + f'key = "{fake(40, ALNUM, "history")}"\n', encoding="utf-8")
        (repo / ".env").write_text("X=1\n", encoding="utf-8")
        subprocess.run(["git", "add", "-f", "-A"], cwd=repo, check=True, capture_output=True)
        self.commit(repo, "add files")
        subprocess.run(["git", "rm", "-q", "oops.md", ".env"], cwd=repo, check=True, capture_output=True)
        self.commit(repo, "remove them again, and paste a token in the message: " + "gh" + "p_" + fake(36, ALNUM, "msg"))

    def test_history_finds_deleted_secrets_files_and_messages(self):
        ss = scanner()
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            self.make_repo(repo)
            self.assertEqual(ss.scan_tree(repo, ss.Allow()).findings, [], "the working tree is clean")
            res = ss.scan_history(repo, ss.Allow())
            found = {(f.rule) for f in res.findings}
            self.assertEqual(found, {"credential-assignment", "secret-file-name", "github-token"})
            self.assertEqual((res.commits, res.shallow), (2, False))
            where = " ".join(f.where for f in res.findings)
            self.assertIn("oops.md", where)
            self.assertIn("commit message", where)

    def test_history_decodes_utf16_blobs_and_reports_text_that_starts_with_a_nul(self):
        ss = scanner()
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
            (repo / "wide.md").write_bytes(("api_" + f'key = "{fake(40, ALNUM, "hist-wide")}"\n').encode("utf-16"))
            (repo / "nul.md").write_bytes(b"\0nothing to see here\n")
            (repo / "blob.bin").write_bytes(b"\0\1\2\3")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
            self.commit(repo, "add three files")
            res = ss.scan_history(repo, ss.Allow())
            self.assertEqual(sorted((f.rule, f.where.split()[-1]) for f in res.findings),
                             [("credential-assignment", "wide.md"), ("unscannable-file", "nul.md")])

    def test_empty_repository_and_shallow_clone(self):
        ss = scanner()
        with tempfile.TemporaryDirectory() as d:
            empty = Path(d) / "empty"
            empty.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=empty, check=True, capture_output=True)
            res = ss.scan_history(empty, ss.Allow())
            self.assertEqual((res.findings, res.blobs, res.commits), ([], 0, 0))
            full = Path(d) / "full"
            full.mkdir()
            self.make_repo(full)
            shallow = Path(d) / "shallow"
            clone = subprocess.run(["git", "clone", "-q", "--depth", "1", full.as_uri(), str(shallow)], capture_output=True, check=False)
            if clone.returncode != 0:
                self.skipTest("this git cannot make a shallow clone from a file:// URL")
            res = ss.scan_history(shallow, ss.Allow())
            self.assertTrue(res.shallow)
            self.assertEqual(res.commits, 1, "only the newest commit is in a depth-1 clone")

    def test_a_blob_over_the_size_limit_is_skipped_and_reported(self):
        ss = scanner()
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            self.make_repo(repo)
            before = ss.MAX_BYTES
            ss.MAX_BYTES = 20  # every file in the sample repository is bigger than this
            try:
                res = ss.scan_history(repo, ss.Allow())
            finally:
                ss.MAX_BYTES = before
            self.assertNotIn("credential-assignment", {f.rule for f in res.findings})
            self.assertTrue(any("larger than 20 bytes" in note for note in res.skipped), res.skipped)

    def test_cli_exit_status(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            self.make_repo(repo)
            script = str(ROOT / "scripts" / "scan_secrets.py")
            tree = subprocess.run([sys.executable, script, "--root", str(repo)], capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(tree.returncode, 0, tree.stderr + tree.stdout)
            hist = subprocess.run([sys.executable, script, "--root", str(repo), "--history"], capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(hist.returncode, 1, hist.stdout)
            self.assertIn("scan_secrets: FAIL", hist.stdout)
            self.assertEqual(sum(ln.startswith("FAIL") for ln in hist.stderr.splitlines()), 3, hist.stderr)
            self.assertNotIn(fake(40, ALNUM, "history"), hist.stderr, "the whole secret must not be printed")
        with tempfile.TemporaryDirectory() as d:  # not a repository: --history cannot run
            p = subprocess.run([sys.executable, script, "--root", d, "--history"], capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)


# -------------------------------------------------------------------- no key reaches a committed file through a fetcher
class FetchersRecordNoCredentials(unittest.TestCase):
    """pipeline/fetch_issuance.py reads NEAR_ARCHIVAL_RPC from the environment and used to write the URL, verbatim, into
    data/raw/rpc/epoch_issuance.json ("source") and data/MANIFEST.json: a keyed URL (a key in the path or the query, or
    user:password@) would have been committed by the next refresh. Only scheme and host are recorded now."""

    KEYED = "https://user:pw@rpc.example/KEY123?apikey=abc"
    SECRETS = ("user:pw", "pw@", "KEY123", "apikey", "=abc", "@")

    def test_endpoint_origin_keeps_scheme_and_host_only(self):
        for url, want in ((self.KEYED, "https://rpc.example"),
                          ("https://archival-rpc.mainnet.fastnear.com", "https://archival-rpc.mainnet.fastnear.com"),
                          ("https://archival-rpc.mainnet.fastnear.com/", "https://archival-rpc.mainnet.fastnear.com"),
                          ("  https://rpc.example/v2/KEY123  ", "https://rpc.example"),
                          ("https://rpc.example?token=abc", "https://rpc.example"),
                          ("https://rpc.example#KEY123", "https://rpc.example"),
                          ("https://tok3n@rpc.example/", "https://rpc.example"),
                          ("http://RPC.Example:8545/path?x=1", "http://rpc.example:8545"),
                          ("https://[::1]:3030/KEY123", "https://[::1]:3030")):
            with self.subTest(url=url):
                self.assertEqual(C.endpoint_origin(url), want)

    def test_endpoint_origin_rejects_what_it_cannot_reduce_without_echoing_it(self):
        for bad in ("rpc.example/KEY123", "KEY123", "", "ftp://rpc.example/KEY123", "https:///KEY123", "https://rpc.example:99999/KEY123",
                    "//rpc.example/KEY123", "https://host\\KEY123", "https://host.example%2fKEY123/x", "https://exa mple/KEY123"):
            with self.subTest(bad=bad), self.assertRaises(ValueError) as caught:
                C.endpoint_origin(bad)
            self.assertNotIn("KEY123", str(caught.exception))

    def test_fetch_issuance_records_only_the_origin(self):
        with mock.patch.object(FI, "RPC", self.KEYED):
            self.assertEqual(FI.recorded_rpc(), "https://rpc.example")
            with mock.patch.object(FI, "protocol_config", lambda h: {"epoch_length": 43200, "num_blocks_per_year": 31536000,
                                                                      "max_inflation_rate": [1, 40]}), \
                    mock.patch.object(FI, "walk", lambda n: [[h, "hash", "eid", 0, "0", "0", h - 1, "prev", "0", "0"]
                                                              for h in FI.TREASURY_CHECKS]), \
                    mock.patch.object(FI, "block", lambda b: {"header": {"hash": "h", "timestamp_nanosec": 1, "total_supply": "0",
                                                                         "prev_hash": "p", "height": 1}, "chunks": []}), \
                    mock.patch.object(FI, "view", lambda a, h: {"amount": "0", "locked": "0"}):
                obj = FI.fetch()
        self.assertTrue(obj["source"].startswith("https://rpc.example JSON-RPC `block`"), obj["source"])
        dumped = json.dumps(obj)
        for secret in self.SECRETS:
            self.assertNotIn(secret, dumped, secret)

    def test_the_manifest_source_written_by_main_has_no_credential_either(self):
        recorded: list[tuple[str, str]] = []
        stub = {"epochs": [], "source": "x"}
        with mock.patch.object(FI, "RPC", self.KEYED), mock.patch.object(FI, "fetch", lambda: stub), \
                mock.patch.object(FI, "write_raw", lambda rel, obj, source: recorded.append((rel, source))), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(FI.main([]), 0)
        self.assertEqual(len(recorded), 1)
        rel, source = recorded[0]
        self.assertEqual(rel, "rpc/epoch_issuance.json")
        self.assertTrue(source.startswith("https://rpc.example block headers at epoch boundaries"), source)
        for secret in self.SECRETS:
            self.assertNotIn(secret, source, secret)

    def test_a_malformed_endpoint_stops_the_run_before_any_request(self):
        calls: list[object] = []
        with mock.patch.object(FI, "RPC", "rpc.example/KEY123"), mock.patch.object(FI, "fetch", lambda: calls.append("fetch")), \
                mock.patch.object(FI, "write_raw", lambda *a, **k: calls.append("write_raw")):   # never the real committed file
            with self.assertRaises(ValueError) as caught:
                FI.main([])
        self.assertEqual(calls, [])
        self.assertNotIn("KEY123", str(caught.exception))

    def test_the_variable_is_documented(self):
        self.assertIn("NEAR_ARCHIVAL_RPC", FI.__doc__)
        self.assertIn("scheme and host", FI.__doc__)

    def test_record_and_write_raw_refuse_a_url_that_carries_a_credential(self):
        for source in (self.KEYED, "https://rpc.example/v2?api_key=abc", "https://rpc.example/v2?apikey=abc",
                       "https://rpc.example/#access_token=abc", "https://rpc.example/?accessKey=abc", "https://rpc.example/?privatekey=abc",
                       "https://rpc.example/?pass=abc", "https://rpc.example/?authkey=abc", "https://rpc.example/?bearer=abc",
                       "https://rpc.example/?X-Amz-Credential=abc", "https://rpc.example/?x%2dapi%2dkey=abc",
                       "https://tok3n@rpc.example/x", "https://user:pw@rpc.example/x",
                       "https://rpc.example/v2?api-key=abc", "https://rpc.example/?access_token=abc",
                       "see https://rpc.example/x?x_cg_demo_api_key=abc", "https://rpc.example/?Authorization=abc",
                       "https://rpc.example/?client_secret=abc"):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
                data = Path(tmp) / "data"
                with mock.patch.object(C, "DATA", data), mock.patch.object(C, "RAW", data / "raw"), \
                        mock.patch.object(C, "MANIFEST", data / "MANIFEST.json"):
                    with self.assertRaises(ValueError) as caught:
                        C.write_raw("rpc/x.json", {"a": 1}, source)
                    self.assertNotIn("abc", str(caught.exception))
                    self.assertFalse((data / "raw" / "rpc" / "x.json").exists(), "nothing is written when the source is refused")
                    self.assertFalse((data / "MANIFEST.json").exists())

    def test_record_refuses_a_credential_in_its_extra_fields_and_writes_no_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "data"
            (data / "raw" / "x").mkdir(parents=True)
            path = data / "raw" / "x" / "y.json"
            path.write_bytes(b'{"a":1}\n')
            with mock.patch.object(C, "DATA", data), mock.patch.object(C, "RAW", data / "raw"), \
                    mock.patch.object(C, "MANIFEST", data / "MANIFEST.json"):
                with self.assertRaises(ValueError) as caught:
                    C.record(path, "ok", {"note": "https://x.example/?api_key=abc"})
                self.assertNotIn("abc", str(caught.exception))
                self.assertFalse((data / "MANIFEST.json").exists())

    def test_record_and_write_raw_still_accept_the_sources_the_fetchers_use(self):
        for source in ("https://api.llama.fi/summary/dexs/near-intents?dataType=dailyVolume",
                       "https://api.coingecko.com/api/v3/coins/<coin>/market_chart?vs_currency=usd&days=90&interval=daily",
                       "https://explorer.near-intents.org/api/v0/transactions?statuses=SUCCESS (per-day cursor pull)",
                       "bigquery: sql/staking_flows_daily.sql", "rpc view_account at block 223230811",
                       "https://design.example/?author=1&keyword=2&monkey=3"):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
                data = Path(tmp) / "data"
                with mock.patch.object(C, "DATA", data), mock.patch.object(C, "RAW", data / "raw"), \
                        mock.patch.object(C, "MANIFEST", data / "MANIFEST.json"):
                    path = C.write_raw("x/y.json", {"a": 1}, source)
                    self.assertEqual(path.read_bytes(), b'{"a":1}\n')
                    entry = json.loads((data / "MANIFEST.json").read_bytes())["files"]["raw/x/y.json"]
                    self.assertEqual((entry["source"], entry["bytes"]), (source, 8))

    def test_writers_produce_the_same_bytes_whatever_the_platform_default(self):
        """Canonical JSON plus one LF, UTF-8, no CRLF: the form every committed raw file and the manifest are in."""
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "data"
            with mock.patch.object(C, "DATA", data), mock.patch.object(C, "RAW", data / "raw"), \
                    mock.patch.object(C, "MANIFEST", data / "MANIFEST.json"):
                path = C.write_raw("a/b.json", {"b": [1, 2], "a": "é"}, "test source")
                self.assertEqual(path.read_bytes(), b'{"a":"\\u00e9","b":[1,2]}\n')
                raw = (data / "MANIFEST.json").read_bytes()
                self.assertTrue(raw.endswith(b"}\n") and b"\r" not in raw)
                self.assertEqual(raw, (json.dumps(json.loads(raw), indent=1, sort_keys=True) + "\n").encode("utf-8"))

    # ---- what is committed
    def test_the_committed_issuance_file_and_manifest_hold_no_keyed_url(self):
        d = json.loads((ROOT / "data" / "raw" / "rpc" / "epoch_issuance.json").read_text(encoding="utf-8"))
        first = d["source"].split()[0]
        self.assertEqual(C.endpoint_origin(first), first, "the committed source is already in its sanitised form")
        files = json.loads((ROOT / "data" / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
        self.assertGreater(len(files), 40)
        for rel, entry in files.items():
            for key, value in entry.items():
                if isinstance(value, str):
                    with self.subTest(file=rel, field=key):
                        C.refuse_credentials(value, f"{key} of {rel}")

    def test_no_text_in_any_committed_json_file_under_data_carries_a_credential_bearing_url(self):
        def walk(obj, where):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    yield from walk(v, f"{where}/{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    yield from walk(v, f"{where}/{i}")
            elif isinstance(obj, str) and "://" in obj:
                yield where, obj

        checked = 0
        for path in sorted((ROOT / "data").rglob("*.json")):
            for where, text in walk(json.loads(path.read_text(encoding="utf-8")), path.relative_to(ROOT).as_posix()):
                checked += 1
                try:
                    C.refuse_credentials(text)
                except ValueError:
                    self.fail(f"{where} holds a URL with a credential in it")
        self.assertGreater(checked, 5, "the walk found almost no URLs, so it proved nothing")


# ---------------------------------------------------------------------------------------- fresh-clone script
@unittest.skipUnless(shutil.which("bash"), "bash is not installed")
class FreshCloneScript(unittest.TestCase):
    """The script runs this test suite itself, so it is only parsed here, never run. CI runs it for real."""

    SCRIPT = ROOT / "scripts" / "fresh_clone_check.sh"

    def test_it_parses_and_uses_strict_mode(self):
        p = subprocess.run(["bash", "-n", str(self.SCRIPT)], capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("set -euo pipefail", self.SCRIPT.read_text(encoding="utf-8"))

    def test_it_requires_the_files_that_keep_the_hashes_valid(self):
        """A copy without .gitattributes is not ready to submit: a Windows clone of it would fail every raw-data hash."""
        text = self.SCRIPT.read_text(encoding="utf-8")
        listed = set(re.search(r'REQUIRED_FILES="([^"]*)"', text).group(1).split())
        for name in (".gitattributes", "PREREG.md", "PREREG-ADDENDUM.md", "data/MANIFEST.json", "scripts/scan_secrets.py"):
            self.assertIn(name, listed)

    def test_help_names_the_modes(self):
        p = subprocess.run(["bash", str(self.SCRIPT), "--help"], capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(p.returncode, 0, p.stderr)
        for word in ("--worktree", "URL", "--keep", "PYTHON"):
            self.assertIn(word, p.stdout)

    def test_a_bad_option_is_a_usage_error(self):
        p = subprocess.run(["bash", str(self.SCRIPT), "--no-such-option"], capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn("unknown option", p.stderr)

    @unittest.skipUnless(shutil.which("git"), "git is not installed")
    def test_a_failed_clone_exits_2_and_removes_its_temporary_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "no-such-repository.git")
            env = {**os.environ, "TMPDIR": tmp}
            p = subprocess.run(["bash", str(self.SCRIPT), missing], capture_output=True, text=True, encoding="utf-8", check=False, env=env)
            self.assertEqual(p.returncode, 2, p.stderr)
            self.assertEqual(list(Path(tmp).iterdir()), [], "the temporary directory was not removed")


# ---------------------------------------------------------------------------------------------------- workflows
class Workflows(unittest.TestCase):
    """Text checks, because the repository cannot depend on a YAML parser."""

    @staticmethod
    def active_lines(name: str) -> list[str]:
        text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        return [re.sub(r"\s+#.*$", "", ln).rstrip() for ln in text.splitlines() if not ln.lstrip().startswith("#")]

    def test_ci_runs_the_offline_checks_with_a_read_only_token(self):
        ci = "\n".join(self.active_lines("ci.yml"))
        self.assertRegex(ci, r"(?m)^on:\n  push:\n  pull_request:")
        self.assertRegex(ci, r"(?m)^permissions:\n  contents: read\n")
        self.assertNotRegex(ci, r"(?m)^\s+(contents|pages|id-token|actions|packages|pull-requests|checks): write")
        self.assertNotIn("pull_request_target", ci)
        self.assertNotRegex(ci, r"\$\{\{\s*secrets\.", "CI needs no secret")
        self.assertNotIn("secrets: inherit", ci)
        self.assertRegex(ci, r"(?m)^concurrency:\n  group: .+\n  cancel-in-progress: true")
        self.assertRegex(ci, r'python-version: \["3\.10", "3\.13"\]')
        # A line scan, not a regex with nested quantifiers: such a pattern backtracks exponentially when the line is missing,
        # so an edit of the checkout step would hang this test instead of failing it.
        lines = ci.split("\n")
        start = next((k for k, ln in enumerate(lines) if re.search(r"actions/checkout@v\d+", ln)), None)
        self.assertIsNotNone(start, "ci.yml no longer uses actions/checkout")
        step = []
        for ln in lines[start + 1:]:
            if ln.lstrip().startswith("- "):
                break
            step.append(ln.strip())
        self.assertIn("fetch-depth: 0", step, "the secret scan reads every commit and the freeze tag must exist: no shallow checkout")
        for command in ("python3 -m pipeline.check --manifest", "python3 -m pipeline.compute",
                        "git diff --exit-code data/metrics.json data/series.json", "python3 -m pipeline.check --numbers",
                        "python3 -m unittest discover -s tests", "python3 -m pipeline.render --check",
                        "python3 scripts/scan_secrets.py", "python3 scripts/scan_secrets.py --history",
                        "bash scripts/fresh_clone_check.sh"):
            self.assertRegex(ci, r"(?m)^\s+run: " + re.escape(command) + r"( -v)?$", command)

    def test_ci_never_fetches_or_installs(self):
        ci = "\n".join(self.active_lines("ci.yml"))
        for forbidden in ("pipeline.fetch", "pipeline.bq_run", "make fetch", "make explorer", "make bq", "score_forward",
                          "pip install", "pip3 install", "curl ", "wget ", "npm "):
            self.assertNotIn(forbidden, ci)

    def test_pages_publishes_only_the_committed_site_folder(self):
        pages = "\n".join(self.active_lines("pages.yml"))
        self.assertRegex(pages, r"(?m)^on:\n  push:\n    branches: \[main\]\n    paths:\n      - \"site/\*\*\"\n  workflow_dispatch:")
        self.assertRegex(pages, r"(?m)^permissions:\n  contents: read\n  pages: write\n  id-token: write\n")
        self.assertRegex(pages, r"environment:\n\s+name: github-pages")
        self.assertRegex(pages, r"uses: actions/configure-pages@v5")
        self.assertRegex(pages, r"uses: actions/upload-pages-artifact@v3\n\s+with:\n\s+path: site\n")
        self.assertRegex(pages, r"uses: actions/deploy-pages@v4")
        runs = [ln.strip() for ln in pages.splitlines() if re.match(r"\s+(- )?run:", ln)]
        self.assertEqual(len(runs), 1, "pages.yml must not build anything; its one shell step only checks that site/index.html exists")
        self.assertTrue(runs[0].startswith("run: test -s site/index.html"), runs[0])

    def test_pages_header_explains_the_two_settings(self):
        head = "\n".join((ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8").splitlines()[:14])
        self.assertIn("public", head)
        self.assertIn("GitHub Actions", head)

    def test_every_action_is_pinned_to_a_release(self):
        for name in ("ci.yml", "pages.yml"):
            for ln in self.active_lines(name):
                m = re.search(r"\buses:\s*(\S+)", ln)
                if m:
                    ref = m.group(1).partition("@")[2]
                    self.assertRegex(ref, r"^(v\d+(\.\d+){0,2}|[0-9a-f]{40})$", f"{name}: {m.group(1)}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
