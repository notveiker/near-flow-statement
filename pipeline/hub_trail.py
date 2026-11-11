"""Tier 4: label unlabelled top-100 NEAR receivers by where their NEAR goes. Rules: docs/hub-trail-method.md.

Input: the node census edge list (pipeline/census_graph.py merge output, committed under data/raw/census/).
Output: data/derived/hub_trail.json, with every label and its trail, coverage with and without tier 4, sensitivity
runs (95% threshold, 1 hop), and H1b recomputed under tier 4 as a SIDE REPORT. Nothing here changes the primary
measure, PREREG.md or the rating rule.

    python3 -m pipeline.hub_trail run --edges data/raw/census/edges_<first>_<last>.json.gz
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from .common import DATA, RAW, YOCTO, read_raw, utc_now
from .h1b import _nonexchange, compute as h1b_compute

MIN_SENT_NEAR = 1000
SHARE = 0.80
HOPS = 3
DROP_BELOW = 10  # docs/hub-trail-method.md: fewer than 10 of the 80 reaching tier 4 means the census could not resolve it


def load_edges(path: Path) -> tuple[dict, dict[str, dict[str, int]]]:
    doc = json.loads(gzip.decompress(Path(path).read_bytes()))
    out: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for a, b, _n, y in doc["edges"]:
        out[a][b] += y
    meta = {k: doc[k] for k in ("first_height", "last_height", "shards")}
    return meta, out


def labels() -> tuple[list[dict], set[str], list[str]]:
    """(top-100 rows, labelled set for tiers 1-3, unlabelled candidates in rank order)."""
    a = read_raw("bq/h1b_a_native_flows.json")
    top = sorted((x for x in a if x["leg"] == "top100"), key=lambda x: int(x["rk"]))
    lab: set[str] = set()
    for x in a:
        if x["leg"] == "member":
            lab.add(x["account"])
        elif x["leg"] in ("top100", "hub") and x["tier"] in ("1", "2", "3"):
            lab.add(x["account"])
    for e in read_raw("labels/exchange_accounts.json")["accounts"]:
        lab.add(e["account"])
    cands = [x["account"] for x in top if x["tier"] is None and not _nonexchange(x["account"])]
    return top, lab, cands


def trace(out: dict, base: set[str], cands: list[str], share: float, hops: int, min_sent: int) -> dict[str, dict]:
    """Fixed point: an account joins at depth d if it sent >= min_sent NEAR and >= share of it went to base or depth < d."""
    got: dict[str, dict] = {}
    for depth in range(1, hops + 1):
        known = base | set(got)
        new = {}
        for c in cands:
            if c in got:
                continue
            o = out.get(c, {})
            tot = sum(o.values())
            if tot < min_sent * YOCTO:
                continue
            to_known = sum(v for k, v in o.items() if k in known)
            if to_known / tot >= share:
                dest = sorted(((k, v) for k, v in o.items() if k in known), key=lambda kv: -kv[1])[:5]
                new[c] = {"depth": depth, "sent_near": tot / YOCTO, "share_to_labelled": to_known / tot,
                          "to": [{"account": k, "near": v / YOCTO, "label": "tier4" if k in got else "tier1-3"} for k, v in dest]}
        if not new:
            break
        got.update(new)
    return got


def net_flows() -> dict[str, Decimal]:
    """Window net inflow (NEAR) of each unlabelled top-100 account, with the same filters h1b.py uses."""
    a = read_raw("bq/h1b_a_native_flows.json")
    b = read_raw("bq/h1b_b_wnear_logs.json")
    net: dict[str, Decimal] = defaultdict(Decimal)
    for x in a:
        if x["leg"] == "flow" and x["lvl"] == "4" and x["note"].startswith("kind=transfer;") and not x["note"].endswith(";cp=wrap"):
            v = Decimal(x["near"])
            net[x["exchange"].removeprefix("top100:")] += v if x["direction"] == "in" else -v
    for x in b:
        if x.get("leg") == "flow" and x.get("lvl") == "4":
            v = Decimal(x["near"])
            net[x["exchange"].removeprefix("top100:")] += v if x["direction"] == "in" else -v
    return net


def run(edges_path: Path, out_path: Path) -> dict:
    meta, out = load_edges(edges_path)
    top, base, cands = labels()
    primary = {"tiers_1_3_count": sum(1 for x in top if x["tier"] in ("1", "2", "3"))}
    runs = {}
    for name, share, hops in (("rule", SHARE, HOPS), ("strict_95pct", 0.95, HOPS), ("one_hop", SHARE, 1)):
        runs[name] = trace(out, base, cands, share, hops, MIN_SENT_NEAR)
    main = runs["rule"]
    h = h1b_compute()
    nf = net_flows()
    lower3 = h["total"][3]
    add = sum(nf.get(a, Decimal(0)) for a in main)
    metrics = json.loads((DATA / "metrics.json").read_text())
    gross = Decimal(str(metrics["h1a_gross_issuance_90d_m"])) * 10**6
    cov13 = primary["tiers_1_3_count"]
    cov14 = cov13 + len(main)
    lower4 = lower3 + add
    upper = h["total"][4]
    res = {
        "generated_utc": utc_now(), "census": meta, "rule": {"min_sent_near": MIN_SENT_NEAR, "share": SHARE, "hops": HOPS},
        "candidates": len(cands), "candidates_with_enough_outflow": sum(1 for c in cands if sum(out.get(c, {}).values()) >= MIN_SENT_NEAR * YOCTO),
        "coverage": {"tiers_1_3_pct": cov13, "tiers_1_4_pct": cov14, "tier4_count": len(main)},
        "sensitivity": {k: {"tier4_count": len(v)} for k, v in runs.items()},
        "dropped": len(main) < DROP_BELOW,
        "h1b_side_report": {
            "label": "if tier 4 is accepted; the frozen rule and primary coverage are unchanged",
            "lower_near_m": float(lower4 / 10**6), "primary_lower_near_m": float(lower3 / 10**6), "upper_near_m": float(upper / 10**6),
            "gross_issuance_near_m": float(gross / 10**6), "coverage_pct": cov14,
            "verdict": ("pass" if cov14 >= 50 and lower4 < gross else "fail" if cov14 >= 50 else "inconclusive"),
        },
        "labels": [{"account": a, **v, "window_net_inflow_near": float(nf.get(a, Decimal(0)))} for a, v in sorted(main.items(), key=lambda kv: kv[1]["depth"])],
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run")
    p.add_argument("--edges", required=True)
    p.add_argument("--out", default=str(DATA / "derived" / "hub_trail.json"))
    a = ap.parse_args(argv)
    r = run(Path(a.edges), Path(a.out))
    print(json.dumps({k: r[k] for k in ("census", "candidates", "candidates_with_enough_outflow", "coverage", "sensitivity", "dropped", "h1b_side_report")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
