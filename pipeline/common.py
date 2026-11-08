"""Shared helpers: paths, HTTP with retries, raw snapshots and the SHA-256 manifest.

Standard library only (Python 3.10+), so the offline rebuild needs nothing installed.

Every text file this package reads or writes is UTF-8 with LF line endings, whatever the locale or the operating
system. Raw snapshots and the manifest are byte-hashed, and the platform defaults differ: text mode writes CRLF on
Windows, and a non-UTF-8 locale cannot read the UTF-8 write-up that `python3 -m pipeline.check --numbers` scans.
Readers pass encoding="utf-8" and writers pass encoding="utf-8", newline="\\n".

A URL that goes into a `source` or `note` field of data/MANIFEST.json or data/raw/ must carry no credential:
`endpoint_origin` reduces an endpoint to scheme and host, and `record` refuses text with a user:password@ part or a
key-like query parameter.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
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
    refuse_credentials(source, "the source of " + rel)  # before anything is written: the file and its entry stay in step
    path = RAW / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    path.write_text(text + "\n", encoding="utf-8", newline="\n")
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
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"files": {}}


# A user:password@ part in a URL, or a query parameter whose name says it is a key, token or secret (api_key, apikey,
# access_token, x_cg_demo_api_key, client_secret, password, jwt, key, sig, auth ...). Not "design", "author" or "keyword".
# On purpose it fails closed: any parameter name containing token, secret, passw, apikey or jwt is refused (so tokens_sold
# would be too). A fetcher with such a URL should record endpoint_origin(url) or a keyless description instead.
_URL_USERINFO = re.compile(r"://[^\s/?#@]*@")
_URL_KEY_PARAM = re.compile(
    r"(?i)[?&;](?:[^=&;#\s]*(?:token|secret|passw|apikey|api[_-]?key|jwt)[^=&;#\s]*"
    r"|(?:[^=&;#\s]*[_.-])?(?:key|sig|signature|auth|authorization|pwd))=")


def refuse_credentials(text: str, what: str = "text") -> None:
    """Raise ValueError if `text` holds a URL that carries a credential (user:password@host, ?api_key=...).

    A guard for what goes into data/MANIFEST.json and data/raw/: both are committed, hashed and public."""
    if _URL_USERINFO.search(text) or _URL_KEY_PARAM.search(text):
        raise ValueError(f"refusing to record {what}: it holds a URL with a credential in it (user:password@ or a "
                         "key-like query parameter); record endpoint_origin(url) instead")


def endpoint_origin(url: str) -> str:
    """`url` reduced to scheme://host[:port]: userinfo, path, query and fragment dropped.

    For an endpoint that may carry a key (https://user:pw@rpc.example/KEY?apikey=abc -> https://rpc.example).
    Raises ValueError for anything that is not an absolute http(s) URL, so a malformed value is never recorded as is."""
    parts = urllib.parse.urlsplit(url.strip())
    host = parts.hostname
    if parts.scheme not in ("http", "https") or not host:
        raise ValueError("not an absolute http(s) URL; its text is not echoed because it may hold a key")
    if ":" in host:  # IPv6 literal
        host = f"[{host}]"
    try:
        port = parts.port
    except ValueError:
        raise ValueError("not a valid port in the URL (text not echoed: it may hold a key)") from None
    return f"{parts.scheme}://{host}" + (f":{port}" if port else "")


def record(path: Path, source: str, extra: dict | None = None) -> None:
    refuse_credentials(source, "the source of " + path.name)
    for k, v in (extra or {}).items():
        if isinstance(v, str):
            refuse_credentials(v, f"{k} of {path.name}")
    m = load_manifest()
    rel = str(path.relative_to(DATA))
    entry = {"sha256": sha256(path), "bytes": path.stat().st_size,
             "source": source, "fetched_at": utc_now()}
    if extra:
        entry.update(extra)
    m["files"][rel] = entry
    MANIFEST.write_text(json.dumps(m, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


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
    return json.loads((RAW / rel).read_text(encoding="utf-8"))


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)
