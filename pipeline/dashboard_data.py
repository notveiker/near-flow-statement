"""Assemble everything the dashboard shows from committed data (offline, standard library only).

Every number here is read from data/metrics.json, data/series.json or a raw snapshot under data/raw/, or is computed
from them in this file with the formula next to it. Nothing is typed in by hand except the HSP-029 constants, which are
read from data/raw/rpc/rating_assumptions.json.

`build()` returns one JSON-serialisable dict; `pipeline.build_dashboard` embeds it in dashboard/template.html.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .common import DATA, RAW, ROOT

QUARTER_FIELDS = ("txns", "active_accounts", "new_accounts")


def _load(p: Path):
    return json.loads(Path(p).read_text())


def _q(date: str) -> str:
    return f"{date[:4]}Q{(int(date[5:7]) - 1) // 3 + 1}"


def nearblocks_quarterly() -> list[dict]:
    """Daily Nearblocks charts -> per-quarter mean per day."""
    rows = _load(RAW / "nearblocks" / "charts.json")["charts"]
    agg: dict[str, dict] = {}
    for r in rows:
        a = agg.setdefault(_q(r["date"]), {"n": 0, "txns": 0.0, "active": 0.0, "new": 0.0, "fee_near": 0.0})
        a["n"] += 1
        a["txns"] += float(r.get("txns") or 0)
        a["active"] += float(r.get("active_accounts") or 0)
        a["new"] += float(r.get("new_accounts") or 0)
        a["fee_near"] += float(r.get("txn_fee") or 0) / 1e24
    return [{"q": q, "days": a["n"], "tx_per_day": a["txns"] / a["n"], "active_per_day": a["active"] / a["n"],
             "new_per_day": a["new"] / a["n"], "fee_near_per_day": a["fee_near"] / a["n"]} for q, a in sorted(agg.items())]


def market() -> dict:
    """Relative performance and a weekly indexed price series from Binance daily closes."""
    def load(sym):
        rows = _load(RAW / "market" / f"spot_{sym}usdt_1d.json")["rows"]
        return {int(r[0] // 1000) // 86400 * 86400: float(r[4]) for r in rows}, sum(float(r[7]) for r in rows[-30:]) / 30
    px, vol = {}, {}
    for s in ("near", "eth", "sol", "btc"):
        px[s], vol[s] = load(s)
    last = max(px["near"])

    def at(s, t):
        ks = [k for k in px[s] if k <= t]
        return px[s][max(ks)]

    perf = {str(b): {s: at(s, last) / at(s, last - b * 86400) - 1 for s in px} for b in (30, 90, 180, 365)}
    start = last - 365 * 86400
    weekly = []
    t = start
    while t <= last:
        weekly.append({"t": t, **{s: at(s, t) / at(s, start) * 100 for s in px}})
        t += 7 * 86400
    funding = _load(RAW / "market" / "futures_funding_nearusdt.json")
    ls = _load(RAW / "market" / "futures_longshort_nearusdt_1d.json")
    oi = _load(RAW / "market" / "futures_oi_nearusdt_1d.json")
    return {
        "asof": datetime.fromtimestamp(last, timezone.utc).date().isoformat(), "perf": perf, "weekly": weekly,
        "near_spot_usd_per_day_30d": vol["near"],
        "funding_90d_avg_8h": sum(float(x["fundingRate"]) for x in funding[-270:]) / 270,
        "long_short_ratio": float(ls[-1]["longShortRatio"]), "open_interest_usd": float(oi[-1]["sumOpenInterestValue"]),
    }


def ecosystem() -> dict:
    ch = _load(RAW / "ecosystem" / "chain_tvl.json")
    st = _load(RAW / "ecosystem" / "stablecoins.json")
    dx = _load(RAW / "ecosystem" / "dex_volume.json")
    fe = _load(RAW / "ecosystem" / "fees.json")
    pr = _load(RAW / "ecosystem" / "protocols_on_near.json")

    def qlast(rows, key):
        out: dict[str, float] = {}
        for r in rows:
            d = datetime.fromtimestamp(int(r["date"]), timezone.utc).date().isoformat()
            out[_q(d)] = key(r)
        return out
    tvl_q = qlast(ch, lambda r: r["tvl"])
    stable_q = qlast(st, lambda r: r["totalCirculatingUSD"]["peggedUSD"])
    return {
        "tvl_q": tvl_q, "stable_q": stable_q, "tvl_now": ch[-1]["tvl"], "stable_now": st[-1]["totalCirculatingUSD"]["peggedUSD"],
        "dex_30d": dx["total30d"], "dex_1y": dx["total1y"], "dex_top": sorted(dx["protocols"], key=lambda p: -(p["total30d"] or 0))[:5],
        "fees_30d": fe["total30d"], "fees_1y": fe["total1y"],
        "protocols": [{"name": p["name"], "category": p["category"], "tvl": p["near_tvl"]} for p in pr[:12]],
        "protocol_count": len(pr),
    }


def governance() -> dict:
    ts = _load(RAW / "governance" / "topics.json")
    by_year: dict[str, int] = {}
    for t in ts:
        by_year[t["created_at"][:4]] = by_year.get(t["created_at"][:4], 0) + 1
    hsp = [t for t in ts if "HSP" in (t["title"] or "")]
    return {"topics": len(ts), "by_year": by_year, "hsp_threads": len(hsp)}


def hsp029(assump: dict) -> dict:
    """Issuance cap path: flat at start_cap until activation, then linear to target_cap over ramp_months."""
    h = assump["hsp029"]
    act = datetime.fromisoformat(h["activation_date"]).replace(tzinfo=timezone.utc)
    pts, y, m = [], datetime(2026, 11, 1, tzinfo=timezone.utc).year, 11
    for i in range(0, 41):
        mm = (10 + i) % 12 + 1
        yy = 2026 + (10 + i) // 12
        d = datetime(yy, mm, 1, tzinfo=timezone.utc)
        t = max(0.0, (d - act).total_seconds() / (365.25 / 12 * 86400))
        cap = h["start_cap"] - (h["start_cap"] - h["target_cap"]) * min(t, h["ramp_months"]) / h["ramp_months"]
        pts.append({"date": d.date().isoformat(), "cap_pct": round(cap * 100, 4)})
    return {"start_cap_pct": h["start_cap"] * 100, "target_cap_pct": h["target_cap"] * 100, "activation": h["activation_date"],
            "ratification": h["ratification_utc"], "ramp_months": h["ramp_months"], "path": pts}


def holdings() -> dict | None:
    snap = RAW / "intents" / "holdings_snapshot.json"
    if not snap.exists():
        return None
    s = _load(snap)
    by_chain: dict[str, float] = {}
    for t in s["tokens"]:
        by_chain[t.get("chain") or "other"] = by_chain.get(t.get("chain") or "other", 0) + t.get("value_usd", 0)
    wn = next((t for t in s["tokens"] if t["token_id"] == "nep141:wrap.near"), None)
    out = {"asof_utc": s["asof_utc"], "block_height": s["block_height"], "total_usd": s["total_value_usd"], "tokens": s["token_count"],
           "top": [{k: t[k] for k in ("symbol", "chain", "amount", "value_usd")} for t in s["tokens"][:10]],
           "by_chain": sorted(({"chain": k, "usd": v} for k, v in by_chain.items()), key=lambda r: -r["usd"])[:8],
           "wnear_amount": wn["amount"] if wn else None, "wnear_usd": wn["value_usd"] if wn else None, "history": None}
    hist = RAW / "intents" / "holdings_history.json"
    if hist.exists():
        h = _load(hist)
        px = {t["token_id"]: (t["price_usd"], t["decimals"]) for t in h["tokens"]}
        pts = []
        for p in h["points"]:
            tot, wnv = 0.0, 0.0
            for tid, raw in p["supply_raw"].items():
                if raw is None:
                    continue
                price, dec = px[tid]
                v = int(raw) / 10 ** dec * (price or 0)
                tot += v
                if tid == "nep141:wrap.near":
                    wnv = int(raw) / 10 ** dec
            pts.append({"month": p["month"], "usd": tot, "wnear": wnv})
        out["history"] = pts
        out["history_tokens"] = len(h["tokens"])
        ids = {t["token_id"] for t in h["tokens"]}
        out["history_now_usd"] = sum(t.get("value_usd", 0) for t in _load(snap)["tokens"] if t["token_id"] in ids)
    return out


def peers() -> dict | None:
    p = RAW / "peers" / "revenue.json"
    if not p.exists():
        return None
    r = _load(p)
    mc = {c["id"]: c for c in _load(RAW / "peers" / "market_caps.json")["coins"]}
    tok = {"near-intents": "near", "thorchain-dex": "thorchain", "chainflip-amm": "chainflip", "maya-protocol": "cacao"}
    rows = []
    for slug, name in r["venues"].items():
        ser = r["series"][slug]
        f = lambda k, n=30: sum(v for _, v in ser[k][-n:])
        rows.append({"slug": slug, "venue": name, "fees_30d": f("dailyFees"), "revenue_30d": f("dailyRevenue"),
                     "holders_30d": f("dailyHoldersRevenue"), "token_mcap": mc[tok[slug]]["market_cap"]})
    return {"asof": datetime.fromtimestamp(r["series"]["near-intents"]["dailyFees"][-1][0], timezone.utc).date().isoformat(), "venues": rows}


def usage_flows(usage: dict | None) -> dict | None:
    """Deposits, withdrawals and public swap legs from the census, valued at the holdings snapshot's prices."""
    snap = RAW / "intents" / "holdings_snapshot.json"
    if not usage or "flows" not in usage or not snap.exists():
        return None
    tok = {t["token_id"]: t for t in _load(snap)["tokens"]}
    usd = {"deposit": 0.0, "withdraw": 0.0, "swap_in": 0.0}
    unpriced = set()
    for tid, f in usage["flows"].items():
        t = tok.get(tid)
        if not t:
            unpriced.add(tid)
            continue
        for k in usd:
            if k in f:
                usd[k] += int(f[k]) / 10 ** t["decimals"] * t["price_usd"]
    return {**usd, "token_ids": len(usage["flows"]), "unpriced_ids": len(unpriced)}


def builders() -> dict | None:
    p = RAW / "builders" / "npm_daily.json"
    if not p.exists():
        return None
    d = _load(p)
    out = {}
    for pkg, rows in d["packages"].items():
        m: dict[str, int] = {}
        for day, n in rows:
            m[day[:7]] = m.get(day[:7], 0) + n
        out[pkg] = [{"month": k, "n": v} for k, v in sorted(m.items())]
    return {"end": d["end"], "packages": out}


def validators() -> dict | None:
    p = RAW / "rpc" / "validators_epochs.json"
    if not p.exists():
        return None
    e = _load(p)["epochs"]
    m = RAW / "rpc" / "validators_monthly.json"
    return {"latest": e[-1], "monthly": _load(m)["months"] if m.exists() else None}


def web_facts() -> dict | None:
    p = RAW / "web" / "third_party_facts.json"
    return {f["id"]: {"claim": f["claim"], "url": f["url"], "quote": f["quote"]} for f in _load(p)["facts"]} if p.exists() else None


def optional(rel: str):
    p = DATA / rel
    return _load(p) if p.exists() else None


def reproducibility() -> dict:
    man = DATA / "MANIFEST.json"
    plan = DATA / "sample" / "plan.sha256"
    return {
        "manifest_files": len(_load(man)["files"]),
        "manifest_sha256": hashlib.sha256(man.read_bytes()).hexdigest(),
        "sample_plan_sha256": plan.read_text().split()[0] if plan.exists() else None,
        "prereg_sha256": "19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240",
    }


def build() -> dict:
    m = _load(DATA / "metrics.json")
    s = _load(DATA / "series.json")
    assump = _load(RAW / "rpc" / "rating_assumptions.json")
    return {
        "metrics": m, "series": s,
        "nearblocks_q": nearblocks_quarterly(), "market": market(), "ecosystem": ecosystem(), "governance": governance(),
        "hsp029": hsp029(assump), "price_usd": assump["price_usd"],
        "history": optional("derived/history_results.json"), "census": optional("derived/census_summary.json"),
        "hub_trail": optional("derived/hub_trail.json"), "census_hourly": optional("derived/census_hourly.json"), "usage": optional("derived/census_usage.json"), "usage_flows": usage_flows(optional("derived/census_usage.json")),
        "sample_extras": optional("derived/sample_extras_results.json"),
        "holdings": holdings(), "peers": peers(), "builders": builders(), "validators": validators(), "web_facts": web_facts(),
        "repro": reproducibility(),
    }


if __name__ == "__main__":
    d = build()
    print(json.dumps({k: (list(v)[:6] if isinstance(v, dict) else type(v).__name__) for k, v in d.items()}, indent=1)[:900])
