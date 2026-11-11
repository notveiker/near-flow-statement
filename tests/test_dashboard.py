import json
import re
import unittest

from pipeline import build_dashboard as bd
from pipeline.dashboard_data import build, hsp029


class TestDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build()
        cls.html = bd.render(cls.data)

    def test_embedded_json_round_trips(self):
        m = re.search(r'<script id="data" type="application/json">(.*?)</script>', self.html, re.S)
        got = json.loads(m.group(1))
        self.assertEqual(got["metrics"]["rating_output"], self.data["metrics"]["rating_output"])
        self.assertEqual(got["price_usd"], self.data["price_usd"])

    def test_no_script_breakout(self):
        m = re.search(r'<script id="data" type="application/json">(.*?)</script>', self.html, re.S)
        self.assertNotIn("</", m.group(1))

    def test_no_forbidden_wording(self):
        low = self.html.lower()
        for bad in ("aka" + "sh", "bull" + " case", "cro" + "nos", "bear" + " case"):
            self.assertNotIn(bad, low)

    def test_page_makes_no_network_requests(self):
        self.assertNotRegex(self.html, r'(src|href)="https?://(?!github\.com/notveiker)')
        self.assertNotIn("fetch(", self.html)

    def test_hsp029_path_monotone_and_bounded(self):
        a = json.loads(open("data/raw/rpc/rating_assumptions.json").read())
        caps = [p["cap_pct"] for p in hsp029(a)["path"]]
        self.assertTrue(all(x >= y - 1e-9 for x, y in zip(caps, caps[1:])))
        self.assertAlmostEqual(caps[0], 2.5)
        self.assertAlmostEqual(caps[-1], 1.6)

    def test_market_perf_shapes(self):
        mk = self.data["market"]
        for w in ("30", "90", "180", "365"):
            self.assertEqual(set(mk["perf"][w]), {"near", "eth", "sol", "btc"})
        self.assertGreater(len(mk["weekly"]), 50)


if __name__ == "__main__":
    unittest.main()
