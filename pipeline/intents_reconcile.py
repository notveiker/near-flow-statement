"""Check the census flows against the contract's own supply: for every priced asset, the change in `mt_supply` between two blocks should
equal deposits minus withdrawals (`mt_mint` minus `mt_burn`) that the census counted between them.

Reads `mt_supply` at two heights from a node that still holds that state (set NEAR_RPC; a local node keeps about five epochs).
Transaction outcomes are attributed to the block of their transaction, so receipts that execute just after the window's last block
can differ a little; the output reports the difference rather than hiding it.

    NEAR_RPC=http://127.0.0.1:3030 python3 -m pipeline.intents_reconcile --usage data/derived/census_usage.json --snapshot data/raw/intents/holdings_snapshot.json --out data/derived/intents_reconcile.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .fetch_intents_holdings import FAST, GAP, view


def supply(token_id: str, height: int) -> int | None:
    try:
        return int(view(FAST, "mt_supply", {"token_id": token_id}, height, GAP))
    except RuntimeError:
        return None


def reconcile(usage: dict, tokens: list[dict], read=supply) -> dict:
    a, b = usage["first_height"], usage["last_height"]
    rows = []
    for t in tokens:
        f = usage["flows"].get(t["token_id"], {})
        net_census = int(f.get("deposit", 0)) - int(f.get("withdraw", 0))
        s0, s1 = read(t["token_id"], a), read(t["token_id"], b)
        if s0 is None or s1 is None:
            continue
        d = s1 - s0
        scale = 10 ** t["decimals"] * t["price_usd"]
        rows.append({"symbol": t["symbol"], "chain": t["chain"], "token_id": t["token_id"], "supply_change_usd": d / scale,
                     "census_net_usd": net_census / scale, "gap_usd": (d - net_census) / scale})
    gross = sum(abs(r["census_net_usd"]) for r in rows)
    gap = sum(abs(r["gap_usd"]) for r in rows)
    exact = sum(1 for r in rows if abs(r["gap_usd"]) < 1.0)
    return {"first_height": a, "last_height": b, "assets": len(rows), "assets_matching_within_1usd": exact,
            "sum_abs_census_net_usd": gross, "sum_abs_gap_usd": gap, "net_supply_change_usd": sum(r["supply_change_usd"] for r in rows),
            "net_census_usd": sum(r["census_net_usd"] for r in rows), "rows": sorted(rows, key=lambda r: -abs(r["gap_usd"]))[:25]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--usage", required=True)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    usage = json.loads(Path(a.usage).read_text())
    tokens = [t for t in json.loads(Path(a.snapshot).read_text())["tokens"] if t.get("price_usd")]
    out = reconcile(usage, tokens)
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"{out['assets']} assets, {out['assets_matching_within_1usd']} match within $1; net change {out['net_supply_change_usd']:.0f} vs census {out['net_census_usd']:.0f}; sum |gap| {out['sum_abs_gap_usd']:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
