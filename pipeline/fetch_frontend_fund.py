"""Chain reads behind docs/second-review.md section 1 (exploratory, 2026-11-13), at one fixed historical block.

At block 223,088,015 (the last block of 2026-11-04, before the forward-test window), through NEAR archival RPC:
- view_account for fefundsadmin.sputnik-dao.near (the front-end fund) and 1csfundsadmin.sputnik-dao.near;
- the front-end fund's get_proposals (every proposal) and get_policy.
The buyback wallet is not read here: its balance at that block is already committed in
data/raw/rpc/buyback_balance_endpoints.json. Keyless; writes data/raw/rpc/frontend_fund_223088015.json.

Run: python3 -m pipeline.fetch_frontend_fund
"""
from __future__ import annotations

import base64
import json
import sys

from .common import http_json, write_raw

ARCHIVAL = ["https://archival-rpc.mainnet.fastnear.com", "https://archival-rpc.mainnet.near.org"]
BLOCK = 223_088_015
FUND = "fefundsadmin.sputnik-dao.near"
OTHER = "1csfundsadmin.sputnik-dao.near"
UA = "research-script/0.1"  # generic: no repository or owner name in third-party requests


def rpc(method: str, params: dict) -> dict:
    last = None
    for url in ARCHIVAL:
        try:
            r = http_json(url, body={"jsonrpc": "2.0", "id": "x", "method": method, "params": params}, retries=6, user_agent=UA)
            if "result" in r:
                return r["result"]
            last = r.get("error")
        except RuntimeError as exc:
            last = exc
    raise RuntimeError(f"archival rpc {method} failed on all endpoints: {last}")


def view(account: str, method: str, args: dict) -> object:
    res = rpc("query", {"request_type": "call_function", "block_id": BLOCK, "account_id": account,
                        "method_name": method, "args_base64": base64.b64encode(json.dumps(args).encode()).decode()})
    return json.loads(bytes(res["result"]).decode())


def main(argv: list[str]) -> int:
    accounts = {a: rpc("query", {"request_type": "view_account", "block_id": BLOCK, "account_id": a}) for a in (FUND, OTHER)}
    proposals = view(FUND, "get_proposals", {"from_index": 0, "limit": 1000})
    policy = view(FUND, "get_policy", {})
    write_raw(f"rpc/frontend_fund_{BLOCK}.json",
              {"block": BLOCK, "accounts": accounts, "fund": FUND, "proposals": proposals, "policy": policy},
              f"archival rpc query at block_id {BLOCK} ({ARCHIVAL[0]}): view_account {FUND}, {OTHER}; "
              f"call_function {FUND} get_proposals, get_policy")
    print(f"ok    block {BLOCK}: {len(proposals)} proposals, {len(accounts)} accounts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
