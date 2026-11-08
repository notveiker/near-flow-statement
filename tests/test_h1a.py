"""Offline tests for pipeline/h1a.py: internal consistency of the committed epoch evidence, and the published
H1a / rating numbers (frozen 2026-11-06; a change here means the committed raw data changed).

Run: make test
"""
from __future__ import annotations

import math
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

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


class RatingRule(unittest.TestCase):
    """PREREG, "Rating rule": Buy if G_obs >= G_req and H1b passes; Avoid if G_obs < G_req / 2 and H1b fails; Hold otherwise.

    G_req is 32.0 here so that G_req / 2 = 16.0 is exact in binary floating point and the equality cases are exact."""

    INCONCLUSIVE = "inconclusive (upper bound exceeds any plausible gross issuance)"
    # (H1b verdict, G_obs, G_req, rating): written out, not computed, so that a change of the rule shows up as a diff.
    TABLE = (
        ("pass", 320.0, 32.0, "Buy"), ("pass", 32.5, 32.0, "Buy"),
        ("pass", 32.0, 32.0, "Buy"),                                   # G_obs == G_req: Buy needs >=
        ("pass", math.nextafter(32.0, 0), 32.0, "Hold"),               # the smallest step below G_req
        ("pass", 24.0, 32.0, "Hold"), ("pass", 16.0, 32.0, "Hold"), ("pass", 0.0, 32.0, "Hold"),
        ("pass", -0.9, 32.0, "Hold"),                                  # a pass never gives Avoid, however low G_obs is
        ("fail", 320.0, 32.0, "Hold"), ("fail", 32.0, 32.0, "Hold"), ("fail", 24.0, 32.0, "Hold"),
        ("fail", math.nextafter(16.0, 32.0), 32.0, "Hold"),
        ("fail", 16.0, 32.0, "Hold"),                                  # G_obs == G_req / 2: Avoid needs <
        ("fail", math.nextafter(16.0, 0), 32.0, "Avoid"),              # the smallest step below G_req / 2
        ("fail", 8.0, 32.0, "Avoid"), ("fail", 0.0, 32.0, "Avoid"), ("fail", -0.9, 32.0, "Avoid"),
        ("fail", 10.7, 32.0, "Avoid"),                                 # between G_req / 3 and G_req / 2: not a divisor of 3
        ("inconclusive", 320.0, 32.0, "Hold"), ("inconclusive", 0.0, 32.0, "Hold"), ("inconclusive", 16.0, 32.0, "Hold"),
        (INCONCLUSIVE, 320.0, 32.0, "Hold"), (INCONCLUSIVE, 0.0, 32.0, "Hold"),
        ("pending", 320.0, 32.0, "Hold"), ("pending", 0.0, 32.0, "Hold"),
    )

    def test_every_h1b_outcome_against_g_obs_relative_to_g_req_and_half_of_it(self):
        for verdict, go, gr, want in self.TABLE:
            with self.subTest(h1b=verdict, g_obs=go, g_req=gr):
                self.assertEqual(H.rating_rule(verdict, go, gr), want)

    def test_the_table_reaches_every_branch(self):
        self.assertEqual({row[3] for row in self.TABLE}, {"Buy", "Avoid", "Hold"})

    def test_avoid_needs_the_h1b_verdict_to_fail(self):
        """Below 50% label coverage H1b is 'pass' or 'inconclusive' (tests/test_h1b.py), so Avoid cannot happen there."""
        for verdict in ("pass", "inconclusive", self.INCONCLUSIVE, "pending"):
            for go in (-0.99, 0.0, 1.0, 15.99, 100.0):
                self.assertNotEqual(H.rating_rule(verdict, go, 32.0), "Avoid", (verdict, go))

    def test_the_constants_the_rule_uses(self):
        self.assertEqual((H.AVOID_DIVISOR, H.H1A_PASS_BELOW_X, H.STAKING_REWARD_SHARE), (2, 0.5, 0.9))


class RatingAppliesTheRuleToTheData(unittest.TestCase):
    """rating() applies the rule to G_obs computed from the committed revenue series, with a forced G_req."""

    @staticmethod
    def observed_growth() -> float:
        """G_obs as PREREG defines it, computed here without pipeline code: annualised growth of captured revenue over
        the last 180 days against the 180 days before (the series is DefiLlama's near-intents dailyRevenue)."""
        ra = read_raw("rpc/rating_assumptions.json")
        assert (ra["g_obs_days"], ra["asof"]) == (180, "2026-11-04")
        by_day = {datetime.fromtimestamp(t, tz=timezone.utc).date(): float(v)
                  for t, v in read_raw("llama/dailyRevenue_near-intents.json")["totalDataChart"]}
        asof = date.fromisoformat(ra["asof"])
        last = sum(by_day[asof - timedelta(days=i)] for i in range(180))
        before = sum(by_day[asof - timedelta(days=i)] for i in range(180, 360))
        return (last / before) ** (365 / 180) - 1

    def rating_with(self, g_req: float, verdict: str) -> str:
        m = {"h1b_verdict": verdict}
        with mock.patch.object(H, "g_req", lambda *a, **k: g_req):
            H.rating(m)
        return m["rating_output"]

    def test_g_obs_is_the_committed_619_percent(self):
        self.assertEqual(round(self.observed_growth() * 100, 1), 619.0)

    def test_the_g_req_line_decides_buy(self):
        go = self.observed_growth()
        self.assertEqual(self.rating_with(go * 0.999999, "pass"), "Buy")     # G_obs a hair above G_req
        self.assertEqual(self.rating_with(go * 1.000001, "pass"), "Hold")    # a hair below
        self.assertEqual(self.rating_with(go * 1.000001, "fail"), "Hold")

    def test_the_half_g_req_line_decides_avoid(self):
        go = self.observed_growth()
        self.assertEqual(self.rating_with(go * 2.000002, "fail"), "Avoid")   # G_req / 2 a hair above G_obs
        self.assertEqual(self.rating_with(go * 1.999998, "fail"), "Hold")    # a hair below
        self.assertEqual(self.rating_with(go * 2.000002, "pass"), "Hold")
        self.assertEqual(self.rating_with(go * 2.000002, "inconclusive"), "Hold")


class H1aThreshold(unittest.TestCase):
    """H1a as written: every measure of net staking outflow is below 50% of staking rewards, strictly; staking rewards
    are 90% of gross issuance. h1a() reads two measures (daily flows, archival endpoints) once the archival file exists."""

    GROSS = 1_000_000.0                       # gross issuance of the synthetic window, NEAR
    REWARDS = 0.9 * GROSS
    LIMIT = 0.5 * REWARDS                     # 450,000.0: H1a passes below this

    @staticmethod
    def below(x: float) -> float:
        return math.nextafter(x, 0.0)

    @staticmethod
    def above(x: float) -> float:
        return math.nextafter(x, math.inf)

    def fake_raw(self, outflow: float, endpoint_outflow: float):
        """read_raw stand-in: daily flows with net outflow `outflow`; pools whose balance did not change, so the
        archival measure (rewards credited minus the change in pool balances) equals `endpoint_outflow`."""
        data = {
            "bq/staking_flows_daily.json": [{"rewards_near": endpoint_outflow, "gas_rebate_near": 0.0,
                                             "inflow_near": 0.0, "outflow_near": outflow}],
            "rpc/pool_endpoints_archival.json": {"pools": {"a.pool.near": ["0", "0"]},
                                                  "lst_pool": {"native_in_near": 0.0, "native_out_near": 0.0},
                                                  "flipside_check": {"amount_locked": [["0", "0"], ["0", "0"]]}},
            "bq/staking_pool_totals_endpoints.json": [{"block_date": "2026-11-04", "pool_total_near": "0"},
                                                      {"block_date": "2026-08-06", "pool_total_near": "0"}],
        }
        return lambda rel: data[rel]

    def run_h1a(self, outflow: float, endpoint_outflow: float | None = None) -> dict:
        """Metrics from h1a(). With endpoint_outflow=None the archival file is absent, so only the daily flows count."""
        m: dict = {}
        issuance = {"gross": self.GROSS, "net": 0.99 * self.GROSS, "burn": 0.01 * self.GROSS, "n_epochs": 297}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(H, "issuance", lambda: issuance):
            raw = Path(tmp)
            (raw / "rpc").mkdir()
            (raw / "rpc" / "epoch_issuance.json").write_text("{}\n", encoding="utf-8")
            if endpoint_outflow is not None:
                (raw / "rpc" / "pool_endpoints_archival.json").write_text("{}\n", encoding="utf-8")
            with mock.patch.object(H, "RAW", raw), mock.patch.object(
                    H, "read_raw", self.fake_raw(outflow, 0.0 if endpoint_outflow is None else endpoint_outflow)):
                H.h1a(m)
        return m

    def test_staking_rewards_are_90_percent_of_gross_issuance(self):
        m = self.run_h1a(self.LIMIT)
        self.assertEqual(m["h1a_gross_issuance_90d_m"], 1.0)
        self.assertEqual(m["h1a_staking_rewards_90d_m"], 0.9)

    def test_one_measure_net_outflow_just_below_at_and_just_above_half_the_rewards(self):
        for outflow, passes in ((self.below(self.LIMIT), True), (self.LIMIT, False), (self.above(self.LIMIT), False),
                                (0.0, True), (-1000.0, True), (self.REWARDS, False)):
            with self.subTest(outflow=outflow):
                self.assertIs(self.run_h1a(outflow)["h1a_pass_as_written"], passes)

    def test_two_measures_both_must_be_below_half_the_rewards(self):
        low, at, high = self.below(self.LIMIT), self.LIMIT, self.above(self.LIMIT)
        for flows, endpoints, passes in ((low, low, True), (at, low, False), (high, low, False),
                                         (low, at, False), (low, high, False), (at, at, False)):
            with self.subTest(daily_flows=flows, endpoints=endpoints):
                m = self.run_h1a(flows, endpoints)
                self.assertIs(m["h1a_pass_as_written"], passes)
                self.assertEqual(m["h1a_ratio_as_written_x"], round(flows / self.REWARDS, 2))
                self.assertEqual(m["h1a_ratio_endpoint_archival_x"], round(endpoints / self.REWARDS, 2))

    def test_the_committed_data_fail_it_with_a_ratio_far_above_half(self):
        m: dict = {}
        H.h1a(m)
        self.assertIs(m["h1a_pass_as_written"], False)
        self.assertGreater(m["h1a_ratio_as_written_x"], 0.5)
        self.assertGreater(m["h1a_ratio_endpoint_archival_x"], 0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
