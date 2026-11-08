"""Offline tests for pipeline/score_forward.py against the repo's committed raw snapshots (no network).

Run: make test   (python3 -m unittest discover -s tests -v, from the repo root)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import render as R  # noqa: E402
from pipeline import score_forward as sf  # noqa: E402

REPO_RAW = ROOT / "data" / "raw"
WIN = ("2026-10-28", "2026-11-04")  # 8 days the repo snapshot covers
# PREREG.md: "Scoring uses DefiLlama data fetched on or after 2026-11-14 and the first final RPC block after 2026-11-14 00:00 UTC."
# Written out here, not read from pipeline.score_forward, so moving the module's constant cannot also move the tests.
CUTOFF = datetime(2026, 11, 14, 0, 0, 0, tzinfo=timezone.utc)


def repo_snapshot(fetched_at: str = "2026-11-14T01:00:00Z") -> dict:
    src = {}
    for p in sf.PEERS:
        src[f"llama_volume_{p}"] = {"url": "repo", "fetched_at": fetched_at,
                                    "data": json.loads((REPO_RAW / f"llama/volume_{p}.json").read_text(encoding="utf-8"))}
    src["llama_revenue_near-intents"] = {"url": "repo", "fetched_at": fetched_at, "data": json.loads(
        (REPO_RAW / "llama/dailyRevenue_near-intents.json").read_text(encoding="utf-8"))}
    src["nearblocks_charts"] = {"url": "repo", "fetched_at": fetched_at,
                                "data": json.loads((REPO_RAW / "nearblocks/charts.json").read_text(encoding="utf-8"))}
    w = json.loads((REPO_RAW / "rpc/wallets.json").read_text(encoding="utf-8"))
    src["rpc_f1"] = {"url": "repo", "fetched_at": fetched_at, "data": {
        "target_utc": "2026-11-14T00:00:00Z", "block_height": w["at_block"], "block_hash": "x",
        "block_timestamp_ns": 0, "view_account": w["accounts"][sf.BUYBACK]}}
    return {"fetched_at": fetched_at, "sources": src, "errors": {}}


class T(unittest.TestCase):
    def test_values_match_independent_arithmetic(self):
        res = sf.score(repo_snapshot(), WIN, sf.SCORE_NOT_BEFORE)
        days = sf.days_between(*WIN)
        rev = {sf.day_of(t): v for t, v in json.loads((REPO_RAW / "llama/dailyRevenue_near-intents.json")
                                                      .read_text(encoding="utf-8"))["totalDataChart"]}
        vols = {p: {sf.day_of(t): v for t, v in json.loads((REPO_RAW / f"llama/volume_{p}.json").read_text(encoding="utf-8"))
                    ["totalDataChart"]} for p in sf.PEERS}
        bp = sum(rev[d] for d in days) / sum(vols["near-intents"][d] for d in days) * 1e4
        self.assertAlmostEqual(res["F3"]["take_rate_bp"], bp, places=9)
        share = sum(vols["near-intents"][d] for d in days) / sum(vols[p][d] for p in sf.PEERS for d in days) * 100
        self.assertAlmostEqual(res["F4"]["intents_share_pct"], share, places=9)
        w = json.loads((REPO_RAW / "rpc/wallets.json").read_text(encoding="utf-8"))["accounts"][sf.BUYBACK]
        self.assertEqual(res["F1"]["balance_near"], int(w["amount"]) / sf.YOCTO)
        self.assertEqual(res["F2"]["n_deltas"], 8)
        self.assertTrue(80_000 < res["F2"]["mean_near_per_day"] < 95_000)
        for k in ("F1", "F2", "F3", "F4"):
            self.assertIn(res[k]["result"], ("PASS", "MISS"))

    def test_missing_day_is_not_scorable(self):
        snap = repo_snapshot()
        tdc = snap["sources"]["llama_volume_maya-protocol"]["data"]["totalDataChart"]
        snap["sources"]["llama_volume_maya-protocol"]["data"]["totalDataChart"] = [
            x for x in tdc if sf.day_of(x[0]) != "2026-11-01"]
        res = sf.score(snap, WIN, sf.SCORE_NOT_BEFORE)
        self.assertEqual(res["F4"]["result"], sf.NOT_SCORABLE)
        self.assertNotEqual(res["F3"]["result"], sf.NOT_SCORABLE)

    def test_window_beyond_data_is_not_scorable(self):
        res = sf.score(repo_snapshot(), sf.WINDOW, sf.SCORE_NOT_BEFORE)  # real window, data ends 11-04
        for k in ("F2", "F3", "F4"):
            self.assertEqual(res[k]["result"], sf.NOT_SCORABLE, k)

    def test_early_fetch_is_not_scorable(self):
        res = sf.score(repo_snapshot(fetched_at="2026-11-13T23:00:00Z"), WIN, sf.SCORE_NOT_BEFORE)
        self.assertEqual(res["F3"]["result"], sf.NOT_SCORABLE)
        self.assertEqual(res["F4"]["result"], sf.NOT_SCORABLE)

    def test_failed_rpc_is_not_scorable(self):
        snap = repo_snapshot()
        del snap["sources"]["rpc_f1"]
        snap["errors"]["rpc_f1"] = "RuntimeError: boom"
        self.assertEqual(sf.score(snap, WIN, sf.SCORE_NOT_BEFORE)["F1"]["result"], sf.NOT_SCORABLE)

    def test_band_edges_inclusive(self):
        self.assertTrue(sf.in_band(2_210_000.0, sf.F1_BAND))
        self.assertTrue(sf.in_band(2_400_000.0, sf.F1_BAND))
        self.assertFalse(sf.in_band(2_400_000.0001, sf.F1_BAND))

    def test_the_cutoff_is_the_pre_registered_instant(self):
        self.assertEqual(sf.SCORE_NOT_BEFORE, CUTOFF)
        self.assertEqual(sf.F1_T, CUTOFF)

    def test_a_fetch_exactly_at_the_cutoff_counts_and_one_second_earlier_does_not(self):
        on_time = sf.score(repo_snapshot(fetched_at="2026-11-14T00:00:00Z"), WIN, CUTOFF)
        early = sf.score(repo_snapshot(fetched_at="2026-11-13T23:59:59Z"), WIN, CUTOFF)
        for k in ("F3", "F4"):
            self.assertIn(on_time[k]["result"], ("PASS", "MISS"), k)
            self.assertEqual(early[k]["result"], sf.NOT_SCORABLE, k)

    def test_refuses_before_nov_14(self):
        # The constant is compared with the literal first: if it were moved earlier, this test must fail, not skip itself.
        self.assertEqual(sf.SCORE_NOT_BEFORE, CUTOFF)
        if datetime.now(timezone.utc) >= CUTOFF:
            self.skipTest("past 2026-11-14")
        forward = ROOT / "data" / "forward"
        before = sorted(p.name for p in forward.iterdir()) if forward.is_dir() else None
        # --out and a dead proxy keep a guard that has been broken from writing into data/forward or reaching the network:
        # the scorer would then sit in its retry loop, so the run is cut off after a minute and the test fails.
        dead = {"HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9",
                "http_proxy": "http://127.0.0.1:9", "https_proxy": "http://127.0.0.1:9"}
        with tempfile.TemporaryDirectory() as out:
            p = subprocess.run([sys.executable, "-m", "pipeline.score_forward", "--score", "--out", out],
                               capture_output=True, text=True, encoding="utf-8", cwd=ROOT, env={**os.environ, **dead}, timeout=60)
            self.assertEqual(list(Path(out).iterdir()), [], "a refused run writes nothing")
        self.assertEqual(p.returncode, 2)
        self.assertIn("refusing to score", p.stderr)
        self.assertEqual(p.stdout, "", "a refusal prints nothing but the message on stderr")
        self.assertEqual(sorted(x.name for x in forward.iterdir()) if forward.is_dir() else None, before,
                         "a refused run must not create or change anything under data/forward")


class FromSnapshot(unittest.TestCase):
    """`--score --from-snapshot DIR` re-scores a saved snapshot offline. It does not compare the clock with the 2026-11-14 cutoff (it still stamps scored_at), it writes into DIR, and
    it believes the snapshot's own recorded times: the refusal before 2026-11-14 belongs to the live command, which fetches.

    What a snapshot has to show (established by running the code on fixtures):
      F3, F4  every DefiLlama source's own fetched_at must be on or after 2026-11-14 00:00 UTC, else 'not scorable';
      F1      the rpc_f1 read must name the target 2026-11-14T00:00:00Z. The live fetch raises 'nothing final yet' before
              that instant, and a dry run targets its own day, so neither writes that target before 2026-11-14;
      F2      Nearblocks must hold a total_supply row for 2026-11-05 through 2026-11-13. No fetch time is checked for F2; the
              committed Nearblocks snapshot, fetched on 2026-11-05 22:51 UTC, ends on 2026-11-04.
    So on the evidence of the code and of that snapshot, a snapshot the fetcher wrote before the cutoff scores nothing,
    while a hand-built one (the rehearsal fixture used here is one) can say anything: the scorer does not verify where a
    snapshot came from. A result.json is evidence together with its snapshot.json and the git history, not by itself."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def folder(self, snap: dict, name: str = "score_20261114T060000Z") -> Path:
        d = Path(self.tmp.name) / name
        d.mkdir()
        (d / "snapshot.json").write_text(json.dumps(snap, indent=1), encoding="utf-8")
        return d

    @staticmethod
    def cli(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-m", "pipeline.score_forward", *args], cwd=ROOT, capture_output=True,
                              text=True, encoding="utf-8", check=False)

    @staticmethod
    def written(d: Path) -> dict:
        return json.loads((d / "result.json").read_text(encoding="utf-8"))

    def test_it_does_not_gate_on_the_clock(self):
        d = self.folder(repo_snapshot(fetched_at="2026-11-14T06:00:00Z"))      # a fixture that claims a post-cutoff fetch
        p = self.cli("--score", "--from-snapshot", str(d))
        self.assertEqual(p.returncode, 0, p.stderr)                            # exit 0 on any day, before the cutoff too
        self.assertEqual(sorted(x.name for x in d.iterdir()), ["result.json", "snapshot.json"])
        r = self.written(d)
        self.assertEqual((r["mode"], r["is_score"], r["snapshot_fetched_at"]), ("score", True, "2026-11-14T06:00:00Z"))
        self.assertEqual(r["window"], list(sf.WINDOW))

    def test_a_snapshot_fetched_before_the_cutoff_cannot_score_the_defillama_tests(self):
        """KNOWN LIMIT, pinned as it is: the file still says is_score true and mode score (only its tests are 'not
        scorable'). A guard that wrote mode 'rehearsal' for such a snapshot would change this test, on purpose."""
        d = self.folder(repo_snapshot(fetched_at="2026-11-13T23:59:59Z"))
        self.assertEqual(self.cli("--score", "--from-snapshot", str(d)).returncode, 0)
        r = self.written(d)
        for k in ("F3", "F4"):
            self.assertEqual(r["results"][k]["result"], sf.NOT_SCORABLE, k)
            self.assertIn("before 2026-11-14", r["results"][k]["why"])
        self.assertEqual(r["results"]["F2"]["result"], sf.NOT_SCORABLE)        # no row for the window's days
        self.assertEqual((r["mode"], r["is_score"]), ("score", True))

    def test_f1_comes_from_the_snapshots_rpc_read_whatever_its_recorded_time(self):
        """F1 has no fetched_at check; its protection is the target string and the live fetch's own refusal."""
        snap = repo_snapshot(fetched_at="2026-11-08T00:00:00Z")
        d = self.folder(snap)
        self.cli("--score", "--from-snapshot", str(d))
        f1 = self.written(d)["results"]["F1"]
        self.assertIn(f1["result"], ("PASS", "MISS"))
        self.assertEqual(f1["target_utc"], "2026-11-14T00:00:00Z")

    def test_a_dry_run_snapshot_is_refused_as_a_score(self):
        snap = repo_snapshot(fetched_at="2026-11-08T00:00:00Z")
        snap["sources"]["rpc_f1"]["data"]["target_utc"] = "2026-11-08T00:00:00Z"     # what --dry-run targets: its own midnight
        d = self.folder(snap)
        p = self.cli("--score", "--from-snapshot", str(d))
        self.assertEqual(p.returncode, 2)
        self.assertIn("snapshot F1 target is not 2026-11-14T00:00:00Z; refusing", p.stderr)
        self.assertFalse((d / "result.json").exists(), "a refused snapshot must not leave a result behind")

    def test_a_snapshot_with_no_f1_read_scores_f1_as_not_scorable_and_says_why(self):
        snap = repo_snapshot(fetched_at="2026-11-08T00:00:00Z")
        del snap["sources"]["rpc_f1"]
        snap["errors"]["rpc_f1"] = "RuntimeError: final head 1 (1) is before the target time; nothing final yet"
        d = self.folder(snap)
        self.assertEqual(self.cli("--score", "--from-snapshot", str(d)).returncode, 0)
        r = self.written(d)
        self.assertEqual(r["results"]["F1"], {"result": sf.NOT_SCORABLE, "why": snap["errors"]["rpc_f1"]})
        self.assertEqual(r["fetch_errors"], snap["errors"])

    def test_the_result_goes_into_the_snapshot_folder_and_out_is_ignored(self):
        d = self.folder(repo_snapshot(fetched_at="2026-11-14T06:00:00Z"))
        elsewhere = Path(self.tmp.name) / "elsewhere"
        self.assertEqual(self.cli("--score", "--from-snapshot", str(d), "--out", str(elsewhere)).returncode, 0)
        self.assertTrue((d / "result.json").is_file())
        self.assertFalse(elsewhere.exists())

    def test_scoring_the_same_snapshot_twice_differs_only_in_scored_at(self):
        """The offline re-check of a committed result (re-score a copy of its folder and compare) relies on this."""
        d = self.folder(repo_snapshot(fetched_at="2026-11-14T06:00:00Z"))
        self.cli("--score", "--from-snapshot", str(d))
        first = (d / "result.json").read_text(encoding="utf-8")
        again = Path(self.tmp.name) / "again"
        again.mkdir()
        (again / "snapshot.json").write_bytes((d / "snapshot.json").read_bytes())
        self.cli("--score", "--from-snapshot", str(again))
        second = (again / "result.json").read_text(encoding="utf-8")
        strip = lambda t: re.sub(r'"scored_at": "[^"]*"', '"scored_at": "-"', t)  # noqa: E731
        self.assertEqual(strip(first), strip(second))
        self.assertTrue(first.startswith("{\n \"mode\""), "indent=1 JSON, as the committed results will be")

    def test_a_dry_run_never_writes_result_json(self):
        d = self.folder(repo_snapshot(fetched_at="2026-11-08T00:00:00Z"), name="dry-run_x")
        p = self.cli("--dry-run", "--from-snapshot", str(d))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("NOT A SCORE", p.stdout)
        self.assertEqual(sorted(x.name for x in d.iterdir()), ["DRY_RUN_result_NOT_A_SCORE.json", "snapshot.json"])
        r = json.loads((d / "DRY_RUN_result_NOT_A_SCORE.json").read_text(encoding="utf-8"))
        self.assertEqual((r["mode"], r["is_score"]), ("DRY-RUN", False))


class OnlyARealScoreIsRendered(unittest.TestCase):
    """The dashboard reads data/forward/score_<UTC stamp>/result.json and nothing else, and only with is_score true and mode
    score. (pipeline.render.load_forward; read here, not edited.) The folder name has to be score_YYYYMMDDTHHMMSSZ, the one
    pipeline.score_forward writes. Every case below that is meant to be rejected for what the FILE says uses such a name, so
    that the content test is what rejects it: with a name the filter would reject first (score_a) the content test would be
    pinned by nothing. Names that do not fit the pattern are in tests/test_render_guards.py."""

    GOOD = {"mode": "score", "is_score": True, "window": list(sf.WINDOW), "scored_at": "2026-11-14T06:00:00Z",
            "results": {"F1": {"result": sf.NOT_SCORABLE, "why": "x"}}}
    STAMPED = "score_20261114T061500Z"      # a folder name the scorer could have written

    def loaded(self, layout: dict[str, object]):
        with tempfile.TemporaryDirectory() as tmp:
            for rel, obj in layout.items():
                f = Path(tmp) / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(json.dumps(obj), encoding="utf-8")
            found = R.load_forward(Path(tmp))
            return None if found is None else found["_path"]

    def test_a_real_score_is_found(self):
        self.assertEqual(self.loaded({"score_20261114T061500Z/result.json": self.GOOD}),
                         "data/forward/score_20261114T061500Z/result.json")

    def test_a_valid_stamp_with_this_content_is_found(self):
        """The control for the next test: the same folder name and the same content, except for the one field it changes."""
        self.assertEqual(self.loaded({f"{self.STAMPED}/result.json": self.GOOD}), f"data/forward/{self.STAMPED}/result.json")

    def test_a_score_without_a_results_object_stops_the_render_instead_of_being_ignored(self):
        """It says it is a score (is_score true, mode score) and has nothing to draw: ignoring it left the page saying pending over it."""
        bad = f"{self.STAMPED}/result.json"
        for label, obj in (("no results", {k: v for k, v in self.GOOD.items() if k != "results"}),
                           ("results that is not an object", {**self.GOOD, "results": []})):
            with self.subTest(label), tempfile.TemporaryDirectory() as tmp:
                f = Path(tmp) / bad
                f.parent.mkdir(parents=True)
                f.write_text(json.dumps(obj), encoding="utf-8")
                with self.assertRaises(SystemExit) as caught:
                    R.load_forward(Path(tmp))
                self.assertIn(f"data/forward/{bad}", str(caught.exception))

    def test_nothing_else_under_data_forward_is_rendered_as_a_score(self):
        bad = f"{self.STAMPED}/result.json"
        for label, layout in (
                ("dry-run folder", {"dry-run_20261108T000000Z/DRY_RUN_result_NOT_A_SCORE.json": self.GOOD}),
                ("dry-run file inside a score folder", {f"{self.STAMPED}/DRY_RUN_result_NOT_A_SCORE.json": self.GOOD}),
                ("a dry-run result.json", {"dry-run_x/result.json": self.GOOD}),
                ("is_score false", {bad: {**self.GOOD, "is_score": False}}),
                ("is_score the text true", {bad: {**self.GOOD, "is_score": "true"}}),
                ("is_score the number 1", {bad: {**self.GOOD, "is_score": 1}}),
                ("is_score missing", {bad: {k: v for k, v in self.GOOD.items() if k != "is_score"}}),
                ("mode DRY-RUN", {bad: {**self.GOOD, "mode": "DRY-RUN"}}),
                ("mode missing", {bad: {k: v for k, v in self.GOOD.items() if k != "mode"}}),
                ("a JSON array", {bad: []}),
                ("a JSON number", {bad: 7}),
                ("a deeper folder", {f"{self.STAMPED}/sub/result.json": self.GOOD}),
                ("another prefix", {"rescore_20261114T061500Z/result.json": self.GOOD}),
                ("a file, not a folder", {"score_20261114T061500Z.json": self.GOOD}),
                ("a newer folder that is not a score hides an older one", {
                    "score_20261114T061500Z/result.json": self.GOOD,
                    "score_20261114T071500Z/result.json": {**self.GOOD, "is_score": False}})):
            with self.subTest(label):
                self.assertIsNone(self.loaded(layout))


if __name__ == "__main__":
    unittest.main(verbosity=2)
