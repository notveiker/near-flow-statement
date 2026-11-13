"""Staking-flow windows (ask A, 2026-11-13): the H1a query on the eight 90-day windows before 2026-08-07.

Separate from the Intents rebuild (pipeline/rebuild.py bans account_changes, which this query needs). The same discipline:
  * data cutoff 2026-11-04 / block 223,088,015 (every window ends before 2026-08-07; the guard still enforces it);
  * the buyback wallet is never named in a query;
  * every run is dry-run first, capped, given an explicit job id and logged (SQL hash, bytes, output SHA-256) in
    data/raw/windows/jobs.jsonl; the sum of dry-run bytes over all windows must stay at or under 1.5 TB or nothing runs.
Run:  python3 -m pipeline.windows plan | dry | run
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta, timezone

from . import rebuild as rb
from .common import RAW, ROOT, record, sha256

SQLD = ROOT / "sql" / "windows"
OUT = RAW / "windows"
JOBS = OUT / "jobs.jsonl"
N_WINDOWS = 8
LAST_END = date(2026, 8, 6)          # the day before the H1a window starts
TOTAL_CAP_BYTES = int(1.5e12)


def windows() -> list[dict]:
    out, end = [], LAST_END
    for k in range(1, N_WINDOWS + 1):
        start = end - timedelta(days=89)
        out.append({"k": k, "start": start.isoformat(), "end": end.isoformat(), "seed": (start - timedelta(days=1)).isoformat()})
        end = start - timedelta(days=1)
    return out


def guard(sql: str) -> None:
    if rb.FORBIDDEN_BALANCE_ACCOUNT in sql:
        raise ValueError("the buyback wallet is never named")
    for t in ("ft_balances_daily", "circulating_supply"):
        if t in sql:
            raise ValueError(f"banned table {t}")
    scans = len(re.findall(rf"{rb.PUBLIC}\.\w+", sql))
    capped = len(re.findall(rf"block_height\s*<=\s*{rb.CUTOFF_BLOCK}\b", sql))
    if scans and capped < scans:
        raise ValueError("every public-table scan needs block_height <= cutoff")
    for d in re.findall(r"'(\d{4}-\d{2}-\d{2})'", sql):
        if d > rb.CUTOFF_DATE:
            raise ValueError(f"date after cutoff {d}")


def render(kind: str, w: dict) -> tuple[str, str]:
    tpl = (SQLD / f"staking_{kind}_window.sql.tpl").read_text()
    sql = tpl.replace("{START}", w["start"]).replace("{END}", w["end"]).replace("{SEED}", w["seed"])
    stem = f"sw_{kind}_w{w['k']}"
    return stem, sql


def dry_all() -> dict:
    sizes = {}
    for w in windows():
        for kind in ("flows", "endpoints"):
            stem, sql = render(kind, w)
            guard(sql)
            sizes[stem] = rb_dry(sql)
    sizes["_total"] = sum(sizes.values())
    return sizes


def rb_dry(sql: str) -> int:
    msg = rb._bq(["query", "--dry_run", "--use_legacy_sql=false", "\n" + sql])
    m = re.search(r"process (?:upper bound of )?(\d+) bytes", msg)
    if not m:
        raise RuntimeError(msg)
    return int(m.group(1))


def run_all(cap_each_gb: float = 400.0) -> None:
    """Run windows in order (most recent first) while the cumulative dry-run bytes stay at or under 1.5 TB; stop at the first window that
    would pass it and report which windows were not run."""
    sizes = dry_all()
    wins = windows()
    cum, todo, skipped = 0, [], []
    for w in wins:
        unit = sizes[f"sw_flows_w{w['k']}"] + sizes[f"sw_endpoints_w{w['k']}"]
        if not skipped and cum + unit <= TOTAL_CAP_BYTES:
            cum += unit
            todo.append(w)
        else:
            skipped.append(w)
    print(f"all {N_WINDOWS} windows: {sizes['_total']/1e9:.1f} GB; running {len(todo)} ({cum/1e9:.1f} GB, cap {TOTAL_CAP_BYTES/1e9:.0f} GB); NOT run: {[w['k'] for w in skipped]}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "plan_run.json").write_text(json.dumps({"dry_run_gb": {k: round(v / 1e9, 1) for k, v in sizes.items()}, "run": [w["k"] for w in todo],
                                                   "not_run_over_cap": [w["k"] for w in skipped], "cap_gb": TOTAL_CAP_BYTES / 1e9}, indent=1) + "\n")
    record(OUT / "plan_run.json", "dry-run sizes and the windows run under the 1.5 TB cap, pipeline.windows")
    for w in todo:
        for kind in ("flows", "endpoints"):
            stem, sql = render(kind, w)
            dest = OUT / f"{stem}.json"
            if dest.exists():
                continue
            now = datetime.now(timezone.utc)
            job_id = f"{stem}_{now.strftime('%Y%m%dT%H%M%SZ')}"
            out = rb._bq(["query", "--use_legacy_sql=false", f"--job_id={job_id}", f"--maximum_bytes_billed={int(cap_each_gb*1e9)}", "--format=json", "--max_rows=1000000", "\n" + sql])
            rows = json.loads(out or "[]")
            dest.write_text(json.dumps(rows, sort_keys=True, separators=(",", ":")) + "\n")
            rec = rb.job_record(stem, job_id, sql)
            rec.update(rows=len(rows), output=str(dest.relative_to(ROOT)), output_sha256=sha256(dest), window=w)
            with JOBS.open("a") as f:
                f.write(json.dumps(rec, sort_keys=True) + "\n")
            record(dest, f"bigquery job {job_id}: sql/windows/staking_{kind}_window.sql.tpl", {"rows": len(rows)})
            record(JOBS, "append-only log written by pipeline.windows")
            print(f"ok {stem}: {rec['bytes_billed']/1e9:.1f} GB billed, {len(rows)} rows", flush=True)


def run_file(rel: str, cap_gb: float, outdir: str) -> None:
    """Run one SQL file (guarded, dry-run first, capped, logged) and save data/raw/<outdir>/<stem>.json."""
    path = ROOT / rel
    sql = path.read_text()
    guard(sql)
    est = rb_dry(sql)
    if est > cap_gb * 1e9:
        raise SystemExit(f"{rel}: dry run {est/1e9:.1f} GB exceeds cap {cap_gb} GB")
    now = datetime.now(timezone.utc)
    stem = path.stem
    job_id = f"ask_{stem}_{now.strftime('%Y%m%dT%H%M%SZ')}"
    out = rb._bq(["query", "--use_legacy_sql=false", f"--job_id={job_id}", f"--maximum_bytes_billed={int(cap_gb*1e9)}", "--format=json", "--max_rows=1000000", "\n" + sql])
    rows = json.loads(out or "[]")
    dest_dir = RAW / outdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{stem}.json"
    dest.write_text(json.dumps(rows, sort_keys=True, separators=(",", ":")) + "\n")
    rec = rb.job_record(stem, job_id, sql)
    rec.update(rows=len(rows), output=str(dest.relative_to(ROOT)), output_sha256=sha256(dest), sql_file=rel)
    jobs = dest_dir / "jobs.jsonl"
    with jobs.open("a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    record(dest, f"bigquery job {job_id}: {rel}", {"rows": len(rows)})
    record(jobs, "append-only log written by pipeline.windows run-file")
    print(f"ok {stem}: {rec['bytes_billed']/1e9:.1f} GB billed, {len(rows)} rows")


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "plan"
    if cmd == "run-file":
        run_file(argv[1], float(argv[2]), argv[3])
        return 0
    if cmd == "plan":
        print(json.dumps(windows(), indent=1))
    elif cmd == "dry":
        s = dry_all()
        print(json.dumps({k: round(v / 1e9, 1) for k, v in s.items()}, indent=1))
    elif cmd == "run":
        run_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
