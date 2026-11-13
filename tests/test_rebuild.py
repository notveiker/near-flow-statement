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

    def test_f2b_and_f4_reconcile(self):
        r = json.load(open(rb.ROOT / "data" / "derived" / "rebuild_results.json"))
        f = r["f2b"]
        self.assertAlmostEqual(f["R_pass_through"], 1.0, places=3)
        self.assertAlmostEqual(f["direct_coverage_of_wrapped"], 1.0, places=2)
        self.assertTrue(f["f1_consistent"])
        self.assertAlmostEqual(f["top_funder_matches_f1"]["ratio"], 1.0, places=4)
        g = r["f4"]
        self.assertAlmostEqual(g["rest_group_escrow_funded_near"] / g["deliveries_csv_escrow_unshield_near"], 1.0, delta=0.01)
        self.assertFalse(g["H_F4a_strict"]["attribution_allowed_by_reconciliation"])
        self.assertTrue(g["H_F4b_strict"]["supported"])
