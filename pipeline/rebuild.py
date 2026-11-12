"""Chain rebuild of NEAR Intents (Q1 escrow, Q2 fee-stream switch, Q3 solvers, Q4 non-1Click volume).

Everything that touches BigQuery goes through here so the pre-registered rules are enforced in code:
  * data cutoff: block 223,088,015 / 2026-11-04. Every scan of a public table must carry `block_height <= 223088015`;
    no date after 2026-11-04 may appear in a query.
  * the balance of buybacks.multisignature.near is never read: account_changes, ft_balances_daily and circulating_supply
    are banned tables, and the archival-RPC reader refuses that account.
  * every real run is dry-run first, capped with --maximum_bytes_billed, given an explicit job id, and logged with the
    SQL hash, bytes billed and the SHA-256 of the saved output in data/raw/rebuild/jobs.jsonl.

Run (billing project: NFS_BQ_PROJECT, default below; the Senthos project is not used):
  python3 -m pipeline.rebuild aux              # build the token and price tables (local files only)
  python3 -m pipeline.rebuild dry <stem>       # dry run (bytes only)
  python3 -m pipeline.rebuild run <stem>       # run sql/rebuild/<stem>.sql; saves data/raw/rebuild/<stem>.json for SELECTs
  python3 -m pipeline.rebuild load-aux         # load aux tables into the staging dataset
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

from .common import RAW, ROOT, env, record, sha256

CUTOFF_BLOCK = 223_088_015
CUTOFF_DATE = "2026-11-04"
WINDOW_START = "2026-07-07"      # Q1/Q2 window
SWAP_START = "2026-08-07"        # Q3/Q4 window: the 90 days the Explorer series covers
PROJECT = env("NFS_BQ_PROJECT") or "inlaid-backbone-501715-q6"
DATASET = "nfs_rebuild"
SQL = ROOT / "sql" / "rebuild"
OUT = RAW / "rebuild"
JOBS = OUT / "jobs.jsonl"
BANNED_TABLES = ("account_changes", "ft_balances_daily", "circulating_supply")
ESCROW = "51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe"
FORBIDDEN_BALANCE_ACCOUNT = "buybacks.multisignature.near"
PUBLIC = "crypto_near_mainnet_us"

# Symbols priced from CoinGecko daily closes (data/raw/coingecko). Stable tokens are priced at 1.00 by rule; any other
# symbol stays unpriced and its swaps are counted but not valued.
PRICE_ALIAS = {"BTC": "bitcoin", "WBTC": "bitcoin", "CBBTC": "bitcoin", "NBTC": "bitcoin", "ETH": "ethereum", "WETH": "ethereum",
               "SOL": "solana", "ZEC": "zcash", "XRP": "ripple", "TRX": "tron", "DOGE": "dogecoin", "LTC": "litecoin",
               "BNB": "binancecoin", "NEAR": "near", "WNEAR": "near"}


def is_stable(symbol: str, price: float | None) -> bool:
    """Pre-registered stable rule: symbol contains USD or is DAI, and the token list's snapshot price is within 3% of 1."""
    s = (symbol or "").upper()
    return ("USD" in s or s == "DAI") and price is not None and 0.97 <= price <= 1.03


def guard(sql: str) -> None:
    """Raise if a query could read past the cutoff or read a banned balance table."""
    low = sql.lower()
    for t in BANNED_TABLES:
        if re.search(rf"\b{t}\b", low):
            raise ValueError(f"banned table: {t}")
    scans = len(re.findall(rf"{PUBLIC}\.\w+", sql))
    capped = len(re.findall(rf"block_height\s*<=\s*{CUTOFF_BLOCK}\b", sql))
    if scans and capped < scans:
        raise ValueError(f"{scans} public-table scan(s) but only {capped} block_height <= {CUTOFF_BLOCK} filter(s)")
    for d in re.findall(r"'(\d{4}-\d{2}-\d{2})'", sql):
        if d > CUTOFF_DATE:
            raise ValueError(f"date after cutoff: {d}")


def _bq(args: list[str]) -> str:
    out = subprocess.run(["bq", "--quiet", "--headless", f"--project_id={PROJECT}"] + args, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or out.stdout.strip())
    return out.stdout


def dry(sql: str) -> int:
    guard(sql)
    msg = _bq(["query", "--dry_run", "--use_legacy_sql=false", "\n" + sql])
    m = re.search(r"process (?:upper bound of )?(\d+) bytes", msg)
    if not m:
        raise RuntimeError(f"cannot read dry-run size: {msg}")
    return int(m.group(1))


def _check_heights(rows: list[dict]) -> None:
    for r in rows:
        for k in ("h", "min_h", "max_h", "block_height"):
            if r.get(k) not in (None, "") and int(r[k]) > CUTOFF_BLOCK:
                raise RuntimeError(f"result row past the cutoff block: {k}={r[k]}")
        for k in ("day", "first_day", "last_day"):
            if r.get(k) and str(r[k]) > CUTOFF_DATE:
                raise RuntimeError(f"result row past the cutoff date: {k}={r[k]}")


def job_record(stem: str, job_id: str, sql: str) -> dict:
    info = json.loads(_bq(["show", "-j", "--location=us-east1", "--format=json", job_id]))
    st = info.get("statistics", {})
    return {"stem": stem, "job_id": job_id, "location": "us-east1", "project": PROJECT, "sql_sha256": sha256_text(sql),
            "created_utc": datetime.fromtimestamp(int(st["creationTime"]) / 1000, timezone.utc).isoformat(),
            "ended_utc": datetime.fromtimestamp(int(st["endTime"]) / 1000, timezone.utc).isoformat(),
            "bytes_processed": int(st.get("totalBytesProcessed", 0)), "bytes_billed": int(st.get("query", {}).get("totalBytesBilled", 0))}


def run(stem: str, cap_gb: float = 300.0) -> None:
    path = SQL / f"{stem}.sql"
    sql = path.read_text()
    est = dry(sql)
    cap = int(cap_gb * 1e9)
    if est > cap:
        raise RuntimeError(f"{stem}: dry run {est/1e9:.1f} GB exceeds cap {cap/1e9:.0f} GB")
    now = datetime.now(timezone.utc)
    job_id = f"rb_{stem}_{now.strftime('%Y%m%dT%H%M%SZ')}"
    is_ddl = re.sub(r"(?m)^--.*$", "", sql).lstrip().upper().startswith("CREATE")
    out = _bq(["query", "--use_legacy_sql=false", f"--job_id={job_id}", f"--maximum_bytes_billed={cap}", "--format=json", "--max_rows=1000000", "\n" + sql])
    rec = job_record(stem, job_id, sql)
    if not is_ddl:
        rows = json.loads(out or "[]")
        _check_heights(rows)
        dest = OUT / f"{stem}.json"
        dest.write_text(json.dumps(rows, sort_keys=True, separators=(",", ":")) + "\n")
        record(dest, f"bigquery job {job_id}: sql/rebuild/{stem}.sql", {"rows": len(rows)})
        rec.update(rows=len(rows), output=str(dest.relative_to(ROOT)), output_sha256=sha256(dest))
    OUT.mkdir(parents=True, exist_ok=True)
    with JOBS.open("a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    record(JOBS, "append-only log written by pipeline.rebuild")
    print(f"ok {stem}: job {job_id}, {rec['bytes_billed']/1e9:.1f} GB billed" + ("" if is_ddl else f", {rec['rows']} rows"))


def sha256_text(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode()).hexdigest()


# ------------------------------------------------------------------ aux tables (local files only)

def build_aux() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    toks = json.loads((OUT / "tokens_1click_20261112.json").read_text())
    with (OUT / "aux_tokens.ndjson").open("w") as f:
        for t in sorted(toks, key=lambda x: x["assetId"]):
            f.write(json.dumps({"asset_id": t["assetId"], "symbol": t["symbol"], "decimals": t["decimals"], "blockchain": t["blockchain"],
                                "is_stable": is_stable(t["symbol"], t.get("price"))}, sort_keys=True) + "\n")
    series: dict[str, dict[str, float]] = {}
    maj = json.loads((RAW / "coingecko" / "majors_90d.json").read_text())
    for cg, rows in maj.items():
        series[cg] = {datetime.fromtimestamp(ts / 1000, timezone.utc).date().isoformat(): px for ts, px in rows}
    near = json.loads((RAW / "coingecko" / "near_market_chart_365d.json").read_text())["prices"]
    series["near"] = {datetime.fromtimestamp(ts / 1000, timezone.utc).date().isoformat(): px for ts, px in near}
    days = []
    d = date.fromisoformat(SWAP_START)
    while d.isoformat() <= CUTOFF_DATE:
        days.append(d.isoformat())
        d += timedelta(days=1)
    with (OUT / "aux_prices.ndjson").open("w") as f:
        for sym, cg in sorted(PRICE_ALIAS.items()):
            s = series.get(cg, {})
            if not s:
                continue
            for day in days:
                near_day = min(s, key=lambda k: abs((date.fromisoformat(k) - date.fromisoformat(day)).days))  # nearest day when missing
                f.write(json.dumps({"day": day, "symbol": sym, "usd": s[day] if day in s else s[near_day]}, sort_keys=True) + "\n")
    for n in ("aux_tokens.ndjson", "aux_prices.ndjson"):
        record(OUT / n, "built by pipeline.rebuild build_aux from tokens_1click_20261112.json and data/raw/coingecko")


def load_aux() -> None:
    try:
        _bq(["mk", "--dataset", "--location=us-east1", f"{PROJECT}:{DATASET}"])
    except RuntimeError as exc:
        if "Already Exists" not in str(exc):
            raise
    _bq(["load", "--replace", "--source_format=NEWLINE_DELIMITED_JSON", f"{DATASET}.tokens", str(OUT / "aux_tokens.ndjson"),
         "asset_id:STRING,symbol:STRING,decimals:INTEGER,blockchain:STRING,is_stable:BOOLEAN"])
    _bq(["load", "--replace", "--source_format=NEWLINE_DELIMITED_JSON", f"{DATASET}.prices", str(OUT / "aux_prices.ndjson"),
         "day:DATE,symbol:STRING,usd:FLOAT"])
    print("loaded tokens and prices")


def selftest_sql() -> str:
    return (SQL / "rb_t0_selftest.sql").read_text()


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    if cmd == "aux":
        build_aux()
    elif cmd == "load-aux":
        load_aux()
    elif cmd == "dry":
        print(f"{dry((SQL / (argv[1] + '.sql')).read_text())/1e9:.2f} GB")
    elif cmd == "record":  # log a job that finished but was not logged (DDL runs)
        sql = (SQL / (argv[1] + ".sql")).read_text()
        OUT.mkdir(parents=True, exist_ok=True)
        with JOBS.open("a") as f:
            f.write(json.dumps(job_record(argv[1], argv[2], sql), sort_keys=True) + "\n")
    elif cmd == "run":
        run(argv[1], float(argv[2]) if len(argv) > 2 else 300.0)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
