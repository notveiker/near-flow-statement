"""`python3 -m pipeline.check` from the command line, and the offline commands under a non-UTF-8 locale.

These are subprocess tests, because what they pin is the exit status and the exact output of the commands the README
quotes: `check: PASS`, `FAIL  hash mismatch: ...`, and a refusal (exit 2, no PASS) of anything that is not an option.
The tampered trees are temporary copies of the repository's code and data. Nothing here writes into the repository.

Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import ast
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
from pipeline import check as CHECK  # noqa: E402

# A locale that is not UTF-8, as a stricter CI image, an old Windows code page or a CJK locale would give.
NON_UTF8 = {"PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0", "LC_ALL": "C", "LANG": "C"}
CLEAN_ENV_DROP = ("PYTHONPATH", "PYTHONUTF8", "PYTHONCOERCECLOCALE", "PYTHONIOENCODING", "LC_ALL", "LANG", "LC_CTYPE")


def environment(**extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in CLEAN_ENV_DROP}
    env.update(extra)
    return env


def python(args: list[str], cwd: Path = ROOT, **env: str) -> subprocess.CompletedProcess:
    """Run this interpreter in `cwd`; the output is returned as str (utf-8, undecodable bytes replaced)."""
    p = subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, env=environment(**env), check=False)
    return subprocess.CompletedProcess(p.args, p.returncode, p.stdout.decode("utf-8", "replace"),
                                       p.stderr.decode("utf-8", "replace"))


def check(*args: str, cwd: Path = ROOT, **env: str) -> subprocess.CompletedProcess:
    return python(["-m", "pipeline.check", *args], cwd=cwd, **env)


def copy_of_the_repository(dest: Path) -> Path:
    """The code and data that pipeline.check and pipeline.compute read, copied to `dest` (a few MB, well under a second)."""
    shutil.copytree(ROOT / "pipeline", dest / "pipeline", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "data", dest / "data")
    shutil.copytree(ROOT / "docs", dest / "docs")
    for name in ("README.md", "THESIS.md", "PREREG-ADDENDUM.md"):
        shutil.copy2(ROOT / name, dest / name)
    return dest


class ManifestKeysAreIdenticalOnEveryPlatform(unittest.TestCase):
    """data/MANIFEST.json keys are `raw/llama/x.json`. str(path) on Windows is `raw\\llama\\x.json`, which is never a key: every
    file would be "not in manifest" and `record` would write keys that nothing reads back. This cannot be run on Windows here, so
    the Windows flavour of pathlib stands in for it."""

    KEY = "raw/llama/volume_maya-protocol.json"

    def test_the_key_is_the_path_below_data_with_forward_slashes(self):
        from pathlib import PurePosixPath, PureWindowsPath
        from pipeline import common as C
        self.assertEqual(C.manifest_key(PureWindowsPath("C:/repo/data/" + self.KEY), PureWindowsPath("C:/repo/data")), self.KEY)
        self.assertEqual(C.manifest_key(PurePosixPath("/repo/data/" + self.KEY), PurePosixPath("/repo/data")), self.KEY)
        listed = json.loads((ROOT / "data" / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
        for key in listed:
            with self.subTest(key=key):
                self.assertEqual(C.manifest_key(ROOT / "data" / key, ROOT / "data"), key)

    def test_check_manifest_finds_a_listed_file_whose_path_is_a_windows_path(self):
        from pathlib import PureWindowsPath

        class WindowsFile(PureWindowsPath):
            def is_symlink(self) -> bool:
                return False

            def is_file(self) -> bool:
                return True

        class WindowsRaw:
            parent = PureWindowsPath("C:/repo/data")

            def rglob(self, pattern: str) -> list:
                return [WindowsFile("C:/repo/data/" + ManifestKeysAreIdenticalOnEveryPlatform.KEY)]

        with mock.patch.object(CHECK, "RAW", WindowsRaw()), mock.patch.object(CHECK, "verify_manifest", lambda: []), \
                mock.patch.object(CHECK, "load_manifest", lambda: {"files": {self.KEY: {}}}):
            self.assertEqual(CHECK.check_manifest(), [])


class CheckCommandLine(unittest.TestCase):
    """pipeline.check used to treat any argument list without --manifest or --numbers as 'run nothing', then printed
    `check: PASS` and exited 0, so `--help` or a typo looked like a success on a tampered tree."""

    def test_the_documented_forms_pass_and_print_exactly_check_pass(self):
        for args in ((), ("--manifest",), ("--numbers",), ("--manifest", "--numbers"), ("--numbers", "--manifest")):
            with self.subTest(args=args):
                p = check(*args)
                self.assertEqual((p.returncode, p.stdout, p.stderr), (0, "check: PASS\n", ""))

    def test_an_argument_that_is_not_an_option_is_a_usage_error_and_never_a_pass(self):
        for args in (("--manifst",), ("--numbrs",), ("--Manifest",), ("manifest",), ("--no-such-flag",), ("-x",),
                     ("--man",), ("--num",),  # abbreviations of real options are refused too
                     ("--manifest=yes",), ("--manifest", "extra"), ("--manifest", "--numbrs"), ("--manifst", "--numbers"),
                     ("--manifest", "--numbers", "--typo")):
            with self.subTest(args=args):
                p = check(*args)
                self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
                self.assertNotIn("check: PASS", p.stdout + p.stderr)
                self.assertIn("usage: python3 -m pipeline.check", p.stderr)
                self.assertEqual(p.stdout, "", "a refused command prints nothing on stdout")

    def test_help_prints_the_usage_on_stdout_exits_0_and_runs_no_check(self):
        for flag in ("-h", "--help"):
            with self.subTest(flag=flag):
                p = check(flag)
                self.assertEqual((p.returncode, p.stderr), (0, ""))
                self.assertIn("usage: python3 -m pipeline.check", p.stdout)
                for option in ("--manifest", "--numbers"):
                    self.assertIn(option, p.stdout)
                self.assertNotIn("PASS", p.stdout)
                self.assertNotIn("check:", p.stdout)


class CheckOnATamperedCopy(unittest.TestCase):
    """A real tamper must still fail with exit 1 and the messages the README quotes, and a typo must not hide it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = copy_of_the_repository(Path(self.tmp.name))

    def run_check(self, *args: str, **env: str) -> subprocess.CompletedProcess:
        return check(*args, cwd=self.repo, **env)

    def test_the_untouched_copy_passes(self):
        p = self.run_check()
        self.assertEqual((p.returncode, p.stdout, p.stderr), (0, "check: PASS\n", ""))

    def test_one_changed_byte_fails_the_manifest_check_as_the_readme_says(self):
        victim = self.repo / "data" / "raw" / "llama" / "volume_maya-protocol.json"
        victim.write_bytes(victim.read_bytes() + b" ")
        for args in (("--manifest",), ()):
            with self.subTest(args=args):
                p = self.run_check(*args)
                self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
                self.assertEqual(p.stderr, "FAIL  hash mismatch: raw/llama/volume_maya-protocol.json\n")
                self.assertEqual(p.stdout, "check: 1 problem(s)\n")
        only_numbers = self.run_check("--numbers")
        self.assertEqual((only_numbers.returncode, only_numbers.stdout), (0, "check: PASS\n"),
                         "--numbers must not run the manifest check")

    def test_an_unlisted_or_missing_raw_file_fails(self):
        raw = self.repo / "data" / "raw"
        (raw / "extra.json").write_text("{}\n", encoding="utf-8")
        (raw / "llama" / "fees_maya-protocol.json").unlink()
        p = self.run_check("--manifest")
        self.assertEqual(p.returncode, 1)
        self.assertIn("FAIL  not in manifest: data/raw/extra.json", p.stderr)
        self.assertIn("FAIL  missing: raw/llama/fees_maya-protocol.json", p.stderr)
        self.assertEqual(p.stdout, "check: 2 problem(s)\n")

    def test_a_symlinked_directory_cannot_hide_unlisted_files(self):
        """Path.rglob does not enter a symlinked directory, so what sits behind one used to go unchecked."""
        elsewhere = self.repo / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "unlisted.json").write_text("{}\n", encoding="utf-8")
        try:
            os.symlink(elsewhere, self.repo / "data" / "raw" / "linked", target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"cannot create a symbolic link here: {exc}")
        p = self.run_check("--manifest")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("FAIL  symbolic link under data/raw: data/raw/linked", p.stderr)

    def test_a_changed_number_next_to_its_marker_fails_the_numbers_check(self):
        marker = re.compile(r"(?<![\w.])(\d[\d,]*\.?\d*)(<!--n:[a-z0-9_]+-->)")
        for name in ("THESIS.md", "README.md"):
            path = self.repo / name
            text = path.read_text(encoding="utf-8")
            m = marker.search(text)
            if m:
                break
        else:
            self.fail("no marked number found in THESIS.md or README.md")
        wrong = m.group(1) + "7" if "." in m.group(1) else m.group(1) + ".5"
        path.write_text(text[:m.start()] + wrong + m.group(2) + text[m.end():], encoding="utf-8")
        p = self.run_check("--numbers")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertRegex(p.stderr, rf"FAIL  {re.escape(name)}: [a-z0-9_]+ says {re.escape(wrong)}, metrics.json says ")
        self.assertRegex(p.stdout, r"^check: 1 problem\(s\)$")
        self.assertEqual(self.run_check("--manifest").returncode, 0, "--manifest must not run the numbers check")

    def append_to_thesis(self, extra: str) -> subprocess.CompletedProcess:
        """THESIS.md as committed plus one line. Every call starts again from the committed text: setUp runs once per test
        method and not once per sub-test, so appending to the copy would let each sub-case inherit the defect of the one
        before it, and from the second on it would fail whatever the code does."""
        committed = (ROOT / "THESIS.md").read_text(encoding="utf-8")
        (self.repo / "THESIS.md").write_text(committed + "\n" + extra + "\n", encoding="utf-8", newline="\n")
        return self.run_check("--numbers")

    def test_a_marker_that_does_not_follow_a_number_fails(self):
        p = self.append_to_thesis("about<!--n:h1a_ratio_as_written_x-->")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("marker(s) not directly after a number", p.stderr)
        self.assertNotIn("PASS", p.stdout)

    def test_a_mistyped_marker_is_reported_not_skipped(self):
        """Each typo alone, on the committed text, must be the only problem and be called a malformed marker."""
        for typo in ("<!--n:h1a-ratio_as_written_x-->", "<!--N:h1a_ratio_as_written_x-->", "<!-- n:h1a_ratio_as_written_x-->",
                     "<!--n :h1a_ratio_as_written_x-->", "<!--n:h1a_ratio_as_written_x -->", "<!--n:H1A_RATIO_AS_WRITTEN_X-->",
                     "<!--n:-->", "<!--n:h1a_ratio_as_written_x"):
            with self.subTest(typo=typo):
                p = self.append_to_thesis("9.99" + typo)
                self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
                self.assertEqual(p.stdout, "check: 1 problem(s)\n")
                self.assertTrue(p.stderr.startswith("FAIL  THESIS.md: 1 malformed marker(s)"), p.stderr)

    def test_a_marker_after_text_that_is_not_a_number_is_a_fail_line_not_a_traceback(self):
        for extra in ("the end.<!--n:h1a_ratio_as_written_x-->", "6.56.<!--n:h1a_ratio_as_written_x-->",
                      "2026-11-04<!--n:h1a_ratio_as_written_x-->", "6.56<!--n:h1b_verdict-->", "1<!--n:escrow_share_of_buyback_by_month-->"):
            with self.subTest(extra=extra):
                p = self.append_to_thesis(extra)
                self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
                self.assertEqual(p.stdout, "check: 1 problem(s)\n")
                self.assertNotIn("Traceback", p.stderr)
                self.assertRegex(p.stderr, r"^FAIL  THESIS\.md: [a-z0-9_]+ follows .* which cannot be compared as numbers\n$")

    def test_a_sub_case_does_not_inherit_the_defect_of_the_one_before_it(self):
        """The helper above starts from the committed text: a bad line, then the committed text alone, passes again."""
        self.assertEqual(self.append_to_thesis("about<!--n:h1a_ratio_as_written_x-->").returncode, 1)
        p = self.append_to_thesis("")
        self.assertEqual((p.returncode, p.stdout, p.stderr), (0, "check: PASS\n", ""))

    def test_a_missing_document_cannot_pass_by_being_skipped(self):
        """Each of the three documents the check requires, one at a time: a copy without one of them must not pass by skipping its
        markers. (The one document that was tested was THESIS.md, so dropping README.md or the addendum from the list went unseen.)"""
        for name in ("README.md", "THESIS.md", "PREREG-ADDENDUM.md"):
            with self.subTest(name):
                (self.repo / name).unlink()
                p = self.run_check("--numbers")
                self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
                self.assertEqual(p.stderr, f"FAIL  {name}: missing, so its markers were not checked\n")
                self.assertEqual(p.stdout, "check: 1 problem(s)\n")
                shutil.copy2(ROOT / name, self.repo / name)
        self.assertEqual(self.run_check("--numbers").returncode, 0, "and the copy passes again once the three are back")

    def test_missing_metrics_are_a_problem_and_not_a_traceback(self):
        (self.repo / "data" / "metrics.json").unlink()
        p = self.run_check("--numbers")
        self.assertEqual((p.returncode, p.stdout), (1, "check: 1 problem(s)\n"))
        self.assertEqual(p.stderr, "FAIL  data/metrics.json missing: run `make compute` first\n")
        self.assertEqual(self.run_check("--manifest").returncode, 0, "--manifest does not read the metrics")

    def test_a_long_run_of_digits_does_not_stall_the_numbers_check(self):
        import time
        started = time.monotonic()
        p = self.append_to_thesis("-" * 60_000 + " " + "1" * 60_000)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertLess(time.monotonic() - started, 20, "the marker regex must not be quadratic in a run of digits")

    def test_a_typo_or_help_does_not_turn_a_tampered_tree_into_a_pass(self):
        (self.repo / "data" / "raw" / "extra.json").write_text("{}\n", encoding="utf-8")
        self.assertEqual(self.run_check("--manifest").returncode, 1)
        for args in (("--manifst",), ("--numbers", "--manifst"), ("manifest",)):
            with self.subTest(args=args):
                p = self.run_check(*args)
                self.assertEqual(p.returncode, 2)
                self.assertNotIn("check: PASS", p.stdout + p.stderr)
        helped = self.run_check("--help")
        self.assertEqual(helped.returncode, 0)
        self.assertNotIn("check: PASS", helped.stdout + helped.stderr)

    def test_manifest_check_alone_cannot_see_a_raw_file_that_vanished_with_its_entry_but_the_recompute_can(self):
        """A known limit of --manifest: the manifest is its own source of truth. `compute` skips a block whose raw input is
        absent and still exits 0, so the guard is the comparison of its output with the committed data/metrics.json."""
        import json
        gone = "raw/rpc/rating_assumptions.json"
        manifest_path = self.repo / "data" / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        del manifest["files"][gone]
        manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        (self.repo / "data" / gone).unlink()
        self.assertEqual(self.run_check("--manifest").returncode, 0, "the limit this test documents")
        p = python(["-c", COMPARE_WITH_COMMITTED], cwd=self.repo)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("differs: metrics.json", p.stdout)


class MarkedNumbersKeepTheirSign(unittest.TestCase):
    """A marked number is compared with its sign: a hyphen-minus or U+2212 (MINUS SIGN) in front of it is part of it. Only the
    hyphen was, so a text with a typographic minus passed with the wrong sign (the digits alone were compared), and a correct
    negative number written that way failed. In-process, on a temporary tree and metrics file (check_numbers reads ROOT and METRICS)."""

    MINUS = "\u2212"

    def problems(self, text: str, metrics: dict) -> list[str]:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "docs").mkdir()
            (root / "data").mkdir()
            for name in ("README.md", "PREREG-ADDENDUM.md"):
                (root / name).write_text("", encoding="utf-8", newline="\n")
            (root / "THESIS.md").write_text(text + "\n", encoding="utf-8", newline="\n")
            (root / "data" / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8", newline="\n")
            with mock.patch.object(CHECK, "ROOT", root), mock.patch.object(CHECK, "METRICS", root / "data" / "metrics.json"):
                return CHECK.check_numbers()

    def test_the_right_sign_passes_with_either_minus(self):
        for sign in ("-", self.MINUS):
            with self.subTest(sign=ascii(sign)):
                self.assertEqual(self.problems(f"net {sign}6.56<!--n:neg--> and 6.56<!--n:pos-->", {"neg": -6.56, "pos": 6.56}), [])
                self.assertEqual(self.problems(f"{sign}1,234.5<!--n:neg-->", {"neg": -1234.5}), [])
                self.assertEqual(self.problems(f"{sign}7 <!--n:neg-->", {"neg": -7}), [])

    def test_the_wrong_sign_fails_with_either_minus(self):
        for sign in ("-", self.MINUS):
            with self.subTest(sign=ascii(sign), case="a minus before a positive metric"):
                got = self.problems(f"{sign}6.56<!--n:pos-->", {"pos": 6.56})
                self.assertEqual(len(got), 1, got)
                self.assertRegex(got[0], r"^THESIS\.md: pos says .*6\.56, metrics\.json says 6\.56$")
        with self.subTest(case="no minus before a negative metric"):
            got = self.problems("6.56<!--n:neg-->", {"neg": -6.56})
            self.assertEqual(len(got), 1, got)
            self.assertIn("neg says 6.56, metrics.json says -6.56", got[0])

    def test_two_signs_or_a_sign_after_the_number_is_reported_not_a_traceback(self):
        for text in (self.MINUS + "-6.56<!--n:neg-->", "--6.56<!--n:neg-->", "6.56" + self.MINUS + "<!--n:neg-->"):
            with self.subTest(text=ascii(text)):
                self.assertEqual(len(self.problems(text, {"neg": -6.56})), 1)

    def test_a_long_run_of_minus_signs_does_not_stall_the_marker_search(self):
        """The lookbehind keeps the search linear in a run of signs and digits; the same must hold for U+2212. A child process
        with a time limit, so that a regression fails here instead of hanging the suite."""
        child = (
            "import sys, time\n"
            "sys.path.insert(0, '.')\n"
            "from pipeline.check import LOOSE, MARK, TAG\n"
            "minus = chr(0x2212)\n"
            "cases = {'typographic minus': minus * 100_000 + ' ' + '1' * 100_000, 'hyphen': '-' * 100_000 + '1' * 100_000,\n"
            "         'mixed signs': (minus + '-') * 50_000, 'digits and commas': '1,' * 100_000, 'dots': '.' * 200_000}\n"
            "for name, text in cases.items():\n"
            "    t0 = time.monotonic()\n"
            "    MARK.findall(text); TAG.findall(text); LOOSE.findall(text)\n"
            "    print(name + ':', time.monotonic() - t0)\n")
        try:
            p = subprocess.run([sys.executable, "-I", "-c", child], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                               timeout=30, check=False)
        except subprocess.TimeoutExpired:
            self.fail("the marker search took more than 30 s on a few hundred thousand characters: it is no longer linear")
        self.assertEqual(p.returncode, 0, p.stderr)
        times = {line.rsplit(": ", 1)[0]: float(line.rsplit(": ", 1)[1]) for line in p.stdout.splitlines()}
        self.assertEqual(len(times), 5, p.stdout)
        for name, seconds in times.items():
            self.assertLess(seconds, 10.0, f"{name}: {seconds:.1f} s")


# Recompute in memory and compare, byte for byte, with the committed files (`compute` itself would overwrite them).
COMPARE_WITH_COMMITTED = r'''
import json
import sys
from pathlib import Path

from pipeline import compute

root = Path(compute.__file__).resolve().parent.parent
m, series = compute.build()
bad = []
for name, obj in (("metrics.json", m), ("series.json", series)):
    got = (json.dumps(obj, indent=1, sort_keys=True) + "\n").encode("utf-8")
    if got != (root / "data" / name).read_bytes():
        bad.append(name)
print("differs: " + ", ".join(bad) if bad else "identical")
sys.exit(1 if bad else 0)
'''


class OfflineCommandsUnderANonUtf8Locale(unittest.TestCase):
    """`check --numbers` used to crash under a locale whose default encoding is not UTF-8 (the write-up has non-ASCII
    text), and a text-mode write would turn LF into CRLF on Windows. The committed files are UTF-8 with LF, byte-hashed."""

    @classmethod
    def setUpClass(cls):
        probe = python(["-c", "import locale, sys; print(locale.getpreferredencoding(False).lower(), sys.flags.utf8_mode)"],
                       **NON_UTF8)
        cls.probe = probe.stdout.strip()
        cls.forced = probe.returncode == 0 and not cls.probe.startswith("utf-8") and cls.probe.endswith(" 0")

    def setUp(self):
        if not self.forced:
            self.skipTest(f"cannot force a non-UTF-8 locale here (the interpreter reports {self.probe!r})")

    def test_check_manifest_and_numbers_pass(self):
        for flag in ("--manifest", "--numbers"):
            with self.subTest(flag=flag):
                p = check(flag, **NON_UTF8)
                self.assertEqual((p.returncode, p.stdout, p.stderr), (0, "check: PASS\n", ""))

    def test_recomputing_reproduces_the_committed_bytes_in_either_locale(self):
        for label, env in (("default", {}), ("non-UTF-8", NON_UTF8)):
            with self.subTest(locale=label):
                p = python(["-c", COMPARE_WITH_COMMITTED], **env)
                self.assertEqual((p.returncode, p.stdout.strip()), (0, "identical"), p.stdout + p.stderr)

    def test_render_check_passes(self):
        p = python(["-m", "pipeline.render", "--check"], **NON_UTF8)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("site/ matches a fresh render", p.stdout)


class ComputeTakesNoArguments(unittest.TestCase):
    """`python3 -m pipeline.compute --help` used to ignore the argument, recompute and rewrite data/metrics.json and
    data/series.json. Run in a temporary copy: a regression here must not rewrite the repository's own files."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = copy_of_the_repository(Path(self.tmp.name))
        self.stamp = {n: (self.repo / "data" / n).stat().st_mtime_ns for n in ("metrics.json", "series.json")}

    def untouched(self) -> bool:
        return self.stamp == {n: (self.repo / "data" / n).stat().st_mtime_ns for n in ("metrics.json", "series.json")}

    def test_help_prints_the_usage_and_writes_nothing(self):
        p = python(["-m", "pipeline.compute", "--help"], cwd=self.repo)
        self.assertEqual((p.returncode, p.stderr), (0, ""))
        self.assertIn("usage: python3 -m pipeline.compute", p.stdout)
        self.assertNotIn("wrote", p.stdout)
        self.assertTrue(self.untouched())

    def test_an_argument_is_a_usage_error_and_writes_nothing(self):
        p = python(["-m", "pipeline.compute", "--no-such-option"], cwd=self.repo)
        self.assertEqual(p.returncode, 2)
        self.assertIn("usage: python3 -m pipeline.compute", p.stderr)
        self.assertNotIn("wrote", p.stdout)
        self.assertTrue(self.untouched())

    def test_without_an_argument_it_still_writes_the_same_bytes(self):
        before = {n: (self.repo / "data" / n).read_bytes() for n in ("metrics.json", "series.json")}
        p = python(["-m", "pipeline.compute"], cwd=self.repo)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(p.stdout.startswith("wrote data/metrics.json ("), p.stdout)
        self.assertEqual({n: (self.repo / "data" / n).read_bytes() for n in before}, before)


class TextIoIsExplicit(unittest.TestCase):
    """Every text file the package reads or writes says its encoding, and every text write says its line ending, so that
    the bytes do not depend on the locale or the operating system (see the pipeline.common docstring). This is a static
    check of pipeline/*.py and scripts/*.py: a call of read_text, write_text or open in text mode, or a subprocess run with
    text=True, must pass encoding= (and a write must pass newline=)."""

    # Call sites that predate this check and were left alone on purpose. The one file handles ASCII only (json.dumps escapes
    # everything else), so nothing is wrong on Linux or macOS; on Windows the writes would produce CRLF. The counts are an
    # upper bound: a new offender anywhere, or a fourth in that file, fails the test. Lower a count when its file is fixed.
    KNOWN_GAPS = {
        # compute.py: fixed (the CSV read, and the write of data/metrics.json and of data/series.json).
        "pipeline/compute.py": 0,
        # score_forward.py: the write of snapshot.json and of result.json, and the read of snapshot.json. The scorer is
        # left unedited until it has been run, and its files are ASCII JSON.
        "pipeline/score_forward.py": 3,
    }

    @staticmethod
    def offenders(path: Path) -> list[str]:
        out: list[str] = []
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            kw = {k.arg for k in node.keywords if k.arg}
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
            writes = False
            if name in ("read_text", "write_text"):
                if name == "read_text" and node.args:
                    continue                                         # not Path.read_text (render.Ctx.read_text(rel) is utf-8)
                writes = name == "write_text"
            elif name == "open":
                mode = next((a.value for a in node.args[1:2] if isinstance(a, ast.Constant)), None)
                mode = next((k.value.value for k in node.keywords if k.arg == "mode" and isinstance(k.value, ast.Constant)), mode)
                if isinstance(mode, str) and "b" in mode:
                    continue                                         # binary: no encoding, no newline translation
                writes = isinstance(mode, str) and any(c in mode for c in "wax+")
            elif name in ("run", "Popen", "check_output") and ({"text", "universal_newlines"} & kw):
                if "encoding" not in kw:
                    out.append(f"{path.name}:{node.lineno}: {name}(text=True) without encoding=")
                continue
            else:
                continue
            if "encoding" not in kw:
                out.append(f"{path.name}:{node.lineno}: {name}() without encoding=")
            elif writes and "newline" not in kw:
                out.append(f"{path.name}:{node.lineno}: {name}() writes text without newline=")
        return out

    def test_no_text_io_depends_on_the_platform_default(self):
        files = sorted((ROOT / "pipeline").glob("*.py")) + sorted((ROOT / "scripts").glob("*.py"))
        self.assertGreater(len(files), 12)
        for f in files:
            rel = f.relative_to(ROOT).as_posix()
            found = self.offenders(f)
            with self.subTest(file=rel):
                self.assertLessEqual(len(found), self.KNOWN_GAPS.get(rel, 0), "\n".join(found))

    def test_the_checker_itself_sees_the_patterns_it_is_meant_to_catch(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.py"
            bad.write_text("import subprocess\n"
                           "a = p.read_text()\n"
                           "p.write_text(x, encoding='utf-8')\n"
                           "open(p)\n"
                           "open(p, 'w', encoding='utf-8')\n"
                           "open(p, 'rb')\n"
                           "open(p, mode='wb')\n"
                           "subprocess.run(c, capture_output=True, text=True)\n"
                           "p.read_text(encoding='utf-8')\n"
                           "p.write_text(x, encoding='utf-8', newline='\\n')\n", encoding="utf-8")
            found = self.offenders(bad)
        self.assertEqual([x.split(": ", 1)[1] for x in found],
                         ["read_text() without encoding=", "write_text() writes text without newline=", "open() without encoding=",
                          "open() writes text without newline=", "run(text=True) without encoding="])


if __name__ == "__main__":
    unittest.main(verbosity=2)
