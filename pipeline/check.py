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

# The lookbehind makes the number start at the beginning of a run of digits, minus signs, dots and commas: without it a long run
# with no marker after it is scanned from every position (quadratic). A minus sign is the hyphen-minus or U+2212 (MINUS SIGN),
# which a typographic edit puts there: a number written with one is read with its sign, and the sign is compared too.
# `LOOSE` counts anything that looks like a marker, so a mistyped one (<!--n:h1a-ratio-->, <!-- n:key-->) is reported instead of
# silently skipped; the descriptive `<!--n:…-->` is exempt.
MARK = re.compile(r"(?<![-\u2212\d.,])([-\u2212\d.,]+)\s*<!--n:([a-z0-9_]+)-->")
TAG = re.compile(r"<!--n:[a-z0-9_]+-->")
LOOSE = re.compile(r"<!--\s*[nN]\s*:(?!…)")


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
    required = [ROOT / "README.md", ROOT / "THESIS.md", ROOT / "PREREG-ADDENDUM.md"]
    files = required + sorted((ROOT / "docs").glob("*.md"))
    for f in files:
        name = str(f.relative_to(ROOT))
        if not f.exists():
            if f in required:  # a copy without THESIS.md must not pass by skipping its markers
                problems.append(f"{name}: missing, so its markers were not checked")
            continue
        text = f.read_text(encoding="utf-8")
        n_tags, n_loose, found = len(TAG.findall(text)), len(LOOSE.findall(text)), MARK.findall(text)
        if n_loose != n_tags:
            problems.append(f"{name}: {n_loose - n_tags} malformed marker(s): write <!--n:key--> with a key made of a-z, 0-9 and _")
        if n_tags != len(found):
            problems.append(f"{name}: {n_tags - len(found)} marker(s) not directly after a number")
        for value, key in found:
            if key not in m:
                problems.append(f"{name}: unknown metric {key}")
                continue
            try:
                same = float(value.replace(",", "").replace("\u2212", "-")) == float(m[key])
            except (ValueError, TypeError):
                problems.append(f"{name}: {key} follows {value!r} or holds {m[key]!r}, which cannot be compared as numbers")
                continue
            if not same:
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
