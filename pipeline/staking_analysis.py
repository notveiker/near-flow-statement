"""Ask A: apply docs/staking-windows-method.md to the saved window outputs. Writes data/derived/staking_windows.json."""
from __future__ import annotations

import itertools
import json
import urllib.request
from datetime import date, datetime, timedelta, timezone
from statistics import median

from .common import RAW, ROOT, sha256, write_raw
from . import windows as W
from .rebuild import CUTOFF_DATE

OUT = RAW / "windows"
H1A_END, H1A_SEED = "2026-11-04", "2026-08-06"


def fetch_prices() -> None:
    """NEAR USD daily from DefiLlama coins (spans of at most 400 days), saved once with SHA-256."""
    p = OUT / "near_price_daily_llama.json"
    if p.exists():
        return
    pts, start = {}, int(datetime(2024, 8, 10, tzinfo=timezone.utc).timestamp())
    while start < datetime(2026, 11, 5, tzinfo=timezone.utc).timestamp():
        u = f"https://coins.llama.fi/chart/coingecko:near?start={start}&span=380&period=1d"
        d = json.load(urllib.request.urlopen(u, timeout=60))["coins"]["coingecko:near"]["prices"]
        for x in d:
            day = datetime.fromtimestamp(x["timestamp"], timezone.utc).date().isoformat()
            if day <= CUTOFF_DATE:          # data cutoff enforced here: nothing after 2026-11-04 is kept
                pts[day] = x["price"]
        start += 380 * 86400
    write_raw("windows/near_price_daily_llama.json", pts, "https://coins.llama.fi/chart/coingecko:near (daily, spans of 380 days)")


def price(px: dict, day: str) -> float:
    d0 = date.fromisoformat(day)
    for k in (0, 1, -1, 2, -2):
        v = px.get((d0 + timedelta(days=k)).isoformat())
        if v:
            return v
    raise KeyError(day)


def rank_corr(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    a, b = rk(x), rk(y)
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = (sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b)) ** 0.5
    return num / den if den else None


def perm_p(x, y, rho):
    n = len(x)
    c = tot = 0
    for p in itertools.permutations(range(n)):
        r = rank_corr(x, [y[i] for i in p])
        tot += 1
        if r is not None and abs(r) >= abs(rho) - 1e-12:
            c += 1
    return c / tot


def window_stats(flows, ends, seed, end, px):
    f = lambda k: sum(float(r[k]) for r in flows)
    rewards, inflow, outflow, gas = f("rewards_near"), f("inflow_near"), f("outflow_near"), f("gas_rebate_near")
    net = outflow - inflow
    e = {r["block_date"]: r for r in ends}
    start_total = float(e[seed]["pool_total_near"])
    end_total = float(e[end]["pool_total_near"])
    return {"seed": seed, "end": end, "days": len(flows), "rewards_near": rewards, "inflow_near": inflow, "outflow_near": outflow, "net_outflow_near": net,
            "net_over_rewards": net / rewards, "pool_total_start_near": start_total, "pool_total_end_near": end_total,
            "net_share_of_stake_pct": net / start_total * 100, "price_start": price(px, seed), "price_end": price(px, end),
            "price_change_pct": (price(px, end) / price(px, seed) - 1) * 100,
            "flow_residual_near": (end_total - start_total) - (rewards + gas + inflow - outflow)}


def main() -> int:
    fetch_prices()
    px = json.loads((OUT / "near_price_daily_llama.json").read_text())
    plan = json.loads((OUT / "plan_run.json").read_text())
    res = {"windows": {}}
    h1 = window_stats(json.loads((RAW / "bq" / "staking_flows_daily.json").read_text()), json.loads((RAW / "bq" / "staking_pool_totals_endpoints.json").read_text()), H1A_SEED, H1A_END, px)
    res["windows"]["H1a"] = h1
    for w in W.windows():
        if w["k"] not in plan["run"]:
            continue
        fl = json.loads((OUT / f"sw_flows_w{w['k']}.json").read_text())
        en = json.loads((OUT / f"sw_endpoints_w{w['k']}.json").read_text())
        s = window_stats(fl, en, w["seed"], w["end"], px)
        s["start"] = w["start"]
        res["windows"][f"W{w['k']}"] = s
    res["not_run_over_cap"] = [f"W{k}" for k in plan["not_run_over_cap"]]
    res["dry_run_total_gb_all_eight"] = plan["dry_run_gb"]["_total"]
    names = list(res["windows"])
    earlier = [n for n in names if n != "H1a"]
    rat = {n: res["windows"][n]["net_over_rewards"] for n in names}
    order = sorted(names, key=lambda n: -rat[n])
    med = median(rat[n] for n in earlier)
    rk = order.index("H1a") + 1
    # The rule as written: unusual = rank 1 or 2 and ratio >= 1.5 x the median of the earlier windows; typical = rank >= 4 or ratio <= 1.2 x that median.
    # Applied literally, including when the median is negative (a 1.5 x a negative median is below any positive ratio). Disclosed in the results.
    unusual = rk <= 2 and rat["H1a"] >= 1.5 * med
    typical = rk >= 4 or rat["H1a"] <= 1.2 * med
    ratio_to_median = rat["H1a"] / med if med > 0 else None
    res["rank"] = {"by_net_over_rewards": rk, "of": len(names), "by_net_outflow_near": sorted(names, key=lambda n: -res["windows"][n]["net_outflow_near"]).index("H1a") + 1,
                   "by_net_share_of_stake": sorted(names, key=lambda n: -res["windows"][n]["net_share_of_stake_pct"]).index("H1a") + 1,
                   "order_by_net_over_rewards": order, "median_of_earlier": med, "h1a_over_median": ratio_to_median, "median_is_negative": med < 0, "max_of_earlier": max(rat[n] for n in earlier), "h1a_over_max_earlier": rat["H1a"] / max(rat[n] for n in earlier), "earlier_windows_with_ratio_ge_3": [n for n in earlier if rat[n] >= 3],
                   "reading": "unusual" if unusual else "typical" if typical else "borderline"}
    pc = [res["windows"][n]["price_change_pct"] for n in names]
    for key, label in (("net_outflow_near", "net_outflow_near"), ("net_share_of_stake_pct", "net_share_of_stake")):
        xs = [res["windows"][n][key] for n in names]
        rho = rank_corr(xs, pc)
        p = perm_p(xs, pc, rho)
        res.setdefault("rank_correlation_with_price_change", {})[label] = {"rho": rho, "perm_p": p, "n": len(names),
            "reading": "associated" if abs(rho) >= 0.6 and p <= 0.10 else "no association" if abs(rho) < 0.3 else "weak"}
    dest = ROOT / "data" / "derived" / "staking_windows.json"
    dest.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(f"wrote {dest.relative_to(ROOT)} ({sha256(dest)[:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
