"""Offline tests for the counts that pipeline.compute.escrow_recheck takes from the committed output of
`python3 -m pipeline.fetch_escrow verify --all` (data/raw/escrow/verify_all.json).

THESIS.md, the dashboard's escrow card and docs/sources-checked.md say that the full re-read of the delivery table
against the chain passed every check on all but ten rows, that those ten fail on block height alone, and that every
funding transfer passed. These tests recount that from the per-row records, independently of compute.py, so the wording
cannot outlive the data: if the file is refreshed and a row fails for another reason, or a funding hop fails, the
recount and the wording part ways here.

Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import copy
import csv
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import compute  # noqa: E402

RAW = ROOT / "data" / "raw" / "escrow"
LO, HI = "2026-10-06", "2026-11-04"          # the 30-day window of the escrow evidence (compute.build)
# The error strings pipeline/fetch_escrow.py check_delivery can return; any other string comes from check_funding.
DELIVERY_SIDE = ("delivery tx not returned", "no successful Transfer", "block mismatch", "no native_withdraw",
                 "native_withdraw source")


def load():
    verify = json.loads((RAW / "verify_all.json").read_text(encoding="utf-8"))
    with open(RAW / "deliveries.csv", newline="", encoding="utf-8") as f:
        table = list(csv.DictReader(f))
    return verify, table


class Recount(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verify, cls.table = load()
        cls.m: dict = {}
        compute.escrow_recheck(cls.m, LO, HI)
        cls.committed = json.loads((ROOT / "data" / "metrics.json").read_text(encoding="utf-8"))

    def test_the_metrics_are_the_committed_ones(self):
        got = {k: v for k, v in self.m.items()}
        self.assertEqual(len(got), 9)
        self.assertEqual({k: self.committed[k] for k in got}, got)

    def test_every_delivery_row_was_re_read_once(self):
        rows = self.verify["rows"]
        self.assertEqual(self.m["escrow_recheck_rows_n"], len(rows))
        self.assertEqual([r["delivery_tx_hash"] for r in rows], [r["delivery_tx_hash"] for r in self.table])
        self.assertEqual(len({r["delivery_tx_hash"] for r in rows}), len(rows))

    def test_pass_and_fail_counts_are_recounted_from_the_rows(self):
        rows = self.verify["rows"]
        failed = [r for r in rows if r["errors"]]
        self.assertEqual(self.m["escrow_recheck_failed_n"], len(failed))
        self.assertEqual(self.m["escrow_recheck_rows_ok_n"], len(rows) - len(failed))
        self.assertTrue(all(bool(r["ok"]) == (not r["errors"]) for r in rows))

    def test_the_rows_that_fail_fail_on_block_height_alone(self):
        """The wording 'fail on block height alone' is only true while no failing row has any other error."""
        failed = [r for r in self.verify["rows"] if r["errors"]]
        for r in failed:
            self.assertTrue(r["errors"] and all(e.startswith("block mismatch: csv ") for e in r["errors"]), r)
        self.assertEqual(self.m["escrow_recheck_failed_height_only_n"], len(failed))
        # and each is a difference of a few blocks, not a different transaction
        for r in failed:
            csv_h, chain = r["errors"][0].split("csv ")[1].split(" chain ")
            heights = [int(x) for x in chain.strip("[]").split(",")]
            self.assertTrue(all(0 < h - int(csv_h) <= 3 for h in heights), r)

    def test_every_funding_transfer_passed(self):
        by_hash = {r["delivery_tx_hash"]: r for r in self.verify["rows"]}
        hops = [x for x in self.table if x["funding_tx_hash"]]
        self.assertEqual(self.m["escrow_recheck_funding_hops_n"], len(hops))
        bad = [x["delivery_tx_hash"] for x in hops
               if any(not e.startswith(DELIVERY_SIDE) for e in by_hash[x["delivery_tx_hash"]]["errors"])]
        self.assertEqual(bad, [])
        self.assertEqual(self.m["escrow_recheck_funding_hops_ok_n"], len(hops))

    def test_the_window_counts_match_the_ladder_metrics(self):
        """The 909 of THESIS section 2 are the same rows the ladder counts as single-use deliveries."""
        self.assertEqual(self.m["escrow_recheck_window_single_use_n"], self.committed["escrow_single_use_30d_n"])
        self.assertEqual(self.m["escrow_recheck_window_funding_ok_n"], self.committed["escrow_funded_exact_30d_n"])
        by_hash = {r["delivery_tx_hash"]: r for r in self.verify["rows"]}
        win = [x for x in self.table if LO <= x["day"] <= HI and x["path"] in ("escrow_unshield", "other")
               and x["single_use_account"]]
        self.assertEqual(self.m["escrow_recheck_window_rows_ok_n"], sum(1 for x in win if by_hash[x["delivery_tx_hash"]]["ok"]))

    def test_the_tools_own_summary_agrees_with_the_rows(self):
        s = self.verify["summary"]
        self.assertEqual((s["rows"], s["rows_ok"], s["funding_hops"], s["funding_hops_ok"]),
                         (self.m["escrow_recheck_rows_n"], self.m["escrow_recheck_rows_ok_n"],
                          self.m["escrow_recheck_funding_hops_n"], self.m["escrow_recheck_funding_hops_ok_n"]))


class RefusesAnEditedFile(unittest.TestCase):
    """A summary or a row list that was edited by hand must stop the build, not change a published number."""

    def run_with(self, edit):
        verify, _ = load()
        verify = copy.deepcopy(verify)
        edit(verify)
        real = compute.read_raw
        with mock.patch.object(compute, "read_raw",
                               side_effect=lambda rel: verify if rel == "escrow/verify_all.json" else real(rel)):
            compute.escrow_recheck({}, LO, HI)

    def test_a_summary_that_disagrees_with_the_rows(self):
        with self.assertRaisesRegex(ValueError, "differs from its rows"):
            self.run_with(lambda v: v["summary"].update(rows_ok=v["summary"]["rows_ok"] + 1))

    def test_a_row_list_that_is_not_the_table(self):
        with self.assertRaisesRegex(ValueError, "do not list the same delivery transactions"):
            self.run_with(lambda v: v["rows"].pop())

    def test_a_row_edited_to_pass_changes_the_counts_and_is_caught(self):
        def flip(v):
            bad = next(r for r in v["rows"] if r["errors"])
            bad["errors"], bad["ok"] = [], True          # the summary still says one more failure
        with self.assertRaisesRegex(ValueError, "differs from its rows"):
            self.run_with(flip)


if __name__ == "__main__":
    unittest.main()
