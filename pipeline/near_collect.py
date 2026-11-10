"""Archive NEAR mainnet blocks from the keyless NEARDATA server into sealed, checksummed shards.

Why this exists: BigQuery is one source for the flow statement. This collector builds a second, independent copy of
raw chain data (blocks with every shard, transaction, receipt, execution outcome and state change) so that the
BigQuery-derived findings can be cross-checked against the chain itself, and so that anyone can re-run it.

Source: https://mainnet.neardata.xyz/v0/block/<height> (free, no key). Its published limit is 180 requests a minute
per IP. This tool stays under it with a token bucket (default 150/min), identifies itself in the User-Agent, backs
off on HTTP 429 and never runs more than one process per IP. To go faster, ask FastNear for a higher limit; do not
add IPs.

Layout under --root:
    shards/<start>_<end>.jsonl.gz   one JSON object per height: {"h": 123, "b": <block or null>}
    shards/<start>_<end>.json       manifest: count, null heights, sha256 of the .gz, first/last hash, time range
    part/<start>_<end>.jsonl        open shard (resumable; sealed when it holds every height in its range)
    log.jsonl                       one line per event (start, 429, seal, error)

Shards cover aligned ranges of SHARD heights (default 1000). A height that NEARDATA reports as null (a skipped
height) is stored as null, so a sealed shard is always complete.

Run:
    python3 -m pipeline.near_collect plan   --root /data/near                   # show cursors and the rate plan
    python3 -m pipeline.near_collect run    --root /data/near --backfill-days 5 # forward tail + backward backfill
    python3 -m pipeline.near_collect verify --root /data/near                   # hashes, counts, prev_hash chain
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://mainnet.neardata.xyz"
UA = "near-flow-statement/0.1 (research; +https://github.com/notveiker/near-flow-statement)"
SHARD = 1000
BLOCKS_PER_DAY = 86_400  # about one block a second; used only to size the backfill


# ---------------------------------------------------------------- rate limiting
class Bucket:
    """Token bucket: at most `per_min` requests a minute, with no burst larger than 5."""

    def __init__(self, per_min: float, now=time.monotonic, sleep=time.sleep):
        self.interval = 60.0 / per_min
        self.next = 0.0
        self.now, self.sleep = now, sleep

    def wait(self) -> None:
        t = self.now()
        if t < self.next:
            self.sleep(self.next - t)
            t = self.now()
        self.next = max(self.next, t - 4 * self.interval) + self.interval

    def slow_down(self, factor: float = 1.5, floor_per_min: float = 20) -> None:
        self.interval = min(self.interval * factor, 60.0 / floor_per_min)


# ---------------------------------------------------------------- fetching
def fetch_block(height: int, timeout: int = 60):
    """Return (status, block_or_None). status is 200, 404 or 429; raises on other errors."""
    req = urllib.request.Request(f"{BASE}/v0/block/{height}", headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            return 200, json.loads(raw)
    except urllib.error.HTTPError as e:
        if e.code in (404, 429):
            return e.code, None
        raise


def tip_height(timeout: int = 60) -> int:
    req = urllib.request.Request(f"{BASE}/v0/last_block/final", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["block"]["header"]["height"]


# ---------------------------------------------------------------- shard store
def rng(start: int) -> tuple[int, int]:
    s = start - start % SHARD
    return s, s + SHARD - 1


def name(s: int, e: int) -> str:
    return f"{s:012d}_{e:012d}"


def list_sealed(root: Path) -> list[tuple[int, int]]:
    out = []
    for p in sorted((Path(root) / "shards").glob("*.json")):
        s, e = p.stem.split("_")
        out.append((int(s), int(e)))
    return out


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)
        for d in ("shards", "part"):
            (self.root / d).mkdir(parents=True, exist_ok=True)
        self.logf = open(self.root / "log.jsonl", "a", buffering=1)
        self.cache: dict[int, set[int]] = {}

    def log(self, **kw) -> None:
        kw["t"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.logf.write(json.dumps(kw, separators=(",", ":")) + "\n")

    def sealed(self) -> list[tuple[int, int]]:
        return list_sealed(self.root)

    def is_sealed(self, s: int) -> bool:
        return (self.root / "shards" / f"{name(*rng(s))}.json").exists()

    def part_path(self, s: int) -> Path:
        return self.root / "part" / f"{name(*rng(s))}.jsonl"

    def have(self, s: int) -> set[int]:
        """Heights already stored in the open part of the shard that holds s (cached; a torn last line is cut)."""
        a, _ = rng(s)
        if a in self.cache:
            return self.cache[a]
        p, got, good = self.part_path(s), set(), 0
        if p.exists():
            with open(p, "rb") as f:
                for line in f:
                    try:
                        got.add(json.loads(line)["h"])
                        good += len(line)
                    except (json.JSONDecodeError, KeyError):
                        break  # a torn last line from a stopped run: cut it and refetch that height
            if good < p.stat().st_size:
                with open(p, "r+b") as f:
                    f.truncate(good)
        self.cache[a] = got
        return got

    def add(self, h: int, block) -> None:
        got = self.have(h)
        with open(self.part_path(h), "a") as f:
            f.write(json.dumps({"h": h, "b": block}, separators=(",", ":")) + "\n")
        got.add(h)

    def try_seal(self, s: int) -> bool:
        a, b = rng(s)
        if len(self.have(s)) < SHARD:
            return False
        rows = {}
        with open(self.part_path(s), "rb") as f:
            for line in f:
                d = json.loads(line)
                rows[d["h"]] = d["b"]
        got = rows
        body = "".join(json.dumps({"h": h, "b": got[h]}, separators=(",", ":")) + "\n" for h in range(a, b + 1)).encode()
        gz = self.root / "shards" / f"{name(a, b)}.jsonl.gz"
        tmp = gz.with_suffix(".tmp")
        with open(tmp, "wb") as f:
            f.write(gzip.compress(body, 6, mtime=0))
        os.replace(tmp, gz)
        real = [got[h] for h in range(a, b + 1) if got[h] is not None]
        man = {
            "start": a, "end": b, "count": len(real),
            "null_heights": [h for h in range(a, b + 1) if got[h] is None],
            "sha256": hashlib.sha256(gz.read_bytes()).hexdigest(),
            "first_hash": real[0]["block"]["header"]["hash"] if real else None,
            "first_prev_hash": real[0]["block"]["header"]["prev_hash"] if real else None,
            "last_hash": real[-1]["block"]["header"]["hash"] if real else None,
            "first_ts_ns": real[0]["block"]["header"]["timestamp_nanosec"] if real else None,
            "last_ts_ns": real[-1]["block"]["header"]["timestamp_nanosec"] if real else None,
        }
        (self.root / "shards" / f"{name(a, b)}.json").write_text(json.dumps(man, indent=1) + "\n")
        self.part_path(s).unlink(missing_ok=True)
        self.cache.pop(a, None)
        self.log(ev="seal", start=a, end=b, count=len(real))
        return True


# ---------------------------------------------------------------- verification
def read_shard(root: Path, a: int, b: int):
    with gzip.open(Path(root) / "shards" / f"{name(a, b)}.jsonl.gz", "rt") as f:
        for line in f:
            yield json.loads(line)


def verify(root: Path) -> dict:
    """Re-hash every shard, check counts and the prev_hash chain inside and across adjacent shards."""
    root = Path(root)
    bad, shards, blocks, prev_last = [], 0, 0, None  # prev_last: (end_height, last_hash)
    for a, b in list_sealed(root):
        man = json.loads((root / "shards" / f"{name(a, b)}.json").read_text())
        gz = root / "shards" / f"{name(a, b)}.jsonl.gz"
        if hashlib.sha256(gz.read_bytes()).hexdigest() != man["sha256"]:
            bad.append((a, "sha256"))
            continue
        last_hash = None
        if prev_last and prev_last[0] == a - 1 and man["first_prev_hash"] and prev_last[1] != man["first_prev_hash"]:
            bad.append((a, "chain_across_shards"))
        for d in read_shard(root, a, b):
            blk = d["b"]
            if blk is None:
                continue
            hd = blk["block"]["header"]
            if hd["height"] != d["h"]:
                bad.append((d["h"], "height"))
            if last_hash is not None and hd["prev_hash"] != last_hash:
                bad.append((d["h"], "prev_hash"))
            last_hash = hd["hash"]
            blocks += 1
        if last_hash != man["last_hash"]:
            bad.append((a, "last_hash"))
        shards += 1
        prev_last = (b, man["last_hash"])
    return {"shards": shards, "blocks": blocks, "bad": bad}


# ---------------------------------------------------------------- run loop
def next_missing(store: Store, cursor: int, step: int) -> int | None:
    """Move `cursor` by `step` (+1 or -1) to the next height not yet stored, or None if the shard is sealed."""
    while True:
        if store.is_sealed(cursor):
            cursor = (rng(cursor)[1] + 1) if step > 0 else (rng(cursor)[0] - 1)
            continue
        got = store.have(cursor)
        a, b = rng(cursor)
        order = range(a, b + 1) if step > 0 else range(b, a - 1, -1)
        for h in order:
            if h not in got:
                return h
        store.try_seal(cursor)
        cursor = (b + 1) if step > 0 else (a - 1)


def run(root: Path, backfill_days: float, per_min: float, stop_at_tip_lag: int = 3) -> None:
    store, bucket = Store(root), Bucket(per_min)
    tip = tip_height()
    fwd = tip - tip % SHARD if not store.sealed() else max(e for _, e in store.sealed()) + 1
    bwd = fwd - 1
    floor = bwd - int(backfill_days * BLOCKS_PER_DAY)
    store.log(ev="start", tip=tip, fwd=fwd, bwd=bwd, backfill_floor=floor, per_min=per_min)
    last_tip_check, tries = time.monotonic(), {}
    while True:
        # forward has priority: take it whenever the chain has produced the height, else backfill
        if time.monotonic() - last_tip_check > 20:
            tip, last_tip_check = tip_height(), time.monotonic()
        h = None
        if fwd <= tip - stop_at_tip_lag:
            h = next_missing(store, fwd, +1)
            if h is not None:
                fwd = h
                kind = "fwd"
        if h is None or h > tip - stop_at_tip_lag:
            h = next_missing(store, bwd, -1) if bwd > floor else None
            if h is None or h < floor:
                if fwd > tip - stop_at_tip_lag:
                    time.sleep(2)
                    continue
                break
            bwd, kind = h, "bwd"
        bucket.wait()
        try:
            status, blk = fetch_block(h)
        except Exception as exc:  # network error: log and retry shortly
            store.log(ev="error", h=h, err=str(exc)[:200])
            time.sleep(5)
            continue
        if status == 429:
            bucket.slow_down()
            store.log(ev="429", h=h, interval=round(bucket.interval, 2))
            time.sleep(30)
            continue
        if status == 404:
            tries[h] = tries.get(h, 0) + 1
            if tries[h] < 5:
                store.log(ev="404", h=h, tries=tries[h])
                time.sleep(5)
                continue
            store.log(ev="404_stored_as_null", h=h)
        store.add(h, blk if status == 200 else None)
        store.try_seal(h)
        if kind == "fwd":
            fwd = h + 1
        else:
            bwd = h - 1


def plan(root: Path, per_min: float) -> None:
    st = Store(root).sealed()
    tip = tip_height()
    rate = per_min / 60
    print(f"tip {tip:,}; sealed shards {len(st)}")
    print(f"rate {per_min:.0f}/min = {rate:.2f} blocks/s; the chain makes ~1.03 blocks/s, leaving {max(rate - 1.03, 0):.2f}/s for backfill")
    print(f"backfill per day at that rate: {max(rate - 1.03, 0) * 86400:,.0f} blocks = {max(rate - 1.03, 0) * 86400 / BLOCKS_PER_DAY:.1f} days of chain")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("cmd", choices=["plan", "run", "verify"])
    ap.add_argument("--root", required=True)
    ap.add_argument("--per-min", type=float, default=150.0, help="request rate (the server allows 180)")
    ap.add_argument("--backfill-days", type=float, default=5.0)
    a = ap.parse_args(argv)
    if a.per_min > 170:
        print("refusing a rate above 170/min: the server's published limit is 180", file=sys.stderr)
        return 2
    if a.cmd == "plan":
        plan(Path(a.root), a.per_min)
    elif a.cmd == "run":
        run(Path(a.root), a.backfill_days, a.per_min)
    else:
        r = verify(Path(a.root))
        print(json.dumps(r))
        return 1 if r["bad"] else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
