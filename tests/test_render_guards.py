"""The paths of pipeline/render.py that stop the render or refuse a value, and the parts of a scored page that
tests/test_render.py leaves to the live data. Each test here was written together with a mutant of the code that must fail it.

  * MisnamedScoreFolders           a real score in a score_* folder not named score_YYYYMMDDTHHMMSSZ stops the render, and so does a
                                   stamped one that says it is a score and holds no results
  * ObservedValuesTheAxisCannotDraw  an observed value no axis can draw stops the render with a message, not with memory
  * TheAxisWidens                  the forward-test axes widen for an observed value outside the frozen band
  * ScoredStatusIcons              the icon of each F1-F4 row of a scored card
  * HandEditedResults              a result.json a person has edited, or a shape the scorer does not write: a stop that names the file and
                                   the field and says what clears it, never a traceback
  * WhatTheScorerCanWrite          every result the real scorer writes on a snapshot with a missing day, a failed fetch or a zero volume
                                   renders (the one that cannot, a share of zero over zero, stops with the message that clears it)
  * LongReasons                    a long reason for 'not scorable' (an RPC error text) keeps every line of the page short, and its text
  * FreezeOrder                    the render stops unless the manifest puts the first BigQuery record after the freeze
  * WhatMainReports                `--out` is reported as written, the folder given with --forward-dir is the one used and is named in
                                   the hint, and the page size, fingerprint and date the README quotes are the page's

The fixtures come from tests/test_render.py (fixture_result), so they follow the layout pipeline.score_forward writes.
Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import contextlib
import copy
import html
import io
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from pipeline import render as R  # noqa: E402
from pipeline import score_forward as sf  # noqa: E402
from test_render import (Node, hl, ascii_words, card_node, check_forward_numbers, fixture_result, forward_dom, parse, realistic_result,  # noqa: E402
                         realistic_snapshot, scored_result, write_forward)

PAGE_KEY = f"{R.SITE_DIR}/{R.PAGE_NAME}"
STAMPED = "score_20261114T060000Z"      # a folder name pipeline.score_forward could have written


class MisnamedScoreFolders(unittest.TestCase):
    """A real score in a score_* folder whose name is not exactly score_YYYYMMDDTHHMMSSZ used to be ignored without a word,
    and the page went on saying "pending". The render now stops and names the folder. What is not a real score stays ignored."""

    MISNAMED = (
        "score_20261114T060000Z_rerun",      # a suffix: tells a fullmatch from a match
        "score_20261114T060000Zextra",
        "score_20261114T0600Z",              # a truncated stamp: tells \d{8}T\d{6}Z from \d+T\d+Z
        "score_20261114T060000",
        "score_final",
        "score_",
        "score_a_score_20261114T060000Z",    # a stamp inside the name: tells a fullmatch from a search
        "score_20261114T060000z",            # lower case
        "score_2026-11-14T060000Z",
        # the literal T, the digit counts and the digit class of the stamp, one name each
        "score_20261114X060000Z", "score_20261114_060000Z", "score_20261114t060000Z", "score_2026111T060000Z",
        "score_202611140T060000Z", "score_20261114T06000Z", "score_20261114T0600000Z", "score_2026111aT060000Z",
        "score_20261114T06000aZ",
    )
    # What the file says when it does not say it is a score (is_score true and mode "score"): such a file stays ignored in a folder
    # that is not named as the scorer names it, and load_forward returns None.
    NOT_A_SCORE = {
        "is_score false": {**fixture_result(), "is_score": False},
        "is_score the text true": {**fixture_result(), "is_score": "true"},
        "is_score the number 1": {**fixture_result(), "is_score": 1},
        "mode DRY-RUN with is_score true": fixture_result(is_score=True, mode="DRY-RUN"),
        "mode Score": {**fixture_result(), "mode": "Score"},
        "a dry run": fixture_result(is_score=False, mode="DRY-RUN"),
        "mode missing": {k: v for k, v in fixture_result().items() if k != "mode"},
        "is_score missing": {k: v for k, v in fixture_result().items() if k != "is_score"},
        "a JSON array": [],
        "a JSON string": "score",
    }
    # It says it is a score but is not complete. It cannot be drawn, so it stops the render in a folder named as the scorer names it
    # and in one that is not: the claim is what matters to a person who looks for the score and finds a page that says pending.
    INCOMPLETE_SCORES = {
        "no results": {"is_score": True, "mode": "score"},
        "results that is not an object": {**fixture_result(), "results": []},
    }

    def test_a_real_score_in_a_misnamed_folder_stops_the_render_and_names_the_folder(self):
        for name in self.MISNAMED:
            with self.subTest(name), tempfile.TemporaryDirectory() as d:
                tmp = Path(d)
                write_forward(tmp, name, fixture_result())
                with self.assertRaises(SystemExit) as caught:
                    R.load_forward(tmp)
                message = str(caught.exception)
                self.assertIn(f"data/forward/{name}/result.json", message)
                self.assertIn("score_YYYYMMDDTHHMMSSZ", message)
                self.assertIn("'pending'", message)
                with self.assertRaises(SystemExit):
                    R.render(forward_dir=tmp)
                with self.assertRaises(SystemExit):
                    R.Ctx(forward_dir=tmp)

    def test_the_command_exits_1_with_the_message_on_stderr_and_prints_nothing_else(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as out:
            tmp = Path(d)
            write_forward(tmp, "score_final", fixture_result())
            for args in (["--check"], []):
                with self.subTest(args=args):
                    p = subprocess.run([sys.executable, "-m", "pipeline.render", *args, "--forward-dir", str(tmp), "--out", out],
                                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
                    self.assertEqual((p.returncode, p.stdout), (1, ""))
                    self.assertTrue(p.stderr.startswith("render: data/forward/score_final/result.json is a scored result"), p.stderr)
                    self.assertEqual(list(Path(out).iterdir()), [], "a refused render writes nothing")

    def test_what_does_not_say_it_is_a_score_stays_ignored_in_a_misnamed_folder(self):
        for label, obj in self.NOT_A_SCORE.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as d:
                tmp = Path(d)
                write_forward(tmp, "score_final", obj)
                self.assertIsNone(R.load_forward(tmp))
                R.Ctx(forward_dir=tmp)

    def test_a_result_that_says_it_is_a_score_stops_the_render_in_a_misnamed_folder_even_if_it_is_incomplete(self):
        for label, obj in self.INCOMPLETE_SCORES.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as d:
                tmp = Path(d)
                write_forward(tmp, "score_final", obj)
                with self.assertRaises(SystemExit) as caught:
                    R.load_forward(tmp)
                self.assertIn("data/forward/score_final/result.json", str(caught.exception))

    def test_a_result_that_says_it_is_a_score_stops_the_render_in_a_folder_named_as_the_scorer_names_it_even_if_it_is_incomplete(self):
        """It used to be ignored there without a word: the render and `render --check` passed and the page said pending (a hand-made
        {"is_score": true, "mode": "score"} in score_20261114T060000Z, which is what a half-copied or hand-trimmed result looks like)."""
        for label, obj in self.INCOMPLETE_SCORES.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as d:
                tmp = Path(d)
                write_forward(tmp, STAMPED, obj)
                with self.assertRaises(SystemExit) as caught:
                    R.load_forward(tmp)
                message = str(caught.exception)
                self.assertTrue(message.startswith(f"render: data/forward/{STAMPED}/result.json is a scored result"), message)
                self.assertIn("holds no results object", message)
                self.assertIn("'pending'", message)
                with self.assertRaises(SystemExit):
                    R.render(forward_dir=tmp)
                with self.assertRaises(SystemExit):
                    R.Ctx(forward_dir=tmp)
                for args in (["--check"], []):                          # the reviewer's commands: rc 0 and "matches a fresh render" before the fix
                    with tempfile.TemporaryDirectory() as out:
                        p = subprocess.run([sys.executable, "-m", "pipeline.render", *args, "--forward-dir", str(tmp), "--out", out],
                                           cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
                        self.assertEqual((p.returncode, p.stdout), (1, ""), (args, p.stderr))
                        self.assertTrue(p.stderr.startswith(f"render: data/forward/{STAMPED}/result.json is a scored result"), p.stderr)
                        self.assertEqual(list(Path(out).iterdir()), [], "a refused render writes nothing")

    def test_only_the_newest_stamped_result_is_looked_at_and_an_incomplete_one_does_not_fall_back_to_an_older_score(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            write_forward(tmp, "score_20261114T050000Z", fixture_result())
            self.assertEqual(R.load_forward(tmp)["_path"], "data/forward/score_20261114T050000Z/result.json")
            write_forward(tmp, STAMPED, {"is_score": True, "mode": "score"})
            with self.assertRaises(SystemExit) as caught:
                R.load_forward(tmp)
            self.assertIn(STAMPED, str(caught.exception))
        with tempfile.TemporaryDirectory() as d:                         # while an older incomplete one under a newer complete one is not read
            tmp = Path(d)
            write_forward(tmp, "score_20261114T050000Z", {"is_score": True, "mode": "score"})
            write_forward(tmp, STAMPED, fixture_result())
            self.assertEqual(R.load_forward(tmp)["_path"], f"data/forward/{STAMPED}/result.json")

    def test_a_misnamed_folder_with_a_file_that_cannot_be_read_stays_ignored(self):
        real = json.dumps(fixture_result()).encode("utf-8")
        for label, raw in (("not JSON", b"{not json"), ("empty", b""), ("a byte-order mark", b"\xef\xbb\xbf" + real),
                           ("not UTF-8", b'{"a": "\xff\xfe"}'), ("truncated", real[:40])):
            with self.subTest(label), tempfile.TemporaryDirectory() as d:
                tmp = Path(d)
                (tmp / "score_rehearsal").mkdir()
                (tmp / "score_rehearsal" / "result.json").write_bytes(raw)
                self.assertIsNone(R.load_forward(tmp))

    def test_a_deeply_nested_file_is_not_a_traceback(self):
        """json.loads raises RecursionError, not ValueError, on a result nested far deeper than the parser allows: a misnamed
        folder with such a file stays ignored (as before), and the newest stamped one stops the render with a message."""
        deep = "[" * 200000
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "score_rehearsal").mkdir()
            (tmp / "score_rehearsal" / "result.json").write_text(deep, encoding="utf-8")
            self.assertIsNone(R.load_forward(tmp))
            (tmp / STAMPED).mkdir()
            (tmp / STAMPED / "result.json").write_text(deep, encoding="utf-8")
            with self.assertRaises(SystemExit) as caught:
                R.load_forward(tmp)
            self.assertIn(STAMPED, str(caught.exception))
            self.assertIn("RecursionError", str(caught.exception))

    def test_folders_that_are_not_score_folders_are_not_looked_at(self):
        for name in ("dry-run_20261108T000000Z", "dry-run_x", "rescore_final", "final_score", "Score_final", "scores_final"):
            with self.subTest(name), tempfile.TemporaryDirectory() as d:
                tmp = Path(d)
                write_forward(tmp, name, fixture_result())
                self.assertIsNone(R.load_forward(tmp))

    def test_a_directory_or_a_deeper_file_is_not_a_result(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "score_final" / "result.json").mkdir(parents=True)               # a directory named result.json
            (tmp / STAMPED / "result.json").mkdir(parents=True)                     # the same under a name the scorer writes
            write_forward(tmp, "score_deeper", fixture_result(), "elsewhere.json")  # a real score in another file name
            (tmp / "score_deepest" / "sub").mkdir(parents=True)
            (tmp / "score_deepest" / "sub" / "result.json").write_text(json.dumps(fixture_result()), encoding="utf-8")
            self.assertIsNone(R.load_forward(tmp))

    def test_a_real_score_in_a_folder_the_scorer_would_have_named_is_still_drawn(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as empty:
            tmp = Path(d)
            write_forward(tmp, STAMPED, fixture_result())
            got = R.load_forward(tmp)
            self.assertEqual(got["_path"], f"data/forward/{STAMPED}/result.json")
            scored, pending = R.render(forward_dir=tmp)[PAGE_KEY], R.render(forward_dir=Path(empty))[PAGE_KEY]
            self.assertNotEqual(scored, pending)
            self.assertIn(b'data-f="F3.take_rate_bp"', scored)
            self.assertNotIn(b'data-f="F3.take_rate_bp"', pending)

    def test_a_stamped_score_beside_a_misnamed_one_still_stops_and_beside_a_misnamed_non_score_is_drawn(self):
        """The non-score folder is named like the stamped one plus a suffix, so it sorts after it: if it counted as a stamped
        folder it would be the newest, and the older real score would be hidden."""
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            write_forward(tmp, STAMPED, fixture_result())
            write_forward(tmp, STAMPED + "_notes", fixture_result(is_score=False, mode="DRY-RUN"))
            self.assertEqual(R.load_forward(tmp)["_path"], f"data/forward/{STAMPED}/result.json")
            write_forward(tmp, "score_copy_of_the_final", fixture_result())
            with self.assertRaises(SystemExit) as caught:
                R.load_forward(tmp)
            self.assertIn("score_copy_of_the_final", str(caught.exception))
            self.assertNotIn("_notes", str(caught.exception))

    def test_every_misnamed_real_score_is_named(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            for name in ("score_b", "score_a"):
                write_forward(tmp, name, fixture_result())
            with self.assertRaises(SystemExit) as caught:
                R.load_forward(tmp)
            message = str(caught.exception)
            self.assertIn("data/forward/score_a/result.json, data/forward/score_b/result.json are scored results", message)

    def test_the_stamp_is_ascii_digits_only(self):
        arabic = "".join(chr(0x660 + int(c)) for c in "20261114") + "T" + "".join(chr(0x660 + int(c)) for c in "060000")
        name = f"score_{arabic}Z"
        self.assertRegex(name, r"score_\d{8}T\d{6}Z")        # a Unicode-aware \d would take this name for a stamp
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            try:
                write_forward(tmp, name, fixture_result())
            except (OSError, UnicodeError) as exc:
                self.skipTest(f"this file system cannot hold the folder name: {exc}")
            with self.assertRaises(SystemExit) as caught:
                R.load_forward(tmp)
            self.assertIn("score_YYYYMMDDTHHMMSSZ", str(caught.exception))

    def test_a_newest_result_the_process_may_not_read_stops_the_render(self):
        """An OSError (a permission, an I/O error) is treated like bad JSON: the page must not say pending over a file it could
        not open. chmod 000 does not stop root, so the read is made to fail instead, which is what the mode would do."""
        real = Path.read_text

        def deny(self_: Path, *a, **k):
            if self_.name == "result.json":
                raise PermissionError(13, "Permission denied", str(self_))
            return real(self_, *a, **k)

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            write_forward(tmp, "score_20261114T010000Z", fixture_result())
            write_forward(tmp, "score_20261114T020000Z", fixture_result())
            with mock.patch.object(Path, "read_text", deny):
                with self.assertRaises(SystemExit) as caught:
                    R.load_forward(tmp)
            self.assertIn("score_20261114T020000Z", str(caught.exception))
            self.assertIn("PermissionError", str(caught.exception))
            self.assertIn("'pending'", str(caught.exception))

    def test_an_unreadable_file_in_a_misnamed_folder_does_not_stop_a_stamped_score_from_being_drawn(self):
        real = Path.read_text

        def deny(self_: Path, *a, **k):
            if self_.parent.name == "score_rehearsal":
                raise PermissionError(13, "Permission denied", str(self_))
            return real(self_, *a, **k)

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            write_forward(tmp, STAMPED, fixture_result())
            write_forward(tmp, "score_rehearsal", fixture_result())
            with mock.patch.object(Path, "read_text", deny):
                self.assertEqual(R.load_forward(tmp)["_path"], f"data/forward/{STAMPED}/result.json")


CHILD = r'''
import json, sys, tempfile
from pathlib import Path
try:
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (2 << 30, 2 << 30))   # a render that runs away ends in MemoryError, not in the machine's memory
except (ImportError, ValueError, OSError):
    pass
root, tests = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)
sys.path.insert(0, tests)
from pipeline import render as R
from test_render import fixture_result, write_forward
for fid, key, value in json.loads(sys.stdin.read()):
    res = fixture_result()
    res["results"][fid] = {**res["results"][fid], "result": "MISS", key: value}   # the numbers of a test that is not scorable are not read
    with tempfile.TemporaryDirectory() as d:
        write_forward(Path(d), "score_20261114T060000Z", res)
        try:
            page = R.render(forward_dir=Path(d))[R.SITE_DIR + "/" + R.PAGE_NAME]
            out = {"outcome": "rendered", "bytes": len(page)}
        except SystemExit as exc:
            out = {"outcome": "stop", "message": str(exc)}
        except BaseException as exc:      # MemoryError, OverflowError, ...
            out = {"outcome": "crash", "type": type(exc).__name__, "message": str(exc)[:200]}
    print(json.dumps(out), flush=True)
'''


def render_in_a_child(cases: list[tuple[str, str, object]]) -> list[dict]:
    """Render the scored fixture once per (test, field, value), each in a child process that has an address-space limit and a time
    limit, and return what happened. A corrupt value used to make a page of 150 MB or exhaust memory: this keeps a regression of
    the guard from doing that to the machine that runs the tests."""
    try:
        p = subprocess.run([sys.executable, "-I", "-c", CHILD, str(ROOT), str(HERE)], input=json.dumps(cases), capture_output=True,
                           text=True, encoding="utf-8", timeout=120, check=False)
    except subprocess.TimeoutExpired:
        raise AssertionError("rendering a corrupt value took more than 120 s") from None
    if p.returncode != 0:
        raise AssertionError(f"the child process failed ({p.returncode}): {p.stderr[-500:]}")
    return [json.loads(line) for line in p.stdout.splitlines()]


class ObservedValuesTheAxisCannotDraw(unittest.TestCase):
    """The first guard rejected NaN and infinity only. A finite but absurd observed value passed it, and the axis then drew one tick
    per step: 1e6 basis points made a page of 150 MB, 1e300 ran out of memory, and an integer beyond the range of a float (a JSON
    number may have any number of digits) raised OverflowError from math.isfinite. Now each of them stops the render with a message."""

    ABSURD = (
        ("F1", "balance_near", 1e12), ("F1", "balance_near", 1e300), ("F1", "balance_near", 1 << 2000),
        ("F2", "mean_near_per_day", 1e9), ("F2", "mean_near_per_day", -1e9), ("F2", "mean_near_per_day", 1e300),
        ("F2", "mean_near_per_day", -(1 << 2000)),
        ("F3", "take_rate_bp", 1e6), ("F3", "take_rate_bp", 1e9), ("F3", "take_rate_bp", -1e6), ("F3", "take_rate_bp", 1e300),
        ("F3", "take_rate_bp", 1.7e308), ("F3", "take_rate_bp", 10 ** 400),
        ("F4", "intents_share_pct", 1e6), ("F4", "intents_share_pct", -1e6), ("F4", "intents_share_pct", 1e300),
        ("F4", "intents_share_pct", 1 << 2000))

    def test_an_absurd_observed_value_stops_the_render_with_a_message_about_that_value(self):
        outcomes = render_in_a_child([list(c) for c in self.ABSURD])
        self.assertEqual(len(outcomes), len(self.ABSURD))
        for (fid, key, value), out in zip(self.ABSURD, outcomes):
            with self.subTest(f"{fid}.{key} = {str(value)[:12]}"):
                self.assertEqual(out["outcome"], "stop", out)
                message = out["message"]
                self.assertTrue(message.startswith(f"render: {fid}.{key}"), message)
                self.assertLess(len(message), 700, "the message must not print the number when it has hundreds of digits")
                if isinstance(value, int) and abs(value) > 1 << 1100:
                    self.assertIn("an integer too large for a float", message)
                else:
                    self.assertIn(f"the page draws at most {R.MAX_AXIS_TICKS}", message)
                self.assertIn("not scorable", message, "it says what to do")

    def render(self, fid: str, key: str, value: float, result: str = "MISS") -> str:
        res = fixture_result()
        res["results"][fid] = {**res["results"][fid], "result": result, key: value}
        with tempfile.TemporaryDirectory() as d:
            write_forward(Path(d), STAMPED, res)
            return R.render(forward_dir=Path(d))[PAGE_KEY].decode("utf-8")

    def test_the_longest_axis_is_drawn_and_one_tick_more_is_not(self):
        """The tick count is bounded by R.MAX_AXIS_TICKS, inclusive. F3 and F4 start at zero on a step that divides the limit, so the
        value that needs exactly that many ticks is known: step * (MAX - 2) puts the last tick at step * (MAX - 1)."""
        most = R.MAX_AXIS_TICKS
        for fid, key, step in (("F3", "take_rate_bp", 2), ("F4", "intents_share_pct", 25)):
            with self.subTest(fid):
                self.render(fid, key, float(step * (most - 2)))
                with self.assertRaises(SystemExit) as caught:
                    self.render(fid, key, float(step * (most - 2) + 1))
                self.assertIn(f"{most + 1} ticks", str(caught.exception))

    def test_every_value_the_scorer_can_really_produce_still_renders(self):
        """Far from the band, but real: a balance of tens of millions of NEAR, a net supply that falls by half a million a day, a take
        rate of a hundred basis points. None of them may be mistaken for corrupt data."""
        for fid, key, value in (("F1", "balance_near", 0.0), ("F1", "balance_near", 5e6), ("F1", "balance_near", 3e7),
                                ("F2", "mean_near_per_day", 0.0), ("F2", "mean_near_per_day", -5e5), ("F2", "mean_near_per_day", 8e5),
                                ("F3", "take_rate_bp", 0.0), ("F3", "take_rate_bp", 100.0), ("F3", "take_rate_bp", 395.0),
                                ("F4", "intents_share_pct", 0.0), ("F4", "intents_share_pct", 100.0)):
            with self.subTest(f"{fid}.{key} = {value:g}"):
                self.assertIn(f'data-f="{fid}.{key}"', self.render(fid, key, value))

    def test_the_committed_axes_draw_few_ticks(self):
        """The bound is far above what the card draws today (four or five ticks an axis), so it is not what shapes the page."""
        self.assertGreaterEqual(R.MAX_AXIS_TICKS, 100)
        with tempfile.TemporaryDirectory() as empty:
            dom, _ = forward_dom(Path(empty))
        for g in card_node(dom, "forward").find_all("g", "nl"):
            self.assertLessEqual(len(g.find_all("text", "tk")), 15, g.attrs["data-id"])


WIDENED = (
    # (test, field, observed value, axis lo, axis hi, ticks, first label, last label)
    ("F1", "balance_near", 3_000_000.0, 2.0, 3.2, 7, "2.0", "3.2"),
    ("F1", "balance_near", 1_000_000.0, 0.8, 2.6, 10, "0.8", "2.6"),
    ("F2", "mean_near_per_day", 100_500.0, 82.0, 110.0, 8, "82", "110"),
    ("F2", "mean_near_per_day", 60_000.0, 56.0, 96.0, 11, "56", "96"),
    ("F3", "take_rate_bp", 12.34, 0.0, 16.0, 9, "0", "16"),
    ("F3", "take_rate_bp", -3.0, -6.0, 8.0, 8, "-6", "8"),
    ("F4", "intents_share_pct", 130.0, 0.0, 175.0, 8, "0%", "175%"),
    ("F4", "intents_share_pct", -10.0, -50.0, 100.0, 7, "-50%", "100%"),
)


class TheAxisWidens(unittest.TestCase):
    """The number line of each forward test starts from the frozen band and is widened, in steps, to hold an observed value. The
    fixtures of tests/test_render.py all fall inside the default axes, so nothing there showed whether the widening happens."""

    def lines(self, fid: str, key: str, value: float):
        res = fixture_result()
        res["results"][fid] = {**res["results"][fid], "result": "MISS", key: value}
        with tempfile.TemporaryDirectory() as d:
            write_forward(Path(d), STAMPED, res)
            dom, _ = forward_dom(Path(d))
        found = [g for sv in card_node(dom, "forward").find_all("svg", "svg") for g in sv.find_all("g", "nl") if g.attrs["data-id"] == fid]
        self.assertEqual(len(found), 2, "a wide and a phone drawing")
        return found

    def test_an_observed_value_outside_the_default_axis_widens_it(self):
        for fid, key, value, lo, hi, ticks, first, last in WIDENED:
            with self.subTest(f"{fid} = {value:g}"):
                for g in self.lines(fid, key, value):
                    self.assertEqual((float(g.attrs["data-lo"]), float(g.attrs["data-hi"])), (lo, hi))
                    labels = [t.text().strip() for t in g.find_all("text", "tk")]
                    self.assertEqual((len(labels), labels[0], labels[-1]), (ticks, first, last))
                    x0, pw = float(g.attrs["data-x0"]), float(g.attrs["data-pw"])
                    dot = g.find("circle", "sk")
                    self.assertAlmostEqual(float(dot.attrs["cx"]), x0 + pw * (value / (1e6 if fid == "F1" else 1e3 if fid == "F2" else 1)
                                                                              - lo) / (hi - lo), delta=0.2)
                    self.assertTrue(x0 <= float(dot.attrs["cx"]) <= x0 + pw, "the dot is on the axis")

    def test_a_value_inside_the_default_axis_does_not_move_it(self):
        for fid, key, value, lo, hi in (("F1", "balance_near", 2_300_000.0, 2.0, 2.6), ("F3", "take_rate_bp", 3.0, 0.0, 8.0),
                                        ("F4", "intents_share_pct", 40.0, 0.0, 100.0)):
            with self.subTest(fid):
                for g in self.lines(fid, key, value):
                    self.assertEqual((float(g.attrs["data-lo"]), float(g.attrs["data-hi"])), (lo, hi))


class ScoredStatusIcons(unittest.TestCase):
    """A scored row carries a shape as well as a word (never colour alone). The fixture has a pass, a miss and a test that is not
    scorable; the pending card has the clock. This is the card that is published on the day the tests are scored."""

    PATHS = {"pending": "M10 5.4V10l3.2 2", "na": "M4.6 15.4l10.8-10.8"}

    @staticmethod
    def rows(dom) -> dict[str, object]:
        return {n.attrs["data-k"]: n for n in card_node(dom, "forward").find_all("li") if n.attrs.get("data-k") in ("F1", "F2", "F3", "F4")}

    @staticmethod
    def shape(li) -> tuple[set[str], list[str]]:
        svg = li.find("svg", "ico")
        return ({c for el in svg.iter() for c in el.classes()} - {"ico"},
                [el.attrs["d"] for el in svg.iter() if el.tag == "path" and "d" in el.attrs])

    def test_each_row_of_a_scored_card_has_the_icon_of_its_word(self):
        with tempfile.TemporaryDirectory() as d:
            write_forward(Path(d), STAMPED, fixture_result())
            dom, _ = forward_dom(Path(d))
        rows = self.rows(dom)
        self.assertEqual(sorted(rows), ["F1", "F2", "F3", "F4"])
        words = {fid: li.find("span", "fword").text().strip() for fid, li in rows.items()}
        self.assertEqual(words, {"F1": "PASS", "F2": "MISS", "F3": "PASS", "F4": "not scorable"})
        for fid, good in (("F1", True), ("F2", False), ("F3", True)):
            classes, _ = self.shape(rows[fid])
            self.assertIn("i-ok" if good else "i-bad", classes, fid)
            self.assertNotIn("i-bad" if good else "i-ok", classes, fid)
        classes, paths = self.shape(rows["F4"])
        self.assertTrue(classes.isdisjoint({"i-ok", "i-bad"}))
        self.assertIn(self.PATHS["na"], paths, "not scorable is the struck-through circle, neither a tick nor a cross")

    def test_a_pending_row_has_the_clock(self):
        with tempfile.TemporaryDirectory() as empty:
            dom, _ = forward_dom(Path(empty))
        for fid, li in self.rows(dom).items():
            classes, paths = self.shape(li)
            self.assertEqual((classes, paths), ({"i-line"}, [self.PATHS["pending"]]), fid)

    def test_status_kind_maps_every_word_the_page_uses(self):
        for word, kind in (("PASS", "pass"), ("pass", "pass"), ("Buy", "pass"), ("MISS", "fail"), ("miss", "fail"), ("fail", "fail"),
                           ("Avoid", "fail"), ("inconclusive", "inconclusive"), ("Hold", "hold"), ("not scorable", "na"),
                           ("scored", "scored"), ("pending", "pending"), ("", "pending"), ("something else", "pending")):
            with self.subTest(word):
                self.assertEqual(R.status_kind(word), kind)


REALISTIC = realistic_result()      # what the real scorer writes on the committed snapshots: all four tests have numbers


def base() -> dict:
    """A scored result with a number under every test (a copy: the tests change it)."""
    return copy.deepcopy(REALISTIC)


def context(res: dict) -> R.Ctx:
    """The context a render builds from this result. The folder is read when it is built, so it can go at once."""
    with tempfile.TemporaryDirectory() as d:
        write_forward(Path(d), STAMPED, res)
        return R.Ctx(forward_dir=Path(d))


def parsed(markup: str) -> Node:
    dom, errors = parse(markup)
    assert not errors, errors
    return dom


class HandEditedResults(unittest.TestCase):
    """A result.json that a person has edited, or a shape the scorer does not write. The stop over an unusable number said to 'record that
    test as not scorable by hand', and doing exactly that still stopped the render, because the number was read whatever the word said. Other
    shapes did not stop it with a message at all: a test written as a string or null raised AttributeError in the scorecard, a PASS or MISS
    without a number the card prints raised KeyError, and a number written as text raised TypeError. Each now stops the render with a
    message that names the file and the field, and the stop that is about a number is cleared by what its message says."""

    @staticmethod
    def page(res: dict) -> Node:
        """The forward card the render draws for this result, parsed (the rest of the page does not depend on it)."""
        return parsed(R.card_forward(context(res)))

    def stop(self, res: dict, at_load: bool = True) -> str:
        """The message of the stop. The render stops with it; so do the loader and the context, unless the value is finite and only the axis
        cannot draw it (at_load False): that stop comes when the card is built."""
        with tempfile.TemporaryDirectory() as d:
            write_forward(Path(d), STAMPED, res)
            with self.assertRaises(SystemExit) as caught:
                R.render(forward_dir=Path(d))
            if at_load:
                with self.assertRaises(SystemExit) as at:
                    R.load_forward(Path(d))
                with self.assertRaises(SystemExit):
                    R.Ctx(forward_dir=Path(d))
                self.assertEqual(str(at.exception), str(caught.exception))
        return str(caught.exception)

    @staticmethod
    def changed(fid: str, entry: object) -> dict:
        res = base()
        res["results"][fid] = entry
        return res

    # ---- a stop over a number is cleared by recording the test as not scorable
    NUMBERS = (   # (test, key, value, whether the loader stops over it: a finite value is stopped by the axis, when the card is built)
        ("F4", "intents_share_pct", float("nan"), True), ("F4", "intents_share_pct", float("inf"), True), ("F4", "intents_share_pct", float("-inf"), True),
        ("F1", "balance_near", 1 << 2000, True),                      # an integer beyond the range of a float
        ("F3", "take_rate_bp", 1e12, False), ("F2", "mean_near_per_day", 1e300, False), ("F1", "balance_near", 1e12, False),
        ("F4", "intents_share_pct", "45.9", True), ("F1", "balance_near", None, True), ("F3", "take_rate_bp", True, True),
        ("F2", "mean_near_per_day", [1.0], True), ("F1", "block_height", float("nan"), True), ("F2", "n_deltas", "8", True),
        ("F3", "revenue_usd", float("inf"), True), ("F3", "volume_usd", {"a": 1}, True),
    )

    def test_recording_the_test_as_not_scorable_clears_a_stop_over_its_numbers_and_the_message_says_so(self):
        for fid, key, value, at_load in self.NUMBERS:
            with self.subTest(f"{fid}.{key} = {str(value)[:14]}"):
                res = base()
                res["results"][fid][key] = value
                message = self.stop(res, at_load)
                self.assertTrue(message.startswith(f"render: {fid}.{key}"), message)
                self.assertIn(f"data/forward/{STAMPED}/result.json", message, "the file")
                self.assertIn("set the result of that test to 'not scorable' and give a why (the numbers of a test that is not scorable are not read)",
                              message, "what clears it")
                self.assertLess(len(message), 700)
                # what the message says: change the word and give a reason. The numbers stay in the file and are not read.
                res["results"][fid].update(result="not scorable", why="recorded by hand")
                card = card_node(self.page(res), "forward")
                row = next(li for li in card.find_all("li") if li.attrs.get("data-k") == fid)
                self.assertEqual(row.find("span", "fword").text().strip(), "not scorable")
                self.assertIn("Not scorable: recorded by hand. It is never estimated.", re.sub(r"\s+", " ", row.text()))
                self.assertEqual(len(card.find_all("circle", "sk")), 2 * 3, "a dot for each of the other three tests, in two drawings")

    def test_the_numbers_of_a_test_that_is_not_scorable_draw_nothing_and_widen_nothing(self):
        """The scorer's own output for a zero total (F4 a MISS with a share of NaN) after the hand edit its message asked for, and an F1
        that carries junk beside its reason."""
        res = base()
        res["results"]["F4"].update(result="not scorable", why="zero total volume")
        res["results"]["F1"] = {"result": "not scorable", "why": "no RPC read", "balance_near": 9e99, "block_height": "x"}
        res["results"]["F4"]["intents_share_pct"] = float("nan")
        card = card_node(self.page(res), "forward")
        self.assertEqual([li.find("span", "fword").text().strip() for li in card.find_all("li") if li.attrs.get("data-k")],
                         ["not scorable", "PASS", "MISS", "not scorable"])
        for svg in card.find_all("svg", "svg"):
            by_id = {g.attrs["data-id"]: g for g in svg.find_all("g", "nl")}
            self.assertEqual((by_id["F1"].find("circle", "sk"), by_id["F4"].find("circle", "sk")), (None, None))
            self.assertEqual((float(by_id["F1"].attrs["data-hi"]), float(by_id["F4"].attrs["data-hi"])), (2.6, 100.0), "the default axes")
        self.assertEqual([n.text() for n in card.iter() if n.attrs.get("data-f", "").startswith("F4.") and not n.attrs["data-f"].endswith(".why")], [])

    # ---- shapes that raised a traceback
    def test_a_test_that_is_not_an_object_stops_the_render_naming_the_file_and_the_test(self):
        for label, value in (("a string", "not scorable"), ("null", None), ("a list", []), ("a number", 5), ("true", True), ("a float", 1.5)):
            with self.subTest(label):
                message = self.stop(self.changed("F4", value))
                self.assertTrue(message.startswith(f"render: F4 in data/forward/{STAMPED}/result.json is "), message)
                self.assertIn("not an object", message)
                self.assertIn('"result": "not scorable"', message, "it shows what to write")

    def test_each_of_the_four_tests_is_looked_at(self):
        for fid in R.FORWARD_IDS:
            with self.subTest(fid):
                self.assertTrue(self.stop(self.changed(fid, None)).startswith(f"render: {fid} in "))

    def test_a_pass_or_miss_without_a_number_the_card_prints_stops_the_render(self):
        keys = [(fid, key) for fid, names in R.FORWARD_NUMBERS.items() for key in names]
        self.assertEqual(len(keys), 8, "eight numbers are printed in the list")
        for fid, key in keys:
            with self.subTest(f"{fid}.{key}"):
                res = base()
                del res["results"][fid][key]
                message = self.stop(res)
                self.assertTrue(message.startswith(f"render: {fid}.{key} is missing from data/forward/{STAMPED}/result.json"), message)
                self.assertIn(f"but {fid} is {res['results'][fid]['result']} and the card prints it", message)
                self.assertIn("set the result of that test to 'not scorable' and give a why", message)

    def test_a_number_that_is_not_a_number_stops_the_render_and_the_message_says_what_it_is(self):
        for fid, names in R.FORWARD_NUMBERS.items():
            for key in names:
                for label, value, said in (("text", "12.5", "the text '12.5'"), ("null", None, "null"), ("true", True, "true"), ("false", False, "false"),
                                           ("a list", [1], "a list"), ("an object", {"a": 1}, "an object")):
                    with self.subTest(f"{fid}.{key} as {label}"), tempfile.TemporaryDirectory() as d:
                        res = base()
                        res["results"][fid][key] = value
                        write_forward(Path(d), STAMPED, res)
                        with self.assertRaises(SystemExit) as caught:
                            R.load_forward(Path(d))
                        self.assertIn(f"render: {fid}.{key} in data/forward/{STAMPED}/result.json is {said}, not a number", str(caught.exception))

    def test_a_long_text_in_a_message_is_cut(self):
        res = base()
        res["results"]["F4"]["intents_share_pct"] = "9" * 500
        message = self.stop(res)
        self.assertIn("(cut)", message)
        self.assertLess(len(message), 700)

    def test_a_reason_that_is_not_text_stops_the_render_but_only_where_it_is_printed(self):
        for label, value in (("null", None), ("a number", 5), ("a list", ["x"]), ("an object", {"a": 1}), ("true", True)):
            with self.subTest(label):
                message = self.stop(self.changed("F4", {"result": "not scorable", "why": value}))
                self.assertTrue(message.startswith(f"render: F4.why in data/forward/{STAMPED}/result.json is "), message)
                self.assertIn("not text", message)
        res = base()
        res["results"]["F3"]["why"] = 5          # a PASS or MISS does not print a reason, so one it carries is not read
        self.assertIsNotNone(card_node(self.page(res), "forward"))

    def test_a_test_the_file_does_not_record_is_drawn_as_not_scorable_with_no_reason_recorded(self):
        """As it always was, and as tests/test_score_forward.py pins (its fixture records F1 only). The scorer writes all four."""
        res = base()
        del res["results"]["F2"]
        del res["results"]["F3"]
        card = card_node(self.page(res), "forward")
        rows = {li.attrs["data-k"]: re.sub(r"\s+", " ", li.find("p", "tnote").text()).strip() for li in card.find_all("li") if li.attrs.get("data-k")}
        self.assertEqual(rows["F2"], "Not scorable: no reason recorded. It is never estimated.")
        self.assertEqual(rows["F3"], "Not scorable: no reason recorded. It is never estimated.")
        self.assertEqual(re.sub(r"\s+", " ", hl(card).text()), "Forward tests scored: 0 passed, 2 missed and 2 not scorable of 4.")

    def test_a_value_is_named_in_a_message_as_what_it_is(self):
        kind = R.json_kind
        self.assertEqual([kind(None), kind(True), kind(False), kind([1]), kind({}), kind(5), kind(2.5), kind(float("nan"))],
                         ["null", "true", "false", "a list", "an object", "5", "2.5", "nan"])
        self.assertEqual(kind("x" * 30), "the text " + repr("x" * 30), "thirty characters are shown whole")
        self.assertEqual(kind("x" * 31), "the text " + repr("x" * 30) + " (cut)")
        self.assertEqual(kind(10 ** 30 - 1), str(10 ** 30 - 1))
        self.assertEqual(kind(10 ** 30), "an integer too large to print")

    def test_the_word_the_page_prints_for_a_test_comes_from_one_place(self):
        fw = {"results": {"F1": {"result": "PASS"}, "F2": {"result": "MISS"}, "F3": {"result": "not scorable"}, "F4": "anything", "F5": {"result": "PASS"}}}
        self.assertEqual([R.forward_word(fw, f) for f in R.FORWARD_IDS], ["PASS", "MISS", "not scorable", "not scorable"])
        self.assertEqual(R.forward_word({"results": {}}, "F2"), "not scorable", "a test the file does not record")
        self.assertEqual(R.forward_word({"results": {"F1": {}}}, "F1"), "not scorable", "a test with no word")
        self.assertEqual([R.forward_word(None, f) for f in R.FORWARD_IDS], ["pending"] * 4)

    def test_the_scorecard_counts_with_the_word_of_the_card_even_for_a_context_the_loader_did_not_build(self):
        """The scorecard read the word on its own and raised AttributeError for a test that is not an object. The loader stops those now; the
        scorecard no longer depends on that."""
        ctx = R.Ctx()
        ctx.forward = {"results": {"F1": {"result": "PASS"}, "F2": "x", "F3": None, "F4": {"result": "MISS"}}, "_path": "p"}
        tile = [n for n in parsed(R.scorecard(ctx)).find_all("li") if "tile" in n.classes()][4]
        self.assertIn("1 pass, 1 miss", tile.text())
        self.assertIn("2 not scorable", tile.text())

    def test_keys_and_tests_the_card_does_not_know_are_ignored(self):
        res = base()
        res["results"]["F5"] = "anything"
        res["results"]["F1"]["something_new"] = {"a": [1, 2]}
        self.assertEqual(len([li for li in card_node(self.page(res), "forward").find_all("li") if li.attrs.get("data-k")]), 4)


# ---- what the real scorer can write
RPC_ERROR = ("RuntimeError: rpc block {'finality': 'final'}: {'name': 'HANDLER_ERROR', 'cause': {'info': {}, 'name': 'UNKNOWN_BLOCK'}, "
             "'code': -32000, 'message': 'Server error', 'data': 'DB Not Found Error: BLOCK HEIGHT: 223230811'}")
LONG_RPC_ERROR = " ".join([RPC_ERROR] * 12)[:2395]     # the reviewer's reproduction: an RPC error text of 2,395 characters
NS = "not scorable"


def without(snap: dict, source: str, error: str) -> dict:
    """A fetch that failed: no source, and the error text that fetch_all keeps for it."""
    del snap["sources"][source]
    snap["errors"][source] = error
    return snap


def drop_day(snap: dict, source: str, day: str) -> dict:
    """One UTC day taken out of a DefiLlama series."""
    data = snap["sources"][source]["data"]
    data["totalDataChart"] = [row for row in data["totalDataChart"] if sf.day_of(row[0]) != day]
    return snap


def drop_supply_day(snap: dict, day: str) -> dict:
    data = snap["sources"]["nearblocks_charts"]["data"]
    data["charts"] = [row for row in data["charts"] if row["date"][:10] != day]
    return snap


def zero_volumes(snap: dict, peers: tuple[str, ...] | list[str] = tuple(sf.PEERS)) -> dict:
    for peer in peers:
        data = snap["sources"][f"llama_volume_{peer}"]["data"]
        data["totalDataChart"] = [[t, 0] for t, _ in data["totalDataChart"]]
    return snap


def scorer_inputs() -> list[tuple[str, dict, tuple[str, str, str, str]]]:
    """(what is wrong with the snapshot, the result.json that the real score() and main() write for it, the word it gives F1 to F4)."""
    out = []

    def add(label: str, res: dict, words: tuple[str, str, str, str]) -> None:
        out.append((label, res, words))

    fresh = realistic_snapshot
    add("the committed snapshots", scored_result(fresh()), ("MISS", "PASS", "MISS", "MISS"))
    add("F1: the RPC read failed", scored_result(without(fresh(), "rpc_f1", RPC_ERROR)), (NS, "PASS", "MISS", "MISS"))
    add("F1: the RPC read failed with an error of 2,395 characters", scored_result(without(fresh(), "rpc_f1", LONG_RPC_ERROR)), (NS, "PASS", "MISS", "MISS"))
    add("F1: no error was kept for the failed read", scored_result({**without(fresh(), "rpc_f1", "x"), "errors": {}}), (NS, "PASS", "MISS", "MISS"))
    add("F2: Nearblocks failed", scored_result(without(fresh(), "nearblocks_charts", "URLError: <urlopen error timed out>")), ("MISS", NS, "MISS", "MISS"))
    add("F2: a day of total_supply is missing", scored_result(drop_supply_day(fresh(), "2026-11-01")), ("MISS", NS, "MISS", "MISS"))
    add("F3: the revenue fetch failed", scored_result(without(fresh(), "llama_revenue_near-intents", "RuntimeError: GET failed")), ("MISS", "PASS", NS, "MISS"))
    add("F3: a day of revenue is missing", scored_result(drop_day(fresh(), "llama_revenue_near-intents", "2026-11-01")), ("MISS", "PASS", NS, "MISS"))
    add("F3 and F4: Intents' own volume fetch failed", scored_result(without(fresh(), "llama_volume_near-intents", "RuntimeError: GET failed")),
        ("MISS", "PASS", NS, NS))
    add("F3 and F4: fetched before the cutoff", scored_result(fresh("2026-11-13T23:00:00Z")), ("MISS", "PASS", NS, NS))
    add("F4: a peer's fetch failed", scored_result(without(fresh(), "llama_volume_maya-protocol", "RuntimeError: GET failed")), ("MISS", "PASS", "MISS", NS))
    add("F4: a day of a peer is missing", scored_result(drop_day(fresh(), "llama_volume_maya-protocol", "2026-11-01")), ("MISS", "PASS", "MISS", NS))
    add("F3 and F4: Intents' own volume is zero", scored_result(zero_volumes(fresh(), ["near-intents"])), ("MISS", "PASS", NS, "MISS"))
    every = fresh()
    every["sources"] = {}
    every["errors"] = {"rpc_f1": RPC_ERROR, "nearblocks_charts": "URLError: boom"}
    add("every fetch failed", scored_result(every), (NS, NS, NS, NS))
    add("the real window, with data that end on 2026-11-04", scored_result(fresh(), sf.WINDOW), ("MISS", NS, NS, NS))
    return out


class WhatTheScorerCanWrite(unittest.TestCase):
    """The scoring-day inputs: the result.json that the real score() and main() write when the committed snapshots are complete, and when
    a fetch failed, a day is missing, the volume is zero, or the data stop before the window ends. Every one of them renders, and its page
    ties to it. The one exception is a share of zero over zero, which the scorer writes as a MISS with a share of NaN: no honest number can
    be drawn, so the render stops (HandEditedResults) with a message that says how to clear it."""

    def test_each_input_gives_the_words_it_was_built_to_give(self):
        inputs = scorer_inputs()
        self.assertGreaterEqual(len(inputs), 15)
        for label, res, words in inputs:
            with self.subTest(label):
                self.assertEqual(tuple(res["results"][f]["result"] for f in R.FORWARD_IDS), words)
                self.assertEqual((res["mode"], res["is_score"]), ("score", True))

    def test_every_result_the_scorer_writes_renders_and_its_page_ties_to_it(self):
        for label, res, words in scorer_inputs():
            with self.subTest(label):
                ctx = context(res)
                dom, page = parsed(R.card_forward(ctx)), R.build_page(ctx)
                card = card_node(dom, "forward")
                listed = [n.text().strip() for n in card.find_all("span") if "data-status" in n.attrs]
                self.assertEqual(listed, list(words))
                table = next(t for t in card.find_all("table") if t.find("caption").text() == "Forward tests as frozen")
                self.assertEqual([tr.find_all("td")[2].text().strip() for tr in table.find_all("tr") if tr.find_all("td")], list(words))
                self.assertGreater(check_forward_numbers(self, dom, res), 3)
                self.assertLessEqual(max(len(line) for line in page.split("\n")), 2000)
                counts = {w: words.count(w) for w in ("PASS", "MISS", NS)}
                self.assertEqual(re.sub(r"\s+", " ", hl(card).text()),
                                 f"Forward tests scored: {counts['PASS']} passed, {counts['MISS']} missed and {counts[NS]} not scorable of 4.")
                tile = [n for n in parsed(R.scorecard(ctx)).find_all("li") if "tile" in n.classes()][4]
                self.assertIn(f"{counts['PASS']} pass, {counts['MISS']} miss", tile.text())
                for li in card.find_all("li"):
                    fid = li.attrs.get("data-k")
                    if fid in R.FORWARD_IDS and res["results"][fid]["result"] == NS:
                        why = " ".join(ascii_words(res["results"][fid]["why"]))
                        self.assertEqual(" ".join(ascii_words(li.find("p", "tnote").text())), f"Not scorable: {why}. It is never estimated.", fid)
                for svg in card.find_all("svg", "svg"):       # a dot for each test that has a number, none for the others
                    self.assertEqual(len(svg.find_all("circle", "sk")), sum(1 for w in words if w != NS), label)

    def test_a_zero_total_volume_is_the_one_result_that_cannot_be_drawn_and_it_stops_with_a_message(self):
        res = scored_result(zero_volumes(realistic_snapshot()))
        self.assertEqual(tuple(res["results"][f]["result"] for f in R.FORWARD_IDS), ("MISS", "PASS", NS, "MISS"))
        self.assertEqual(res["results"]["F3"]["why"], "zero volume")
        self.assertTrue(math.isnan(res["results"]["F4"]["intents_share_pct"]), "the scorer writes a share of NaN, not 'not scorable'")
        with tempfile.TemporaryDirectory() as d:
            write_forward(Path(d), STAMPED, res)
            raw = (Path(d) / STAMPED / "result.json").read_text(encoding="utf-8")
            self.assertIn('"intents_share_pct": NaN', raw)                # what a file written by json.dumps holds
            with self.assertRaises(SystemExit) as caught:
                R.render(forward_dir=Path(d))
        message = str(caught.exception)
        self.assertTrue(message.startswith("render: F4.intents_share_pct is nan, not a finite number"), message)
        self.assertIn(f"data/forward/{STAMPED}/result.json", message)
        res["results"]["F4"].update(result=NS, why="zero total volume over the window")        # the edit the message asks for
        dom = parsed(R.card_forward(context(res)))
        self.assertGreater(check_forward_numbers(self, dom, res), 5)
        self.assertEqual([n.text().strip() for n in card_node(dom, "forward").find_all("span") if "data-status" in n.attrs],
                         ["MISS", "PASS", NS, NS])


# ---- a long reason
def longest_line(page: str) -> int:
    return max(len(line) for line in page.split("\n"))


class LongReasons(unittest.TestCase):
    """F1's reason for 'not scorable' is the text of the RPC error, which can run to thousands of characters, and the suite fails on a line of
    the page over 2,000 (tests/test_render.py, LineBreaks). A 2,395-character reason made the page a line of 2,623 and the suite fail on
    scoring day, though `render` and `render --check` passed. The reason is now broken at spaces, one source line at most R.REASON_LINE."""

    @staticmethod
    def page_with(why: str) -> tuple[Node, str, dict]:
        """(the forward card parsed, the whole page, the result) for a scored result whose F1 is not scorable for this reason."""
        res = base()
        res["results"]["F1"] = {"result": NS, "why": why}
        ctx = context(res)
        return parsed(R.card_forward(ctx)), R.build_page(ctx), res

    def span(self, dom: Node) -> Node:
        found = [n for n in dom.iter() if n.attrs.get("data-f") == "F1.why"]
        self.assertEqual(len(found), 1)
        return found[0]

    def test_the_reviewers_2395_character_reason_keeps_every_line_short_and_its_text(self):
        self.assertEqual(len(LONG_RPC_ERROR), 2395)
        dom, page, res = self.page_with(LONG_RPC_ERROR)
        self.assertLessEqual(longest_line(page), 2000)
        self.assertEqual(ascii_words(self.span(dom).text()), ascii_words(LONG_RPC_ERROR))
        self.assertGreater(check_forward_numbers(self, dom, res), 3)
        short = self.page_with("a DefiLlama peer fetch is missing")[1].split("\n")
        extra = [line for line in page.split("\n") if line not in set(short)]
        self.assertGreater(len(extra), 2, "the reason takes several lines of the page")
        self.assertLessEqual(max(len(line) for line in extra), R.REASON_LINE + 120)

    def test_the_old_code_made_a_line_of_more_than_2000_characters_of_the_same_reason(self):
        """The control: the reason as the old code wrote it, whole on one line (this checks the premise of the test above, not the render)."""
        _, page, _ = self.page_with(LONG_RPC_ERROR)
        unwrapped = page.replace(R.wrap_reason(LONG_RPC_ERROR), R.esc(LONG_RPC_ERROR))
        self.assertNotEqual(unwrapped, page)
        self.assertGreater(longest_line(unwrapped), 2000)

    def test_one_word_of_3000_characters_has_no_space_to_break_at_and_is_cut_in_the_source_only(self):
        word = "q" * 3000
        dom, page, res = self.page_with(word)
        self.assertLessEqual(longest_line(page), 2000)
        self.assertEqual(self.span(dom).text(), word, "the text is the word, whole: the break is a comment, which is not text")
        self.assertEqual(page.count(R.SOURCE_BREAK), 2, "three pieces of at most R.REASON_LINE characters")
        self.assertGreater(check_forward_numbers(self, dom, res), 3)
        self.assertIn(R.SOURCE_BREAK, page)

    def test_a_reason_of_quote_marks_is_measured_as_the_page_writes_it(self):
        """A quote mark is six characters in the page (&#x27;). 1,500 of them are 9,000, so they are cut by what they take in the source."""
        dom, page, res = self.page_with("'" * 1500)
        self.assertLessEqual(longest_line(page), 2000)
        self.assertEqual(self.span(dom).text(), "'" * 1500)
        words = self.page_with("' " * 3000)
        self.assertLessEqual(longest_line(words[1]), 2000)
        self.assertEqual(ascii_words(self.span(words[0]).text()), ["'"] * 3000)

    def test_white_space_in_a_reason_is_drawn_as_one_space_and_a_blank_reason_as_nothing(self):
        dom, _, _ = self.page_with("a\t b\n\n  c\r\nd")
        self.assertEqual(ascii_words(self.span(dom).text()), ["a", "b", "c", "d"])
        for blank in ("", "   \n "):
            dom, page, _ = self.page_with(blank)
            self.assertEqual(self.span(dom).text(), "")
            self.assertLessEqual(longest_line(page), 2000)

    def test_a_non_breaking_space_and_a_line_separator_are_drawn_as_they_are(self):
        """Only ASCII white space is cut at: str.split() would also turn U+00A0 and U+2028 into spaces, which changes the drawing (a browser does not
        break at a non-breaking space) and the height of the note on a narrow screen."""
        why = "a\u00a0b\u2028c d"
        dom, _, _ = self.page_with(why)
        self.assertEqual(self.span(dom).text(), why)

    def test_the_line_breaks_of_the_page_still_add_only_newlines_around_a_wrapped_reason(self):
        for why in (LONG_RPC_ERROR, "q" * 3000, "'" * 1500):
            with self.subTest(why[:12]):
                res = base()
                res["results"]["F1"] = {"result": NS, "why": why}
                ctx = context(res)
                plain, broken = R.build_page(ctx, breaks=False), R.build_page(ctx)
                self.assertGreater(len(broken), len(plain))
                self.assertEqual(plain.replace("\n", ""), broken.replace("\n", ""), "break_lines added newlines and nothing else")
                self.assertEqual(R.break_lines(broken), broken, "and it is idempotent on this page")

    # ---- wrap_reason on its own
    def test_wrap_reason_escapes_and_leaves_a_short_reason_alone(self):
        self.assertEqual(R.wrap_reason("a DefiLlama peer fetch is missing or before 2026-11-14"), "a DefiLlama peer fetch is missing or before 2026-11-14")
        self.assertEqual(R.wrap_reason('a < b & "c" \'d\''), "a &lt; b &amp; &quot;c&quot; &#x27;d&#x27;")
        self.assertEqual(R.wrap_reason(""), "")

    def test_wrap_reason_breaks_at_spaces_and_no_line_is_longer_than_the_width(self):
        text = " ".join(f"word{i}" for i in range(300))
        for width in (20, 57, 100, 1000):
            with self.subTest(width=width):
                lines = R.wrap_reason(text, width).split("\n")
                self.assertTrue(all(len(line) <= width for line in lines), max(map(len, lines)))
                self.assertEqual(" ".join(lines), text, "a newline stands where a space was, and nothing else changed")
                self.assertTrue(all(len(a) + 1 + len(b.split(" ")[0]) > width for a, b in zip(lines, lines[1:])), "no line is broken early")

    def test_wrap_reason_cuts_a_word_that_no_line_can_hold_without_cutting_an_entity(self):
        for word in ("x" * 100, "&" * 100, "'" * 70, "a<b" * 40):
            with self.subTest(word[:6]):
                marked = R.wrap_reason("start " + word + " end", 30)
                lines = marked.split("\n")
                self.assertEqual(lines[0], "start")
                self.assertEqual(lines[-1], "end")
                pieces = "\n".join(lines[1:-1]).split(R.SOURCE_BREAK)
                self.assertGreater(len(pieces), 1)
                self.assertTrue(all(len(piece) <= 30 for piece in pieces), [len(p) for p in pieces])
                self.assertEqual(html.unescape("".join(pieces)), word, "no entity is cut: the pieces read back as the word")
                for piece in pieces:
                    self.assertEqual(html.unescape(piece).count("&"), piece.count("&amp;"), "a piece holds whole entities")

    def test_the_source_break_is_a_comment_that_holds_only_a_newline(self):
        self.assertEqual(R.SOURCE_BREAK, "<!--\n-->")
        dom, errors = parse("<p>ab" + R.SOURCE_BREAK + "cd</p>")
        self.assertEqual((errors, dom.find("p").text()), ([], "abcd"))


class FreezeOrder(unittest.TestCase):
    """The page says the freeze came before the first BigQuery result the repository records only because the manifest says so; if it
    ever does not, the render stops. The boundary is the instant of the freeze commit itself."""

    FREEZE = datetime.fromisoformat(R.FREEZE_UTC)

    def ctx(self, *rows: tuple[str, str, float]):
        """A Ctx stand-in with a manifest of (path, source, seconds after the freeze) rows."""
        return types.SimpleNamespace(manifest={rel: {"source": src, "fetched_at": (self.FREEZE + timedelta(seconds=sec)).strftime("%Y-%m-%dT%H:%M:%SZ")}
                                               for rel, src, sec in rows})

    def test_a_first_record_at_or_before_the_freeze_stops_the_render(self):
        for seconds in (0, -1, -3600):
            with self.subTest(seconds=seconds), self.assertRaises(SystemExit) as caught:
                R.freeze_order(self.ctx(("raw/bq/a.json", "bigquery: sql/a.sql", seconds)))
            self.assertIn("raw/bq/a.json", str(caught.exception))
            self.assertIn("not after the freeze commit", str(caught.exception))

    def test_a_first_record_after_the_freeze_is_accepted(self):
        for seconds in (1, 29, 61, 599, 601, 86400):
            with self.subTest(seconds=seconds):
                span, how_long = R.freeze_order(self.ctx(("raw/bq/a.json", "bigquery: sql/a.sql", seconds)))
                self.assertIn('data-r="stamp:raw/bq/a.json"', span)
                self.assertTrue(how_long)

    def test_the_first_record_is_the_earliest_one_that_says_bigquery(self):
        ctx = self.ctx(("raw/rpc/early.json", "rpc view_account", -9999), ("raw/bq/late.json", "BigQuery: sql/late.sql", 500),
                       ("raw/bq/first.json", "bigquery: sql/first.sql", 40), ("raw/llama/x.json", "https://api.llama.fi/x", -5))
        rel, stamp = R.first_bigquery_record(ctx)
        self.assertEqual(rel, "raw/bq/first.json")
        self.assertEqual(stamp, (self.FREEZE + timedelta(seconds=40)).strftime("%Y-%m-%d %H:%M:%S"))

    def test_a_manifest_without_a_bigquery_record_stops_the_render(self):
        with self.assertRaises(SystemExit):
            R.first_bigquery_record(self.ctx(("raw/rpc/early.json", "rpc view_account", 5)))

    def test_the_committed_manifest_puts_the_first_record_after_the_freeze(self):
        ctx = R.Ctx()
        R.freeze_order(ctx)


class WhatMainReports(unittest.TestCase):
    """`render --out DIR` wrote DIR/index.html and said it wrote site/index.html, and it read the data a second time, without the
    --forward-dir it was given, to name the fingerprint: with a broken default data/forward it stopped after the page was written."""

    @staticmethod
    def run_main(*args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = R.main(list(args))
        return code, out.getvalue(), err.getvalue()

    SUMMARY = r"\([\d,]+ bytes\), data fingerprint [0-9a-f]{16}, data as of \d{4}-\d{2}-\d{2}"

    def test_out_names_the_file_it_wrote(self):
        with tempfile.TemporaryDirectory() as d:
            site = Path(d) / "elsewhere"
            code, out, err = self.run_main("--out", str(site))
            self.assertEqual((code, err), (0, ""))
            self.assertRegex(out, "^" + re.escape(f"render: wrote {site / R.PAGE_NAME} ") + self.SUMMARY + "\n$")
            self.assertNotIn("site/index.html", out)
            code, out, err = self.run_main("--check", "--out", str(site))
            self.assertEqual((code, err), (0, ""))
            self.assertRegex(out, "^" + re.escape(f"render: {site} matches a fresh render ({site / R.PAGE_NAME} ") + self.SUMMARY + r"\)" + "\n$")
            (site / R.PAGE_NAME).unlink()
            code, out, err = self.run_main("--check", "--out", str(site))
            self.assertEqual((code, out), (1, ""))
            self.assertIn(f"FAIL  missing: {site / R.PAGE_NAME}", err)
            self.assertIn(f"render: {site} is out of date", err)

    def test_the_default_messages_are_exactly_what_the_readme_quotes(self):
        p = subprocess.run([sys.executable, "-m", "pipeline.render", "--check"], cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", check=False)
        self.assertEqual((p.returncode, p.stderr), (0, ""))
        self.assertRegex(p.stdout, r"^render: site/ matches a fresh render \(site/index\.html " + self.SUMMARY + r"\)" + "\n$")
        with mock.patch.object(Path, "write_bytes", autospec=True) as write, mock.patch.object(Path, "mkdir", autospec=True):
            code, out, err = self.run_main()
        self.assertEqual((code, err), (0, ""))
        self.assertRegex(out, r"^render: wrote site/index\.html " + self.SUMMARY + "\n$")
        # Two files since 2026-11-14: the dashboard and the story page (site/story.html), in that order; the message names the dashboard.
        self.assertEqual([c.args[0] for c in write.call_args_list], [ROOT / R.SITE_DIR / R.PAGE_NAME, ROOT / R.SITE_DIR / R.STORY_NAME])

    def test_the_byte_count_fingerprint_and_date_the_readme_quotes_are_the_pages(self):
        """README.md step 6 prints what `render --check` and `render` print: the size of the page, the data fingerprint and the data date. Nothing
        compared them with the page, so every commit that changed the page could leave the README quoting an old size (it did, three times)."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        quoted = re.findall(r"site/index\.html \(([\d,]+) bytes\), data fingerprint ([0-9a-f]{16}), data as of (\d{4}-\d{2}-\d{2})", readme)
        self.assertEqual(len(quoted), 2, "step 6 of README.md quotes the line twice: after `render --check` and after `render`")
        files, ctx = R.build_site()
        want = (f"{len(files[PAGE_KEY]):,}", ctx.fingerprint, ctx.m["asof"])
        for got in quoted:
            self.assertEqual(got, want, f"README.md step 6 quotes (N bytes) = {got[0]}, fingerprint {got[1]}, data as of {got[2]}; the page is "
                                        f"{want[0]} bytes, fingerprint {want[1]}, data as of {want[2]}. Edit those two lines of README.md to say so "
                                        "(`python3 -m pipeline.render --check` prints them).")

    def test_the_metric_count_the_readme_quotes_is_the_one_compute_prints(self):
        """README.md steps 2 and 5 quote what `python3 -m pipeline.compute` prints: the number of metrics and the data date. Nothing compared
        them with data/metrics.json, so the README went on saying 270 after compute had grown to 378 (found by an outside screen, 2026-11-13)."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        quoted = re.findall(r"wrote data/metrics\.json \((\d+) metrics, as of (\d{4}-\d{2}-\d{2})\)", readme)
        self.assertEqual(len(quoted), 3, "README.md quotes the compute line three times: step 2 (twice) and step 5")
        m = json.loads((ROOT / "data" / "metrics.json").read_text(encoding="utf-8"))
        want = (str(len(m)), m["asof"])
        for got in quoted:
            self.assertEqual(got, want, f"README.md quotes ({got[0]} metrics, as of {got[1]}); `python3 -m pipeline.compute` prints "
                                        f"({want[0]} metrics, as of {want[1]}). Edit README.md steps 2 and 5 to say so.")

    def test_a_given_forward_dir_is_not_this_repositorys_own_render_so_the_hint_carries_it(self):
        """`render --check --forward-dir DIR` without --out was taken for the repository's own check, and its hint said to run
        `python3 -m pipeline.render` and commit the result, which reads data/forward and not DIR: following it could not make the check pass."""
        with tempfile.TemporaryDirectory() as d:
            scored = Path(d) / "scored"
            res = fixture_result()
            res["scored_at"] = "1999-12-31T23:59:59Z"                  # a score no committed page can contain, even a rehearsal built from the fixture
            write_forward(scored, STAMPED, res)                        # so this page differs from the committed one, pending or scored
            code, out, err = self.run_main("--check", "--forward-dir", str(scored))
            site = ROOT / R.SITE_DIR
            self.assertEqual((code, out), (1, ""))
            self.assertIn(f"FAIL  differs from a fresh render: {site / R.PAGE_NAME}", err)
            self.assertIn(f"render: {site} is out of date; run `python3 -m pipeline.render --forward-dir {scored} --out {site}`", err)
            self.assertNotIn("and commit the result", err)
            # and the hint works: the check passes against the folder the hint writes
            elsewhere = Path(d) / "site"
            self.assertEqual(self.run_main("--forward-dir", str(scored), "--out", str(elsewhere))[0], 0)
            self.assertEqual(self.run_main("--check", "--forward-dir", str(scored), "--out", str(elsewhere))[0], 0)

    def test_the_hint_for_a_root_that_is_not_this_repo_carries_its_arguments(self):
        """Following the hint must render THAT root and THAT forward folder, not this repository's data."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "root"
            shutil.copytree(ROOT / "data", root / "data", ignore=shutil.ignore_patterns("forward"))
            shutil.copytree(ROOT / "sql", root / "sql")
            shutil.copy2(ROOT / "PREREG.md", root / "PREREG.md")
            code, out, err = self.run_main("--root", str(root))
            self.assertEqual((code, err), (0, ""))
            self.assertRegex(out, "^" + re.escape(f"render: wrote {root / R.SITE_DIR / R.PAGE_NAME} ") + self.SUMMARY + "\n$")
            self.assertNotIn("render: wrote site/index.html", out)
            ok = Path(d) / "ok"
            write_forward(ok, STAMPED, fixture_result())
            (root / R.SITE_DIR / R.PAGE_NAME).write_bytes(b"stale")
            code, out, err = self.run_main("--check", "--root", str(root), "--forward-dir", str(ok))
            self.assertEqual((code, out), (1, ""))
            self.assertIn(f"`python3 -m pipeline.render --root {root} --forward-dir {ok} --out {root / R.SITE_DIR}`", err)

    def test_one_context_is_built_and_the_forward_dir_given_is_the_one_used(self):
        calls: list[tuple] = []
        real_init = R.Ctx.__init__

        def spy(self_, *a, **k):
            calls.append((a, k))
            real_init(self_, *a, **k)

        with tempfile.TemporaryDirectory() as d:
            ok = Path(d) / "ok"
            write_forward(ok, STAMPED, fixture_result())
            with mock.patch.object(R.Ctx, "__init__", spy):
                code, out, err = self.run_main("--forward-dir", str(ok), "--out", str(Path(d) / "site"))
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(len(calls), 1, "the data is read once, with the arguments the command was given")
        self.assertEqual(Path(calls[0][0][1] if len(calls[0][0]) > 1 else calls[0][1]["forward_dir"]), ok)

    def test_a_broken_default_forward_folder_does_not_stop_a_command_that_was_given_another(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "root"
            # data/forward is left out: once a real score is committed it would be copied too, and this folder must be the only one
            shutil.copytree(ROOT / "data", root / "data", ignore=shutil.ignore_patterns("forward"))
            shutil.copytree(ROOT / "sql", root / "sql")
            shutil.copy2(ROOT / "PREREG.md", root / "PREREG.md")
            bad = root / "data" / "forward" / STAMPED
            bad.mkdir(parents=True)
            (bad / "result.json").write_bytes(b"\xef\xbb\xbf" + json.dumps(fixture_result()).encode("utf-8"))   # a byte-order mark
            ok = Path(d) / "ok"
            write_forward(ok, STAMPED, fixture_result())
            site = Path(d) / "site"
            code, out, err = self.run_main("--root", str(root), "--forward-dir", str(ok), "--out", str(site))
            self.assertEqual((code, err), (0, ""), out)
            self.assertEqual((site / R.PAGE_NAME).read_bytes(), R.render(root, ok)[PAGE_KEY])
            code, out, err = self.run_main("--check", "--root", str(root), "--forward-dir", str(ok), "--out", str(site))
            self.assertEqual((code, err), (0, ""), out)
            with self.assertRaises(SystemExit) as caught:          # and the broken one still stops a command that reads it
                self.run_main("--root", str(root), "--out", str(Path(d) / "other"))
            self.assertIn(STAMPED, str(caught.exception))
            self.assertFalse((Path(d) / "other").exists(), "nothing is written when the data cannot be read")

    def test_summary_still_takes_a_repo_root(self):
        files = R.render()
        self.assertEqual(R.summary(files, ROOT), R.summary(files, R.Ctx()))
        self.assertTrue(R.summary(files, R.Ctx(), "x/y.html").startswith("x/y.html ("))


if __name__ == "__main__":
    unittest.main(verbosity=2)
