import math
import unittest
from datetime import datetime, timedelta, timezone

from pipeline import cross_section_analysis as cs


def row(slug, fees, rev, hold, s0, s1, price=1.0):
    ts = [int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp()) for d in cs.DAYS]
    mc = []
    for i, t in enumerate(ts):
        s = s0 + (s1 - s0) * i / 29
        mc.append([t * 1000, s * price])
    return {"slug": slug, "dailyFees": [[t, fees / 30] for t in ts], "dailyRevenue": [[t, rev / 30] for t in ts],
            "dailyHoldersRevenue": [[t, hold / 30] for t in ts], "prices": [[t * 1000, price] for t in ts], "market_caps": mc}


class CrossSection(unittest.TestCase):
    def rows(self):
        r = [row("near-intents", 100, 10, 5, 1000, 2000), row("a", 100, 50, 40, 1000, 1100), row("b", 100, 60, 50, 1000, 1050),
             row("c", 100, 70, 60, 1000, 900), row("d", 100, 80, 20, 1000, 1010), row("e", 100, 90, 10, 1000, 1500)]
        return r

    def test_capture_and_net_burn(self):
        m = cs.metrics(self.rows()[3])
        self.assertEqual(m["capture_status"], "net_burn")
        m = cs.metrics(self.rows()[0])
        self.assertAlmostEqual(m["capture"], 5 / 1000, places=6)

    def test_h_x1_bottom_half(self):
        res = cs.evaluate(self.rows(), None)
        self.assertEqual(res["H_X1"]["rank"], 6)           # lowest capture ratio of six
        self.assertTrue(res["H_X1"]["supported"] and not res["H_X1"]["falsified"])

    def test_not_scorable_with_fewer_than_six(self):
        res = cs.evaluate(self.rows()[:4], None)
        self.assertEqual(res["H_X1"]["verdict"], "not scorable")

    def test_h_x2_percentile(self):
        res = cs.evaluate(self.rows(), None)
        self.assertEqual(res["H_X2"]["percentile"], 0.0)   # NEAR's revenue/fees (0.10) below all five others
        self.assertTrue(res["H_X2"]["supported"])

    def test_h_x3_needs_sources(self):
        partner = {v: {"value": x, "source": "u"} for v, x in (("near-intents", 0.3), ("thorchain-dex", 0.1), ("chainflip-amm", 0.2), ("maya-protocol", None))}
        res = cs.evaluate(self.rows(), partner)
        self.assertEqual((res["H_X3"]["rank"], res["H_X3"]["n"]), (1, 3))
        res = cs.evaluate(self.rows(), {"near-intents": {"value": 0.3}})
        self.assertEqual(res["H_X3"]["verdict"], "not scorable")

    def test_missing_day_is_not_scorable(self):
        r = self.rows()[0]
        r["dailyHoldersRevenue"] = r["dailyHoldersRevenue"][:-1]
        self.assertEqual(cs.metrics(r)["capture_status"], "not scorable")


if __name__ == "__main__":
    unittest.main()
