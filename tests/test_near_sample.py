"""Offline tests for the stratified history sampler, on a fake chain whose block time changes over its life."""
import gzip
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from pipeline import near_sample as ns
from pipeline.near_collect import Bucket

H0 = 1000
T0 = int(datetime(2021, 2, 10, tzinfo=timezone.utc).timestamp() * 1e9)
SPLIT = 400_000  # block time is 120 s before this height and 100 s after it (scaled so a short chain spans years)
TIP = 1_600_000
SKIPPED = {1_000_007, 1_200_003}


def ts_of(h: int) -> int:
    if h <= SPLIT:
        return T0 + int((h - H0) * 1.2e11)
    return T0 + int((SPLIT - H0) * 1.2e11) + int((h - SPLIT) * 1.0e11)


def prev_of(h: int) -> int:
    p = h - 1
    while p in SKIPPED:
        p -= 1
    return p


def fake_fetch(h: int):
    if h in SKIPPED or h < H0 or h > TIP:
        return 404, None
    return 200, {"block": {"header": {"height": h, "hash": f"H{h}", "prev_hash": f"H{prev_of(h)}", "timestamp_nanosec": str(ts_of(h))}}, "shards": []}


def date_ns(y, m, d=1):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1e9)


class TestStrata(unittest.TestCase):
    def test_quarter_edges_cover_the_range_and_are_clipped(self):
        e = ns.quarter_edges(date_ns(2021, 2, 10), date_ns(2022, 5, 3))
        self.assertEqual([x[0] for x in e], ["2021Q1", "2021Q2", "2021Q3", "2021Q4", "2022Q1", "2022Q2"])
        self.assertEqual(e[0][1], date_ns(2021, 2, 10))
        self.assertEqual(e[-1][2], date_ns(2022, 5, 3))
        for a, b in zip(e, e[1:]):
            self.assertEqual(a[2], b[1])

    def test_locate_finds_boundary_when_block_time_changes(self):
        calls = []

        def probe(h):
            while h in SKIPPED:
                h += 1
            calls.append(h)
            return h, ts_of(h)

        lo, hi = (H0, ts_of(H0)), (TIP, ts_of(TIP))
        target = date_ns(2021, 10, 1)
        h, t = ns.locate(target, probe, lo, hi)
        self.assertLessEqual(abs(t - target), 1800 * 10**9)
        self.assertLess(len(calls), 12)


class TestPlan(unittest.TestCase):
    strata = [
        {"id": "A", "h0": 1000, "h1": 300_000, "t0_ns": 0, "t1_ns": 10**30, "n": 5},
        {"id": "B", "h0": 300_001, "h1": 600_000, "t0_ns": 0, "t1_ns": 10**30, "n": 8},
    ]

    def test_same_seed_same_plan_and_other_seed_differs(self):
        a = ns.plan_bytes(ns.build_plan("seed1", self.strata))
        self.assertEqual(a, ns.plan_bytes(ns.build_plan("seed1", self.strata)))
        self.assertNotEqual(a, ns.plan_bytes(ns.build_plan("seed2", self.strata)))

    def test_clusters_are_inside_strata_do_not_overlap_and_are_round_robin(self):
        p = ns.build_plan("s", self.strata)
        self.assertEqual(len(p["clusters"]), 13)
        by = {}
        for c in p["clusters"]:
            s = next(x for x in self.strata if x["id"] == c["stratum"])
            self.assertTrue(s["h0"] <= c["start"] and c["end"] <= s["h1"] + 1)
            by.setdefault(c["stratum"], []).append(c["start"])
        for starts in by.values():
            starts.sort()
            for x, y in zip(starts, starts[1:]):
                self.assertGreaterEqual(y - x, ns.CL)
        rounds = [c["round"] for c in p["clusters"]]
        self.assertEqual(rounds, sorted(rounds))  # round 1 of every stratum comes first
        self.assertEqual({c["stratum"] for c in p["clusters"] if c["round"] == 6}, {"B"})

    def test_too_many_clusters_for_a_short_stratum_is_refused(self):
        with self.assertRaises(ValueError):
            ns.draw_clusters("s", "X", 0, 500, 5)


class TestRunAndVerify(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        strata = [
            {"id": "A", "h0": 1000, "h1": 700_000, "t0_ns": ts_of(1000), "t1_ns": ts_of(700_000), "n": 2},
            {"id": "B", "h0": 700_001, "h1": 1_500_000, "t0_ns": ts_of(700_001), "t1_ns": ts_of(1_500_000), "n": 2},
        ]
        ns.write_plan(self.root, ns.build_plan("test-seed", strata))

    def tearDown(self):
        self.tmp.cleanup()

    def test_run_seals_clusters_and_verify_passes(self):
        ns.run(self.root, per_min=1e9, fetch=fake_fetch, sleep=lambda s: None)
        r = ns.verify(self.root)
        self.assertEqual((r["clusters"], r["planned"], r["bad"]), (4, 4, []))
        self.assertEqual(r["blocks"], 400 - sum(1 for c in ns.load_plan(self.root)["clusters"] for h in SKIPPED if c["start"] <= h <= c["end"]))

    def test_round_caps_stop_a_stratum_early(self):
        plan = ns.load_plan(self.root)
        plan["strata"][1]["n"] = 3  # B is now the heavier stratum
        plan = ns.build_plan("test-seed", plan["strata"])
        root = self.root / "c"
        ns.write_plan(root, plan)
        ns.run(root, per_min=1e9, fetch=fake_fetch, sleep=lambda s: None, max_round_early=1, max_round_recent=2)
        done = sorted(p.stem for p in (root / "clusters").glob("*.json"))
        self.assertEqual(done, ["A_01", "B_01", "B_02"])
        self.assertEqual(ns.round_caps(plan, None, None), {"A": 2, "B": 3})

    def test_balanced_when_stopped_early(self):
        ns.run(self.root, per_min=1e9, fetch=fake_fetch, max_clusters=2, sleep=lambda s: None)
        done = {p.stem for p in (self.root / "clusters").glob("*.json")}
        self.assertEqual(done, {"A_01", "B_01"})

    def test_resume_after_a_torn_line_does_not_refetch_stored_heights(self):
        plan = ns.load_plan(self.root)
        c = plan["clusters"][0]
        st = ns.Clusters(self.root)
        for h in range(c["start"], c["start"] + 10):
            st.add(c["id"], h, fake_fetch(h)[1])
        with open(st.part(c["id"]), "a") as f:
            f.write('{"h": 99999, "b": {"tru')  # torn
        st.close()
        calls = []

        def counting(h):
            calls.append(h)
            return fake_fetch(h)

        ns.run(self.root, per_min=1e9, fetch=counting, max_clusters=1, sleep=lambda s: None)
        self.assertNotIn(c["start"], calls)
        self.assertEqual(len(calls), 90 + 0)
        self.assertEqual(ns.verify(self.root)["bad"], [])

    def test_skipped_height_is_stored_as_null_after_retries(self):
        strata = [{"id": "S", "h0": 1_000_000 - 50, "h1": 1_100_000, "t0_ns": ts_of(1_000_000 - 50), "t1_ns": ts_of(1_100_000), "n": 1}]
        root = self.root / "s"
        plan = ns.build_plan("x", strata)
        plan["clusters"][0].update(start=1_000_000 - 50, end=1_000_000 + 49)
        ns.write_plan(root, plan)
        ns.run(root, per_min=1e9, fetch=fake_fetch, sleep=lambda s: None)
        rows = {d["h"]: d["b"] for d in ns.read_cluster(root, "S_01")}
        self.assertIsNone(rows[1_000_007])
        self.assertEqual(ns.verify(root)["bad"], [])

    def test_429_slows_the_bucket_and_retries(self):
        seen = {"n": 0}

        def flaky(h):
            seen["n"] += 1
            return (429, None) if seen["n"] == 3 else fake_fetch(h)

        sleeps = []
        ns.run(self.root, per_min=1e9, fetch=flaky, max_clusters=1, sleep=sleeps.append)
        self.assertIn(30, sleeps)
        self.assertEqual(ns.verify(self.root)["bad"], [])

    def test_verify_detects_changed_file_and_chain_break_and_plan_edit(self):
        ns.run(self.root, per_min=1e9, fetch=fake_fetch, max_clusters=1, sleep=lambda s: None)
        gz = self.root / "clusters" / "A_01.jsonl.gz"
        good = gz.read_bytes()
        gz.write_bytes(good[:-3] + b"xyz")
        self.assertEqual(ns.verify(self.root)["bad"][0][1], "sha256")
        # a re-sealed file with a broken chain still fails on the chain
        rows = [json.loads(x) for x in gzip.decompress(good).decode().splitlines()]
        rows[50]["b"]["block"]["header"]["prev_hash"] = "WRONG"
        body = "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows).encode()
        gz.write_bytes(gzip.compress(body, 6, mtime=0))
        man = json.loads((self.root / "clusters" / "A_01.json").read_text())
        import hashlib
        man["sha256"] = hashlib.sha256(gz.read_bytes()).hexdigest()
        (self.root / "clusters" / "A_01.json").write_text(json.dumps(man))
        self.assertIn(("A_01", "prev_hash"), ns.verify(self.root)["bad"])
        (self.root / "plan.json").write_text((self.root / "plan.json").read_text().replace("test-seed", "other"))
        with self.assertRaises(SystemExit):
            ns.load_plan(self.root)


class TestCli(unittest.TestCase):
    def test_refuses_high_rate(self):
        self.assertEqual(ns.main(["run", "--root", "/nonexistent", "--per-min", "999"]), 2)

    def test_bucket_is_the_shared_one(self):
        self.assertIs(ns.Bucket, Bucket)


if __name__ == "__main__":
    unittest.main()
