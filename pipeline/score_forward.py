"""Score PREREG.md forward tests F1-F4 exactly as written (standard library only, Python 3.10+).

PREREG.md (frozen 2026-11-05), "Forward tests (resolve before judging)":
  Window: 2026-11-06 00:00 UTC -> 2026-11-13 23:59 UTC. Scoring uses DefiLlama data fetched on or after
  2026-11-14 and the first final RPC block after 2026-11-14 00:00 UTC.
  F1  buybacks.multisignature.near balance at the first final block after 2026-11-14 00:00 UTC is in
      [2.21M, 2.40M] NEAR                                                                      (p = 0.70)
  F2  Mean net supply increase per day (Nearblocks total_supply, daily deltas for 2026-11-06 -> 2026-11-13)
      is in [86.0K, 89.5K] NEAR/day                                                             (p = 0.75)
  F3  Captured take rate (DefiLlama dailyRevenue / dailyVolume, summed over the window) is below 4.0 bp
                                                                                                (p = 0.65)
  F4  NEAR Intents' share of the peer-set volume (reported basis) over the window is >= 50%    (p = 0.70)
  Scoring rules: a forward test with missing data is scored "not scorable". It is never estimated.
                 Every result is published, including misses.

Operational readings (written 2026-11-06 ~22:30-23:40 UTC, i.e. after the window opened at 00:00 UTC, without
reading any scoring-window data; they follow pipeline/compute.py):
  * F1 balance = view_account `amount` (liquid balance), the field the repo's buyback_wallet_near_m uses.
    `locked` is printed alongside. "First final block after T": the lowest-height block whose header timestamp
    is >= T (2026-11-14T00:00:00Z), confirmed to be at or below the network's current final head. Found by
    binary search over heights on archival RPC; heights with no block (skipped) are stepped over.
  * F2 daily delta for day d = total_supply(d) - total_supply(d-1), Nearblocks /v1/charts rows keyed by the
    row's date (YYYY-MM-DD), for d = 2026-11-06 .. 2026-11-13 (8 deltas, needs the 2026-11-05 row). Same
    convention as compute.py `issuance_usd`. Mean = sum / 8. Any missing row -> not scorable.
  * F3 = sum(dailyRevenue) / sum(dailyVolume) over the 8 window days, in bp (x 1e4). Pass iff < 4.0 bp.
    DefiLlama daily points keyed by UTC date of their unix timestamp (compute.py `day()`).
  * F4 = sum(near-intents dailyVolume) / sum over {near-intents, thorchain-dex, chainflip-amm, maya-protocol}
    dailyVolume (the repo's PEERS, reported basis), over the 8 window days. Pass iff >= 50%.
  * DefiLlama: every series must have all 8 window days, and the fetch time must be >= 2026-11-14T00:00Z.
    A missing day or failed fetch in any series a test needs -> that test is "not scorable".
  * Interval bounds are inclusive ([a, b]); boundaries compared on unrounded values.

Modes (run from the repo root):
  python3 -m pipeline.score_forward --score            # real scoring; refuses to run before 2026-11-14 00:00 UTC
  python3 -m pipeline.score_forward --dry-run          # DRY RUN on current data, shifted window; NOT A SCORE
  python3 -m pipeline.score_forward --score --from-snapshot DIR   # re-score offline from a saved snapshot
Every live run writes its raw fetches + result to an output directory (default data/forward/<mode>_<UTC stamp>/).
Standalone: imports nothing from the rest of pipeline/, so it can also be copied and run as a script.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

WINDOW = ("2026-11-06", "2026-11-13")
SCORE_NOT_BEFORE = datetime(2026, 11, 14, 0, 0, tzinfo=timezone.utc)
F1_T = SCORE_NOT_BEFORE
BUYBACK = "buybacks.multisignature.near"
F1_BAND = (2_210_000.0, 2_400_000.0)
F2_BAND = (86_000.0, 89_500.0)
F3_MAX_BP = 4.0
F4_MIN_PCT = 50.0
PEERS = ["near-intents", "thorchain-dex", "chainflip-amm", "maya-protocol"]
LLAMA = "https://api.llama.fi"
NEARBLOCKS = "https://api.nearblocks.io/v1/charts"
RPCS = ["https://archival-rpc.mainnet.fastnear.com", "https://archival-rpc.mainnet.near.org"]
UA = "near-flow-statement/score_forward (research)"
YOCTO = 10**24
NOT_SCORABLE = "not scorable"


# ---------------------------------------------------------------- helpers
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def day_of(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()


def days_between(lo: str, hi: str) -> list[str]:
    a, b = date.fromisoformat(lo), date.fromisoformat(hi)
    return [(a + timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]


def http_json(url: str, body: dict | None = None, tries: int = 5):
    data = json.dumps(body).encode() if body is not None else None
    hdr = {"User-Agent": UA, "Accept": "application/json"}
    if data is not None:
        hdr["Content-Type"] = "application/json"
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data, hdr), timeout=90) as r:
                return json.loads(r.read().decode())
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"GET/POST {url} failed: {last}")


def rpc(method: str, params) -> dict:
    """JSON-RPC result, trying each archival endpoint; raises on error."""
    last = None
    for url in RPCS:
        for _ in range(3):
            try:
                env = http_json(url, {"jsonrpc": "2.0", "id": "f", "method": method, "params": params}, tries=2)
            except RuntimeError as exc:
                last = exc
                continue
            if "result" in env:
                return env["result"]
            last = env.get("error")
            if "UNKNOWN_BLOCK" in json.dumps(last):
                raise LookupError(json.dumps(last))
            time.sleep(1)
        time.sleep(0.25)
    raise RuntimeError(f"rpc {method} {params}: {last}")


def block_at_or_after(h: int, max_skip: int = 50) -> dict | None:
    """Block at height h, or the next existing height (skipped heights have no block)."""
    for k in range(max_skip):
        try:
            return rpc("block", {"block_id": h + k})
        except LookupError:
            continue
    return None


def ts_of(b: dict) -> int:
    return int(b["header"]["timestamp_nanosec"])


# ---------------------------------------------------------------- fetch (live)
def fetch_all(outdir: Path, t_block: datetime) -> dict:
    snap: dict = {"fetched_at": iso(utc_now()), "sources": {}, "errors": {}}

    def keep(name: str, url: str, fn):
        try:
            snap["sources"][name] = {"url": url, "fetched_at": iso(utc_now()), "data": fn()}
        except Exception as exc:  # noqa: BLE001
            snap["errors"][name] = f"{type(exc).__name__}: {exc}"

    for slug in PEERS:
        u = f"{LLAMA}/summary/dexs/{slug}?" + urllib.parse.urlencode(
            {"dataType": "dailyVolume", "excludeTotalDataChartBreakdown": "true"})
        keep(f"llama_volume_{slug}", u, lambda u=u: {"totalDataChart": http_json(u).get("totalDataChart")})
    u = f"{LLAMA}/summary/fees/near-intents?" + urllib.parse.urlencode(
        {"dataType": "dailyRevenue", "excludeTotalDataChartBreakdown": "true"})
    keep("llama_revenue_near-intents", u, lambda: {"totalDataChart": http_json(u).get("totalDataChart")})
    keep("nearblocks_charts", NEARBLOCKS, lambda: http_json(NEARBLOCKS))
    keep("rpc_f1", "|".join(RPCS), lambda: fetch_f1(t_block))
    (outdir / "snapshot.json").write_text(json.dumps(snap, indent=1))
    return snap


def fetch_f1(t: datetime) -> dict:
    """Binary-search the first block with timestamp >= t; read the buyback wallet there."""
    target = int(t.timestamp() * 1e9)
    head = rpc("block", {"finality": "final"})
    head_h, head_ts = head["header"]["height"], ts_of(head)
    if head_ts < target:
        raise RuntimeError(f"final head {head_h} ({head_ts}) is before the target time; nothing final yet")
    # P(x) = "the first existing block at height >= x has timestamp >= target" is monotone in x, so bisect on
    # heights: lo has P false, hi has P true; the answer is block_at_or_after(hi). Skipped heights are harmless.
    cache: dict[int, dict | None] = {}

    def at(x: int) -> dict | None:
        if x not in cache:
            cache[x] = block_at_or_after(x)
        return cache[x]

    def P(x: int) -> bool:
        b = at(x)
        return b is None or ts_of(b) >= target

    hi = head_h
    lo = max(1, head_h - int((head_ts - target) / 0.55e9) - 20_000)  # ~0.6 s per block, generous margin
    while P(lo):
        lo = max(1, lo - 200_000)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if P(mid):
            hi = mid
        else:
            lo = mid
    first = at(hi)
    assert first is not None and ts_of(first) >= target, "search failed"
    prev = rpc("block", {"block_id": first["header"]["prev_hash"]})
    assert ts_of(prev) < target, "previous block is not before the target time"
    final_now = rpc("block", {"finality": "final"})["header"]["height"]
    assert first["header"]["height"] <= final_now, "block not yet final"
    acct = rpc("query", {"request_type": "view_account", "block_id": first["header"]["height"], "account_id": BUYBACK})
    return {"target_utc": iso(t), "block_height": first["header"]["height"], "block_hash": first["header"]["hash"],
            "block_timestamp_ns": ts_of(first), "prev_block_height": prev["header"]["height"],
            "prev_block_timestamp_ns": ts_of(prev), "final_head_at_read": final_now,
            "view_account": acct}


# ---------------------------------------------------------------- scoring (pure, offline)
def llama_days(src: dict | None) -> dict[str, float] | None:
    if not src or not src.get("data") or not src["data"].get("totalDataChart"):
        return None
    return {day_of(t): float(v) for t, v in src["data"]["totalDataChart"]}


def need_days(series: dict[str, float] | None, days: list[str]) -> list[str]:
    if series is None:
        return list(days)
    return [d for d in days if d not in series]


def fetched_ok(src: dict | None, not_before: datetime | None) -> bool:
    if not src:
        return False
    if not_before is None:
        return True
    return datetime.fromisoformat(src["fetched_at"].replace("Z", "+00:00")) >= not_before


def in_band(x: float, band: tuple[float, float]) -> bool:
    return band[0] <= x <= band[1]


def score(snap: dict, window: tuple[str, str], llama_not_before: datetime | None) -> dict:
    days = days_between(*window)
    S = snap["sources"]
    res: dict = {}

    # F1
    f1 = S.get("rpc_f1")
    if not f1 or "view_account" not in f1.get("data", {}):
        res["F1"] = {"result": NOT_SCORABLE, "why": snap["errors"].get("rpc_f1", "no RPC read")}
    else:
        d = f1["data"]
        amt = int(d["view_account"]["amount"]) / YOCTO
        res["F1"] = {"result": "PASS" if in_band(amt, F1_BAND) else "MISS", "balance_near": amt,
                     "locked_near": int(d["view_account"]["locked"]) / YOCTO, "band": F1_BAND,
                     "block_height": d["block_height"], "block_hash": d["block_hash"],
                     "block_timestamp_ns": d["block_timestamp_ns"], "target_utc": d["target_utc"]}

    # F2
    nb = S.get("nearblocks_charts")
    if not nb:
        res["F2"] = {"result": NOT_SCORABLE, "why": snap["errors"].get("nearblocks_charts", "no data")}
    else:
        sup = {r["date"][:10]: int(r["total_supply"]) / YOCTO for r in nb["data"]["charts"] if r.get("total_supply")}
        prev = (date.fromisoformat(days[0]) - timedelta(days=1)).isoformat()
        missing = [d for d in [prev] + days if d not in sup]
        if missing:
            res["F2"] = {"result": NOT_SCORABLE, "why": f"Nearblocks total_supply missing for {missing}"}
        else:
            deltas = {d: sup[d] - sup[(date.fromisoformat(d) - timedelta(days=1)).isoformat()] for d in days}
            mean = sum(deltas.values()) / len(deltas)
            res["F2"] = {"result": "PASS" if in_band(mean, F2_BAND) else "MISS", "mean_near_per_day": mean,
                         "band": F2_BAND, "daily_deltas": deltas, "n_deltas": len(deltas)}

    # F3
    rev = S.get("llama_revenue_near-intents")
    vol = S.get("llama_volume_near-intents")
    rs, vs = llama_days(rev), llama_days(vol)
    miss = {"revenue": need_days(rs, days), "volume": need_days(vs, days)}
    if not (fetched_ok(rev, llama_not_before) and fetched_ok(vol, llama_not_before)):
        res["F3"] = {"result": NOT_SCORABLE, "why": "DefiLlama fetch missing or fetched before 2026-11-14"}
    elif miss["revenue"] or miss["volume"]:
        res["F3"] = {"result": NOT_SCORABLE, "why": f"missing days {miss}"}
    else:
        r_sum = sum(rs[d] for d in days)
        v_sum = sum(vs[d] for d in days)
        if v_sum <= 0:
            res["F3"] = {"result": NOT_SCORABLE, "why": "zero volume"}
        else:
            bp = r_sum / v_sum * 1e4
            res["F3"] = {"result": "PASS" if bp < F3_MAX_BP else "MISS", "take_rate_bp": bp,
                         "revenue_usd": r_sum, "volume_usd": v_sum, "threshold_bp": F3_MAX_BP}

    # F4
    srcs = {p: S.get(f"llama_volume_{p}") for p in PEERS}
    ser = {p: llama_days(s) for p, s in srcs.items()}
    miss = {p: need_days(ser[p], days) for p in PEERS}
    if not all(fetched_ok(s, llama_not_before) for s in srcs.values()):
        res["F4"] = {"result": NOT_SCORABLE, "why": "a DefiLlama peer fetch is missing or before 2026-11-14"}
    elif any(miss.values()):
        res["F4"] = {"result": NOT_SCORABLE, "why": f"missing days {({k: v for k, v in miss.items() if v})}"}
    else:
        sums = {p: sum(ser[p][d] for d in days) for p in PEERS}
        tot = sum(sums.values())
        share = sums["near-intents"] / tot * 100 if tot else float("nan")
        res["F4"] = {"result": "PASS" if share >= F4_MIN_PCT else "MISS", "intents_share_pct": share,
                     "volume_usd_by_venue": sums, "threshold_pct": F4_MIN_PCT}
    return res


# ---------------------------------------------------------------- main
def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--score", action="store_true", help="real scoring (only on/after 2026-11-14 00:00 UTC)")
    g.add_argument("--dry-run", action="store_true", help="exercise the code on current data; NOT A SCORE")
    ap.add_argument("--from-snapshot", type=Path, help="score offline from DIR/snapshot.json")
    ap.add_argument("--out", type=Path, help="output directory")
    a = ap.parse_args(argv)
    now = utc_now()

    if a.score:
        mode, window, t_block, llama_nb = "score", WINDOW, F1_T, SCORE_NOT_BEFORE
        if a.from_snapshot is None and now < SCORE_NOT_BEFORE:
            print(f"refusing to score: it is {iso(now)}, scoring opens {iso(SCORE_NOT_BEFORE)} (PREREG.md).",
                  file=sys.stderr)
            return 2
    else:
        # DRY RUN: same code, shifted to the last 8 complete UTC days and today's 00:00 UTC block.
        mode = "DRY-RUN"
        today = now.date()
        window = ((today - timedelta(days=8)).isoformat(), (today - timedelta(days=1)).isoformat())
        t_block = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        llama_nb = None
        print("=" * 78 + "\nDRY RUN ON CURRENT DATA - NOT A SCORE OF F1-F4. Window shifted to "
              f"{window[0]}..{window[1]}, block target {iso(t_block)}.\n" + "=" * 78)

    if a.from_snapshot:
        snap = json.loads((a.from_snapshot / "snapshot.json").read_text())
        outdir = a.from_snapshot
        if a.score:
            for k in ("rpc_f1",):
                if k in snap["sources"] and snap["sources"][k]["data"]["target_utc"] != iso(F1_T):
                    print("snapshot F1 target is not 2026-11-14T00:00:00Z; refusing", file=sys.stderr)
                    return 2
    else:
        outdir = a.out or (Path(__file__).resolve().parent.parent / "data" / "forward"
                           / f"{mode.lower()}_{now.strftime('%Y%m%dT%H%M%SZ')}")
        outdir.mkdir(parents=True, exist_ok=True)
        snap = fetch_all(outdir, t_block)

    res = score(snap, window, llama_nb)
    out = {"mode": mode, "is_score": mode == "score", "window": window, "f1_block_target_utc": iso(t_block),
           "scored_at": iso(now), "snapshot_fetched_at": snap.get("fetched_at"),
           "fetch_errors": snap.get("errors"), "urls": {k: v["url"] for k, v in snap["sources"].items()},
           "results": res}
    (outdir / ("result.json" if mode == "score" else "DRY_RUN_result_NOT_A_SCORE.json")).write_text(
        json.dumps(out, indent=1, default=str))
    for k in ("F1", "F2", "F3", "F4"):
        r = res[k]
        val = {kk: vv for kk, vv in r.items() if kk not in ("daily_deltas", "volume_usd_by_venue")}
        print(f"{'[DRY RUN] ' if mode != 'score' else ''}{k}: {r['result']}  {json.dumps(val, default=str)}")
    print(f"wrote {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
