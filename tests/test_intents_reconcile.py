import unittest

from pipeline.intents_reconcile import reconcile


class T(unittest.TestCase):
    def test_gap(self):
        usage = {"first_height": 1, "last_height": 2, "flows": {"a": {"deposit": "1500000", "withdraw": "500000"}, "b": {"deposit": "10"}}}
        toks = [{"token_id": "a", "symbol": "A", "chain": "x", "decimals": 6, "price_usd": 1.0}, {"token_id": "b", "symbol": "B", "chain": "x", "decimals": 0, "price_usd": 2.0}]
        sup = {("a", 1): 100, ("a", 2): 1_000_100, ("b", 1): 0, ("b", 2): 12}
        r = reconcile(usage, toks, read=lambda t, h: sup[(t, h)])
        self.assertEqual(r["assets"], 2)
        self.assertEqual(r["assets_matching_within_1usd"], 1)
        self.assertAlmostEqual(r["sum_abs_gap_usd"], 4.0)  # b: supply +12 vs census +10 -> 2 units x $2


if __name__ == "__main__":
    unittest.main()
