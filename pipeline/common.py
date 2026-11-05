"""Shared helpers: paths, HTTP with retries, raw snapshots and the SHA-256 manifest.

Standard library only (Python 3.10+), so the offline rebuild needs nothing installed.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
MANIFEST = DATA / "MANIFEST.json"
METRICS = DATA / "metrics.json"
USER_AGENT = "near-flow-statement/0.1 (research; +https://github.com/notveiker/near-flow-statement)"

# One NEAR = 10^24 yoctoNEAR.
YOCTO = 10**24


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def day(ts: int | float) -> str:
    """Unix seconds -> ISO date (UTC)."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()


def add_days(iso: str, n: int) -> str:
    return (date.fromisoformat(iso) + timedelta(days=n)).isoformat()


def http_json(url: str, params: dict | None = None, body: dict | None = None,
              retries: int = 5, timeout: int = 90) -> object:
    """GET (or POST when body is given) a JSON endpoint with exponential backoff."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:  # noqa: PERF203
            last = exc
            code = getattr(exc, "code", None)
            if code is not None and code < 500 and code != 429:
                break
            time.sleep(min(60, 2 ** attempt * 2))
    raise RuntimeError(f"fetch failed: {url}: {last}")


def write_raw(rel: str, obj: object, source: str) -> Path:
    """Write a raw snapshot as canonical JSON and record it in the manifest."""
    path = RAW / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    path.write_text(text + "\n")
    record(path, source)
    return path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {"files": {}}


def record(path: Path, source: str, extra: dict | None = None) -> None:
    m = load_manifest()
    rel = str(path.relative_to(DATA))
    entry = {"sha256": sha256(path), "bytes": path.stat().st_size,
             "source": source, "fetched_at": utc_now()}
    if extra:
        entry.update(extra)
    m["files"][rel] = entry
    MANIFEST.write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")


def verify_manifest() -> list[str]:
    """Return a list of problems (empty list = every raw file matches its recorded hash)."""
    m = load_manifest()
    problems = []
    for rel, entry in sorted(m["files"].items()):
        p = DATA / rel
        if not p.exists():
            problems.append(f"missing: {rel}")
        elif sha256(p) != entry["sha256"]:
            problems.append(f"hash mismatch: {rel}")
    return problems


def read_raw(rel: str) -> object:
    return json.loads((RAW / rel).read_text())


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)
