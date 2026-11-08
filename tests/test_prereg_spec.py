"""Spec lock: the pre-registered numbers in the code equal the FROZEN text of PREREG.md.

PREREG.md is read here and never edited (git tag prereg-freeze; tests/test_integrity.py pins its SHA-256). Each constant
that the code uses for a hypothesis, a forward test or the rating rule is extracted from the frozen text with a regular
expression and compared with the code, and the comparison operators (strict or inclusive) are pinned at the boundary.
Where pipeline/render.py keeps its own copy of a constant (render.CONSTS, which the dashboard prints) it is compared
with the module that owns it. Before this file, moving F1_BAND, F3_MAX_BP, F4_MIN_PCT, COVERAGE_MIN_PCT or the H1a 0.5
was caught only by side effects in the dashboard tests, and the H1a 0.5 not at all.

Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import math
import re
import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import fetch_issuance as FI  # noqa: E402
from pipeline import h1a as A  # noqa: E402
from pipeline import h1b as B  # noqa: E402
from pipeline import render as R  # noqa: E402
from pipeline import score_forward as sf  # noqa: E402
from pipeline.common import read_raw  # noqa: E402

PREREG = (ROOT / "PREREG.md").read_text(encoding="utf-8")
UTC = timezone.utc
SCALE = {"K": Decimal(1000), "M": Decimal(1_000_000)}


def find(pattern: str) -> re.Match[str]:
    """The one match of `pattern` in the frozen text; the test fails, naming the pattern, if the text has changed."""
    found = list(re.finditer(pattern, PREREG))
    if len(found) != 1:
        raise AssertionError(f"PREREG.md: expected exactly one match of {pattern!r}, found {len(found)}")
    return found[0]


def band(row: str, unit: str) -> tuple[float, float]:
    """The [lo, hi] band of a forward-test row, e.g. **[2.21M, 2.40M] NEAR** -> (2210000.0, 2400000.0)."""
    m = find(rf"\|\s*{row}\s*\|[^\n]*?\*\*\[([\d.]+)([KM]), ([\d.]+)([KM])\] {unit}\*\*")
    return float(Decimal(m.group(1)) * SCALE[m.group(2)]), float(Decimal(m.group(3)) * SCALE[m.group(4)])


class FrozenTextIsWhatTheseTestsRead(unittest.TestCase):
    def test_the_sentences_the_patterns_below_depend_on_are_there(self):
        # If PREREG.md could change, these would fail first and name the sentence.
        for sentence in ("Net staking outflow < 50% of staking rewards", "Net exchange inflow < gross issuance (90d)",
                         "Identified buying ÷ net exchange inflow ≥ 25%", "If labelled coverage is below 50%",
                         "A test passes only if it passes under both bounds. Otherwise it is \"inconclusive\".",
                         "**Buy:** G_obs ≥ G_req, and H1b passes.", "**Avoid:** G_obs < G_req / 2, and H1b fails.",
                         "**Hold:** anything else."):
            self.assertIn(sentence, PREREG)


class HypothesisConstants(unittest.TestCase):
    def test_h1a_pass_below_half_of_staking_rewards(self):
        pct = Decimal(find(r"Net staking outflow < (\d+)% of staking rewards").group(1))
        self.assertEqual(A.H1A_PASS_BELOW_X, float(pct / 100))
        self.assertEqual(A.H1A_PASS_BELOW_X, 0.5)

    def test_staking_rewards_are_90_percent_of_gross_issuance(self):
        pct = Decimal(find(r"\*Staking rewards:\*\s+(\d+)% of gross issuance").group(1))
        self.assertEqual(A.STAKING_REWARD_SHARE, float(pct / 100))

    def test_h1c_needs_25_percent_inclusive(self):
        pct = Decimal(find(r"Identified buying ÷ net exchange inflow ≥ (\d+)%").group(1))
        self.assertEqual(B.H1C_MIN, pct / 100)
        self.assertEqual(B.H1C_MIN, Decimal("0.25"))

    def test_label_coverage_threshold_is_50_percent(self):
        pct = float(find(r"If labelled coverage is below (\d+)%").group(1))
        self.assertEqual(B.COVERAGE_MIN_PCT, pct)

    def test_h1b_passes_when_inflow_is_below_issuance_and_below_fifty_percent_coverage_needs_both_bounds(self):
        find(r"Net exchange inflow < gross issuance \(90d\)")
        find(r"below 50%, H1b and H1c are reported as ranges, with the unlabelled share assumed to be 0% or 100% exchange-bound")
        # strict < for H1b, both bounds below 50% coverage, the lower bound otherwise: pinned at the boundary in test_h1b.py
        self.assertEqual(B._both(True, True, 49.99), "pass")
        self.assertEqual(B._both(True, False, 49.99), "inconclusive")

    def test_identified_buying_is_the_buyback_wallet_over_the_h1a_window(self):
        find(r"\*Identified buying:\* the NEAR balance increase of `buybacks\.multisignature\.near` over the window")
        self.assertEqual(sf.BUYBACK, "buybacks.multisignature.near")
        self.assertEqual(set(read_raw("rpc/buyback_balance_endpoints.json")["blocks"]), {A.B0, A.B1})


class H1aWindow(unittest.TestCase):
    """PREREG: 'over the 90 days 2026-08-07 → 2026-11-04 inclusive'. The code works in block heights."""

    def test_the_window_dates_in_the_frozen_text(self):
        m = find(r"over the 90 days (\d{4}-\d{2}-\d{2}) → (\d{4}-\d{2}-\d{2}) inclusive")
        self.assertEqual((m.group(1), m.group(2)), ("2026-08-07", "2026-11-04"))
        self.assertEqual((datetime(2026, 11, 4) - datetime(2026, 8, 7)).days + 1, 90)

    def test_the_block_heights_are_the_first_and_last_block_of_those_days(self):
        d = read_raw("rpc/epoch_issuance.json")
        before, last = d["endpoints"][A.B0], d["endpoints"][A.B1]
        self.assertEqual((int(A.B0), int(A.B1)), (A.W_FIRST - 1, A.W_LAST))

        def utc(ns: str) -> datetime:
            return datetime.fromtimestamp(int(ns) / 1e9, tz=UTC)

        # the block before the window is in the last minute of 2026-08-06, the last block in the last minute of 2026-11-04
        self.assertTrue(datetime(2026, 8, 6, 23, 59, tzinfo=UTC) <= utc(before["timestamp_nanosec"]) < datetime(2026, 8, 7, tzinfo=UTC))
        self.assertTrue(datetime(2026, 11, 4, 23, 59, tzinfo=UTC) <= utc(last["timestamp_nanosec"]) < datetime(2026, 11, 5, tzinfo=UTC))
        self.assertEqual((d["window"]["first_block"], d["window"]["last_block"]), (A.W_FIRST, A.W_LAST))
        self.assertEqual((d["window"]["start_utc"], d["window"]["end_utc"]), ("2026-08-07T00:00:00Z", "2026-11-05T00:00:00Z"))

    def test_the_fetcher_uses_the_same_window(self):
        self.assertEqual((FI.WINDOW_FIRST, FI.WINDOW_LAST), (A.W_FIRST, A.W_LAST))
        self.assertEqual(FI.ENDPOINTS, (A.W_FIRST - 1, A.W_LAST))


class ForwardTestConstants(unittest.TestCase):
    def test_f1_and_f2_bands(self):
        self.assertEqual(sf.F1_BAND, band("F1", "NEAR"))
        self.assertEqual(sf.F1_BAND, (2_210_000.0, 2_400_000.0))
        self.assertEqual(sf.F2_BAND, band("F2", "NEAR/day"))
        self.assertEqual(sf.F2_BAND, (86_000.0, 89_500.0))

    def test_f3_is_below_4_bp_and_f4_is_at_least_50_percent(self):
        self.assertEqual(sf.F3_MAX_BP, float(find(r"\*\*below ([\d.]+) bp\*\*").group(1)))
        self.assertEqual(sf.F4_MIN_PCT, float(find(r"\*\*≥ ([\d.]+)%\*\*").group(1)))
        self.assertEqual((sf.F3_MAX_BP, sf.F4_MIN_PCT), (4.0, 50.0))

    def test_scoring_opens_at_2026_11_14_00_00_utc(self):
        """The date is written out here, not read from the module, so moving the module's constant cannot also move this."""
        for pattern in (r"fetched on or after (\d{4}-\d{2}-\d{2})", r"first final RPC block after (\d{4}-\d{2}-\d{2}) 00:00 UTC"):
            self.assertEqual(find(pattern).group(1), "2026-11-14")
        self.assertEqual(sf.SCORE_NOT_BEFORE, datetime(2026, 11, 14, 0, 0, 0, tzinfo=UTC))
        self.assertEqual(sf.F1_T, datetime(2026, 11, 14, 0, 0, 0, tzinfo=UTC))
        self.assertEqual(sf.iso(sf.SCORE_NOT_BEFORE), "2026-11-14T00:00:00Z")

    def test_the_window_is_2026_11_06_to_2026_11_13(self):
        m = find(r"\*\*Window:\*\* (\d{4}-\d{2}-\d{2}) 00:00 UTC → (\d{4}-\d{2}-\d{2}) 23:59 UTC")
        self.assertEqual(sf.WINDOW, (m.group(1), m.group(2)))
        self.assertEqual(sf.WINDOW, ("2026-11-06", "2026-11-13"))
        self.assertEqual(find(r"daily deltas for (\d{4}-\d{2}-\d{2}) → (\d{4}-\d{2}-\d{2})").groups(), sf.WINDOW)
        self.assertEqual(len(sf.days_between(*sf.WINDOW)), 8)

    def test_the_peer_set_is_the_four_venues_named_in_the_text(self):
        sentence = find(r"Intents share of the native cross-chain peer set \(([^)]*)\)").group(1)
        self.assertEqual(sf.PEERS, ["near-intents", "thorchain-dex", "chainflip-amm", "maya-protocol"])
        for word in ("Intents", "THORChain", "Chainflip", "Maya"):
            self.assertIn(word, sentence)

    def test_scoring_rules_are_not_estimated_and_published(self):
        find(r"A forward test with missing data is scored \"not scorable\"\. It is never estimated\.")
        self.assertEqual(sf.NOT_SCORABLE, "not scorable")


def llama(per_day: dict[str, float], fetched_at: str = "2026-11-14T06:00:00Z") -> dict:
    rows = [[int(datetime.fromisoformat(d).replace(tzinfo=UTC).timestamp()), v] for d, v in per_day.items()]
    return {"url": "synthetic", "fetched_at": fetched_at, "data": {"totalDataChart": rows}}


def snapshot(*, revenue: float = 0.0, volumes: dict[str, float] | None = None, supply_step: float | None = None,
             balance_near: int | None = None) -> dict:
    """A synthetic snapshot for the real window 2026-11-06..2026-11-13, fetched after 2026-11-14 00:00 UTC."""
    days = sf.days_between(*sf.WINDOW)
    vols = volumes or {p: 1e9 for p in sf.PEERS}
    sources: dict = {f"llama_volume_{p}": llama({d: vols[p] for d in days}) for p in sf.PEERS}
    sources["llama_revenue_near-intents"] = llama({d: revenue for d in days})
    base = 1_000_000_000                                 # NEAR; integers below 2**53, so the daily deltas are exact
    step = 86_000 if supply_step is None else supply_step
    rows = [{"date": f"{sf.days_between('2026-11-05', '2026-11-13')[k]}T00:00:00.000Z",
             "total_supply": str(int((base + k * step) * sf.YOCTO))} for k in range(9)]
    sources["nearblocks_charts"] = {"url": "synthetic", "fetched_at": "2026-11-14T06:00:00Z", "data": {"charts": rows}}
    amount = 2_300_000 if balance_near is None else balance_near
    sources["rpc_f1"] = {"url": "synthetic", "fetched_at": "2026-11-14T06:00:00Z", "data": {
        "target_utc": "2026-11-14T00:00:00Z", "block_height": 1, "block_hash": "h", "block_timestamp_ns": 0,
        "view_account": {"amount": str(amount * sf.YOCTO), "locked": "0"}}}
    return {"fetched_at": "2026-11-14T06:00:00Z", "sources": sources, "errors": {}}


def result(snap: dict, test: str) -> str:
    return sf.score(snap, sf.WINDOW, sf.SCORE_NOT_BEFORE)[test]["result"]


class ForwardTestComparators(unittest.TestCase):
    """The pre-registered bands are inclusive, 'below 4.0 bp' is strict, '≥ 50%' is inclusive. Pinned on the real score()."""

    def test_f1_band_edges_are_inside_and_one_near_beyond_is_outside(self):
        for near, want in ((2_210_000, "PASS"), (2_209_999, "MISS"), (2_400_000, "PASS"), (2_400_001, "MISS"), (2_300_000, "PASS")):
            with self.subTest(balance_near=near):
                self.assertEqual(result(snapshot(balance_near=near), "F1"), want)

    def test_f2_band_edges_are_inside_and_one_near_beyond_is_outside(self):
        for step, want in ((86_000, "PASS"), (85_999, "MISS"), (89_500, "PASS"), (89_501, "MISS"), (88_295, "PASS")):
            with self.subTest(mean_net_increase_per_day=step):
                snap = snapshot(supply_step=step)
                self.assertEqual(result(snap, "F2"), want)
                self.assertEqual(sf.score(snap, sf.WINDOW, sf.SCORE_NOT_BEFORE)["F2"]["n_deltas"], 8)

    def test_f2_needs_the_nearblocks_row_of_the_day_before_the_window_and_every_day_in_it(self):
        for day in ("2026-11-05", "2026-11-06", "2026-11-13"):
            with self.subTest(missing=day):
                snap = snapshot()
                charts = snap["sources"]["nearblocks_charts"]["data"]["charts"]
                snap["sources"]["nearblocks_charts"]["data"]["charts"] = [r for r in charts if not r["date"].startswith(day)]
                res = sf.score(snap, sf.WINDOW, sf.SCORE_NOT_BEFORE)["F2"]
                self.assertEqual(res["result"], sf.NOT_SCORABLE)
                self.assertIn(day, res["why"])

    def test_f3_is_below_4_bp_with_the_real_threshold(self):
        # revenue per day over a volume of $1B a day: 399,000 is 3.99 bp, 401,000 is 4.01 bp
        self.assertEqual(result(snapshot(revenue=399_000.0), "F3"), "PASS")
        self.assertEqual(result(snapshot(revenue=401_000.0), "F3"), "MISS")

    def test_f3_exactly_at_the_threshold_misses_because_it_is_strictly_below(self):
        snap = snapshot(revenue=400_000.0)
        res = sf.score(snap, sf.WINDOW, sf.SCORE_NOT_BEFORE)["F3"]
        bp = res["take_rate_bp"]
        with mock.patch.object(sf, "F3_MAX_BP", bp):                       # threshold equal to the measured rate, to the bit
            self.assertEqual(result(snap, "F3"), "MISS")
        with mock.patch.object(sf, "F3_MAX_BP", math.nextafter(bp, math.inf)):
            self.assertEqual(result(snap, "F3"), "PASS")

    def test_f4_is_at_least_50_percent_inclusive(self):
        even = {"near-intents": 1e9, "thorchain-dex": 1e9, "chainflip-amm": 0.0, "maya-protocol": 0.0}
        self.assertEqual(result(snapshot(volumes=even), "F4"), "PASS")                    # exactly 50.0%
        self.assertEqual(sf.score(snapshot(volumes=even), sf.WINDOW, sf.SCORE_NOT_BEFORE)["F4"]["intents_share_pct"], 50.0)
        below = {**even, "near-intents": 1e9 - 1000}
        self.assertEqual(result(snapshot(volumes=below), "F4"), "MISS")
        above = {**even, "near-intents": 1e9 + 1000}
        self.assertEqual(result(snapshot(volumes=above), "F4"), "PASS")


class RenderKeepsTheSameConstants(unittest.TestCase):
    """The dashboard prints these from render.CONSTS (its own copy). It must be the number the code uses."""

    def test_consts_equal_the_modules_that_own_them(self):
        c = {k: v[0] for k, v in R.CONSTS.items()}
        self.assertEqual(c["h1a_pass_below_x"], A.H1A_PASS_BELOW_X)
        self.assertAlmostEqual(c["staking_rewards_share_pct"], A.STAKING_REWARD_SHARE * 100, places=9)
        self.assertEqual(c["h1b_coverage_min_pct"], B.COVERAGE_MIN_PCT)
        self.assertEqual(c["h1c_min_pct"], float(B.H1C_MIN) * 100)
        self.assertEqual((c["f1_lo"], c["f1_hi"]), sf.F1_BAND)
        self.assertEqual((c["f2_lo"], c["f2_hi"]), sf.F2_BAND)
        self.assertEqual(c["f3_max_bp"], sf.F3_MAX_BP)
        self.assertEqual(c["f4_min_pct"], sf.F4_MIN_PCT)

    def test_consts_still_has_every_entry_compared_above(self):
        """(tests/test_render.py pins the exact set of keys; this only guards the ones compared here against a rename.)"""
        self.assertLessEqual({"h1a_pass_below_x", "staking_rewards_share_pct", "h1b_coverage_min_pct", "h1c_min_pct",
                              "f1_lo", "f1_hi", "f2_lo", "f2_hi", "f3_max_bp", "f4_min_pct"}, set(R.CONSTS))


class RatingRuleConstants(unittest.TestCase):
    def test_the_three_branches_are_written_as_in_the_frozen_text(self):
        find(r"\*\*Buy:\*\* G_obs ≥ G_req, and H1b passes\.")
        divisor = int(find(r"\*\*Avoid:\*\* G_obs < G_req / (\d+), and H1b fails\.").group(1))
        find(r"\*\*Hold:\*\* anything else\.")
        self.assertEqual(A.AVOID_DIVISOR, divisor)
        # Buy is inclusive of G_req, Avoid is strictly below G_req / 2, anything else is Hold (all three outcomes exist)
        self.assertEqual(A.rating_rule("pass", 1.0, 1.0), "Buy")
        self.assertEqual(A.rating_rule("fail", 0.5, 1.0), "Hold")
        self.assertEqual(A.rating_rule("fail", math.nextafter(0.5, 0), 1.0), "Avoid")

    def test_the_rating_inputs_follow_the_frozen_text(self):
        ra = read_raw("rpc/rating_assumptions.json")
        m = find(r"annual growth in captured Intents revenue needed .* by (\d{4}-\d{2}-\d{2})\.")
        self.assertEqual(ra["target_date"], m.group(1))
        m = find(r"ramp to ([\d.]+)% after the (\d+)-day grace period, a constant price, and starts from the last (\d+) days")
        self.assertEqual(ra["hsp029"]["target_cap"], float(Decimal(m.group(1)) / 100))
        self.assertEqual(ra["hsp029"]["grace_days"], int(m.group(2)))
        self.assertEqual(ra["r90_days"], int(m.group(3)))
        m = find(r"annualized growth of captured revenue over the last (\d+) days vs the (\d+) days before")
        self.assertEqual(ra["g_obs_days"], int(m.group(1)))
        self.assertEqual(int(m.group(1)), int(m.group(2)))
        self.assertEqual(ra["asof"], "2026-11-04")                     # the last day of the H1a window


if __name__ == "__main__":
    unittest.main(verbosity=2)
