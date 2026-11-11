import unittest

from pipeline.hub_trail import trace

Y = 10**24


def g(**kw):
    return {a: {b: int(v * Y) for b, v in d.items()} for a, d in kw.items()}


class TestTrace(unittest.TestCase):
    base = {"EX"}

    def test_one_hop_label(self):
        out = g(a={"EX": 900, "x": 100}, b={"x": 2000})
        got = trace(out, self.base, ["a", "b"], 0.8, 3, 500)
        self.assertEqual(set(got), {"a"})
        self.assertEqual(got["a"]["depth"], 1)

    def test_two_hop_chain_needs_hop_budget(self):
        out = g(a={"EX": 2000}, b={"a": 2000}, c={"b": 2000})
        self.assertEqual({k: v["depth"] for k, v in trace(out, self.base, ["c", "b", "a"], 0.8, 3, 1000).items()}, {"a": 1, "b": 2, "c": 3})
        self.assertEqual(set(trace(out, self.base, ["c", "b", "a"], 0.8, 1, 1000)), {"a"})

    def test_threshold_and_minimum_sent(self):
        out = g(a={"EX": 790, "x": 210}, b={"EX": 400})
        self.assertEqual(trace(out, self.base, ["a", "b"], 0.8, 3, 500), {})
        self.assertEqual(set(trace(out, self.base, ["a", "b"], 0.78, 3, 500)), {"a"})

    def test_cycle_without_labelled_exit_stays_unlabelled(self):
        out = g(a={"b": 5000}, b={"a": 5000})
        self.assertEqual(trace(out, self.base, ["a", "b"], 0.8, 3, 1000), {})


if __name__ == "__main__":
    unittest.main()
