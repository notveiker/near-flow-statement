"""The investment case (exploratory, 2026-11-14; pipeline/investment_case.py) recomputed from the committed raw files.

Each test rebuilds a published ic_* metric with its own arithmetic from data/raw/, not by calling the function that wrote it, and
compares it with data/metrics.json. The Monte Carlo's determinism is checked by running it twice."""
from __future__ import annotations

import json
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.common import YOCTO, read_raw  # noqa: E402

M = json.loads((ROOT / "data" / "metrics.json").read_text(encoding="utf-8"))
S = json.loads((ROOT / "data" / "series.json").read_text(encoding="utf-8"))
PEERS = ("near-intents", "thorchain-dex", "chainflip-amm", "maya-protocol")
ASOF = M["asof"]


def llama(rel: str) -> dict[str, float]:
    return {datetime.fromtimestamp(t, tz=timezone.utc).date().isoformat(): float(v) for t, v in read_raw(rel)["totalDataChart"]}


def days_back(end: str, n: int) -> list[str]:
    e = date.fromisoformat(end)
    return [(e - timedelta(days=i)).isoformat() for i in range(n)]


def wsum(series: dict[str, float], end: str, n: int) -> float:
    return sum(series.get(d, 0.0) for d in days_back(end, n))


REV = llama("llama/dailyRevenue_near-intents.json")
VOL = {s: llama(f"llama/volume_{s}.json") for s in PEERS}
FEES = {s: llama(f"llama/fees_{s}.json") for s in PEERS}


class ReverseDCF(unittest.TestCase):
    def test_every_grid_cell_is_the_formula(self):
        """required revenue in 2031 = market cap x (1 + r)^5 x supply factor / X; growth = (required / today's)^(1/5) - 1."""
        mcap = float(read_raw("coingecko/near_snapshot.json")["market_cap_usd"])
        rev0 = wsum(REV, ASOF, 90) * 365 / 90
        self.assertAlmostEqual(rev0 / 1e6, M["ic_rev_90d_ann_m"], delta=0.05)
        n = M["ic_years_n"]
        for r in (10, 15, 20):
            for x in (10, 25, 50):
                need = mcap * (1 + r / 100) ** n * M["ic_supply_factor_x"] / x
                got = ((need / rev0) ** (1 / n) - 1) * 100
                self.assertAlmostEqual(got, M[f"ic_implied_cagr_r{r}_x{x}_pct"], delta=0.15, msg=(r, x))   # the supply factor is published rounded

    def test_the_supply_factor_is_the_rating_rules_path(self):
        """The factor comes from the same daily path as G_req; G_req recomputed from that path must equal the published one."""
        from pipeline.h1a import issuance
        from pipeline.model import supply_path
        ra = read_raw("rpc/rating_assumptions.json")
        a0, t = date.fromisoformat(ra["asof"]), date.fromisoformat(ra["target_date"])
        path = supply_path(a0, t, True)
        self.assertAlmostEqual(path[t] / path[a0], M["ic_supply_factor_x"], places=3)
        self.assertAlmostEqual(path[a0], issuance()["supply_end"], places=6)
        n90 = path[t] - path[t - timedelta(days=90)]
        g = (n90 * ra["price_usd"] / wsum(REV, ASOF, 90)) ** (1 / ra["horizon_years"]) - 1
        self.assertAlmostEqual(g * 100, M["rating_g_req_pct"], delta=0.05)


class Market(unittest.TestCase):
    def test_annual_volumes_and_growth(self):
        ys = [sum(wsum(VOL[s], (date.fromisoformat(ASOF) - timedelta(days=365 * k)).isoformat(), 365) for s in PEERS) for k in range(5)]
        for k, y in enumerate(ys):
            self.assertAlmostEqual(y / 1e9, M[f"ic_market_y{k}_b"], delta=0.05, msg=k)
        for n in (1, 2, 3, 4):
            self.assertAlmostEqual(((ys[0] / ys[n]) ** (1 / n) - 1) * 100, M[f"ic_market_cagr_{n}y_pct"], delta=0.05, msg=n)
        ex = [sum(wsum(VOL[s], (date.fromisoformat(ASOF) - timedelta(days=365 * k)).isoformat(), 365) for s in PEERS if s != "near-intents") for k in range(5)]
        for n in (1, 2, 4):
            self.assertAlmostEqual(((ex[0] / ex[n]) ** (1 / n) - 1) * 100, M[f"ic_market_ex_intents_cagr_{n}y_pct"], delta=0.05, msg=n)
        self.assertLess(M["ic_market_ex_intents_cagr_1y_pct"], 0, "last year's growth of the set is all Intents': the other venues fell")

    def test_share_and_take_today_multiply_back_to_revenue(self):
        v90, mkt = wsum(VOL["near-intents"], ASOF, 90), sum(wsum(VOL[s], ASOF, 90) for s in PEERS)
        r90 = wsum(REV, ASOF, 90)
        self.assertAlmostEqual(v90 / mkt * 100, M["ic_share_90d_pct"], delta=0.05)
        self.assertAlmostEqual(r90 / v90 * 1e4, M["ic_take_90d_bp"], delta=0.005)
        self.assertAlmostEqual(mkt * (v90 / mkt) * (r90 / v90), r90, delta=1e-6 * r90)
        self.assertAlmostEqual(wsum(FEES["near-intents"], ASOF, 90) / v90 * 1e4, M["ic_gross_bp_90d"], delta=0.05)


def monthly(series: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for d, v in series.items():
        out[d[:7]] = out.get(d[:7], 0.0) + v
    return out


class Scenarios(unittest.TestCase):
    def test_the_anchors_are_the_extremes_of_the_months_they_name(self):
        mv = {s: monthly(VOL[s]) for s in PEERS}
        shares = {k: mv["near-intents"][k] / sum(mv[s].get(k, 0.0) for s in PEERS) * 100
                  for k in mv["near-intents"] if "2025-11" <= k <= "2026-10"}
        self.assertEqual(len(shares), 12)
        mr = monthly(REV)
        takes = {k: mr.get(k, 0.0) / mv["near-intents"][k] * 1e4 for k in mv["near-intents"] if "2026-03" <= k <= "2026-10"}
        self.assertEqual(len(takes), 8)
        self.assertAlmostEqual(min(shares.values()), M["ic_share_min_pct"], delta=0.05)
        self.assertAlmostEqual(max(shares.values()), M["ic_share_max_pct"], delta=0.05)
        self.assertAlmostEqual(min(takes.values()), M["ic_take_min_bp"], delta=0.005)
        self.assertAlmostEqual(max(takes.values()), M["ic_take_max_bp"], delta=0.005)
        self.assertEqual((M["ic_bear_share_pct"], M["ic_bull_share_pct"]), (M["ic_share_min_pct"], M["ic_share_max_pct"]))
        self.assertEqual((M["ic_bear_take_bp"], M["ic_bull_take_bp"]), (M["ic_take_min_bp"], M["ic_take_max_bp"]))
        self.assertEqual((M["ic_bear_market_cagr_pct"], M["ic_base_market_cagr_pct"], M["ic_bull_market_cagr_pct"]),
                         (M["ic_market_cagr_2y_pct"], M["ic_market_cagr_1y_pct"], M["ic_market_cagr_4y_pct"]))
        self.assertEqual((M["ic_bear_hsp029"], M["ic_base_hsp029"], M["ic_bull_hsp029"]), ("no", "yes", "yes"))

    def test_the_multiples_multiply(self):
        self.assertAlmostEqual(M["ic_mult_market_x"] * M["ic_mult_share_x"] * M["ic_mult_take_x"], M["ic_required_multiple_x"], delta=0.15)
        self.assertAlmostEqual(M["ic_take_90d_bp"] * M["ic_mult_take_x"], M["ic_take_needed_bp"], delta=0.3)
        self.assertAlmostEqual(M["ic_take_needed_bp"] / M["ic_gross_bp_90d"], M["ic_take_needed_vs_gross_x"], delta=0.05)
        self.assertAlmostEqual((1 + M["ic_market_cagr_1y_pct"] / 100) ** M["ic_years_n"], M["ic_mult_market_x"], delta=0.01)

    def test_base_coverage_is_base_revenue_over_the_rules_dilution(self):
        """The base case keeps the last 90 days' share and take, so its 2031 revenue is today's grown at the market's last-year pace."""
        self.assertAlmostEqual(M["ic_base_rev_multiple_x"], M["ic_mult_market_x"], delta=0.01)
        self.assertAlmostEqual(M["ic_base_rev_2031_m"], M["ic_rev_90d_ann_m"] * M["ic_mult_market_x"], delta=0.2)
        self.assertLess(M["ic_bear_coverage_2031_pct"], M["ic_base_coverage_2031_pct"])
        self.assertLess(M["ic_base_coverage_2031_pct"], M["ic_bull_coverage_2031_pct"])
        for k in ("market", "share", "take", "hsp029", "price"):
            self.assertLessEqual(M[f"ic_tor_{k}_lo_pct"], M["ic_base_coverage_2031_pct"] + 0.05, k)
            self.assertGreaterEqual(M[f"ic_tor_{k}_hi_pct"], M["ic_base_coverage_2031_pct"] - 0.05, k)


class Peers(unittest.TestCase):
    def test_multiples_are_the_point_nearest_the_snapshot_over_365_days_of_fees(self):
        snap = read_raw("coingecko/near_snapshot.json")
        t = datetime.fromisoformat(snap["last_updated"].replace("Z", "+00:00")).timestamp() * 1000
        caps = read_raw("coingecko/peer_caps_30d.json")
        for slug, key in (("thorchain-dex", "thorchain"), ("chainflip-amm", "chainflip")):
            cap = min(caps[slug]["market_caps"], key=lambda p: abs(p[0] - t))[1]
            self.assertAlmostEqual(cap / 1e6, M[f"ic_peer_{key}_mcap_m"], delta=0.05, msg=key)
            self.assertAlmostEqual(cap / wsum(FEES[slug], ASOF, 365), M[f"ic_peer_{key}_mcap_to_fees_x"], delta=0.05, msg=key)
        self.assertAlmostEqual(float(snap["market_cap_usd"]) / wsum(FEES["near-intents"], ASOF, 365), M["ic_near_mcap_to_intents_fees_x"], delta=0.05)
        near_cap = min(caps["near-intents"]["market_caps"], key=lambda p: abs(p[0] - t))[1]
        self.assertLess(abs(near_cap / float(snap["market_cap_usd"]) - 1), 0.01, "the hourly point and the committed snapshot agree")


class StakingFloat(unittest.TestCase):
    def test_float_from_the_pool_endpoints_and_supply_headers(self):
        pe, ei = read_raw("rpc/pool_endpoints_archival.json"), read_raw("rpc/epoch_issuance.json")
        b0, b1 = (str(b) for b in pe["blocks"])
        st = [sum(int(v[i]) for v in pe["pools"].values()) / YOCTO for i in (0, 1)]
        ts = [int(ei["endpoints"][b]["total_supply"]) / YOCTO for b in (b0, b1)]
        self.assertAlmostEqual(st[0] / ts[0] * 100, M["ic_staked_share_start_pct"], delta=0.05)
        self.assertAlmostEqual(st[1] / ts[1] * 100, M["ic_staked_share_end_pct"], delta=0.05)
        self.assertAlmostEqual(((ts[1] - st[1]) - (ts[0] - st[0])) / 1e6, M["ic_float_change_90d_m"], delta=0.05)


class History(unittest.TestCase):
    def test_the_last_point_is_p3s_quantity_and_points_are_a_week_apart(self):
        h = S["cov_hist"]
        self.assertEqual(h[-1]["date"], ASOF)
        self.assertAlmostEqual(h[-1]["cov_pct"], M["p3_quantity_90d_asof_pct"], delta=0.05)
        self.assertEqual(len(h), M["ic_cov_hist_points_n"])
        gaps = {(date.fromisoformat(b["date"]) - date.fromisoformat(a["date"])).days for a, b in zip(h, h[1:])}
        self.assertEqual(gaps, {7})


class MonteCarlo(unittest.TestCase):
    def test_the_model_is_deterministic_and_its_dated_forecasts_hold(self):
        """M1-M4 (PREREG-ADDENDUM.md, 2026-11-13 23:50 UTC) quote fwd_* metrics; a second run must give the same values."""
        from pipeline.compute import llama_daily
        from pipeline.common import day
        from pipeline.model import forward
        rev = llama_daily("llama/dailyRevenue_near-intents.json")
        vol = llama_daily("llama/volume_near-intents.json")
        price = {}
        for ms, p in read_raw("coingecko/near_market_chart_365d.json")["prices"]:
            price[day(ms / 1000)] = float(p)
        m: dict = {}
        forward(m, rev, vol, price)
        for k in ("fwd_p_cov_ge25_2027_pct", "fwd_cov_2027_p25_pct", "fwd_cov_2027_p75_pct", "fwd_p_cov_ge100_2028_pct", "fwd_p_cov_ge100_2031_pct",
                  "fwd_p_cov_ge100_2031_no_hsp029_pct", "fwd_block_p_cov_ge100_2031_pct", "fwd_exsep_p_cov_ge100_2031_pct", "fwd_exsep_vol_monthly_mean_pct"):
            self.assertEqual(m[k], M[k], k)



class StoryPage(unittest.TestCase):
    """site/story.html: the six charts of the case, one per screen, for the demo. It is part of the render and of `render --check`."""

    def test_the_story_is_rendered_with_the_dashboard_and_links_back_into_it(self):
        import re
        from pipeline import render as R
        files = R.render()
        page, story = files["site/index.html"].decode("utf-8"), files["site/story.html"].decode("utf-8")
        self.assertEqual((ROOT / "site" / "story.html").read_bytes(), files["site/story.html"], "run python3 -m pipeline.render and commit site/")
        self.assertNotIn("<script", story.lower())
        self.assertNotRegex(story, r'(?:src|href)="(?:https?:)?//(?!github\.com/)')   # nothing loaded from another host; links go to GitHub only
        for cid in R.STORY_CARDS:
            self.assertIn(f'id="chart-{cid}"', story, cid)
        ids = set(re.findall(r' id="([^"]+)"', page))
        targets = set(re.findall(r'href="index\.html#([^"]+)"', story))
        self.assertTrue(targets)
        self.assertEqual(targets - ids, set(), "every link from the story lands on the dashboard")
        self.assertNotRegex(story, r'href="#')


if __name__ == "__main__":
    unittest.main()
