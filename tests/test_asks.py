import json
import unittest

from pipeline import rebuild as rb, windows as w
from pipeline.common import ROOT


class Windows(unittest.TestCase):
    def test_windows_are_non_overlapping_90_days_before_h1a(self):
        ws = w.windows()
        self.assertEqual(len(ws), 8)
        self.assertEqual(ws[0]["end"], "2026-08-06")
        for a, b in zip(ws, ws[1:]):
            self.assertEqual(a["seed"], b["end"])
        self.assertTrue(all(x["end"] <= rb.CUTOFF_DATE for x in ws))

    def test_templates_pass_guard(self):
        for k in ("flows", "endpoints"):
            for x in w.windows():
                w.guard(w.render(k, x)[1])
        for p in (ROOT / "sql" / "april").glob("*.sql"):
            w.guard(p.read_text())

    def test_cost_cap_respected_and_reported(self):
        plan = json.load(open(ROOT / "data" / "raw" / "windows" / "plan_run.json"))
        ran = sum(plan["dry_run_gb"][f"sw_{k}_w{i}"] for i in plan["run"] for k in ("flows", "endpoints"))
        self.assertLessEqual(ran, 1500)
        self.assertEqual(sorted(plan["run"] + plan["not_run_over_cap"]), list(range(1, 9)))

    def test_price_series_stops_at_cutoff(self):
        px = json.load(open(ROOT / "data" / "raw" / "windows" / "near_price_daily_llama.json"))
        self.assertLessEqual(max(px), rb.CUTOFF_DATE)


class April(unittest.TestCase):
    def test_classification_follows_the_pre_registered_criteria(self):
        r = json.load(open(ROOT / "data" / "derived" / "april_drop.json"))
        c = r["fortnights"]["criteria"]
        self.assertEqual(r["fortnights"]["one_class_ended"], all(c.values()))
        self.assertAlmostEqual(r["fortnights"]["before_total"] - r["fortnights"]["after_total"], -r["fortnights"]["net_change"], places=0)
