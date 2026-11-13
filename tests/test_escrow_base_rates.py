"""pipeline/escrow_base_rates.py reproduces the base rates that the escrow-release forward tests E1-E5 quote
(PREREG-ADDENDUM.md, 2026-11-13 06:23 UTC entry), from committed data and days up to 2026-11-04 only. Two figures differ
slightly from that entry; its 2026-11-13 corrections-and-disclosures entry states both, and the tests below pin the
recomputed values."""
from __future__ import annotations

import unittest

from pipeline import escrow_base_rates as E


class EscrowBaseRates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = E.summary()

    def test_reads_no_day_after_the_cutoff(self):
        D = E.load()
        for key in ("price", "vol", "exp", "esc", "a"):
            self.assertLessEqual(max(D[key]), "2026-11-04", key)

    def test_windows(self):
        self.assertEqual((self.s["n_windows"], self.s["n_settled"]), (92, 39))

    def test_e1(self):
        s = self.s
        self.assertEqual((s["e1_pass"], s["e1_pass_settled"], s["e1_min_days_settled"]), (73, 39, 30))
        self.assertEqual((s["e1_min_daily_count_from_0829"], s["e1_median_daily_count_from_0829"]), (10, 27))

    def test_e2(self):
        s = self.s
        self.assertEqual((s["e2_pass"], s["e2_min_band_pct"], s["e2_min_band_end"], s["e2_min_floor_pct"]), (92, 97.3, "2026-10-05", 97.6))

    def test_e3(self):
        s = self.s
        self.assertEqual((s["e3_pass"], s["e3_pass_settled"], s["e3_max_settled_pct"], s["e3_max_all_pct"]), (55, 39, 11.8, 32.4))
        self.assertEqual((s["e3_day_1004_near"], s["e3_day_1015_near"]), (26697, 28623))
        self.assertAlmostEqual(s["e3_window_near_to_cutoff"], 298000, delta=1000)   # "about 298,000 NEAR"

    def test_e4(self):
        s = self.s
        self.assertEqual((s["e4_pass"], s["e4_pass_settled"], s["e4_min_settled"], s["e4_median_settled"]), (85, 39, 0.216, 0.368))
        # The entry says the minimum, 0.144, falls "in the windows ending 2026-08-10 to 08-12"; it is the one window ending 08-11.
        self.assertEqual((s["e4_min_all"], s["e4_min_all_ends"]), (0.144, ["2026-08-11"]))
        self.assertEqual((s["e4_outside_n"], s["e4_outside_pass"], s["e4_outside_median_settled"]), (61, 61, 0.535))
        self.assertAlmostEqual(s["e4_explorer_median_settled"], 0.21, delta=0.005)   # "about 0.21"

    def test_e5(self):
        s = self.s
        # The entry says the one exception "is in August"; it is the window ending 2026-09-17.
        self.assertEqual((s["e5_pass"], s["e5_miss"]), (91, [("2026-09-17", 1.29)]))
        # The entry says 1.35 to 2.48 bp; the recomputed maximum is 2.4749 bp (window ending 2026-11-02), which rounds to 2.47.
        self.assertEqual((s["e5_settled_min_bp"], s["e5_settled_max_bp"], s["e5_bp_to_cutoff"]), (1.35, 2.47, 2.3))
        self.assertEqual((s["e5_usd_1103"], s["e5_usd_1104"]), (9017, 7671))
        self.assertEqual(s["escrow_bp_1020_1104"], (7.13, 8.08))


if __name__ == "__main__":
    unittest.main()
