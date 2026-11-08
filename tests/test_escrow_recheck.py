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

import ast
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


def tool_errors(func: str) -> list[str]:
    """The fixed start of every error string that pipeline/fetch_escrow.py `func` can write, read from its source (up to the
    first {placeholder} of an f-string), so that the classification below is tested against what the tool really writes."""
    tree = ast.parse((ROOT / "pipeline" / "fetch_escrow.py").read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == func)
    found = []
    for n in ast.walk(fn):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "append"
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "errs"):
            found.append(n.args[0])
        elif isinstance(n, ast.Return) and isinstance(n.value, ast.List):
            found.extend(n.value.elts)
    heads = []
    for c in sorted(found, key=lambda c: (c.lineno, c.col_offset)):
        if isinstance(c, ast.Constant) and isinstance(c.value, str):
            heads.append(c.value)
        elif isinstance(c, ast.JoinedStr) and c.values and isinstance(c.values[0], ast.Constant):
            heads.append(c.values[0].value)
        else:
            raise AssertionError(f"{func}: an error string this test cannot read at line {c.lineno}")
    return heads


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


class ClassifiesTheErrors(unittest.TestCase):
    """The committed file has no row with a funding-side error and none with a second error beside a height mismatch, so a
    counter that confused them would pass on the real data. These tests edit one row of a copy and recount.

    The row they edit has a funding hop inside the window: a row without one is not in `hops`, so no classification of its
    error strings could change a funding count. Every error string is taken from the source of pipeline/fetch_escrow.py,
    so a message the tool gains is classified by a test and not assumed."""

    @classmethod
    def setUpClass(cls):
        verify, table = load()
        window_hops = {x["delivery_tx_hash"] for x in table if LO <= x["day"] <= HI and x["path"] in ("escrow_unshield", "other")
                       and x["single_use_account"] and x["funding_tx_hash"]}
        cls.target = next((r["delivery_tx_hash"] for r in verify["rows"] if r["ok"] and r["delivery_tx_hash"] in window_hops), None)
        if cls.target is None:
            raise AssertionError("no row of verify_all.json passed and has a funding hop in the window; the tests below need one")
        cls.base: dict = {}
        compute.escrow_recheck(cls.base, LO, HI)

    @staticmethod
    def metrics_after(edit):
        verify, _ = load()
        verify = copy.deepcopy(verify)
        edit(verify)
        real = compute.read_raw
        with mock.patch.object(compute, "read_raw", side_effect=lambda rel: verify if rel == "escrow/verify_all.json" else real(rel)):
            m: dict = {}
            compute.escrow_recheck(m, LO, HI)
        return m

    def with_errors(self, errors, funding_hop_lost):
        """The metrics after the target row gets `errors`. The tool's own summary is kept in step with the classification the
        test expects: one funding hop fewer when `funding_hop_lost`, else the same. A different classification then trips the
        summary check in compute.escrow_recheck, which is reported here as what it means."""
        def edit(v):
            row = next(r for r in v["rows"] if r["delivery_tx_hash"] == self.target)
            row["errors"], row["ok"] = list(errors), False
            v["summary"]["rows_ok"] -= 1
            if funding_hop_lost:
                v["summary"]["funding_hops_ok"] -= 1
        try:
            return self.metrics_after(edit)
        except ValueError as exc:
            self.fail(f"{errors} was classified the other way (compute.escrow_recheck: {exc})")

    def test_the_edited_row_is_a_funding_hop_in_the_window(self):
        verify, table = load()
        row = next(x for x in table if x["delivery_tx_hash"] == self.target)
        self.assertTrue(row["funding_tx_hash"], "a row without a funding hop cannot show how its errors are classified")
        self.assertTrue(LO <= row["day"] <= HI and row["single_use_account"])

    def test_the_tools_delivery_messages_are_the_delivery_side_prefixes_and_the_funding_ones_are_not(self):
        delivery, funding = tool_errors("check_delivery"), tool_errors("check_funding")
        self.assertEqual(len(delivery), len(DELIVERY_SIDE))
        self.assertEqual([next(p for p in DELIVERY_SIDE if h.startswith(p)) for h in delivery], list(DELIVERY_SIDE))
        self.assertTrue(funding)
        self.assertFalse([h for h in funding if h.startswith(DELIVERY_SIDE)])

    def test_a_funding_side_error_is_not_a_height_failure_and_costs_a_funding_hop(self):
        m = self.with_errors(["funder mismatch: chain [] csv x"], funding_hop_lost=True)
        base = self.base
        self.assertEqual(m["escrow_recheck_failed_n"], base["escrow_recheck_failed_n"] + 1)
        self.assertEqual(m["escrow_recheck_failed_height_only_n"], base["escrow_recheck_failed_height_only_n"],
                         "a funder mismatch is not a block-height failure")
        self.assertEqual(m["escrow_recheck_funding_hops_ok_n"], base["escrow_recheck_funding_hops_ok_n"] - 1)
        self.assertEqual(m["escrow_recheck_window_funding_ok_n"], base["escrow_recheck_window_funding_ok_n"] - 1)
        self.assertEqual(m["escrow_recheck_window_rows_ok_n"], base["escrow_recheck_window_rows_ok_n"] - 1)

    def test_every_funding_side_message_the_tool_writes_costs_a_funding_hop(self):
        base = self.base
        for head in tool_errors("check_funding"):
            with self.subTest(head):
                m = self.with_errors([head.rstrip() + " [edited]"], funding_hop_lost=True)
                self.assertEqual(m["escrow_recheck_failed_n"], base["escrow_recheck_failed_n"] + 1)
                self.assertEqual(m["escrow_recheck_failed_height_only_n"], base["escrow_recheck_failed_height_only_n"])
                self.assertEqual(m["escrow_recheck_funding_hops_ok_n"], base["escrow_recheck_funding_hops_ok_n"] - 1)
                self.assertEqual(m["escrow_recheck_window_funding_ok_n"], base["escrow_recheck_window_funding_ok_n"] - 1)

    def test_every_delivery_side_message_the_tool_writes_leaves_the_funding_hop_alone(self):
        """One sub-test per delivery-side prefix of compute.escrow_recheck: dropping any one of them fails its own."""
        base = self.base
        for head in tool_errors("check_delivery"):
            with self.subTest(head):
                m = self.with_errors([head.rstrip() + " [edited]"], funding_hop_lost=False)
                height_only = 1 if head.startswith("block mismatch") else 0
                self.assertEqual(m["escrow_recheck_failed_n"], base["escrow_recheck_failed_n"] + 1)
                self.assertEqual(m["escrow_recheck_failed_height_only_n"], base["escrow_recheck_failed_height_only_n"] + height_only)
                self.assertEqual(m["escrow_recheck_funding_hops_ok_n"], base["escrow_recheck_funding_hops_ok_n"],
                                 "a delivery-side error is not a funding error")
                self.assertEqual(m["escrow_recheck_window_funding_ok_n"], base["escrow_recheck_window_funding_ok_n"])
                self.assertEqual(m["escrow_recheck_window_rows_ok_n"], base["escrow_recheck_window_rows_ok_n"] - 1)

    def test_a_height_mismatch_with_another_delivery_error_is_not_height_only_and_leaves_the_funding_hop_alone(self):
        m = self.with_errors(["block mismatch: csv 1 chain [2]", "no native_withdraw event to wallet with amount_yocto"],
                             funding_hop_lost=False)
        base = self.base
        self.assertEqual(m["escrow_recheck_failed_n"], base["escrow_recheck_failed_n"] + 1)
        self.assertEqual(m["escrow_recheck_failed_height_only_n"], base["escrow_recheck_failed_height_only_n"])
        self.assertEqual(m["escrow_recheck_funding_hops_ok_n"], base["escrow_recheck_funding_hops_ok_n"],
                         "delivery-side errors are not funding errors")
        self.assertEqual(m["escrow_recheck_window_funding_ok_n"], base["escrow_recheck_window_funding_ok_n"])

    def test_a_delivery_error_beside_a_funding_error_still_costs_the_funding_hop(self):
        """Both kinds on one row: the funding one decides the funding count, the delivery one does not hide it."""
        m = self.with_errors(["block mismatch: csv 1 chain [2]", "funder mismatch: chain [] csv x"], funding_hop_lost=True)
        base = self.base
        self.assertEqual(m["escrow_recheck_funding_hops_ok_n"], base["escrow_recheck_funding_hops_ok_n"] - 1)
        self.assertEqual(m["escrow_recheck_failed_height_only_n"], base["escrow_recheck_failed_height_only_n"])


if __name__ == "__main__":
    unittest.main()
