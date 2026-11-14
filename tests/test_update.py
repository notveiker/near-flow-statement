"""The update to 2026-11-13 (exploratory, pipeline/update.py) recomputed here from data/raw/update/, independently of the module.

It stops at the last full UTC day before the score, never touches a committed metric, and its implied growth uses the same formula
as the investment case at the cutoff."""
from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "update"
M = json.loads((ROOT / "data" / "metrics.json").read_text(encoding="utf-8"))
END = "2026-11-13"


def daily(rel: str) -> dict[str, float]:
    d = json.loads((RAW / rel).read_text(encoding="utf-8"))
    out = {}
    for ts, v in d["totalDataChart"]:
        k = date.fromtimestamp(0).fromordinal(date(1970, 1, 1).toordinal() + int(ts) // 86400).isoformat()
        if k <= END:
            out[k] = float(v)
    return out


def wsum(series: dict[str, float], end: str, days: int) -> float:
    e = date.fromisoformat(end).toordinal()
    return sum(v for k, v in series.items() if e - days < date.fromisoformat(k).toordinal() <= e)


@unittest.skipUnless((RAW / "llama" / "dailyRevenue_near-intents.json").exists(), "no update committed")
class Update(unittest.TestCase):
    def test_it_ends_on_the_last_full_day_before_the_score(self):
        self.assertEqual(M["upd_asof"], END)
        self.assertEqual(M["asof"], "2026-11-04", "the committed analysis keeps its cutoff")

    def test_revenue_take_and_share_over_30_days(self):
        rev = daily("llama/dailyRevenue_near-intents.json")
        vol = {s: daily(f"llama/volume_{s}.json") for s in ("near-intents", "thorchain-dex", "chainflip-amm", "maya-protocol")}
        r30, v30 = wsum(rev, END, 30), wsum(vol["near-intents"], END, 30)
        tot = sum(wsum(v, END, 30) for v in vol.values())
        self.assertAlmostEqual(M["upd_intents_rev_30d_m"], r30 / 1e6, delta=0.006)
        self.assertAlmostEqual(M["upd_take_captured_bp_30d"], r30 / v30 * 1e4, delta=0.006)
        self.assertAlmostEqual(M["upd_intents_share_peerset_30d_pct"], v30 / tot * 100, delta=0.06)
        self.assertAlmostEqual(M["upd_thorchain_share_peerset_30d_pct"], wsum(vol["thorchain-dex"], END, 30) / tot * 100, delta=0.06)
        self.assertGreater(M["upd_intents_share_peerset_30d_pct"], M["upd_thorchain_share_peerset_30d_pct"], "Intents still leads over 30 days")

    def test_the_implied_growth_is_the_cutoff_formula_on_the_update(self):
        rev = daily("llama/dailyRevenue_near-intents.json")
        rev_ann = wsum(rev, END, 90) * 365 / 90
        n = (date(2031, 11, 4) - date.fromisoformat(END)).days / 365.25
        need = M["upd_mcap_usd_b"] * 1e9 * 1.15 ** n * M["upd_ic_supply_factor_x"] / 25
        self.assertAlmostEqual(M["upd_ic_implied_cagr_r15_x25_pct"], ((need / rev_ann) ** (1 / n) - 1) * 100, delta=0.15)
        self.assertGreater(M["upd_ic_implied_cagr_r15_x25_pct"], max(M[f"upd_ic_market_cagr_{k}y_pct"] for k in (1, 2, 3, 4)),
                           "still faster than any window in the data")
        self.assertGreater(M["upd_ic_take_needed_vs_gross_x"], 1, "still more than Intents' whole gross fee")

    def test_no_committed_metric_moved(self):
        for k in ("ic_implied_cagr_r15_x25_pct", "ic_take_needed_vs_gross_x", "ic_base_coverage_2031_pct", "intents_share_peerset_30d_pct"):
            self.assertIn("upd_" + k, M)
        self.assertEqual((M["ic_implied_cagr_r15_x25_pct"], M["ic_take_needed_vs_gross_x"], M["ic_base_coverage_2031_pct"]), (84.9, 2.5, 44.6))


if __name__ == "__main__":
    unittest.main()
