"""Run every sql/*.sql against the NEAR BigQuery public dataset and save results to data/raw/bq/.

Needs the `bq` CLI (Google Cloud SDK) authenticated to a project. Each query is dry-run first,
then run with --maximum_bytes_billed so it cannot exceed its cap. The dry-run estimate of the bytes
each query processes is recorded in data/MANIFEST.json (bytes_processed_estimate).

Run:  python3 -m pipeline.bq_run              (all queries)
      python3 -m pipeline.bq_run staking      (only files whose name contains "staking")
Env:  NFS_BQ_MAX_GB (default 120) caps each query; NFS_BQ_PROJECT overrides the billing project.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

from .common import RAW, ROOT, env, record

SQL = ROOT / "sql"


def bq(args: list[str]) -> str:
    project = env("NFS_BQ_PROJECT")
    base = ["bq", "--quiet", "--headless"] + ([f"--project_id={project}"] if project else [])
    out = subprocess.run(base + args, capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or out.stdout.strip())
    return out.stdout


def dry_run_bytes(query: str) -> int:
    msg = bq(["query", "--dry_run", "--use_legacy_sql=false", "\n" + query])
    m = re.search(r"process (?:upper bound of )?(\d+) bytes", msg)
    if not m:
        raise RuntimeError(f"could not read dry-run size: {msg}")
    return int(m.group(1))


def run(path) -> None:
    query = path.read_text(encoding="utf-8")
    cap = int(float(env("NFS_BQ_MAX_GB", "120")) * 1e9)
    est = dry_run_bytes(query)
    if est > cap:
        raise RuntimeError(f"{path.name}: dry run {est/1e9:.1f} GB exceeds cap {cap/1e9:.0f} GB")
    out = bq(["query", "--use_legacy_sql=false", f"--maximum_bytes_billed={cap}",
              "--format=json", "--max_rows=1000000", "\n" + query])
    rows = json.loads(out or "[]")
    dest = RAW / "bq" / f"{path.stem}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(rows, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    record(dest, f"bigquery: sql/{path.name}", {"bytes_processed_estimate": est, "rows": len(rows)})
    print(f"ok    {path.name}: {len(rows)} rows, ~{est/1e9:.1f} GB")


def main(argv: list[str]) -> int:
    pattern = argv[0] if argv else ""
    # spike_ files are one-off probes; h1b_ files are staged (c -> a -> b) and large (a is ~262 GB),
    # so they run only when named explicitly, e.g. NFS_BQ_MAX_GB=270 python3 -m pipeline.bq_run h1b_a
    skip = ("spike_",) if pattern.startswith("h1b_") else ("spike_", "h1b_")
    files = sorted(p for p in SQL.glob("*.sql") if not p.name.startswith(skip) and pattern in p.name)
    failed = 0
    for p in files:
        try:
            run(p)
        except Exception as exc:  # keep previous snapshot
            failed += 1
            print(f"FAIL  {p.name}: {exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
