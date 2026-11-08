"""Integrity checks the screeners (and CI) run.

  python3 -m pipeline.check                 both checks below
  python3 -m pipeline.check --manifest      every file in data/raw matches the SHA-256 recorded in data/MANIFEST.json
  python3 -m pipeline.check --numbers       every <!--n:key--> marker in README.md, THESIS.md, PREREG-ADDENDUM.md and
                                            docs/*.md matches data/metrics.json
  python3 -m pipeline.check --manifest --numbers    the same as no option

Exit status: 0 and `check: PASS` if every check that ran found nothing; 1 and `check: N problem(s)` otherwise (one
`FAIL  ...` line per problem on stderr); 2 for an option it does not know (usage on stderr, nothing is checked and
`check: PASS` is never printed). `-h` / `--help` prints the usage on stdout and exits 0 without checking anything.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

from .common import METRICS, RAW, ROOT, load_manifest, verify_manifest

MARK = re.compile(r"([-\d.,]+)\s*<!--n:([a-z0-9_]+)-->")
TAG = re.compile(r"<!--n:[a-z0-9_]+-->")


def check_manifest() -> list[str]:
    problems = verify_manifest()
    listed = set(load_manifest()["files"])
    for p in RAW.rglob("*"):
        if p.is_symlink():  # rglob does not enter a symlinked directory, so what is behind one would go unchecked
            problems.append(f"symbolic link under data/raw: {p.relative_to(ROOT)}")
        elif p.is_file() and str(p.relative_to(RAW.parent)) not in listed:
            problems.append(f"not in manifest: {p.relative_to(ROOT)}")
    return problems


def check_numbers() -> list[str]:
    if not METRICS.exists():
        return ["data/metrics.json missing: run `make compute` first"]
    m = json.loads(METRICS.read_text(encoding="utf-8"))
    problems = []
    files = [ROOT / "README.md", ROOT / "THESIS.md", ROOT / "PREREG-ADDENDUM.md"] + sorted((ROOT / "docs").glob("*.md"))
    for f in files:
        name = str(f.relative_to(ROOT))
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        n_tags, found = len(TAG.findall(text)), MARK.findall(text)
        if n_tags != len(found):
            problems.append(f"{name}: {n_tags - len(found)} marker(s) not directly after a number")
        for value, key in found:
            if key not in m:
                problems.append(f"{name}: unknown metric {key}")
            elif float(value.replace(",", "")) != float(m[key]):
                problems.append(f"{name}: {key} says {value}, metrics.json says {m[key]}")
    return problems


def main(argv: list[str] | None = None) -> int:
    # An option it does not know must stop here: silently running no check and printing PASS would be a false pass.
    ap = argparse.ArgumentParser(prog="python3 -m pipeline.check", allow_abbrev=False,
                                 description="Offline integrity checks. With neither option, both run.")
    ap.add_argument("--manifest", action="store_true",
                    help="every file in data/raw matches data/MANIFEST.json, and none is missing or unlisted")
    ap.add_argument("--numbers", action="store_true",
                    help="every <!--n:key--> marker in the write-up equals data/metrics.json[key]")
    a = ap.parse_args(argv)
    both = not (a.manifest or a.numbers)
    problems = []
    if a.manifest or both:
        problems += check_manifest()
    if a.numbers or both:
        problems += check_numbers()
    for p in problems:
        print(f"FAIL  {p}", file=sys.stderr)
    print("check: PASS" if not problems else f"check: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
