"""What the chain is used for, counted from the node census: contracts by share of transactions and of gas, gasless relayed
transactions, Chain Signatures requests, and stablecoin transfers (counts and USD amount from NEP-141 events).

A transaction's target is its receiver, or the inner receiver when it is a delegate (relayed, gasless) transaction.
Gas is attributed to the account that executed each receipt, so a contract pays for the work done inside it.

    python3 -m pipeline.census_usage --root /data/near/archive --out data/derived/census_usage.json --workers 48
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

from pipeline.near_collect import list_sealed, read_shard

STABLES = {
    "usdt.tether-token.near": ("USDT", 6),
    "17208628f84f5d6ad33f0da3bbbeb27ffcb398eac501a31bd6ad2011e36133a1": ("USDC", 6),
}
FOCUS = ("intents.near", "v1.signer")
TOP = 40


def _failed(st) -> bool:
    return isinstance(st, dict) and "Failure" in st


def target_of(tx: dict) -> tuple[str, bool, str | None]:
    """(effective receiver, is_delegate, first method name)."""
    recv = tx["receiver_id"]
    acts = tx.get("actions", [])
    delegate = False
    for a in acts:
        if isinstance(a, dict) and "Delegate" in a:
            delegate = True
            da = a["Delegate"]["delegate_action"]
            recv = da.get("receiver_id", recv)
            acts = da.get("actions", [])
            break
    for a in acts:
        if isinstance(a, dict) and "FunctionCall" in a:
            return recv, delegate, a["FunctionCall"]["method_name"]
    return recv, delegate, None


def shard_usage(blocks) -> dict:
    tx_by: Counter = Counter()
    ok_by: Counter = Counter()
    gas_by: Counter = Counter()
    burn_by: Counter = Counter()
    methods: dict[str, Counter] = {k: Counter() for k in FOCUS}
    out = Counter()
    stable: dict[str, Counter] = {k: Counter() for k in STABLES}
    for d in blocks:
        b = d["b"]
        if not b:
            continue
        out["blocks"] += 1
        for t in b["txs"].values():
            recv, delegate, method = target_of(t["transaction"])
            ok = not _failed(t.get("status"))
            out["txs"] += 1
            out["ok_txs"] += ok
            out["delegate_txs"] += delegate
            tx_by[recv] += 1
            ok_by[recv] += ok
            if recv in methods and method:
                methods[recv][method] += 1
            for o in t.get("receipts_outcome", []):
                oc = o["outcome"]
                ex = oc["executor_id"]
                gas_by[ex] += oc["gas_burnt"]
                burn_by[ex] += int(oc["tokens_burnt"])
                out["gas"] += oc["gas_burnt"]
                if ex in stable and not _failed(oc["status"]):
                    for lg in oc["logs"]:
                        if not lg.startswith("EVENT_JSON:"):
                            continue
                        try:
                            e = json.loads(lg[11:])
                        except json.JSONDecodeError:
                            continue
                        if e.get("standard") == "nep141" and e.get("event") == "ft_transfer":
                            for x in e.get("data", []):
                                stable[ex]["transfers"] += 1
                                stable[ex]["raw"] += int(x.get("amount", 0))
    return {"out": dict(out), "tx_by": tx_by, "ok_by": ok_by, "gas_by": gas_by, "burn_by": burn_by,
            "methods": methods, "stable": {k: dict(v) for k, v in stable.items()}}


def _work(args):
    root, a, b = args
    return shard_usage(read_shard(Path(root), a, b))


def merge(parts: list[dict]) -> dict:
    tot: dict = {"out": Counter(), "tx_by": Counter(), "ok_by": Counter(), "gas_by": Counter(), "burn_by": Counter(),
                 "methods": {k: Counter() for k in FOCUS}, "stable": {k: Counter() for k in STABLES}}
    for p in parts:
        tot["out"].update(p["out"])
        for k in ("tx_by", "ok_by", "gas_by", "burn_by"):
            tot[k].update(p[k])
        for k in FOCUS:
            tot["methods"][k].update(p["methods"][k])
        for k in STABLES:
            tot["stable"][k].update(p["stable"][k])
    return tot


def report(tot: dict, first: int, last: int) -> dict:
    o = tot["out"]
    txs, gas = o["txs"], o["gas"]
    contracts = [{"account": a, "txs": n, "tx_share": n / txs, "ok_share": tot["ok_by"][a] / n,
                  "gas_share": tot["gas_by"][a] / gas if gas else 0.0} for a, n in tot["tx_by"].most_common(TOP)]
    burners = [{"account": a, "gas_share": g / gas, "burn_near": tot["burn_by"][a] / 1e24} for a, g in tot["gas_by"].most_common(TOP)]
    stable = {STABLES[k][0]: {"transfers": v["transfers"], "usd": v["raw"] / 10 ** STABLES[k][1]} for k, v in tot["stable"].items()}
    return {
        "first_height": first, "last_height": last, "blocks": o["blocks"], "txs": txs, "ok_share": o["ok_txs"] / txs if txs else None,
        "delegate_share": o["delegate_txs"] / txs if txs else None, "contracts": contracts, "gas_burners": burners,
        "methods": {k: dict(v.most_common(12)) for k, v in tot["methods"].items()}, "stablecoins": stable,
        "note": "target = inner receiver for delegate (relayed) transactions; gas share is by executing account",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args(argv)
    sealed = list_sealed(Path(a.root))
    with Pool(a.workers) as p:
        parts = p.map(_work, [(a.root, x, y) for x, y in sealed])
    doc = report(merge(parts), sealed[0][0], sealed[-1][1])
    Path(a.out).write_text(json.dumps(doc, separators=(",", ":")) + "\n")
    print(doc["blocks"], "blocks,", doc["txs"], "txs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
