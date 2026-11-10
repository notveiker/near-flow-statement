"""Offline tests for the node archiver: a fake RPC serves a small chain with a skipped height."""
import tempfile
import unittest
from pathlib import Path

from pipeline import near_collect as nc
from pipeline import near_node_archive as na

SKIPPED = 1005


class FakeChain:
    def __init__(self, first, head, earliest=None):
        self.first, self.head, self.earliest = first, head, earliest if earliest is not None else first
        self.calls = []
        self.syncing = False

    def hash(self, h):
        return f"H{h}"

    def prev(self, h):
        p = h - 1
        while p == SKIPPED:
            p -= 1
        return self.hash(p)

    def __call__(self, method, params):
        self.calls.append(method)
        if method == "status":
            return {"sync_info": {"latest_block_height": self.head, "earliest_block_height": self.earliest, "syncing": self.syncing}}
        if method == "block":
            h = params["block_id"]
            if h == SKIPPED or h > self.head or h < self.earliest:
                raise na.RpcError({"name": "HANDLER_ERROR", "cause": {"name": "UNKNOWN_BLOCK"}})
            return {"header": {"height": h, "hash": self.hash(h), "prev_hash": self.prev(h), "timestamp_nanosec": str(h * 10**9)},
                    "chunks": [{"chunk_hash": f"C{h}a", "height_included": h}, {"chunk_hash": f"old{h}", "height_included": h - 1}]}
        if method == "chunk":
            h = int(params["chunk_id"][1:-1])
            return {"transactions": [{"hash": f"T{h}x", "signer_id": "a.near"}, {"hash": f"T{h}y", "signer_id": "b.near"}]}
        if method == "EXPERIMENTAL_tx_status":
            return {"status": {"SuccessValue": ""}, "receipts_outcome": [{"id": "r", "proof": [1, 2, 3], "outcome": {"logs": ["x"]}}]}
        raise AssertionError(method)


class TestHttpRpc(unittest.TestCase):
    def test_http_422_with_json_error_body_becomes_rpc_error(self):
        import json as _json
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                body = _json.dumps({"error": {"name": "HANDLER_ERROR", "cause": {"name": "UNKNOWN_BLOCK"}}}).encode()
                self.send_response(422)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        srv = HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            call = na.http_rpc(f"http://127.0.0.1:{srv.server_port}")
            with self.assertRaises(na.RpcError) as cm:
                call("block", {"block_id": 1})
            self.assertTrue(cm.exception.unknown)
        finally:
            srv.shutdown()
            srv.server_close()


class TestNodeArchive(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_archives_and_verifies_with_skipped_height_and_strips_proofs(self):
        chain = FakeChain(1000, 2100)
        na.run(self.root, "x", None, 4, lag=20, once=True, call=chain)
        self.assertEqual(nc.list_sealed(self.root), [(1000, 1999)])
        r = nc.verify(self.root)
        self.assertEqual((r["blocks"], r["bad"]), (999, []))
        rows = {d["h"]: d["b"] for d in nc.read_shard(self.root, 1000, 1999)}
        self.assertIsNone(rows[SKIPPED])
        b = rows[1001]
        self.assertEqual(len(b["chunks"]), 1)  # only the chunk produced in this block
        self.assertEqual(set(b["txs"]), {"T1001x", "T1001y"})
        self.assertNotIn("proof", b["txs"]["T1001x"]["receipts_outcome"][0])
        self.assertEqual(b["txs"]["T1001x"]["receipts_outcome"][0]["outcome"]["logs"], ["x"])

    def test_waits_for_lag(self):
        chain = FakeChain(1000, 1500)
        na.run(self.root, "x", None, 2, lag=20, once=True, call=chain)
        self.assertEqual(nc.list_sealed(self.root), [])
        self.assertEqual(len(nc.Store(self.root).have(1000)), 481)  # heights 1000..1480

    def test_resume_does_not_refetch(self):
        chain = FakeChain(1000, 1500)
        na.run(self.root, "x", None, 2, lag=20, once=True, call=chain)
        chain.calls.clear()
        chain.head = 1600
        na.run(self.root, "x", None, 2, lag=20, once=True, call=chain)
        self.assertEqual(len(nc.Store(self.root).have(1000)), 581)
        self.assertEqual(chain.calls.count("block"), 100)

    def test_first_shard_starts_at_aligned_earliest(self):
        chain = FakeChain(1000, 2100, earliest=1337)
        na.run(self.root, "x", None, 2, lag=20, once=True, call=chain)
        self.assertEqual(nc.list_sealed(self.root), [])  # head too low to seal 2000..2999
        self.assertEqual(min(nc.Store(self.root).have(2000)), 2000)

    def test_gap_older_than_earliest_is_refused(self):
        chain = FakeChain(1000, 2100, earliest=1500)
        with self.assertRaises(SystemExit):
            na.run(self.root, "x", 1000, 2, lag=20, once=True, call=chain)

    def test_skipped_height_below_earliest_is_an_error_not_null(self):
        chain = FakeChain(1000, 2100, earliest=1500)
        with self.assertRaises(na.RpcError):
            na.fetch_height(chain, 1400, 1500)

    def test_refuses_while_syncing(self):
        chain = FakeChain(1000, 2100)
        chain.syncing = True
        na.run(self.root, "x", None, 2, call=chain, once=True)
        self.assertEqual(chain.calls, ["status"])


if __name__ == "__main__":
    unittest.main()
