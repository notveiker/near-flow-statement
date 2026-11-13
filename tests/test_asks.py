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


class CrossSection(unittest.TestCase):
    def test_held_protocols_refused_before_unlock_without_flag_or_scoring(self):
        from datetime import datetime, timezone
        from pipeline import fetch_cross_section as f
        early = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
        late = datetime(2026, 11, 14, 1, 0, tzinfo=timezone.utc)
        for s in f.HELD:
            with self.assertRaises(PermissionError):
                f.assert_allowed(s, now=late, held_flag=False)
            with self.assertRaises(PermissionError):
                f.assert_allowed(s, now=early, held_flag=True)
        if not f.scoring_has_run():
            with self.assertRaises(PermissionError):
                f.assert_allowed("near-intents", now=late, held_flag=True)

    def test_no_held_slug_in_comparators_and_no_overview_endpoint(self):
        from pipeline import fetch_cross_section as f
        self.assertFalse({c["slug"] for c in f.COMPARATORS} & set(f.HELD))
        import re
        calls = re.findall(r"http_json\(f?\"([^\"]+)\"", open(f.__file__).read())
        self.assertTrue(calls and all("overview" not in c for c in calls))

    def test_nothing_fetched_for_held_yet(self):
        from pipeline import fetch_cross_section as f
        p = f.ROOT / "data" / "raw" / "cross_section"
        self.assertFalse((p / "all.json").exists() and not f.scoring_has_run())


class SampleValidation(unittest.TestCase):
    def test_validation_matches_rule(self):
        r = json.load(open(ROOT / "data" / "derived" / "history_sample_validation.json"))["primary_198"]
        self.assertEqual(r["intervals_too_narrow_by_rule"], r["covered"] / r["scored_quarters"] < 0.8)
        self.assertEqual(r["scored_quarters"], 24)

    def test_class_adjusted_cut_is_the_198(self):
        r = json.load(open(ROOT / "data" / "derived" / "history_class_adjusted.json"))
        self.assertEqual(r["primary_198_sealed_by_stop"]["clusters"], 198)


class ClassCensus(unittest.TestCase):
    def test_exact_class_shares_consistent(self):
        r = json.load(open(ROOT / "data" / "derived" / "class_census.json"))
        q = r["quarters"]["2025Q3"]
        self.assertAlmostEqual(q["c_per_day"] + q["exc_per_day"], q["tx_per_day"], delta=1.0)
        self.assertEqual(r["decline"]["concentrated"], r["decline"]["signers_for_50pct"] <= 20)


class OtherMetrics(unittest.TestCase):
    def test_definition_check_gates_coverage(self):
        r = json.load(open(ROOT / "data" / "derived" / "history_sample_validation.json"))["other_metrics"]
        for cut in r.values():
            for m in cut.values():
                self.assertEqual(m["definitions_match"], 0.9 <= m["median_sample_over_census"] <= 1.1)
                self.assertEqual(m["coverage"] is None, not m["definitions_match"])


class RX(unittest.TestCase):
    def test_rx_rules_applied(self):
        r = json.load(open(ROOT / "data" / "derived" / "rx_results.json"))
        self.assertEqual(r["rx1"]["H_RX1a_supported"], r["rx1"]["share_top10"] >= 0.25)
        self.assertAlmostEqual(r["rx2"]["total_margin_usd"] / r["rx2"]["delivered_to_revenue_wallets_usd"], r["rx2"]["margin_over_delivered"], places=9)
        win = [m for m in r["rx3"]["months"] if m["per"] in r["rx3"]["window_months"]]
        self.assertEqual(r["rx3"]["H_RX3a_supported"], all(m["top1_share"] >= 0.8 for m in win))


class RX4(unittest.TestCase):
    def test_events_cover_the_wrap_ledger(self):
        r = json.load(open(ROOT / "data" / "derived" / "rx_results.json"))["rx4"]
        for v in r.values():
            self.assertAlmostEqual(v["coverage"], 1.0, places=6)
            self.assertEqual(v["H_RX4a_falsified"], v["top3_share"] < 0.40)
