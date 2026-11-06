"""PREREG H1b/H1c from the committed BigQuery outputs (standard library only).

Inputs (all under data/raw/):
  bq/h1b_a_native_flows.json         native-NEAR legs (sql/h1b_a_native_flows.sql)
  bq/h1b_b_wnear_logs.json           wNEAR legs (sql/h1b_b_wnear_logs.sql)
  rpc/buyback_balance_endpoints.json buybacks.multisignature.near balance at the window endpoint blocks

Rules (PREREG.md, PREREG-ADDENDUM.md "2026-11-06 23:11 UTC: H1b/H1c method"):
  - Net exchange inflow = transfers into the labelled set from outside minus transfers out (boundary).
  - Native = TRANSFER rows (note kind=transfer); rows whose counterparty is wrap.near (cp=wrap) are a
    change of form and are netted out. NEAR attached to function calls is not in the tests.
  - Level 3 (tiers 1-3) = lower bound (unlabelled 0% exchange-bound); level 4 (plus unlabelled
    top-100 receivers) = upper bound (100%). Level 1 = tier-1-only side report.
  - Primary coverage = count share of the top-100 receivers labelled in tiers 1-3.
  - Coverage < 50%: a test passes only if it passes under both bounds, otherwise "inconclusive".
  - Side report: the 100% bound without sourced non-exchange top-100 accounts (pools, intents.near,
    wrap.near, sputnik-dao DAOs), approximated by dropping their level-4 boundary rows.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from .common import YOCTO, read_raw

H1C_MIN = Decimal("0.25")
COVERAGE_MIN_PCT = 50.0
PLAUSIBLE_G_MAX_NEAR = Decimal(10_000_000)


def _nonexchange(acct: str) -> bool:
    return (acct.endswith(".poolv1.near") or acct.endswith(".pool.near") or acct in ("intents.near", "wrap.near")
            or acct.endswith(".sputnik-dao.near"))


def _net(rows: list[dict], keep) -> dict[int, Decimal]:
    out: dict[int, Decimal] = defaultdict(Decimal)
    for x in rows:
        if x["leg"] == "flow" and keep(x):
            v = Decimal(x["near"])
            out[int(x["lvl"])] += v if x["direction"] == "in" else -v
    return out


def compute() -> dict:
    """Full-precision values (Decimal NEAR) behind the metrics."""
    a = read_raw("bq/h1b_a_native_flows.json")
    b = read_raw("bq/h1b_b_wnear_logs.json")
    bal = read_raw("rpc/buyback_balance_endpoints.json")["blocks"]

    top = sorted((x for x in a if x["leg"] == "top100"), key=lambda x: int(x["rk"]))
    if len(top) != 100:
        raise ValueError(f"expected 100 top-100 rows, got {len(top)}")
    tot_in = sum(Decimal(x["near"]) for x in top)

    def labelled(tiers):
        return [x for x in top if x["tier"] is not None and int(x["tier"]) in tiers]

    l13, l1 = labelled((1, 2, 3)), labelled((1,))
    nonex = {"top100:" + x["account"] for x in top if x["tier"] is None and _nonexchange(x["account"])}

    def native(x):
        return x["note"].startswith("kind=transfer;") and not x["note"].endswith(";cp=wrap")

    nat = _net(a, native)
    nat_x = _net(a, lambda x: native(x) and x["exchange"] not in nonex)
    wn = _net(b, lambda x: True)
    wn_x = _net(b, lambda x: x["exchange"] not in nonex)

    lo, hi = "210238033", "223088015"
    buying = Decimal(int(bal[hi]["amount"]) - int(bal[lo]["amount"])) / Decimal(YOCTO)
    return {
        "coverage_count": Decimal(len(l13)), "coverage_tier1_count": Decimal(len(l1)),
        "coverage_inflow": sum(Decimal(x["near"]) for x in l13) / tot_in,
        "coverage_tier1_inflow": sum(Decimal(x["near"]) for x in l1) / tot_in,
        "native": dict(nat), "wnear": dict(wn),
        "total": {k: nat[k] + wn[k] for k in (1, 2, 3, 4)},
        "upper_ex_nonexchange": nat_x[4] + wn_x[4],
        "buying": buying,
    }


def _both(lower_ok: bool, upper_ok: bool, coverage_pct: float) -> str:
    if coverage_pct >= COVERAGE_MIN_PCT:
        return "pass" if lower_ok else "fail"
    return "pass" if lower_ok and upper_ok else "inconclusive"


def h1b(m: dict) -> None:
    c = compute()
    lower, upper, tier1 = c["total"][3], c["total"][4], c["total"][1]
    cov = float(c["coverage_count"])  # out of 100, so count == percent
    m["h1b_coverage_count_pct"] = round(cov, 1)
    m["h1b_coverage_tier1_count_pct"] = round(float(c["coverage_tier1_count"]), 1)
    m["h1b_coverage_inflow_pct"] = round(float(c["coverage_inflow"] * 100), 1)
    m["h1b_coverage_tier1_inflow_pct"] = round(float(c["coverage_tier1_inflow"] * 100), 1)
    m["h1b_net_inflow_lower_m"] = round(float(lower / 10**6), 2)
    m["h1b_net_inflow_upper_m"] = round(float(upper / 10**6), 2)
    m["h1b_net_inflow_tier1_m"] = round(float(tier1 / 10**6), 2)
    m["h1b_net_inflow_upper_ex_nonexchange_m"] = round(float(c["upper_ex_nonexchange"] / 10**6), 2)
    m["h1b_native_lower_m"] = round(float(c["native"][3] / 10**6), 2)
    m["h1b_native_upper_m"] = round(float(c["native"][4] / 10**6), 2)
    m["h1b_wnear_lower_near"] = round(float(c["wnear"][3]), 2)
    m["h1b_wnear_upper_m"] = round(float(c["wnear"][4] / 10**6), 2)
    m["h1c_identified_buying_m"] = round(float(c["buying"] / 10**6), 2)
    m["h1c_ratio_lower_pct"] = round(float(c["buying"] / lower * 100), 2)
    m["h1c_ratio_upper_pct"] = round(float(c["buying"] / upper * 100), 2)

    g_m = m.get("h1a_gross_issuance_90d_m")
    if g_m is not None:
        g = Decimal(str(g_m)) * 10**6
        m["h1b_verdict"] = _both(lower < g, upper < g, cov)
    elif upper > PLAUSIBLE_G_MAX_NEAR and cov < COVERAGE_MIN_PCT:
        m["h1b_verdict"] = "inconclusive (upper bound exceeds any plausible gross issuance)"
    else:
        m["h1b_verdict"] = "pending"

    def h1c_ok(net: Decimal) -> bool:
        return net > 0 and c["buying"] / net >= H1C_MIN

    m["h1c_verdict"] = _both(h1c_ok(lower), h1c_ok(upper), cov)
