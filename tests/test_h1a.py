"""Offline tests for pipeline/h1a.py: internal consistency of the committed epoch evidence, and the published
H1a / rating numbers (frozen 2026-11-06; a change here means the committed raw data changed).

Run: make test
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import h1a as H  # noqa: E402
from pipeline.common import read_raw  # noqa: E402


class Evidence(unittest.TestCase):
    def test_each_mint_is_the_header_identity(self):
        d, rows = H._epochs()
        for r in rows:
            self.assertEqual(int(r["mint"]),
                             int(r["start_total_supply"]) - int(r["prev_total_supply"]) + int(r["start_burnt"]))
            self.assertLess(r["prev_height"], r["start_height"])
            self.assertGreater(int(r["mint"]), 0)

    def test_epochs_are_contiguous_and_cover_the_window(self):
        d, rows = H._epochs()
        gaps = [b["start_height"] - a["start_height"] for a, b in zip(rows, rows[1:])]
        self.assertTrue(all(43_200 <= g <= 43_210 for g in gaps), gaps)
        self.assertLess(rows[0]["start_height"], H.W_FIRST)
        self.assertGreater(rows[-1]["start_height"], H.W_LAST)
        self.assertTrue(all(x["exact"] for x in d["identity_checks"]))

    def test_issuance(self):
        iss = H.issuance()
        self.assertEqual(iss["n_epochs"], 297)
        self.assertAlmostEqual(iss["gross"], 8_009_799.128, delta=0.01)
        self.assertAlmostEqual(iss["net"], 7_932_963.632, delta=0.01)
        self.assertAlmostEqual(iss["burn"], 76_835.496, delta=0.01)
        self.assertTrue(0.99 < iss["cap_share"] < 1.0)


class Metrics(unittest.TestCase):
    def test_h1a_keys(self):
        m: dict = {}
        H.h1a(m)
        self.assertEqual(m["h1a_gross_issuance_90d_m"], 8.0098)
        self.assertEqual(m["h1a_net_supply_change_90d_m"], 7.933)
        self.assertEqual(m["h1a_burn_90d_k"], 76.84)
        self.assertEqual(m["h1a_staking_rewards_90d_m"], 7.2088)
        self.assertEqual(m["h1a_ratio_as_written_x"], 6.56)
        self.assertEqual(m["h1a_ratio_endpoint_archival_x"], 6.56)
        self.assertEqual(m["h1a_ratio_with_lst_pool_x"], 5.96)
        self.assertEqual(m["h1a_residual_repo_m"], 7.11)
        self.assertEqual(m["h1a_residual_flipside_m"], 7.1)
        self.assertEqual(m["h1a_residual_left_k"], -12.1)
        self.assertFalse(m["h1a_pass_as_written"])

    def test_rating(self):
        base: dict = {}
        H.rating(base)
        self.assertEqual(base["rating_g_req_pct"], 33.2)
        self.assertEqual(base["rating_g_req_no_hsp029_pct"], 46.8)
        self.assertEqual(base["rating_g_obs_pct"], 619.0)
        self.assertEqual(base["rating_g_obs_near_pct"], 71.4)
        self.assertEqual(base["rating_output"], "pending (H1b not scored)")
        for verdict, want in (("pass", "Buy"), ("fail", "Hold"),
                              ("inconclusive (upper bound exceeds any plausible gross issuance)", "Hold")):
            m = {"h1b_verdict": verdict}
            H.rating(m)
            self.assertEqual(m["rating_output"], want, verdict)

    def test_rule_branches(self):
        # Avoid needs G_obs < G_req/2 with H1b failing: check the branch with a forced G_obs.
        ra = read_raw("rpc/rating_assumptions.json")
        self.assertEqual(ra["hsp029"]["activation_date"], "2027-02-14")
        orig = H.g_req
        try:
            H.g_req = lambda *a, **k: 100.0  # G_req = 10,000%/yr, so G_obs (619%) < G_req/2
            for verdict, want in (("fail", "Avoid"), ("pass", "Hold"), ("inconclusive", "Hold")):
                m = {"h1b_verdict": verdict}
                H.rating(m)
                self.assertEqual(m["rating_output"], want, verdict)
        finally:
            H.g_req = orig


if __name__ == "__main__":
    unittest.main(verbosity=2)
