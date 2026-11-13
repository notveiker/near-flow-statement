"""Cross-section of fee-sharing tokens: metrics and the three hypotheses of docs/cross-section-method.md.

Reads data/raw/cross_section/{comparators,all}.json (written by pipeline.fetch_cross_section) and, optionally, partner_share.json.
Writes data/derived/cross_section.json. Does nothing until those files exist (nothing is fetched for the four held venues before scoring).
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone

from .common import RAW, ROOT

W0, W1 = "2026-10-15", "2026-11-13"
DAYS = [(datetime.fromisoformat(W0) + timedelta(days=i)).date().isoformat() for i in range(30)]
SWAP_VENUES = ("near-intents", "thorchain-dex", "chainflip-amm", "maya-protocol")


def by_day(series, scale=1.0):
    out = {}
    for t, v in series:
        out[datetime.fromtimestamp(t / scale, timezone.utc).date().isoformat()] = v
    return out


def window_sum(series):
    d = by_day(series)
    if any(x not in d or d[x] is None for x in DAYS):
        return None
    return sum(d[x] for x in DAYS)


def metrics(row: dict) -> dict:
    fees, rev, hold = (window_sum(row[k]) for k in ("dailyFees", "dailyRevenue", "dailyHoldersRevenue"))
    price = by_day(row["prices"], 1000.0)
    mcap = by_day(row["market_caps"], 1000.0)
    out = {"slug": row["slug"], "fees": fees, "revenue": rev, "holders_revenue": hold}
    out["rev_over_fees"] = rev / fees if fees and rev is not None else None
    if hold is None or any(x not in price or x not in mcap or not price[x] for x in (W0, W1)):
        out["capture"] = None
        out["capture_status"] = "not scorable"
    else:
        s0, s1 = mcap[W0] / price[W0], mcap[W1] / price[W1]
        mean_p = sum(price[x] for x in DAYS if x in price) / sum(1 for x in DAYS if x in price)
        out.update(supply_start=s0, supply_end=s1, net_new_supply_usd=(s1 - s0) * mean_p)
        if s1 <= s0:
            out["capture"], out["capture_status"] = math.inf, "net_burn"
        else:
            out["capture"], out["capture_status"] = hold / ((s1 - s0) * mean_p), "finite"
    return out


def rank_desc(vals: dict) -> dict:
    """1 = highest; ties take the better rank; None excluded."""
    ok = {k: v for k, v in vals.items() if v is not None}
    return {k: 1 + sum(1 for x in ok.values() if x > v) for k, v in ok.items()}


def evaluate(rows: list[dict], partner: dict | None) -> dict:
    ms = {r["slug"]: metrics(r) for r in rows}
    cap = {k: m["capture"] for k, m in ms.items()}
    n = sum(1 for v in cap.values() if v is not None)
    rk = rank_desc(cap)
    res = {"metrics": ms, "n_capture": n}
    me = "near-intents"
    if me not in ms:
        return {**res, "status": "near-intents not fetched"}
    if n >= 6 and me in rk:
        r = rk[me]
        res["H_X1"] = {"rank": r, "n": n, "supported": r > n / 2, "falsified": r <= math.ceil(n / 3)}
    else:
        res["H_X1"] = {"verdict": "not scorable", "n": n}
    rof = {k: m["rev_over_fees"] for k, m in ms.items()}
    mine = rof.get(me)
    others = [v for k, v in rof.items() if k != me and v is not None]
    if mine is None or not others:
        res["H_X2"] = {"verdict": "not scorable"}
    else:
        pct = sum(1 for v in others if v < mine) / len(others)
        res["H_X2"] = {"percentile": pct, "supported": pct < 0.5, "falsified": pct > 0.6}
    ps = {v: (partner or {}).get(v, {}).get("value") for v in SWAP_VENUES if (partner or {}).get(v, {}).get("source")}
    ps = {k: v for k, v in ps.items() if v is not None}
    if len(ps) >= 3 and me in ps:
        r = rank_desc(ps)[me]
        res["H_X3"] = {"rank": r, "n": len(ps), "supported": r == 1, "falsified": r > 2}
    else:
        res["H_X3"] = {"verdict": "not scorable", "non_null": len(ps)}
    return res


def main() -> int:
    d = RAW / "cross_section"
    rows = []
    for f in ("comparators.json", "all.json"):
        if (d / f).exists():
            rows += json.loads((d / f).read_text())["rows"]
    if not rows:
        print("nothing fetched yet (held protocols are fetched only after the forward scoring); no analysis")
        return 0
    partner = json.loads((d / "partner_share.json").read_text()) if (d / "partner_share.json").exists() else None
    res = evaluate(rows, partner)
    (ROOT / "data" / "derived" / "cross_section.json").write_text(json.dumps(res, indent=1, sort_keys=True, default=str) + "\n")
    print("wrote data/derived/cross_section.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
