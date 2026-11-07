"""Integrity tests, offline and fast: the frozen pre-registration, the secret-handling files, the raw-data manifest, the
secret scanner (scripts/scan_secrets.py) and the CI / Pages workflows.

Run: python3 -m unittest discover -s tests   (or make test)

Tests that need git skip themselves when the folder is not a git checkout (a zip download, or the copy that
scripts/fresh_clone_check.sh --worktree makes) or when the prereg-freeze tag is missing (a shallow clone).
Secret-shaped sample text is built at run time from non-secret pieces, so this file contains no literal that the
scanner would flag.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline.check import check_manifest  # noqa: E402

FROZEN_PREREG_SHA256 = "19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240"
FREEZE_TAG = "prereg-freeze"

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
    p = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
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
            diff = git("diff", FREEZE_TAG, *other, "--", "PREREG.md", text=True)
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertEqual(diff.stdout, "", f"PREREG.md differs from tag {FREEZE_TAG}:\n{diff.stdout[:500]}")
        ancestor = git("merge-base", "--is-ancestor", FREEZE_TAG, "HEAD")
        self.assertEqual(ancestor.returncode, 0, f"tag {FREEZE_TAG} is not an ancestor of HEAD")


# ----------------------------------------------------------------------------------------------- .gitignore
class GitignoreCoversSecrets(unittest.TestCase):
    PATTERNS = (".env", ".env.*", "secrets/", "*.key.json")

    def test_patterns_are_listed(self):
        lines = {ln.strip() for ln in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.lstrip().startswith("#")}
        for pattern in self.PATTERNS:
            self.assertIn(pattern, lines, f".gitignore must list {pattern}")

    def test_git_agrees(self):
        if not own_git():
            self.skipTest("not a git checkout")
        for path in (".env", ".env.local", ".env.production", "secrets/anything.txt", "deep/secrets/a.json",
                     "wallet.key.json", "service-account-prod.json",
                     # key material that scripts/scan_secrets.py also flags by name
                     "tls/server.key", "keys/a.pem", "id_rsa", ".near-credentials/mainnet/me.json",
                     "client_secret_123.json", "application_default_credentials.json"):
            self.assertEqual(git("check-ignore", "-q", "--no-index", path).returncode, 0, f"{path} is not ignored")
        # Files that must be committed are not swallowed by an ignore rule.
        for path in ("README.md", "data/MANIFEST.json", "data/raw/escrow/deliveries.csv", "site/index.html",
                     "scripts/scan_secrets.py", ".github/workflows/ci.yml", "data/forward/score_x/result.json"):
            self.assertEqual(git("check-ignore", "-q", "--no-index", path).returncode, 1, f"{path} is ignored")


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


# --------------------------------------------------------------------------------------------- secret scanner
class SecretScannerOnThisRepo(unittest.TestCase):
    def test_working_tree_has_no_secrets(self):
        p = subprocess.run([sys.executable, "scripts/scan_secrets.py"], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        self.assertIn("scan_secrets: PASS", p.stdout)
        scanned = int(re.search(r"working tree: (\d+) files", p.stdout).group(1))
        self.assertGreater(scanned, 50, "the scan looked at too few files to mean anything")

    def test_rules_can_be_listed(self):
        p = subprocess.run([sys.executable, "scripts/scan_secrets.py", "--rules"], cwd=ROOT, capture_output=True, text=True, check=False)
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
            tree = subprocess.run([sys.executable, script, "--root", str(repo)], capture_output=True, text=True, check=False)
            self.assertEqual(tree.returncode, 0, tree.stderr + tree.stdout)
            hist = subprocess.run([sys.executable, script, "--root", str(repo), "--history"], capture_output=True, text=True, check=False)
            self.assertEqual(hist.returncode, 1, hist.stdout)
            self.assertIn("scan_secrets: FAIL", hist.stdout)
            self.assertEqual(sum(ln.startswith("FAIL") for ln in hist.stderr.splitlines()), 3, hist.stderr)
            self.assertNotIn(fake(40, ALNUM, "history"), hist.stderr, "the whole secret must not be printed")
        with tempfile.TemporaryDirectory() as d:  # not a repository: --history cannot run
            p = subprocess.run([sys.executable, script, "--root", d, "--history"], capture_output=True, text=True, check=False)
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)


# ---------------------------------------------------------------------------------------- fresh-clone script
@unittest.skipUnless(shutil.which("bash"), "bash is not installed")
class FreshCloneScript(unittest.TestCase):
    """The script runs this test suite itself, so it is only parsed here, never run. CI runs it for real."""

    SCRIPT = ROOT / "scripts" / "fresh_clone_check.sh"

    def test_it_parses_and_uses_strict_mode(self):
        p = subprocess.run(["bash", "-n", str(self.SCRIPT)], capture_output=True, text=True, check=False)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("set -euo pipefail", self.SCRIPT.read_text(encoding="utf-8"))

    def test_help_names_the_modes(self):
        p = subprocess.run(["bash", str(self.SCRIPT), "--help"], capture_output=True, text=True, check=False)
        self.assertEqual(p.returncode, 0, p.stderr)
        for word in ("--worktree", "URL", "--keep", "PYTHON"):
            self.assertIn(word, p.stdout)

    def test_a_bad_option_is_a_usage_error(self):
        p = subprocess.run(["bash", str(self.SCRIPT), "--no-such-option"], capture_output=True, text=True, check=False)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn("unknown option", p.stderr)

    @unittest.skipUnless(shutil.which("git"), "git is not installed")
    def test_a_failed_clone_exits_2_and_removes_its_temporary_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "no-such-repository.git")
            env = {**os.environ, "TMPDIR": tmp}
            p = subprocess.run(["bash", str(self.SCRIPT), missing], capture_output=True, text=True, check=False, env=env)
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
        self.assertRegex(ci, r"actions/checkout@v\d+\n\s+with:\n(\s+.+\n)*?\s+fetch-depth: 0")
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
