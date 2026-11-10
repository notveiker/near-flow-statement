"""Offline tests for pipeline/near_collect.py: sealing, verification, resuming and the rate limit. No network.

Run: make test
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import near_collect as C  # noqa: E402


def fake_block(h: int, prev: str | None) -> dict:
    return {"block": {"header": {"height": h, "hash": f"hash{h}", "prev_hash": prev or f"hash{h - 1}",
                                 "timestamp_nanosec": str(h * 10**9)}}, "shards": []}


class Store(unittest.TestCase):
    def setUp(self):
        self._shard = C.SHARD
        C.SHARD = 10
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        C.SHARD = self._shard
        self.tmp.cleanup()

    def fill(self, store, a, b, skip=()):
        for h in range(a, b + 1):
            store.add(h, None if h in skip else fake_block(h, None))
        store.try_seal(a)

    def test_a_shard_seals_only_when_complete(self):
        s = C.Store(self.root)
        for h in range(20, 29):
            s.add(h, fake_block(h, None))
        self.assertFalse(s.try_seal(20))
        s.add(29, fake_block(29, None))
        self.assertTrue(s.try_seal(20))
        self.assertTrue(s.is_sealed(25))
        self.assertFalse((self.root / "part" / "000000000020_000000000029.jsonl").exists())

    def test_verify_passes_on_a_linked_chain_with_a_skipped_height(self):
        s = C.Store(self.root)
        for h in range(20, 30):
            if h == 25:
                s.add(h, None)  # the chain skipped this height; block 26 points at 24
            else:
                s.add(h, fake_block(h, "hash24" if h == 26 else None))
        s.try_seal(20)
        r = C.verify(self.root)
        self.assertEqual(r["bad"], [])
        self.assertEqual((r["shards"], r["blocks"]), (1, 9))

    def test_verify_detects_a_changed_file_and_a_broken_chain(self):
        s = C.Store(self.root)
        self.fill(s, 20, 29)
        self.assertEqual(C.verify(self.root)["bad"], [])
        gz = self.root / "shards" / "000000000020_000000000029.jsonl.gz"
        gz.write_bytes(gz.read_bytes() + b"x")
        self.assertEqual(C.verify(self.root)["bad"], [(20, "sha256")])

    def test_chain_break_inside_a_shard_is_reported(self):
        s = C.Store(self.root)
        for h in range(20, 30):
            s.add(h, fake_block(h, "bad" if h == 24 else None))
        s.try_seal(20)
        self.assertIn((24, "prev_hash"), C.verify(self.root)["bad"])

    def test_chain_break_across_shards_is_reported(self):
        s = C.Store(self.root)
        self.fill(s, 20, 29)
        for h in range(30, 40):
            s.add(h, fake_block(h, "elsewhere" if h == 30 else None))
        s.try_seal(30)
        self.assertIn((30, "chain_across_shards"), C.verify(self.root)["bad"])

    def test_resume_cuts_a_torn_last_line(self):
        s = C.Store(self.root)
        for h in range(20, 23):
            s.add(h, fake_block(h, None))
        with open(s.part_path(20), "a") as f:
            f.write('{"h":23,"b":{"block"')  # a run stopped mid-write
        s2 = C.Store(self.root)
        self.assertEqual(s2.have(20), {20, 21, 22})
        s2.add(23, fake_block(23, None))
        self.assertEqual(s2.have(20), {20, 21, 22, 23})
        lines = s2.part_path(20).read_text().splitlines()
        self.assertEqual([json.loads(x)["h"] for x in lines], [20, 21, 22, 23])

    def test_next_missing_skips_sealed_shards_in_both_directions(self):
        s = C.Store(self.root)
        self.fill(s, 20, 29)
        self.assertEqual(C.next_missing(s, 20, +1), 30)
        self.assertEqual(C.next_missing(s, 29, -1), 19)
        s.add(30, fake_block(30, None))
        self.assertEqual(C.next_missing(s, 30, +1), 31)


class Rate(unittest.TestCase):
    def test_bucket_never_exceeds_the_rate(self):
        t = [0.0]
        slept = []

        def sleep(x):
            slept.append(x)
            t[0] += x

        b = C.Bucket(120, now=lambda: t[0], sleep=sleep)  # 2 a second
        for _ in range(100):
            b.wait()
        self.assertGreaterEqual(t[0], 99 / 2 - 4 * 0.5)  # burst allowance is at most four intervals

    def test_429_slows_the_bucket_down(self):
        b = C.Bucket(150)
        before = b.interval
        b.slow_down()
        self.assertGreater(b.interval, before)

    def test_the_cli_refuses_a_rate_above_the_published_limit(self):
        self.assertEqual(C.main(["plan", "--root", tempfile.gettempdir(), "--per-min", "200"]), 2)


if __name__ == "__main__":
    unittest.main()
