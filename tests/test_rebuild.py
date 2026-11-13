import json
import unittest

from pipeline import rebuild as rb


class Guard(unittest.TestCase):
    def test_all_rebuild_sql_pass_the_guard(self):
        for p in sorted(rb.SQL.glob("*.sql")):
            rb.guard(p.read_text())

    def test_public_scan_without_cutoff_is_rejected(self):
        with self.assertRaises(ValueError):
            rb.guard("SELECT 1 FROM `bigquery-public-data.crypto_near_mainnet_us.transactions` WHERE block_date='2026-11-01'")

    def test_dates_after_cutoff_are_rejected(self):
        with self.assertRaises(ValueError):
            rb.guard("SELECT 1 FROM x WHERE day = '2026-11-05'")

    def test_balance_tables_are_banned(self):
        for t in rb.BANNED_TABLES:
            with self.assertRaises(ValueError):
                rb.guard(f"SELECT 1 FROM `bigquery-public-data.crypto_near_mainnet_us.{t}` WHERE block_height <= {rb.CUTOFF_BLOCK}")

    def test_buyback_balance_read_refused(self):
        from pipeline.rebuild_rpc import mt_balance_of
        with self.assertRaises(ValueError):
            mt_balance_of(rb.FORBIDDEN_BALANCE_ACCOUNT, "nep141:wrap.near", 100)
        with self.assertRaises(ValueError):
            mt_balance_of(rb.ESCROW, "nep141:wrap.near", rb.CUTOFF_BLOCK + 1)

    def test_height_check(self):
        rb._check_heights([{"h": str(rb.CUTOFF_BLOCK)}])
        with self.assertRaises(RuntimeError):
            rb._check_heights([{"h": str(rb.CUTOFF_BLOCK + 1)}])


class Rules(unittest.TestCase):
    def test_stable_rule(self):
        self.assertTrue(rb.is_stable("USDC", 0.9995))
        self.assertTrue(rb.is_stable("DAI", 1.0))
        self.assertFalse(rb.is_stable("USDX", 0.80))
        self.assertFalse(rb.is_stable("NEAR", 1.0))

    def test_selftest_parse_is_as_designed(self):
        rows = {r["event"]: r for r in json.load(open(rb.OUT / "selftest_synthetic.json"))}
        self.assertEqual(rows["mt_mint"]["wnear_mt"], "5")
        self.assertEqual(rows["token_diff"]["wnear_diff"], "-12")
        self.assertIn('"nep141:usdc":"34"', rows["token_diff"]["pairs"])
        self.assertEqual(rows["token_diff"]["pairs"], rows["token_diff"]["pairs_from_string"])  # production (STRING) form


if __name__ == "__main__":
    unittest.main()


class Results(unittest.TestCase):
    def test_escrow_ledger_reconciles_and_cutoff_respected(self):
        r = json.load(open(rb.ROOT / "data" / "derived" / "rebuild_results.json"))
        self.assertTrue(r["q1"]["ledger_complete_within_1pct"])
        self.assertEqual(r["cutoff_block"], rb.CUTOFF_BLOCK)
        self.assertEqual(r["q2"]["chain_vs_deliveries_csv"]["days_with_diff_gt_1near"], 0)

    def test_fu2b_and_f4_reconcile(self):
        r = json.load(open(rb.ROOT / "data" / "derived" / "rebuild_results.json"))
        f = r["fu2b"]
        self.assertAlmostEqual(f["R_pass_through"], 1.0, places=3)
        self.assertAlmostEqual(f["direct_coverage_of_wrapped"], 1.0, places=2)
        self.assertTrue(f["fu1_consistent"])
        self.assertAlmostEqual(f["top_funder_matches_fu1"]["ratio"], 1.0, places=4)
        g = r["fu4"]
        self.assertAlmostEqual(g["rest_group_escrow_funded_near"] / g["deliveries_csv_escrow_unshield_near"], 1.0, delta=0.01)
        self.assertFalse(g["H_FU4a_strict"]["attribution_allowed_by_reconciliation"])
        self.assertTrue(g["H_FU4b_strict"]["supported"])

    def test_fu5_numbers_are_consistent(self):
        r = json.load(open(rb.ROOT / "data" / "derived" / "rebuild_results.json"))["fu5"]
        self.assertAlmostEqual(sum(r["delivered_usd_by_group"].values()), r["delivered_usd"], delta=1.0)
        self.assertTrue(r["H_FU5a_falsified"])
        self.assertTrue(r["post_hoc_llama_denominator"]["within_25pct"])

    def test_fu6_placebo_gate(self):
        r = json.load(open(rb.ROOT / "data" / "derived" / "rebuild_results.json"))["fu6"]
        self.assertEqual(r["step_called"], r["mirrored"] and r["share_of_boundaries_with_ratio_at_least_0901"] <= 0.10)

    def test_fu7_relay_reconciles(self):
        r = json.load(open(rb.ROOT / "data" / "derived" / "rebuild_results.json"))["fu7"]
        self.assertAlmostEqual(r["coverage_K"], 1.0, places=3)
        self.assertAlmostEqual(r["to_bridge_share_of_outflow"], 1.0, places=3)
        self.assertTrue(r["H_FU7b_supported"])

    def test_fu8_relay_dominates_exchange_share(self):
        r = json.load(open(rb.ROOT / "data" / "derived" / "rebuild_results.json"))["fu8"]
        self.assertGreater(r["all"]["coverage"], 0.6)
        self.assertTrue(r["H_FU8a_supported"])
        self.assertTrue(r["H_FU8b_falsified"])

    def test_fu9_rules_applied(self):
        r = json.load(open(rb.ROOT / "data" / "derived" / "rebuild_results.json"))["fu9"]
        for sv in ("blockzen-1-main.near", "crux-solver.near"):
            self.assertEqual(r[sv]["H_FU9a_falsified"], any(abs(x) > 0.5 for x in r[sv]["month_deviation"].values()))

    def test_fu10_books_close(self):
        r = json.load(open(rb.ROOT / "data" / "derived" / "rebuild_results.json"))["fu10"]
        self.assertTrue(r["H_FU10a_complete"])
        self.assertLess(r["residual_over_larger_flow"], 1e-9)
        self.assertAlmostEqual(r["d6b77389"]["sent_over_direct_plus_native_withdraw_post_hoc"], 1.0, places=4)

    def test_fu11_rules_applied(self):
        r = json.load(open(rb.ROOT / "data" / "derived" / "rebuild_results.json"))["fu11"]
        p = r["primary_same_symbol_1click"]
        self.assertGreaterEqual(p["swaps"], 10000)
        self.assertEqual(r["H_FU11a_falsified"], p["spread_bp"] < 2 or p["spread_bp"] > 25)
