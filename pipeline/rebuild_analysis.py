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


# ------------------------------------------------------------------ F2b
BRIDGE = "bridge-mng.near"


def f2b() -> dict:
    a = load("rb_f2b_a_daily")
    k, n = Counter(), Counter()
    for r in a:
        k[r["kind"]] += int(r["yocto"]) / Y
        n[r["kind"]] += int(r["n"])
    R = k["out"] / k["wrap"]
    f1_mints = f1()["external_mint_deposits_near"]
    b = load("rb_f2b_b_withdrawals_to_bridge")
    to_bridge = [r for r in b if r["part"] == "to_bridge"]
    wd_native = sum(int(r["yocto"] or 0) for r in to_bridge if r["event"] == "native_withdraw" or r["token"] == "nep141:wrap.near") / Y
    wd_share = wd_native / k["wrap"]
    funders = load("rb_f2b_c_direct_funders")
    by = {r["signer"]: float(r["near"] or 0) for r in funders if r["part"] == "by_signer"}
    direct = sum(by.values())
    top = sorted(by.items(), key=lambda kv: -kv[1])
    unst = set(json.loads((RAW / "unstakers" / "account_set.json").read_text())["accounts"])
    exch = set()
    for v in json.loads((RAW / "labels" / "exchange_accounts.json").read_text()).values():
        if isinstance(v, list):
            for z in v:
                if isinstance(z, dict) and "account" in z:
                    exch.add(z["account"])
                elif isinstance(z, str):
                    exch.add(z)
    in_lists = sum(v for a_, v in by.items() if a_ in unst or a_ in exch)
    over = [r for r in load("rb_f2b_d_funder_overlap") if r["part"] == "overlap"]
    ov_fund = sum(float(r["x"] or 0) for r in over)
    ov_wd = sum(float(r["y"] or 0) for r in over)
    foot = [r for r in load("rb_f2b_d_funder_overlap") if r["part"] != "overlap"]
    return {"wrapped_near": k["wrap"], "wrap_events": n["wrap"], "passed_to_intents_near": k["out"], "R_pass_through": R,
            "H_F2b_a_supported": 0.95 <= R <= 1.05, "H_F2b_a_falsified": R < 0.8 or R > 1.2,
            "transfers_in_near": k["in"], "refund_in_near": k["refund_in"], "f1_mints_near": f1_mints, "f1_consistent": k["out"] >= f1_mints * 0.999,
            "withdrawals_to_bridge_near": wd_native, "withdrawals_share_of_wrapped": wd_share,
            "H_F2b_b_supported": wd_share >= 0.5, "H_F2b_b_falsified": wd_share < 0.1, "step3_triggered": wd_share < 0.8,
            "direct_funded_near": direct, "direct_coverage_of_wrapped": direct / k["wrap"], "direct_transfers": sum(int(r["n"]) for r in funders if r["part"] == "by_signer"),
            "funders": len(by), "top_funders": [{"signer": a_, "near": v, "share": v / direct} for a_, v in top[:10]], "top10_share": sum(v for _, v in top[:10]) / direct,
            "funded_by_unstakers_or_exchange_list_near": in_lists, "funded_by_lists_share": in_lists / direct,
            "H_F2b_c_supported": (direct / k["wrap"] >= 0.8 and sum(v for _, v in top[:10]) / direct >= 0.5 and in_lists / direct < 0.1),
            "H_F2b_c_falsified": in_lists / direct >= 0.1,
            "top_funder_matches_f1": {"signer": top[0][0], "near": top[0][1], "f1_mints_near": f1_mints, "ratio": top[0][1] / f1_mints},
            "post_hoc_recycled": {"funders_also_native_withdraw_receivers": len(over), "funded_near": ov_fund, "withdrawn_to_them_near": ov_wd, "share_of_direct": ov_fund / direct},
            "post_hoc_top_funder_intents_events": len(foot)}


# ------------------------------------------------------------------ F4
def f4() -> dict:
    rows = load("rb_f4a_fee_credits")
    q2d = load("rb_q2_native_withdraw")
    deliv = Counter()
    for r in q2d:
        s = r["src"]
        g = "5880ad2b" if s.startswith("5880ad2b") else "143f2bb4" if s.startswith("143f2bb4") else "176121bd" if s.startswith("176121bd") else "rest"
        deliv[g] += int(r["yocto"]) / Y
    cred = defaultdict(Counter)
    for r in rows:
        cred[r["grp"]][r["channel"]] += int(r["yocto"] or 0) / Y
    recon = {g: {"delivered_near": deliv[g], "credits_all_channels_near": sum(cred[g].values()), "ratio_all": sum(cred[g].values()) / deliv[g],
                 "credits_mt_transfer_near": cred[g]["mt_transfer"], "ratio_mt_transfer_only_post_hoc": cred[g]["mt_transfer"] / deliv[g],
                 "token_diff_near_gross_positive": cred[g]["token_diff"]} for g in deliv}
    for g in recon:
        recon[g]["within_0p8_1p5_all_channels"] = 0.8 <= recon[g]["ratio_all"] <= 1.5
    both = ("5880ad2b", "143f2bb4")
    send = Counter()
    credit_all, credit_mt = 0.0, 0.0
    for r in rows:
        if r["grp"] in both:
            v = int(r["yocto"] or 0) / Y
            credit_all += v
            if r["channel"] == "mt_transfer":
                credit_mt += v
                send[r["cp"]] += v
    top_sender, top_v = send.most_common(1)[0]
    esc_p = Counter()
    tot_p = Counter()
    for r in rows:
        if r["period"] == "pre_0819" or r["grp"] == "176121bd":
            continue
        v = int(r["yocto"] or 0) / Y
        tot_p["all"] += v
        if r["channel"] == "mt_transfer":
            tot_p["mt"] += v
        if r["channel"] == "mt_transfer" and r["cp"] == ESCROW:
            esc_p["esc"] += v
    esc_pre = sum(int(r["yocto"]) / Y for r in rows if r["period"] == "pre_0819" and r["channel"] == "mt_transfer" and r["cp"] == ESCROW and r["grp"] != "176121bd")
    tot_pre = sum(int(r["yocto"] or 0) / Y for r in rows if r["period"] == "pre_0819" and r["grp"] != "176121bd")
    esc_rest_all = sum(int(r["yocto"]) / Y for r in rows if r["grp"] == "rest" and r["cp"] == ESCROW)
    csv_unshield = sum(int(r["amount_yocto"]) / Y for r in csv.DictReader(open(RAW / "escrow" / "deliveries.csv")) if r["path"] == "escrow_unshield" and WINDOW_START <= r["day"] <= CUTOFF_DATE)
    mt_by_period = defaultdict(Counter)
    for r in rows:
        if r["grp"] in both and r["channel"] == "mt_transfer":
            mt_by_period[r["period"]][r["cp"]] += int(r["yocto"]) / Y
    share = esc_p["esc"] / tot_p["all"]
    return {"reconciliation": recon, "delivered_total_near": sum(deliv.values()),
            "H_F4a_strict": {"top_sender": top_sender, "top_sender_near": top_v, "credits_all_channels_near": credit_all, "share": top_v / credit_all,
                              "supported": top_v / credit_all >= 0.5, "falsified": top_v / credit_all < 0.25,
                              "attribution_allowed_by_reconciliation": all(recon[g]["within_0p8_1p5_all_channels"] for g in both)},
            "H_F4a_mt_transfer_only_post_hoc": {"share": top_v / credit_mt, "credits_mt_transfer_near": credit_mt,
                                                 "top_senders": [{"sender": a, "near": v, "share": v / credit_mt} for a, v in send.most_common(5)]},
            "H_F4b_strict": {"escrow_mt_transfer_near_mid_post": esc_p["esc"], "all_credits_mid_post_near": tot_p["all"], "share": share, "supported": share >= 0.2, "falsified": share < 0.05,
                              "share_of_mt_transfer_only_post_hoc": esc_p["esc"] / tot_p["mt"], "pre_0819_share_all_channels": esc_pre / tot_pre},
            "rest_group_escrow_funded_near": esc_rest_all, "rest_group_escrow_share_of_credits": esc_rest_all / sum(cred["rest"].values()),
            "deliveries_csv_escrow_unshield_near": csv_unshield, "rest_delivered_near": deliv["rest"],
            "senders_by_period_persistent_accounts_post_hoc": {p: [{"sender": a, "near": v} for a, v in c.most_common(4)] for p, c in sorted(mt_by_period.items())}}


# ------------------------------------------------------------------ F5
def f5() -> dict:
    ds = days(SWAP_START, CUTOFF_DATE)
    px = {r["day"]: r["usd"] for r in map(json.loads, (OUT / "aux_prices.ndjson").read_text().splitlines()) if r["symbol"] == "NEAR"}
    cx = {r["day"]: float(r["usd_anchored"]) for r in load("rb_f3a_daily")}
    q4d = {r["day"]: float(r["usd_all"]) for r in load("rb_q4a_daily_volume")}
    vol = {d: q4d[d] + cx[d] for d in ds}
    exp = {r["date"]: r["usd_in"] for r in json.loads((RAW / "explorer" / "daily.json").read_text())["days"]}
    grp = {d: Counter() for d in ds}
    for r in load("rb_q2_native_withdraw"):
        if r["day"] in grp:
            sname = r["src"]
            g = "persistent_5880ad2b_143f2bb4" if sname.startswith(("5880ad2b", "143f2bb4")) else "fee_176121bd" if sname.startswith("176121bd") else "escrow_funded_rest"
            grp[r["day"]][g] += int(r["yocto"]) / Y * px[r["day"]]
    usd = {d: sum(grp[d].values()) for d in ds}
    tau_c = sum(usd.values()) / sum(vol.values()) * 1e4
    tau_1 = sum(usd.values()) / sum(exp.get(d, 0) for d in ds) * 1e4
    months = {}
    for mo in sorted({d[:7] for d in ds}):
        md = [d for d in ds if d[:7] == mo]
        if len(md) < 14:
            continue
        months[mo] = {"days": len(md), "tau_chain_bp": sum(usd[d] for d in md) / sum(vol[d] for d in md) * 1e4,
                      "tau_1click_bp": sum(usd[d] for d in md) / sum(exp.get(d, 0) for d in md) * 1e4}
    weeks = [ds[i:i + 7] for i in range(0, len(ds) - 6, 7)]
    wv = [sum(vol[d] for d in w) for w in weeks]
    corr = {"total": pearson([sum(usd[d] for d in w) for w in weeks], wv)}
    for g in ("persistent_5880ad2b_143f2bb4", "fee_176121bd", "escrow_funded_rest"):
        corr[g] = pearson([sum(grp[d][g] for d in w) for w in weeks], wv)
    dev = {mo: v["tau_chain_bp"] / tau_c - 1 for mo, v in months.items()}
    by_group_usd = {g: sum(grp[d][g] for d in ds) for g in ("persistent_5880ad2b_143f2bb4", "fee_176121bd", "escrow_funded_rest")}
    ll = {datetime.fromtimestamp(t, timezone.utc).date().isoformat(): v for t, v in json.loads((RAW / "llama" / "volume_near-intents.json").read_text())["totalDataChart"]}
    tau_l = sum(usd.values()) / sum(ll.get(d, 0) for d in ds) * 1e4
    llama_months = {mo: sum(usd[d] for d in ds if d[:7] == mo) / sum(ll.get(d, 0) for d in ds if d[:7] == mo) * 1e4 for mo in months}
    group_months = {mo: {g: sum(grp[d][g] for d in ds if d[:7] == mo) for g in ("persistent_5880ad2b_143f2bb4", "fee_176121bd", "escrow_funded_rest")} for mo in months}
    post_hoc_llama = {"note": "post hoc: the repo's 4.98 bp is over DefiLlama volume, not 1Click; the pre-registered H-F5a compared the wrong denominator",
                      "tau_llama_bp": tau_l, "tau_llama_over_repo": tau_l / 4.98, "within_25pct": abs(tau_l / 4.98 - 1) <= 0.25, "tau_llama_bp_by_month": llama_months,
                      "delivered_usd_by_group_by_month": group_months}
    return {"post_hoc_llama_denominator": post_hoc_llama, "window": [SWAP_START, CUTOFF_DATE], "delivered_usd": sum(usd.values()), "chain_volume_usd": sum(vol.values()),
            "oneclick_volume_usd": sum(exp.get(d, 0) for d in ds), "tau_chain_bp": tau_c, "tau_1click_bp": tau_1, "repo_tau_bp": 4.98,
            "H_F5a_supported": abs(tau_1 / 4.98 - 1) <= 0.25, "H_F5a_falsified": abs(tau_1 / 4.98 - 1) > 0.5, "tau_1click_over_repo": tau_1 / 4.98,
            "months": months, "month_deviation_from_window": dev, "H_F5c_supported": all(abs(v) <= 0.3 for v in dev.values()), "H_F5c_falsified": any(abs(v) > 0.5 for v in dev.values()),
            "weekly_corr": corr, "weeks": len(weeks), "H_F5b_supported": corr["total"] is not None and corr["total"] >= 0.5, "H_F5b_falsified": corr["total"] is not None and corr["total"] < 0.2,
            "delivered_usd_by_group": by_group_usd, "mean_near_price": sum(px[d] for d in ds) / len(ds)}


def main() -> int:
    res = {"cutoff_block": 223_088_015, "windows": {"q1_q2": [WINDOW_START, CUTOFF_DATE], "q3_q4": [SWAP_START, CUTOFF_DATE]}, "q1": q1(), "q2": q2(), "q3": q3(), "q4": q4(), "f1": f1(), "f3": f3(), "f2b": f2b(), "f4": f4(), "f5": f5()}
    jobs = [json.loads(l) for l in (OUT / "jobs.jsonl").read_text().splitlines()]
    res["bytes_billed_total"] = sum(j["bytes_billed"] for j in jobs)
    dest = ROOT / "data" / "derived" / "rebuild_results.json"
    dest.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(f"wrote {dest.relative_to(ROOT)} ({sha256(dest)[:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
