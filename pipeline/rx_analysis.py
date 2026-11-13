"""Apply docs/research-extensions-method.md (RX1-RX8) and docs/rx9-rx10-method.md (RX9-RX10) to the saved outputs. Writes data/derived/rx_results.json."""
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


FAMILY = {"solver-priv-liq.near", "solver-multichain-asset.near", "solver-multichain-asset-escrow.near", "solver-multichain-asset-2.near"}


def rx4() -> dict:
    import gzip
    d = json.loads(gzip.open(OUT / "rx4_lst_omni.json.gz", "rt").read())
    led = json.loads((RAW / "rebuild" / "rb_fu10_a_ledger.json").read_text())
    res = {}
    for rc in ("lst-pool.near", "omni.bridge.near"):
        rows = [r for r in d if r["receiver"] == rc and r["token"] in ("nep141:wrap.near", "wrap.near")]
        by, mon = {}, {}
        for r in rows:
            v = int(r["yocto"]) / 1e24
            by[r["src"]] = by.get(r["src"], 0.0) + v
            mon[r["month"]] = mon.get(r["month"], 0.0) + v
        tot = sum(by.values())
        top = sorted(by.items(), key=lambda kv: -kv[1])
        fu10_out = sum(int(x["yocto"]) / 1e24 for x in led if x["cp"] == rc and x["kind"] == "out")
        fam = sum(v for k, v in by.items() if k in FAMILY)
        evm = sum(v for k, v in by.items() if k.startswith("0x"))
        vals = sorted(by.values())
        top3 = sum(v for _, v in top[:3]) / tot
        res[rc] = {"events_near": tot, "fu10_wrap_transfers_out_near": fu10_out, "coverage": tot / fu10_out, "accounts": len(by), "events": sum(int(r["n"]) for r in rows),
                   "top3_share": top3, "top_sources": [{"src": k[:14], "near": v} for k, v in top[:5]], "family_share": fam / tot, "evm_address_accounts_share_of_near": evm / tot,
                   "evm_accounts": sum(1 for k in by if k.startswith("0x")), "median_account_near": vals[len(vals) // 2], "by_month_near": dict(sorted(mon.items())),
                   "H_RX4a_supported": top3 >= 0.70, "H_RX4a_falsified": top3 < 0.40, "H_RX4b_supported": fam / tot >= 0.50, "H_RX4b_falsified": fam / tot < 0.10}
    return res


import random
from datetime import date, timedelta


def _price(px, day):
    d0 = date.fromisoformat(day)
    for k in (0, 1, -1, 2, -2, 3, -3):
        v = px.get((d0 + timedelta(days=k)).isoformat())
        if v:
            return v
    raise KeyError(day)


def _px():
    return json.loads((OUT.parent / "windows" / "near_price_daily_llama.json").read_text())


def rx5() -> dict:
    px = _px()
    q2 = json.loads((RAW / "rebuild" / "rb_q2_native_withdraw.json").read_text())
    days = [(date(2026, 10, 6) + timedelta(days=i)).isoformat() for i in range(30)]
    pub = esc = 0.0
    for r in q2:
        if r["day"] in days:
            v = int(r["yocto"]) / 1e24 * _price(px, r["day"])
            if r["src"].startswith(("5880ad2b", "143f2bb4", "176121bd")):
                pub += v
            else:
                esc += v
    iss = json.loads((ROOT / "data" / "metrics.json").read_text())["net_issuance_usd_30d_m"] * 1e6
    ratio = (pub + esc) / iss
    target, tshare = 0.1581, 11.25 / 15.81
    share = esc / (pub + esc)
    return {"window": [days[0], days[-1]], "public_usd": pub, "escrow_funded_usd": esc, "total_usd": pub + esc, "net_issuance_usd": iss, "ratio": ratio, "repo_ratio": target,
            "ratio_over_repo": ratio / target, "public_ratio": pub / iss, "escrow_ratio": esc / iss, "escrow_share": share, "repo_escrow_share": tshare,
            "H_RX5a_supported": abs(ratio / target - 1) <= 0.10, "H_RX5a_falsified": abs(ratio / target - 1) > 0.25,
            "H_RX5b_supported": abs(share - tshare) <= 0.05, "H_RX5b_falsified": abs(share - tshare) > 0.15}


def _rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def _spearman(x, y):
    a, b = _rank(x), _rank(y); n = len(a); ma, mb = sum(a) / n, sum(b) / n
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b)); den = (sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b)) ** 0.5
    return num / den if den else None


def _mc_p(x, y, rho, n=20000, seed=20261113):
    rng = random.Random(seed); y = list(y); c = 0
    for _ in range(n):
        rng.shuffle(y)
        r = _spearman(x, y)
        if r is not None and abs(r) >= abs(rho) - 1e-12:
            c += 1
    return c / n


def rx6() -> dict:
    px = _px()
    led = {}
    for r in json.loads((OUT / "rx6_wrap_daily.json").read_text()):
        led.setdefault(r["day"], {})[r["kind"]] = int(r["yocto"]) / 1e24
    start = date(2026, 7, 7)
    weeks = []
    for w in range(17):
        ds = [(start + timedelta(days=7 * w + i)).isoformat() for i in range(7)]
        g = lambda k: sum(led.get(d, {}).get(k, 0.0) for d in ds)
        inn, out = g("in") + g("refund_in"), g("out") + g("refund_out") + g("unwrap")
        weeks.append({"week_start": ds[0], "in": inn, "out": out, "unwrap": g("unwrap"), "net": inn - out, "close": _price(px, ds[-1]), "prev_close": _price(px, (start + timedelta(days=7 * w - 1)).isoformat())})
    for w in weeks:
        w["ret"] = w["close"] / w["prev_close"] - 1
    net = [w["net"] for w in weeks]; ret = [w["ret"] for w in weeks]
    rho = _spearman(net, ret); p = _mc_p(net, ret, rho)
    rho_l = _spearman(net[:-1], ret[1:]); p_l = _mc_p(net[:-1], ret[1:], rho_l)
    keep = [i for i, w in enumerate(weeks) if w["week_start"] not in ("2026-09-15", "2026-09-22")]
    rho_ex = _spearman([net[i] for i in keep], [ret[i] for i in keep])
    gross = [w["in"] + w["out"] for w in weeks]
    rho_turn = _spearman(gross, [abs(x) for x in ret])
    post_hoc = {"note": "post hoc, tagged: robustness of the same-week result and a turnover check", "rho_same_week_without_0915_0922": rho_ex, "p_without": _mc_p([net[i] for i in keep], [ret[i] for i in keep], rho_ex),
                "n_without": len(keep), "rho_gross_turnover_vs_abs_return": rho_turn, "p_turnover": _mc_p(gross, [abs(x) for x in ret], rho_turn),
                "net_near_0915_0922": net[10] + net[11], "gross_near_0915_0922": gross[10] + gross[11], "gross_near_all": sum(gross)}
    return {"post_hoc": post_hoc, "weeks": weeks, "rho_same_week": rho, "p_same_week": p, "rho_flow_leads_return": rho_l, "p_lead": p_l, "share_weeks_net_inflow": sum(1 for x in net if x > 0) / len(net),
            "total_net_near": sum(net), "H_RX6a_supported": rho >= 0.30 and p <= 0.10, "H_RX6a_falsified": rho <= -0.30, "H_RX6b_supported": rho_l >= 0.30 and p_l <= 0.10, "H_RX6b_falsified": rho_l <= -0.30}


def rx7() -> dict:
    br, rel, inn = {}, {}, {}
    for r in json.loads((RAW / "rebuild" / "rb_fu2b_a_daily.json").read_text()):
        if r["kind"] == "wrap":
            br[r["day"]] = int(r["yocto"]) / 1e24
    for r in json.loads((RAW / "rebuild" / "rb_fu7_a_summary.json").read_text()):
        if r["part"] == "out_by_day":
            rel[r["day"]] = float(r["near"] or 0)
    for r in json.loads((OUT / "rx6_wrap_daily.json").read_text()):
        if r["kind"] == "in":
            inn[r["day"]] = int(r["yocto"]) / 1e24
    start = date(2026, 7, 7)
    weeks = []
    for w in range(17):
        ds = [(start + timedelta(days=7 * w + i)).isoformat() for i in range(7)]
        I, B, R = (sum(x.get(d, 0.0) for d in ds) for x in (inn, br, rel))
        weeks.append({"week_start": ds[0], "transfers_in": I, "bridge_mng": B, "bridge_share": B / I, "relay": R, "relay_share_of_bridge": R / B if B else None})
    sp = [w for w in weeks if w["week_start"] in ("2026-09-15", "2026-09-22")]
    I, B, R = (sum(w[k] for w in sp) for k in ("transfers_in", "bridge_mng", "relay"))
    return {"weeks": weeks, "spike_transfers_in": I, "spike_bridge_mng": B, "spike_bridge_share": B / I, "spike_relay": R, "spike_relay_share_of_bridge": R / B,
            "H_RX7a_supported": B / I >= 0.60, "H_RX7a_falsified": B / I < 0.30, "H_RX7b_supported": R / B >= 0.40, "H_RX7b_falsified": R / B < 0.15}


def rx8() -> dict:
    d = json.loads((OUT / "rx8_signer_tx_daily.json").read_text())

    def q(day):
        return f"{day[:4]}Q{(int(day[5:7]) - 1) // 3 + 1}"
    agg = {}
    for r in d:
        a = agg.setdefault(q(r["day"]), {"days": 0, "tx": 0, "signers": 0, "failed": 0})
        a["days"] += 1; a["tx"] += int(r["tx"]); a["signers"] += int(r["signers"]); a["failed"] += int(r["failed"])
    series = {k: {"days": a["days"], "tx_per_day": a["tx"] / a["days"], "signers_per_day": a["signers"] / a["days"], "failed_share": a["failed"] / a["tx"]} for k, a in sorted(agg.items())}
    ratio = series["2026Q3"]["tx_per_day"] / series["2025Q3"]["tx_per_day"]
    sratio = series["2026Q3"]["signers_per_day"] / series["2025Q3"]["signers_per_day"]
    t = json.loads((OUT / "rx8b_signer_top.json").read_text())
    tot = next(x for x in t if x["part"] == "total")
    top = sorted([x for x in t if x["part"] == "top"], key=lambda x: int(x["n"]))
    a_tot, b_tot = float(tot["a"]), float(tot["b"])
    top3 = sum(float(x["b"]) for x in top[:3]) / b_tot
    bench = next((x for x in top if x["sg"] == "tx-bench.near"), None)
    nodes = [x for x in top if x["sg"] != "tx-bench.near"]
    return {"series": series, "ratio_tx_2026Q3_over_2025Q3": ratio, "ratio_signers": sratio, "sample_estimate_2026Q3": 36633, "sample_over_exact_2026Q3": 36633 / series["2026Q3"]["tx_per_day"],
            "quarter_totals": {"2025Q3": a_tot, "2026Q3": b_tot, "signers_in_quarter_union": float(tot["n"])},
            "top15": [{"signer": x["sg"], "q3_2025": float(x["a"]), "q3_2026": float(x["b"]), "share_2026Q3": float(x["b"]) / b_tot} for x in top],
            "top3_share_2026Q3": top3, "tx_bench_share_2025Q3": (float(bench["a"]) / a_tot) if bench else None, "tx_bench_share_2026Q3": (float(bench["b"]) / b_tot) if bench else None,
            "top_nodes_each_share_2026Q3": [float(x["b"]) / b_tot for x in nodes[:9]],
            "H_RX8a_supported": ratio >= 10, "H_RX8a_falsified": ratio < 3, "H_RX8b_within_factor_2": 0.5 <= 36633 / series["2026Q3"]["tx_per_day"] <= 2,
            "H_RX8c_supported": sratio >= 3, "H_RX8c_falsified": sratio < 1.2, "H_RX8d_supported": top3 >= 0.80, "H_RX8d_falsified": top3 < 0.50}


def _mix_rows() -> list[dict]:
    return json.loads((OUT / "rx9_rx10_mix.json").read_text())


def rx9() -> dict:
    rows = _mix_rows()
    part = lambda n: [r for r in rows if r["part"] == n]
    cls = {r["k"]: {"swaps": f(r["x1"]), "usd": f(r["x2"])} for r in part("class")}
    classified = [k for k in cls if k in ("stable_stable", "stable_volatile", "volatile_volatile")]
    tot = sum(cls[k]["usd"] for k in classified)
    pairs = sorted(({"pair": r["k"], "swaps": f(r["x1"]), "usd": f(r["x2"])} for r in part("pair") if r["k"] and "UNKNOWN" not in r["k"]), key=lambda r: -r["usd"])
    ptot = sum(x["usd"] for x in pairs)
    top5 = sum(x["usd"] for x in pairs[:5]) / ptot
    near = {r["k"]: {"swaps": f(r["x1"]), "usd": f(r["x2"])} for r in part("near")}
    near_share = near["true"]["usd"] / (near["true"]["usd"] + near["false"]["usd"])
    xc = {r["k"]: {"swaps": f(r["x1"]), "usd": f(r["x2"])} for r in part("xchain")}
    xshare = xc["true"]["usd"] / (xc["true"]["usd"] + xc["false"]["usd"])
    ss = cls["stable_stable"]["usd"] / tot
    strip = lambda x: x.replace("(DEPRECATED)", "")
    same = sum(x["usd"] for x in pairs if len(x["pair"].split("/")) == 2 and strip(x["pair"].split("/")[0]) == strip(x["pair"].split("/")[1])) / ptot
    wk = sorted(((int(r["k"]), f(r["x1"]), f(r["x2"]), f(r["x3"])) for r in part("weekly")))
    return {
        "classes": cls, "priced_total_usd_classified": tot, "stable_stable_share": ss,
        "stable_volatile_share": cls["stable_volatile"]["usd"] / tot, "volatile_volatile_share": cls["volatile_volatile"]["usd"] / tot,
        "unknown_swaps": cls.get("unknown", {}).get("swaps", 0),
        "top25_pairs": [{**x, "share": x["usd"] / ptot} for x in pairs[:25]], "top5_share": top5, "post_hoc_same_symbol_share": same,
        "near_token_share": near_share, "near_token_swaps": near["true"]["swaps"], "cross_chain_share": xshare,
        "weekly_stable_stable": [{"block": b, "share": (a / t) if t else None, "swaps": n} for b, a, t, n in wk],
        "H_RX9a_supported": ss >= 0.50, "H_RX9a_falsified": ss < 0.25,
        "H_RX9b_supported": top5 >= 0.50, "H_RX9b_falsified": top5 < 0.30,
        "H_RX9c_supported": near_share <= 0.10, "H_RX9c_falsified": near_share > 0.25,
        "H_RX9d_supported": xshare >= 0.70, "H_RX9d_falsified": xshare < 0.40,
    }


def rx10() -> dict:
    rows = _mix_rows()
    part = lambda n: [r for r in rows if r["part"] == n]
    size = {r["k"]: {"swaps": f(r["x1"]), "usd": f(r["x2"])} for r in part("size")}
    n_all, v_all = sum(x["swaps"] for x in size.values()), sum(x["usd"] for x in size.values())
    big = [size[k] for k in ("e_100k-1m", "f_>=1m")]
    big_n, big_v = sum(x["swaps"] for x in big), sum(x["usd"] for x in big)
    pct = {int(r["k"]): f(r["x1"]) for r in part("pct")}
    days = sorted(((r["k"], f(r["x1"]), f(r["x2"])) for r in part("topday")), key=lambda t: -t[1])
    d_tot = sum(x[1] for x in days)
    top_day_share = days[0][1] / d_tot
    return {
        "swaps": n_all, "usd": v_all, "percentiles_usd": {"p10": pct[100], "p25": pct[250], "p50": pct[500], "p75": pct[750], "p90": pct[900], "p99": pct[990], "p99.9": pct[999]},
        "buckets": {k: {**v, "swap_share": v["swaps"] / n_all, "usd_share": v["usd"] / v_all} for k, v in sorted(size.items())},
        "ge_100k_swaps": big_n, "ge_100k_swap_share": big_n / n_all, "ge_100k_usd_share": big_v / v_all,
        "largest_day": days[0][0], "largest_day_share": top_day_share, "largest_day_usd": days[0][1], "largest_day_swaps": days[0][2],
        "top3_days": [{"day": d, "share": u / d_tot} for d, u, _ in days[:3]],
        "top10_swaps_usd": [f(r["x1"]) for r in sorted(part("top"), key=lambda r: -f(r["x1"]))],
        "H_RX10a_supported": pct[500] < 1000, "H_RX10a_falsified": pct[500] > 5000,
        "H_RX10b_supported": big_n / n_all < 0.01 and big_v / v_all >= 0.30, "H_RX10b_falsified": big_v / v_all < 0.15 or big_n / n_all >= 0.01,
        "H_RX10c_supported": top_day_share < 0.05, "H_RX10c_falsified": top_day_share > 0.10,
    }


def main() -> int:
    res = {"rx1": rx1(), "rx2": rx2(), "rx3": rx3(), "rx4": rx4(), "rx5": rx5(), "rx6": rx6(), "rx7": rx7(), "rx8": rx8(), "rx9": rx9(), "rx10": rx10()}
    dest = ROOT / "data" / "derived" / "rx_results.json"
    dest.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print("wrote", dest.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
