"""Re-check the escrow-unshield evidence from FastNEAR and NEAR archival RPC (keyless, standard library only).

data/raw/escrow/deliveries.csv has one row per native-NEAR delivery from intents.near to the three revenue
wallets (2026-07-07..2026-11-04). Collector rows come from two recurring fee collectors; escrow rows come from
single-use accounts funded by an exact-amount wNEAR transfer out of the Confidential Intents treasury
(PRIVATE_TREASURY_ACCOUNT_ID 51e8f94d...7cbe). This module re-pulls any delivery tx and funding tx by hash from
FastNEAR's transaction API (batches of 20, the API's limit) and checks amounts and parties against the CSV, and
re-reads the two archival total_supply values behind the net-issuance denominator.

Run:
  python3 -m pipeline.fetch_escrow supply                       # (re)write data/raw/escrow/issuance_reads.json
  python3 -m pipeline.fetch_escrow verify --sample 60 --seed 20261106
  python3 -m pipeline.fetch_escrow verify --all                 # every row (about 230 batched requests)
  python3 -m pipeline.fetch_escrow verify --hash <delivery_or_funding_tx_hash> ...

`verify` writes data/raw/escrow/verify_<label>.json (per-row checks plus a pass count) and also re-reads the two
total_supply values and compares them with issuance_reads.json. Exit status 1 if any check fails.
"""
from __future__ import annotations

import csv
import json
import random
import sys
import time

from .common import RAW, http_json, write_raw

TX_API = "https://tx.main.fastnear.com/v0/transactions"
BATCH = 20  # FastNEAR's per-request limit for tx_hashes
ARCHIVAL = ["https://archival-rpc.mainnet.fastnear.com", "https://archival-rpc.mainnet.near.org"]

CSV = RAW / "escrow" / "deliveries.csv"
SUPPLY = "escrow/issuance_reads.json"
# Window endpoints of the 30-day net-issuance denominator (first block at/after 2026-10-06 00:33 UTC; last block read
# for 2026-11-04 23:57 UTC). Net issuance per day = supply delta / elapsed days between the two block timestamps.
SUPPLY_BLOCKS = [218_718_000, 223_087_766]

INTENTS = "intents.near"
TREASURY = "51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe"
COLLECTOR_A = "5880ad2b362620fadf759cbceb1cd5737ce8c6ed7fb8e9942881e6731f9247dd"
COLLECTOR_B = "143f2bb439575c286f4f585163f0e5fb4e464f8ce57ec06ae80741407d3cfb31"
WNEAR = "nep141:wrap.near"
PAUSE = 1.0  # seconds between batched requests (keyless rate limit)


# ---------------------------------------------------------------- fetch

def rpc(method: str, params) -> dict:
    last = None
    for url in ARCHIVAL:
        try:
            r = http_json(url, body={"jsonrpc": "2.0", "id": "nfs", "method": method, "params": params}, retries=6)
            if "result" in r:
                return r["result"]
            last = r.get("error")
        except RuntimeError as exc:
            last = exc
    raise RuntimeError(f"archival rpc {method} failed on all endpoints: {last}")


def read_supply() -> list[dict]:
    out = []
    for h in SUPPLY_BLOCKS:
        hdr = rpc("block", {"block_id": h})["header"]
        out.append({"block": hdr["height"], "timestamp_ns": str(hdr["timestamp"]), "total_supply": hdr["total_supply"]})
    return out


def fetch_txs(hashes: list[str]) -> dict[str, dict]:
    """FastNEAR tx API, BATCH hashes per POST; returns {hash: tx}. Hashes the API does not know are absent."""
    hashes = list(dict.fromkeys(h for h in hashes if h))
    got: dict[str, dict] = {}
    for k in range(0, len(hashes), BATCH):
        r = http_json(TX_API, body={"tx_hashes": hashes[k:k + BATCH]}, retries=8, timeout=120)
        for t in r.get("transactions") or []:
            if t:
                got[t["transaction"]["hash"]] = t
        time.sleep(PAUSE)
    return got


# ---------------------------------------------------------------- checks

def events(tx: dict, executor: str = INTENTS):
    """(receipt_id, event) for every EVENT_JSON log emitted by `executor` in the tx."""
    for rc in tx["receipts"]:
        o = rc["execution_outcome"]["outcome"]
        if o["executor_id"] != executor:
            continue
        for line in o["logs"]:
            if line.startswith("EVENT_JSON:"):
                try:
                    yield rc["receipt"]["receipt_id"], json.loads(line[11:])
                except json.JSONDecodeError:
                    continue


def withdraw_source(row: dict) -> str | None:
    if row["path"] == "collector_a":
        return COLLECTOR_A
    if row["path"] == "collector_b":
        return COLLECTOR_B
    if row["single_use_account"]:
        return row["single_use_account"]
    if row["path_detail"].startswith("recurring:"):
        return row["path_detail"].split(":", 1)[1]
    return None


def check_delivery(row: dict, tx: dict | None) -> list[str]:
    """NEAR Transfer receipt intents.near -> wallet of amount_yocto at block_height, plus the matching native_withdraw."""
    if tx is None:
        return ["delivery tx not returned"]
    errs = []
    amt, wallet = int(row["amount_yocto"]), row["wallet"]
    hits = []
    for rc in tx["receipts"]:
        r = rc["receipt"]
        if r["receiver_id"] != wallet or r["predecessor_id"] != INTENTS:
            continue
        acts = r["receipt"].get("Action", {}).get("actions", [])
        dep = sum(int(a["Transfer"]["deposit"]) for a in acts if isinstance(a, dict) and "Transfer" in a)
        status = rc["execution_outcome"]["outcome"]["status"]
        if dep == amt and not (isinstance(status, dict) and "Failure" in status):
            hits.append(rc["execution_outcome"]["block_height"])
    if not hits:
        errs.append("no successful Transfer intents.near->wallet with amount_yocto")
    elif int(row["block_height"]) not in hits:
        errs.append(f"block mismatch: csv {row['block_height']} chain {hits}")
    src = withdraw_source(row)
    nw = [d for _, e in events(tx) if e.get("event") == "native_withdraw" for d in e.get("data", [])
          if d.get("receiver_id") == wallet and int(d.get("amount", -1)) == amt]
    if not nw:
        errs.append("no native_withdraw event to wallet with amount_yocto")
    elif src and not any(d.get("account_id") == src for d in nw):
        errs.append(f"native_withdraw source {[d.get('account_id') for d in nw]} != csv {src}")
    return errs


def check_funding(row: dict, tx: dict | None) -> list[str]:
    """dip4 transfer of wNEAR funder -> single_use_account (exact amount when exact_amount_flag=1)."""
    if tx is None:
        return ["funding tx not returned"]
    acct, funder, amt = row["single_use_account"], row["funder"], int(row["amount_yocto"])
    credits = [(rid, d) for rid, e in events(tx) if e.get("standard") == "dip4" and e.get("event") == "transfer"
               for d in e.get("data", []) if d.get("receiver_id") == acct and WNEAR in d.get("tokens", {})]
    if not credits:
        return ["no dip4 wNEAR transfer to the single-use account"]
    errs = []
    if not any(d.get("account_id") == funder for _, d in credits):
        errs.append(f"funder mismatch: chain {[d.get('account_id') for _, d in credits]} csv {funder}")
    if row["exact_amount_flag"] == "1" and not any(int(d["tokens"][WNEAR]) == amt for _, d in credits):
        errs.append("exact_amount_flag=1 but no transfer of exactly amount_yocto")
    if row["exact_amount_flag"] == "0" and any(int(d["tokens"][WNEAR]) == amt for _, d in credits):
        errs.append("exact_amount_flag=0 but an exact-amount transfer exists")
    if row["funding_receipt_id"] and not any(rid == row["funding_receipt_id"] for rid, _ in credits):
        errs.append("funding_receipt_id not among the crediting receipts")
    if row["path"] == "escrow_unshield" and funder != TREASURY:
        errs.append("escrow_unshield row with a non-treasury funder")
    return errs


# ---------------------------------------------------------------- commands

def load_rows() -> list[dict]:
    with open(CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pick_sample(rows: list[dict], n: int, seed: int) -> list[dict]:
    """Stratified: >=40% Oct-window BigQuery funding hops, 20% earlier sampled hops, 20% collector/other, rest unattributed."""
    rng = random.Random(seed)
    strata = [
        (max(20, int(n * 0.4)), [r for r in rows if r["funding_evidence"].startswith("bq_oct_scan")]),
        (int(n * 0.2), [r for r in rows if r["funding_tx_hash"] and not r["funding_evidence"].startswith("bq_oct_scan")]),
        (int(n * 0.2), [r for r in rows if not r["single_use_account"]]),
    ]
    used = sum(k for k, _ in strata)
    strata.append((max(0, n - used), [r for r in rows if r["single_use_account"] and not r["funding_tx_hash"]]))
    out = []
    for k, pool in strata:
        out += rng.sample(pool, min(k, len(pool)))
    return out


def verify(rows: list[dict], label: str, meta: dict) -> int:
    txs = fetch_txs([r["delivery_tx_hash"] for r in rows] + [r["funding_tx_hash"] for r in rows])
    results, n_ok, n_fund, n_fund_ok = [], 0, 0, 0
    for r in rows:
        errs = check_delivery(r, txs.get(r["delivery_tx_hash"]))
        ferrs = []
        if r["funding_tx_hash"]:
            n_fund += 1
            ferrs = check_funding(r, txs.get(r["funding_tx_hash"]))
            n_fund_ok += not ferrs
        ok = not errs and not ferrs
        n_ok += ok
        results.append({"delivery_tx_hash": r["delivery_tx_hash"], "funding_tx_hash": r["funding_tx_hash"],
                        "day": r["day"], "wallet": r["wallet"], "path": r["path"],
                        "funding_evidence": r["funding_evidence"], "ok": ok, "errors": errs + ferrs})
    committed = {x["block"]: x for x in json.loads((RAW / SUPPLY).read_text(encoding="utf-8"))["reads"]}
    supply = []
    for x in read_supply():
        c = committed.get(x["block"], {})
        supply.append({**x, "matches_committed": c.get("total_supply") == x["total_supply"]
                       and c.get("timestamp_ns") == x["timestamp_ns"]})
    summary = {"rows": len(rows), "rows_ok": n_ok, "funding_hops": n_fund, "funding_hops_ok": n_fund_ok,
               "oct_bq_funding_hops": sum(1 for r in rows if r["funding_evidence"].startswith("bq_oct_scan")),
               "supply_reads_ok": sum(s["matches_committed"] for s in supply)}
    write_raw(f"escrow/verify_{label}.json", {**meta, "summary": summary, "supply": supply, "rows": results},
              f"{TX_API} (batches of {BATCH}) + archival rpc block; checks in pipeline/fetch_escrow.py")
    print(json.dumps(summary))
    for x in results:
        if not x["ok"]:
            print("FAIL", x["delivery_tx_hash"], x["errors"], file=sys.stderr)
    return 0 if n_ok == len(rows) and summary["supply_reads_ok"] == len(SUPPLY_BLOCKS) else 1


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("supply", "verify"):
        print(__doc__)
        return 2
    if argv[0] == "supply":
        reads = read_supply()
        (t0, s0), (t1, s1) = [(int(x["timestamp_ns"]), int(x["total_supply"])) for x in reads]
        write_raw(SUPPLY, {"reads": reads, "net_issuance_near_per_day": f"{(s1 - s0) / 10**24 / ((t1 - t0) / 86400e9):.4f}"},
                  f"archival rpc block {{block_id}} for {SUPPLY_BLOCKS} ({ARCHIVAL[0]})")
        print(json.dumps(reads))
        return 0
    rows = load_rows()
    args = argv[1:]
    if "--all" in args:
        return verify(rows, "all", {"mode": "all"})
    if "--hash" in args:
        hs = set(args[args.index("--hash") + 1:])
        sel = [r for r in rows if r["delivery_tx_hash"] in hs or r["funding_tx_hash"] in hs]
        if not sel:
            print("no deliveries.csv row has any of those hashes", file=sys.stderr)
            return 1
        return verify(sel, "hash", {"mode": "hash", "hashes": sorted(hs)})
    n = int(args[args.index("--sample") + 1]) if "--sample" in args else 60
    seed = int(args[args.index("--seed") + 1]) if "--seed" in args else 20261106
    return verify(pick_sample(rows, n, seed), "sample", {"mode": "sample", "n": n, "seed": seed})


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
