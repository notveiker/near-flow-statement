"""Offline tests for pipeline/score_forward.py against the repo's committed raw snapshots (no network).

Run: make test   (python3 -m unittest discover -s tests -v, from the repo root)
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import score_forward as sf  # noqa: E402

REPO_RAW = ROOT / "data" / "raw"
WIN = ("2026-10-28", "2026-11-04")  # 8 days the repo snapshot covers


def repo_snapshot(fetched_at: str = "2026-11-14T01:00:00Z") -> dict:
    src = {}
    for p in sf.PEERS:
        src[f"llama_volume_{p}"] = {"url": "repo", "fetched_at": fetched_at,
                                    "data": json.loads((REPO_RAW / f"llama/volume_{p}.json").read_text())}
    src["llama_revenue_near-intents"] = {"url": "repo", "fetched_at": fetched_at, "data": json.loads(
        (REPO_RAW / "llama/dailyRevenue_near-intents.json").read_text())}
    src["nearblocks_charts"] = {"url": "repo", "fetched_at": fetched_at,
                                "data": json.loads((REPO_RAW / "nearblocks/charts.json").read_text())}
    w = json.loads((REPO_RAW / "rpc/wallets.json").read_text())
    src["rpc_f1"] = {"url": "repo", "fetched_at": fetched_at, "data": {
        "target_utc": "2026-11-14T00:00:00Z", "block_height": w["at_block"], "block_hash": "x",
        "block_timestamp_ns": 0, "view_account": w["accounts"][sf.BUYBACK]}}
    return {"fetched_at": fetched_at, "sources": src, "errors": {}}


class T(unittest.TestCase):
    def test_values_match_independent_arithmetic(self):
        res = sf.score(repo_snapshot(), WIN, sf.SCORE_NOT_BEFORE)
        days = sf.days_between(*WIN)
        rev = {sf.day_of(t): v for t, v in json.loads((REPO_RAW / "llama/dailyRevenue_near-intents.json")
                                                      .read_text())["totalDataChart"]}
        vols = {p: {sf.day_of(t): v for t, v in json.loads((REPO_RAW / f"llama/volume_{p}.json").read_text())
                    ["totalDataChart"]} for p in sf.PEERS}
        bp = sum(rev[d] for d in days) / sum(vols["near-intents"][d] for d in days) * 1e4
        self.assertAlmostEqual(res["F3"]["take_rate_bp"], bp, places=9)
        share = sum(vols["near-intents"][d] for d in days) / sum(vols[p][d] for p in sf.PEERS for d in days) * 100
        self.assertAlmostEqual(res["F4"]["intents_share_pct"], share, places=9)
        w = json.loads((REPO_RAW / "rpc/wallets.json").read_text())["accounts"][sf.BUYBACK]
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

    def test_refuses_before_nov_14(self):
        if datetime.now(timezone.utc) >= sf.SCORE_NOT_BEFORE:
            self.skipTest("past 2026-11-14")
        p = subprocess.run([sys.executable, "-m", "pipeline.score_forward", "--score"],
                           capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(p.returncode, 2)
        self.assertIn("refusing to score", p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
