"""The paths of pipeline/render.py that stop the render or refuse a value, and the parts of a scored page that
tests/test_render.py leaves to the live data. Each test here was written together with a mutant of the code that must fail it.

  * MisnamedScoreFolders           a real score in a score_* folder not named score_YYYYMMDDTHHMMSSZ stops the render
  * ObservedValuesTheAxisCannotDraw  an observed value no axis can draw stops the render with a message, not with memory
  * TheAxisWidens                  the forward-test axes widen for an observed value outside the frozen band
  * ScoredStatusIcons              the icon of each F1-F4 row of a scored card
  * FreezeOrder                    the render stops unless the manifest puts the first BigQuery record after the freeze
  * WhatMainReports                `--out` is reported as written, and the folder given with --forward-dir is the one used

The fixtures come from tests/test_render.py (fixture_result), so they follow the layout pipeline.score_forward writes.
Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import contextlib
import io
import json
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
from test_render import card_node, fixture_result, forward_dom, write_forward  # noqa: E402

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
    # It says it is a score but is not complete. It could not be drawn if its folder were named right, and in a folder that is not,
    # it still stops the render: the claim is what matters to a person who looks for the score and finds a page that says pending.
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
                write_forward(tmp, STAMPED, obj)                       # while in a folder named as the scorer names it, it is ignored
                (tmp / "score_final" / "result.json").unlink()
                (tmp / "score_final").rmdir()
                self.assertIsNone(R.load_forward(tmp))

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
    res["results"][fid][key] = value
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
        write.assert_called_once()
        self.assertEqual(write.call_args.args[0], ROOT / R.SITE_DIR / R.PAGE_NAME)

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
