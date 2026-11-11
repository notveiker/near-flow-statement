"""Keyless prop-research extras: liquid staking, on-chain fee hierarchy, DEX share, GitHub pulse, live Nearblocks stats.

None of these feed a pre-registered test. They sit next to the Intents thesis so the paper can show what else is
happening on the chain while Intents grows.

    python3 -m pipeline.fetch_prop_extras
Outputs under data/raw/prop/: lst.json, fees_near.json, dexs_near.json, github.json, nearblocks_stats.json
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone

from .common import USER_AGENT, http_json, write_raw

LST = [
    ("linear-protocol", "LiNEAR"),
    ("meta-pool-near", "Meta Pool"),
    ("rhea-lst", "RHEA LST"),
]
FEE_KEEP = ("near-intents", "rhea-dex", "rhea-lend", "near", "rhea-lst", "rhea-cross-chain")
DEX_KEEP = ("near-intents", "rhea-dex", "rhea-cross-chain", "deltatrade", "veax-clmm")
REPOS = [
    "near/nearcore",
    "near/near-sdk-rs",
    "near/near-api-js",
    "near/intents",
    "near/mpc",
    "defuse-protocol/one-click-sdk-typescript",
    "defuse-protocol/sdk-monorepo",
    "defuse-protocol/near-intents-amm-solver",
]


def _q(ts: int) -> str:
    d = datetime.fromtimestamp(ts, timezone.utc)
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


def lst() -> dict:
    out = {"asof_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "protocols": []}
    for slug, name in LST:
        try:
            d = http_json(f"https://api.llama.fi/protocol/{slug}")
        except Exception as e:
            out["protocols"].append({"slug": slug, "name": name, "error": str(e)})
            continue
        series = d.get("tvl") or []
        # keep monthly last-of-month points for a compact series
        by_m: dict[str, float] = {}
        for r in series:
            m = datetime.fromtimestamp(r["date"], timezone.utc).strftime("%Y-%m")
            by_m[m] = float(r["totalLiquidityUSD"])
        months = sorted(by_m)
        q_last: dict[str, float] = {}
        for m, v in by_m.items():
            q_last[_q(int(datetime.strptime(m + "-01", "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()))] = v
        out["protocols"].append({
            "slug": slug, "name": name or d.get("name"),
            "tvl_now": by_m[months[-1]] if months else None,
            "tvl_30d_ago": by_m[months[-2]] if len(months) > 1 else None,
            "tvl_365d_ago": next((by_m[m] for m in reversed(months) if m <= months[-1][:4] + f"-{int(months[-1][5:7]) - 0:02d}" ), None),
            "monthly": [{"month": m, "tvl": by_m[m]} for m in months if m >= "2024-01"],
            "quarterly_end": [{"q": q, "tvl": q_last[q]} for q in sorted(q_last) if q >= "2024Q1"],
        })
        # fix 365d: pick month ~12 months back
        if months:
            target = f"{int(months[-1][:4]) - 1}-{months[-1][5:7]}"
            out["protocols"][-1]["tvl_365d_ago"] = by_m.get(target) or next((by_m[m] for m in reversed(months) if m <= target), None)
    return out


def fees() -> dict:
    d = http_json("https://api.llama.fi/overview/fees/near")
    prots = []
    for p in d.get("protocols", []):
        slug = (p.get("slug") or "").lower()
        if slug in FEE_KEEP or p.get("protocolType") == "chain" or slug.startswith("near"):
            prots.append({
                "slug": p.get("slug"), "name": p.get("name"), "category": p.get("category"),
                "total24h": p.get("total24h"), "total7d": p.get("total7d"), "total30d": p.get("total30d"),
                "total1y": p.get("total1y"), "change_30dover30d": p.get("change_30dover30d"),
            })
    prots = sorted(prots, key=lambda x: -(x.get("total30d") or 0))
    top = prots[0] if prots else {}
    rest = sum((p.get("total30d") or 0) for p in prots[1:])
    return {
        "asof_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "chain_total30d": d.get("total30d"), "chain_total1y": d.get("total1y"),
        "top_share_30d_pct": round(100 * (top.get("total30d") or 0) / d["total30d"], 1) if d.get("total30d") else None,
        "top": top, "rest_30d": rest, "protocols": prots,
        "chart_daily": d.get("totalDataChart", [])[-400:],  # last ~400 days
    }


def dexs() -> dict:
    d = http_json("https://api.llama.fi/overview/dexs/near")
    prots = []
    for p in d.get("protocols", []):
        prots.append({
            "slug": p.get("slug"), "name": p.get("name"), "category": p.get("category"),
            "total24h": p.get("total24h"), "total7d": p.get("total7d"), "total30d": p.get("total30d"),
            "total1y": p.get("total1y"), "change_30dover30d": p.get("change_30dover30d"),
        })
    prots = sorted(prots, key=lambda x: -(x.get("total30d") or 0))
    top = prots[0] if prots else {}
    return {
        "asof_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "chain_total30d": d.get("total30d"), "chain_total1y": d.get("total1y"),
        "top_share_30d_pct": round(100 * (top.get("total30d") or 0) / d["total30d"], 1) if d.get("total30d") else None,
        "protocols": prots[:12],
        "chart_daily": d.get("totalDataChart", [])[-400:],
    }


def github() -> dict:
    out = {"asof_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "repos": []}
    for full in REPOS:
        url = f"https://api.github.com/repos/{full}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            out["repos"].append({
                "full_name": d["full_name"], "stars": d["stargazers_count"], "forks": d["forks_count"],
                "open_issues": d["open_issues_count"], "pushed_at": d["pushed_at"], "created_at": d["created_at"],
                "watchers": d.get("subscribers_count"), "size_kb": d.get("size"),
            })
        except Exception as e:
            out["repos"].append({"full_name": full, "error": str(e)})
    return out


def nearblocks_stats() -> dict:
    d = http_json("https://api.nearblocks.io/v1/stats")
    s = d["stats"][0]
    keep = {k: s.get(k) for k in (
        "near_price", "market_cap", "total_supply", "circulating_supply", "avg_block_time", "gas_price",
        "nodes_online", "nodes", "rpc_nodes", "total_txns", "txn_fee", "txn_fee_usd", "active_accounts",
        "new_accounts", "active_contracts", "new_contracts", "volume", "volume_usd",
    ) if k in s or True}
    return {"asof_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "stats": keep, "raw_keys": sorted(s.keys())}


def main() -> int:
    write_raw("prop/lst.json", lst(), "DefiLlama protocol TVL for LiNEAR, Meta Pool, RHEA LST")
    write_raw("prop/fees_near.json", fees(), "DefiLlama overview/fees/near")
    write_raw("prop/dexs_near.json", dexs(), "DefiLlama overview/dexs/near")
    write_raw("prop/github.json", github(), "GitHub public repo metadata")
    write_raw("prop/nearblocks_stats.json", nearblocks_stats(), "Nearblocks /v1/stats")
    print("wrote data/raw/prop/{lst,fees_near,dexs_near,github,nearblocks_stats}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
