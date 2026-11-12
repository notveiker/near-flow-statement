"""Apply the pre-registered rules in docs/chain-rebuild-method.md to the saved chain-rebuild outputs.

Reads only files under data/raw/ (BigQuery outputs in data/raw/rebuild/, deliveries, Explorer, DefiLlama); writes
data/derived/rebuild_results.json. No network. Run: python3 -m pipeline.rebuild_analysis
"""
from __future__ import annotations

import csv
import json
import random
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

from .common import RAW, ROOT, sha256, write_raw
from .rebuild import CUTOFF_DATE, ESCROW, SWAP_START, WINDOW_START, OUT

Y = 1e24
FEE_ACCT = "176121bd389320632360a091f587af1e2de87d06d3b7c8eec7b2d2871442e3e8"
COLLECTORS = {"5880ad2b362620fadf759cbceb1cd5737ce8c6ed7fb8e9942881e6731f9247dd", "143f2bb439575c286f4f585163f0e5fb4e464f8ce57ec06ae80741407d3cfb31"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def load(stem: str):
    return json.loads((OUT / f"{stem}.json").read_text())


def days(a: str, b: str) -> list[str]:
    d, out = date.fromisoformat(a), []
    while d.isoformat() <= b:
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def pearson(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sx = sum((a - mx) ** 2 for a in x) ** 0.5
    sy = sum((b - my) ** 2 for b in y) ** 0.5
    return None if sx == 0 or sy == 0 else sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def conc(vals: list[float]) -> dict:
    t = sum(vals) or 1.0
    v = sorted(vals, reverse=True)
    return {"top1": v[0] / t if v else None, "top5": sum(v[:5]) / t, "top10": sum(v[:10]) / t, "hhi": sum((a / t) ** 2 for a in v), "n": len(v)}


# ------------------------------------------------------------------ Q1
def q1() -> dict:
    rows = [r for r in load("rb_q1a_escrow_ledger") if r["event"] == "mt_transfer"]
    other_events = Counter(r["event"] for r in load("rb_q1a_escrow_ledger") if r["event"] != "mt_transfer")
    inn, out = Counter(), Counter()
    n_ev = Counter()
    din, dout = defaultdict(Counter), defaultdict(Counter)
    for r in rows:
        a = int(r["mt_yocto"]) / Y
        if r["new_owner"] == ESCROW:
            inn[r["old_owner"]] += a; n_ev[r["old_owner"]] += int(r["n"]); din[r["old_owner"]][r["day"]] += a
        if r["old_owner"] == ESCROW:
            out[r["new_owner"]] += a; n_ev[r["new_owner"]] += int(r["n"]); dout[r["new_owner"]][r["day"]] += a
    bal = {b["block"]: int(b["yocto"]) / Y for b in json.loads((OUT / "q1_escrow_balances.json").read_text())}
    b0, b1 = sorted(bal)
    tin, tout = sum(inn.values()), sum(out.values())
    resid = (bal[b1] - bal[b0]) - (tin - tout)
    unst = set(json.loads((RAW / "unstakers" / "account_set.json").read_text())["accounts"])

    def cls(a: str) -> str:
        if a == "bridge-mng.near":
            return "bridge-mng.near"
        if a.endswith(".sputnik-dao.near"):
            return "named_dao"
        if a in unst:
            return "unstakers_set"
        if HEX64.match(a) and n_ev[a] <= 2:
            return "single_use"
        return "other"

    def by_class(c):
        d = Counter()
        for a, v in c.items():
            d[cls(a)] += v
        return {k: {"near": v, "share": v / (sum(c.values()) or 1)} for k, v in d.most_common()}

    top = lambda c: [{"account": a, "near": v, "class": cls(a), "events": n_ev[a]} for a, v in c.most_common(10)]
    # attack test: releases to the revenue wallets = escrow-funded deliveries
    rel = Counter()
    for r in csv.DictReader(open(RAW / "escrow" / "deliveries.csv")):
        if r["path"] == "escrow_unshield" and WINDOW_START <= r["day"] <= CUTOFF_DATE:
            rel[r["day"]] += int(r["amount_yocto"]) / Y
    release_total = sum(rel.values())
    nonuser = [a for a, _ in inn.most_common() if cls(a) != "single_use"][:10]
    S_total = sum(inn[a] for a in nonuser)
    alld = days(WINDOW_START, CUTOFF_DATE)
    dS = {d: sum(din[a].get(d, 0) for a in nonuser) for d in alld}
    weeks = [alld[i:i + 7] for i in range(0, len(alld) - 6, 7)]
    corr = {}
    for lag in (0, 1, 2):
        xs = [sum(dS[days_[i] if False else alld[max(0, alld.index(days_[i]) - lag)]] for i in range(len(days_))) for days_ in weeks]
        ys = [sum(rel.get(d, 0) for d in days_) for days_ in weeks]
        corr[lag] = pearson(xs, ys)
    rbest = max((c for c in corr.values() if c is not None), default=None)
    # corr of the revenue-wallet releases against ALL non-single-use deposits, and against net solver-priv-liq flow, for context (post hoc)
    sp = "solver-priv-liq.near"
    return {
        "balances_near": {"start_block": b0, "start": bal[b0], "end_block": b1, "end": bal[b1]},
        "ledger": {"inflow_near": tin, "outflow_near": tout, "net": tin - tout, "events_in": sum(int(r["n"]) for r in rows if r["new_owner"] == ESCROW),
                   "events_out": sum(int(r["n"]) for r in rows if r["old_owner"] == ESCROW), "counterparties_in": len(inn), "counterparties_out": len(out)},
        "mass_balance_residual_near": resid, "mass_balance_residual_pct_of_larger_flow": abs(resid) / max(tin, tout) * 100,
        "ledger_complete_within_1pct": abs(resid) / max(tin, tout) <= 0.01,
        "other_event_types_naming_escrow": dict(other_events),
        "coverage_C_inflow_over_outflow": tin / tout,
        "in_by_class": by_class(inn), "out_by_class": by_class(out),
        "in_top10": top(inn), "out_top10": top(out), "in_conc": conc(list(inn.values())), "out_conc": conc(list(out.values())),
        "mint_deposits_to_escrow_rows": len(load("rb_q1b_escrow_deposit_senders")),
        "attack_test": {"release_to_revenue_wallets_near": release_total, "S_accounts": nonuser, "S_deposits_near": S_total,
                        "S_share_of_releases": S_total / release_total, "size_criterion_met": S_total >= 0.8 * release_total,
                        "weekly_corr_by_lag": corr, "corr_criterion_met": rbest is not None and rbest >= 0.7, "weeks": len(weeks)},
        "solver_priv_liq": {"in_near": inn[sp], "out_near": out[sp], "net_near": inn[sp] - out[sp], "share_of_inflow": inn[sp] / tin, "share_of_outflow": out[sp] / tout},
    }


# ------------------------------------------------------------------ Q2
def change_point(y: list[float], min_side: int = 7):
    def sse(a):
        m = sum(a) / len(a)
        return sum((v - m) ** 2 for v in a)
    best = None
    for k in range(min_side, len(y) - min_side + 1):
        s = sse(y[:k]) + sse(y[k:])
        if best is None or s < best[0]:
            best = (s, k)
    return best[1], sse(y) - best[0], sse(y)


def q2() -> dict:
    alld = days(WINDOW_START, CUTOFF_DATE)
    s1, s2, col = Counter(), Counter(), Counter()
    chain_total = defaultdict(Counter)
    for r in load("rb_q2_native_withdraw"):
        a = int(r["yocto"]) / Y
        chain_total[r["day"]][r["wallet"]] += a
        if r["src"] == FEE_ACCT:
            s1[r["day"]] += a
        elif r["src"] in COLLECTORS:
            col[r["day"]] += a
        else:
            s2[r["day"]] += a
    csv_total = defaultdict(float)
    for r in csv.DictReader(open(RAW / "escrow" / "deliveries.csv")):
        csv_total[r["day"]] += int(r["amount_yocto"]) / Y
    diff = {d: sum(chain_total[d].values()) - csv_total.get(d, 0) for d in alld}
    y1 = [s1.get(d, 0) for d in alld]
    y2 = [s2.get(d, 0) for d in alld]
    k, red, tot = change_point(y1)
    rng = random.Random(20261112)
    ge = 0
    for _ in range(10000):
        sh = y1[:]
        rng.shuffle(sh)
        if change_point(sh)[1] >= red:
            ge += 1
    p = (ge + 1) / 10001
    sw = alld[k]
    pre, post = y1[max(0, k - 14):k], y1[k:k + 14]
    pre2, post2 = y2[max(0, k - 14):k], y2[k:k + 14]
    m = lambda a: sum(a) / len(a)
    d1, d2 = m(post) - m(pre), m(post2) - m(pre2)
    frac = min(1.0, -d1 / d2) if d1 < 0 < d2 else None
    # abruptness: share of the pre/post-mean drop that is already realised within +-3 days of the change point
    near_pre = m(y1[max(0, k - 14):max(0, k - 3)]); near_post = m(y1[k + 3:k + 14]) if len(y1) > k + 3 else None
    k2, red2, tot2 = change_point(y2)
    A, B = m(y1[max(0, k - 14):max(0, k - 3)]), m(y1[k + 3:k + 14])
    abrupt = m(y1[k:k + 3]) <= B + 0.2 * (A - B)  # at least 80% of the pre/post drop is realised within 3 days of the change point
    fe = Counter(); fe_s1 = Counter()
    for r in load("rb_q2_native_withdraw"):
        if r["wallet"] == "fefundsadmin.sputnik-dao.near":
            (fe_s1 if r["src"] == FEE_ACCT else fe if r["src"] not in COLLECTORS else Counter())[r["day"]] += int(r["yocto"]) / Y
    exp = {r["date"]: r for r in json.loads((RAW / "explorer" / "daily.json").read_text())["days"]}
    vol = lambda ds: sum(exp[d]["usd_in"] for d in ds if d in exp)
    pre_d, post_d = alld[max(0, k - 14):k], alld[k:k + 14]
    return {
        "switch_day_fee_account": sw, "change_index": k, "sse_reduction_share": red / tot, "permutation_p": p,
        "fee_account_mean_pre14_near_per_day": m(pre), "fee_account_mean_post14_near_per_day": m(post),
        "single_use_mean_pre14": m(pre2), "single_use_mean_post14": m(post2),
        "delta_fee_account": d1, "delta_single_use": d2, "rerouted_fraction": frac,
        "claim_new_revenue_falsified": (frac is not None and frac >= 0.5), "null_reported": (frac is None or frac < 0.2),
        "single_use_change_day": alld[k2], "abrupt": abrupt,
        "fefundsadmin_only_post_hoc": {mo: {"fee_account": sum(v for d, v in fe_s1.items() if d[:7] == mo), "single_use": sum(v for d, v in fe.items() if d[:7] == mo)} for mo in sorted({d[:7] for d in alld})},
        "combined_pre14": m(pre) + m(pre2), "combined_post14": m(post) + m(post2),
        "explorer_usd_in_pre14_days": vol(pre_d), "explorer_usd_in_post14_days": vol(post_d),
        "monthly_near": {mo: {"fee_account": sum(v for d, v in s1.items() if d[:7] == mo), "single_use": sum(v for d, v in s2.items() if d[:7] == mo),
                              "collectors": sum(v for d, v in col.items() if d[:7] == mo)} for mo in sorted({d[:7] for d in alld})},
        "chain_vs_deliveries_csv": {"chain_total_near": sum(sum(c.values()) for c in chain_total.values()), "csv_total_near": sum(csv_total.values()),
                                    "max_abs_daily_diff_near": max(abs(v) for v in diff.values()), "days_with_diff_gt_1near": sum(1 for v in diff.values() if abs(v) > 1)},
        "series": {"days": alld, "fee_account": y1, "single_use": y2},
    }


# ------------------------------------------------------------------ Q3
def q3() -> dict:
    a = load("rb_q3a_solver_shares")
    alt = load("rb_q3b_solver_alt_rule")
    daily = load("rb_q4a_daily_volume")
    n_simple = sum(int(r["n_simple"]) for r in daily)
    n_complex = sum(int(r["n_complex"]) for r in daily)
    legs_simple = 2 * n_simple
    legs_complex = sum(int(r["legs_complex"]) for r in daily)
    classified = sum(int(r["fills"]) for r in a)
    usd_total = sum(float(r["usd"] or 0) for r in a)
    f = [int(r["fills"]) for r in a]
    u = [float(r["usd"] or 0) for r in a]
    top = [{"solver": r["solver"], "fills": int(r["fills"]), "fill_share": int(r["fills"]) / classified, "usd": float(r["usd"] or 0),
            "usd_share": float(r["usd"] or 0) / usd_total, "distinct_counterparties": int(r["cps"]), "days": int(r["days"])} for r in a[:15]]
    unst = set(json.loads((RAW / "unstakers" / "account_set.json").read_text())["accounts"])
    exch = set()
    ex = json.loads((RAW / "labels" / "exchange_accounts.json").read_text())
    for v in ex.values():
        if isinstance(v, list):
            for z in v:
                if isinstance(z, dict) and "account" in z:
                    exch.add(z["account"])
                elif isinstance(z, str):
                    exch.add(z)
    topn = [r["solver"] for r in a[:20]]
    fund = defaultdict(list)
    for r in load("rb_q3d_solver_funding"):
        fund[r["solver"]].append(r)
    fund_out = {}
    for s in topn:
        rows = fund.get(s, [])
        fund_out[s] = {"total_inbound_events": int(rows[0]["solver_total_inbound"]) if rows else 0,
                       "top_counterparties": [{"cp": r["cp"], "kind": r["kind"], "n": int(r["n"]), "in_unstakers_set": r["cp"] in unst, "in_exchange_list": r["cp"] in exch} for r in rows[:5]],
                       "any_in_unstakers_set": any(r["cp"] in unst for r in rows), "any_in_exchange_list": any(r["cp"] in exch for r in rows),
                       "solver_in_unstakers_set": s in unst}
    alt_f = sorted((int(r["fills"]) for r in alt), reverse=True)
    return {
        "simple_swaps": n_simple, "complex_receipts": n_complex, "complex_share_of_receipts": n_complex / (n_simple + n_complex),
        "complex_share_of_legs": legs_complex / (legs_simple + legs_complex),
        "classified_fills": classified, "unclassified_share_of_simple": 1 - classified / n_simple, "solvers_classified": len(a),
        "fill_conc": conc(f), "usd_conc": conc(u), "top15": top,
        "alt_rule_fill_conc": conc(alt_f), "alt_rule_top1": alt[0]["solver"], "top1_same_under_both_rules": alt[0]["solver"] == a[0]["solver"],
        "priced_share_of_classified": sum(int(r["priced"]) for r in a) / classified, "funding_top20": fund_out,
    }


# ------------------------------------------------------------------ Q4
def q4() -> dict:
    daily = {r["day"]: r for r in load("rb_q4a_daily_volume")}
    exp = {r["date"]: r["usd_in"] for r in json.loads((RAW / "explorer" / "daily.json").read_text())["days"]}
    ll = {datetime.fromtimestamp(t, timezone.utc).date().isoformat(): v for t, v in json.loads((RAW / "llama" / "volume_near-intents.json").read_text())["totalDataChart"]}
    ds = days(SWAP_START, CUTOFF_DATE)
    chain = [float(daily[d]["usd_all"]) for d in ds]
    one = [exp.get(d, 0) for d in ds]
    llv = [ll.get(d, 0) for d in ds]
    w = lambda arr, a, b: sum(arr[ds.index(d)] for d in days(a, b))
    wk = {}
    for name, arr in (("chain", chain), ("oneclick", one), ("llama", llv)):
        wk[name] = {"before": w(arr, "2026-08-25", "2026-08-31"), "after": w(arr, "2026-09-01", "2026-09-07")}
        wk[name]["ratio"] = wk[name]["after"] / wk[name]["before"]
    L, C = wk["llama"]["ratio"], wk["chain"]["ratio"]
    verdict = "shows" if C >= 1 + 0.5 * (L - 1) else "absent" if C <= 1 + 0.1 * (L - 1) else "ambiguous"
    ref = defaultdict(float)
    for r in load("rb_q4b_referral"):
        ref[r["referral"]] += float(r["usd"] or 0)
    tot = sum(ref.values())
    oc = sum(v for k, v in ref.items() if k.startswith("1click-"))
    n_simple = sum(int(r["n_simple"]) for r in daily.values()); n_priced = sum(int(r["n_priced"]) for r in daily.values())
    sh = lambda a, b: sum(a) / sum(b)
    pre = days(SWAP_START, "2026-08-31"); post = days("2026-09-08", CUTOFF_DATE)
    sl = lambda arr, dd: [arr[ds.index(d)] for d in dd]
    return {
        "chain_priced_usd_total": sum(chain), "oneclick_usd_in_total": sum(one), "llama_total": sum(llv),
        "chain_over_oneclick": sh(chain, one), "chain_over_llama": sh(chain, llv), "oneclick_over_llama": sh(one, llv),
        "remainder_chain_minus_oneclick_usd": sum(chain) - sum(one),
        "priced_share_of_simple_swaps": n_priced / n_simple,
        "step_2026_09_01": {"weeks": wk, "verdict": verdict, "chain_over_llama_before_week": wk["chain"]["before"] / wk["llama"]["before"],
                            "chain_over_llama_after_week": wk["chain"]["after"] / wk["llama"]["after"],
                            "chain_over_llama_08_07_to_08_31": sh(sl(chain, pre), sl(llv, pre)), "chain_over_llama_09_08_to_11_04": sh(sl(chain, post), sl(llv, post))},
        "referral_split": {"tagged_1click_usd": oc, "tagged_1click_share_of_chain": oc / tot, "none_share": ref.get("(none)", 0) / tot,
                           "other_referral_share": (tot - oc - ref.get("(none)", 0)) / tot,
                           "top": [{"referral": k, "usd": v, "share": v / tot} for k, v in sorted(ref.items(), key=lambda kv: -kv[1])[:12]]},
        "series": {"days": ds, "chain": chain, "oneclick": one, "llama": llv},
    }


# ------------------------------------------------------------------ F1
FAMILY = {"solver-priv-liq.near", "solver-multichain-asset.near", "solver-multichain-asset-escrow.near", "solver-multichain-asset-2.near"}


def f1() -> dict:
    rows = [r for r in load("rb_q1a_escrow_ledger") if r["event"] == "mt_transfer"]
    gin = sum(int(r["mt_yocto"]) for r in rows if r["new_owner"] == ESCROW and r["old_owner"] in FAMILY) / Y
    gout = sum(int(r["mt_yocto"]) for r in rows if r["old_owner"] == ESCROW and r["new_owner"] in FAMILY) / Y
    dep = load("rb_f1a_family_deposits")
    by_signer = Counter()
    month = Counter()
    for r in dep:
        by_signer[(r["signer"], r["tx_receiver"])] += int(r["yocto"]) / Y
        month[r["day"][:7]] += int(r["yocto"]) / Y
    wd = load("rb_f1b_family_withdrawals")
    burn = sum(int(r["yocto"] or 0) for r in wd if r["event"] == "mt_burn") / Y
    native = Counter()
    for r in wd:
        if r["event"] == "native_withdraw":
            native[r["receiver_id"]] += int(r["yocto"] or 0) / Y
    ext = sum(by_signer.values())
    net = ext - burn
    unst = set(json.loads((RAW / "unstakers" / "account_set.json").read_text())["accounts"])
    return {"family": sorted(FAMILY), "gross_inflow_to_escrow_near": gin, "gross_outflow_from_escrow_near": gout,
            "external_mint_deposits_near": ext, "external_deposits_over_gross_inflow": ext / gin, "mt_burn_near": burn,
            "native_withdraw_by_receiver_near": dict(native), "net_external_near": net, "recycling_ratio": gin / net if net > 0 else None,
            "H_F1_supported": (net > 0 and gin / net >= 5 and ext / gin < 0.25), "H_F1_falsified": ext / gin >= 0.5,
            "deposits_by_signer": [{"signer": a, "tx_receiver": b, "near": v, "in_unstakers_set": a in unst} for (a, b), v in by_signer.most_common(5)],
            "top5_signer_share": sum(v for _, v in by_signer.most_common(5)) / ext, "deposits_by_month_near": dict(month)}


# ------------------------------------------------------------------ F3
def f3() -> dict:
    ds = days(SWAP_START, CUTOFF_DATE)
    cx = {r["day"]: r for r in load("rb_f3a_daily")}
    q4d = {r["day"]: r for r in load("rb_q4a_daily_volume")}
    n_anch = sum(int(r["n_anchored"]) for r in cx.values())
    n_un = sum(int(r["n_unanchored"]) for r in cx.values())
    simple = [float(q4d[d]["usd_all"]) for d in ds]
    anch = [float(cx[d]["usd_anchored"]) for d in ds]
    comb = [a + b for a, b in zip(simple, anch)]
    w = lambda arr, a, b: sum(arr[ds.index(d)] for d in days(a, b))
    step = lambda arr: w(arr, "2026-09-01", "2026-09-07") / w(arr, "2026-08-25", "2026-08-31")
    L = q4()["step_2026_09_01"]["weeks"]["llama"]["ratio"]
    thr = 1 + 0.5 * (L - 1)
    exp = {r["date"]: r["usd_in"] for r in json.loads((RAW / "explorer" / "daily.json").read_text())["days"]}
    one = sum(exp.get(d, 0) for d in ds)
    ll = {datetime.fromtimestamp(t, timezone.utc).date().isoformat(): v for t, v in json.loads((RAW / "llama" / "volume_near-intents.json").read_text())["totalDataChart"]}
    llt = sum(ll.get(d, 0) for d in ds)
    rows = load("rb_f3b_solver_fills")
    tot = {r["solver"]: int(r["fills_simple"]) + int(r["fills_complex"]) for r in rows}
    t = sum(tot.values())
    top = sorted(tot.items(), key=lambda kv: -kv[1])
    simple_top10 = q3()["fill_conc"]["top10"]
    comb_top10 = sum(v for _, v in top[:10]) / t
    return {"anchored_receipts": n_anch, "unanchored_receipts": n_un, "anchored_share_of_complex": n_anch / (n_anch + n_un),
            "anchored_usd": sum(anch), "simple_usd": sum(simple), "combined_usd": sum(comb), "uplift_vs_simple": sum(anch) / sum(simple),
            "combined_over_oneclick": sum(comb) / one, "combined_over_llama": sum(comb) / llt, "llama_over_oneclick": llt / one,
            "step_ratio_combined": step(comb), "step_ratio_anchored_only": step(anch), "step_threshold": thr, "step_shows_on_chain": step(comb) >= thr,
            "fills_simple": sum(int(r["fills_simple"]) for r in rows), "fills_complex": sum(int(r["fills_complex"]) for r in rows),
            "top10_fill_share_combined": comb_top10, "top10_fill_share_simple": simple_top10, "H_F3a_robust": abs(comb_top10 - simple_top10) <= 0.05,
            "top1_combined": {"solver": top[0][0], "share": top[0][1] / t}, "top3_combined": [{"solver": k, "share": v / t} for k, v in top[:3]]}


def main() -> int:
    res = {"cutoff_block": 223_088_015, "windows": {"q1_q2": [WINDOW_START, CUTOFF_DATE], "q3_q4": [SWAP_START, CUTOFF_DATE]}, "q1": q1(), "q2": q2(), "q3": q3(), "q4": q4(), "f1": f1(), "f3": f3()}
    jobs = [json.loads(l) for l in (OUT / "jobs.jsonl").read_text().splitlines()]
    res["bytes_billed_total"] = sum(j["bytes_billed"] for j in jobs)
    dest = ROOT / "data" / "derived" / "rebuild_results.json"
    dest.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(f"wrote {dest.relative_to(ROOT)} ({sha256(dest)[:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
