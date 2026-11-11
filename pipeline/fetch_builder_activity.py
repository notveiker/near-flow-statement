"""Builder adoption from public package registries (no key): npm daily downloads for the packages people use to
build on NEAR and on NEAR Intents, and crates.io totals for the Rust SDK.

Download counts include CI runs and mirrors, so levels overstate people; the series is useful for its shape.

    python3 -m pipeline.fetch_builder_activity
Outputs: data/raw/builders/npm_daily.json, data/raw/builders/crates.json
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from .common import http_json, write_raw

NPM = [
    "@defuse-protocol/one-click-sdk-typescript",   # the 1Click swap API client
    "@defuse-protocol/intents-sdk",
    "near-api-js",
    "@near-js/accounts",
    "@near-js/providers",
    "@near-js/signers",
    "@near-wallet-selector/core",
    "@hot-labs/near-connect",
]
CRATES = ["near-sdk", "near-primitives"]
START = "2025-01-01"


def main() -> int:
    end = datetime.now(timezone.utc).date().isoformat()
    npm = {}
    for pkg in NPM:
        d = http_json(f"https://api.npmjs.org/downloads/range/{START}:{end}/{pkg}")
        npm[pkg] = [[r["day"], r["downloads"]] for r in d["downloads"]]
        print(pkg, sum(r[1] for r in npm[pkg]))
    write_raw("builders/npm_daily.json", {"start": START, "end": end, "packages": npm}, "https://api.npmjs.org/downloads/range")
    crates = {}
    for c in CRATES:
        d = http_json(f"https://crates.io/api/v1/crates/{c}")["crate"]
        crates[c] = {"downloads": d["downloads"], "recent_downloads": d["recent_downloads"], "max_version": d["max_version"],
                     "updated_at": d["updated_at"]}
    write_raw("builders/crates.json", {"asof": end, "crates": crates}, "https://crates.io/api/v1/crates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
