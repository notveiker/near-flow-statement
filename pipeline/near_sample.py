"""Stratified random sample of NEAR mainnet history, pulled from the keyless NEARDATA server.

Why this exists: one recent week of blocks cannot show whether NEAR's usage, fees and Intents activity have grown. A
sample spread over the chain's whole life can, with confidence intervals, and it is small enough to pull politely
from one IP (about 22 blocks a minute is what NEARDATA allows us in practice).

Design (frozen in plan.json before any block is read; see docs/history-sample-prereg.md):
  * Strata are calendar quarters (UTC), from the first block to the plan date. Boundaries are found by searching for
    block timestamps, and the heights and timestamps found are written into the plan.
  * Each stratum gets a fixed number of clusters. A cluster is CL contiguous blocks (default 100, about 1.7 minutes).
    Cluster starts are drawn uniformly at random inside the stratum, without overlap, so day of week and hour of day
    are covered by chance and not by us.
  * Contiguous blocks keep transaction-to-receipt links and the prev_hash chain intact inside a cluster, so each
    sealed cluster is checked on its own.
  * The random seed is the hash of the final NEAR block at plan time. Neither we nor anyone else could choose it
    ahead of time. Anyone can re-derive the whole plan from the seed and the boundaries.
  * Clusters are ordered in rounds (cluster 1 of every stratum, then cluster 2 of every stratum, ...), so stopping
    early still leaves a balanced sample.

Layout under --root:
    plan.json, plan.sha256          the frozen design
    clusters/<id>.jsonl.gz          one JSON object per height: {"h": 123, "b": <block or null>}
    clusters/<id>.json              manifest: count, null heights, sha256 of the .gz, first/last hash and time
    part/<id>.jsonl                 open cluster (resumable)
    log.jsonl                       one line per event

Run:
    python3 -m pipeline.near_sample plan   --root data/sample --per-stratum 18 --recent-from 2025-01-01 --recent-per 30
    python3 -m pipeline.near_sample run    --root data/sample
    python3 -m pipeline.near_sample status --root data/sample
    python3 -m pipeline.near_sample verify --root data/sample
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import random
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from pipeline.near_collect import BASE, UA, Bucket, fetch_block

CL = 100  # blocks per cluster
GENESIS_HEIGHT = 9_820_210  # first block NEARDATA serves for mainnet
DEFAULT_PER_MIN = 22.0


# ---------------------------------------------------------------- strata
def quarter_edges(first_ns: int, last_ns: int) -> list[tuple[str, int, int]]:
    """(id, start_ns, end_ns) for every UTC calendar quarter touched by [first_ns, last_ns]; first and last are clipped."""
    first = datetime.fromtimestamp(first_ns / 1e9, timezone.utc)
    last = datetime.fromtimestamp(last_ns / 1e9, timezone.utc)
    out, y, q = [], first.year, (first.month - 1) // 3
    while True:
        s = datetime(y, q * 3 + 1, 1, tzinfo=timezone.utc)
        ny, nq = (y + 1, 0) if q == 3 else (y, q + 1)
        e = datetime(ny, nq * 3 + 1, 1, tzinfo=timezone.utc)
        out.append((f"{y}Q{q + 1}", max(int(s.timestamp() * 1e9), first_ns), min(int(e.timestamp() * 1e9), last_ns)))
        if e > last:
            return out
        y, q = ny, nq


def locate(target_ns: int, probe, lo: tuple[int, int], hi: tuple[int, int], tol_ns: int = 1800 * 10**9, max_iter: int = 14):
    """First block at or after target_ns, found by interpolation search.

    probe(h) -> (height, ts_ns) of the first non-skipped block at or after h. lo and hi are (height, ts_ns) with
    ts(lo) <= target <= ts(hi). Stops within tol_ns of the target; the exact height found is what the plan records.
    """
    (hl, tl), (hh, th) = lo, hi
    best = hi
    for _ in range(max_iter):
        if hh - hl <= 1:
            return hh, th
        frac = (target_ns - tl) / (th - tl) if th > tl else 0.5
        h = int(hl + frac * (hh - hl))
        h = min(max(h, hl + 1), hh - 1)
        h, t = probe(h)
        if abs(t - target_ns) <= tol_ns:
            return h, t
        if t < target_ns:
            hl, tl = h, t
        else:
            hh, th, best = h, t, (h, t)
    return best


# ---------------------------------------------------------------- the plan
def draw_clusters(seed: str, sid: str, h0: int, h1: int, n: int, cl: int = CL) -> list[int]:
    """n non-overlapping cluster starts inside [h0, h1], uniform, deterministic in (seed, stratum)."""
    if (h1 - h0 + 1) < n * cl * 2:
        raise ValueError(f"stratum {sid} is too short for {n} clusters of {cl}")
    r = random.Random(f"{seed}:{sid}")
    got: list[int] = []
    while len(got) < n:
        s = r.randint(h0, h1 - cl + 1)
        if all(abs(s - g) >= cl for g in got):
            got.append(s)
    return got


def build_plan(seed: str, strata: list[dict], cl: int = CL) -> dict:
    """strata: [{id, h0, h1, t0_ns, t1_ns, n}] -> plan with clusters ordered in rounds."""
    clusters = []
    for st in strata:
        starts = draw_clusters(seed, st["id"], st["h0"], st["h1"], st["n"], cl)
        for i, s in enumerate(starts):
            clusters.append({"id": f"{st['id']}_{i + 1:02d}", "stratum": st["id"], "round": i + 1, "start": s, "end": s + cl - 1})
    clusters.sort(key=lambda c: (c["round"], c["stratum"]))
    return {"version": 1, "seed": seed, "cluster_len": cl, "strata": strata, "clusters": clusters}


def plan_bytes(plan: dict) -> bytes:
    return (json.dumps(plan, indent=1, sort_keys=True) + "\n").encode()


def write_plan(root: Path, plan: dict) -> str:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    body = plan_bytes(plan)
    (root / "plan.json").write_bytes(body)
    digest = hashlib.sha256(body).hexdigest()
    (root / "plan.sha256").write_text(f"{digest}  plan.json\n")
    return digest


def load_plan(root: Path) -> dict:
    body = (Path(root) / "plan.json").read_bytes()
    want = (Path(root) / "plan.sha256").read_text().split()[0]
    if hashlib.sha256(body).hexdigest() != want:
        raise SystemExit("plan.json does not match plan.sha256: the design was changed after it was frozen")
    return json.loads(body)


def get_tip(timeout: int = 60) -> tuple[int, str, int]:
    req = urllib.request.Request(f"{BASE}/v0/last_block/final", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        hd = json.loads(r.read())["block"]["header"]
    return hd["height"], hd["hash"], int(hd["timestamp_nanosec"])


def make_probe(bucket: Bucket, fetch=fetch_block):
    """probe(h) -> (height, ts_ns) of the first block at or after h that exists."""
    def probe(h: int):
        for _ in range(60):
            bucket.wait()
            status, blk = fetch(h)
            if status == 429:
                bucket.slow_down()
                time.sleep(30)
                continue
            if status == 404:
                h += 1
                continue
            return h, int(blk["block"]["header"]["timestamp_nanosec"])
        raise RuntimeError(f"could not probe near height {h}")
    return probe


def plan_cmd(root: Path, per_stratum: int, recent_from: str | None, recent_per: int, per_min: float, cl: int = CL) -> None:
    bucket = Bucket(per_min)
    probe = make_probe(bucket)
    tip_h, tip_hash, _ = get_tip()
    tip_h -= 100  # a block that is certainly in the archive
    tip_h, tip_ts = probe(tip_h)
    g_h, g_ts = probe(GENESIS_HEIGHT)
    edges = quarter_edges(g_ts, tip_ts)
    bounds = [(g_h, g_ts)]
    for _, s_ns, _ in edges[1:]:
        h, t = locate(s_ns, probe, bounds[-1], (tip_h, tip_ts))
        bounds.append((h, t))
        print(f"  boundary {datetime.fromtimestamp(s_ns / 1e9, timezone.utc):%Y-%m-%d}: height {h:,}", file=sys.stderr)
    bounds.append((tip_h, tip_ts))
    recent_ns = int(datetime.fromisoformat(recent_from).replace(tzinfo=timezone.utc).timestamp() * 1e9) if recent_from else None
    strata = []
    for i, (sid, s_ns, e_ns) in enumerate(edges):
        (h0, t0), (h1, t1) = bounds[i], bounds[i + 1]
        h1 = h1 - 1 if i < len(edges) - 1 else h1
        n = recent_per if recent_ns is not None and t0 >= recent_ns else per_stratum
        strata.append({"id": sid, "h0": h0, "h1": h1, "t0_ns": t0, "t1_ns": t1, "n": n})
    plan = build_plan(tip_hash, strata, cl)
    plan["frozen_at_tip"] = {"height": tip_h + 100, "hash": tip_hash}
    digest = write_plan(root, plan)
    total = len(plan["clusters"]) * cl
    print(f"plan: {len(strata)} strata, {len(plan['clusters'])} clusters, {total:,} blocks; sha256 {digest}")
    print(f"at {per_min:.0f} blocks/min that is about {total / per_min / 60:.1f} hours")


# ---------------------------------------------------------------- store
class Clusters:
    def __init__(self, root: Path):
        self.root = Path(root)
        for d in ("clusters", "part"):
            (self.root / d).mkdir(parents=True, exist_ok=True)
        self.logf = open(self.root / "log.jsonl", "a", buffering=1)

    def close(self) -> None:
        self.logf.close()

    def log(self, **kw) -> None:
        kw["t"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.logf.write(json.dumps(kw, separators=(",", ":")) + "\n")

    def done(self, cid: str) -> bool:
        return (self.root / "clusters" / f"{cid}.json").exists()

    def part(self, cid: str) -> Path:
        return self.root / "part" / f"{cid}.jsonl"

    def have(self, cid: str) -> dict[int, object]:
        p, rows, good = self.part(cid), {}, 0
        if p.exists():
            with open(p, "rb") as f:
                for line in f:
                    try:
                        d = json.loads(line)
                        rows[d["h"]] = d["b"]
                        good += len(line)
                    except (json.JSONDecodeError, KeyError):
                        break  # torn last line from a stopped run
            if good < p.stat().st_size:
                with open(p, "r+b") as f:
                    f.truncate(good)
        return rows

    def add(self, cid: str, h: int, blk) -> None:
        with open(self.part(cid), "a") as f:
            f.write(json.dumps({"h": h, "b": blk}, separators=(",", ":")) + "\n")

    def seal(self, c: dict, rows: dict[int, object]) -> None:
        a, b = c["start"], c["end"]
        body = "".join(json.dumps({"h": h, "b": rows[h]}, separators=(",", ":")) + "\n" for h in range(a, b + 1)).encode()
        gz = self.root / "clusters" / f"{c['id']}.jsonl.gz"
        tmp = gz.with_suffix(".tmp")
        tmp.write_bytes(gzip.compress(body, 6, mtime=0))
        os.replace(tmp, gz)
        real = [rows[h] for h in range(a, b + 1) if rows[h] is not None]

        def hd(x):
            return x["block"]["header"]

        man = {
            "id": c["id"], "stratum": c["stratum"], "start": a, "end": b, "count": len(real),
            "null_heights": [h for h in range(a, b + 1) if rows[h] is None],
            "sha256": hashlib.sha256(gz.read_bytes()).hexdigest(),
            "first_hash": hd(real[0])["hash"] if real else None,
            "last_hash": hd(real[-1])["hash"] if real else None,
            "first_ts_ns": hd(real[0])["timestamp_nanosec"] if real else None,
            "last_ts_ns": hd(real[-1])["timestamp_nanosec"] if real else None,
        }
        (self.root / "clusters" / f"{c['id']}.json").write_text(json.dumps(man, indent=1) + "\n")
        self.part(c["id"]).unlink(missing_ok=True)
        self.log(ev="seal", id=c["id"], count=len(real))


def read_cluster(root: Path, cid: str):
    with gzip.open(Path(root) / "clusters" / f"{cid}.jsonl.gz", "rt") as f:
        for line in f:
            yield json.loads(line)


# ---------------------------------------------------------------- run
def round_caps(plan: dict, early: int | None, recent: int | None) -> dict[str, int]:
    """Per-stratum cap on the draw round to collect. 'Recent' strata are the ones with the plan's largest n."""
    top = max(s["n"] for s in plan["strata"])
    return {s["id"]: (recent if s["n"] == top else early) or s["n"] for s in plan["strata"]}


def run(root: Path, per_min: float = DEFAULT_PER_MIN, fetch=fetch_block, max_clusters: int | None = None, sleep=time.sleep,
        max_round_early: int | None = None, max_round_recent: int | None = None) -> None:
    """Collect the plan's clusters in their frozen order. Optional caps stop a stratum after round k. Clusters are
    exchangeable uniform draws, so the first k of a stratum are themselves a uniform random sample of it."""
    plan = load_plan(root)
    caps = round_caps(plan, max_round_early, max_round_recent)
    st, bucket = Clusters(root), Bucket(per_min)
    st.log(ev="start", per_min=per_min, plan_sha=hashlib.sha256(plan_bytes(plan)).hexdigest())
    sealed = 0
    try:
        for c in plan["clusters"]:
            if st.done(c["id"]) or c["round"] > caps[c["stratum"]]:
                continue
            if max_clusters is not None and sealed >= max_clusters:
                return
            rows = st.have(c["id"])
            tries: dict[int, int] = {}
            h = c["start"]
            while h <= c["end"]:
                if h in rows:
                    h += 1
                    continue
                bucket.wait()
                try:
                    status, blk = fetch(h)
                except Exception as exc:  # network error: log and retry shortly
                    st.log(ev="error", h=h, err=str(exc)[:200])
                    sleep(5)
                    continue
                if status == 429:
                    bucket.slow_down()
                    st.log(ev="429", h=h, interval=round(bucket.interval, 2))
                    sleep(30)
                    continue
                if status == 404:
                    tries[h] = tries.get(h, 0) + 1
                    if tries[h] < 5:
                        sleep(3)
                        continue
                    st.log(ev="404_stored_as_null", h=h)
                    blk = None
                st.add(c["id"], h, blk)
                rows[h] = blk
                h += 1
            st.seal(c, rows)
            sealed += 1
    finally:
        st.close()


# ---------------------------------------------------------------- verify and status
def verify(root: Path) -> dict:
    """Plan hash, every sealed cluster's sha256, heights, chain inside the cluster, and membership in the plan."""
    root = Path(root)
    plan = load_plan(root)
    by_id = {c["id"]: c for c in plan["clusters"]}
    strata = {s["id"]: s for s in plan["strata"]}
    bad, n, blocks = [], 0, 0
    for p in sorted((root / "clusters").glob("*.json")):
        cid = p.stem
        man = json.loads(p.read_text())
        if cid not in by_id:
            bad.append((cid, "not_in_plan"))
            continue
        c = by_id[cid]
        gz = root / "clusters" / f"{cid}.jsonl.gz"
        if hashlib.sha256(gz.read_bytes()).hexdigest() != man["sha256"]:
            bad.append((cid, "sha256"))
            continue
        s = strata[c["stratum"]]
        last, seen = None, 0
        for d in read_cluster(root, cid):
            if d["h"] != c["start"] + seen:
                bad.append((cid, "height_order"))
                break
            seen += 1
            blk = d["b"]
            if blk is None:
                continue
            hd = blk["block"]["header"]
            if hd["height"] != d["h"]:
                bad.append((cid, "height"))
            if last is not None and hd["prev_hash"] != last:
                bad.append((cid, "prev_hash"))
            if not (s["t0_ns"] <= int(hd["timestamp_nanosec"]) <= s["t1_ns"]):
                bad.append((cid, "outside_stratum"))
            last = hd["hash"]
            blocks += 1
        if seen != c["end"] - c["start"] + 1:
            bad.append((cid, "length"))
        n += 1
    return {"clusters": n, "blocks": blocks, "planned": len(plan["clusters"]), "bad": bad}


def status(root: Path) -> None:
    plan = load_plan(root)
    done = {p.stem for p in (Path(root) / "clusters").glob("*.json")}
    per: dict[str, list[int]] = {}
    for c in plan["clusters"]:
        d = per.setdefault(c["stratum"], [0, 0])
        d[1] += 1
        d[0] += c["id"] in done
    print(f"{len(done)} of {len(plan['clusters'])} clusters sealed")
    print(" ".join(f"{k}:{v[0]}/{v[1]}" for k, v in sorted(per.items())))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("plan", "run", "status", "verify"):
        p = sub.add_parser(n)
        p.add_argument("--root", required=True)
        if n in ("plan", "run"):
            p.add_argument("--per-min", type=float, default=DEFAULT_PER_MIN)
        if n == "run":
            p.add_argument("--max-round-early", type=int, default=None, help="stop the lighter-allocated (earlier) strata after this draw round")
            p.add_argument("--max-round-recent", type=int, default=None, help="stop the heavier-allocated (recent) strata after this draw round")
        if n == "plan":
            p.add_argument("--per-stratum", type=int, default=18)
            p.add_argument("--recent-from", default=None, help="strata starting on or after this date get --recent-per clusters")
            p.add_argument("--recent-per", type=int, default=30)
    a = ap.parse_args(argv)
    if getattr(a, "per_min", 0) > 170:
        print("refusing --per-min above 170 (NEARDATA's published limit is 180)", file=sys.stderr)
        return 2
    root = Path(a.root)
    if a.cmd == "plan":
        if (root / "plan.json").exists():
            print("plan.json already exists and is frozen; use a new --root to make a new plan", file=sys.stderr)
            return 2
        plan_cmd(root, a.per_stratum, a.recent_from, a.recent_per, a.per_min)
    elif a.cmd == "run":
        run(root, a.per_min, max_round_early=a.max_round_early, max_round_recent=a.max_round_recent)
    elif a.cmd == "status":
        status(root)
    else:
        r = verify(root)
        print(json.dumps(r))
        return 1 if r["bad"] else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
