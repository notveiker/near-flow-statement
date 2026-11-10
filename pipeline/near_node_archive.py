"""Archive NEAR mainnet from our own nearcore RPC node into sealed, checksummed shards.

Why this exists: the public RPCs are rate limited to a few requests a minute for history, and BigQuery is one source.
A node we run ourselves (see docs/running-a-node.md) answers as fast as its disk allows, so we can keep every block, every
chunk and the full result of every transaction (all receipts, execution outcomes, logs, gas and tokens burnt) for the
window the node holds, and cross-check the BigQuery-derived findings against the chain itself.

Per height we store one JSON object: {"h": height, "b": null | {"block": <block>, "chunks": [<chunk>...],
"txs": {<tx_hash>: <EXPERIMENTAL_tx_status result>}}}. The only thing removed is the merkle `proof` arrays inside
execution outcomes (large, and recomputable from the block); everything else is kept as returned.

Same shard layout, sealing and verifier as near_collect (aligned ranges of 1000 heights, sha256 manifest, prev_hash
chain check), so `pipeline.near_collect verify` works on this output too.

A height the node reports as unknown is stored as null only if the node still holds history that far back
(height >= earliest_block_height); otherwise the run stops with an error, because a missing block that is really a
garbage-collected block would silently make a shard look complete.

Run (on the machine that hosts the node):
    python3 -m pipeline.near_node_archive run    --root /data/near/archive --rpc http://127.0.0.1:3030
    python3 -m pipeline.near_node_archive status --root /data/near/archive --rpc http://127.0.0.1:3030
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pipeline.near_collect import SHARD, Store, next_missing, rng, verify

DEFAULT_RPC = "http://127.0.0.1:3030"
LAG = 20  # stay this many final blocks behind the head so that every receipt of a transaction has executed


class RpcError(Exception):
    def __init__(self, err):
        super().__init__(json.dumps(err)[:300])
        self.err = err

    @property
    def unknown(self) -> bool:
        s = json.dumps(self.err)
        return "UNKNOWN_BLOCK" in s or "UNKNOWN_CHUNK" in s


def http_rpc(url: str, timeout: int = 120):
    def call(method: str, params):
        body = json.dumps({"jsonrpc": "2.0", "id": "a", "method": method, "params": params}).encode()
        req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.load(r)
        except urllib.error.HTTPError as e:  # nearcore answers 4xx with a JSON-RPC error body (e.g. 422 for a skipped height)
            try:
                d = json.load(e)
            except ValueError:
                raise e
            if "error" not in d:
                raise
        if "error" in d:
            raise RpcError(d["error"])
        return d["result"]
    return call


def strip_proofs(x):
    """Drop `proof` arrays from execution outcomes in place and return x."""
    if isinstance(x, dict):
        x.pop("proof", None)
        for v in x.values():
            strip_proofs(v)
    elif isinstance(x, list):
        for v in x:
            strip_proofs(v)
    return x


def sync_state(call) -> dict:
    s = call("status", [])["sync_info"]
    return {"head": s["latest_block_height"], "earliest": s.get("earliest_block_height", 0), "syncing": s["syncing"]}


def fetch_height(call, h: int, earliest: int, pool: ThreadPoolExecutor | None = None):
    """Return the stored record for height h, or None for a height the chain skipped."""
    try:
        block = call("block", {"block_id": h})
    except RpcError as e:
        if e.unknown and h >= earliest:
            return None
        raise
    chunks = []
    for c in block["chunks"]:
        # chunks that were not produced in this block carry the old height_included; only read the new ones
        if c["height_included"] != h:
            continue
        chunks.append(call("chunk", {"chunk_id": c["chunk_hash"]}))
    txs = [(t["hash"], t["signer_id"]) for ch in chunks for t in ch["transactions"]]

    def one(item):
        th, signer = item
        return th, strip_proofs(call("EXPERIMENTAL_tx_status", {"tx_hash": th, "sender_account_id": signer, "wait_until": "FINAL"}))

    results = list(pool.map(one, txs)) if pool else [one(i) for i in txs]
    return {"block": block, "chunks": chunks, "txs": dict(results)}


def run(root: Path, rpc: str, start: int | None, workers: int, lag: int = LAG, once: bool = False, call=None, allow_syncing: bool = False) -> None:
    call = call or http_rpc(rpc)
    store = Store(root)
    st = sync_state(call)
    if st["syncing"] and not allow_syncing:
        print("node is still syncing; wait for syncing=false or pass --allow-syncing", file=sys.stderr)
        return
    aligned = -(-st["earliest"] // SHARD) * SHARD  # first shard start the node still holds in full
    cursor = start if start is not None else aligned
    if store.sealed():
        cursor = max(cursor, max(e for _, e in store.sealed()) + 1)
    store.log(ev="start", head=st["head"], earliest=st["earliest"], cursor=cursor, workers=workers)
    last = 0
    with ThreadPoolExecutor(workers) as pool:
        while True:
            if time.monotonic() - last > 5:
                st, last = sync_state(call), time.monotonic()
            if cursor > st["head"] - lag:
                if once:
                    return
                time.sleep(2)
                continue
            h = next_missing(store, cursor, +1)
            if h is None or h > st["head"] - lag:
                if once:
                    return
                time.sleep(2)
                continue
            cursor = h
            if h < st["earliest"]:
                raise SystemExit(f"height {h} is older than the node's earliest block {st['earliest']}; refusing to store a gap")
            try:
                rec = fetch_height(call, h, st["earliest"], pool)
            except RpcError as e:
                store.log(ev="rpc_error", h=h, err=str(e)[:200])
                time.sleep(3)
                st = sync_state(call)
                continue
            except OSError as e:
                store.log(ev="net_error", h=h, err=str(e)[:200])
                time.sleep(3)
                continue
            store.add(h, rec)
            store.try_seal(h)
            cursor = h + 1


def status(root: Path, rpc: str) -> None:
    st = sync_state(http_rpc(rpc))
    sealed = Store(root).sealed()
    print(f"node head {st['head']:,} earliest {st['earliest']:,} syncing={st['syncing']}")
    if sealed:
        print(f"sealed shards {len(sealed)}; heights {sealed[0][0]:,}..{sealed[-1][1]:,}; behind head by {st['head'] - sealed[-1][1]:,} blocks")
    else:
        print("no sealed shards yet")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("run", "status", "verify"):
        p = sub.add_parser(n)
        p.add_argument("--root", required=True)
        if n != "verify":
            p.add_argument("--rpc", default=DEFAULT_RPC)
        if n == "run":
            p.add_argument("--start", type=int, default=None, help="first height (default: first full shard the node holds)")
            p.add_argument("--workers", type=int, default=16)
            p.add_argument("--allow-syncing", action="store_true",
                           help="archive the blocks the node has already applied while it is still catching up to the head")
    a = ap.parse_args(argv)
    if a.cmd == "run":
        run(Path(a.root), a.rpc, a.start, a.workers, allow_syncing=a.allow_syncing)
    elif a.cmd == "status":
        status(Path(a.root), a.rpc)
    else:
        r = verify(Path(a.root))
        print(json.dumps(r))
        return 1 if r["bad"] else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
