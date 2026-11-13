"""Apply docs/research-extensions-method.md (RX1-RX3) to the saved outputs. Writes data/derived/rx_results.json."""
from __future__ import annotations

import json

from .common import RAW, ROOT

OUT = RAW / "rx"
f = lambda v: float(v or 0)


def rx1() -> dict:
    d = json.loads((OUT / "rx1_users.json").read_text())
    s = next(r for r in d if r["part"] == "summary")
    users, fills, vol = f(s["x1"]), f(s["x2"]), f(s["x3"])
    conc = {int(r["k"]): f(r["x1"]) / vol for r in d if r["part"] == "conc"}
    g = next(r for r in d if r["part"] == "ge_100k")
    n100, v100 = f(g["x1"]), f(g["x2"])
    size = {r["k"]: {"users": f(r["x1"]), "volume": f(r["x2"]), "fills": f(r["x3"])} for r in d if r["part"] == "size"}
    top = sorted([r for r in d if r["part"] == "top"], key=lambda r: f(r["x4"]))
    wk = sorted([(int(r["k"]), f(r["x1"]), f(r["x2"])) for r in d if r["part"] == "weekly"])
    ret = next(r for r in d if r["part"] == "retention")
    retention = f(ret["x2"]) / f(ret["x1"])
    return {"users": users, "fills": fills, "priced_volume_usd": vol, "share_top1": conc[1], "share_top10": conc[10], "share_top100": conc[100], "share_top1000": conc[1000],
            "users_ge_100k": n100, "users_ge_100k_share_of_users": n100 / users, "volume_share_ge_100k": v100 / vol,
            "size_buckets": size, "top10": [{"user8": r["k"], "volume": f(r["x1"]), "fills": f(r["x2"]), "span_days": f(r["x3"])} for r in top],
            "weekly_active_new": [{"block": b, "active": a, "new": n} for b, a, n in wk],
            "retention_first_blocks_0_3": {"users": f(ret["x1"]), "returned_4_plus_blocks_later": f(ret["x2"]), "share": retention},
            "H_RX1a_supported": conc[10] >= 0.25, "H_RX1a_falsified": conc[10] < 0.10,
            "H_RX1b_supported": n100 / users < 0.02 and v100 / vol >= 0.80, "H_RX1b_falsified": v100 / vol < 0.60,
            "H_RX1c_supported": retention >= 0.30, "H_RX1c_falsified": retention < 0.15}


def rx2() -> dict:
    rows = json.loads((RAW / "rebuild" / "rb_fu11_a_stable_spread.json").read_text())
    per = {}
    paid = {}
    for r in rows:
        if r["pair_class"] != "same_symbol":
            continue
        per[r["solver"]] = per.get(r["solver"], 0.0) + f(r["paid"]) - f(r["received"])
        paid[r["solver"]] = paid.get(r["solver"], 0.0) + f(r["paid"])
    pos = sum(v for v in per.values() if v > 0)
    top = sorted(per.items(), key=lambda kv: -kv[1])
    top3 = sum(v for _, v in top[:3]) / pos
    total = sum(per.values())
    deliv = json.loads((ROOT / "data" / "derived" / "rebuild_results.json").read_text())["fu5"]["delivered_usd"]
    return {"solvers": len(per), "total_margin_usd": total, "positive_margin_usd": pos, "solvers_negative": sum(1 for v in per.values() if v < 0), "top3_share_of_positive": top3,
            "top": [{"solver": k, "margin_usd": v, "paid_usd": paid[k], "bp": v / paid[k] * 1e4} for k, v in top[:8]],
            "delivered_to_revenue_wallets_usd": deliv, "margin_over_delivered": total / deliv,
            "H_RX2a_supported": top3 >= 0.5, "H_RX2a_falsified": top3 < 0.3, "H_RX2b_supported": total / deliv < 0.25, "H_RX2b_falsified": total / deliv > 0.5}


def rx3() -> dict:
    d = json.loads((OUT / "rx3_relayer.json").read_text())
    mo = sorted([r for r in d if r["kind"] == "month"], key=lambda r: r["per"])
    wk = sorted([r for r in d if r["kind"] == "week_ending"], key=lambda r: r["per"])
    row = lambda r: {"per": r["per"], "tx": int(r["tx"]), "signers": int(r["signers"]), "top1": r["top1"], "top1_share": int(r["top1_n"]) / int(r["tx"]),
                     "top5_share": int(r["top5_n"]) / int(r["tx"]), "top2": r["top2"], "top2_share": int(r["top2_n"]) / int(r["tx"])}
    months = [row(r) for r in mo]
    win = [m for m in months if "2026-05" <= m["per"] <= "2026-10"]
    weeks = [row(r) for r in wk]
    return {"months": months, "weeks": weeks, "min_week_top1_share": min(w["top1_share"] for w in weeks), "window_months": [m["per"] for m in win],
            "H_RX3a_supported": all(m["top1_share"] >= 0.80 for m in win), "H_RX3a_falsified": any(m["top1_share"] < 0.60 for m in win),
            "H_RX3b_supported": all(m["top5_share"] >= 0.95 for m in win), "H_RX3b_falsified": any(m["top5_share"] < 0.85 for m in win)}


def main() -> int:
    res = {"rx1": rx1(), "rx2": rx2(), "rx3": rx3()}
    dest = ROOT / "data" / "derived" / "rx_results.json"
    dest.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print("wrote", dest.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
