"""Per-swap evidence for the fee mechanics: who actually receives what on intents.near.

Two steps, so the on-chain part can be re-checked by anyone without a key:

  python3 -m pipeline.fetch_fee_evidence sample   # needs NEAR_INTENTS_EXPLORER_JWT (see README)
      Pulls one page of successful 1Click swaps for each of four hours inside the 30-day window and keeps
      up to PER_CHANNEL swaps of at least MIN_USD per channel, with their NEAR tx hashes.
      Writes data/raw/evidence/fee_sample_explorer.json.

  python3 -m pipeline.fetch_fee_evidence trace    # keyless (FastNEAR tx API)
      Re-reads every sampled swap's NEAR transactions and records every intents.near token movement
      in raw token units.
      Writes data/raw/evidence/fee_sample_onchain.json.

compute.py then reports, per channel, how many swaps paid each party on chain and at what rate.
"""
from __future__ import annotations

import json
import sys
import time

from .common import write_raw
from .fetch_escrow import INTENTS, events, fetch_txs
from .fetch_explorer import channel, get, jwt

HOURS = ["2026-10-08T14", "2026-10-15T09", "2026-10-22T18", "2026-10-29T03"]  # UTC, inside 10-06..11-04
PER_CHANNEL = 3
MIN_USD = 200.0
KEEP = ("createdAt", "referral", "appFees", "originAsset", "destinationAsset", "amountIn", "amountOut",
        "amountInUsd", "amountOutUsd", "intentHashes", "nearTxHashes", "depositType", "recipientType")


def sample() -> None:
    token = jwt()
    picked: list[dict] = []
    for h in HOURS:
        params = {"numberOfTransactions": 1000, "statuses": "SUCCESS", "direction": "next",
                  "startTimestamp": f"{h}:00:00Z", "endTimestamp": f"{h}:59:59.999Z"}
        page = get(params, token)
        time.sleep(5.5)
        per: dict[str, int] = {}
        for t in page:
            if float(t.get("amountInUsd") or 0) < MIN_USD or not t.get("nearTxHashes"):
                continue
            row = {k: t.get(k) for k in KEEP}
            ch = channel({"ref": t.get("referral"), "fees": [[f["recipient"], f["fee"]] for f in t.get("appFees") or []]})
            if per.get(ch, 0) >= PER_CHANNEL:
                continue
            per[ch] = per.get(ch, 0) + 1
            row["channel"] = ch
            row["hour"] = h
            picked.append(row)
        print(f"ok    {h}: {len(page)} swaps on the page, kept {sum(per.values())} across {len(per)} channels")
    write_raw("evidence/fee_sample_explorer.json", {"hours": HOURS, "per_channel": PER_CHANNEL, "min_usd": MIN_USD,
                                                     "swaps": picked},
              "NEAR Intents Explorer API, one page per hour in `hours` (statuses=SUCCESS); sampled fields only")


def transfers(tx: dict):
    """(kind, from, to, token, amount) for each intents.near token movement in the tx."""
    for _, ev in events(tx, INTENTS):
        std, name = ev.get("standard"), ev.get("event")
        for d in ev.get("data") or []:
            if std == "dip4" and name == "transfer":
                for tok, amt in (d.get("tokens") or {}).items():
                    yield "dip4_transfer", d.get("account_id"), d.get("receiver_id"), tok, str(amt)
            elif std == "nep245" and name == "mt_transfer":
                for tok, amt in zip(d.get("token_ids") or [], d.get("amounts") or []):
                    yield "mt_transfer", d.get("old_owner_id"), d.get("new_owner_id"), tok, str(amt)


def trace() -> None:
    from .common import read_raw
    swaps = read_raw("evidence/fee_sample_explorer.json")["swaps"]
    txs = fetch_txs([h for s in swaps for h in s["nearTxHashes"]])
    out = []
    for s in swaps:
        moves, seen = [], set()
        for h in s["nearTxHashes"]:
            tx = txs.get(h)
            if tx is None:
                continue
            for kind, frm, to, tok, amt in transfers(tx):
                key = (h, frm, to, tok, amt)  # dip4 and nep245 events describe the same movement
                if key not in seen:
                    seen.add(key)
                    moves.append({"tx": h, "from": frm, "to": to, "token": tok, "amount": amt})
        out.append({"nearTxHashes": s["nearTxHashes"], "txs_found": sum(1 for h in s["nearTxHashes"] if h in txs),
                    "moves": moves})
    write_raw("evidence/fee_sample_onchain.json", {"swaps": out},
              "FastNEAR tx API (tx.main.fastnear.com/v0/transactions): every intents.near dip4/nep245 token movement")
    print(f"ok    traced {len(out)} swaps; {sum(1 for x in out if x['txs_found'])} with txs found")


def main(argv: list[str]) -> int:
    step = argv[0] if argv else ""
    if step == "sample":
        sample()
    elif step == "trace":
        trace()
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
