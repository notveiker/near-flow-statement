"""Hourly activity on the NEAR Intents contract and on the chain as a whole, from the node census.

Per UTC hour: blocks, transactions (and how many succeeded), distinct transaction signers, and from the logs that
`intents.near` emits: `intents_executed` events and the intents inside them (each carries an account id), `token_diff`
events (public-mode swaps), deposits (`mt_mint`) and withdrawals (`mt_burn`), plus distinct accounts seen in executed
intents. Counted straight from receipts, so no aggregator sits between the chain and the number.

    python3 -m pipeline.census_summary --root /data/near/archive --out data/derived/census_hourly.json --workers 48
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

from pipeline.near_collect import list_sealed, read_shard

INTENTS = "intents.near"


def _hour(ns: int) -> str:
    import datetime as dt
    return dt.datetime.fromtimestamp(ns / 1e9, dt.timezone.utc).strftime("%Y-%m-%dT%H")


def shard_summary(blocks) -> dict:
    hrs: dict[str, dict] = defaultdict(lambda: {"blocks": 0, "txs": 0, "ok_txs": 0, "signers": set(), "executed_events": 0, "intents": 0,
                                                "token_diff": 0, "deposits": 0, "withdrawals": 0, "accounts": set(), "intents_txs": 0})
    for d in blocks:
        b = d["b"]
        if not b:
            continue
        hdr = (b.get("block") or {}).get("header") or {}
        if not hdr.get("timestamp"):
            continue
        a = hrs[_hour(int(hdr["timestamp"]))]
        a["blocks"] += 1
        for t in b["txs"].values():
            a["txs"] += 1
            st = t.get("status")
            a["ok_txs"] += 0 if (isinstance(st, dict) and "Failure" in st) else 1
            a["signers"].add(t["transaction"]["signer_id"])
            touched = False
            for o in t.get("receipts_outcome", []):
                oc = o["outcome"]
                if oc["executor_id"] != INTENTS:
                    continue
                touched = True
                for lg in oc["logs"]:
                    if not lg.startswith("EVENT_JSON:"):
                        continue
                    try:
                        e = json.loads(lg[11:])
                    except json.JSONDecodeError:
                        continue
                    ev = e.get("event")
                    if ev == "intents_executed":
                        a["executed_events"] += 1
                        for x in e.get("data", []):
                            a["intents"] += 1
                            if isinstance(x, dict) and x.get("account_id"):
                                a["accounts"].add(x["account_id"])
                    elif ev == "token_diff":
                        a["token_diff"] += len(e.get("data", []))
                    elif ev == "mt_mint":
                        a["deposits"] += 1
                    elif ev == "mt_burn":
                        a["withdrawals"] += 1
            a["intents_txs"] += touched
    return {h: {**v, "signers": sorted(v["signers"]), "accounts": sorted(v["accounts"])} for h, v in hrs.items()}


def _work(args):
    root, a, b = args
    return shard_summary(read_shard(Path(root), a, b))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args(argv)
    jobs = [(a.root, x, y) for x, y in list_sealed(Path(a.root))]
    with Pool(a.workers) as p:
        parts = p.map(_work, jobs)
    tot: dict[str, dict] = {}
    for part in parts:
        for h, v in part.items():
            t = tot.setdefault(h, {"blocks": 0, "txs": 0, "ok_txs": 0, "signers": set(), "executed_events": 0, "intents": 0, "token_diff": 0,
                                   "deposits": 0, "withdrawals": 0, "accounts": set(), "intents_txs": 0})
            for k, x in v.items():
                if k in ("signers", "accounts"):
                    t[k] |= set(x)
                else:
                    t[k] += x
    window = {"distinct_signers": len(set().union(*(t["signers"] for t in tot.values()))),
              "distinct_intents_accounts": len(set().union(*(t["accounts"] for t in tot.values())))}
    rows = [{"hour": h, **{k: (len(v) if isinstance(v, set) else v) for k, v in t.items()}} for h, t in sorted(tot.items())]
    first, last = list_sealed(Path(a.root))[0][0], list_sealed(Path(a.root))[-1][1]
    Path(a.out).write_text(json.dumps({"first_height": first, "last_height": last, "window": window, "hours": rows}, separators=(",", ":")) + "\n")
    print(len(rows), "hours,", sum(r["blocks"] for r in rows), "blocks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
