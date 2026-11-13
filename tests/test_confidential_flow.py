"""docs/confidential-flow.md (exploratory, 2026-11-13): the committed queries read no day after 2026-11-04, and the
figures the write-up states as findings still hold on the committed data."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "data" / "metrics.json").read_text(encoding="utf-8"))


class Queries(unittest.TestCase):
    def test_no_query_reads_a_day_after_the_cutoff(self):
        for name in ("confidential_treasury_daily.sql", "confidential_solver_blocks.sql"):
            sql = (ROOT / "sql" / name).read_text(encoding="utf-8")
            body = "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))
            days = re.findall(r"'(20\d\d-\d\d-\d\d)'", body)
            self.assertTrue(days, name)
            self.assertLessEqual(max(days), "2026-11-04", name)

    def test_the_outputs_hold_no_day_after_the_cutoff(self):
        for name in ("confidential_treasury_daily.json", "confidential_solver_blocks.json"):
            rows = json.loads((ROOT / "data" / "raw" / "bq" / name).read_text(encoding="utf-8"))
            self.assertLessEqual(max(r["day"] for r in rows), "2026-11-04", name)


class Findings(unittest.TestCase):
    def test_solver_shields_pair_with_unshields_of_another_token(self):
        for tag in ("0902", "1008", "1022"):
            self.assertGreaterEqual(M[f"conf_{tag}_paired_3pct_pct"], 70.0, tag)
            self.assertGreaterEqual(M[f"conf_{tag}_paired_other_token_pct"], 99.0, tag)
            self.assertLessEqual(M[f"conf_{tag}_paired_gap_median_blocks"], 10, tag)

    def test_releases_track_confidential_volume_more_than_public_volume(self):
        for kind in ("", "_detrended", "_dlog"):
            self.assertGreater(M[f"conf_rel_corr_solver{kind}"], M[f"conf_rel_corr_oneclick{kind}"] + 0.3, kind)
        self.assertGreater(M["conf_rel_corr_solver"], max(M["conf_rel_corr_solver_lag1"], M["conf_rel_corr_solver_lead1"]))

    def test_reading_3_lies_near_the_halved_basis_and_between_the_other_two(self):
        lo, hi = M["legcount_k_solver_window_lo"], M["legcount_k_solver_window_hi"]
        self.assertTrue(M["legcount_k_window_hi"] < lo <= hi < M["legcount_k_public_window_lo"])
        self.assertTrue(1.7 <= lo <= hi <= 2.0)

    def test_the_daily_query_reproduces_the_leg_count_treasury_totals(self):
        for tag in ("0818", "0831", "0902", "1008", "1022"):
            self.assertEqual(M[f"legcount_{tag}_daily_query_over_leg_query_pct"], 100.0, tag)


if __name__ == "__main__":
    unittest.main()
