"""Escrow balance reads for the chain rebuild: intents.near `mt_balance_of` at fixed blocks (archival RPC, keyless).

Used only for the mass-balance check in Q1: the escrow's wNEAR balance at the start of the window and at the cutoff
block must equal the sum of the event ledger. Refuses the buyback wallet, whose balance is never read.
"""
from __future__ import annotations

import base64
import json
import sys

from .fetch_escrow import rpc
from .rebuild import CUTOFF_BLOCK, ESCROW, FORBIDDEN_BALANCE_ACCOUNT, OUT

WNEAR = "nep141:wrap.near"


def mt_balance_of(account: str, token: str, block: int) -> int:
    if account == FORBIDDEN_BALANCE_ACCOUNT:
        raise ValueError("the buyback wallet's balance is never read")
    if block > CUTOFF_BLOCK:
        raise ValueError(f"block {block} is after the data cutoff {CUTOFF_BLOCK}")
    args = base64.b64encode(json.dumps({"account_id": account, "token_id": token}).encode()).decode()
    res = rpc("query", {"request_type": "call_function", "block_id": block, "account_id": "intents.near",
                        "method_name": "mt_balance_of", "args_base64": args})
    return int(json.loads(bytes(res["result"]).decode()))


def main(argv: list[str]) -> int:
    blocks = [int(b) for b in argv]
    rows = [{"block": b, "account": ESCROW, "token": WNEAR, "yocto": str(mt_balance_of(ESCROW, WNEAR, b))} for b in blocks]
    dest = OUT / "q1_escrow_balances.json"
    dest.write_text(json.dumps(rows, indent=1, sort_keys=True) + "\n")
    print(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
