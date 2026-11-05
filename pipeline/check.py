"""Integrity checks the screeners (and CI) run.

  --manifest  every file in data/raw matches the SHA-256 recorded in data/MANIFEST.json
  --numbers   every <!--n:key--> marker in README.md / THESIS.md matches data/metrics.json
"""
from __future__ import annotations

import json
import re
import sys

from .common import METRICS, RAW, ROOT, load_manifest, verify_manifest

MARK = re.compile(r"([-\d.,]+)\s*<!--n:([a-z0-9_]+)-->")


def check_manifest() -> list[str]:
    problems = verify_manifest()
    listed = set(load_manifest()["files"])
    for p in RAW.rglob("*"):
        if p.is_file() and str(p.relative_to(RAW.parent)) not in listed:
            problems.append(f"not in manifest: {p.relative_to(ROOT)}")
    return problems


def check_numbers() -> list[str]:
    if not METRICS.exists():
        return ["data/metrics.json missing: run `make compute` first"]
    m = json.loads(METRICS.read_text())
    problems = []
    for name in ("README.md", "THESIS.md"):
        f = ROOT / name
        if not f.exists():
            continue
        for value, key in MARK.findall(f.read_text()):
            if key not in m:
                problems.append(f"{name}: unknown metric {key}")
            elif float(value.replace(",", "")) != float(m[key]):
                problems.append(f"{name}: {key} says {value}, metrics.json says {m[key]}")
    return problems


def main(argv: list[str]) -> int:
    problems = []
    if "--manifest" in argv or not argv:
        problems += check_manifest()
    if "--numbers" in argv or not argv:
        problems += check_numbers()
    for p in problems:
        print(f"FAIL  {p}", file=sys.stderr)
    print("check: PASS" if not problems else f"check: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
