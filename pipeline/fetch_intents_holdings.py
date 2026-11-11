"""What the NEAR Intents contract holds, read from chain state (not from an aggregator).

`intents.near` is a NEP-245 multi-token contract: every asset a user has deposited is a token id such as
`nep141:wrap.near` with a total supply held inside the contract. This module reads those supplies with `mt_tokens` and
`mt_supply` view calls for the assets in the keyless 1Click token list, prices them with the keyless 1Click token list, and writes a snapshot. `history` repeats the
read at month starts from archival state for the largest tokens, at the archival node's published rate.

    python3 -m pipeline.fetch_intents_holdings snapshot                 # current state, public RPC
    python3 -m pipeline.fetch_intents_holdings history --from 2025-01    # archival reads, one request per 3 s

Outputs: data/raw/intents/holdings_snapshot.json, data/raw/intents/holdings_history.json.
Prices are today's 1Click prices applied to every date, so the history is a quantity series valued at one price list.
That is stated in the output file and wherever the series is shown.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from .common import RAW, USER_AGENT, http_json, utc_now, write_raw

CONTRACT = "intents.near"
FAST = os.environ.get("NEAR_RPC", "https://free.rpc.fastnear.com")  # set NEAR_RPC=http://127.0.0.1:3030 on a machine with a node
ARCHIVAL = "https://archival-rpc.mainnet.fastnear.com"  # the near.org archival host is deprecated and answers 429 to everything
TOKENS_URL = "https://1click.chaindefuser.com/v0/tokens"
GAP = 0.0 if "127.0.0.1" in FAST or "localhost" in FAST else 1.0
ARCHIVAL_GAP_S = 3.0  # conservative on the free tier


def rpc(url: str, method: str, params: dict, retries: int = 8, gap: float = 0.0) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, body, {"Content-Type": "application/json", "User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.load(r)
            if gap:
                time.sleep(gap)
            return d
        except urllib.error.HTTPError as e:
            if e.code in (400, 422):  # a skipped height or unknown block: the body is a JSON-RPC error, not a transport failure
                try:
                    return json.loads(e.read())
                except json.JSONDecodeError:
                    pass
            last = e
            wait = e.headers.get("Retry-After") if e.code == 429 else None  # honour the server's own back-off
            time.sleep(min(float(wait), 300) if wait and wait.isdigit() else max(gap, 5) * (i + 1))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last = e
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"rpc {method} failed: {last}")


def view(url: str, method: str, args: dict, block_id=None, gap: float = 0.0, account: str = CONTRACT):
    p = {"request_type": "call_function", "account_id": account, "method_name": method,
         "args_base64": base64.b64encode(json.dumps(args).encode()).decode()}
    p.update({"block_id": block_id} if block_id is not None else {"finality": "final"})
    d = rpc(url, "query", p, gap=gap)
    if "error" in d or "error" in d.get("result", {}):
        raise RuntimeError(f"{method}@{block_id}: {d.get('error') or d['result']['error']}")
    return json.loads(bytes(d["result"]["result"]))


def block_at(url: str, height=None, gap: float = 0.0) -> dict:
    p = {"block_id": height} if height is not None else {"finality": "final"}
    d = rpc(url, "block", p, gap=gap)
    if "error" in d:
        raise RuntimeError(str(d["error"]))
    return d["result"]["header"]


def token_ids(url: str, block_id=None) -> list[str]:
    out, i = [], 0
    while True:
        page = view(url, "mt_tokens", {"from_index": str(i), "limit": 200}, block_id)
        out += [t["token_id"] for t in page]
        if len(page) < 200:
            return out
        i += 200


def snapshot() -> dict:
    h = block_at(FAST)
    height = h["height"]
    listing = {t["assetId"]: t for t in http_json(TOKENS_URL)}
    ids = [t for t in listing if t.startswith(("nep141:", "nep245:"))]
    rows = []
    for tid in ids:
        try:
            sup = int(view(FAST, "mt_supply", {"token_id": tid}, None, gap=GAP))
        except RuntimeError as e:
            print(f"skip {tid}: {str(e)[:80]}", file=sys.stderr, flush=True)
            continue
        print(f"{len(rows) + 1}/{len(ids)} {tid[:50]}", file=sys.stderr, flush=True)
        meta = listing.get(tid)
        row = {"token_id": tid, "supply_raw": str(sup), "listed": meta is not None}
        if meta:
            usd = sup / 10 ** meta["decimals"] * (meta.get("price") or 0)
            row.update({"symbol": meta["symbol"], "chain": meta["blockchain"], "decimals": meta["decimals"],
                        "price_usd": meta.get("price"), "amount": sup / 10 ** meta["decimals"], "value_usd": usd})
        rows.append(row)
    rows.sort(key=lambda r: -r.get("value_usd", 0))
    doc = {"asof_utc": utc_now(), "contract": CONTRACT, "block_height": height, "block_timestamp_ns": h["timestamp"],
           "token_count": len(ids), "priced_count": sum(r["listed"] for r in rows), "unlisted_ids_not_read": "the contract holds thousands of further token ids (the paged mt_tokens listing exceeds 2,600); only assets in the 1Click list can be priced, so only those are read",
           "total_value_usd": sum(r.get("value_usd", 0) for r in rows),
           "price_source": TOKENS_URL, "tokens": rows,
           "note": "supply is mt_supply from intents.near at finality final, read over a few minutes starting at block_height; value uses the price in the 1Click token list at asof_utc; unlisted tokens are not valued"}
    write_raw("intents/holdings_snapshot.json", doc, f"{FAST} mt_tokens/mt_supply on {CONTRACT} at block {height}; {TOKENS_URL}")
    return doc


def month_starts(first: str) -> list[datetime]:
    y, m = map(int, first.split("-"))
    now = datetime.now(timezone.utc)
    out = []
    while (y, m) <= (now.year, now.month):
        out.append(datetime(y, m, 1, tzinfo=timezone.utc))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def height_at(url: str, target_ns: int, lo: int, hi: int, gap: float, tol_s: int = 1800) -> tuple[int, int]:
    """Height whose timestamp is within tol_s of target, by interpolation on timestamps (a few archival calls)."""
    hl, hh = block_at(url, lo, gap), block_at(url, hi, gap)
    a, b = (lo, hl["timestamp"]), (hi, hh["timestamp"])
    for _ in range(8):
        guess = int(a[0] + (b[0] - a[0]) * (target_ns - a[1]) / (b[1] - a[1]))
        g = block_at(url, guess, gap)
        if abs(g["timestamp"] - target_ns) < tol_s * 10**9:
            return g["height"], g["timestamp"]
        if g["timestamp"] < target_ns:
            a = (g["height"], g["timestamp"])
        else:
            b = (g["height"], g["timestamp"])
    return g["height"], g["timestamp"]


def history(first: str, top: int, gap: float) -> dict:
    snap = json.loads((RAW / "intents" / "holdings_snapshot.json").read_text())
    tokens = [t for t in snap["tokens"] if t.get("value_usd")][:top]
    path = RAW / "intents" / "holdings_history.json"
    doc = json.loads(path.read_text()) if path.exists() else {
        "contract": CONTRACT, "price_note": "quantities at each date, valued at the 1Click prices of the snapshot",
        "snapshot_block": snap["block_height"], "tokens": [{k: t[k] for k in ("token_id", "symbol", "chain", "decimals", "price_usd")} for t in tokens],
        "points": []}
    have = {p["month"] for p in doc["points"]}
    tip = snap["block_height"]
    tip_ns = snap["block_timestamp_ns"]
    genesis_like = 129_000_000  # 2024-10-01, before Intents existed
    g = block_at(ARCHIVAL, genesis_like, gap)
    for d in month_starts(first):
        label = d.strftime("%Y-%m")
        if label in have:
            continue
        target = int(d.timestamp() * 10**9)
        if target >= tip_ns:
            continue
        h, ts = height_at(ARCHIVAL, target, genesis_like, tip, gap)
        sup = {}
        for t in doc["tokens"]:
            try:
                sup[t["token_id"]] = str(int(view(ARCHIVAL, "mt_supply", {"token_id": t["token_id"]}, h, gap)))
            except RuntimeError as e:  # token not yet created at that height
                sup[t["token_id"]] = "0" if "does not exist" in str(e) or "token" in str(e).lower() else None
        doc["points"].append({"month": label, "height": h, "timestamp_ns": ts, "supply_raw": sup})
        doc["points"].sort(key=lambda p: p["month"])
        write_raw("intents/holdings_history.json", doc, f"{ARCHIVAL} mt_supply on {CONTRACT} at month-start blocks")
        print(f"{label} h={h}", file=sys.stderr, flush=True)
    return doc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("snapshot")
    p = sub.add_parser("history")
    p.add_argument("--from", dest="first", default="2025-01")
    p.add_argument("--top", type=int, default=12)
    p.add_argument("--gap", type=float, default=ARCHIVAL_GAP_S)
    a = ap.parse_args(argv)
    if a.cmd == "snapshot":
        d = snapshot()
        print(f"{d['token_count']} tokens, {d['priced_count']} priced, ${d['total_value_usd'] / 1e6:.1f}M at block {d['block_height']}")
    else:
        history(a.first, a.top, a.gap)
    return 0


if __name__ == "__main__":
    sys.exit(main())
