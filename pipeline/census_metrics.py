"""Headline numbers from the node census, written to data/derived/census_metrics.json.

REPORT.md quotes these with <!--c:key--> markers, and `python3 -m pipeline.check --numbers` compares each marker with this file.
Offline: reads only committed files (census_usage.json, census_hourly.json, hub_trail.json, holdings_snapshot.json).
"""
from __future__ import annotations

import json
import sys

from .common import ROOT

DER = ROOT / "data" / "derived"
OUT = DER / "census_metrics.json"
BLOCKS_PER_S = 1.75


def _j(rel):
    p = DER / rel if not rel.startswith("data/") else ROOT / rel
    return json.loads(p.read_text())


def compute() -> dict:
    u, h = _j("census_usage.json"), _j("census_hourly.json")
    snap = _j("data/raw/intents/holdings_snapshot.json")
    m: dict = {}
    hrs = u["blocks"] / BLOCKS_PER_S / 3600
    m["census_hours"] = round(hrs, 1)
    m["census_txs_k"] = round(u["txs"] / 1e3)
    by = {c["account"]: c for c in u["contracts"]}
    burn = {c["account"]: c for c in u["gas_burners"]}
    m["intents_tx_share_pct"] = round(by["intents.near"]["tx_share"] * 100, 1)
    m["intents_gas_share_pct"] = round(burn["intents.near"]["gas_share"] * 100, 1)
    m["intents_ok_pct"] = round(by["intents.near"]["ok_share"] * 100)
    m["delegate_share_pct"] = round(u["delegate_share"] * 100)
    full = [r for r in h["hours"] if r["blocks"] >= 5000]
    tx, touched = sum(r["txs"] for r in full), sum(r["intents_txs"] for r in full)
    m["intents_touch_share_pct"] = round(touched / tx * 100)
    m["intents_accounts_window"] = h["window"]["distinct_intents_accounts"]
    m["signatures_per_day_k"] = round(u["methods"]["v1.signer"].get("respond", 0) / hrs * 24 / 1e3, 1)
    st = u["stablecoins"]
    m["stablecoin_transfers_per_day_k"] = round(sum(v["transfers"] for v in st.values()) / hrs * 24 / 1e3, 1)
    m["stablecoin_usd_per_day_m"] = round(sum(v["usd"] for v in st.values()) / hrs * 24 / 1e6, 1)
    r = u["relayers"]
    m["relayer_accounts"] = r["distinct"]
    m["relayer_top1_pct"] = round(r["top1_share"] * 100)
    m["relayer_top5_pct"] = round(r["top5_share"] * 100, 1)
    tok = {t["token_id"]: t for t in snap["tokens"]}
    usd = {"deposit": 0.0, "withdraw": 0.0}
    for tid, f in u["flows"].items():
        t = tok.get(tid)
        for k in usd:
            if t and k in f:
                usd[k] += int(f[k]) / 10 ** t["decimals"] * t["price_usd"]
    m["deposits_per_day_m"] = round(usd["deposit"] / hrs * 24 / 1e6, 1)
    m["withdrawals_per_day_m"] = round(usd["withdraw"] / hrs * 24 / 1e6, 1)
    m["net_deposits_per_day_m"] = round((usd["deposit"] - usd["withdraw"]) / hrs * 24 / 1e6, 1)
    m["held_total_usd_m"] = round(snap["total_value_usd"] / 1e6, 1)
    wn = tok["nep141:wrap.near"]
    m["held_wnear_share_pct"] = round(wn["value_usd"] / snap["total_value_usd"] * 100)
    from .dashboard_data import peers
    pr = peers()
    if pr:
        for v in pr["venues"]:
            if v["revenue_30d"] > 0:
                m["peer_mult_" + v["slug"].split("-")[0]] = round(v["token_mcap"] / (v["revenue_30d"] * 365 / 30))
    return m


def main() -> int:
    m = compute()
    OUT.write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")
    print(f"{len(m)} census metrics -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
