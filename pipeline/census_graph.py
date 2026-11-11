"""Native-NEAR transfer edges from the node census, for labelling the unlabelled top-100 receivers.

Why this exists: H1b is inconclusive only because 80 of the top-100 NEAR receivers carry no citable label. The
census (every block, every transaction result, from our own node) shows where those accounts send their NEAR.
An account whose outflow goes almost entirely into already-labelled exchange accounts is on the exchange's side of
the sweep, by the same logic as tiers 2-3 in PREREG-ADDENDUM. This module builds the edge list; pipeline/hub_trail.py
turns it into labels with the rules written in docs/hub-trail-method.md.

An edge is a successful receipt with a Transfer action: predecessor -> receiver, summed per shard of 1,000 blocks.
Excluded: receipts from "system" (gas refunds), failed receipts, NEAR attached to function calls (PREREG: native = TRANSFER).

Run (on the machine with the census):
    python3 -m pipeline.census_graph edges --root /data/near/archive --interest interest.json --out /data/near/edges --workers 24
    python3 -m pipeline.census_graph merge --edges /data/near/edges --out /data/near/edges_merged.json.gz
interest.json is a list of account ids. Per shard we keep every edge that touches an interest account, plus every
edge sent by an account that sent to an interest account in that shard (so a sender's total outflow can be judged).
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

from pipeline.near_collect import list_sealed, name, read_shard

YOCTO = 10**24


def _failed(status) -> bool:
    return isinstance(status, dict) and "Failure" in status


def shard_edges(blocks, interest: frozenset) -> list[list]:
    """blocks: iterable of {"h", "b"} census rows -> [[from, to, n, yocto], ...] restricted as described above."""
    e: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    for d in blocks:
        b = d["b"]
        if not b:
            continue
        for t in b["txs"].values():
            ok = {o["id"]: not _failed(o["outcome"]["status"]) for o in t.get("receipts_outcome", [])}
            for r in t.get("receipts", []):
                pred = r["predecessor_id"]
                if pred == "system" or not ok.get(r["receipt_id"], False):
                    continue
                act = (r.get("receipt") or {}).get("Action")
                if not act:
                    continue
                for a in act["actions"]:
                    if isinstance(a, dict) and "Transfer" in a:
                        amt = int(a["Transfer"]["deposit"])
                        if amt:
                            x = e[(pred, r["receiver_id"])]
                            x[0] += 1
                            x[1] += amt
    into = {a for (a, b) in e if b in interest}
    return [[a, b, n, y] for (a, b), (n, y) in e.items() if a in interest or b in interest or a in into]


def _work(args):
    root, a, b, interest, out = args
    dst = Path(out) / f"{name(a, b)}.json.gz"
    if dst.exists():
        return 0
    rows = shard_edges(read_shard(Path(root), a, b), interest)
    tmp = dst.with_suffix(".tmp")
    tmp.write_bytes(gzip.compress(json.dumps(rows, separators=(",", ":")).encode(), 6, mtime=0))
    tmp.rename(dst)
    return len(rows)


def edges_cmd(root: Path, interest_path: Path, out: Path, workers: int) -> int:
    interest = frozenset(json.loads(Path(interest_path).read_text()))
    Path(out).mkdir(parents=True, exist_ok=True)
    jobs = [(str(root), a, b, interest, str(out)) for a, b in list_sealed(root)]
    with Pool(workers) as p:
        n = sum(p.imap_unordered(_work, jobs))
    print(f"{len(jobs)} shards, {n} new edge rows")
    return 0


def merge_cmd(edges: Path, out: Path) -> int:
    m: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    files = sorted(Path(edges).glob("*.json.gz"))
    for f in files:
        for a, b, n, y in json.loads(gzip.decompress(f.read_bytes())):
            x = m[(a, b)]
            x[0] += n
            x[1] += y
    rows = sorted(([a, b, n, y] for (a, b), (n, y) in m.items()), key=lambda r: -r[3])
    first, last = files[0].name[:12], files[-1].name[13:25]
    doc = {"first_height": int(first), "last_height": int(last), "shards": len(files), "edges": rows}
    Path(out).write_bytes(gzip.compress(json.dumps(doc, separators=(",", ":")).encode(), 6, mtime=0))
    print(f"{len(files)} shards -> {len(rows)} edges ({first}..{last})")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("edges")
    p.add_argument("--root", required=True)
    p.add_argument("--interest", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=16)
    p = sub.add_parser("merge")
    p.add_argument("--edges", required=True)
    p.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "edges":
        return edges_cmd(Path(a.root), Path(a.interest), Path(a.out), a.workers)
    return merge_cmd(Path(a.edges), Path(a.out))


if __name__ == "__main__":
    sys.exit(main())
