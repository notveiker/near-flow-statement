"""Integrity checks the screeners (and CI) run.

  --manifest  every file in data/raw matches the SHA-256 recorded in data/MANIFEST.json
  --numbers   every <!--n:key--> marker in README.md, THESIS.md, REPORT.md, PREREG-ADDENDUM.md and docs/*.md
              matches data/metrics.json; every <!--c:key--> marker matches data/derived/census_metrics.json
"""
from __future__ import annotations

import json
import re
import sys

from .common import METRICS, RAW, ROOT, load_manifest, verify_manifest

MARK = re.compile(r"([-\d.,]+)\s*<!--n:([a-z0-9_]+)-->")
TAG = re.compile(r"<!--n:[a-z0-9_]+-->")
CMARK = re.compile(r"([-\d.,]+)\s*<!--c:([a-z0-9_]+)-->")
CTAG = re.compile(r"<!--c:[a-z0-9_]+-->")
CENSUS = ROOT / "data" / "derived" / "census_metrics.json"


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
    files = [ROOT / "README.md", ROOT / "THESIS.md", ROOT / "REPORT.md", ROOT / "PREREG-ADDENDUM.md"] + sorted((ROOT / "docs").glob("*.md"))
    for f in files:
        name = str(f.relative_to(ROOT))
        if not f.exists():
            continue
        text = f.read_text()
        n_tags, found = len(TAG.findall(text)), MARK.findall(text)
        if n_tags != len(found):
            problems.append(f"{name}: {n_tags - len(found)} marker(s) not directly after a number")
        cm = json.loads(CENSUS.read_text()) if CENSUS.exists() else {}
        c_found = CMARK.findall(text)
        if len(CTAG.findall(text)) != len(c_found):
            problems.append(f"{name}: {len(CTAG.findall(text)) - len(c_found)} census marker(s) not directly after a number")
        for value, key in c_found:
            if key not in cm:
                problems.append(f"{name}: unknown census metric {key}")
            elif float(value.replace(",", "")) != float(cm[key]):
                problems.append(f"{name}: {key} says {value}, census_metrics.json says {cm[key]}")
        for value, key in found:
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
