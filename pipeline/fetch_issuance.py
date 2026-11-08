"""Fetch the H1a gross-issuance evidence from archival NEAR RPC into data/raw/rpc/epoch_issuance.json.

PREREG.md: gross issuance is "measured from epoch-boundary block headers". No header field reports the amount
minted, but total_supply obeys, for every block b:
    supply(b) = supply(prev(b)) + minted(b) - sum(chunk.balance_burnt for chunks with height_included == b)
and minted(b) != 0 only at the first block of an epoch. So for each epoch start s the script stores both headers
and the burnt sum, and mint(s) = supply(s) - supply(prev(s)) + burnt(s).

Epoch starts: seed epoch from `validators {epoch_id}`; then previous start + epoch_length, verified on chain (the
block carries the expected epoch_id and its predecessor a different one); `validators {epoch_id}` otherwise.

  python3 -m pipeline.fetch_issuance              # full walk (~600 block reads), writes the raw file + manifest
  python3 -m pipeline.fetch_issuance --verify 10  # re-read 10 random committed epochs + endpoints, compare, no write

Standard library only. Polite: one request per RPC_PACE seconds (default 0.5); waits out HTTP 429 (FastNEAR's
free tier is rate-limited). archival-rpc.mainnet.near.org is deprecated (answers 429 to everything) and not used.

Environment:
  NEAR_ARCHIVAL_RPC  archival JSON-RPC endpoint to read (default https://archival-rpc.mainnet.fastnear.com). It may be
                     a keyed URL (a key in the user-info, the path or the query). Requests use it exactly as given, but
                     only its scheme and host (`recorded_rpc()`) are written to data/raw/rpc/epoch_issuance.json and
                     data/MANIFEST.json, which are committed. A provider that puts the key in the host name itself
                     (an account-specific sub-domain) cannot be recorded safely: refresh with a keyless endpoint.
  RPC_PACE           seconds between requests (default 0.5)
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request

from .common import USER_AGENT, endpoint_origin, read_raw, write_raw

RPC = os.environ.get("NEAR_ARCHIVAL_RPC", "https://archival-rpc.mainnet.fastnear.com")


def recorded_rpc() -> str:
    """The endpoint as it may be written to a committed file: scheme and host only (see the module docstring)."""
    return endpoint_origin(RPC)


PACE = float(os.environ.get("RPC_PACE", "0.5"))
WINDOW_FIRST, WINDOW_LAST = 210_238_034, 223_088_015  # first block of 2026-08-07 UTC, last block of 2026-11-04 UTC
ENDPOINTS = (210_238_033, 223_088_015)
STOP_AFTER = 223_088_016            # walk until one epoch starts after the window (its mint pays the straddler)
V87_START, V86_LAST_START = 223_012_337, 222_969_137
TREASURY_CHECKS = (210_441_134, 211_089_134)
IDENTITY_CHECKS = (213_000_123, 223_050_001)
FIELDS = ["start_height", "start_hash", "epoch_id", "start_timestamp_ns", "start_total_supply", "start_burnt",
          "prev_height", "prev_hash", "prev_total_supply", "mint"]
_last = [0.0]


def rpc(method: str, params, budget_s: float = 4 * 3600) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": "nfs", "method": method, "params": params}).encode()
    waited, i = 0.0, 0
    while True:
        dt = _last[0] + PACE - time.time()
        if dt > 0:
            time.sleep(dt)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(RPC, body, {"Content-Type": "application/json", "User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=90) as r:
                env = json.load(r)
            if "result" in env:
                return env["result"]
            err = json.dumps(env.get("error"))
            if "UNKNOWN_EPOCH" in err and i < 10:  # load-balanced backends intermittently miss an epoch
                i += 1
                time.sleep(1)
                continue
            raise LookupError(err)
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and waited < budget_s:
                s = min(120.0, 15.0 * (1 + min(i, 7)))
                time.sleep(s)
                waited += s
                i += 1
                continue
            if exc.code >= 500 and i < 8:
                i += 1
                time.sleep(2 * i)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            i += 1
            if i >= 8:
                raise RuntimeError(f"rpc {method}: {exc}") from exc
            time.sleep(2 * i)


def block(block_id) -> dict:
    return rpc("block", {"block_id": block_id})


def burnt_in(b: dict) -> int:
    h = b["header"]["height"]
    return sum(int(c["balance_burnt"]) for c in b["chunks"] if c["height_included"] == h)


def epoch_row(start: dict, prev: dict) -> list:
    s, p = start["header"], prev["header"]
    mint = int(s["total_supply"]) - int(p["total_supply"]) + burnt_in(start)
    return [s["height"], s["hash"], s["epoch_id"], int(s["timestamp_nanosec"]), s["total_supply"],
            str(burnt_in(start)), p["height"], p["hash"], p["total_supply"], str(mint)]


def walk(epoch_length: int) -> list[list]:
    eid = block(WINDOW_FIRST)["header"]["epoch_id"]
    rows, prev_start = [], None
    while True:
        start = None
        if prev_start is not None:
            try:
                cand = block(prev_start + epoch_length)
                if cand["header"]["epoch_id"] == eid:
                    start = cand
            except LookupError:
                start = None
        if start is not None:
            prev = block(start["header"]["prev_hash"])
            if prev["header"]["epoch_id"] == eid:
                start = None
        if start is None:
            start = block(rpc("validators", {"epoch_id": eid})["epoch_start_height"])
            prev = block(start["header"]["prev_hash"])
        assert start["header"]["epoch_id"] == eid and prev["header"]["epoch_id"] != eid
        rows.append(epoch_row(start, prev))
        prev_start = start["header"]["height"]
        print(f"{len(rows):3d} start={prev_start}", flush=True)
        if prev_start > STOP_AFTER:
            return rows
        eid = start["header"]["next_epoch_id"]


def protocol_config(h: int) -> dict:
    c = rpc("EXPERIMENTAL_protocol_config", {"block_id": h})
    keep = {k: c.get(k) for k in ("protocol_version", "max_inflation_rate", "protocol_reward_rate", "epoch_length",
                                  "num_blocks_per_year", "protocol_treasury_account")}
    keep["burnt_gas_reward"] = c.get("runtime_config", {}).get("transaction_costs", {}).get("burnt_gas_reward")
    return keep


def view(acct: str, h: int) -> dict:
    return rpc("query", {"request_type": "view_account", "block_id": h, "account_id": acct})


def fetch() -> dict:
    cfgs = {str(h): protocol_config(h) for h in (WINDOW_FIRST, V86_LAST_START, V87_START, ENDPOINTS[1])}
    rows = walk(cfgs[str(WINDOW_FIRST)]["epoch_length"])
    ends = {}
    for h in ENDPOINTS:
        hd = block(h)["header"]
        ends[str(h)] = {k: hd[k] for k in ("hash", "timestamp_nanosec", "total_supply")}
    ident = []
    for h in IDENTITY_CHECKS:
        b = block(h)
        p = block(b["header"]["prev_hash"])
        ds = int(b["header"]["total_supply"]) - int(p["header"]["total_supply"])
        ident.append({"height": h, "prev": p["header"]["height"], "d_supply": str(ds),
                      "minus_burnt_in": str(-burnt_in(b)), "exact": ds == -burnt_in(b)})
    by_h = {r[0]: r for r in rows}
    tre = []
    for h in TREASURY_CHECKS:
        r = by_h[h]
        a, b = view("treasury.near", r[6]), view("treasury.near", h)
        tre.append({"start_height": h, "prev_height": r[6], "mint": r[9],
                    "treasury_delta": str(int(b["amount"]) + int(b["locked"]) - int(a["amount"]) - int(a["locked"])),
                    "treasury_before": [a["amount"], a["locked"]], "treasury_after": [b["amount"], b["locked"]]})
    mi = cfgs[str(ENDPOINTS[1])]["max_inflation_rate"]
    return {"source": f"{recorded_rpc()} JSON-RPC `block` (and `validators` by epoch_id where the arithmetic start did not "
                      "verify); written by pipeline/fetch_issuance.py",
            "method": "mint(s) = total_supply(s) - total_supply(prev(s)) + sum(chunk.balance_burnt, height_included "
                      "== s) for each epoch-start block s; supply(b) = supply(prev) + minted(b) - burnt(b) holds "
                      "exactly on non-boundary blocks (see identity_checks)",
            "epoch_fields": FIELDS, "epochs": rows,
            "window": {"first_block": WINDOW_FIRST, "last_block": WINDOW_LAST,
                       "start_utc": "2026-08-07T00:00:00Z", "end_utc": "2026-11-05T00:00:00Z"},
            "endpoints": ends,
            "protocol": {"epoch_length": cfgs[str(WINDOW_FIRST)]["epoch_length"],
                         "num_seconds_per_year": cfgs[str(WINDOW_FIRST)]["num_blocks_per_year"],
                         "max_inflation_rate": mi, "v87_first_epoch_start": V87_START, "protocol_config": cfgs},
            "identity_checks": ident, "treasury_split_checks": tre}


def verify(n: int, seed: int) -> int:
    d = read_raw("rpc/epoch_issuance.json")
    rows = [dict(zip(d["epoch_fields"], r)) for r in d["epochs"]]
    sample = random.Random(seed).sample(rows, min(n, len(rows)))
    bad = 0
    for r in sample:
        s, p = block(r["start_height"]), block(r["prev_height"])
        got = dict(zip(FIELDS, epoch_row(s, p)))
        ok = got == r and s["header"]["prev_hash"] == r["prev_hash"]
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} epoch start {r['start_height']} mint {int(r['mint']) / 1e24:,.6f}"
              + ("" if ok else f"  committed={r} reread={got}"))
    for h, e in d["endpoints"].items():
        hd = block(int(h))["header"]
        ok = all(hd[k] == e[k] for k in e)
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} endpoint {h} total_supply {int(e['total_supply']) / 1e24:,.6f}")
    print("verify: PASS" if not bad else f"verify: {bad} mismatch(es)")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", type=int, metavar="N", help="re-read N random committed epochs and compare")
    ap.add_argument("--seed", type=int, default=None, help="RNG seed for --verify (default: random)")
    a = ap.parse_args(argv)
    if a.verify:
        return verify(a.verify, a.seed if a.seed is not None else random.SystemRandom().randrange(1 << 30))
    recorded_rpc()  # fail now, not after a walk of ~600 block reads, if NEAR_ARCHIVAL_RPC is not an absolute http(s) URL
    obj = fetch()
    write_raw("rpc/epoch_issuance.json", obj, f"{recorded_rpc()} block headers at epoch boundaries (pipeline/fetch_issuance.py)")
    print(f"wrote data/raw/rpc/epoch_issuance.json ({len(obj['epochs'])} epochs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
