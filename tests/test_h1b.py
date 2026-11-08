"""Offline tests for the H1b / H1c decision rule in pipeline/h1b.py, which the unit tests did not cover at all before.

The rule is frozen in PREREG.md ("Hypotheses on flows"), with the reading of the below-50% case in PREREG-ADDENDUM.md
(2026-11-06 23:11 UTC, item 6):

  H1b passes if net exchange inflow < gross issuance (90 days). H1c passes if identified buying / net exchange inflow
  >= 25%. If labelled coverage is below 50%, each test is reported as a range: it passes only if it passes under both
  bounds (the unlabelled share assumed 0% or 100% exchange-bound), otherwise it is "inconclusive". With coverage of 50%
  or more the lower bound is the point estimate: "pass" or "fail". So below 50% coverage H1b and H1c can only be
  "pass" or "inconclusive", never "fail", which is why the rating rule's Avoid branch cannot be reached there.

The synthetic cases drive the real h1b(m) with pipeline.h1b.compute replaced by a stub that returns chosen bounds.
tests/test_prereg_spec.py checks the constants (COVERAGE_MIN_PCT, H1C_MIN) against the frozen text.

Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import itertools
import json
import sys
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import h1a as A  # noqa: E402
from pipeline import h1b as B  # noqa: E402

GROSS_M = 8.0                               # gross issuance in the synthetic cases, million NEAR
GROSS = Decimal("8000000")
BUYING = Decimal("1000000")                 # identified buying, NEAR
COMBOS = list(itertools.product((True, False), repeat=2))


def stub(lower, upper, *, buying=BUYING, coverage=20, inflow_coverage="0.246"):
    """What h1b.compute() returns, with the pieces h1b() reads, for chosen lower and upper bounds of net inflow."""
    d = Decimal
    return {"coverage_count": d(coverage), "coverage_tier1_count": d(10), "coverage_inflow": d(inflow_coverage),
            "coverage_tier1_inflow": d("0.202"), "native": {3: d(lower), 4: d(upper)}, "wnear": {3: d(0), 4: d(0)},
            "total": {1: d(lower), 2: d(lower), 3: d(lower), 4: d(upper)}, "upper_ex_nonexchange": d(upper),
            "buying": d(buying)}


def run(lower, upper, *, coverage, buying=BUYING, gross_m=GROSS_M, inflow_coverage="0.246") -> dict:
    m: dict = {} if gross_m is None else {"h1a_gross_issuance_90d_m": gross_m}
    with mock.patch.object(B, "compute", return_value=stub(lower, upper, buying=buying, coverage=coverage,
                                                           inflow_coverage=inflow_coverage)):
        B.h1b(m)
    return m


class BothBounds(unittest.TestCase):
    def test_below_the_coverage_threshold_a_test_passes_only_if_both_bounds_pass(self):
        want = {(True, True): "pass", (True, False): "inconclusive", (False, True): "inconclusive", (False, False): "inconclusive"}
        for coverage in (0.0, 10.0, 20.0, 49.0, 49.9, 49.999999):
            for (lower_ok, upper_ok), expected in want.items():
                with self.subTest(coverage=coverage, lower_ok=lower_ok, upper_ok=upper_ok):
                    self.assertEqual(B._both(lower_ok, upper_ok, coverage), expected)

    def test_at_or_above_the_threshold_the_lower_bound_is_the_point_estimate(self):
        for coverage in (50.0, 50.000001, 75.0, 100.0):
            for lower_ok, upper_ok in COMBOS:
                with self.subTest(coverage=coverage, lower_ok=lower_ok, upper_ok=upper_ok):
                    self.assertEqual(B._both(lower_ok, upper_ok, coverage), "pass" if lower_ok else "fail")

    def test_the_threshold_itself_counts_as_covered(self):
        """PREREG says 'below 50%' gives ranges, so exactly 50% is a point estimate."""
        self.assertEqual(B.COVERAGE_MIN_PCT, 50.0)
        self.assertEqual(B._both(True, False, 50.0), "pass")
        self.assertEqual(B._both(True, False, 49.99999999999999), "inconclusive")

    def test_below_the_threshold_the_verdict_is_never_fail(self):
        """This is why Avoid is unreachable at low coverage (PREREG-ADDENDUM 2026-11-06 23:11 UTC, item 6)."""
        seen = {B._both(lo, up, cov / 2) for cov in range(0, 100) for lo, up in COMBOS}   # coverage 0.0 .. 49.5
        self.assertEqual(seen, {"pass", "inconclusive"})
        at_or_above = {B._both(lo, up, 50 + cov / 2) for cov in range(0, 101) for lo, up in COMBOS}
        self.assertIn("fail", at_or_above, "the property above is not vacuous: fail exists once coverage is 50% or more")


class CoverageReading(unittest.TestCase):
    """PREREG: coverage is 'the share of the top-100 native-NEAR receivers by inflow that we were able to label'. The code
    reads it as the count of labelled accounts out of 100 (the inflow-weighted share is a side metric; PREREG-ADDENDUM
    2026-11-06 23:11 UTC, item 4). That reading decides whether a test is a range or a point estimate."""

    def test_the_count_share_decides_not_the_inflow_share(self):
        wide = run(GROSS - 1, GROSS * 50, coverage=60, inflow_coverage="0.10")     # 60 of 100 labelled, 10% of the inflow
        self.assertEqual(wide["h1b_verdict"], "pass")                              # a point estimate: coverage is enough
        narrow = run(GROSS - 1, GROSS * 50, coverage=40, inflow_coverage="0.90")   # 40 of 100 labelled, 90% of the inflow
        self.assertEqual(narrow["h1b_verdict"], "inconclusive")                    # still a range
        self.assertEqual((wide["h1b_coverage_count_pct"], wide["h1b_coverage_inflow_pct"]), (60.0, 10.0))

    def test_the_cited_labels_are_tiers_1_to_3_and_tier_1_alone_is_reported_beside_them(self):
        m = {"h1a_gross_issuance_90d_m": 8.0098}
        B.h1b(m)
        self.assertEqual((m["h1b_coverage_count_pct"], m["h1b_coverage_tier1_count_pct"]), (20.0, 10.0))


class H1bVerdict(unittest.TestCase):
    """H1b: net exchange inflow < gross issuance, strictly, for the lower bound (level 3) and the upper bound (level 4)."""

    def verdict(self, lower, upper, coverage) -> str:
        return run(lower, upper, coverage=coverage)["h1b_verdict"]

    def test_point_estimate_at_full_coverage_is_strictly_below_gross_issuance(self):
        for coverage in (50, 100):
            with self.subTest(coverage=coverage):
                self.assertEqual(self.verdict(GROSS - 1, GROSS * 50, coverage), "pass")
                self.assertEqual(self.verdict(GROSS, GROSS * 50, coverage), "fail", "equal to gross issuance is not below it")
                self.assertEqual(self.verdict(GROSS + 1, GROSS * 50, coverage), "fail")

    def test_the_upper_bound_does_not_matter_once_coverage_is_enough(self):
        self.assertEqual(self.verdict(GROSS - 1, GROSS * 50, 50), "pass")
        self.assertEqual(self.verdict(GROSS + 1, GROSS - 1, 50), "fail")

    def test_ranges_below_the_threshold_need_both_bounds_strictly_below_gross_issuance(self):
        self.assertEqual(self.verdict(GROSS - 2, GROSS - 1, 20), "pass")
        self.assertEqual(self.verdict(GROSS - 2, GROSS, 20), "inconclusive", "upper bound equal to gross issuance")
        self.assertEqual(self.verdict(GROSS, GROSS - 2, 20), "inconclusive", "lower bound equal to gross issuance")
        self.assertEqual(self.verdict(GROSS + 5, GROSS + 6, 20), "inconclusive", "both bounds above: still not 'fail'")
        self.assertEqual(self.verdict(GROSS + 5, GROSS - 6, 20), "inconclusive")

    def test_the_verdict_text_when_gross_issuance_is_missing(self):
        """No H1a metric: an upper bound beyond any plausible issuance at low coverage is inconclusive, else pending."""
        huge, small = B.PLAUSIBLE_G_MAX_NEAR + 1, B.PLAUSIBLE_G_MAX_NEAR - 1
        self.assertEqual(run(1, huge, coverage=20, gross_m=None)["h1b_verdict"],
                         "inconclusive (upper bound exceeds any plausible gross issuance)")
        self.assertEqual(run(1, small, coverage=20, gross_m=None)["h1b_verdict"], "pending")
        self.assertEqual(run(1, huge, coverage=50, gross_m=None)["h1b_verdict"], "pending")

    def test_every_verdict_string_h1b_can_write(self):
        """h1a.rating_rule reads the start of these strings, so a new or reworded verdict must be a deliberate change."""
        words = {run(lower, GROSS * 50, coverage=c, gross_m=g)["h1b_verdict"]
                 for lower in (1, GROSS + 1) for c in (20, 50) for g in (GROSS_M, None)}
        self.assertEqual(words, {"pass", "fail", "inconclusive", "pending",
                                 "inconclusive (upper bound exceeds any plausible gross issuance)"})


class H1cVerdict(unittest.TestCase):
    """H1c: identified buying / net exchange inflow >= 25% (inclusive); a net inflow of zero or less cannot pass."""

    def verdict(self, lower, upper, coverage, buying=BUYING) -> str:
        return run(lower, upper, coverage=coverage, buying=buying)["h1c_verdict"]

    def test_exactly_25_percent_passes_and_just_below_fails(self):
        self.assertEqual(B.H1C_MIN, Decimal("0.25"))
        net = BUYING * 4                                    # buying / net = 0.25 exactly
        for coverage in (50, 100):
            with self.subTest(coverage=coverage):
                self.assertEqual(self.verdict(net, net * 9, coverage), "pass")
                self.assertEqual(self.verdict(net - 1, net * 9, coverage), "pass")
                self.assertEqual(self.verdict(net + 1, net * 9, coverage), "fail", "just below 25%")

    def test_the_ratio_metric_is_in_percent_of_the_same_quantity(self):
        m = run(BUYING * 4, BUYING * 8, coverage=20)
        self.assertEqual((m["h1c_ratio_lower_pct"], m["h1c_ratio_upper_pct"]), (25.0, 12.5))
        self.assertEqual(m["h1c_identified_buying_m"], 1.0)

    def test_ranges_below_the_threshold_need_both_bounds_at_25_percent_or_more(self):
        net = BUYING * 4
        self.assertEqual(self.verdict(net, net, 20), "pass")
        self.assertEqual(self.verdict(net - 1, net - 1, 20), "pass")
        self.assertEqual(self.verdict(net, net + 1, 20), "inconclusive")
        self.assertEqual(self.verdict(net + 1, net, 20), "inconclusive")
        self.assertEqual(self.verdict(net + 1, net + 1, 20), "inconclusive", "both bounds miss: still not 'fail'")

    def test_a_net_inflow_of_zero_or_less_cannot_pass(self):
        """Buying cannot be a share of an inflow that is not positive. An implementation choice, not PREREG text."""
        self.assertEqual(self.verdict(-1, BUYING * 4, 100), "fail")
        self.assertEqual(self.verdict(-1, -1, 20), "inconclusive")
        self.assertEqual(self.verdict(BUYING * 4, -5, 20), "inconclusive")
        self.assertEqual(self.verdict(-BUYING * 4, -BUYING * 4, 50), "fail")
        # a falling buyback balance over a falling exchange balance has a positive ratio (25%), which must not pass either
        self.assertEqual(self.verdict(-BUYING * 4, -BUYING * 4, 100, buying=-BUYING), "fail")

    def test_h1b_and_h1c_are_judged_independently(self):
        m = run(GROSS - 1, GROSS - 1, coverage=100, buying=BUYING)   # inflow below gross; buying is 12.5% of it: H1c fails
        self.assertEqual((m["h1b_verdict"], m["h1c_verdict"]), ("pass", "fail"))


class AvoidIsUnreachableAtLowCoverage(unittest.TestCase):
    def test_no_verdict_h1b_can_give_below_50_percent_coverage_lets_the_rule_output_avoid(self):
        reachable = {run(lo, up, coverage=cov)["h1b_verdict"]
                     for cov in (0, 20, 49) for lo in (GROSS - 1, GROSS + 1) for up in (GROSS - 1, GROSS + 1)}
        self.assertEqual(reachable, {"pass", "inconclusive"})
        for verdict in reachable:
            for gr in (1.0, 33.2, 1e6):
                for go in (-0.99, 0.0, gr / 2 - 1e-9, gr / 2, gr, gr * 20, 1e9):
                    self.assertNotEqual(A.rating_rule(verdict, go, gr), "Avoid", (verdict, go, gr))


class CommittedInputs(unittest.TestCase):
    """The real committed BigQuery outputs: 20% of the top-100 receivers are labelled, so both tests are ranges."""

    @classmethod
    def setUpClass(cls):
        cls.m = {"h1a_gross_issuance_90d_m": json.loads((ROOT / "data" / "metrics.json").read_text(encoding="utf-8"))
                 ["h1a_gross_issuance_90d_m"]}
        B.h1b(cls.m)
        cls.committed = json.loads((ROOT / "data" / "metrics.json").read_text(encoding="utf-8"))

    def test_both_tests_are_inconclusive_because_coverage_is_below_half(self):
        self.assertLess(self.m["h1b_coverage_count_pct"], B.COVERAGE_MIN_PCT)
        self.assertEqual((self.m["h1b_verdict"], self.m["h1c_verdict"]), ("inconclusive", "inconclusive"))

    def test_the_bounds_straddle_the_thresholds(self):
        gross_m = self.m["h1a_gross_issuance_90d_m"]
        self.assertLess(self.m["h1b_net_inflow_lower_m"], gross_m)       # the lower bound alone would pass H1b
        self.assertGreater(self.m["h1b_net_inflow_upper_m"], gross_m)    # the upper bound alone would fail it
        self.assertGreaterEqual(self.m["h1c_ratio_lower_pct"], 25.0)
        self.assertLess(self.m["h1c_ratio_upper_pct"], 25.0)

    def test_every_h1b_and_h1c_metric_equals_the_committed_one(self):
        keys = [k for k in self.m if k.startswith(("h1b_", "h1c_"))]
        self.assertGreater(len(keys), 15)
        for k in keys:
            self.assertEqual(self.m[k], self.committed[k], k)

    def test_the_rating_follows_from_them(self):
        m = {"h1b_verdict": self.m["h1b_verdict"]}
        A.rating(m)
        self.assertEqual(m["rating_output"], self.committed["rating_output"])
        self.assertEqual(m["rating_output"], "Hold")


if __name__ == "__main__":
    unittest.main(verbosity=2)
