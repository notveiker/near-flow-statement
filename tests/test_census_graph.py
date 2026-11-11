import unittest

from pipeline.census_graph import shard_edges

Y = 10**24


def _tx(rows):
    outs = [{"id": rid, "outcome": {"status": st}} for rid, _, _, _, st in rows]
    recs = [{"receipt_id": rid, "predecessor_id": p, "receiver_id": r,
             "receipt": {"Action": {"actions": [{"Transfer": {"deposit": str(a)}}]}}} for rid, p, r, a, _ in rows]
    return {"receipts_outcome": outs, "receipts": recs}


OK, BAD = {"SuccessValue": ""}, {"Failure": {}}


class TestShardEdges(unittest.TestCase):
    def blocks(self):
        t = _tx([("1", "a", "b", 5 * Y, OK), ("2", "a", "c", 5 * Y, BAD), ("3", "system", "a", Y, OK),
                 ("4", "a", "b", 2 * Y, OK), ("5", "d", "e", Y // 10, OK)])
        return [{"h": 1, "b": {"txs": {"x": t}}}, {"h": 2, "b": None}]

    def test_failed_and_system_excluded_and_summed(self):
        got = shard_edges(self.blocks(), None, 0)
        self.assertIn(["a", "b", 2, 7 * Y], got)
        self.assertFalse(any(r[1] == "c" or r[0] == "system" for r in got))

    def test_min_amount_filter_in_full_graph_mode(self):
        got = shard_edges(self.blocks(), None, Y)
        self.assertEqual([r[:2] for r in got], [["a", "b"]])

    def test_interest_mode_keeps_senders_into_interest(self):
        got = shard_edges(self.blocks(), frozenset({"b"}))
        self.assertEqual([r[:2] for r in got], [["a", "b"]])


if __name__ == "__main__":
    unittest.main()
