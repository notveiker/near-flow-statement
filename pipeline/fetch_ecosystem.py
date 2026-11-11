"""NEAR ecosystem breadth from DefiLlama's free endpoints: chain TVL, DEX volume, chain fees, stablecoin supply and the
protocols that run on NEAR. No key. Each snapshot is hashed into data/MANIFEST.json by write_raw.

Run: python3 -m pipeline.fetch_ecosystem
"""
from __future__ import annotations

from .common import http_json, write_raw

LLAMA = "https://api.llama.fi"
STABLES = "https://stablecoins.llama.fi"


def on_near(p: dict) -> bool:
    return any(c.lower() == "near" for c in (p.get("chains") or []))


def main() -> None:
    write_raw("ecosystem/chain_tvl.json", http_json(f"{LLAMA}/v2/historicalChainTvl/Near"), "defillama: v2/historicalChainTvl/Near")
    d = http_json(f"{LLAMA}/overview/dexs/near", {"excludeTotalDataChartBreakdown": "true"})
    write_raw("ecosystem/dex_volume.json", {k: d.get(k) for k in ("totalDataChart", "total24h", "total7d", "total30d", "total1y", "totalAllTime")}
              | {"protocols": [{k: p.get(k) for k in ("name", "category", "total24h", "total7d", "total30d", "total1y")} for p in d.get("protocols", [])]},
              "defillama: overview/dexs/near")
    d = http_json(f"{LLAMA}/overview/fees/near", {"excludeTotalDataChartBreakdown": "true"})
    write_raw("ecosystem/fees.json", {k: d.get(k) for k in ("totalDataChart", "total24h", "total7d", "total30d", "total1y", "totalAllTime")}
              | {"protocols": [{k: p.get(k) for k in ("name", "category", "total24h", "total7d", "total30d", "total1y")} for p in d.get("protocols", [])]},
              "defillama: overview/fees/near")
    write_raw("ecosystem/stablecoins.json", http_json(f"{STABLES}/stablecoincharts/Near"), "defillama stablecoins: stablecoincharts/Near")
    ps = [p for p in http_json(f"{LLAMA}/protocols") if on_near(p)]
    keep = ("name", "slug", "category", "chains", "tvl", "change_1d", "change_7d", "change_1m", "listedAt", "mcap")
    rows = []
    for p in ps:
        r = {k: p.get(k) for k in keep}
        r["near_tvl"] = (p.get("chainTvls") or {}).get("Near")
        rows.append(r)
    write_raw("ecosystem/protocols_on_near.json", sorted(rows, key=lambda r: -(r["near_tvl"] or 0)), "defillama: protocols filtered to chain Near")
    print(f"ecosystem: {len(rows)} protocols on NEAR")


if __name__ == "__main__":
    main()
