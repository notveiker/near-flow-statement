"""Pull successful 1Click swaps from the NEAR Intents Explorer API and aggregate them by day.

Needs NEAR_INTENTS_EXPLORER_JWT (an "Explorer" key from partners.near-intents.org) in the
environment or in a git-ignored .env file. The API allows 1 request per 5 seconds, so a
30-day pull takes roughly 40 minutes; finished days are cached in .cache/explorer/ and skipped
on the next run.

Committed output (re-used offline): data/raw/explorer/daily.json — per-day totals, top
referral channels, and USD fees routed to each appFee recipient (amountInUsd x bps).
Per-swap rows stay in the git-ignored cache (they are large and are the API's data).

Run: python3 -m pipeline.fetch_explorer 2026-10-06 2026-11-04
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict

from .common import ROOT, add_days, http_json, write_raw

API = "https://explorer.near-intents.org/api/v0/transactions"
CACHE = ROOT / ".cache" / "explorer"
PAUSE = 5.5  # seconds between requests (limit: 1 per 5 s per partner)


def jwt() -> str:
    import os
    tok = os.environ.get("NEAR_INTENTS_EXPLORER_JWT")
    env = ROOT / ".env"
    if not tok and env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("NEAR_INTENTS_EXPLORER_JWT="):
                tok = line.split("=", 1)[1].strip()
    if not tok:
        raise SystemExit("NEAR_INTENTS_EXPLORER_JWT is not set (see README).")
    return tok


def get(params: dict, token: str) -> list:
    import urllib.error
    import urllib.parse
    import urllib.request
    url = f"{API}?{urllib.parse.urlencode(params)}"
    for attempt in range(6):
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json",
                                                   "User-Agent": "near-flow-statement/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code == 429 or exc.code >= 500:
                time.sleep(10 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"explorer request failed: {url}")


def compact(t: dict) -> dict:
    return {"t": t["createdAt"], "oa": t.get("originAsset"), "da": t.get("destinationAsset"),
            "in": float(t.get("amountInUsd") or 0), "out": float(t.get("amountOutUsd") or 0),
            "ref": t.get("referral"), "fees": [[f["recipient"], f["fee"]] for f in (t.get("appFees") or [])],
            "dt": t.get("depositType"), "rt": t.get("recipientType"),
            "k": f'{t.get("depositAddress")}|{t.get("depositMemo") or ""}'}


def pull_day(d: str, token: str) -> list[dict]:
    """All SUCCESS swaps created on UTC day d (newest first, cursor pagination)."""
    path = CACHE / f"{d}.jsonl"
    if path.exists():
        return [json.loads(x) for x in path.read_text().splitlines()]
    rows, seen = [], set()
    params = {"numberOfTransactions": 1000, "statuses": "SUCCESS", "direction": "next",
              "startTimestamp": f"{add_days(d, -1)}T23:59:59.999Z", "endTimestamp": f"{add_days(d, 1)}T00:00:00Z"}
    while True:
        page = get(params, token)
        time.sleep(PAUSE)
        new = [compact(t) for t in page if f'{t.get("depositAddress")}|{t.get("depositMemo") or ""}' not in seen]
        for t in new:
            seen.add(t["k"])
        rows += [t for t in new if t["t"][:10] == d]
        if len(page) < 1000 or not new:
            break
        last = page[-1]
        params["lastDepositAddress"] = last.get("depositAddress")
        if last.get("depositMemo"):
            params["lastDepositMemo"] = last["depositMemo"]
        else:
            params.pop("lastDepositMemo", None)
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(t, separators=(",", ":")) + "\n" for t in rows))
    return rows


def aggregate(d: str, rows: list[dict]) -> dict:
    by_ref = Counter()
    by_ref_n = Counter()
    fee_usd = defaultdict(float)
    by_dt = Counter()
    for t in rows:
        ref = t["ref"] or "(none)"
        by_ref[ref] += t["in"]
        by_ref_n[ref] += 1
        by_dt[t["dt"] or "?"] += t["in"]
        for rcpt, bps in t["fees"]:
            fee_usd[rcpt] += t["in"] * bps / 1e4
    top = [{"referral": k, "usd_in": round(v, 2), "n": by_ref_n[k]} for k, v in by_ref.most_common(25)]
    return {"date": d, "n": len(rows), "usd_in": round(sum(t["in"] for t in rows), 2),
            "usd_out": round(sum(t["out"] for t in rows), 2),
            "n_zero_usd": sum(1 for t in rows if t["in"] == 0),
            "top_referrals": top, "usd_in_by_deposit_type": {k: round(v, 2) for k, v in by_dt.items()},
            "fee_usd_by_recipient": {k: round(v, 2) for k, v in sorted(fee_usd.items(), key=lambda x: -x[1])}}


def main(argv: list[str]) -> int:
    start, end = argv[:2] if len(argv) >= 2 else ("2026-10-06", "2026-11-04")
    token = jwt()
    out_path = ROOT / "data" / "raw" / "explorer" / "daily.json"
    existing = {x["date"]: x for x in json.loads(out_path.read_text())["days"]} if out_path.exists() else {}
    d = end
    while d >= start:
        rows = pull_day(d, token)
        existing[d] = aggregate(d, rows)
        print(f"ok    {d}: {len(rows)} swaps, ${existing[d]['usd_in']/1e6:.1f}M in", flush=True)
        d = add_days(d, -1)
    days = [existing[k] for k in sorted(existing)]
    write_raw("explorer/daily.json", {"days": days, "statuses": "SUCCESS",
                                      "note": "fee_usd_by_recipient = sum(amountInUsd * appFee bps / 1e4); an estimate from quoted bps"},
              f"{API}?statuses=SUCCESS (per-day cursor pull, {days[0]['date']}..{days[-1]['date']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
