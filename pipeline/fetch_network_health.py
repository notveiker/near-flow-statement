"""Validator-set health from chain state: stake, decentralisation and block production per epoch.

Reads the `validators` RPC for the current epoch and walks back one epoch at a time (the block before an epoch's start
belongs to the previous epoch). A node keeps the last few dozen epochs, so run it where a node is, with
NEAR_RPC=http://127.0.0.1:3030 (a public endpoint works too but is rate limited).

Nakamoto coefficient here is the smallest number of validators whose stake exceeds one third of the total, the share
that can halt finality.

    NEAR_RPC=http://127.0.0.1:3030 python3 -m pipeline.fetch_network_health --epochs 28
Output: data/raw/rpc/validators_epochs.json
"""
from __future__ import annotations

import argparse
import sys

from .common import YOCTO, utc_now, write_raw
from .fetch_intents_holdings import FAST, GAP, rpc


def epoch_row(v: dict, ts_ns: int | None) -> dict:
    cur = v["current_validators"]
    stakes = sorted((int(x["stake"]) for x in cur), reverse=True)
    tot = sum(stakes)
    run, k = 0, 0
    for s in stakes:
        run += s
        k += 1
        if run * 3 > tot:
            break
    exp = sum(x["num_expected_blocks"] for x in cur)
    prod = sum(x["num_produced_blocks"] for x in cur)
    hhi = sum((s / tot) ** 2 for s in stakes)
    return {"epoch_start_height": v["epoch_start_height"], "timestamp_ns": ts_ns, "validators": len(cur),
            "total_stake_near": tot / YOCTO, "top1_share": stakes[0] / tot, "top10_share": sum(stakes[:10]) / tot,
            "nakamoto_third": k, "hhi": hhi, "block_uptime": prod / exp if exp else None,
            "min_stake_near": stakes[-1] / YOCTO}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--epochs", type=int, default=28)
    a = ap.parse_args(argv)
    rows = []
    v = rpc(FAST, "validators", [None], gap=GAP)["result"]
    for _ in range(a.epochs):
        start = v["epoch_start_height"]
        hdr = None
        for h in range(start, start + 8):  # an epoch's first height can be a skipped one
            d = rpc(FAST, "block", {"block_id": h}, gap=GAP)
            if "result" in d:
                hdr = d["result"]["header"]
                break
        if hdr is None:
            break
        rows.append(epoch_row(v, hdr["timestamp"]))
        d = rpc(FAST, "validators", [start - 1], gap=GAP)
        if "error" in d:
            print("stopped:", str(d["error"])[:120], file=sys.stderr)
            break
        v = d["result"]
    rows.sort(key=lambda r: r["epoch_start_height"])
    write_raw("rpc/validators_epochs.json", {"asof_utc": utc_now(), "epochs": rows,
              "note": "current epoch is partial: block_uptime covers blocks produced so far"}, f"{FAST} validators")
    print(len(rows), "epochs; latest", rows[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
