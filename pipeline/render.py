"""Static dashboard: one self-contained page, site/index.html, rebuilt offline from the committed data.

  python3 -m pipeline.render            write site/index.html
  python3 -m pipeline.render --check    exit 1 unless the committed site/ equals a fresh render, byte for byte
                                        (files in site/ that the renderer does not produce are ignored)
  --out DIR          write or check DIR instead of site/ (the tests use a temporary directory)
  --forward-dir DIR  read score_*/result.json from DIR instead of data/forward (the tests inject fixtures)
  --root DIR         read the committed data from another checkout of this repo

Standard library only (Python 3.10+). The page loads no script, font, image or stylesheet from any other file
or host, so it opens from file:// and from GitHub Pages alike. Its one inline script is the live Today row
(LIVE_JS), which reads four public, keyless APIs in the reader's browser and writes text only. The render is
deterministic: no timestamps, git hashes or randomness; the output depends only on the committed files. Links to
repo files are absolute GitHub URLs built from REPO_URL and BRANCH.

Every number the page prints as a value is a span that names where it comes from, so tests/test_render.py can prove
the page cannot drift from the data (the only other numbers are dates, identifiers, window lengths and axis ticks, and
the tests fail on any other):
  data-m="key"           data/metrics.json[key]
  data-s="series.row.f"  data/series.json, e.g. intents_monthly.2026-10.captured_bp
  data-d="expression"    arithmetic over metrics.json keys (only + - * / and parentheses)
  data-k="name"          a threshold fixed in PREREG.md (CONSTS below; the tests compare each with the frozen text)
  data-f="F1.balance_near"  a scored forward test (data/forward/score_*/result.json, only when is_score is true)
  data-r="bytes:sql/x.sql"  a fact read from a repo file: its size in bytes, the number of very long lines the page
                         cuts from it (cut:), or the time
                         data/MANIFEST.json records for a file (stamp:raw/bq/x.json)
Tables of raw or series rows carry data-raw / data-series, one data-k per row and one data-c per column.

The charts carry the numbers they draw, so the tests can check geometry as well as text: every SVG panel is a
<g class="panel"> that states its kind and axis (data-kind, data-lo, data-hi and the plot box), every bar, column
and segment carries data-v (the value it is drawn from; data-lv is the value its label prints when that differs),
and each bar row or column group is a <g class="row" data-row> or <g class="col" data-cat>. A vertical marker on a
line chart carries data-i (the index of the point it stands on) and data-date. The panels of a figure with two or
more are titled "A. ", "B. " ..., which is what a caption's "Panel A" refers to.

The page is written with newlines between block-level tags and between the children of a chart (see break_lines), so
that no line is longer than a file viewer can show; they are placed only where a browser ignores whitespace, and the
tests check that the page is otherwise the same.
"""
from __future__ import annotations

import argparse
import ast
import csv
import functools
import hashlib
import html
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from . import score_forward as sf
from .common import ROOT
from .h1b import COVERAGE_MIN_PCT, H1C_MIN, _nonexchange

REPO_URL = "https://github.com/notveiker/near-flow-statement"
BRANCH = "main"
SITE_DIR = "site"
PAGE_NAME = "index.html"

# PREREG.md is frozen (git tag prereg-freeze, commit 413d776). The page prints the hash of the file it was built from.
FROZEN_PREREG_SHA256 = "19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240"
FREEZE_TAG = "prereg-freeze"
FREEZE_COMMIT = "413d776"
FREEZE_UTC = "2026-11-05 22:53:29"   # commit time of FREEZE_COMMIT (README.md and the 2026-11-07 addendum entry state it; a test compares)

# Thresholds and shares fixed in PREREG.md: name -> (value, shown text, scale). value == float(text) * scale.
# tests/test_render.py compares each with the frozen text; the forward-test bands come from pipeline/score_forward.py.
CONSTS: dict[str, tuple[float, str, float]] = {
    "h1a_pass_below_x": (0.5, "0.5", 1.0),                      # H1a: net staking outflow < 50% of staking rewards
    "staking_rewards_share_pct": (90.0, "90", 1.0),             # staking rewards = 90% of gross issuance
    "h1b_coverage_min_pct": (float(COVERAGE_MIN_PCT), "50", 1.0),  # below 50% labelled coverage: ranges
    "h1c_min_pct": (float(H1C_MIN) * 100, "25", 1.0),           # H1c: identified buying / net inflow >= 25%
    "f1_lo": (sf.F1_BAND[0], "2.21", 1e6), "f1_hi": (sf.F1_BAND[1], "2.40", 1e6),
    "f2_lo": (sf.F2_BAND[0], "86.0", 1e3), "f2_hi": (sf.F2_BAND[1], "89.5", 1e3),
    "f3_max_bp": (sf.F3_MAX_BP, "4.0", 1.0), "f4_min_pct": (sf.F4_MIN_PCT, "50", 1.0),
}

SCORE_FOLDER = re.compile(r"score_[0-9]{8}T[0-9]{6}Z")   # what pipeline.score_forward --score names its folder (ASCII digits)
# The most ticks one axis of the forward-test card may draw. The committed axes draw 4 or 5, and one tick is drawn for every
# step an observed value lies outside them, so a corrupt value (1e6 basis points, 1e9 NEAR a day) made a page of 150 MB, or
# no page. This many ticks still draws every value the scorer can really produce: an F3 take rate of about 400 bp, an F2 mean
# of about 870 thousand NEAR a day, an F1 balance of about 40 million NEAR. Beyond that the render stops and says why.
MAX_AXIS_TICKS = 200

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

# Smallest drawn sizes, so a tiny value stays visible. tests/test_render.py pins them with literals.
MIN_BAR = 1.5     # horizontal bar length
MIN_SEG = 1.0     # length of a segment of a stacked bar
SEG_GAP = 2       # gap left after every segment but the last
MIN_COL = 1.0     # column height
PREREG_ANCHOR = "what-we-had-already-seen-when-we-froze-this"  # GitHub's anchor for that heading of PREREG.md


# ------------------------------------------------------------------ text helpers
def esc(s: object) -> str:
    """Escape for HTML text and attribute values. Every string that enters the page goes through this."""
    return html.escape(str(s), quote=True)


def n1(x: float) -> str:
    """SVG coordinate: at most one decimal, no trailing zero, no negative zero."""
    s = f"{x:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    return "0" if s in ("-0", "-0.0") else s


def dv(x: float) -> str:
    """A value as it goes into a data-v attribute: eight significant digits, no trailing zeros."""
    return format(float(x), ".8g")


def fmt_value(v: object, dec: int | None = None) -> str:
    """A number as the page shows it: thousands separators, decimals as in the metric (or as asked)."""
    if isinstance(v, bool):
        raise TypeError("booleans are not numbers")
    if isinstance(v, int):
        return f"{v:,}"
    f = float(v)  # type: ignore[arg-type]
    if dec is None:
        r = repr(f)
        dec = len(r.split(".")[1]) if "." in r and "e" not in r else 0
    s = f"{f:,.{dec}f}"
    return "0" if s in ("-0", "-0.0", "-0.00") else s


def date_short(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{MONTHS[d.month - 1]} {d.day}"


def eval_expr(expr: str, env: dict) -> float:
    """Arithmetic over metric keys: + - * / and parentheses only (no calls, attributes or subscripts)."""
    def ev(n: ast.AST) -> float:
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return n.value
        if isinstance(n, ast.Name):
            return float(env[n.id])
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -ev(n.operand)
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Add):
                return a + b
            if isinstance(n.op, ast.Sub):
                return a - b
            if isinstance(n.op, ast.Mult):
                return a * b
            if isinstance(n.op, ast.Div):
                return a / b
        raise ValueError(f"unsupported expression: {expr!r}")
    return ev(ast.parse(expr, mode="eval"))


def md_inline(s: str) -> str:
    """Minimal markdown for text quoted from PREREG.md: `code` and **bold**; everything else is escaped text."""
    out = esc(s)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)


def _greedy_lines(text: str, max_chars: int) -> list[str]:
    lines: list[str] = []
    cur = ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines or [""]


def wrap_words(text: str, max_chars: int) -> list[str]:
    """Wrap at max_chars, then at the narrowest width that keeps the same number of lines, so the lines come out even and a
    label never ends on one short hanging word."""
    lines = _greedy_lines(text, max_chars)
    if len(lines) < 2:
        return lines
    words = text.split()
    glued: list[str] = []          # a number stays with the word after it ("180 days", "30 days"), as the page's number rules read it
    for w in words:
        if glued and re.fullmatch(r"[$]?[\d.,]+[%×MKB]?", glued[-1]):
            glued[-1] += "\u2060" + w
        else:
            glued.append(w)
    kept = " ".join(glued)
    if len(_greedy_lines(kept, max_chars)) > len(lines):
        return lines
    lo, hi = 1, max_chars
    while lo < hi:
        mid = (lo + hi) // 2
        if len(_greedy_lines(kept, mid)) <= len(lines):
            hi = mid
        else:
            lo = mid + 1
    return [line.replace("\u2060", " ") for line in _greedy_lines(kept, lo)]


def tw(s: str, fs: float, bold: bool = False) -> float:
    """Rough text width in user units for system-ui (used only for layout decisions)."""
    return len(s) * fs * (0.60 if bold else 0.55)


# A label is (svg_or_html_markup, plain_text): the plain text is what layout measures.
Txt = tuple[str, str]


def T(*parts: object) -> Txt:
    """Join plain strings (escaped) and (markup, plain) pairs into one label."""
    mk: list[str] = []
    pl: list[str] = []
    for p in parts:
        if isinstance(p, tuple):
            mk.append(p[0])
            pl.append(p[1])
        else:
            mk.append(esc(p))
            pl.append(str(p))
    return "".join(mk), "".join(pl)


def mk(t: object) -> str:
    return t[0] if isinstance(t, tuple) else esc(t)


def pl(t: object) -> str:
    return t[1] if isinstance(t, tuple) else str(t)


# ------------------------------------------------------------------ data
def gh(path: str) -> str:
    """Absolute GitHub URL of a repo file (the site is served from site/, so relative links would not reach it)."""
    return f"{REPO_URL}/blob/{BRANCH}/{path}"


def says_it_is_a_score(d: object) -> bool:
    """True for a parsed result.json that claims to be a real score: is_score true and mode "score"."""
    return isinstance(d, dict) and d.get("is_score") is True and d.get("mode") == "score"


def is_real_score(d: object) -> bool:
    """True for a parsed result.json that the page may draw as a score: it says it is one, and it holds a results object."""
    return says_it_is_a_score(d) and isinstance(d.get("results"), dict)


FORWARD_IDS = ("F1", "F2", "F3", "F4")
# The numbers the forward-test card prints for a test the scorer calls PASS or MISS. The first of each is the observed value: the
# number line, the dot and the dot's label are drawn from it. pipeline/score_forward.py writes every one of them for a PASS or a MISS.
FORWARD_NUMBERS = {"F1": ("balance_near", "block_height"), "F2": ("mean_near_per_day", "n_deltas"),
                   "F3": ("take_rate_bp", "revenue_usd", "volume_usd"), "F4": ("intents_share_pct",)}
# What clears a stop over one test's numbers: the numbers of a test that is not scorable are not read. (Each such message ends with it.)
NOT_SCORABLE_FIX = ("set the result of that test to 'not scorable' and give a why (the numbers of a test that is not scorable are not read), "
                    "and say so in a dated addendum entry")


def json_kind(v: object) -> str:
    """A parsed JSON value as a message names it: null, true, a list, an object, the text 'abc', or the number itself."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return f"the text {v[:30]!r}" + (" (cut)" if len(v) > 30 else "")
    if isinstance(v, list):
        return "a list"
    if isinstance(v, dict):
        return "an object"
    return repr(v) if isinstance(v, float) or abs(v) < 10 ** 30 else "an integer too large to print"


def forward_number(fid: str, r: dict, key: str, where: str) -> float:
    """r[key], a number that a PASS or MISS test records, as a finite float. A number the card cannot print or draw (missing, null, a
    string, true, NaN, infinity, an integer beyond the range of a float) stops the render with a message that names the field and the
    file, and says what clears it. (A value that is finite but absurd is stopped by the axis, which would otherwise draw millions of ticks.)"""
    if key not in r:
        raise SystemExit(f"render: {fid}.{key} is missing from {where}, but {fid} is {r.get('result')} and the card prints it; "
                         f"put it back or {NOT_SCORABLE_FIX}")
    v = r[key]
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise SystemExit(f"render: {fid}.{key} in {where} is {json_kind(v)}, not a number, so the page cannot print it; "
                         f"correct it or {NOT_SCORABLE_FIX}")
    try:
        finite = math.isfinite(v)
    except OverflowError:       # an integer beyond the range of a float (JSON allows any number of digits)
        finite = False
    if not finite:
        shown = repr(v) if isinstance(v, float) else "an integer too large for a float"
        raise SystemExit(f"render: {fid}.{key} is {shown}, not a finite number (in {where}), so the page cannot draw it; {NOT_SCORABLE_FIX}")
    return float(v)


def check_forward_results(results: dict, where: str) -> None:
    """Stop the render, naming the field and the file, on a recorded test the card cannot be drawn from.

    Each of F1 to F4 that the file records must be an object (a string or null made the scorecard raise AttributeError). One that says PASS or
    MISS must hold every number the card prints, as a finite number (a missing key made the card raise KeyError, a number written as text
    raised TypeError). One that says anything else is drawn as "not scorable", and its `why`, if it has one, must be text. A test the file does
    not record at all is drawn as "not scorable" with "no reason recorded", as it always was: the real scorer writes all four."""
    for fid in FORWARD_IDS:
        if fid not in results:
            continue
        r = results[fid]
        if not isinstance(r, dict):
            raise SystemExit(f"render: {fid} in {where} is {json_kind(r)}, not an object; write it as the scorer does: "
                             '{"result": "not scorable", "why": "..."}, or "PASS" or "MISS" with its numbers')
        if "result" not in r:
            raise SystemExit(f"render: {fid} in {where} has no \"result\" key; write it as the scorer does: "
                             '{"result": "not scorable", "why": "..."}, or "PASS" or "MISS" with its numbers')
        if r.get("result") in ("PASS", "MISS"):
            for key in FORWARD_NUMBERS[fid]:
                forward_number(fid, r, key, where)
        elif "why" in r and not isinstance(r["why"], str):
            raise SystemExit(f"render: {fid}.why in {where} is {json_kind(r['why'])}, not text; write the reason as text")


def forward_word(fw: dict | None, fid: str) -> str:
    """What the page prints for one forward test: "pending" without a score, else PASS or MISS as recorded, else "not scorable".

    A test the file does not record, or records with any other word, is "not scorable": the card, the table, the counts and the scorecard
    all take the word from here."""
    if not fw:
        return "pending"
    r = fw["results"].get(fid)
    w = str(r.get("result", "not scorable")) if isinstance(r, dict) else "not scorable"
    return w if w in ("PASS", "MISS") else "not scorable"


REASON_LINE = 1000   # characters (as escaped in the page) of a not-scorable reason on one source line
SOURCE_BREAK = "<!--\n-->"   # a comment that holds only a newline: a browser draws nothing for it and does not split the text at it


def wrap_reason(text: str, width: int = REASON_LINE) -> str:
    """A reason for 'not scorable' as escaped markup whose source lines are no longer than about `width` characters, however long it is.

    The scorer's `why` is the text of an RPC error when F1 cannot be read, which can run to thousands of characters, and one line of the page
    over 2,000 fails the suite (tests/test_render.py, LineBreaks). Lines are broken at spaces: a newline in place of a space, which a browser
    collapses back into a space, so what is drawn is the same text. A run of white space becomes one, as it is drawn. A word that no line can
    hold (an escaped length over `width`; a quote mark escapes to six characters) cannot be broken at a space, so it is cut into pieces of at
    most `width` characters with SOURCE_BREAK between them: an HTML comment is not drawn and not part of the text, so the word is drawn as
    one word. In every case the text of the span is the reason, up to white space (tests/test_render_guards.py pins both)."""
    lines: list[str] = []
    cur = ""
    for word in (w for w in re.split(r"[ \t\r\n\f]+", text) if w):      # ASCII white space only: U+00A0 and U+2028 are drawn as they are
        e = esc(word)
        if len(e) > width:
            if cur:
                lines.append(cur)
                cur = ""
            pieces, piece, size = [], [], 0
            for ch in word:                 # pieces of the word whose escaped length is at most `width`, never cut inside an entity
                k = len(esc(ch))
                if piece and size + k > width:
                    pieces.append("".join(piece))
                    piece, size = [], 0
                piece.append(ch)
                size += k
            pieces.append("".join(piece))
            lines.append(SOURCE_BREAK.join(esc(x) for x in pieces))
        elif cur and len(cur) + 1 + len(e) > width:
            lines.append(cur)
            cur = e
        else:
            cur = f"{cur} {e}" if cur else e
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def load_forward(forward_dir: Path) -> dict | None:
    """The newest data/forward/score_<UTC stamp>/result.json, only if it is a real score (is_score true, mode "score").

    Dry-run output (dry-run_*/DRY_RUN_result_NOT_A_SCORE.json) is never opened: only files named result.json inside
    folders named score_YYYYMMDDTHHMMSSZ are considered (a folder such as score_rehearsal is ignored, so it cannot
    outrank a real stamp), and a parseable result whose mode is not "score" is ignored. A newest result.json that
    cannot be read as JSON (a byte-order mark, a truncated file) stops the render: showing "pending" while a score
    file exists would let a stale page pass every check. So does a result that says it is a score (is_score true, mode
    "score") in a score_* folder whose name is not exactly score_YYYYMMDDTHHMMSSZ, the name pipeline.score_forward
    gives it: it would be ignored, and the page would say "pending" over it. The other files of such folders (not a
    score, a dry run, not JSON) are ignored as before. In the newest stamped folder a file that says it is a score but holds
    no results object stops the render for the same reason, and a score whose tests the card cannot be drawn from stops it
    too (check_forward_results)."""
    if not forward_dir.is_dir():
        return None
    files = sorted(p for p in forward_dir.glob("score_*/result.json") if p.is_file())
    cands = [p for p in files if SCORE_FOLDER.fullmatch(p.parent.name)]
    misnamed = []
    for p in files:
        if SCORE_FOLDER.fullmatch(p.parent.name):
            continue
        try:
            found = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError, RecursionError):
            continue    # it cannot be read, so it cannot be told from a rehearsal: ignored, as a folder without a stamp always was
        if says_it_is_a_score(found):
            misnamed.append(f"data/forward/{p.parent.name}/result.json")
    if misnamed:
        many = len(misnamed) > 1
        raise SystemExit(f"render: {', '.join(misnamed)} {'are scored results' if many else 'is a scored result'} (mode \"score\", "
                         f"is_score true) in {'folders' if many else 'a folder'} not named score_YYYYMMDDTHHMMSSZ, the name "
                         f"pipeline.score_forward gives it, so the page would say 'pending' over {'them' if many else 'it'}. "
                         "Rename the folder to score_<UTC stamp>, or remove it if it is a rehearsal.")
    if not cands:
        return None
    path = cands[-1]
    where = f"data/forward/{path.parent.name}/result.json"
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError) as exc:
        raise SystemExit(f"render: {where} exists but cannot be read as JSON "
                         f"({type(exc).__name__}); the page would say 'pending'. Fix or remove it.")
    if not says_it_is_a_score(d):
        return None
    if not is_real_score(d):
        raise SystemExit(f"render: {where} is a scored result (mode \"score\", is_score true) that holds no results object, so the "
                         "page cannot be drawn from it and would say 'pending' over it. Complete it, or remove it if it is a rehearsal.")
    check_forward_results(d["results"], where)
    d["_path"] = where
    return d


def prereg_forward(text: str) -> dict[str, dict]:
    """The F1-F4 rows of PREREG.md's forward-test table: verbatim prediction text and prior probability."""
    out: dict[str, dict] = {}
    for line in text.splitlines():
        mt = re.match(r"^\|\s*(F[1-4])\s*\|\s*(.+?)\s*\|\s*([0-9.]+)\s*\|\s*$", line)
        if mt:
            out[mt.group(1)] = {"text": mt.group(2), "p": mt.group(3)}
    return out


class Ctx:
    """Everything the page is built from, read from a repo root (injectable for tests)."""

    def __init__(self, root: Path = ROOT, forward_dir: Path | None = None) -> None:
        self.root = Path(root)
        self.data = self.root / "data"
        self.forward_dir = Path(forward_dir) if forward_dir is not None else self.data / "forward"
        self.m: dict = json.loads((self.data / "metrics.json").read_text(encoding="utf-8"))
        self.s: dict = json.loads((self.data / "series.json").read_text(encoding="utf-8"))
        manifest_bytes = (self.data / "MANIFEST.json").read_bytes()
        self.fingerprint = hashlib.sha256(manifest_bytes).hexdigest()[:16]
        self.manifest: dict = json.loads(manifest_bytes)["files"]
        prereg_bytes = (self.root / "PREREG.md").read_bytes()
        self.prereg_sha = hashlib.sha256(prereg_bytes).hexdigest()
        self.prereg_forward = prereg_forward(prereg_bytes.decode("utf-8"))
        self.forward = load_forward(self.forward_dir)
        self._sidx: dict[str, dict[str, dict]] = {}
        for name, rows in self.s.items():
            key = "month" if rows and "month" in rows[0] else "date"
            self._sidx[name] = {r[key]: r for r in rows}

    # ---- files
    def read_text(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")

    def sha12(self, raw_rel: str) -> str | None:
        """First 12 hex of the SHA-256 recorded in data/MANIFEST.json for a path like raw/bq/x.json."""
        e = self.manifest.get(raw_rel)
        return e["sha256"][:12] if e else None

    # ---- numbers: each returns (markup, plain); M/S/D/K return the markup only (HTML context)
    def _num(self, attr: str, ref: str, value: object, dec: int | None, tag: str) -> Txt:
        if isinstance(value, bool):
            text = "pass" if value else "fail"
        elif isinstance(value, str):
            text = value
        else:
            text = fmt_value(value, dec)
        return f'<{tag} {attr}="{esc(ref)}">{esc(text)}</{tag}>', text

    def metric(self, path: str) -> object:
        """metrics.json[key], or a path into a list-valued metric such as buyback_fee_by_channel.0.share_pct."""
        cur: object = self.m
        for part in path.split("."):
            cur = cur[int(part)] if isinstance(cur, list) else cur[part]  # type: ignore[index]
        return cur

    def Mt(self, key: str, dec: int | None = None, tag: str = "tspan") -> Txt:
        return self._num("data-m", key, self.metric(key), dec, tag)

    def M(self, key: str, dec: int | None = None) -> str:
        return self.Mt(key, dec, "span")[0]

    def series_value(self, path: str) -> object:
        name, key, field = path.split(".")
        return self._sidx[name][key][field]

    def St(self, path: str, dec: int | None = None, tag: str = "tspan") -> Txt:
        return self._num("data-s", path, self.series_value(path), dec, tag)

    def S(self, path: str, dec: int | None = None) -> str:
        return self.St(path, dec, "span")[0]

    def Dt(self, expr: str, dec: int, tag: str = "tspan") -> Txt:
        v = eval_expr(expr, self.m)
        return f'<{tag} data-d="{esc(expr)}">{esc(fmt_value(round(v, dec), dec))}</{tag}>', fmt_value(round(v, dec), dec)

    def D(self, expr: str, dec: int) -> str:
        return self.Dt(expr, dec, "span")[0]

    def Kt(self, name: str, tag: str = "tspan") -> Txt:
        return f'<{tag} data-k="{esc(name)}">{esc(CONSTS[name][1])}</{tag}>', CONSTS[name][1]

    def K(self, name: str) -> str:
        return self.Kt(name, "span")[0]

    def plain(self, key: str, dec: int | None = None) -> str:
        """A metric as plain text (for alt text, where markup is not allowed)."""
        return self._num("data-m", key, self.metric(key), dec, "span")[1]


# ------------------------------------------------------------------ SVG primitives
# Every chart is drawn twice, once for wide screens (viewBox 720) and once for phones (viewBox 340), so text stays
# readable without any script: CSS shows one of the two. Colours are CSS classes (tokens), never inline values.
@dataclass(frozen=True)
class Variant:
    name: str
    w: int
    narrow: bool
    fs: float   # label font size in user units
    bt: int     # bar thickness


WIDE = Variant("wide", 720, False, 12.5, 16)
NARROW = Variant("narrow", 340, True, 11.5, 14)
VARIANTS = (WIDE, NARROW)


def text(x: float, y: float, content: str, *, cls: str = "", anchor: str = "start", fs: float | None = None) -> str:
    """<text> with markup content (already escaped by the caller)."""
    a = f' class="{cls}"' if cls else ""
    an = f' text-anchor="{anchor}"' if anchor != "start" else ""
    f = f' font-size="{n1(fs)}"' if fs else ""
    return f'<text x="{n1(x)}" y="{n1(y)}"{a}{an}{f}>{content}</text>'


def hline(x1: float, x2: float, y: float, cls: str, attrs: str = "") -> str:
    return f'<line class="{cls}"{attrs} x1="{n1(x1)}" x2="{n1(x2)}" y1="{n1(y)}" y2="{n1(y)}" />'


def vline(x: float, y1: float, y2: float, cls: str, attrs: str = "") -> str:
    return f'<line class="{cls}"{attrs} x1="{n1(x)}" x2="{n1(x)}" y1="{n1(y1)}" y2="{n1(y2)}" />'


def hbar_path(x: float, y: float, w: float, h: float, r: float = 4) -> str:
    """Horizontal bar: square at the baseline (left), rounded data end (right)."""
    r = min(r, w, h / 2)
    if w < 2 * r:
        return f"M{n1(x)},{n1(y)}h{n1(w)}v{n1(h)}h{n1(-w)}z"
    return (f"M{n1(x)},{n1(y)}h{n1(w - r)}a{n1(r)},{n1(r)} 0 0 1 {n1(r)},{n1(r)}v{n1(h - 2 * r)}"
            f"a{n1(r)},{n1(r)} 0 0 1 {n1(-r)},{n1(r)}h{n1(-(w - r))}z")


def vbar_path(x: float, y: float, w: float, h: float, r: float = 4) -> str:
    """Column: square at the baseline (bottom), rounded data end (top). y is the top edge."""
    r = min(r, w / 2, h)
    if h < 2 * r or w < 2 * r:
        return f"M{n1(x)},{n1(y + h)}V{n1(y)}h{n1(w)}V{n1(y + h)}z"
    return (f"M{n1(x)},{n1(y + h)}V{n1(y + r)}a{n1(r)},{n1(r)} 0 0 1 {n1(r)},{n1(-r)}h{n1(w - 2 * r)}"
            f"a{n1(r)},{n1(r)} 0 0 1 {n1(r)},{n1(r)}V{n1(y + h)}z")


def tip(s: str) -> str:
    return f"<title>{esc(s)}</title>" if s else ""


def title_block(v: Variant, title: object, tag: str = "") -> tuple[str, float]:
    """A panel title, wrapped to the panel width. Returns (markup, height used).

    tag is the panel's letter in a figure of two or more panels ("A", "B"): it is printed first, as "A. ", so that a
    caption or a description that says "Panel A" names something the reader can see."""
    fs = v.fs + 1
    lines = wrap_words((f"{tag}. " if tag else "") + pl(title), int(v.w / (fs * 0.6)))
    out = "".join(text(0, fs + j * (fs + 3), esc(line), cls="ttl", fs=fs) for j, line in enumerate(lines))
    return out, len(lines) * (fs + 3)


def clamp_anchor(x: float, width: float, total: float) -> tuple[float, str]:
    """Where to anchor a centred label so that it stays inside 0..total."""
    if x - width / 2 < 0:
        return 0.0, "start"
    if x + width / 2 > total:
        return total, "end"
    return x, "middle"


def svg_wrap(v: Variant, uid: str, height: float, title: str, desc: str, body: str) -> str:
    return (f'<svg class="svg" viewBox="0 0 {v.w} {n1(height)}" role="img" aria-labelledby="{uid}-t {uid}-d" '
            f'focusable="false"><title id="{uid}-t">{esc(title)}</title><desc id="{uid}-d">{esc(desc)}</desc>'
            f"{body}</svg>")


def stack(panels: list[tuple[str, float]], gap: float = 30) -> tuple[str, float]:
    """Stack panels vertically; each is (markup, height) drawn at the origin."""
    out: list[str] = []
    y = 0.0
    for i, (body, h) in enumerate(panels):
        out.append(f'<g transform="translate(0,{n1(y)})">{body}</g>')
        y += h + (gap if i < len(panels) - 1 else 0)
    return "".join(out), y


def legend(v: Variant, items: list[tuple[str, object, str]], y: float) -> tuple[str, float]:
    """items: (css class, name (str or Txt), 'rect' | 'line'). Laid out in rows that wrap; returns (markup, height)."""
    fs = v.fs
    out: list[str] = []
    x = 0.0
    yy = y
    for cls, name, kind in items:
        wi = (22 if kind == "line" else 16) + tw(pl(name), fs) + 18
        if x > 0 and x + wi > v.w:
            x = 0.0
            yy += fs + 8
        if kind == "line":
            out.append(f'<line class="lg {cls}" x1="{n1(x)}" x2="{n1(x + 16)}" y1="{n1(yy - 4)}" y2="{n1(yy - 4)}" />')
            out.append(text(x + 22, yy, mk(name), fs=fs))
        else:
            out.append(f'<rect class="{cls}" x="{n1(x)}" y="{n1(yy - 9)}" width="10" height="10" rx="2" />')
            out.append(text(x + 16, yy, mk(name), fs=fs))
        x += wi
    return "".join(out), yy - y + 6


def hbar_panel(v: Variant, *, title: object, rows: list[dict], vmax: float, ticks: list[float],
               tick_fmt=lambda t: f"{t:g}", refs: list[dict] | None = None,
               legend_items: list[tuple[str, object, str]] | None = None, tag: str = "") -> tuple[str, float]:
    """Horizontal bars from zero on one linear axis.

    rows: {"label": str, "bars": [{"v": float, "cls": "s1", "txt": Txt, "tip": str,
           "lv": float (the value the label prints, when it is not the value drawn),
           "track": bool (full-scale track behind the bar), "segs": [{"v", "cls", "tip"}] (a stacked bar of total v)}]}
    refs: {"v": float, "label": Txt}, a vertical reference line (a pass line or a required threshold).
    tag: the panel's letter when it is one of several in a figure (see title_block).

    The panel is one <g class="panel"> stating its axis and plot box, each row is a <g class="row" data-row>, and
    every bar and segment carries data-v, which is what tests/test_render.py checks the drawn length against."""
    refs = refs or []
    fs = v.fs
    lab_w = 0 if v.narrow else 212
    x0 = 3 if v.narrow else lab_w + 8
    x1 = v.w - (64 if v.narrow else 80)
    pw = x1 - x0

    def sx(val: float) -> float:
        return pw * val / vmax

    tb, th = title_block(v, title, tag)
    out: list[str] = [tb]
    lg_h = 0.0
    if legend_items:
        lg, lg_h = legend(v, legend_items, th + fs + 4)
        out.append(lg)
        lg_h += 12   # clear space between the legend and the first row's label
    ytop = th + 6 + lg_h + 15 * len(refs)
    ry = ytop + (9 if v.narrow else 4)
    geoms = []
    for r in rows:
        nb = len(r["bars"])
        chars = int((v.w if v.narrow else lab_w) / (fs * 0.56))
        lab = wrap_words(r["label"], chars)
        lab_h = len(lab) * (fs + 3)
        bars_h = nb * v.bt + (nb - 1) * 3
        if v.narrow:
            rh = lab_h + bars_h + 12
            by, ly = ry + lab_h + 3, ry + fs
        else:
            rh = max(lab_h + 8, bars_h + 10)
            by, ly = ry + (rh - bars_h) / 2, ry + (rh - lab_h) / 2 + fs
        geoms.append((r, lab, ly, by))
        ry += rh
    ybot = ry
    for t in ticks:
        tx, tan = clamp_anchor(x0 + sx(t), tw(tick_fmt(t), fs), v.w)
        out.append(vline(x0 + sx(t), ytop, ybot, "axis" if t == 0 else "grid"))
        out.append(text(tx, ybot + fs + 3, esc(tick_fmt(t)), cls="tk", anchor=tan, fs=fs))
    ref_x = [x0 + sx(rf["v"]) for rf in refs]
    block_spans = []
    for r, lab, ly, by in geoms:
        block_spans.append((by - 3, by + len(r["bars"]) * v.bt + (len(r["bars"]) - 1) * 3 + 3))
        row: list[str] = []
        for j, line in enumerate(lab):
            row.append(text(0, ly + j * (fs + 3), esc(line), cls="rl", fs=fs))
        for k, b in enumerate(r["bars"]):
            by_k = by + k * (v.bt + 3)
            w = sx(b["v"])
            if b.get("track"):
                row.append(f'<rect class="track" x="{n1(x0)}" y="{n1(by_k)}" width="{n1(pw)}" height="{v.bt}" rx="4" />')
            if b.get("segs"):
                xs = x0
                for si, sg in enumerate(b["segs"]):
                    sw = sx(sg["v"])
                    last = si == len(b["segs"]) - 1
                    wseg = max(sw if last else sw - SEG_GAP, MIN_SEG)
                    d = (hbar_path(xs, by_k, wseg, v.bt) if last
                         else f"M{n1(xs)},{n1(by_k)}h{n1(wseg)}v{n1(v.bt)}h{n1(-wseg)}z")
                    row.append(f'<path class="{sg["cls"]}" data-v="{dv(sg["v"])}" d="{d}">{tip(sg.get("tip", ""))}</path>')
                    xs += sw
            elif b["v"] > 0:
                lv = f' data-lv="{dv(b["lv"])}"' if "lv" in b else ""
                row.append(f'<path class="{b["cls"]}" data-v="{dv(b["v"])}"{lv} d="{hbar_path(x0, by_k, max(w, MIN_BAR), v.bt)}">'
                           f'{tip(b.get("tip", ""))}</path>')
            lx = x0 + max(w, MIN_BAR) + 6
            wl = tw(pl(b["txt"]), fs, True)
            for rx in ref_x:  # keep a value label off a reference line
                if lx - 3 <= rx <= lx + wl + 3:
                    lx = rx + 6
            row.append(text(lx, by_k + v.bt / 2 + fs * 0.35, mk(b["txt"]), cls="val", fs=fs))
        out.append(f'<g class="row" data-row="{esc(r["label"])}">{"".join(row)}</g>')
    for i, rf in enumerate(refs):
        rx = ref_x[i]
        ly = th + 6 + lg_h + 15 * (i + 1)
        dva = f' data-v="{dv(rf["v"])}"'
        if v.narrow:  # labels sit above the bars here, so draw the line only across the bar blocks
            out.extend(vline(rx, a_, b_, "refline", dva) for a_, b_ in block_spans)
        else:
            out.append(vline(rx, ly + 3, ybot, "refline", dva))
        wl = tw(pl(rf["label"]), fs)
        if rx + 6 + wl <= v.w:
            out.append(text(rx + 6, ly, mk(rf["label"]), cls="rl", fs=fs))
        elif rx - 6 - wl >= 0:
            out.append(text(rx - 6, ly, mk(rf["label"]), cls="rl", anchor="end", fs=fs))
        else:
            out.append(text(0, ly, mk(rf["label"]), cls="rl", fs=fs))
    panel = (f'<g class="panel" data-kind="hbar" data-lo="0" data-hi="{dv(vmax)}" data-x0="{n1(x0)}" data-pw="{n1(pw)}">'
             f'{"".join(out)}</g>')
    return panel, ybot + fs + 10


def vcol_panel(v: Variant, *, title: object, cats: list[dict], series: list[dict], ymax: float, yticks: list[float],
               h_plot: float, tick_fmt=lambda t: f"{t:g}", label_step: int = 1, refs: list[dict] | None = None,
               brackets: list[dict] | None = None, val_labels: bool = True,
               footnote: str | None = None, tag: str = "", ml_min: float = 0, mr_min: float = 0) -> tuple[str, float]:
    """Columns from zero. cats: {"label": str, "vals": [..], "txts": [Txt|None], "tips": [str], "cls": [str]}.

    series: {"cls": "s1", "name": str}; a legend is drawn when there is more than one series.
    refs: {"v": float, "label": Txt}, a horizontal reference line; its label is a legend row above the plot,
    never inside it, so it cannot cover a column. footnote: plain text under the brackets.
    tag: the panel's letter when it is one of several in a figure (see title_block).

    The panel is one <g class="panel"> stating its axis and plot box; each category is a <g class="col" data-cat>
    and every column carries data-v, which tests/test_render.py checks the drawn height against."""
    refs = refs or []
    brackets = brackets or []
    fs = v.fs
    ml = max(max(tw(tick_fmt(t), fs) for t in yticks) + 12, ml_min)   # ml_min, mr_min: the other panel's margins, so two stacked plots share their edges
    mr = max(8, mr_min)
    pw = v.w - ml - mr
    tb, th = title_block(v, title, tag)
    out: list[str] = [tb]
    y = th + 4
    if len(series) > 1:
        lg, lh = legend(v, [(s["cls"], s["name"], "rect") for s in series], y + fs)
        out.append(lg)
        y += lh + fs
    if refs:
        lg, lh = legend(v, [("refline", rf["label"], "line") for rf in refs], y + fs)
        out.append(lg)
        y += lh + fs
    top = y + fs + 6          # room for value labels above the tallest column
    base = top + h_plot

    def sy(val: float) -> float:
        return h_plot * val / ymax

    for t in yticks:
        out.append(hline(ml, ml + pw, base - sy(t), "axis" if t == 0 else "grid"))
        out.append(text(ml - 6, base - sy(t) + fs * 0.35, esc(tick_fmt(t)), cls="tk", anchor="end", fs=fs))
    n = len(cats)
    gw = pw / n
    ns = len(series)
    bw = min(24.0, (gw * 0.78 - 2 * (ns - 1)) / ns)
    bw = max(bw, 1.2)
    for i, c in enumerate(cats):
        cx = ml + gw * (i + 0.5)
        x_start = cx - (ns * bw + (ns - 1) * 2) / 2
        col: list[str] = []
        for j, val in enumerate(c["vals"]):
            if val is None:
                continue
            bx = x_start + j * (bw + 2)
            h = sy(val)
            cls = (c.get("cls") or [series[j]["cls"]] * ns)[j]
            if val > 0:
                col.append(f'<path class="{cls}" data-v="{dv(val)}" d="{vbar_path(bx, base - h, bw, max(h, MIN_COL))}">'
                           f'{tip((c.get("tips") or [""] * ns)[j])}</path>')
            txt = (c.get("txts") or [None] * ns)[j]
            if val_labels and txt:
                lx, an = clamp_anchor(bx + bw / 2, tw(pl(txt), fs - 0.5, True), v.w)
                col.append(text(lx, base - max(h, MIN_COL) - 4, mk(txt), cls="val", anchor=an, fs=fs - 0.5))
        if (n - 1 - i) % label_step == 0:
            for k, line in enumerate(c["label"].split("\n")):
                lx, an = clamp_anchor(cx, tw(line, fs), v.w)
                col.append(text(lx, base + fs + 4 + k * (fs + 2), esc(line), cls="tk", anchor=an, fs=fs))
        out.append(f'<g class="col" data-cat="{esc(c["label"].replace(chr(10), " "))}">{"".join(col)}</g>')
    lab_rows = max(len(c["label"].split("\n")) for c in cats)
    ybot = base + (fs + 4) + (lab_rows - 1) * (fs + 2)
    for rf in refs:
        out.append(hline(ml, ml + pw, base - sy(rf["v"]), "refline", f' data-v="{dv(rf["v"])}"'))
    yb = ybot + 12            # all brackets share one baseline; their labels hang below it
    most_lines = 0
    for bk in brackets:
        xa = ml + gw * bk["i0"] + 3
        xb = ml + gw * (bk["i1"] + 1) - 3
        out.append(f'<path class="bracket" d="M{n1(xa)},{n1(yb - 5)}V{n1(yb)}H{n1(xb)}V{n1(yb - 5)}" />')
        lab_lines = wrap_words(bk["label"], max(8, int((xb - xa) / (fs * 0.5))))
        for k, line in enumerate(lab_lines):
            out.append(text((xa + xb) / 2, yb + fs + 2 + k * (fs + 2), esc(line), cls="tk", anchor="middle", fs=fs - 0.5))
        most_lines = max(most_lines, len(lab_lines))
    if brackets:
        ybot = max(ybot, yb + (fs + 2) * (most_lines + 1))
    if footnote:
        fl = wrap_words(footnote, max(10, int(v.w / ((fs - 0.5) * 0.5))))
        yb = ybot + 6
        for k, line in enumerate(fl):
            out.append(text(0, yb + fs + k * (fs + 2), esc(line), cls="tk", fs=fs - 0.5))
        ybot = yb + (fs + 2) * len(fl)
    panel = (f'<g class="panel" data-kind="vcol" data-lo="0" data-hi="{dv(ymax)}" data-base="{n1(base)}" data-ph="{n1(h_plot)}" '
             f'data-x0="{n1(ml)}" data-pw="{n1(pw)}">{"".join(out)}</g>')
    return panel, ybot + 8


def line_panel(v: Variant, *, title: object, xlabels: list[str], xtick_idx: list[int], series: list[dict],
               ymin: float, ymax: float, yticks: list[float], h_plot: float, tick_fmt=lambda t: f"{t:g}",
               refs: list[dict] | None = None, area_first: bool = False, ynote: str | None = None,
               annots: list[dict] | None = None, vmarks: list[dict] | None = None, tag: str = "",
               ml_min: float = 0, mr_min: float = 0) -> tuple[str, float]:
    """Lines on one axis. series: {"cls": "l1", "dot": "s1", "ys": [..], "end": Txt, "name": str}.
    annots: {"i": point index, "y": value, "txt": Txt}, a labelled dot (a peak or another point worth naming).
    vmarks: {"i": point index, "date": str, "label": Txt}, a labelled vertical line from the top of the plot to the axis
    (an event on the horizontal axis); the label sits beside it, inside the plot.
    tag: the panel's letter when it is one of several in a figure (see title_block).

    A legend is drawn when there are two or more series; the last point of each series is labelled directly.

    The panel is one <g class="panel"> stating its axis and plot box; the dot at the end of each series, and each
    annotated dot, carries data-v, which tests/test_render.py checks the drawn height against, and each vertical line
    carries data-i and data-date, which it checks the drawn position against."""
    refs = refs or []
    fs = v.fs
    ml = max(max(tw(tick_fmt(t), fs) for t in yticks) + 12, ml_min)
    mr = max(58 if v.narrow else 76, max([tw(pl(s["end"]), fs, True) for s in series if s.get("end")] or [0]) + 14, mr_min)
    pw = v.w - ml - mr
    tb, th = title_block(v, title, tag)
    out: list[str] = [tb]
    y = th + 4
    if ynote:
        out.append(text(0, y + fs, esc(ynote), cls="tk", fs=fs - 0.5))
        y += fs + 4
    if len(series) > 1:
        lg, lh = legend(v, [(s["cls"], s["name"], "line") for s in series], y + fs)
        out.append(lg)
        y += lh + fs
    top = y + 10
    base = top + h_plot
    span = ymax - ymin

    def sy(val: float) -> float:
        return base - h_plot * (val - ymin) / span

    n = len(xlabels)

    def sx(i: int) -> float:
        return ml + (pw * i / (n - 1) if n > 1 else 0)

    for t in yticks:
        out.append(hline(ml, ml + pw, sy(t), "axis" if t == (0 if ymin <= 0 else ymin) else "grid"))
        out.append(text(ml - 6, sy(t) + fs * 0.35, esc(tick_fmt(t)), cls="tk", anchor="end", fs=fs))
    for i in xtick_idx:
        lx, an = clamp_anchor(sx(i), tw(xlabels[i], fs), v.w)
        out.append(text(lx, base + fs + 7, esc(xlabels[i]), cls="tk", anchor=an, fs=fs))
    for rf in refs:
        yy = sy(rf["v"])
        out.append(hline(ml, ml + pw, yy, "refline", f' data-v="{dv(rf["v"])}"'))
        out.append(text(ml + 4, yy - 5, mk(rf["label"]), cls="rl", fs=fs))
    for vm in vmarks or []:  # drawn before the lines, so a line is never hidden by its marker
        mx = sx(vm["i"])
        out.append(f'<line class="vmark" data-i="{vm["i"]}" data-date="{esc(vm["date"])}" x1="{n1(mx)}" x2="{n1(mx)}" '
                   f'y1="{n1(top)}" y2="{n1(base)}" />')
    ends: list[tuple[float, dict]] = []
    for si, s in enumerate(series):
        pts = [(sx(i), sy(val)) for i, val in enumerate(s["ys"]) if val is not None]
        if area_first and si == 0 and len(pts) > 1:
            d = "M" + "L".join(f"{n1(px)},{n1(py)}" for px, py in pts) + f"L{n1(pts[-1][0])},{n1(base)}L{n1(pts[0][0])},{n1(base)}z"
            out.append(f'<path class="wash {s["dot"]}" d="{d}" />')
        out.append(f'<path class="ln {s["cls"]}" d="M{"L".join(f"{n1(px)},{n1(py)}" for px, py in pts)}" />')
        if pts:
            last_v = [val for val in s["ys"] if val is not None][-1]
            out.append(f'<circle class="{s["dot"]} ring" data-v="{dv(last_v)}" cx="{n1(pts[-1][0])}" cy="{n1(pts[-1][1])}" r="4" />')
            if s.get("end"):
                ends.append((pts[-1][1], s))
    for an in annots or []:
        ax, ay = sx(an["i"]), sy(an["y"])
        out.append(f'<circle class="{series[0]["dot"]} ring" data-v="{dv(an["y"])}" cx="{n1(ax)}" cy="{n1(ay)}" r="4" />')
        aw = tw(pl(an["txt"]), fs, True)
        axa = min(max(ax, ml + aw / 2), ml + pw - aw / 2)
        out.append(text(axa, ay - 9, mk(an["txt"]), cls="val", anchor="middle", fs=fs))
    for vm in vmarks or []:  # the label goes on the side of the line that has room for it
        mx = sx(vm["i"])
        if mx + 6 + tw(pl(vm["label"]), fs) <= ml + pw:
            out.append(text(mx + 6, top + fs, mk(vm["label"]), cls="rl", fs=fs))
        else:
            out.append(text(mx - 6, top + fs, mk(vm["label"]), cls="rl", anchor="end", fs=fs))
    ends.sort(key=lambda e: e[0])
    placed = -1e9
    for ey, s in ends:  # direct end labels, nudged apart by at least one text line
        ly = max(ey + fs * 0.35, placed + fs + 2)
        placed = ly
        out.append(text(sx(n - 1) + 9, ly, mk(s["end"]), cls="val", fs=fs))
    panel = (f'<g class="panel" data-kind="line" data-lo="{dv(ymin)}" data-hi="{dv(ymax)}" data-base="{n1(base)}" data-ph="{n1(h_plot)}" '
             f'data-x0="{n1(ml)}" data-pw="{n1(pw)}">{"".join(out)}</g>')
    return panel, base + fs + 16


def dual(ctx: "Ctx", uid: str, title: str, desc: str, build) -> str:
    """Both variants of one chart. build(variant) -> (svg body markup, height)."""
    parts = []
    for v in VARIANTS:
        body, h = build(v)
        parts.append(f'<div class="cv cv-{v.name}">{svg_wrap(v, f"{uid}-{v.name[0]}", h, title, desc, body)}</div>')
    return f'<div class="chart">{"".join(parts)}</div>'


# ------------------------------------------------------------------ style
DARK_TOKENS = (
    "color-scheme:dark;--bg:#0f0f0d;--surface:#171714;--raise:#1e1e1a;--ink:#f1efe7;--ink2:#c6c3b6;--muted:#a19e91;"
    "--grid:#2b2a25;--axis:#4c4a43;--border:rgba(241,239,231,.13);--code:#22211d;--s1:#3987e5;--s2:#d95926;"
    "--ctx:#898781;--link:#8ab8ee;--focus:#6da7ec;--shade:rgba(255,255,255,.22);"
)

CSS = """
:root{color-scheme:light;--bg:#f5f3ec;--surface:#fcfbf7;--raise:#ffffff;--ink:#16150f;--ink2:#4b4940;--muted:#67655b;--grid:#e2dfd4;
--axis:#b4b1a4;--border:rgba(22,21,15,.14);--code:#edeae0;--s1:#2a78d6;--s2:#e8632f;--ctx:#898781;
--link:#1c5cab;--focus:#2a78d6;--shade:rgba(22,21,15,.2);
--sans:Arial,"Helvetica Neue",Helvetica,sans-serif;
--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){/*DARK*/}}
:root[data-theme="dark"]{/*DARK*/}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-padding-top:62px}
@media (prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 var(--sans);overflow-wrap:break-word;-webkit-font-smoothing:antialiased}
a{color:var(--link);text-underline-offset:3px;text-decoration-thickness:1px}
a:hover{text-decoration-thickness:2px}
a:focus-visible,summary:focus-visible,.tablewrap:focus-visible,pre:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.skip{position:absolute;left:-9999px;top:8px;background:var(--ink);color:var(--surface);padding:8px 14px;border-radius:6px;z-index:20}
.skip:focus{left:8px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
code,pre{font-family:var(--mono);font-size:.85em}
code{overflow-wrap:anywhere}
p,li{max-width:72ch}
@media (min-width:1100px){p,li{max-width:88ch}}
:where(#main) p,:where(#main) li{max-width:none}
h1,h2,h3,.big,.gridhead{text-wrap:balance}
p,li,dd,.tnote,.note,.finding{text-wrap:pretty}
[data-m],[data-k],[data-f],[data-d],[data-s]{white-space:nowrap}

/* frame */
.wrap{max-width:900px;margin:0 auto;padding:0 20px}
@media (min-width:1100px){.wrap{max-width:1480px;padding:0 32px}}
@media (min-width:1680px){
.wrap{max-width:1720px;display:grid;grid-template-columns:196px minmax(0,1fr);grid-template-areas:"side main" "side foot";column-gap:44px}
main{grid-area:main}footer{grid-area:foot}
}

/* first screen: the question, a one-line answer, four figures as ledger rows, the live row. No boxes. */
header.top{position:relative;overflow:hidden;display:flex;flex-direction:column;justify-content:center;min-height:100vh;min-height:100svh;
padding:56px max(20px,calc((100% - 860px) / 2)) 44px;border-bottom:1px solid var(--grid)}
@media (min-width:1100px){header.top{padding-left:max(32px,calc((100% - 1416px) / 2));padding-right:max(32px,calc((100% - 1416px) / 2))}}
@media (min-width:1680px){header.top{padding-left:max(32px,calc((100% - 1656px) / 2));padding-right:max(32px,calc((100% - 1656px) / 2))}}
header.top>*{position:relative;z-index:1}
/* NEAR's mark behind the cover, at the right, running off the edge of the window */
header.top::after{content:"";position:absolute;z-index:0;top:45%;right:-8%;width:clamp(300px,46%,680px);aspect-ratio:1;
transform:translateY(-50%);background:var(--ink);opacity:.07;pointer-events:none;
-webkit-mask:var(--mark) center / contain no-repeat;mask:var(--mark) center / contain no-repeat}
header.top{--mark:url("/*MARK*/")}
.eyebrow{margin:0 0 22px;font-size:.875rem;color:var(--muted)}
h1{font-size:clamp(2.4rem,6.6vw,4.75rem);font-weight:700;line-height:1.03;letter-spacing:-.03em;margin:0 0 .42em;max-width:17ch}
.sub{margin:0 0 1.5rem;max-width:50ch;font-size:clamp(1.125rem,2.1vw,1.5rem);line-height:1.35;color:var(--ink2)}
.byline{margin:0 0 3.2rem;max-width:none;font-size:1rem;font-weight:700;color:var(--ink)}
header.top>.byline{margin-bottom:0}
header.top>.scrollcue{position:absolute;left:50%;bottom:26px;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center;gap:9px;margin:0;max-width:none;font-size:.6875rem;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
header.top>.scrollcue::after{content:"";width:1px;height:30px;background:var(--axis)}
@media print{header.top>.scrollcue{display:none}}
.gauge-head{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 18px;margin:0 0 14px;max-width:none}
.gauge-num{font-size:clamp(2rem,4.8vw,3.25rem);font-weight:700;line-height:1;letter-spacing:-.03em;font-variant-numeric:lining-nums tabular-nums;color:var(--ink)}
.gauge-lab{flex:1 1 47rem;min-width:0;font-size:1.0625rem;line-height:1.4;color:var(--ink2)}
.gauge-track{height:34px;background:var(--grid)}
.gauge-fill{display:flex;height:100%;background:var(--s2)}
.gauge-core{height:100%;background:var(--s1)}
.gauge-foot{display:flex;flex-wrap:wrap;justify-content:space-between;gap:4px 24px;margin:10px 0 0;max-width:none;font-size:.8125rem;line-height:1.45;color:var(--muted)}
.gauge-key{display:inline-block;width:10px;height:10px;margin-right:7px;background:var(--s1)}
#brief{padding:2.6rem 0 0}
#brief>h2{margin:0 0 .7rem}
.thesis{margin:0 0 1.8rem;max-width:76ch}
.thesis p{margin:0 0 .9rem;max-width:none;text-wrap:balance;font-size:1.1875rem;line-height:1.5;color:var(--ink)}
.thesis .go{margin:0;font-size:1rem;color:var(--ink2)}
.kcap{margin:0;padding:0 0 9px;max-width:none;font-size:.8125rem;line-height:1.4;color:var(--muted)}
.kpis{list-style:none;padding:0;margin:0;border-top:1px solid var(--ink)}
.kpi{display:grid;grid-template-columns:minmax(0,1fr) auto;column-gap:28px;align-items:baseline;max-width:none;padding:13px 0 12px;border-bottom:1px solid var(--grid)}
.kpi .kl{grid-column:1;grid-row:1;font-size:.9375rem;line-height:1.35;color:var(--ink)}
.kpi .kw,.kw{grid-column:1;grid-row:2;font-size:.8125rem;line-height:1.4;color:var(--muted)}
.kpi .kv{grid-column:2;grid-row:1 / span 2;align-self:center;text-align:right;font-size:clamp(1.6rem,3.4vw,2.125rem);font-weight:600;line-height:1.1;letter-spacing:-.025em;font-variant-numeric:lining-nums tabular-nums;color:var(--ink);text-decoration:none}
.kpi a.kv:hover{text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:5px}
.today{margin:1.9rem 0 0}
.todaycap{margin:0;padding:0 0 9px;font-size:.8125rem;line-height:1.4;color:var(--muted)}
.todayrow{list-style:none;padding:0;margin:0;border-top:1px solid var(--axis)}
.todayrow li{display:grid;grid-template-columns:minmax(0,1fr) auto;column-gap:28px;align-items:baseline;max-width:none;padding:8px 0 7px;border-bottom:1px solid var(--grid)}
.tl{grid-column:1;grid-row:1;font-size:.875rem;line-height:1.35;color:var(--ink)}
.tw{grid-column:1;grid-row:2;font-size:.75rem;line-height:1.4;color:var(--muted)}
.todayrow output{grid-column:2;grid-row:1 / span 2;align-self:center;text-align:right;font-size:1.0625rem;font-weight:600;line-height:1.2;font-variant-numeric:lining-nums tabular-nums}
details.readmore{margin:.2rem 0 .6rem;border:0;padding:0}
details.metawrap,details.fz{border:0;padding:0;margin:.6rem 0}
details.metawrap>summary,details.fz>summary,details.readmore>summary,section>details.more>summary{font-size:.875rem;font-weight:500;color:var(--ink2)}
section>details.lead>summary{font-size:.9375rem;font-weight:400;line-height:1.6;color:var(--ink2)}
section>details.lead[open]>summary{color:var(--ink)}
.questions{font-size:1rem;margin:.6rem 0 .7rem}
.answer{margin:.2rem 0 .4rem;padding:0 0 0 16px;border-left:1px solid var(--axis)}
.answer p{margin:.7rem 0;max-width:none;font-size:.9375rem}
@media (min-width:1100px){
#brief{display:grid;grid-template-columns:minmax(0,1.08fr) minmax(0,.92fr);column-gap:72px;align-items:start;
grid-template-areas:"h kcap" "th kpis" "th today"}
#brief>h2{grid-area:h}.thesis{grid-area:th;margin-bottom:0}.kpis{grid-area:kpis}.kcap{grid-area:kcap;align-self:end}
.today{grid-area:today}
}

/* contents rail */
.side{margin:1.4rem 0 0}
.side .toc,.side .toc-more{display:flex;flex-wrap:wrap;gap:4px 18px;list-style:none;padding:0;margin:.4rem 0}
.side .sidecap{margin:.9rem 0 .2rem;font-size:.8125rem;font-weight:600;color:var(--ink)}
.side .sidecap:first-of-type{margin-top:0}
@media (max-width:1679px){.side{display:none}}
@media (min-width:1680px){
.side{grid-area:side;position:sticky;top:0;align-self:start;max-height:100vh;overflow:auto;margin:0;padding:30px 0 24px;font-size:.8125rem;scrollbar-width:thin}
.side .toc,.side .toc-more{display:block;margin:.2rem 0 .3rem}
.side li{margin:0;max-width:none}
.side a{display:block;padding:4px 10px;margin-left:-10px;border-radius:6px;color:var(--ink2);text-decoration:none;line-height:1.35}
.side a:hover{background:var(--code);color:var(--ink)}
.side .sidecap{margin:1.3rem 0 .35rem}
}

/* sections, tabs */
main{padding-top:0}
h2{font-size:1.5rem;font-weight:700;line-height:1.2;letter-spacing:-.015em;margin:2.6rem 0 .5rem}
h3{font-size:1.0625rem;font-weight:650;line-height:1.35;margin:.5rem 0 .6rem}
.lede{font-size:1.0625rem;margin:0 0 1rem}
.note{color:var(--ink2);font-size:.9375rem}
.note,.lede{max-width:none}
.fine{margin:2.2rem 0 0;max-width:none;font-size:.8125rem;line-height:1.55;color:var(--muted)}
.fine a{color:var(--ink2)}
.tabbar{position:sticky;top:0;z-index:3;display:flex;flex-wrap:wrap;gap:0 26px;margin:1.6rem 0 .6rem;padding:0;background:var(--bg);border-bottom:1px solid var(--axis)}
.tabbar a{padding:13px 0 11px;border-bottom:2px solid transparent;margin-bottom:-1px;color:var(--muted);font-size:.9375rem;font-weight:600;text-decoration:none}
.tabbar a:hover{color:var(--ink)}
@media (max-width:759px){.tabbar{flex-wrap:nowrap;overflow-x:auto;gap:0 22px;scrollbar-width:none}.tabbar a{white-space:nowrap}}
.panel>h2:first-child,.panel>section:first-child>h2{margin-top:1.2rem}
@supports selector(:has(*)){
.tabs>.panel{display:none}
.tabs>.panel:target,.tabs>.panel:has(:target),.tabs:not(:has(.panel:target,.panel :target))>#forward-view{display:block}
.tabs:not(:has(.panel:target,.panel :target)) .tabbar a[data-tab="forward-view"],.tabs:has(#forward-view:target,#forward-view :target) .tabbar a[data-tab="forward-view"],
.tabs:has(#preregistered:target,#preregistered :target) .tabbar a[data-tab="preregistered"],.tabs:has(#exploratory:target,#exploratory :target) .tabbar a[data-tab="exploratory"],
.tabs:has(#method:target,#method :target) .tabbar a[data-tab="method"]{color:var(--ink);border-bottom-color:var(--ink)}
}
@media print{.tabs>.panel{display:block!important}.tabbar{display:none}}

/* the frozen predictions */
#scorecard>h2{margin-top:1.2rem}
.tiles{display:grid;gap:0;list-style:none;padding:0;margin:1rem 0 2rem;border-top:2px solid var(--ink)}
.tile{display:grid;grid-template-columns:minmax(0,1fr);gap:4px 28px;align-items:baseline;max-width:none;padding:14px 0 15px;border-bottom:1px solid var(--grid)}
.tile p{margin:0;max-width:none}
.tlabel{font-size:.875rem;font-weight:600;color:var(--ink2)}
.big{font-size:1.375rem;font-weight:650;line-height:1.2;letter-spacing:-.015em;font-variant-numeric:lining-nums tabular-nums}
.tnote{font-size:.875rem;color:var(--ink2)}
.tile a{font-size:.8125rem;white-space:nowrap}
@media (min-width:860px){.tile{grid-template-columns:minmax(0,15rem) minmax(0,13rem) minmax(0,1fr) auto}}
#what-changed{margin:0 0 2rem}
#what-changed h3{font-size:1.125rem;font-weight:700;margin:1.6rem 0 .2rem}
.took{display:grid;gap:0 36px;list-style:none;padding:0;margin:.6rem 0 0;border-top:1px solid var(--grid)}
.took li{max-width:none;text-wrap:balance;margin:0;padding:11px 0 12px;border-bottom:1px solid var(--grid);font-size:.9375rem;line-height:1.5;color:var(--ink2)}
.took strong{color:var(--ink);font-weight:650}
@media (min-width:1100px){.tail{white-space:nowrap}}
.nb{white-space:nowrap}
.card .note{text-wrap:balance}
@media (min-width:900px){.took{grid-template-columns:repeat(2,minmax(0,1fr))}}
.ico{flex:none}
.i-line{fill:none;stroke:var(--ink2);stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}

/* chart cards */
.grid{display:grid;grid-template-columns:minmax(0,1fr);gap:18px}
.cols{display:grid;grid-template-columns:minmax(0,1fr);gap:18px;align-items:start;min-width:0}
.col{display:grid;grid-template-columns:minmax(0,1fr);gap:18px;align-content:start;min-width:0}
@media (min-width:900px){.cols{grid-template-columns:repeat(2,minmax(0,1fr))}}
.grid .card .cv-wide{max-width:900px;margin:0 auto}
.grid>.gridhead{margin:1.4rem 0 -.2rem;max-width:none;font-size:1.0625rem;font-weight:700;color:var(--ink)}
.grid>.gridhead:first-child{margin-top:.4rem}
.grid>.gridlead{margin:-.5rem 0 .1rem;max-width:none;font-size:.9375rem;line-height:1.55;color:var(--ink2)}
.card{container-type:inline-size;min-width:0;margin:0;padding:18px 20px 14px;background:var(--surface);border:1px solid var(--border);border-radius:6px}
/* a card that takes a full row: the chart at the left, its key figures and notes beside it */
@supports selector(:has(*)){@media (min-width:1100px){
.grid>.card.span2:has(>.keyfigs){display:grid;grid-template-columns:minmax(0,1.75fr) minmax(0,1fr);column-gap:40px;align-items:start}
.grid>.card.span2:has(>.keyfigs)>.cardtop,.grid>.card.span2:has(>.keyfigs)>h3,.grid>.card.span2:has(>.keyfigs)>.cardfoot{grid-column:1 / -1}
.grid>.card.span2:has(>.keyfigs)>figure{grid-column:1;grid-row:3 / span 8;margin-top:.4rem}
.grid>.card.span2:has(>.keyfigs)>:not(.cardtop):not(h3):not(figure):not(.cardfoot){grid-column:2}
.grid>.card.span2:has(>.keyfigs)>.keyfigs{grid-template-columns:minmax(0,1fr);gap:0;margin-top:.4rem;padding-top:0;border-top:1px solid var(--grid)}
.grid>.card.span2:has(>.keyfigs)>.keyfigs>div{padding:15px 0 17px;border-bottom:1px solid var(--grid)}
.grid>.card.span2:has(>.keyfigs)>.keyfigs dt{font-size:.9375rem;line-height:1.4;color:var(--ink2)}
.grid>.card.span2:has(>.keyfigs)>.keyfigs dd{margin-top:5px;font-size:clamp(1.625rem,2.3vw,2.125rem);line-height:1.15;letter-spacing:-.02em}
.grid>.card.span2:has(>.keyfigs)>.note{font-size:1rem}
}}
.cardtop{display:flex;align-items:baseline;gap:10px;min-height:1.2rem;font-size:.8125rem}
.fignum{font-weight:600;color:var(--muted)}
.badge{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.cardtop a{margin-left:auto;font-size:.875rem;color:var(--muted);text-decoration:none;opacity:0}
.card:hover .cardtop a,.cardtop a:focus-visible{opacity:1}
.card h3{font-size:1.125rem;font-weight:650;line-height:1.3;letter-spacing:-.008em;margin:.35rem 0 .6rem}
figure.chart-fig{margin:.9rem 0 .4rem}
.chart{margin:0}
.cv{max-width:100%}
.cv-narrow{display:none;max-width:430px}
.grid .cv-narrow{max-width:440px;margin:0 auto}
@media (max-width:699px){.cv-wide{display:none}.cv-narrow{display:block}.card{padding:14px 14px 10px}}
@container (max-width:600px){.cv-wide{display:none}.cv-narrow{display:block;max-width:none}}
figcaption{font-size:.8125rem;line-height:1.5;color:var(--muted);margin-top:8px;text-wrap:balance}
.svg{display:block;width:100%;height:auto}
.svg text{fill:var(--ink2);font-family:inherit}
.svg .ttl{fill:var(--ink);font-weight:700}
.svg .rl{fill:var(--ink)}
.svg .rl,.svg .val{paint-order:stroke;stroke:var(--surface);stroke-width:4px;stroke-linejoin:round}
.svg .tk{fill:var(--muted)}
.svg .val{fill:var(--ink);font-weight:650}
.svg .grid{stroke:var(--grid);stroke-width:1;shape-rendering:crispEdges}
.svg .axis{stroke:var(--axis);stroke-width:1;shape-rendering:crispEdges}
.svg .refline{stroke:var(--ink);stroke-width:1.5}
.svg .lblbg{fill:var(--surface)}
.svg .vmark{stroke:var(--ink);stroke-width:1.5;stroke-dasharray:5 4;shape-rendering:crispEdges}
.svg .bracket{fill:none;stroke:var(--axis);stroke-width:1.2}
.svg .s1{fill:var(--s1)}.svg .s2{fill:var(--s2)}.svg .sc{fill:var(--ctx)}.svg .sk{fill:var(--ink)}.svg .st2{fill:var(--ink2)}
.svg .track{fill:var(--grid)}
.svg .gap{fill:none}
.svg .band{fill:var(--s1);opacity:.22}
.svg .band2{fill:var(--s1);opacity:.38}
.svg .bandedge{stroke:var(--s1);stroke-width:2}
.svg .ln{fill:none;stroke-width:2.2;stroke-linejoin:round;stroke-linecap:round}
.svg .l1{stroke:var(--s1)}.svg .lk{stroke:var(--ink)}.svg .l2{stroke:var(--s2)}.svg .lc{stroke:var(--ctx)}
.svg .lg{stroke-width:2.2;stroke-linecap:round}
.svg .lg.refline{stroke-width:1.5}
.svg .wash{opacity:.12}
.svg .ring{stroke:var(--surface);stroke-width:2}
.svg .ghost{fill:none;stroke:var(--ctx);stroke-width:1.6}
.keyfigs{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px 16px;align-items:end;margin:.9rem 0 .2rem;padding-top:.8rem;border-top:1px solid var(--grid)}
.keyfigs div{min-width:0}
.keyfigs dt{font-size:.75rem;line-height:1.35;color:var(--muted)}
.keyfigs dd{margin:0;font-weight:650;font-size:1.0625rem;font-variant-numeric:lining-nums tabular-nums}
.cardfoot{display:flex;flex-wrap:wrap;gap:4px 20px;margin-top:.9rem;padding-top:.7rem;border-top:1px solid var(--grid)}
.cardfoot details{margin:0;border:0;padding:0;flex:0 0 auto;min-width:0}
.cardfoot details[open]{flex-basis:100%;order:1}
.cardfoot summary{display:inline;padding:0;font-size:.8125rem;font-weight:500;color:var(--link);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px;list-style:none}
.cardfoot summary::-webkit-details-marker{display:none}
.cardfoot summary:hover{text-decoration-thickness:2px}
.cardfoot details[open]>summary{display:block;margin:.3rem 0 .5rem;color:var(--ink);font-weight:650;text-decoration:none}
.finding{margin:.7rem 0 .4rem;font-weight:600}
.shows,.notshows{margin:.35rem 0}
.notshows{color:var(--ink2)}
.sn{display:grid;gap:10px;margin:.6rem 0 .2rem}
.sn p{margin:0;font-size:.9375rem;line-height:1.5;max-width:none}
.sn strong{font-weight:650;color:var(--ink)}
@media (min-width:900px){.sn{grid-template-columns:1fr 1fr}}
.source,.qnote{font-size:.875rem;color:var(--ink2);margin:.7rem 0 .3rem}
.source p{margin:0 0 .2rem}
.source ul{margin:.1rem 0 .3rem;padding-left:1.1rem}
.source li{margin:.15rem 0;max-width:none}
.source ul ul{padding-left:.9rem}
.notes{font-size:.9375rem;color:var(--ink2);margin:.8rem 0 .4rem;padding:0;list-style:none}
.notes li{margin:0 0 .6rem;line-height:1.55}
ul.rule{margin:.8rem 0;padding-left:1.1rem}
ul.rule li{margin:.35rem 0}
.sha{color:var(--muted);font-size:.8125rem;white-space:nowrap}
ol.fwd{list-style:none;padding:0;margin:.9rem 0;display:grid;gap:0;border-bottom:1px solid var(--grid)}
ol.fwd li{border-top:1px solid var(--grid);padding:10px 0;min-width:0;max-width:none}
ol.fwd p{margin:.2rem 0}
.fhead{margin:.2rem 0}
.fhead .st{font-size:.95rem}
.fword{font-weight:700}
.verbatim{font-size:.9rem}

/* details, code, tables */
details{margin:.45rem 0;border-top:1px solid var(--grid);padding-top:.35rem}
summary{cursor:pointer;font-weight:650;padding:4px 0}
pre{margin:.5rem 0 .6rem;padding:12px 14px;background:var(--code);border-radius:4px;overflow:auto;max-height:440px;line-height:1.45;tab-size:2}
.qh{margin:.7rem 0 0;font-size:.875rem}
.tablewrap{overflow:auto;max-height:420px;border-top:1px solid var(--axis);border-bottom:1px solid var(--grid);margin:.5rem 0 .7rem;
background:linear-gradient(to right,var(--surface) 30%,transparent) 0 0/34px 100% no-repeat local,
linear-gradient(to left,var(--surface) 30%,transparent) 100% 0/34px 100% no-repeat local,
linear-gradient(to right,var(--shade),transparent) 0 0/14px 100% no-repeat scroll,
linear-gradient(to left,var(--shade),transparent) 100% 0/14px 100% no-repeat scroll}
.scrollhint{display:none;font-size:.8125rem;color:var(--muted);margin:.4rem 0 0}
table{border-collapse:collapse;width:100%;font-size:.8125rem}
caption{text-align:left;font-weight:650;padding:8px 12px;color:var(--ink2)}
th,td{padding:6px 12px;border-bottom:1px solid var(--grid);white-space:nowrap;vertical-align:top;text-align:right;font-variant-numeric:lining-nums tabular-nums}
th{white-space:normal}
th.txt,td.t{text-align:left;font-variant-numeric:normal;white-space:normal;min-width:10rem}
@media (max-width:699px){th.txt,td.t{min-width:6.5rem}th,td{padding:5px 8px}.scrollhint{display:block}}
thead th{position:sticky;top:0;background:var(--surface);z-index:1;border-bottom:1px solid var(--axis);font-size:.75rem;color:var(--muted)}
tbody tr:last-child td{border-bottom:0}
.update{margin:2.4rem 0 1.2rem}
@media (min-width:1100px){.update{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.5fr);column-gap:48px;align-items:start}
.update .updh{grid-column:1 / -1}.update .tablewrap{margin-top:0}}
.update .updh{margin:.2rem 0 .4rem;font-size:1.0625rem}
.update .tablewrap{max-height:none;background:var(--surface)}
.update td:nth-child(3){font-weight:650;color:var(--ink)}
.update td:nth-child(2){color:var(--muted)}

/* method */
.meta{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:6px 16px;font-size:.9rem;margin:1rem 0;padding:12px 0;border-top:1px solid var(--grid);border-bottom:1px solid var(--grid)}
.meta dt{color:var(--muted);font-weight:600}
.meta dd{margin:0;min-width:0}
@media (max-width:560px){.meta{grid-template-columns:minmax(0,1fr)}.meta dd{margin-bottom:6px}}
#about .meta{margin:.8rem 0}
.docs,.toc{display:flex;flex-wrap:wrap;gap:4px 18px;list-style:none;padding:0;margin:.6rem 0}
ol.steps{padding-left:1.5rem;margin:.6rem 0}
ol.steps li{margin:.9rem 0;max-width:none;padding-left:.2rem}
ol.steps p{margin:.2rem 0}
.do code{display:inline-block;max-width:100%;white-space:pre-wrap;overflow-wrap:anywhere;background:var(--code);padding:3px 9px;border-radius:3px}
ul.plain{padding:0;list-style:none}
ul.plain li{margin:0 0 .7rem;line-height:1.55}
footer{margin:3.5rem 0 2.5rem;padding-top:1rem;border-top:1px solid var(--grid);font-size:.875rem;color:var(--ink2)}
footer p{max-width:none}
/* alignment pass: the Today values as one strip under the thesis, so the two columns above it end together */
@media (min-width:1100px){
#brief{grid-template-areas:"h kcap" "th kpis" "today today"}
.today{margin-top:2.4rem}
.todayrow{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));column-gap:36px}
.todayrow li{grid-template-columns:minmax(0,1fr);row-gap:3px;align-content:start;padding:12px 0;border-bottom:0}
.todayrow li .tl{grid-row:1}
.todayrow output{grid-column:1;grid-row:2;align-self:start;text-align:left;font-size:1.375rem;letter-spacing:-.015em}
.todayrow li .tw{grid-row:3}
}
/* wide charts keep the text size of the two-column charts: the chart column stops at 740px and the figures take the rest */
.grid .card .cv-wide{max-width:760px}
@supports selector(:has(*)){@media (min-width:1300px){
.grid>.card.span2:has(>.keyfigs){grid-template-columns:minmax(0,740px) minmax(0,1fr);column-gap:56px}
}}
/* two-column rows end on one line: the cards of the shorter column share the difference and their links sit at the bottom.
   The changed margins reproduce the ones block layout collapsed, so a card that does not grow keeps its height. */
@media (min-width:900px){
.cols{align-items:stretch}
.col{display:flex;flex-direction:column}
.col>.card{flex:1 0 auto;display:flex;flex-direction:column}
.col>.card>h3{margin-bottom:0}
.col>.card>figure.chart-fig{margin-bottom:.9rem}
.col>.card>.keyfigs{margin-top:0;margin-bottom:.9rem}
.col>.card>.cardfoot{margin-top:auto}
}
/* free height in a card that grows goes above and below its chart, not into a gap over the links */
@media (min-width:900px){
.col>.card>figure.chart-fig{margin:auto 0;padding:.9rem 0}
.col>.card>.cardfoot{margin-top:0}
}
/* a full-width card whose chart is shorter than its figures: the chart sits at mid height */
@supports selector(:has(*)){@media (min-width:1100px){.grid>.card.span2:has(>.keyfigs)>figure{align-self:center}}}
/* and one whose figures are shorter than its chart: the figures share the chart's height as even rows */
@supports selector(:has(*)){@media (min-width:1100px){
.grid>.card.span2:has(>.keyfigs):not(:has(>.note))>.keyfigs{grid-row:3 / span 8;align-self:stretch;align-items:stretch;grid-auto-rows:1fr}
.grid>.card.span2:has(>.keyfigs):not(:has(>.note))>.keyfigs>div{display:flex;flex-direction:column;justify-content:center}
}}
/* the side list fits one screen: its type and spacing follow the window's height */
@media (min-width:1680px){
.side{padding:clamp(10px,2.2vh,30px) 0 clamp(8px,1.8vh,24px);font-size:clamp(.7rem,1.5vh,.8125rem)}
.side a{padding:clamp(1px,.34vh,4px) 10px;line-height:1.3}
.side .sidecap{margin:clamp(.45rem,1.5vh,1.3rem) 0 clamp(.1rem,.4vh,.35rem);font-size:1em}
}
/* the update: a larger lead beside a tighter table, so the two columns are closer in height */
@media (min-width:1100px){
.update{grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr);column-gap:56px}
.update>p{font-size:1.125rem;line-height:1.6;color:var(--ink)}
.update th,.update td{padding-top:5px;padding-bottom:5px}
}
"""


# NEAR's logo mark, drawn faintly behind the cover. The path is the one in NEAR's own app template (github.com/near/create-near-app,
# templates/frontend/next-app/public/near-logo.svg, read on 2026-11-14), with its viewBox and its one transform, unaltered. The mark
# is NEAR's trademark: it names the subject of the page, and this repository's licence does not cover it.
NEAR_MARK_VIEWBOX = "0 0 26.707293 26.619026"
NEAR_MARK_PATH = ("m 24.079,0.690475 c -0.9891,0 -1.9075,0.511145 -2.4256,1.351425 l -5.5825,8.261 c -0.1819,0.2723 -0.1081,0.6393 0.1651,0.8206 0.2214,0.1471 0.5143,0.1289 0.716,-0.044 l 5.495,-4.75049 c 0.0913,-0.0819 0.232,-0.07356 0.3142,0.01744 0.0373,0.04171 0.0571,0.09556 0.0571,0.15092 V 21.3707 c 0,0.1228 -0.0997,0.2214 -0.223,0.2214 -0.0662,0 -0.1285,-0.0288 -0.1704,-0.0796 L 5.81436,1.69457 C 5.27339,1.05829 4.47904,0.691234 3.64284,0.690475 H 3.0623 C 1.4911,0.690475 0.217407,1.96 0.217407,3.52605 V 24.4739 c 0,1.5661 1.273693,2.8356 2.844893,2.8356 0.98913,0 1.9075,-0.5111 2.42565,-1.3514 l 5.58255,-8.261 c 0.1818,-0.2723 0.108,-0.6393 -0.1652,-0.8206 -0.2214,-0.1471 -0.5143,-0.1289 -0.7159,0.044 L 4.69436,21.671 C 4.60306,21.7529 4.4623,21.7445 4.38013,21.6535 4.34284,21.6118 4.32306,21.558 4.32382,21.5026 V 6.62554 c 0,-0.12286 0.09967,-0.22145 0.22293,-0.22145 0.06544,0 0.12859,0.02882 0.17044,0.07963 L 21.3255,26.3054 c 0.5409,0.6363 1.3353,1.0034 2.1715,1.0041 h 0.5805 c 1.5712,8e-4 2.8457,-1.268 2.8472,-2.834 V 3.52605 C 26.9247,1.96 25.651,0.690475 24.0798,0.690475 Z")


def near_mark_uri() -> str:
    """The mark as an inline image (a data: URI, so nothing is loaded), for a CSS mask."""
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='{NEAR_MARK_VIEWBOX}'>"
           f"<path transform='translate(-0.217407,-0.690475)' d='{NEAR_MARK_PATH}'/></svg>")
    return "data:image/svg+xml," + svg.replace("%", "%25").replace("<", "%3C").replace(">", "%3E").replace("#", "%23")


def css() -> str:
    return CSS.replace("/*DARK*/", DARK_TOKENS).replace("/*MARK*/", near_mark_uri()).strip()


# ------------------------------------------------------------------ icons (shape + label, never colour alone)
ICONS = {
    "lock": '<rect class="i-line" x="4.5" y="9" width="11" height="8" rx="1.6" /><path class="i-line" d="M7 9V6.6a3 3 0 0 1 6 0V9" />',
    "compass": '<circle class="i-line" cx="10" cy="10" r="8" /><path class="i-line" d="M12.9 7.1l-1.7 4.1-4.1 1.7 1.7-4.1z" />',
}


def icon(kind: str, size: int = 20) -> str:
    return (f'<svg class="ico" viewBox="0 0 20 20" width="{size}" height="{size}" aria-hidden="true" focusable="false">'
            f"{ICONS[kind]}</svg>")


# ------------------------------------------------------------------ plain words for the pre-registered results
# The page says what each pre-registered result found, in plain words, with no status stamps. PREREG.md's own outcome words (pass, fail,
# inconclusive; Buy, Hold, Avoid; PASS, MISS, not scorable) stay in data/metrics.json, the score files and THESIS.md, and
# docs/glossary.md maps them to the words below.
PLAIN_RESULT = {"pass": "confirmed", "fail": "refuted", "inconclusive": "unsettled"}
PLAIN_RATING = {"Buy": "Buy", "Avoid": "Avoid", "Hold": "None"}          # the signal the frozen rating rule gives
PLAIN_FORWARD = {"pending": "to be scored", "PASS": "came true", "MISS": "did not come true", "not scorable": "could not be scored"}


def plain_result(word: str) -> str:
    return PLAIN_RESULT[str(word)]


def plain_rating(word: str) -> str:
    return PLAIN_RATING[str(word)]


def plain_forward(word: str) -> str:
    return PLAIN_FORWARD[str(word)]


def check_pre_results(ctx: "Ctx") -> None:
    """The plain sentences about the pre-registered results are true of the data as committed: H1a's ratio is over its line, label
    coverage is under the pre-registered minimum, H1b's range spans the NEAR minted, H1c clears its bar at the lower bound only, both
    are unsettled, and the frozen rule gives no signal. If the data stop saying that, the render stops, so the page cannot go on saying it."""
    m = ctx.m
    ok = (m["h1a_pass_as_written"] is False and m["h1a_ratio_as_written_x"] >= CONSTS["h1a_pass_below_x"][0]
          and m["h1b_verdict"] == "inconclusive" and m["h1c_verdict"] == "inconclusive" and m["rating_output"] == "Hold"
          and m["h1b_coverage_count_pct"] < CONSTS["h1b_coverage_min_pct"][0]
          and m["h1b_net_inflow_lower_m"] < m["h1a_gross_issuance_90d_m"] < m["h1b_net_inflow_upper_m"]
          and m["h1c_ratio_upper_pct"] < CONSTS["h1c_min_pct"][0] <= m["h1c_ratio_lower_pct"])
    if not ok:
        raise SystemExit("render: the page describes the pre-registered results in plain words (H1a over its line, H1b's range around the NEAR "
                         "minted, H1c over its bar at one bound only, both unsettled at low label coverage, no signal from the rule); the data no "
                         "longer say that, so rewrite check_pre_results() and the sentences that rely on it")


# ------------------------------------------------------------------ building blocks
def code_link(path: str) -> str:
    return f'<a href="{esc(gh(path))}"><code>{esc(path)}</code></a>'


def raw_ref(ctx: Ctx, rel: str) -> str:
    """A committed raw snapshot (rel is relative to data/, e.g. raw/bq/x.json) with the first 12 hex of its SHA-256."""
    sha = ctx.sha12(rel)
    tail = f' <span class="sha" data-sha-of="{esc(rel)}">sha256 {esc(sha)}</span>' if sha else ""
    return f'<a href="{esc(gh("data/" + rel))}"><code class="rawref">data/{esc(rel)}</code></a>{tail}'


def source_p(ctx: Ctx, *, sql: tuple[str, ...] = (), raw: tuple[str, ...] = (), code: tuple[str, ...] = (),
             upstream: tuple[str, ...] = (), extra: str = "") -> str:
    """The Source block: SQL, raw snapshots (with the first 12 hex of their SHA-256), code and upstream endpoints."""
    items: list[str] = []
    if sql:
        items.append("<li>SQL: " + ", ".join(code_link(p) for p in sql) + "</li>")
    if raw:
        items.append("<li>Raw snapshot: <ul>" + "".join(f"<li>{raw_ref(ctx, r)}</li>" for r in raw) + "</ul></li>")
    if code:
        items.append("<li>Code: " + ", ".join(code_link(p) for p in code) + "</li>")
    if upstream:
        items.append("<li>Upstream: " + "; ".join(esc(u) for u in upstream) + "</li>")
    if extra:
        items.append(f"<li>{extra}</li>")
    return f'<div class="source"><p><strong>Source:</strong></p><ul>{"".join(items)}</ul></div>'


def sql_display(text: str, max_line: int = 400) -> tuple[str, int]:
    """The SQL as stored, except that any single line longer than max_line is cut where marked (the inlined account
    lists in sql/h1b_b_wnear_logs.sql run to 500 KB on one line). Returns (text, number of lines shortened)."""
    out: list[str] = []
    cut = 0
    for line in text.split("\n"):
        if len(line) > max_line:
            out.append(f"{line[:160]} [... {len(line) - 240:,} characters omitted on this line ...] {line[-80:]}")
            cut += 1
        else:
            out.append(line)
    return "\n".join(out), cut


H1B_RUN_NOTE = ("The header comment of this file says &ldquo;NOT run&rdquo; because it was written before the run. "
                "The run record is the 2026-11-06 23:23 UTC entry of "
                f'<a href="{esc(gh("PREREG-ADDENDUM.md"))}">PREREG-ADDENDUM.md</a>.')

# What the forward-test card says about the scorer's dry runs. tests/test_render.py reads both addendum entries it points at.
DRY_RUN_DISCLOSURE = (
    'Its first dry run read no scoring-window day for F2 to F4 and only the window-opening block for F1 '
    f'(<a href="{esc(gh("PREREG-ADDENDUM.md"))}">PREREG-ADDENDUM.md</a>, 2026-11-06 23:49 UTC entry, item 7). '
    'Later dry runs, and direct reads of the buyback wallet&rsquo;s balance, did touch window days; they are disclosed in the '
    f'2026-11-08 05:04 UTC entry of <a href="{esc(gh("PREREG-ADDENDUM.md"))}">PREREG-ADDENDUM.md</a>.')


def query_details(ctx: Ctx, sql: tuple[str, ...] = (), endpoints: tuple[tuple[str, str], ...] = (),
                  note: str = "") -> str:
    """The collapsed "Query" block: full SQL text for BigQuery-backed charts; endpoint and fetcher for API-backed ones."""
    parts: list[str] = []
    if note:
        parts.append(f'<p class="qnote">{note}</p>')
    for rel in sql:
        raw_text = ctx.read_text(rel)
        shown, cut = sql_display(raw_text)
        size = len(raw_text.encode("utf-8"))
        head = f'<p class="qh">{code_link(rel)} <span class="sha" data-r="bytes:{esc(rel)}">{size:,} bytes</span></p>'
        if rel.startswith("sql/h1b_"):
            head += f'<p class="qnote">{H1B_RUN_NOTE}</p>'
        if cut:
            plural, verb = ("s", "are") if cut != 1 else ("", "is")
            head += (f'<p class="qnote">This file is <span data-r="bytes:{esc(rel)}">{size:,}</span> bytes because it inlines the account lists. '
                     f'The page shows it as stored, except that <span data-r="cut:{esc(rel)}">{cut}</span> very long line{plural} '
                     f'{verb} cut where marked; the full file is at the link above.</p>')
        parts.append(f'{head}<pre tabindex="0"><code>{esc(shown)}</code></pre>')
    if endpoints:
        rows = "".join(f"<dt>{esc(k)}</dt><dd><code>{esc(val)}</code></dd>" for k, val in endpoints)
        parts.append(f'<dl class="ep">{rows}</dl>')
    return f'<details class="query"><summary>Query</summary>{"".join(parts)}</details>'


def table_html(cols: list[dict], rows: list[dict], *, caption: str = "", attrs: str = "") -> str:
    """cols: {"h": header, "num": bool (default True), "c": column key}; rows: {"k": row key | None, "cells": [markup]}.
    Numeric cells are right-aligned by the stylesheet; text cells carry class t."""
    th = "".join(
        f'<th scope="col"{"" if c.get("num", True) else " class=" + chr(34) + "txt" + chr(34)}'
        f'{" data-c=" + chr(34) + esc(c["c"]) + chr(34) if c.get("c") else ""}>{esc(c["h"])}</th>' for c in cols)
    body = []
    for r in rows:
        key = f' data-k="{esc(r["k"])}"' if r.get("k") is not None else ""
        tds = "".join(f'<td{"" if c.get("num", True) else " class=" + chr(34) + "t" + chr(34)}>{cell}</td>'
                      for c, cell in zip(cols, r["cells"]))
        body.append(f"<tr{key}>{tds}</tr>")
    cap = f"<caption>{esc(caption)}</caption>" if caption else ""
    return (f'<div class="tablewrap" role="region" aria-label="{esc(caption or "Data table")}" tabindex="0">'
            f"<table{(' ' + attrs) if attrs else ''}>{cap}<thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div>")


def data_details(*tables: str) -> str:
    return (f'<details class="data"><summary>Data</summary><p class="scrollhint">A table wider than the screen scrolls sideways.</p>'
            f'{"".join(tables)}</details>')


WIDE_CARDS = {"fwdcov", "ladder", "revenue", "usage"}   # span both columns of the wide grid


def fig_no(cid: str) -> int:
    """A card's figure number: its place on the page (the case, the supporting evidence, then the track record of pre-registered tests)."""
    return (CASE_IDS + EVID_IDS + tuple(c for c, _, _ in PRE_CARDS)).index(cid) + 1


def card(*, cid: str, kind: str, headline: str, shows: str, notshows: str, figure: str, caption: str,
         source: str, query: str, data: str, extra: str = "", notes: tuple[str, ...] = (), title: str = "", more: str = "", capnote: str = "") -> str:
    """One chart card. kind is "pre" (pre-registered) or "exp" (exploratory, chosen after the freeze).

    With a title, the h3 is that short title and the full headline sentence (p.finding) opens first under "Notes and sources",
    followed by what the chart shows and does not show; without one, the headline is the h3."""
    notes = tuple(notes) + ((capnote,) if capnote else ())   # a sentence kept out of the one-line caption
    finding = f'<p class="finding">{headline}</p>' if title else ""
    sn = (f'<div class="sn"><p class="shows"><strong>What it shows:</strong> {shows}</p>'
          f'<p class="notshows"><strong>What it does not show:</strong> {notshows}</p></div>')
    badge = ('<span class="badge badge-pre">Pre-registered</span>' if kind == "pre"
             else '<span class="badge badge-exp">Exploratory</span>')
    note_ul = f'<ul class="notes">{"".join(f"<li>{n}</li>" for n in notes)}</ul>' if notes else ""
    return (
        f'<section class="card{" span2" if cid in WIDE_CARDS else ""}" id="chart-{cid}" aria-labelledby="chart-{cid}-h">'
        f'<div class="cardtop"><span class="fignum">Figure {fig_no(cid)}</span>{badge}<a href="#chart-{cid}" aria-label="Link to this chart">#</a></div>'
        f'<h3 id="chart-{cid}-h">{title or headline}</h3>'
        f'<figure class="chart-fig">{figure}<figcaption>{caption}</figcaption></figure>'
        f'{extra}<div class="cardfoot"><details class="more"><summary>Notes and sources</summary>{finding}{sn}{more}{note_ul}{source}</details>{query}{data}</div></section>'
    )


# ------------------------------------------------------------------ chart helpers
def nice_axis(vmax: float, n: int = 4) -> tuple[list[float], float]:
    """Round tick values 0..top covering vmax in about n steps."""
    if vmax <= 0:
        return [0.0, 1.0], 1.0
    raw = vmax / n
    mag = 10 ** math.floor(math.log10(raw))
    step = mag
    for mult in (1, 2, 2.5, 5, 10):
        step = mult * mag
        if step * n >= vmax:
            break
    k = math.ceil(vmax / step - 1e-9)
    return [i * step for i in range(k + 1)], k * step


def nice_range(vmin: float, vmax: float, n: int = 4) -> tuple[list[float], float, float]:
    """Round ticks from below vmin (when negative) to above vmax: (ticks, lowest, highest)."""
    ticks_pos, top = nice_axis(vmax, n)
    step = ticks_pos[1] - ticks_pos[0]
    lo = math.floor(min(vmin, 0) / step) * step
    ticks = [lo + i * step for i in range(int(round((top - lo) / step)) + 1)]
    return ticks, lo, top


def bar(val: float, cls: str, txt: Txt, tip_text: str = "", lv: float | None = None) -> dict:
    """One bar. lv is the value the label prints, for the rare bar whose label is not its own value."""
    d = {"v": val, "cls": cls, "txt": txt, "tip": tip_text}
    if lv is not None:
        d["lv"] = lv
    return d


def keyfigs(items: list[tuple[str, str]]) -> str:
    return ('<dl class="keyfigs">' + "".join(f"<div><dt>{esc(k)}</dt><dd>{val}</dd></div>" for k, val in items)
            + "</dl>")


TAIL_CHARS = 56   # how much of a lead's ending stays on one line on a wide screen


def keep_tail(html: str, chars: int = TAIL_CHARS) -> str:
    """The same paragraph content with its last `chars` or so visible characters in span.tail, cut at a space outside every tag.

    On a wide screen span.tail does not wrap, so a paragraph that runs the full width of the page cannot end on a line of two or three words."""
    depth, seen, pos = 0, 0, len(html)
    for tok in reversed(re.split(r"(<[^>]+>)", html)):
        pos -= len(tok)
        if tok.startswith("<"):
            depth += 1 if tok.startswith("</") else (0 if tok.endswith("/>") else -1)   # read backwards: a closing tag opens a nested run
            continue
        for i in range(len(tok) - 1, -1, -1):
            if tok[i] == " " and depth == 0 and seen >= chars:
                return f'{html[:pos + i]} <span class="tail">{html[pos + i + 1:]}</span>'
            seen += 1
    return html


def tailed(html: str) -> str:
    """keep_tail() on every p.note, p.lede and p.fine in a run of HTML (a p never nests, so the shortest match is one paragraph)."""
    return re.sub(r'(<p class="(?:note|lede|fine)">)(.*?)(</p>)', lambda m: m.group(1) + keep_tail(m.group(2)) + m.group(3), html, flags=re.S)


def window_text(ctx: Ctx, days: int) -> str:
    end = date.fromisoformat(ctx.m["asof"])
    start = date.fromordinal(end.toordinal() - days + 1)
    return f"{start.isoformat()} to {end.isoformat()}"


def staking_rows(ctx: Ctx) -> list[dict]:
    """Daily pool flows from the committed BigQuery output (sql/staking_flows_daily.sql), with running totals."""
    raw = json.loads(ctx.read_text("data/raw/bq/staking_flows_daily.json"))
    out: list[dict] = []
    cn = cr = 0.0
    for x in raw:
        infl, outf, rw = float(x["inflow_near"]), float(x["outflow_near"]), float(x["rewards_near"])
        cn += outf - infl
        cr += rw
        out.append({"date": x["block_date"], "out": outf, "in": infl, "net": outf - infl, "rw": rw,
                    "cum_net": cn, "cum_rw": cr})
    if round(cn / 1e6, 1) != ctx.m["pool_net_outflow_90d_m"] or round(cr / 1e6, 2) != ctx.m["pool_rewards_90d_m"]:
        raise SystemExit("render: data/raw/bq/staking_flows_daily.json does not tie to metrics.json; run `make reproduce`")
    return out


# ------------------------------------------------------------------ pre-registered cards
def card_h1a(ctx: Ctx) -> str:
    m, Mt = ctx.m, ctx.Mt
    rows = staking_rows(ctx)
    n = len(rows)
    dates = [r["date"] for r in rows]
    title = "Net staking outflow against staking rewards, 90 days"
    desc = (f"Panel A, bars from zero in million NEAR: withdrawals {ctx.plain('pool_outflow_90d_m')}, deposits "
            f"{ctx.plain('pool_inflow_90d_m')}, net outflow {ctx.plain('pool_net_outflow_90d_m')}, staking rewards "
            f"{ctx.plain('h1a_staking_rewards_90d_m')}. Panel B, lines: cumulative net outflow ends at "
            f"{ctx.plain('pool_net_outflow_90d_m')} and cumulative rewards credited to pools at {ctx.plain('pool_rewards_90d_m')}.")

    def build(v: Variant) -> tuple[str, float]:
        a_rows = [
            {"label": "Withdrawals from staking pools by delegators",
             "bars": [bar(m["pool_outflow_90d_m"], "sc", T(Mt("pool_outflow_90d_m"), "M"),
                          f"Withdrawals: {ctx.plain('pool_outflow_90d_m')}M NEAR")]},
            {"label": "Deposits into staking pools by delegators",
             "bars": [bar(m["pool_inflow_90d_m"], "sc", T(Mt("pool_inflow_90d_m"), "M"),
                          f"Deposits: {ctx.plain('pool_inflow_90d_m')}M NEAR")]},
            {"label": "Net staking outflow (withdrawals minus deposits)",
             "bars": [bar(m["pool_net_outflow_90d_m"], "s2", T(Mt("pool_net_outflow_90d_m"), "M"),
                          f"Net outflow: {ctx.plain('pool_net_outflow_90d_m')}M NEAR")]},
            {"label": "Staking rewards (the pre-registered denominator)",
             "bars": [bar(m["h1a_staking_rewards_90d_m"], "s1", T(Mt("h1a_staking_rewards_90d_m"), "M"),
                          f"Staking rewards: {ctx.plain('h1a_staking_rewards_90d_m')}M NEAR")]},
        ]
        pass_line = eval_expr(f"{CONSTS['h1a_pass_below_x'][0]}*h1a_staking_rewards_90d_m", m)
        a, ha = hbar_panel(v, title="90-day totals, million NEAR", tag="A", rows=a_rows, vmax=250,
                           ticks=[0, 50, 100, 150, 200, 250],
                           refs=[{"v": pass_line, "label": T("H1a’s line: net outflow below ",
                                                              ctx.Dt("0.5*h1a_staking_rewards_90d_m", 2), "M")}])
        ys_net = [r["cum_net"] / 1e6 for r in rows]
        ys_rw = [r["cum_rw"] / 1e6 for r in rows]
        ticks, lo, top = nice_range(min(ys_net), max(ys_net))
        b, hb = line_panel(
            v, title="Running total since the first day, million NEAR (below zero: more went into the pools than out)", tag="B",
            xlabels=[date_short(d) for d in dates], xtick_idx=[0, n // 3, 2 * n // 3, n - 1], ymin=lo, ymax=top,
            yticks=ticks, h_plot=104 if v.narrow else 126,
            series=[{"cls": "l2", "dot": "s2", "ys": ys_net, "end": T(Mt("pool_net_outflow_90d_m"), "M"),
                     "name": "Net outflow from pools (withdrawals minus deposits)"},
                    {"cls": "l1", "dot": "s1", "ys": ys_rw, "end": T(Mt("pool_rewards_90d_m"), "M"),
                     "name": "Rewards credited to pools"}])
        return stack([(a, ha), (b, hb)])

    fig = dual(ctx, "chart-h1a", title, desc, build)
    daily = table_html(
        [{"h": "Day", "num": False, "c": "date"}, {"h": "Withdrawals", "c": "out"}, {"h": "Deposits", "c": "in"},
         {"h": "Net outflow", "c": "net"}, {"h": "Rewards credited", "c": "rw"},
         {"h": "Cumulative net outflow", "c": "cum_net"}, {"h": "Cumulative rewards", "c": "cum_rw"}],
        [{"k": r["date"], "cells": [esc(r["date"])] + [f"{r[c]:,.0f}" for c in ("out", "in", "net", "rw", "cum_net", "cum_rw")]}
         for r in rows],
        caption="Daily pool flows in NEAR (Panel B), 2026-08-07 to 2026-11-04", attrs='data-raw="raw/bq/staking_flows_daily.json"')
    totals = table_html(
        [{"h": "Panel A bar", "num": False}, {"h": "Million NEAR"}],
        [{"k": None, "cells": [esc("Withdrawals from staking pools"), ctx.M("pool_outflow_90d_m")]},
         {"k": None, "cells": [esc("Deposits into staking pools"), ctx.M("pool_inflow_90d_m")]},
         {"k": None, "cells": [esc("Net staking outflow"), ctx.M("pool_net_outflow_90d_m")]},
         {"k": None, "cells": [f'Staking rewards ({ctx.K("staking_rewards_share_pct")}% of gross issuance)', ctx.M("h1a_staking_rewards_90d_m")]},
         {"k": None, "cells": [f'H1a’s line ({ctx.K("h1a_pass_below_x")} x staking rewards)', ctx.D("0.5*h1a_staking_rewards_90d_m", 2)]}],
        caption="Panel A: 90-day totals in million NEAR")
    figs = keyfigs([
        ("Net outflow ÷ staking rewards", f'{ctx.M("h1a_ratio_as_written_x")}×'),
        ("H1a predicted", f'under {ctx.K("h1a_pass_below_x")}×'),
        ("Same ratio, archival pool state", f'{ctx.M("h1a_ratio_endpoint_archival_x")}×')])
    return card(
        cid="h1a", kind="pre",
        title=f'Net staking outflow: {ctx.M("h1a_ratio_as_written_x")}× staking rewards (H1a predicted under {ctx.K("h1a_pass_below_x")}×)',
        headline=f'Net staking outflow was {ctx.M("h1a_ratio_as_written_x")}× staking rewards over 90 days, '
                 f'where H1a predicted under {ctx.K("h1a_pass_below_x")}×.',
        shows=(f'Over the 90 days {window_text(ctx, 90)}, delegators withdrew {ctx.M("pool_outflow_90d_m")}M NEAR from staking pools and '
               f'deposited {ctx.M("pool_inflow_90d_m")}M, a net outflow of {ctx.M("pool_net_outflow_90d_m")}M NEAR against '
               f'{ctx.M("h1a_staking_rewards_90d_m")}M NEAR of staking rewards ({ctx.K("staking_rewards_share_pct")}% of the '
               f'{ctx.M("h1a_gross_issuance_90d_m")}M NEAR minted).'),
        notshows=('Whether rewards themselves stay staked: the ratio nets large principal flows in both directions, so it measures net principal churn. '
                  'Nor who withdrew or where the NEAR went: NEAR is fungible, so nothing here says which coins were sold, and whether the NEAR '
                  'reached exchanges is H1b, which the exchange labels cannot settle.'),
        figure=fig,
        caption=f'Window: 90 days, {window_text(ctx, 90)} (UTC). Unit: million NEAR.',
        extra=figs,
        notes=(f'The {ctx.M("h1a_gross_issuance_90d_m")}M NEAR minted is read from {ctx.M("h1a_epochs_in_window")} epoch-boundary block headers. '
               f'Panel B uses the {ctx.M("pool_rewards_90d_m")}M NEAR of rewards credited to pools in the daily series, so on that denominator the '
               f'ratio is {ctx.M("pool_net_outflow_to_rewards_x")}×; the pre-registered ratio is {ctx.M("h1a_ratio_as_written_x")}×.',
               f'With <code>lst-pool.near</code>, the only validator the pool-name filter misses in the validator sets sampled, added (post hoc; the test is '
               f'not redefined), the ratio is {ctx.M("h1a_ratio_with_lst_pool_x")}×, still far over H1a&rsquo;s line.'),
        source=source_p(ctx, sql=("sql/staking_flows_daily.sql", "sql/staking_pool_totals_endpoints.sql"),
                        raw=("raw/bq/staking_flows_daily.json", "raw/bq/staking_pool_totals_endpoints.json",
                             "raw/rpc/epoch_issuance.json", "raw/rpc/pool_endpoints_archival.json"),
                        code=("pipeline/h1a.py", "pipeline/fetch_issuance.py"),
                        upstream=("BigQuery public dataset bigquery-public-data.crypto_near_mainnet_us, table account_changes",
                                  "NEAR archival RPC epoch-boundary block headers")),
        query=query_details(ctx, sql=("sql/staking_flows_daily.sql", "sql/staking_pool_totals_endpoints.sql")),
        data=data_details(totals, daily))


@functools.lru_cache(maxsize=2)
def _dropped_accounts(text: str) -> tuple[str, ...]:
    rows = json.loads(text)
    return tuple(sorted(x["account"] for x in rows if x["leg"] == "top100" and x["tier"] is None and _nonexchange(x["account"])))


def side_measure_dropped(ctx: Ctx) -> list[str]:
    """The accounts that pipeline/h1b.py drops from the side measure, sorted: the unlabelled top-100 receivers of native NEAR whose names are
    a pool, intents.near, wrap.near or a sputnik-dao DAO. The rule is h1b's own (_nonexchange), applied to the same committed query result."""
    return list(_dropped_accounts(ctx.read_text("data/raw/bq/h1b_a_native_flows.json")))


def side_measure_note(ctx: Ctx) -> str:
    """Why the fourth bar of the H1b chart is longer than the upper bound (markup, for the card's notes).

    That bar is a side measure that pipeline/h1b.py computes as the upper bound (level 4) with the boundary rows of the sourced non-exchange
    accounts among the unlabelled top-100 receivers dropped. It is larger than the upper bound exactly when the dropped rows net to an outflow
    from the set. If the data stop showing that, or the accounts dropped stop being the two the sentence names (intents.near and a DAO
    account), the render stops, so the page cannot go on saying it."""
    m, M = ctx.m, ctx.M
    if not m["h1b_net_inflow_upper_ex_nonexchange_m"] > m["h1b_net_inflow_upper_m"]:
        raise SystemExit("render: the H1b card explains a side measure that is longer than the upper bound because the dropped flows net to an "
                         "outflow; the data no longer show that, so rewrite side_measure_note()")
    dropped = side_measure_dropped(ctx)
    daos = [a for a in dropped if a.endswith(".sputnik-dao.near")]
    if not (len(dropped) == 2 and "intents.near" in dropped and len(daos) == 1):
        raise SystemExit("render: the H1b card says the side measure leaves two accounts out, intents.near and a DAO account; pipeline/h1b.py now "
                         f"drops {len(dropped)} ({', '.join(dropped) or 'none'}), so rewrite side_measure_note()")
    return (f'The fourth bar of Panel A ({M("h1b_net_inflow_upper_ex_nonexchange_m")}M) is longer than the upper bound ({M("h1b_net_inflow_upper_m")}M) although it leaves two '
            f'accounts out: it is a side measure and does not tighten the bound. It drops the transfers between the sourced non-exchange accounts among the unlabelled top-100 receivers (here '
            f'<code>intents.near</code> and a DAO account) and accounts outside the set, which is how <code>pipeline/h1b.py</code> approximates taking them out of '
            f'the set counted as exchange-bound. More NEAR left the set through those transfers than entered it, so dropping them raises the total. The test '
            f'uses only the lower and upper bounds.')


def card_h1b(ctx: Ctx) -> str:
    m, Mt = ctx.m, ctx.Mt
    title = "Net exchange inflow as a range, and how much of the top 100 is labelled"
    desc = (f"Panel A, bars from zero in million NEAR: lower bound {ctx.plain('h1b_net_inflow_lower_m')}, upper bound "
            f"{ctx.plain('h1b_net_inflow_upper_m')}, tier 1 only {ctx.plain('h1b_net_inflow_tier1_m')}, upper bound without sourced "
            f"non-exchange accounts {ctx.plain('h1b_net_inflow_upper_ex_nonexchange_m')}; a reference line marks gross issuance "
            f"{ctx.plain('h1a_gross_issuance_90d_m')}. Panel B, bars from zero in percent: label coverage "
            f"{ctx.plain('h1b_coverage_count_pct')} against the required {CONSTS['h1b_coverage_min_pct'][1]}.")

    def build(v: Variant) -> tuple[str, float]:
        a_rows = [
            {"label": "Lower bound: unlabelled receivers count as 0% exchange-bound",
             "bars": [bar(m["h1b_net_inflow_lower_m"], "s1", T(Mt("h1b_net_inflow_lower_m"), "M"),
                          f"Lower bound: {ctx.plain('h1b_net_inflow_lower_m')}M NEAR")]},
            {"label": "Upper bound: every unlabelled top-100 receiver counts as exchange-bound",
             "bars": [bar(m["h1b_net_inflow_upper_m"], "s2", T(Mt("h1b_net_inflow_upper_m"), "M"),
                          f"Upper bound: {ctx.plain('h1b_net_inflow_upper_m')}M NEAR")]},
            {"label": "Side measure: cited tier-1 accounts only",
             "bars": [bar(m["h1b_net_inflow_tier1_m"], "sc", T(Mt("h1b_net_inflow_tier1_m"), "M"),
                          f"Tier 1 only: {ctx.plain('h1b_net_inflow_tier1_m')}M NEAR")]},
            {"label": "Side measure: upper bound without sourced non-exchange accounts",
             "bars": [bar(m["h1b_net_inflow_upper_ex_nonexchange_m"], "sc", T(Mt("h1b_net_inflow_upper_ex_nonexchange_m"), "M"),
                          f"Upper bound ex non-exchange: {ctx.plain('h1b_net_inflow_upper_ex_nonexchange_m')}M NEAR")]},
        ]
        a, ha = hbar_panel(v, title="Net exchange inflow, 90 days, million NEAR", tag="A", rows=a_rows, vmax=200,
                           ticks=[0, 50, 100, 150, 200],
                           refs=[{"v": m["h1a_gross_issuance_90d_m"],
                                  "label": T("gross issuance ", Mt("h1a_gross_issuance_90d_m"), "M (the H1b bar)")}])
        b_rows = [
            {"label": "Tiers 1-3 by count (the pre-registered measure)",
             "bars": [bar(m["h1b_coverage_count_pct"], "st2", T(Mt("h1b_coverage_count_pct"), "%"),
                          f"Coverage by count: {ctx.plain('h1b_coverage_count_pct')}%")]},
            {"label": "Tier 1 only, by count",
             "bars": [bar(m["h1b_coverage_tier1_count_pct"], "sc", T(Mt("h1b_coverage_tier1_count_pct"), "%"),
                          f"Tier 1 by count: {ctx.plain('h1b_coverage_tier1_count_pct')}%")]},
            {"label": "Tiers 1-3, weighted by inflow",
             "bars": [bar(m["h1b_coverage_inflow_pct"], "sc", T(Mt("h1b_coverage_inflow_pct"), "%"),
                          f"Coverage by inflow: {ctx.plain('h1b_coverage_inflow_pct')}%")]},
        ]
        b, hb = hbar_panel(v, title="Labelled share of the top-100 native-NEAR receivers, %", tag="B", rows=b_rows,
                           vmax=100, ticks=[0, 25, 50, 75, 100], tick_fmt=lambda t: f"{t:g}%",
                           refs=[{"v": CONSTS["h1b_coverage_min_pct"][0],
                                  "label": T("required for a point result: ", ctx.Kt("h1b_coverage_min_pct"), "%")}])
        return stack([(a, ha), (b, hb)])

    fig = dual(ctx, "chart-h1b", title, desc, build)
    tab = table_html(
        [{"h": "Measure", "num": False}, {"h": "Value"}, {"h": "Unit", "num": False}],
        [{"k": None, "cells": [esc("Net exchange inflow, lower bound"), ctx.M("h1b_net_inflow_lower_m"), esc("million NEAR")]},
         {"k": None, "cells": [esc("Net exchange inflow, upper bound"), ctx.M("h1b_net_inflow_upper_m"), esc("million NEAR")]},
         {"k": None, "cells": [esc("Side: tier 1 only"), ctx.M("h1b_net_inflow_tier1_m"), esc("million NEAR")]},
         {"k": None, "cells": [esc("Side: upper bound without sourced non-exchange accounts"),
                               ctx.M("h1b_net_inflow_upper_ex_nonexchange_m"), esc("million NEAR")]},
         {"k": None, "cells": [esc("Gross issuance, 90 days (the H1b bar)"), ctx.M("h1a_gross_issuance_90d_m"), esc("million NEAR")]},
         {"k": None, "cells": [esc("Native NEAR, lower bound"), ctx.M("h1b_native_lower_m"), esc("million NEAR")]},
         {"k": None, "cells": [esc("Native NEAR, upper bound"), ctx.M("h1b_native_upper_m"), esc("million NEAR")]},
         {"k": None, "cells": [esc("Coverage, tiers 1-3 by count (primary)"), ctx.M("h1b_coverage_count_pct"), esc("%")]},
         {"k": None, "cells": [esc("Coverage, tier 1 by count"), ctx.M("h1b_coverage_tier1_count_pct"), esc("%")]},
         {"k": None, "cells": [esc("Coverage, tiers 1-3 by inflow"), ctx.M("h1b_coverage_inflow_pct"), esc("%")]},
         {"k": None, "cells": [esc("Coverage required for a point result"), ctx.K("h1b_coverage_min_pct"), esc("%")]}],
        caption="Plotted values")
    return card(
        cid="h1b", kind="pre",
        title=f'Net exchange inflow: {ctx.M("h1b_net_inflow_lower_m")}M to {ctx.M("h1b_net_inflow_upper_m")}M NEAR ({ctx.M("h1a_gross_issuance_90d_m")}M minted)',
        headline=(f'Net exchange inflow lies between {ctx.M("h1b_net_inflow_lower_m")}M and '
                  f'{ctx.M("h1b_net_inflow_upper_m")}M NEAR, on either side of the {ctx.M("h1a_gross_issuance_90d_m")}M NEAR minted, so the exchange labels cannot settle H1b.'),
        shows=(f'Net exchange inflow of NEAR (native plus wNEAR) into labelled exchange accounts over the 90 days {window_text(ctx, 90)}, as a range: '
               f'{ctx.M("h1b_net_inflow_lower_m")}M NEAR if unlabelled receivers are not exchange-bound, {ctx.M("h1b_net_inflow_upper_m")}M NEAR if every '
               f'unlabelled top-100 receiver is.'),
        notshows=('That any of this NEAR was sold, or by whom (NEAR is fungible): it counts only labelled centralized-exchange accounts, so '
                  '1Click, a non-custodial route out of NEAR, is reported beside H1b and never inside it.'),
        figure=fig,
        caption=f'Window: 90 days, {window_text(ctx, 90)} (UTC).',
        notes=(f'Only {ctx.M("h1b_coverage_count_pct")}% of the top-100 native-NEAR receivers carry an exchange label ({ctx.M("h1b_coverage_tier1_count_pct")}% a cited '
               f'one; the rest are labelled by our sweep rule), below the '
               f'{ctx.K("h1b_coverage_min_pct")}% the pre-registration requires, so H1b is confirmed only if it is true at both bounds. The lower '
               f'bound is under gross issuance and the upper bound is far over it, so the labels cannot settle it.',
               'The upper bound is mechanical: it treats every unlabelled top-100 receiver as an exchange, including accounts that are probably not.',
               side_measure_note(ctx),
               'Labels are snapshots dated 2026-11-06, so exchange addresses retired before then may be missing, which biases the lower bound down. '
               'No citable NEAR address was found for OKX, Coinbase, Kraken, Bybit, HTX, Crypto.com, Upbit or Bithumb.'),
        source=source_p(ctx, sql=("sql/h1b_a_native_flows.sql", "sql/h1b_b_wnear_logs.sql", "sql/h1b_c_sweep_clusters.sql"),
                        raw=("raw/bq/h1b_a_native_flows.json", "raw/bq/h1b_b_wnear_logs.json", "raw/bq/h1b_c_sweep_clusters.json",
                             "raw/labels/exchange_accounts.json", "raw/labels/binance_por_address_2026-11-06.json"),
                        code=("pipeline/h1b.py",),
                        upstream=("BigQuery public dataset bigquery-public-data.crypto_near_mainnet_us, tables receipt_actions and execution_outcomes",
                                  "exchange labels: Binance proof-of-reserves address list and DefiLlama exchange-transparency adapters, snapshots dated 2026-11-06")),
        query=query_details(ctx, sql=("sql/h1b_a_native_flows.sql", "sql/h1b_b_wnear_logs.sql", "sql/h1b_c_sweep_clusters.sql")),
        data=data_details(tab))


def card_h1c(ctx: Ctx) -> str:
    m, Mt = ctx.m, ctx.Mt
    blocks = sorted(json.loads(ctx.read_text("data/raw/rpc/buyback_balance_endpoints.json"))["blocks"], key=int)  # the two end-point blocks
    title = "Identified buying as a share of net exchange inflow, against the 25% bar"
    desc = (f"Bars from zero in percent: identified buying is {ctx.plain('h1c_ratio_lower_pct')} percent of the lower bound of net "
            f"exchange inflow and {ctx.plain('h1c_ratio_upper_pct')} percent of the upper bound; a reference line marks the "
            f"{CONSTS['h1c_min_pct'][1]} percent bar H1c needs at both bounds.")

    def build(v: Variant) -> tuple[str, float]:
        rows = [
            {"label": "Identified buying ÷ lower bound of net exchange inflow",
             "bars": [bar(m["h1c_ratio_lower_pct"], "s1", T(Mt("h1c_ratio_lower_pct"), "%"),
                          f"Against the lower bound: {ctx.plain('h1c_ratio_lower_pct')}%")]},
            {"label": "Identified buying ÷ upper bound of net exchange inflow",
             "bars": [bar(m["h1c_ratio_upper_pct"], "s2", T(Mt("h1c_ratio_upper_pct"), "%"),
                          f"Against the upper bound: {ctx.plain('h1c_ratio_upper_pct')}%")]},
        ]
        return hbar_panel(v, title="Identified buying ÷ net exchange inflow, %", rows=rows, vmax=40,
                          ticks=[0, 10, 20, 30, 40], tick_fmt=lambda t: f"{t:g}%",
                          refs=[{"v": CONSTS["h1c_min_pct"][0], "label": T("H1c’s bar: at least ", ctx.Kt("h1c_min_pct"), "% at both bounds")}])

    fig = dual(ctx, "chart-h1c", title, desc, build)
    tab = table_html(
        [{"h": "Measure", "num": False}, {"h": "Value"}, {"h": "Unit", "num": False}],
        [{"k": None, "cells": [esc("Identified buying: increase in the buyback wallet's balance"), ctx.M("h1c_identified_buying_m"),
                               esc("million NEAR")]},
         {"k": None, "cells": [esc("Net exchange inflow, lower bound"), ctx.M("h1b_net_inflow_lower_m"), esc("million NEAR")]},
         {"k": None, "cells": [esc("Net exchange inflow, upper bound"), ctx.M("h1b_net_inflow_upper_m"), esc("million NEAR")]},
         {"k": None, "cells": [esc("Identified buying ÷ lower bound"), ctx.M("h1c_ratio_lower_pct"), esc("%")]},
         {"k": None, "cells": [esc("Identified buying ÷ upper bound"), ctx.M("h1c_ratio_upper_pct"), esc("%")]},
         {"k": None, "cells": [esc("H1c’s bar"), ctx.K("h1c_min_pct"), esc("%")]}],
        caption="Plotted values")
    figs = keyfigs([("Identified buying", f'{ctx.M("h1c_identified_buying_m")}M NEAR'),
                    ("Lower bound of net inflow", f'{ctx.M("h1b_net_inflow_lower_m")}M NEAR'),
                    ("Upper bound of net inflow", f'{ctx.M("h1b_net_inflow_upper_m")}M NEAR')])
    pointer = ('The net exchange inflow bounds in the denominator come from these two BigQuery queries, the same text as in the Query block of '
               '<a href="#chart-h1b">the H1b chart</a>; this chart adds one RPC read, below.')
    return card(
        cid="h1c", kind="pre",
        title=f'Identified buying: {ctx.M("h1c_ratio_lower_pct")}% of exchange inflow at one bound, {ctx.M("h1c_ratio_upper_pct")}% at the other',
        headline=(f'The buyback wallet grew by {ctx.M("h1c_identified_buying_m")}M NEAR, '
                  f'{ctx.M("h1c_ratio_lower_pct")}% of the lower bound of net exchange inflow but {ctx.M("h1c_ratio_upper_pct")}% of the upper; '
                  f'H1c needs at least {ctx.K("h1c_min_pct")}% at both bounds, so the labels cannot settle it either.'),
        shows=(f'Identified buying, the balance increase of <code>buybacks.multisignature.near</code> between the window&rsquo;s end-point blocks '
               f'({ctx.M("h1c_identified_buying_m")}M NEAR), as a share of the two net exchange inflow bounds from H1b.'),
        notshows=('That the buyback wallet&rsquo;s NEAR came from exchanges: NEAR is fungible, so the ratio is a market-wide balance and traces no individual coins.'),
        figure=fig,
        caption=f'Window: 90 days, {window_text(ctx, 90)} (UTC). Unit: percent.',
        extra=figs,
        notes=(f'With label coverage below {ctx.K("h1b_coverage_min_pct")}%, H1c is confirmed only if it reaches at least {ctx.K("h1c_min_pct")}% at both bounds. '
               f'It clears the bar against the lower bound and falls far short against the upper, so it stays unsettled; it inherits every limit of '
               f'H1b, including the {ctx.M("h1b_coverage_count_pct")}% label coverage.',
               f'The balance growth is the pre-registered numerator and all of it is used. {ctx.M("bb_deliveries_90d_m")}M NEAR of it is delivery from <code>intents.near</code> in the committed escrow table; '
               f'the other {ctx.M("bb_growth_not_delivered_m")}M NEAR ({ctx.M("bb_growth_not_delivered_pct")}%) is not, and a read of the chain on 2026-11-08 traces most of it to a DAO transfer from another NEAR revenue wallet '
               f'(THESIS.md, Limits). It stays unsettled whichever numerator is used.',
               'ETF and treasury-company holdings are not part of the test: PREREG.md says they would be reported where they can be measured, and none was measured. The buyback wallet holds its NEAR: none of it has been burned.'),
        source=source_p(ctx, sql=("sql/h1b_a_native_flows.sql", "sql/h1b_b_wnear_logs.sql"),
                        raw=("raw/rpc/buyback_balance_endpoints.json", "raw/bq/h1b_a_native_flows.json", "raw/bq/h1b_b_wnear_logs.json"),
                        code=("pipeline/h1b.py",),
                        upstream=("NEAR archival RPC view_account of buybacks.multisignature.near at the window's two end-point blocks (heights under Query)",
                                  "BigQuery public dataset bigquery-public-data.crypto_near_mainnet_us")),
        query=query_details(ctx, sql=("sql/h1b_a_native_flows.sql", "sql/h1b_b_wnear_logs.sql"), note=pointer,
                            endpoints=(("RPC call", f"view_account, account_id buybacks.multisignature.near, block_id {blocks[0]} and {blocks[-1]}"),
                                       ("Endpoint", "https://archival-rpc.mainnet.fastnear.com"))),
        data=data_details(tab))


def hold_explanation(ctx: Ctx) -> str:
    """Why the Hold of the frozen rating rule is not a view on NEAR (markup, for the rating card).

    The sentence is true of the data as committed: observed growth is far above the Avoid line (at least twice it), so a failed H1b would also
    give Hold, and coverage is below the pre-registered 50%, where (under the range rule as read before the results) H1b
    cannot fail. If the data stop supporting it the render stops, so the page cannot go on saying it."""
    m = ctx.m
    if not (m["rating_output"] == "Hold" and m["rating_if_h1b_fail"] == "Hold"
            and min(m["rating_g_obs_pct"], m["rating_g_obs_near_pct"]) >= 2 * m["rating_g_avoid_line_pct"]
            and m["h1b_coverage_count_pct"] < CONSTS["h1b_coverage_min_pct"][0]):
        raise SystemExit("render: the rating card explains the Hold with facts the data no longer support; rewrite hold_explanation()")
    M, K = ctx.M, ctx.K
    return (f'The rule gives no signal, and that carries no view on NEAR. Below {K("h1b_coverage_min_pct")}% label coverage H1b can come '
            f'out confirmed or unsettled but never refuted (the range rule as read before the results; <a href="{esc(gh("PREREG-ADDENDUM.md"))}">PREREG-ADDENDUM.md</a>, '
            f'2026-11-06 23:11 UTC entry, item 6), and observed revenue growth ({M("rating_g_obs_pct")}% a year; {M("rating_g_obs_near_pct")}% in NEAR terms) '
            f'is far above the avoid line ({M("rating_g_avoid_line_pct")}% a year, half of G_req {M("rating_g_req_pct")}%), so the rule could only ever have '
            f'given a buy signal or none; had H1b been refuted it would still have given none.')


def card_rating(ctx: Ctx) -> str:
    m, Mt = ctx.m, ctx.Mt
    go, gr = m["rating_g_obs_pct"], m["rating_g_req_pct"]
    h1b_word = str(m["h1b_verdict"])
    h1b_pass, h1b_fail = h1b_word.startswith("pass"), h1b_word.startswith("fail")
    title = "Rating rule inputs: required against observed growth in captured revenue"
    desc = (f"Bars from zero in percent a year: required growth G_req {ctx.plain('rating_g_req_pct')}, or "
            f"{ctx.plain('rating_g_req_no_hsp029_pct')} without HSP-029; observed growth G_obs {ctx.plain('rating_g_obs_pct')} in USD "
            f"and {ctx.plain('rating_g_obs_near_pct')} in NEAR terms. The frozen rule gives no buy or avoid signal.")

    def build(v: Variant) -> tuple[str, float]:
        rows = [
            {"label": "G_req: growth needed for captured revenue to equal net issuance by 2031-11-04",
             "bars": [bar(m["rating_g_req_pct"], "s1", T(Mt("rating_g_req_pct"), "%/yr"), f"G_req: {ctx.plain('rating_g_req_pct')}%/yr")]},
            {"label": "G_req without HSP-029's issuance cut",
             "bars": [bar(m["rating_g_req_no_hsp029_pct"], "sc", T(Mt("rating_g_req_no_hsp029_pct"), "%/yr"),
                          f"G_req without HSP-029: {ctx.plain('rating_g_req_no_hsp029_pct')}%/yr")]},
            {"label": "G_obs in USD: last 180 days against the 180 before, annualized",
             "bars": [bar(m["rating_g_obs_pct"], "s2", T(Mt("rating_g_obs_pct"), "%/yr"), f"G_obs (USD): {ctx.plain('rating_g_obs_pct')}%/yr")]},
            {"label": "G_obs in NEAR terms (sensitivity)",
             "bars": [bar(m["rating_g_obs_near_pct"], "sc", T(Mt("rating_g_obs_near_pct"), "%/yr"),
                          f"G_obs (NEAR terms): {ctx.plain('rating_g_obs_near_pct')}%/yr")]},
        ]
        return hbar_panel(v, title="Growth in captured Intents revenue, % a year", rows=rows, vmax=700,
                          ticks=[0, 100, 200, 300, 400, 500, 600, 700] if not v.narrow else [0, 200, 400, 600])

    fig = dual(ctx, "chart-rating", title, desc, build)

    def yn(b: bool) -> str:
        return "yes" if b else "no"

    ge = go >= gr
    avoid_g = go < gr / 2
    buy_met, avoid_met = ge and h1b_pass, avoid_g and h1b_fail
    hold_met = not (buy_met or avoid_met)

    def met(b: bool) -> str:
        return "met" if b else "not met"

    gives = {"Buy": "a buy signal", "Avoid": "an avoid signal", "Hold": "no signal"}[str(m["rating_output"])]
    h1b_now = plain_result(h1b_word)
    rule = (
        '<ul class="rule">'
        f'<li><strong>Buy signal</strong> needs G_obs ≥ G_req and H1b confirmed. Now: G_obs ≥ G_req is {yn(ge)} ({ctx.M("rating_g_obs_pct")} against '
        f'{ctx.M("rating_g_req_pct")}) and H1b confirmed is {yn(h1b_pass)} (it is {h1b_now}), so the buy signal is {met(buy_met)}.</li>'
        f'<li><strong>Avoid signal</strong> needs G_obs &lt; G_req ÷ 2 and H1b refuted. Now: G_obs &lt; G_req ÷ 2 is {yn(avoid_g)} and H1b refuted is '
        f'{yn(h1b_fail)} (it is {h1b_now}), so the avoid signal is {met(avoid_met)}.</li>'
        f'<li><strong>No signal</strong> otherwise{", which is the case" if hold_met else ""}. The rule gives <strong>{gives}</strong>.</li></ul>')
    tab = table_html(
        [{"h": "Input", "num": False}, {"h": "Value"}, {"h": "Unit", "num": False}],
        [{"k": None, "cells": [esc("G_req"), ctx.M("rating_g_req_pct"), esc("% a year")]},
         {"k": None, "cells": [esc("G_req without HSP-029"), ctx.M("rating_g_req_no_hsp029_pct"), esc("% a year")]},
         {"k": None, "cells": [esc("G_obs, USD"), ctx.M("rating_g_obs_pct"), esc("% a year")]},
         {"k": None, "cells": [esc("G_obs, NEAR terms"), ctx.M("rating_g_obs_near_pct"), esc("% a year")]},
         {"k": None, "cells": [esc("Captured revenue, last 90 days"), ctx.M("rating_r90_usd_m"), esc("USD million")]}],
        caption="Plotted values")
    figs = keyfigs([("Signal from the rule", esc(plain_rating(m["rating_output"]))),
                    ("If H1b were confirmed", esc(plain_rating(m["rating_if_h1b_pass"]))),
                    ("If H1b were refuted", esc(plain_rating(m["rating_if_h1b_fail"])))])
    return card(
        cid="rating", kind="pre",
        title='Rating rule: no buy or avoid signal',
        headline=('The frozen rating rule gives no buy or avoid signal, which carries no view on NEAR: a buy signal needs H1b confirmed and observed growth at '
                  'least the required growth, an avoid signal needs H1b refuted and observed growth under half the required growth, and the exchange labels '
                  'cannot settle H1b.'),
        shows=(f'The two inputs of the pre-registered rating rule: required growth G_req of {ctx.M("rating_g_req_pct")}% a year '
               f'({ctx.M("rating_g_req_no_hsp029_pct")}% without HSP-029) against observed growth G_obs of {ctx.M("rating_g_obs_pct")}% a year in USD '
               f'({ctx.M("rating_g_obs_near_pct")}% in NEAR terms).'),
        notshows=(f'A view on the token. {hold_explanation(ctx)} Nor does it show that the inputs are firm: G_req rests on constants committed after the freeze, '
                  f'with the as-written H1a result (the price, the length of HSP-029&rsquo;s ramp and its activation date; '
                  f'<code>data/raw/rpc/rating_assumptions.json</code>), and G_obs compares the last 180 days with the 180 before, a base window that straddles the '
                  f'2026-02-23 fee switch (pre-switch revenue counts as captured, as DefiLlama labels it), so it does not separate the switch from other causes, '
                  f'and most of the USD growth is the NEAR price. The NEAR-terms growth measures a step in the share of fees NEAR captures: over the same '
                  f'windows gross fees and volume grew far less (<code>docs/second-review.md</code>).'),
        figure=fig,
        caption=f'Observed growth: the last 180 days against the 180 days before, to {ctx.m["asof"]}.',
        extra=figs,
        notes=(f'The frozen rule, branch by branch: {rule}',
               f'G_req is the annual growth in captured Intents revenue ({ctx.M("rating_r90_usd_m")}M USD over the last 90 days, DefiLlama) needed for it to equal '
               f'the USD value of net new supply by 2031-11-04. G_obs is the growth of the last 180 days over the 180 before, annualized.',
               'G_req assumes HSP-029&rsquo;s issuance ramp. Its on-chain timelock ends on 2026-11-16, after the submission deadline. We first added that date up from the proposal&rsquo;s voting start, voting period and timelock period; two published sources give the same date (<code>PREREG-ADDENDUM.md</code>, 2026-11-12 23:50 UTC entry, item 3). Under the House of Stake procedures a Directors&rsquo; decision on execution follows the timelock, and the proposal text also says the cut needs validator adoption through a protocol upgrade; we state it as an open question and do not predict it.',
               f'Under the range rule as read before the results, a low-coverage H1b can come out confirmed or unsettled, never refuted, so the avoid branch cannot be '
               f'reached while coverage is below {ctx.K("h1b_coverage_min_pct")}%. The exploratory ladder below does not feed the rule.'),
        source=source_p(ctx, raw=("raw/rpc/rating_assumptions.json", "raw/rpc/epoch_issuance.json",
                                  "raw/llama/dailyRevenue_near-intents.json", "raw/coingecko/near_market_chart_365d.json"),
                        code=("pipeline/h1a.py",),
                        upstream=("DefiLlama dailyRevenue for near-intents", "CoinGecko NEAR daily price",
                                  "NEAR archival RPC epoch-boundary block headers")),
        query=query_details(ctx, endpoints=(
            ("DefiLlama revenue", "GET https://api.llama.fi/summary/fees/near-intents?dataType=dailyRevenue"),
            ("CoinGecko price", "GET https://api.coingecko.com/api/v3/coins/near/market_chart?vs_currency=usd&days=365&interval=daily"),
            ("Fetchers", "pipeline/fetch_keyless.py, pipeline/fetch_issuance.py"),
            ("Rule and arithmetic", "pipeline/h1a.py, function rating()"))),
        data=data_details(tab))


# ------------------------------------------------------------------ forward tests
def numline_panel(v: Variant, rows: list[dict]) -> tuple[str, float]:
    """One number line per forward test: the frozen prediction as a band, a reference value from the committed data,
    and (only once scored) the observed value. Axes do not start at zero; each says so in its title.

    Each test is one <g class="nl" data-id> stating its axis and plot box; the band carries its edges (data-a, data-b),
    each reference diamond and the observed dot carry data-v, which tests/test_render.py checks the position against."""
    fs = v.fs
    pad = 10.0
    pw = v.w - 2 * pad
    out: list[str] = []
    y = 0.0
    for r in rows:
        lo, hi = r["lo"], r["hi"]
        g: list[str] = []

        def sx(val: float, lo: float = lo, hi: float = hi) -> float:
            return pad + pw * (val - lo) / (hi - lo)

        tl = wrap_words(pl(r["title"]), int(v.w / (fs * 0.56)))
        for j, line in enumerate(tl):
            g.append(text(0, y + fs + j * (fs + 3), esc(line), cls="ttl", fs=fs))
        ya = y + len(tl) * (fs + 3) + 56      # axis y
        a, b = r["band"]
        g.append(f'<rect class="band" data-a="{dv(a)}" data-b="{dv(b)}" x="{n1(sx(a))}" y="{n1(ya - 10)}" '
                 f'width="{n1(sx(b) - sx(a))}" height="20" />')
        for e in (a, b):
            if lo < e < hi:
                g.append(vline(sx(e), ya - 10, ya + 10, "bandedge"))
        g.append(hline(pad, pad + pw, ya, "axis"))
        for t in r["ticks"]:
            g.append(vline(sx(t), ya, ya + 5, "axis"))
            tl_ = r["tick_fmt"](t)
            tx, tan = clamp_anchor(sx(t), tw(tl_, fs), v.w)
            g.append(text(tx, ya + fs + 8, esc(tl_), cls="tk", anchor=tan, fs=fs))
        # band label above the band
        bx = (sx(a) + sx(b)) / 2
        bl = r["band_label"]
        bw = tw(pl(bl), fs, True)
        bxa = min(max(bx, pad + bw / 2), pad + pw - bw / 2)
        g.append(text(bxa, ya - 16, mk(bl), cls="val", anchor="middle", fs=fs))
        # reference markers (values committed before the window opened)
        for ref in r.get("refs", []):
            rx = sx(ref["v"])
            g.append(f'<path class="ghost" data-v="{dv(ref["v"])}" d="M{n1(rx)},{n1(ya - 6)}l5,6l-5,6l-5,-6z" />')
            lw = tw(pl(ref["label"]), fs)
            if rx + lw / 2 > v.w - 2:
                anchor, lx = "end", v.w - 2
            elif rx - lw / 2 < 2:
                anchor, lx = "start", 2.0
            else:
                anchor, lx = "middle", rx
            g.append(text(lx, ya + fs * 2 + 14, mk(ref["label"]), cls="tk", anchor=anchor, fs=fs))
        obs = r.get("obs")
        if obs:
            ox = sx(obs["v"])
            g.append(f'<circle class="sk ring" data-v="{dv(obs["v"])}" cx="{n1(ox)}" cy="{n1(ya)}" r="6" />')
            ow = tw(pl(obs["label"]), fs, True)
            oxa = min(max(ox, pad + ow / 2), pad + pw - ow / 2)
            g.append(text(oxa, ya - 36, mk(obs["label"]), cls="val", anchor="middle", fs=fs))
        out.append(f'<g class="nl" data-id="{esc(r["id"])}" data-lo="{dv(lo)}" data-hi="{dv(hi)}" '
                   f'data-x0="{n1(pad)}" data-pw="{n1(pw)}">{"".join(g)}</g>')
        y = ya + fs * 2 + 34
    return "".join(out), y


def card_forward(ctx: Ctx) -> str:
    m, Mt = ctx.m, ctx.Mt
    fw = ctx.forward
    res = fw["results"] if fw else {}
    where = fw["_path"] if fw else ""
    opens = sf.SCORE_NOT_BEFORE.strftime("%Y-%m-%d %H:%M UTC")
    w0, w1 = sf.WINDOW

    def result_of(fid: str) -> dict:
        r = res.get(fid)
        return r if isinstance(r, dict) else {}

    def word_of(fid: str) -> str:
        return forward_word(fw, fid)

    def obs_of(fid: str, key: str):
        """The number a PASS or MISS test records under `key`, as a float. A test that is anything else has its numbers ignored (None),
        so recording it as 'not scorable' by hand is what clears a stop over a number (forward_number says so)."""
        if word_of(fid) not in ("PASS", "MISS"):
            return None
        return forward_number(fid, result_of(fid), key, where)

    def ftxt(fid: str, key: str, dec: int, scale: float = 1.0, suffix: str = "") -> Txt | None:
        v = obs_of(fid, key)
        if v is None:
            return None
        text_ = fmt_value(round(v / scale, dec), dec)
        return f'<tspan data-f="{fid}.{key}" data-scale="{n1(scale) if scale != 1 else 1}">{esc(text_)}</tspan>{esc(suffix)}', text_ + suffix

    # axes: the frozen band plus the reference value, widened if an observed value falls outside
    def axis(lo: float, hi: float, step: float, ob: float | None, what: str) -> tuple[float, float, list[float]]:
        if ob is not None:
            lo, hi = min(lo, math.floor((ob - step) / step) * step), max(hi, math.ceil((ob + step) / step) * step)
        k = math.ceil((hi - lo) / step - 1e-9)      # k intervals, k + 1 ticks; ob is finite (obs_of), so k is an integer
        if k + 1 > MAX_AXIS_TICKS:
            ticks = f"{k + 1:,}" if k < 10**9 else "over a billion"
            raise SystemExit(f"render: {what} is {ob:.6g}, which needs an axis of {ticks} ticks; the page draws at most "
                             f"{MAX_AXIS_TICKS}. That is too far from its band to be a measurement of this quantity, so the page cannot "
                             f"draw it. Check the snapshot behind {where}; if the data are wrong, {NOT_SCORABLE_FIX}")
        return lo, lo + k * step, [lo + i * step for i in range(k + 1)]

    o1, o2, o3, o4 = (obs_of("F1", "balance_near"), obs_of("F2", "mean_near_per_day"),
                      obs_of("F3", "take_rate_bp"), obs_of("F4", "intents_share_pct"))
    a1 = axis(2.0, 2.6, 0.2, o1 / 1e6 if o1 is not None else None, "F1.balance_near, in million NEAR,")
    a2 = axis(82.0, 94.0, 4.0, o2 / 1e3 if o2 is not None else None, "F2.mean_near_per_day, in thousand NEAR,")
    a3 = axis(0.0, 8.0, 2.0, o3, "F3.take_rate_bp, in basis points,")
    a4 = axis(0.0, 100.0, 25.0, o4, "F4.intents_share_pct, in percent,")

    def mk_obs(fid: str, key: str, val: float | None, dec: int, scale: float, suffix: str):
        t = ftxt(fid, key, dec, scale, suffix)
        return {"v": val, "label": T("observed ", t)} if (t and val is not None) else None

    title = "Forward tests F1 to F4: the frozen predictions" + (", with the scored results" if fw else ", before scoring")
    if fw:
        desc = "Four number lines, one per forward test. Each shows the frozen prediction as a shaded band and the observed value as a dot."
    else:
        desc = ("Four number lines, one per forward test. Each shows the frozen prediction as a shaded band and, as a diamond, the "
                "last value committed before the window opened. For F1 that is the balance known at the freeze (2026-11-05 22:51 UTC), "
                "before the window opened. No test is scored yet, so there is no observed value.")

    def build(v: Variant) -> tuple[str, float]:
        rows = [
            {"id": "F1", "title": T("F1: buyback wallet balance at the first final block after ", opens.split(" UTC")[0], " (million NEAR, axis does not start at zero)"),
             "lo": a1[0], "hi": a1[1], "ticks": a1[2], "tick_fmt": lambda t: f"{t:.1f}",
             "band": (CONSTS["f1_lo"][0] / 1e6, CONSTS["f1_hi"][0] / 1e6),
             "band_label": T("predicted ", ctx.Kt("f1_lo"), "M to ", ctx.Kt("f1_hi"), "M"),
             "refs": [] if fw else [{"v": m["buyback_wallet_near_m"], "label": T("at freeze, block ", Mt("rpc_block", 0), ": ", Mt("buyback_wallet_near_m"), "M")}],
             "obs": mk_obs("F1", "balance_near", o1 / 1e6 if o1 is not None else None, 3, 1e6, "M")},
            {"id": "F2", "title": T("F2: mean net supply increase per day, ", w0, " to ", w1, " (thousand NEAR a day, axis does not start at zero)"),
             "lo": a2[0], "hi": a2[1], "ticks": a2[2], "tick_fmt": lambda t: f"{t:g}",
             "band": (CONSTS["f2_lo"][0] / 1e3, CONSTS["f2_hi"][0] / 1e3),
             "band_label": T("predicted ", ctx.Kt("f2_lo"), "K to ", ctx.Kt("f2_hi"), "K"),
             "refs": [] if fw else [{"v": m["net_issuance_near_per_day_30d_k"], "label": T("30 days to ", m["asof"], ": ", Mt("net_issuance_near_per_day_30d_k"), "K")}],
             "obs": mk_obs("F2", "mean_near_per_day", o2 / 1e3 if o2 is not None else None, 1, 1e3, "K")},
            {"id": "F3", "title": T("F3: captured take rate, DefiLlama revenue ÷ volume, ", w0, " to ", w1, " (basis points)"),
             "lo": a3[0], "hi": a3[1], "ticks": a3[2], "tick_fmt": lambda t: f"{t:g}",
             "band": (a3[0], CONSTS["f3_max_bp"][0]),
             "band_label": T("predicted below ", ctx.Kt("f3_max_bp"), " bp"),
             "refs": [] if fw else [{"v": m["take_captured_bp_30d"], "label": T("30 days to ", m["asof"], ": ", Mt("take_captured_bp_30d"), " bp")}],
             "obs": mk_obs("F3", "take_rate_bp", o3, 2, 1.0, " bp")},
            {"id": "F4", "title": T("F4: NEAR Intents' share of peer-set volume, reported basis, ", w0, " to ", w1, " (percent)"),
             "lo": a4[0], "hi": a4[1], "ticks": a4[2], "tick_fmt": lambda t: f"{t:g}%",
             "band": (CONSTS["f4_min_pct"][0], a4[1]),
             "band_label": T("predicted ", ctx.Kt("f4_min_pct"), "% or more"),
             "refs": [] if fw else [{"v": m["intents_share_peerset_30d_pct"], "label": T("30 days to ", m["asof"], ": ", Mt("intents_share_peerset_30d_pct"), "%")}],
             "obs": mk_obs("F4", "intents_share_pct", o4, 1, 1.0, "%")},
        ]
        return numline_panel(v, rows)

    fig = dual(ctx, "chart-forward", title, desc, build)

    items = []
    for fid in ("F1", "F2", "F3", "F4"):
        pr = ctx.prereg_forward[fid]
        word = word_of(fid)
        r = result_of(fid)
        if fw and word != "not scorable" and r:
            if fid == "F1":
                nums = (f'Balance <span data-f="F1.balance_near" data-scale="1">{fmt_value(round(r["balance_near"]), 0)}</span> NEAR at block '
                        f'<span data-f="F1.block_height" data-scale="1">{fmt_value(int(r["block_height"]))}</span>.')
            elif fid == "F2":
                nums = (f'Mean <span data-f="F2.mean_near_per_day" data-scale="1">{fmt_value(round(r["mean_near_per_day"]), 0)}</span> '
                        f'NEAR a day over <span data-f="F2.n_deltas" data-scale="1">{fmt_value(int(r["n_deltas"]))}</span> daily deltas.')
            elif fid == "F3":
                nums = (f'Take rate <span data-f="F3.take_rate_bp" data-scale="1">{fmt_value(round(r["take_rate_bp"], 2), 2)}</span> bp '
                        f'(revenue $<span data-f="F3.revenue_usd" data-scale="1">{fmt_value(round(r["revenue_usd"]), 0)}</span> over volume '
                        f'$<span data-f="F3.volume_usd" data-scale="1">{fmt_value(round(r["volume_usd"]), 0)}</span>).')
            else:
                nums = (f'Intents share <span data-f="F4.intents_share_pct" data-scale="1">{fmt_value(round(r["intents_share_pct"], 1), 1)}</span>% '
                        f'of peer-set volume.')
        elif fw:
            why = (f'<span data-f="{fid}.why" data-scale="1">{wrap_reason(r["why"])}</span>' if "why" in r else "no reason recorded")
            nums = f'Could not be scored: {why}. It is never estimated.'
        else:
            nums = f"Scored after {esc(opens)}."
        items.append(
            f'<li data-k="{fid}"><p class="fhead"><strong>{fid}</strong> (prior probability '
            f'<span data-p="{fid}">{esc(pr["p"])}</span>): <span class="st">'
            f'<span class="fword" data-status="{fid}">{esc(plain_forward(word))}</span></span></p>'
            f'<p class="verbatim">{md_inline(pr["text"])}</p><p class="tnote">{nums}</p></li>')
    lst = f'<ol class="fwd">{"".join(items)}</ol>'

    if fw:
        counts = {k: sum(1 for f_ in ("F1", "F2", "F3", "F4") if word_of(f_) == k) for k in ("PASS", "MISS", "not scorable")}
        headline = (f'Of the four frozen predictions, <span data-f="@count.PASS" data-scale="1">{counts["PASS"]}</span> came true, '
                    f'<span data-f="@count.MISS" data-scale="1">{counts["MISS"]}</span> did not and '
                    f'<span data-f="@count.not scorable" data-scale="1">{counts["not scorable"]}</span> could not be scored.')
        shows = (f'The four predictions frozen in PREREG.md before the window {esc(w0)} to {esc(w1)}, scored as written, with the scorer&rsquo;s operational readings (PREREG-ADDENDUM.md, 2026-11-08 02:03 UTC entry, item 7), by '
                 f'<code>python3 -m pipeline.score_forward --score</code> on <span data-f="scored_at" data-scale="1">{esc(fw.get("scored_at", ""))}</span> '
                 f'from data fetched at <span data-f="snapshot_fetched_at" data-scale="1">{esc(fw.get("snapshot_fetched_at", ""))}</span>.')
        notes = ('Every result is published, whichever way it went. A test with missing data is recorded as not scorable and never estimated.',
                 'The bands are the frozen predictions and the dot is the observed value. The predictions were frozen before the window; the scorer was '
                 'written on 2026-11-06, after the window opened. ' + DRY_RUN_DISCLOSURE)
    else:
        headline = (f'Forward tests F1 to F4: four predictions frozen before the window {esc(w0)} to {esc(w1)}, to be scored after {esc(opens)}.')
        shows = (f'The four predictions frozen in PREREG.md before the window {esc(w0)} to {esc(w1)}, each with its prior probability; '
                 f'nothing is scored yet.')
        notes = ('The bands are the frozen predictions. The diamonds are the last values committed before the window opened, shown for scale and not as forecasts.',
                 'Every result will be published, whichever way it goes. A test with missing data will be recorded as not scorable and never estimated. The predictions were '
                 'frozen before the window; the scorer was written on 2026-11-06, after the window opened. ' + DRY_RUN_DISCLOSURE)
    notshows = ('A score before scoring opens: a dry run of the scorer is not a score and is never shown here.')
    tab_rows = []
    for fid in ("F1", "F2", "F3", "F4"):
        pr = ctx.prereg_forward[fid]
        tab_rows.append({"k": fid, "cells": [esc(fid), f'<span data-p="{fid}">{esc(pr["p"])}</span>', esc(plain_forward(word_of(fid))),
                                             f'<span class="verbatim">{esc(pr["text"].replace("**", "").replace("`", ""))}</span>']})
    tab = table_html([{"h": "Test", "num": False, "c": "id"}, {"h": "Prior probability", "c": "p"},
                      {"h": "Result", "num": False, "c": "status"}, {"h": "Frozen prediction (PREREG.md, verbatim)", "num": False, "c": "text"}],
                     tab_rows, caption="Forward tests as frozen")
    src_extra = (f'Scored result: <code>{esc(fw["_path"])}</code>.' if fw else
                 'No scored result is committed yet (<code>data/forward/score_*/result.json</code> with <code>is_score: true</code>).')
    return card(
        cid="forward", kind="pre",
        title=(f'Forward tests: <span data-f="@count.PASS" data-scale="1">{sum(1 for f_ in FORWARD_IDS if word_of(f_) == "PASS")}</span> of 4 came true'
               if fw else "Forward tests F1 to F4: scored after the window"),
        headline=headline, shows=shows, notshows=notshows, figure=fig,
        caption=(f'Window: {esc(w0)} to {esc(w1)} (UTC). Scoring {"opened" if fw else "opens"} {esc(opens)}. Each line has its own unit, named in its title.'),
        more=lst, notes=notes,
        source=source_p(ctx, code=("pipeline/score_forward.py",),
                        upstream=("DefiLlama dailyVolume and dailyRevenue (api.llama.fi)", "Nearblocks /v1/charts total_supply",
                                  "NEAR archival RPC view_account of buybacks.multisignature.near"),
                        extra=f'Frozen text: <a href="{esc(gh("PREREG.md"))}"><code>PREREG.md</code></a>, forward-test table. ' + src_extra),
        query=query_details(ctx, endpoints=(
            ("Scorer", "python3 -m pipeline.score_forward --score (refuses to run before 2026-11-14 00:00 UTC)"),
            ("DefiLlama", "GET https://api.llama.fi/summary/dexs/<slug>?dataType=dailyVolume; GET https://api.llama.fi/summary/fees/near-intents?dataType=dailyRevenue"),
            ("Nearblocks", "GET https://api.nearblocks.io/v1/charts"),
            ("NEAR RPC", "https://archival-rpc.mainnet.fastnear.com, view_account at the first final block after 2026-11-14 00:00 UTC"))),
        data=data_details(tab))


# ------------------------------------------------------------------ exploratory cards (chosen after the freeze)
def month_label(month: str) -> str:
    yy, mm = month.split("-")
    return f"{MONTHS[int(mm) - 1]} {yy}"


def block_label(window: str) -> str:
    a, b = window.split("..")
    return f"{date_short(a)} – {date_short(b)}"


FULL_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
               "November", "December")


def partial_month_note(ctx: Ctx) -> str:
    """'1-4 November' for an as-of date of 2026-11-04: the last month in the series is incomplete."""
    d = date.fromisoformat(ctx.m["asof"])
    return f"1-{d.day} {FULL_MONTHS[d.month - 1]}"


def escrow_attribution(ctx: Ctx) -> dict:
    """Where the funding hop of an escrow unshield (a single-use, escrow-path delivery) is traced per delivery and where it is
    attributed from samples, read from data/raw/escrow/deliveries.csv. Before the boundary the file mixes both kinds of row; from
    the first day after the last sample-attributed row on, every escrow-path delivery is traced (attribution "row"). The recurring
    collectors' deliveries have no funding hop and are not looked at here. Returns that first day, and the first and last sampled
    day in the same calendar month before it (None when there are none)."""
    with open(ctx.root / "data/raw/escrow/deliveries.csv", newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["path"] == "escrow_unshield"]
    last_sample = max((r["day"] for r in rows if r["attribution"] == "sample"), default="")
    traced = [r["day"] for r in rows if r["day"] > last_sample]
    if not traced:
        raise SystemExit("render: data/raw/escrow/deliveries.csv has no escrow delivery after its last sample-attributed row")
    first = min(traced)
    early = sorted(r["day"] for r in rows if r["attribution"] == "sample" and r["day"][:7] == first[:7])
    return {"traced_from": first, "sampled_first": early[0] if early else None, "sampled_last": early[-1] if early else None}


def card_ladder(ctx: Ctx) -> str:
    m, Mt = ctx.m, ctx.Mt
    tot, bb = m["ladder_all_wallets_pct_of_issuance"], m["ladder_buyback_only_pct_of_issuance"]
    pub, esc_, oth = (m["ladder_public_collectors_pct_of_issuance"], m["ladder_escrow_unshields_pct_of_issuance"],
                      m["ladder_other_pct_of_issuance"])
    title = "The value-capture ladder: NEAR delivered to the revenue wallets as a share of net issuance"
    desc = (f"Panel A: one bar on a 0 to 100 percent axis, filled to {ctx.plain('ladder_all_wallets_pct_of_issuance', 2)} percent. "
            f"Panel B, zoomed to 0 to 20 percent: a stacked bar of the same total split into public fee collectors "
            f"{ctx.plain('ladder_public_collectors_pct_of_issuance', 2)}, escrow unshields {ctx.plain('ladder_escrow_unshields_pct_of_issuance', 2)} "
            f"and one other source {ctx.plain('ladder_other_pct_of_issuance', 2)}, and the buyback wallet alone at {ctx.plain('ladder_buyback_only_pct_of_issuance', 2)}, a subset.")

    def build(v: Variant) -> tuple[str, float]:
        a, ha = hbar_panel(
            v, title="Share of net issuance matched, % (full scale: 100% is all of net issuance)", tag="A",
            rows=[{"label": "NEAR delivered to the three revenue wallets",
                   "bars": [{"v": tot, "cls": "st2", "track": True, "txt": T(Mt("ladder_all_wallets_pct_of_issuance", 2), "%"),
                             "tip": f"Three revenue wallets: {ctx.plain('ladder_all_wallets_pct_of_issuance', 2)}% of net issuance"}]}],
            vmax=100, ticks=[0, 25, 50, 75, 100], tick_fmt=lambda t: f"{t:g}%")
        segs = [{"v": pub, "cls": "s1", "tip": f"Public fee collectors: {ctx.plain('ladder_public_collectors_pct_of_issuance', 2)}%"},
                {"v": esc_, "cls": "s2", "tip": f"Escrow unshields: {ctx.plain('ladder_escrow_unshields_pct_of_issuance', 2)}%"},
                {"v": oth, "cls": "sc", "tip": f"One other recurring source: {ctx.plain('ladder_other_pct_of_issuance', 2)}%"}]
        b, hb = hbar_panel(
            v, title="Zoom: the same data on a 0 to 20% axis", tag="B",
            rows=[{"label": "All three revenue wallets, by how the NEAR arrived",
                   "bars": [{"v": tot, "cls": "st2", "segs": segs, "txt": T(Mt("ladder_all_wallets_pct_of_issuance", 2), "%")}]},
                  {"label": "Of which the buyback wallet alone (a subset of the three)",
                   "bars": [bar(bb, "st2", T(Mt("ladder_buyback_only_pct_of_issuance", 2), "%"),
                                f"Buyback wallet alone: {ctx.plain('ladder_buyback_only_pct_of_issuance', 2)}%")]}],
            vmax=20, ticks=[0, 5, 10, 15, 20], tick_fmt=lambda t: f"{t:g}%",
            legend_items=[("s1", T("Public fee collectors: ", Mt("ladder_public_collectors_pct_of_issuance", 2), "%"), "rect"),
                          ("s2", T("Escrow unshields, fee stream unattested: ", Mt("ladder_escrow_unshields_pct_of_issuance", 2), "%"), "rect"),
                          ("sc", T("One other recurring source: ", Mt("ladder_other_pct_of_issuance", 2), "%"), "rect")])
        return stack([(a, ha), (b, hb)])

    fig = dual(ctx, "chart-ladder", title, desc, build)
    tab = table_html(
        [{"h": "Rung", "num": False}, {"h": "% of net issuance"}, {"h": "How the NEAR arrived", "num": False}],
        [{"k": None, "cells": [esc("All three revenue wallets"), ctx.M("ladder_all_wallets_pct_of_issuance", 2),
                               esc("sum of the collector, escrow and other-source rows below")]},
         {"k": None, "cells": [esc("Of which the buyback wallet alone"), ctx.M("ladder_buyback_only_pct_of_issuance", 2),
                               esc("a subset of the total, overlapping the rows below")]},
         {"k": None, "cells": [esc("Traceable to two recurring public fee collectors"), ctx.M("ladder_public_collectors_pct_of_issuance", 2),
                               esc("fee collectors A and B")]},
         {"k": None, "cells": [esc("… of which fees from publicly settled swaps"), ctx.M("ladder_collectors_public_swap_pct_of_issuance", 2),
                               esc("the fee payer swapped publicly in the same receipt")]},
         {"k": None, "cells": [esc("… of which fees paid from escrow-funded single-use accounts"), ctx.M("ladder_collectors_escrow_funded_pct_of_issuance", 2),
                               esc("the escrow funded the payer moments before; all at collector A")]},
         {"k": None, "cells": [esc("Released from the Confidential Intents escrow"), ctx.M("ladder_escrow_unshields_pct_of_issuance", 2),
                               esc("fee stream unattested")]},
         {"k": None, "cells": [esc("One other recurring source"), ctx.M("ladder_other_pct_of_issuance", 2), esc("recurring, unnamed")]},
         {"k": None, "cells": [esc("Net issuance, NEAR a day (denominator)"), ctx.M("net_issuance_near_per_day_window", 0),
                               esc("two archival total_supply reads, matched to the window")]}],
        caption="Plotted values, 30 days to the as-of date")
    figs = keyfigs([("Three-wallet total", f'{ctx.M("revwallets_near_k")}K NEAR'),
                    ("Share of DefiLlama's reported Intents revenue, same days", f'{ctx.M("revwallets_vs_llama_rev_pct")}%'),
                    ("Net issuance", f'{ctx.M("net_issuance_near_per_day_window", 0)} NEAR a day')])
    note_job = re.search(r"bqjob_[0-9a-z_]+", ctx.manifest.get("raw/escrow/deliveries.csv", {}).get("source", ""))
    job_text = (f" The BigQuery job that traced the funding hops from {escrow_attribution(ctx)['traced_from']} is recorded in <code>data/MANIFEST.json</code> "
                f"(<code>{esc(note_job.group(0))}</code>); its SQL is not committed in <code>sql/</code>, so the per-delivery table "
                f"<code>data/raw/escrow/deliveries.csv</code> and <code>python3 -m pipeline.fetch_escrow verify</code> are the "
                f"re-checkable evidence.") if note_job else ""
    return card(
        cid="ladder", kind="exp",
        title=f'Verifiable value capture: {ctx.M("ladder_public_collectors_pct_of_issuance", 2)}% to {ctx.M("ladder_all_wallets_pct_of_issuance", 2)}% of net issuance',
        headline=(f'NEAR delivered to NEAR&rsquo;s three Intents revenue wallets equalled {ctx.M("ladder_all_wallets_pct_of_issuance", 2)}% of net '
                  f'issuance; only {ctx.M("ladder_public_collectors_pct_of_issuance", 2)} points trace to public fee collectors and '
                  f'{ctx.M("ladder_escrow_unshields_pct_of_issuance", 2)} arrive as unshields from the Confidential Intents escrow, fee stream unattested.'),
        shows=(f'How much of NEAR&rsquo;s net issuance ({ctx.M("net_issuance_near_per_day_window", 0)} NEAR a day over the 30 days {window_text(ctx, 30)}) '
               f'was matched by NEAR delivered to the three revenue wallets, split by how it arrived: '
               f'{ctx.M("ladder_public_collectors_pct_of_issuance", 2)}% from two recurring public fee collectors and '
               f'{ctx.M("ladder_escrow_unshields_pct_of_issuance", 2)}% released from the Confidential Intents escrow, plus '
               f'{ctx.M("ladder_other_pct_of_issuance", 2)}% from one other source.'),
        notshows=(f'Which fee stream pays for the escrow releases: the NEAR verifiably arrived, but the public chain cannot split the '
                  f'{ctx.M("ladder_escrow_unshields_pct_of_issuance", 2)} points between the two candidate NEAR-side streams that fit, so, if those three are all of NEAR&rsquo;s Intents revenue wallets, measured value capture is a '
                  f'range, {ctx.M("ladder_public_collectors_pct_of_issuance", 2)}% to {ctx.M("ladder_all_wallets_pct_of_issuance", 2)}% of issuance.'),
        figure=fig,
        caption=(f'Window: the 30 days {window_text(ctx, 30)} (UTC). Unit: percent of net issuance. Panel B is a zoom of Panel A.'),
        extra=figs,
        notes=('The two candidate readings are near.com&rsquo;s fees and the Confidential Infrastructure Fee. A per-stream attestation by NEAR would turn the '
               'range into one number. Nothing here alleges misconduct. This is consistent with a privacy feature working as documented, and the question is auditability.',
               'The rungs are not nested: collectors, escrow and one other source add up to all three wallets, and the buyback-wallet rung is a subset of the total.',
               f'Not all of the collector rung is public settlement. Of its {ctx.M("ladder_public_collectors_pct_of_issuance", 2)} points, '
               f'{ctx.M("ladder_collectors_escrow_funded_pct_of_issuance", 2)} were fees paid by single-use accounts the escrow had funded '
               f'(exploratory, every transfer into the collectors classified by sender), so {ctx.M("ladder_escrow_all_pct_of_issuance", 2)} points '
               f'passed through the escrow in all, and counting only publicly settled swaps the floor is {ctx.M("ladder_collectors_public_swap_pct_of_issuance", 2)}%. '
               f'By the last day, {ctx.M("collector_a_escrow_usd_share_last_day_pct")}% of collector A&rsquo;s fee value came from escrow-funded accounts.',
               f'The total matches DefiLlama: {ctx.M("revwallets_near_k")}K NEAR is {ctx.M("revwallets_vs_llama_rev_pct")}% of its reported Intents revenue '
               f'for the same days. DefiLlama&rsquo;s adapter takes the same three wallets from NEAR&rsquo;s own Dune query, so it is the same count: it checks our pricing and wallet list and gives no independent check of the wallets. Even the top of the range covers about a sixth of issuance, and the buyback wallet holds its NEAR: none of it has been burned.',
               f'No valuation is made here. The range is the finding: {ctx.M("ladder_all_wallets_pct_of_issuance", 2)}% is what reached the three wallets and '
               f'{ctx.M("ladder_public_collectors_pct_of_issuance", 2)}% is what is traced to public fee collectors. None of this feeds the rating rule.'),
        source=source_p(ctx, sql=("sql/buyback_withdraw_sources.sql", "sql/collector_inflow_funders.sql", "sql/collector_funder_checks.sql"),
                        raw=("raw/escrow/deliveries.csv", "raw/escrow/issuance_reads.json", "raw/escrow/verify_sample.json",
                             "raw/bq/buyback_withdraw_sources.json", "raw/bq/collector_inflow_funders.json",
                             "raw/bq/collector_funder_checks.json"),
                        code=("pipeline/compute.py", "pipeline/fetch_escrow.py"),
                        upstream=("BigQuery public dataset bigquery-public-data.crypto_near_mainnet_us, table execution_outcomes (intents.near native_withdraw events)",
                                  "FastNEAR transaction API and NEAR archival RPC (keyless) for the funding hops and the two total_supply reads")),
        query=query_details(ctx, sql=("sql/buyback_withdraw_sources.sql", "sql/collector_inflow_funders.sql", "sql/collector_funder_checks.sql"),
                            note="Re-check any delivery or funding transfer from the chain with no key: <code>python3 -m pipeline.fetch_escrow verify --sample 60</code>."
                                 + job_text),
        data=data_details(tab))


def escrow_sql_matches_table(ctx: Ctx, d0: str, d1: str) -> bool:
    """True when the committed output of sql/buyback_withdraw_sources.sql has, for every day d0..d1 and every wallet, the same
    NEAR as the per-delivery table data/raw/escrow/deliveries.csv (exact decimal arithmetic)."""
    from decimal import Decimal
    sql_rows = json.loads(ctx.read_text("data/raw/bq/buyback_withdraw_sources.json"))
    want: dict[tuple[str, str], Decimal] = {}
    for x in sql_rows:
        k = (x["day"], x["wallet"])
        want[k] = want.get(k, Decimal(0)) + Decimal(x["near"])
    got: dict[tuple[str, str], Decimal] = {}
    with open(ctx.root / "data/raw/escrow/deliveries.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if d0 <= r["day"] <= d1:
                k = (r["day"], r["wallet"])
                got[k] = got.get(k, Decimal(0)) + Decimal(int(r["amount_yocto"])) / Decimal(10**24)
    return want.keys() == got.keys() and all(abs(want[k] - got[k]) < Decimal("0.000001") for k in want)


def escrow_query_note(ctx: Ctx) -> str:
    """What the escrow chart's Query block does and does not cover. The SQL names its own dates; the chart is drawn from the
    per-delivery table, whose sources the manifest names. The sentence that the SQL's output equals the table over its
    dates is printed only when the renderer has just checked that it does."""
    mt = re.search(r"BETWEEN '(\d{4}-\d{2}-\d{2})' AND '(\d{4}-\d{2}-\d{2})'", ctx.read_text("sql/buyback_withdraw_sources.sql"))
    cover = f"This SQL covers only {mt.group(1)} to {mt.group(2)}. " if mt else ""
    same = ("Its committed output, <code>data/raw/bq/buyback_withdraw_sources.json</code>, has the same NEAR per day and wallet as the "
            "per-delivery table the chart is drawn from, <code>data/raw/escrow/deliveries.csv</code>, over those days; it does not trace "
            "funding hops. ") if mt and escrow_sql_matches_table(ctx, mt.group(1), mt.group(2)) else ""
    src = ctx.manifest.get("raw/escrow/deliveries.csv", {}).get("source", "")
    where = (f"Earlier deliveries, and the funding hops of the single-use deliveries, come from the sources that <code>data/MANIFEST.json</code> records "
             f"for that table: <code>{esc(src)}</code>. ") if src else ""
    return (f"{cover}{same}{where}The monthly shares are computed in <code>pipeline/compute.py</code>, function <code>escrow_ladder</code>, from "
            f"the per-delivery table. Re-check any delivery with <code>python3 -m pipeline.fetch_escrow verify --sample 60</code>.")


def card_escrow(ctx: Ctx) -> str:
    m, Mt = ctx.m, ctx.Mt
    months = m["escrow_share_of_buyback_by_month"]
    asof = m["asof"]
    att = escrow_attribution(ctx)
    traced_from = att["traced_from"]
    cats, rows = [], []
    for i, row in enumerate(months):
        yy, mm = row["month"].split("-")
        key = f"escrow_share_buyback_{yy}_{mm}_pct"
        sub = row.get("note") or (f"to {asof[5:]}" if row["month"] == asof[:7] else "")
        lab = MONTHS[int(mm) - 1] + (f"\n({sub})" if sub else "")
        cats.append({"label": lab, "vals": [row["share_pct"]], "txts": [T(Mt(key), "%")],
                     "tips": [f"{month_label(row['month'])}: {ctx.plain(key)}% of NEAR delivered to the buyback wallet came through the escrow"]})
        rows.append({"k": row["month"], "cells": [esc(month_label(row["month"])), ctx.M(f"escrow_share_of_buyback_by_month.{i}.share_pct"),
                                                  ctx.M(f"escrow_share_of_buyback_by_month.{i}.note") if row.get("note") else ""]})
    sampled = [i for i, r in enumerate(months) if r["month"] < traced_from[:7]]
    traced = [i for i, r in enumerate(months) if r["month"] >= traced_from[:7]]
    footnote = (f"{FULL_MONTHS[int(traced_from[5:7]) - 1]} includes {att['sampled_first']} to {att['sampled_last']}, attributed from samples."
                if att["sampled_first"] else None)
    title = "Share of the buyback wallet's NEAR that arrived through the Confidential Intents escrow, by month"
    desc = ("Columns from zero in percent, one per month from July to November 2026: " +
            ", ".join(f"{month_label(r['month'])} {ctx.plain('escrow_share_of_buyback_by_month.%d.share_pct' % i)}" for i, r in enumerate(months)) + ".")

    def build(v: Variant) -> tuple[str, float]:
        brackets = []
        if sampled:
            brackets.append({"i0": sampled[0], "i1": sampled[-1], "label": "funding hop attributed from samples"})
        if traced:
            brackets.append({"i0": traced[0], "i1": traced[-1], "label": f"funding hop traced per single-use delivery from {traced_from}"})
        return vcol_panel(v, title="Escrow unshields as % of NEAR delivered to buybacks.multisignature.near", cats=cats,
                          series=[{"cls": "s1", "name": "Escrow share"}], ymax=100, yticks=[0, 25, 50, 75, 100],
                          tick_fmt=lambda t: f"{t:g}%", h_plot=130 if not v.narrow else 120, brackets=brackets, footnote=footnote)

    fig = dual(ctx, "chart-escrow", title, desc, build)
    tab = table_html([{"h": "Month", "num": False}, {"h": "Escrow share of the buyback wallet's NEAR, %"}, {"h": "Note", "num": False}],
                     rows, caption="Plotted values")
    figs = keyfigs([("Single-use deliveries in the 30-day window", ctx.M("escrow_single_use_30d_n")),
                    ("Funded by the escrow for the exact amount", f'{ctx.M("escrow_funded_exact_30d_n")} ({ctx.M("escrow_funded_exact_30d_pct")}%)'),
                    ("Escrow share, 30-day window", f'{ctx.M("escrow_share_of_buyback_near_30d_pct")}%')])
    return card(
        cid="escrow", kind="exp",
        title=f'Escrow share of the buyback wallet&rsquo;s NEAR: {ctx.M("escrow_share_buyback_2026_08_pct")}% in August, {ctx.M("escrow_share_buyback_2026_09_pct")}% in September',
        headline=(f'The escrow&rsquo;s share of the buyback wallet&rsquo;s NEAR stepped up once, at the end of August, and has been flat since: {ctx.M("escrow_share_buyback_2026_07_pct")}% in July and '
                  f'{ctx.M("escrow_share_buyback_2026_08_pct")}% in August, then {ctx.M("escrow_share_buyback_2026_09_pct")}% in September, {ctx.M("escrow_share_buyback_2026_10_pct")}% in October and {ctx.M("escrow_share_buyback_2026_11_pct")}% for {partial_month_note(ctx)}.'),
        shows=('For each calendar month, the share of NEAR delivered to <code>buybacks.multisignature.near</code> that came from single-use accounts '
               'funded by the Confidential Intents escrow (unshields), apart from what the recurring fee collectors delivered.'),
        notshows='Which fee stream the escrow NEAR comes from, which is unattested (the releases move day by day with confidential swap volume, <code>docs/confidential-flow.md</code>), and any share in USD terms: these are shares of NEAR delivered.',
        figure=fig,
        caption=f'Window: 2026-07-07 to {esc(asof)} (UTC), by calendar month. Unit: percent of NEAR delivered.',
        extra=figs,
        notes=(f'Before {traced_from} the funding of a single-use (escrow-path) delivery is mostly attributed from samples; from that date the funding hop of every '
               f'single-use (escrow-path) delivery in the window is traced (every single-use delivery in the 30-day window, {ctx.M("escrow_single_use_30d_n")}), '
               f'so the earlier months are less firmly established. In the window, deliveries from the two recurring fee collectors and from the one other recurring '
               f'source have no funding hop. July starts on 2026-07-07 and November covers {partial_month_note(ctx)} only.',
               f'In the 30-day window all {ctx.M("escrow_funded_exact_30d_n")} single-use deliveries are recorded as funded by the escrow for the exact amount, to the '
               f'yoctoNEAR ({ctx.M("escrow_funded_exact_30d_pct")}%). It tallies two columns of the per-delivery table over the window&rsquo;s single-use accounts, a set that the committed BigQuery output defines without them; '
               f'the funding scan that filled the columns is not in this repository.',
               f'The re-read against the chain on 2026-11-08 (<code>python3 -m pipeline.fetch_escrow verify --all</code>, output in '
               f'<code>data/raw/escrow/verify_all.json</code>): {ctx.M("escrow_recheck_rows_ok_n")} of {ctx.M("escrow_recheck_rows_n")} rows pass every check, the other '
               f'{ctx.M("escrow_recheck_failed_n")} differ in block height alone (one to three blocks off), and all {ctx.M("escrow_recheck_funding_hops_n")} funding '
               f'transfers pass, {ctx.M("escrow_recheck_window_funding_ok_n")} of them in the window. The command therefore exits with an error status on these data.',
               'The escrow is account <code>51e8f94d…7cbe</code>, <code>PRIVATE_TREASURY_ACCOUNT_ID</code> in NEAR&rsquo;s Confidential Intents docs, where it is called the Treasury.'),
        source=source_p(ctx, sql=("sql/buyback_withdraw_sources.sql",),
                        raw=("raw/escrow/deliveries.csv", "raw/escrow/verify_sample.json", "raw/escrow/verify_all.json", "raw/bq/buyback_withdraw_sources.json"),
                        code=("pipeline/compute.py", "pipeline/fetch_escrow.py"),
                        upstream=(f"intents.near native_withdraw deliveries to the three revenue wallets (BigQuery; FastNEAR samples before {traced_from})",)),
        query=query_details(ctx, sql=("sql/buyback_withdraw_sources.sql",), note=escrow_query_note(ctx)),
        data=data_details(tab))


def card_take(ctx: Ctx) -> str:
    m, Mt = ctx.m, ctx.Mt
    blocks = [f"b{i}" for i in (1, 2, 3)]
    labels = [block_label(m[f"take_{b}_window"]) for b in blocks]
    series = [
        {"cls": "s1", "name": "NEAR's explicit buyback fee, bp of 1Click volume", "key": "bb_explicit_bp"},
        {"cls": "s2", "name": "Partner fees, bp of 1Click volume", "key": "partner_bp"},
        {"cls": "sc", "name": "Captured ÷ DefiLlama volume, bp (other basis)", "key": "captured_bp"},
    ]
    title = "NEAR's take and partners' take in three 30-day blocks, basis points of volume"
    desc = ("Grouped columns from zero in basis points for three 30-day blocks. Explicit buyback fee: " +
            ", ".join(ctx.plain(f"take_{b}_bb_explicit_bp") for b in blocks) + ". Partner fees: " +
            ", ".join(ctx.plain(f"take_{b}_partner_bp") for b in blocks) + ". Captured revenue on DefiLlama's basis: " +
            ", ".join(ctx.plain(f"take_{b}_captured_bp") for b in blocks) + ".")

    def build(v: Variant) -> tuple[str, float]:
        cats = []
        for b, lab in zip(blocks, labels):
            cats.append({"label": lab, "vals": [m[f"take_{b}_{s['key']}"] for s in series],
                         "txts": [T(Mt(f"take_{b}_{s['key']}")) for s in series],
                         "tips": [lab + ": " + s["name"] + " " + ctx.plain("take_%s_%s" % (b, s["key"])) for s in series]})
        return vcol_panel(v, title="Basis points of volume (1 bp = 0.01%)", cats=cats, series=series, ymax=50,
                          yticks=[0, 10, 20, 30, 40, 50], h_plot=150 if not v.narrow else 130)

    fig = dual(ctx, "chart-take", title, desc, build)
    cols = [{"h": "Block", "num": False}]
    cols += [{"h": "Explicit buyback fee, bp"}, {"h": "Partner fees, bp"}, {"h": "Share of volume with a buyback fee entry, %"},
             {"h": "SwapKit share of volume, %"}, {"h": "Captured revenue ÷ reported volume (DefiLlama), bp"}, {"h": "1Click volume, USD million"}]
    rws = []
    for b, lab in zip(blocks, labels):
        rws.append({"k": b, "cells": [esc(f"{lab} ({m[f'take_{b}_window']})"), ctx.M(f"take_{b}_bb_explicit_bp"), ctx.M(f"take_{b}_partner_bp"),
                                      ctx.M(f"take_{b}_vol_with_bb_pct"), ctx.M(f"take_{b}_swapkit_vol_pct"), ctx.M(f"take_{b}_captured_bp"),
                                      ctx.M(f"take_{b}_oneclick_usd_m", 0)]})
    tab = table_html(cols, rws, caption="Plotted values and the context behind them")
    return card(
        cid="take", kind="exp",
        title=f'NEAR&rsquo;s explicit 1Click fee: up from {ctx.M("take_b1_bb_explicit_bp")} bp to {ctx.M("take_b3_bb_explicit_bp")} bp of volume',
        headline=(f'NEAR&rsquo;s explicit fee inside 1Click rose from {ctx.M("take_b1_bb_explicit_bp")} bp of volume ({esc(labels[0])}) to '
                  f'{ctx.M("take_b3_bb_explicit_bp")} bp ({esc(labels[2])}), mostly because more volume carries a buyback fee entry; partner '
                  f'fees were {ctx.M("take_b3_partner_bp")} bp in the last block.'),
        shows=('NEAR&rsquo;s explicit buyback fee, partner fees and, on a different basis, captured revenue, in basis points of volume, over three '
               '30-day blocks of 1Click swaps from the NEAR Intents Explorer API.'),
        notshows=('The period since the 2026-02-23 fee switch (this covers 90 days), and a like-for-like comparison of the captured-revenue bars, because '
                  'DefiLlama&rsquo;s volume series steps up on 2026-09-01.'),
        figure=fig,
        caption=('Windows: 2026-08-07 to 2026-11-04 in three 30-day blocks (UTC). Unit: basis points.'),
        capnote='The grey bars use a different denominator and are not like-for-like with the other two.',
        notes=(f'NEAR&rsquo;s explicit take rose mainly because more volume carries a buyback fee entry ({ctx.M("take_b1_vol_with_bb_pct")}% of volume in the first block, '
               f'{ctx.M("take_b3_vol_with_bb_pct")}% in the last); SwapKit&rsquo;s share barely moved: it stayed between {ctx.M("take_b1_swapkit_vol_pct")}% and '
               f'{ctx.M("take_b3_swapkit_vol_pct")}%.',
               f'1Click&rsquo;s share of DefiLlama&rsquo;s volume falls from {ctx.M("oneclick_share_of_llama_week_before_0901_pct")}% in the week before 2026-09-01 to '
               f'{ctx.M("oneclick_share_of_llama_week_after_0901_pct")}% in the week from that day, with no matching change in 1Click&rsquo;s own volume (both shares are on the halved basis used elsewhere on this page; on DefiLlama&rsquo;s reported basis they would be half as large). That is consistent with '
               f'DefiLlama counting more of Intents&rsquo; volume from that date, and a later sum of <code>intents.near</code> settlement shows it: from 2026-09-01 the series adds confidential-treasury flow at about one leg (exploratory, <code>docs/leg-count.md</code>). If so, the first block&rsquo;s {ctx.M("take_b1_captured_bp")} bp is overstated and the true '
               f'rise is, if anything, larger.',
               'Partner numbers rest on one key-gated source, the Explorer API.'),
        source=source_p(ctx, raw=("raw/explorer/daily.json", "raw/llama/volume_near-intents.json", "raw/llama/dailyRevenue_near-intents.json"),
                        code=("pipeline/fetch_explorer.py", "pipeline/fetch_keyless.py", "pipeline/compute.py"),
                        upstream=("NEAR Intents Explorer API (needs a partner key)", "DefiLlama dailyVolume and dailyRevenue for near-intents")),
        query=query_details(ctx, endpoints=(
            ("1Click swaps", "GET https://explorer.near-intents.org/api/v0/transactions?statuses=SUCCESS (per-day cursor pull)"),
            ("Fetcher", "python3 -m pipeline.fetch_explorer 2026-08-07 2026-11-04 (needs NEAR_INTENTS_EXPLORER_JWT; about 1h45m per 30 days)"),
            ("DefiLlama", "GET https://api.llama.fi/summary/dexs/near-intents?dataType=dailyVolume and GET https://api.llama.fi/summary/fees/near-intents?dataType=dailyRevenue"),
            ("Fetcher", "python3 -m pipeline.fetch_keyless (no key)"),
            ("Arithmetic", "pipeline/compute.py, function take_over_time()"))),
        data=data_details(tab))


def channel_label(ch: str) -> str:
    if ch == "(none)":
        return "No referrer (default fee)"
    if re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f-]+", ch):
        return f"Unnamed integrator ({ch[:8]}…)"
    return ch


def card_partners(ctx: Ctx) -> str:
    m, Mt = ctx.m, ctx.Mt
    chans = m["buyback_fee_by_channel"]
    sk_fee_share = m["swapkit_buyback_fees_usd"] / (m["explorer_appfees_to_buybacks_usd_k"] * 1000) * 100
    title = "Who pays NEAR's explicit fees, and what SwapKit's exit could cost"
    desc = (f"Panel A, bars from zero in percent: for SwapKit and the eight channels paying NEAR the most explicit buyback fees, the share of 1Click "
            f"volume against the share of NEAR's explicit buyback fees. SwapKit has {ctx.plain('swapkit_vol_share_pct')} percent of volume and "
            f"{ctx.plain('swapkit_buyback_fees_usd', 0)} dollars of explicit fees. Panel B: share of captured revenue lost if SwapKit left, "
            f"{ctx.plain('swapkit_exit_traceable_pct')} percent on traceable streams, {ctx.plain('swapkit_exit_ceiling_pct')} as a ceiling and "
            f"{ctx.plain('swapkit_exit_ceiling_all_escrow_pct')} as a wider ceiling.")

    def build(v: Variant) -> tuple[str, float]:
        rows = [{"label": "SwapKit (Ledger, Trust, Tangem and others)",
                 "bars": [bar(m["swapkit_vol_share_pct"], "s1", T(Mt("swapkit_vol_share_pct"), "%"),
                              f"SwapKit share of 1Click volume: {ctx.plain('swapkit_vol_share_pct')}%"),
                          bar(sk_fee_share, "s2", T("$", Mt("swapkit_buyback_fees_usd", 0), " of explicit fees"),
                              f"SwapKit explicit buyback fees: ${ctx.plain('swapkit_buyback_fees_usd', 0)}", lv=m["swapkit_buyback_fees_usd"])]}]
        for i, c in enumerate(chans):
            p = f"buyback_fee_by_channel.{i}"
            rows.append({"label": channel_label(c["channel"]),
                         "bars": [bar(c["vol_share_pct"], "s1", T(Mt(f"{p}.vol_share_pct"), "%"), f"{channel_label(c['channel'])}: {c['vol_share_pct']}% of volume"),
                                  bar(c["share_pct"], "s2", T(Mt(f"{p}.share_pct"), "%"), f"{channel_label(c['channel'])}: {c['share_pct']}% of explicit fees")]})
        a, ha = hbar_panel(v, title="Share of 1Click volume and of NEAR's explicit buyback fees, 30 days, %", tag="A",
                           rows=rows, vmax=50, ticks=[0, 10, 20, 30, 40, 50], tick_fmt=lambda t: f"{t:g}%",
                           legend_items=[("s1", "Share of 1Click volume", "rect"), ("s2", "Share of NEAR's explicit buyback fees", "rect")])
        b_rows = [
            {"label": "Traceable streams: explicit fees plus quote-improvement share, pro rata",
             "bars": [bar(m["swapkit_exit_traceable_pct"], "st2", T(Mt("swapkit_exit_traceable_pct"), "%"), f"Traceable: {ctx.plain('swapkit_exit_traceable_pct')}%")]},
            {"label": "Ceiling: also all escrow NEAR unshielded to the buyback wallet",
             "bars": [bar(m["swapkit_exit_ceiling_pct"], "st2", T(Mt("swapkit_exit_ceiling_pct"), "%"), f"Ceiling: {ctx.plain('swapkit_exit_ceiling_pct')}%")]},
            {"label": "Wider ceiling: also the escrow NEAR that reached fefundsadmin",
             "bars": [bar(m["swapkit_exit_ceiling_all_escrow_pct"], "st2", T(Mt("swapkit_exit_ceiling_all_escrow_pct"), "%"),
                          f"Wider ceiling: {ctx.plain('swapkit_exit_ceiling_all_escrow_pct')}%")]},
        ]
        b, hb = hbar_panel(v, title="If SwapKit stopped routing through 1Click: share of captured Intents revenue lost, %", tag="B", rows=b_rows,
                           vmax=100, ticks=[0, 25, 50, 75, 100], tick_fmt=lambda t: f"{t:g}%")
        return stack([(a, ha), (b, hb)])

    fig = dual(ctx, "chart-partners", title, desc, build)
    rows_t = [{"k": None, "cells": [esc("SwapKit"), ctx.M("swapkit_vol_share_pct"), f'${ctx.M("swapkit_buyback_fees_usd", 0)}']}]
    for i, c in enumerate(chans):
        p = f"buyback_fee_by_channel.{i}"
        rows_t.append({"k": None, "cells": [f'<code>{esc(c["channel"])}</code>', ctx.M(f"{p}.vol_share_pct"), ctx.M(f"{p}.share_pct")]})
    tab_a = table_html([{"h": "Channel", "num": False}, {"h": "Share of 1Click volume, %"}, {"h": "Share of NEAR's explicit buyback fees, %"}],
                       rows_t, caption="Panel A: plotted values (SwapKit's fee column is its explicit fees in USD)")
    tab_b = table_html(
        [{"h": "If SwapKit stopped routing through 1Click", "num": False}, {"h": "Share of captured Intents revenue lost, %"}],
        [{"k": None, "cells": [esc("Traceable streams"), ctx.M("swapkit_exit_traceable_pct")]},
         {"k": None, "cells": [esc("Ceiling (all escrow NEAR to the buyback wallet)"), ctx.M("swapkit_exit_ceiling_pct")]},
         {"k": None, "cells": [esc("Wider ceiling (also the escrow NEAR to fefundsadmin)"), ctx.M("swapkit_exit_ceiling_all_escrow_pct")]}],
        caption="Panel B: plotted values")
    figs = keyfigs([("SwapKit share of 1Click volume", f'{ctx.M("swapkit_vol_share_pct")}%'),
                    ("SwapKit share of all Intents volume, halved basis", f'{ctx.M("swapkit_share_of_intents_net_pct")}%'),
                    ("Volume HHI, SwapKit as one channel / split", f'{ctx.M("volume_channel_hhi_swapkit_merged", 3)} / {ctx.M("volume_channel_hhi", 3)}'),
                    ("Explicit buyback fee HHI", ctx.M("buyback_fee_hhi", 3))])
    return card(
        cid="partners", kind="exp",
        title=f'SwapKit: {ctx.M("swapkit_vol_share_pct")}% of 1Click volume, ${ctx.M("swapkit_buyback_fees_usd", 0)} in explicit fees to NEAR in 30 days',
        headline=(f'SwapKit routes {ctx.M("swapkit_vol_share_pct")}% of 1Click volume but paid NEAR ${ctx.M("swapkit_buyback_fees_usd", 0)} in explicit fees '
                  f'over 30 days; if it left, NEAR would lose about {ctx.M("swapkit_exit_traceable_pct")}% of captured revenue on the traceable '
                  f'streams. The ceiling is {ctx.M("swapkit_exit_ceiling_pct")}% if all the escrow NEAR delivered to the buyback wallet counts as SwapKit&rsquo;s, '
                  f'and {ctx.M("swapkit_exit_ceiling_all_escrow_pct")}% if the escrow NEAR reaching the front-end fund is counted too.'),
        shows=(f'For SwapKit and for the channels that pay NEAR the most explicit buyback fees, each channel&rsquo;s share of 1Click volume against its share of '
               f'NEAR&rsquo;s explicit buyback fees over the 30 days {window_text(ctx, 30)}, and what NEAR would lose if SwapKit stopped routing through 1Click.'),
        notshows=(f'Most of the NEAR the buyback wallet receives cannot be traced to any channel on chain, so that part of the exposure is unknown and may be above zero: '
                  f'the ceilings count every escrow unshield as if it came from SwapKit, which neither candidate reading of that stream supports, and the ledger '
                  f'cannot tell 0% from about {ctx.M("near_share_of_partner_fees_max_pct")}% for SwapKit ({ctx.M("near_share_of_partner_fees_max_tight_pct")}% on the tighter reading).'),
        figure=fig,
        caption=(f'Window: the 30 days {window_text(ctx, 30)} (UTC). Unit: percent.'),
        capnote='SwapKit&rsquo;s fee bar is to scale, just too short to see.',
        extra=figs,
        notes=(f'{ctx.M("buyback_fee_unreferred_share_pct")}% of NEAR&rsquo;s explicit fees come from swaps with no referral, meaning integrators on the default fee; '
               f'the top three channels account for {ctx.M("buyback_fee_top3_share_pct")}%.',
               f'The pro-rata assumption (collector B&rsquo;s quote improvement allocated to SwapKit by volume share) has support, since SwapKit swaps do pay collector B '
               f'({ctx.M("fee_ev_collector_b_swapkit_swaps_n")} of the {ctx.M("fee_ev_swapkit_swaps_n")} sampled), but its size is not measured. Fee mechanics come from '
               f'a sample of {ctx.M("fee_ev_swaps_n")} swaps.'),
        source=source_p(ctx, sql=("sql/buyback_withdraw_sources.sql", "sql/collector_inflows.sql", "sql/revenue_wallet_inflows.sql"),
                        raw=("raw/explorer/daily.json", "raw/bq/buyback_withdraw_sources.json", "raw/bq/collector_inflows.json",
                             "raw/bq/revenue_wallet_inflows.json", "raw/evidence/fee_sample_explorer.json", "raw/evidence/fee_sample_onchain.json"),
                        code=("pipeline/compute.py", "pipeline/fetch_explorer.py", "pipeline/fetch_fee_evidence.py"),
                        upstream=("NEAR Intents Explorer API (needs a partner key)",
                                  "BigQuery public dataset bigquery-public-data.crypto_near_mainnet_us, tables execution_outcomes and receipt_actions")),
        query=query_details(ctx, sql=("sql/buyback_withdraw_sources.sql", "sql/collector_inflows.sql", "sql/revenue_wallet_inflows.sql"),
                            endpoints=(("1Click swaps by channel", "GET https://explorer.near-intents.org/api/v0/transactions?statuses=SUCCESS (aggregated into data/raw/explorer/daily.json by pipeline/fetch_explorer.py)"),)),
        data=data_details(tab_a, tab_b))


def card_paid(ctx: Ctx) -> str:
    m, Mt = ctx.m, ctx.Mt
    if (m["fee_ev_partner_fees_nonzero_unmatched_escrow_n"] != m["fee_ev_partner_fees_nonzero_unmatched_n"]
            or m["fee_ev_partner_fees_nonzero_unmatched_n"] == 0):
        raise SystemExit("render: the note on the per-swap sample needs at least one unmatched partner fee, all in escrow-routed swaps; rewrite it in card_paid()")
    unmatched_word = "entry" if m["fee_ev_partner_fees_nonzero_unmatched_n"] == 1 else "entries"
    title = "Partner fees listed by 1Click against NEAR's revenue, and which way 1Click moves NEAR"
    desc = (f"Panel A, bars from zero in multiples of NEAR's entire captured revenue, with a reference line at 1: listed partner fees came to {ctx.plain('partners_kept_vs_near_rev_low_x')} times it "
            f"at the wide lower bound, {ctx.plain('partners_kept_vs_near_rev_low_tight_x')} at the tight lower bound and {ctx.plain('partners_kept_vs_near_rev_high_x')} at the upper. "
            f"Panel B: 1Click swaps into NEAR {ctx.plain('explorer_into_near_usd_m')} million dollars, out of NEAR {ctx.plain('explorer_out_of_near_usd_m')} million.")

    def build(v: Variant) -> tuple[str, float]:
        a_rows = [
            {"label": "Wide lower bound: all unexplained NEAR in the buyback wallet counted as partner fees passed on",
             "bars": [bar(m["partners_kept_vs_near_rev_low_x"], "s1", T(Mt("partners_kept_vs_near_rev_low_x"), "×"),
                          f"Wide lower bound: {ctx.plain('partners_kept_vs_near_rev_low_x')}×")]},
            {"label": "Tight lower bound: only escrow unshields counted as passed on",
             "bars": [bar(m["partners_kept_vs_near_rev_low_tight_x"], "sc", T(Mt("partners_kept_vs_near_rev_low_tight_x"), "×"),
                          f"Tight lower bound: {ctx.plain('partners_kept_vs_near_rev_low_tight_x')}×")]},
            {"label": "Upper: all listed partner fees, none passed on",
             "bars": [bar(m["partners_kept_vs_near_rev_high_x"], "sc", T(Mt("partners_kept_vs_near_rev_high_x"), "×"),
                          f"Upper: {ctx.plain('partners_kept_vs_near_rev_high_x')}×")]},
        ]
        a, ha = hbar_panel(v, title="Partners' listed fees ÷ NEAR's entire captured revenue", tag="A", rows=a_rows, vmax=2.5,
                           ticks=[0, 0.5, 1, 1.5, 2, 2.5], tick_fmt=lambda t: f"{t:g}×",
                           refs=[{"v": 1.0, "label": T("1×: equal to NEAR's whole captured revenue")}])
        b_rows = [
            {"label": "1Click swaps into NEAR", "bars": [bar(m["explorer_into_near_usd_m"], "st2", T("$", Mt("explorer_into_near_usd_m"), "M"),
                                                           f"Into NEAR: ${ctx.plain('explorer_into_near_usd_m')}M")]},
            {"label": "1Click swaps out of NEAR", "bars": [bar(m["explorer_out_of_near_usd_m"], "st2", T("$", Mt("explorer_out_of_near_usd_m"), "M"),
                                                              f"Out of NEAR: ${ctx.plain('explorer_out_of_near_usd_m')}M")]},
        ]
        b, hb = hbar_panel(v, title="1Click swaps with NEAR on one side, USD million, 30 days", tag="B", rows=b_rows, vmax=30,
                           ticks=[0, 10, 20, 30])
        return stack([(a, ha), (b, hb)])

    fig = dual(ctx, "chart-paid", title, desc, build)
    tab = table_html(
        [{"h": "Measure", "num": False}, {"h": "Value"}, {"h": "Unit", "num": False}],
        [{"k": None, "cells": [esc("Partner fees listed on 1Click swaps"), ctx.M("explorer_partner_fees_all_usd_k"), esc("USD thousand")]},
         {"k": None, "cells": [esc("NEAR's captured revenue, three revenue wallets"), ctx.M("revwallets_usd_k"), esc("USD thousand")]},
         {"k": None, "cells": [esc("Listed partner fees ÷ NEAR's revenue, wide lower bound"), ctx.M("partners_kept_vs_near_rev_low_x"), esc("×")]},
         {"k": None, "cells": [esc("Listed partner fees ÷ NEAR's revenue, tight lower bound"), ctx.M("partners_kept_vs_near_rev_low_tight_x"), esc("×")]},
         {"k": None, "cells": [esc("Listed partner fees ÷ NEAR's revenue, upper"), ctx.M("partners_kept_vs_near_rev_high_x"), esc("×")]},
         {"k": None, "cells": [esc("1Click swaps into NEAR"), ctx.M("explorer_into_near_usd_m"), esc("USD million")]},
         {"k": None, "cells": [esc("1Click swaps out of NEAR"), ctx.M("explorer_out_of_near_usd_m"), esc("USD million")]},
         {"k": None, "cells": [esc("Net NEAR sold through 1Click"), ctx.M("explorer_net_near_sold_usd_m"), esc("USD million")]}],
        caption="Plotted values")
    figs = keyfigs([("Partner fees listed", f'${ctx.M("explorer_partner_fees_all_usd_k")}K'),
                    ("NEAR's captured revenue", f'${ctx.M("revwallets_usd_k")}K'),
                    ("Net NEAR sold through 1Click", f'${ctx.M("explorer_net_near_sold_usd_m")}M'),
                    ("Share of 1Click volume with NEAR on one side", f'{ctx.M("explorer_near_side_swap_share_pct")}%')])
    return card(
        cid="paid", kind="exp",
        title=f'Listed partner fees: {ctx.M("partners_kept_vs_near_rev_floor_x")}× to {ctx.M("partners_kept_vs_near_rev_high_x")}× NEAR&rsquo;s captured revenue',
        headline=(f'Listed partner fees were {ctx.M("partners_kept_vs_near_rev_floor_x")}× to {ctx.M("partners_kept_vs_near_rev_high_x")}× NEAR&rsquo;s entire captured revenue ({ctx.M("partners_kept_vs_near_rev_low_x")}× is one reading, '
                  f'{ctx.M("partners_kept_vs_near_rev_low_tight_x")}× on the tighter one), and 1Click was a net route out of NEAR: ${ctx.M("explorer_out_of_near_usd_m")}M out against '
                  f'${ctx.M("explorer_into_near_usd_m")}M in over 30 days.'),
        shows=(f'The fees 1Click swaps listed for partners (${ctx.M("explorer_partner_fees_all_usd_k")}K) as a multiple of NEAR&rsquo;s entire captured Intents revenue '
               f'(${ctx.M("revwallets_usd_k")}K), between {ctx.M("partners_kept_vs_near_rev_low_x")}× and {ctx.M("partners_kept_vs_near_rev_high_x")}× on the readings charted, and 1Click swap volume '
               f'into and out of NEAR, over the 30 days {window_text(ctx, 30)}.'),
        notshows=(f'The other half of Intents: 1Click is {ctx.M("explorer_vs_llama_net_pct")}% of DefiLlama&rsquo;s volume on the halved basis ({ctx.M("legcount_oneclick_share_solver_lo_pct")}% to '
                  f'{ctx.M("legcount_oneclick_share_solver_hi_pct")}% on one-sided volume, taking confidential solver shields as one-sided confidential volume; exploratory), and near.com, direct solver flow '
                  f'and other integrations have a fee structure the Explorer API does not show, so we do not extrapolate.'),
        figure=fig,
        caption=(f'Window: the 30 days {window_text(ctx, 30)} (UTC). Blue: the bound the headline quotes.'),
        extra=figs,
        notes=(f'The wide reading counts all the NEAR in the buyback wallet that the explicit fee entries do not explain as partner fees passed on to NEAR: the listed '
               f'partner fees left after that are at least {ctx.M("partners_kept_vs_near_rev_low_x")}× NEAR&rsquo;s revenue, and at most {ctx.M("near_share_of_partner_fees_max_pct")}% of the fees on '
               f'partner swaps with no buyback fee entry reached NEAR. The tight reading counts only the escrow unshields, reading collector B&rsquo;s NEAR as quote improvement, a role that is inferred '
               f'and unproven: {ctx.M("partners_kept_vs_near_rev_low_tight_x")}× and {ctx.M("near_share_of_partner_fees_max_tight_pct")}%. Both leave out the escrow NEAR '
               f'that reached the front-end fund, where the ledger cannot exclude a partner settlement. If that NEAR (${ctx.M("revwallets_frontend_usd_k")}K) may be partner money too, the floor is '
               f'{ctx.M("partners_kept_vs_near_rev_floor_x")}× and NEAR&rsquo;s share of those fees at most {ctx.M("near_share_of_partner_fees_max_wide_pct")}% (exploratory; <code>docs/second-review.md</code>).',
               f'In the per-swap sample ({ctx.M("fee_ev_swaps_n")} swaps from {ctx.M("fee_ev_hours_with_swaps_n")} sampled hours) every non-zero partner fee entry was matched '
               f'on chain by a payment of about the listed amount to an account other than NEAR&rsquo;s two fee collectors, except {ctx.M("fee_ev_partner_fees_nonzero_unmatched_n")} unmatched {unmatched_word}, in a swap whose tokens went '
               f'into the Confidential Intents escrow, where the public chain shows no fee on that route. A further {ctx.M("fee_ev_swapkit_fees_zero_rate_n")} SwapKit entries '
               f'and {ctx.D("fee_ev_other_partner_fees_zero_rate_n+fee_ev_zodl_fees_zero_rate_n", 0)} others list a zero rate, so nothing is owed on them and no amount can '
               f'match. Who owns those receiving accounts is not shown, so the sample shows the listed amount leaving the swap in one piece; it does not show who keeps it. '
               f'So no split comes out of a listed fee in that sample; whatever 1Click charges on top, and whether it forwards any of it to NEAR, is not visible.',
               f'1Click swaps out of NEAR are not exchange deposits: H1b counts only labelled centralized-exchange accounts and does not see this non-custodial route. '
               f'Only {ctx.M("explorer_near_side_swap_share_pct")}% of 1Click volume has NEAR on one side.',
               'Partner numbers rest on one key-gated source, the Explorer API.'),
        source=source_p(ctx, sql=("sql/revenue_wallet_inflows.sql", "sql/revenue_wallet_wnear_inflows.sql"),
                        raw=("raw/explorer/daily.json", "raw/bq/revenue_wallet_inflows.json", "raw/bq/revenue_wallet_wnear_inflows.json",
                             "raw/llama/dailyRevenue_near-intents.json"),
                        code=("pipeline/compute.py", "pipeline/fetch_explorer.py"),
                        upstream=("NEAR Intents Explorer API (needs a partner key)",
                                  "BigQuery public dataset bigquery-public-data.crypto_near_mainnet_us, tables receipt_actions and ft_events")),
        query=query_details(ctx, sql=("sql/revenue_wallet_inflows.sql", "sql/revenue_wallet_wnear_inflows.sql"),
                            note="The wNEAR query returned zero rows, but it reads <code>ft_events</code>, which appears not to record <code>wrap.near</code> transfers, so that "
                                 f"zero is uninformative. The evidence that wNEAR inflows are negligible is the reconciliation: the native-only total is {ctx.M('revwallets_vs_llama_rev_pct')}% of DefiLlama&rsquo;s revenue."),
        data=data_details(tab))


def tick_every(n: int, step: int) -> list[int]:
    """Indices counted back from the last point, so the newest label is always present."""
    return [i for i in range(n) if (n - 1 - i) % step == 0]


def card_peers(ctx: Ctx) -> str:
    m, St = ctx.m, ctx.St
    rows = ctx.s["peer_share_monthly"]
    n = len(rows)
    last = rows[-1]["month"]
    peak = max(rows, key=lambda r: r["near-intents"])["month"]
    title = "NEAR Intents' share of the peer set's reported volume, by month"
    desc = (f"A line from zero to 100 percent over {n} months. The latest point, {last}, is "
            f"{ctx.series_value('peer_share_monthly.' + last + '.near-intents')} percent, covering part of the month. "
            f"A reference line marks 50 percent.")

    def build(v: Variant) -> tuple[str, float]:
        return line_panel(
            v, title="NEAR Intents' share of Intents + THORChain + Chainflip + Maya volume, %",
            xlabels=[r["month"] for r in rows], xtick_idx=tick_every(n, 6 if v.narrow else 3),
            series=[{"cls": "l1", "dot": "s1", "ys": [r["near-intents"] for r in rows],
                     "end": T(St(f"peer_share_monthly.{last}.near-intents"), "%")}],
            ymin=0, ymax=100, yticks=[0, 25, 50, 75, 100], tick_fmt=lambda t: f"{t:g}%", h_plot=130 if not v.narrow else 120,
            refs=[{"v": CONSTS["f4_min_pct"][0], "label": T(ctx.Kt("f4_min_pct"), "% (the F4 bar)")}], area_first=True,
            ynote=f"The last point covers {partial_month_note(ctx)} only.")

    fig = dual(ctx, "chart-peers", title, desc, build)
    cols = [{"h": "Month", "num": False, "c": "month"}] + [{"h": h, "c": k} for h, k in (
        ("NEAR Intents, %", "near-intents"), ("THORChain, %", "thorchain-dex"), ("Chainflip, %", "chainflip-amm"), ("Maya, %", "maya-protocol"))]
    tab = table_html(cols, [{"k": r["month"], "cells": [esc(r["month"])] + [fmt_value(r[k]) for k in ("near-intents", "thorchain-dex", "chainflip-amm", "maya-protocol")]}
                            for r in rows], caption="Monthly share of the peer set's reported volume", attrs='data-series="peer_share_monthly"')
    peers = table_html(
        [{"h": "Venue", "num": False}, {"h": "Volume, 30 days, USD billion"}, {"h": "Volume, 365 days, USD billion"}, {"h": "Share, 30 days, %"}],
        [{"k": None, "cells": [esc(p["venue"]), ctx.M(f"peers.{i}.vol_30d_b"), ctx.M(f"peers.{i}.vol_365d_b"), ctx.M(f"peers.{i}.share_30d_pct")]}
         for i, p in enumerate(m["peers"])], caption="Peer set, reported basis, to the as-of date")
    figs = keyfigs([("Intents share, 30 days", f'{ctx.M("intents_share_peerset_30d_pct")}%'),
                    ("Intents share, 365 days", f'{ctx.M("intents_share_peerset_365d_pct")}%'),
                    ("30 days, net (halved) basis", f'{ctx.M("intents_share_peerset_30d_net_pct")}%')])
    return card(
        cid="peers", kind="exp",
        title=f'Intents&rsquo; share of its peer set: {ctx.M("intents_share_peerset_30d_pct")}% over 30 days, {ctx.M("intents_share_peerset_365d_pct")}% over 365 days',
        headline=(f'NEAR Intents is {ctx.M("intents_share_peerset_30d_pct")}% of its cross-chain peer set by reported volume over 30 days and '
                  f'{ctx.M("intents_share_peerset_365d_pct")}% over 365 days.'),
        shows=(f'NEAR Intents&rsquo; share of the combined reported volume of Intents, THORChain, Chainflip and Maya (DefiLlama), by calendar month from '
               f'{esc(rows[0]["month"])} to {esc(last)}; the monthly peak was {ctx.S("peer_share_monthly." + peak + ".near-intents")}% in {esc(peak)}.'),
        notshows=(f'Volume is not the token: only {ctx.M("explorer_near_side_swap_share_pct")}% of 1Click volume has NEAR on one side, and a share of volume says '
                  f'nothing about revenue.'),
        figure=fig,
        caption=f'Window: {esc(rows[0]["month"])} to {esc(last)} (UTC), by calendar month. Unit: percent of reported volume.',
        extra=figs,
        notes=(f'Reported Intents volume counts both legs of public swaps (measured), plus, from 2026-09-01, confidential-treasury flow at about one leg (measured; what that flow represents is inferred), which on the solver pairs is swap volume counted at close to both legs; DefiLlama&rsquo;s adapter states no methodology, and this comes from a sum of <code>intents.near</code> settlement on five days and the solver pairs on three (exploratory, <code>docs/leg-count.md</code>, <code>docs/confidential-flow.md</code>). '
               f'On one-sided volume the 30-day share is {ctx.M("legcount_peer_share_solver_lo_pct")}% to {ctx.M("legcount_peer_share_solver_hi_pct")}%, '
               f'near the halved basis, {ctx.M("intents_share_peerset_30d_net_pct")}%. Only Intents is restated.',
               f'The last month covers {partial_month_note(ctx)} only. Forward test F4 asks whether the share over 2026-11-06 to 2026-11-13 is at least '
               f'{ctx.K("f4_min_pct")}% on the reported basis; this chart gives context for that test.'),
        source=source_p(ctx, raw=("raw/llama/volume_near-intents.json", "raw/llama/volume_thorchain-dex.json", "raw/llama/volume_chainflip-amm.json",
                                  "raw/llama/volume_maya-protocol.json"),
                        code=("pipeline/fetch_keyless.py", "pipeline/compute.py"),
                        upstream=("DefiLlama dailyVolume for near-intents, thorchain-dex, chainflip-amm and maya-protocol",)),
        query=query_details(ctx, endpoints=(
            ("Endpoint", "GET https://api.llama.fi/summary/dexs/<slug>?dataType=dailyVolume, slug in near-intents, thorchain-dex, chainflip-amm, maya-protocol"),
            ("Fetcher", "python3 -m pipeline.fetch_keyless (no key), function fetch_llama()"),
            ("Monthly shares", "pipeline/compute.py, series peer_share_monthly in data/series.json"))),
        data=data_details(tab, peers))


def card_revenue(ctx: Ctx) -> str:
    St = ctx.St
    rows = ctx.s["intents_monthly"]
    n = len(rows)
    last = rows[-1]["month"]
    peak = max(rows, key=lambda r: r["captured_bp"])["month"]
    peak_rev = max(rows, key=lambda r: r["rev_m"])["month"]
    peak_i = [r["month"] for r in rows].index(peak)
    title = "Captured Intents revenue and take rate, by month"
    desc = ("Panel A: columns from zero, captured revenue in USD million by month. Panel B: a line, captured revenue in basis points of DefiLlama's reported volume. "
            f"{peak} is the peak at {ctx.series_value('intents_monthly.' + peak + '.captured_bp')} basis points.")

    def build(v: Variant) -> tuple[str, float]:
        mx = max(r["rev_m"] for r in rows)
        ticks, top = nice_axis(mx, 4)
        cats = []
        for r in rows:
            lab_txt = T("$", St(f"intents_monthly.{r['month']}.rev_m"), "M") if r["month"] == peak_rev else None
            cats.append({"label": r["month"], "vals": [r["rev_m"]], "txts": [lab_txt],
                         "tips": [f"{r['month']}: ${fmt_value(r['rev_m'])}M captured revenue"]})
        a, ha = vcol_panel(v, title="Captured revenue per month, USD million", tag="A", cats=cats,
                           series=[{"cls": "s1", "name": "Captured revenue"}], ymax=top, yticks=ticks,
                           h_plot=96 if not v.narrow else 90, label_step=6 if v.narrow else 3, mr_min=58 if v.narrow else 76)
        bticks, btop = nice_axis(max(r["captured_bp"] for r in rows), 4)
        b, hb = line_panel(
            v, title="Captured revenue ÷ DefiLlama reported volume, basis points", tag="B",
            xlabels=[r["month"] for r in rows], xtick_idx=tick_every(n, 6 if v.narrow else 3),
            series=[{"cls": "l1", "dot": "s1", "ys": [r["captured_bp"] for r in rows], "end": T(St(f"intents_monthly.{last}.captured_bp"), " bp")}],
            ymin=0, ymax=btop, yticks=bticks, h_plot=96 if not v.narrow else 90,
            annots=[{"i": peak_i, "y": rows[peak_i]["captured_bp"], "txt": T(St(f"intents_monthly.{peak}.captured_bp"), " bp")}])
        return stack([(a, ha), (b, hb)])

    fig = dual(ctx, "chart-revenue", title, desc, build)
    cols = [{"h": "Month", "num": False, "c": "month"}, {"h": "Reported volume, USD billion", "c": "vol_b"},
            {"h": "Captured revenue, USD million", "c": "rev_m"}, {"h": "Captured take, bp", "c": "captured_bp"},
            {"h": "Gross fees take, bp", "c": "gross_bp"}]
    tab = table_html(cols, [{"k": r["month"], "cells": [esc(r["month"])] + [fmt_value(r[k]) for k in ("vol_b", "rev_m", "captured_bp", "gross_bp")]}
                            for r in rows], caption="Monthly values", attrs='data-series="intents_monthly"')
    figs = keyfigs([("Captured revenue, last 30 days", f'${ctx.M("intents_rev_30d_m")}M'),
                    ("Captured take, last 30 days", f'{ctx.M("take_captured_bp_30d")} bp'),
                    ("Captured share of gross fees, 30 days", f'{ctx.M("capture_share_30d_pct")}%')])
    return card(
        cid="revenue", kind="exp",
        title=f'Captured revenue: ${ctx.S("intents_monthly.2026-10.rev_m")}M in October, {ctx.S("intents_monthly.2026-10.captured_bp")} bp of volume',
        headline=(f'Captured Intents revenue was ${ctx.S("intents_monthly.2026-10.rev_m")}M in October 2026, '
                  f'{ctx.S("intents_monthly.2026-10.captured_bp")} bp of reported volume, up from '
                  f'{ctx.S("intents_monthly.2026-09.captured_bp")} bp in September.'),
        shows=('Monthly captured revenue (DefiLlama dailyRevenue, which counts NEAR delivered to NEAR&rsquo;s revenue wallets) and captured revenue as basis '
               'points of DefiLlama&rsquo;s reported Intents volume.'),
        notshows=('Fees accrued: DefiLlama&rsquo;s revenue is NEAR delivered to the wallets, so a month&rsquo;s figure depends on when deliveries land, and the chart '
                  'does not say which fee stream paid.'),
        figure=fig,
        caption=(f'Window: {esc(rows[0]["month"])} to {esc(last)} (UTC), by calendar month; the last month covers {partial_month_note(ctx)} only.'),
        extra=figs,
        notes=(f'Revenue before the 2026-02-23 fee switch counts as captured, as DefiLlama labels it. Reported volume was ${ctx.S("intents_monthly.2026-10.vol_b")}B in October. '
               f'The volume is what DefiLlama reports: both legs of public swaps, and from 2026-09-01 also the confidential flow, counted at close to both legs (exploratory, <code>docs/confidential-flow.md</code>; its adapter states no methodology). '
               f'So it steps up on 2026-09-01 (see the take chart above), and months before September are on the old definition. On one-sided volume the last 30 days&rsquo; captured take is '
               f'{ctx.M("legcount_take_captured_bp_solver_lo")} to {ctx.M("legcount_take_captured_bp_solver_hi")} bp.',
               f'The last month covers {partial_month_note(ctx)} only. Forward test F3 asks whether the captured take over 2026-11-06 to 2026-11-13 is below '
               f'{ctx.K("f3_max_bp")} bp; this chart gives context for that test.'),
        source=source_p(ctx, raw=("raw/llama/volume_near-intents.json", "raw/llama/dailyRevenue_near-intents.json", "raw/llama/fees_near-intents.json"),
                        code=("pipeline/fetch_keyless.py", "pipeline/compute.py"),
                        upstream=("DefiLlama dailyVolume, dailyRevenue and dailyFees for near-intents",)),
        query=query_details(ctx, endpoints=(
            ("Volume", "GET https://api.llama.fi/summary/dexs/near-intents?dataType=dailyVolume"),
            ("Revenue", "GET https://api.llama.fi/summary/fees/near-intents?dataType=dailyRevenue"),
            ("Gross fees", "GET https://api.llama.fi/summary/fees/near-intents?dataType=dailyFees"),
            ("Fetcher", "python3 -m pipeline.fetch_keyless (no key), function fetch_llama()"),
            ("Monthly sums", "pipeline/compute.py, series intents_monthly in data/series.json"))),
        data=data_details(tab))


def card_supply(ctx: Ctx) -> str:
    m, Mt, St = ctx.m, ctx.Mt, ctx.St
    sd = ctx.s["supply_daily"]
    by_date = {r["date"]: r["supply_m"] for r in sd}
    month_end: dict[str, str] = {}
    for r in sd:
        month_end[r["date"][:7]] = r["date"]
    me_dates = [month_end[k] for k in sorted(month_end)]
    asof = m["asof"]
    end = date.fromisoformat(asof)
    days90 = [date.fromordinal(end.toordinal() - i).isoformat() for i in range(89, -1, -1)]
    daily = []
    for d in days90:
        prev = date.fromordinal(date.fromisoformat(d).toordinal() - 1).isoformat()
        daily.append({"date": d, "supply_m": by_date[d], "change_k": round((by_date[d] - by_date[prev]) * 1000, 1)})
    title = "NEAR supply at each month end, and net issuance per day over the last 90 days"
    desc = (f"Panel A: a line of total supply at each month end, from {fmt_value(by_date[me_dates[0]])} million to "
            f"{fmt_value(by_date[me_dates[-1]])} million NEAR, on an axis that starts at 1,200 million. Panel B: columns from zero, daily net issuance in thousand NEAR over 90 days, "
            f"with a reference line at the 30-day mean, {ctx.plain('net_issuance_near_per_day_30d_k')} thousand.")

    def build(v: Variant) -> tuple[str, float]:
        lo, hi = 1200.0, 1320.0
        end_a = T(St(f"supply_daily.{me_dates[-1]}.supply_m"), "M")
        ml_ab = tw("1320", v.fs) + 12
        mr_ab = max(58 if v.narrow else 76, tw(pl(end_a), v.fs, True) + 14)
        a, ha = line_panel(
            v, title="Total supply at each month end, million NEAR", tag="A", xlabels=[d[:7] for d in me_dates],
            xtick_idx=tick_every(len(me_dates), 6 if v.narrow else 3),
            series=[{"cls": "l1", "dot": "s1", "ys": [by_date[d] for d in me_dates],
                     "end": T(St(f"supply_daily.{me_dates[-1]}.supply_m"), "M")}],
            ymin=lo, ymax=hi, yticks=[1200, 1240, 1280, 1320], h_plot=96 if not v.narrow else 90, area_first=True,
            ynote="The vertical axis starts at 1,200M.")
        cats = [{"label": date_short(r["date"]), "vals": [r["change_k"]], "txts": [None]} for r in daily]
        b, hb = vcol_panel(v, title="Net issuance per day, thousand NEAR", tag="B", cats=cats,
                           series=[{"cls": "s1", "name": "Net issuance"}], ymax=120, yticks=[0, 40, 80, 120],
                           h_plot=96 if not v.narrow else 90, label_step=30 if v.narrow else 15, ml_min=ml_ab, mr_min=mr_ab,
                           refs=[{"v": m["net_issuance_near_per_day_30d_k"], "label": T("30-day mean ", Mt("net_issuance_near_per_day_30d_k"), "K")}])
        return stack([(a, ha), (b, hb)])

    fig = dual(ctx, "chart-supply", title, desc, build)
    tab_a = table_html([{"h": "Month end", "num": False, "c": "date"}, {"h": "Total supply, million NEAR", "c": "supply_m"}],
                       [{"k": d, "cells": [esc(d), fmt_value(by_date[d])]} for d in me_dates],
                       caption="Panel A: plotted values", attrs='data-series="supply_daily"')
    tab_b = table_html([{"h": "Day", "num": False, "c": "date"}, {"h": "Total supply, million NEAR", "c": "supply_m"},
                        {"h": "Net issuance, thousand NEAR", "c": "d:change_k"}],
                       [{"k": r["date"], "cells": [esc(r["date"]), fmt_value(r["supply_m"]), fmt_value(r["change_k"], 1)]} for r in daily],
                       caption="Panel B: plotted values (each day's change from the day before)", attrs='data-series="supply_daily"')
    figs = keyfigs([("Net supply growth, 365 days", f'{ctx.M("net_supply_growth_365d_pct")}%'),
                    ("Net issuance, 30-day mean", f'{ctx.M("net_issuance_near_per_day_30d_k")}K NEAR a day'),
                    ("Gross issuance, 90 days", f'{ctx.M("h1a_gross_issuance_90d_m")}M NEAR'),
                    ("Burn, 90 days", f'{ctx.M("h1a_burn_90d_k")}K NEAR')])
    return card(
        cid="supply", kind="exp",
        title=f'Supply: up {ctx.M("net_supply_growth_365d_pct")}% in 365 days; net issuance {ctx.M("net_issuance_near_per_day_30d_k")}K NEAR a day',
        headline=(f'NEAR&rsquo;s supply grew {ctx.M("net_supply_growth_365d_pct")}% over 365 days; net issuance ran at {ctx.M("net_issuance_near_per_day_30d_k")}K NEAR a day '
                  f'over the last 30 days.'),
        shows=(f'Total NEAR supply at each month end and day-to-day net issuance (mint minus burn) over the 90 days {window_text(ctx, 90)}; net issuance is the quantity the ladder is measured against.'),
        notshows=('Who receives the issuance, or what changes after HSP-029, an issuance cut whose on-chain timelock ends on 2026-11-16 by our own sum of the contract&rsquo;s periods, after the deadline, and which also needs validator adoption.'),
        figure=fig,
        caption=f'Windows (UTC): month ends from {esc(me_dates[0])} (Panel A); the 90 days to {esc(me_dates[-1])} (Panel B).',
        capnote=f'Panel A&rsquo;s last point is the as-of date, {esc(me_dates[-1])}.',
        extra=figs,
        notes=(f'In those 90 days {ctx.M("h1a_gross_issuance_90d_m")}M NEAR were minted (read from {ctx.M("h1a_epochs_in_window")} epoch-boundary block headers), '
               f'{ctx.M("h1a_burn_90d_k")}K NEAR burned and the net supply change was {ctx.M("h1a_net_supply_change_90d_m")}M NEAR.',
               f'NEAR mints once per epoch, and a UTC day holds three or four epoch starts, so the daily bars come in two heights: the taller bars are the four-epoch days. '
               f'Daily values are differences between Nearblocks <code>total_supply</code> values that this repo keeps to the nearest thousand NEAR, so each carries up to about '
               f'a thousand NEAR of rounding. The ladder uses {ctx.M("net_issuance_near_per_day_window", 0)} NEAR a day from two archival reads, a slightly different '
               f'denominator from the {ctx.M("net_issuance_near_per_day_30d_k")}K here.',
               f'Forward test F2 asks whether the mean net increase over 2026-11-06 to 2026-11-13 is between {ctx.K("f2_lo")}K and {ctx.K("f2_hi")}K a day; this chart gives '
               f'context for that test.'),
        source=source_p(ctx, raw=("raw/nearblocks/charts.json", "raw/rpc/epoch_issuance.json"),
                        code=("pipeline/fetch_keyless.py", "pipeline/compute.py", "pipeline/h1a.py"),
                        upstream=("Nearblocks /v1/charts total_supply", "NEAR archival RPC epoch-boundary block headers (gross issuance)")),
        query=query_details(ctx, endpoints=(
            ("Endpoint", "GET https://api.nearblocks.io/v1/charts"),
            ("Fetcher", "python3 -m pipeline.fetch_keyless (no key), function fetch_nearblocks()"),
            ("Series", "pipeline/compute.py, series supply_daily in data/series.json"))),
        data=data_details(tab_a, tab_b))


USAGE_COUNTS = (("tx", "Transactions"), ("contracts", "Active contracts"), ("new_accounts", "New accounts"),
                ("active_accounts", "Active accounts"))   # the four daily counts the step table compares


def card_usage(ctx: Ctx) -> str:
    m, Mt, M, St = ctx.m, ctx.Mt, ctx.M, ctx.St
    rows = ctx.s["l1_daily"]
    n = len(rows)
    dates = [r["date"] for r in rows]
    step, ref, asof = m["l1_step_date"], m["l1_step_ref_date"], m["asof"]
    if dates[-1] != asof or step not in dates:
        raise SystemExit("render: series l1_daily does not end at the as-of date or does not contain the step day; run `make reproduce`")
    si = dates.index(step)
    first, last = dates[0], dates[-1]
    title = "Daily transactions and daily active accounts on NEAR, from Nearblocks"
    desc = (f"Panel A: a line of daily transactions in thousand, on an axis from zero, over the {n} days from {first} to {last}. It stands at "
            f"{ctx.plain('l1_step_tx_before_k')} thousand on {ref} and {ctx.plain('l1_step_tx_after_k')} thousand on {step}, where a dashed vertical "
            f"line marks the largest one-day fall in the 365 days to {asof}, and at {ctx.series_value(f'l1_daily.{last}.tx_k')} thousand on {last}. "
            f"Panel B: a line of daily active accounts in thousand over the same days, with the same dashed line. It stands at "
            f"{ctx.plain('l1_step_active_accounts_before_k')} thousand on {ref}, {ctx.plain('l1_step_active_accounts_after_k')} thousand on {step} and "
            f"{ctx.series_value(f'l1_daily.{last}.active_accounts_k')} thousand on {last}.")
    labels = [f"{MONTHS[int(d[5:7]) - 1]} {d[:4]}" for d in dates]

    def build(v: Variant) -> tuple[str, float]:
        months = (4, 10) if v.narrow else (1, 4, 7, 10)
        ticks_x = [i for i, d in enumerate(dates) if d[8:] == "01" and int(d[5:7]) in months]
        panels = []
        ml_ab = max(tw(f"{t:,.0f}", v.fs) for key in ("tx_k", "active_accounts_k") for t in nice_axis(max(r[key] for r in rows), 5)[0]) + 12
        for key, name, tag in (("tx_k", "Transactions per day, thousand", "A"),
                               ("active_accounts_k", "Active accounts per day, thousand", "B")):
            ys = [r[key] for r in rows]
            yt, top = nice_axis(max(ys), 5)
            panels.append(line_panel(
                v, title=name, tag=tag, xlabels=labels, xtick_idx=ticks_x,
                series=[{"cls": "l1", "dot": "s1", "ys": ys, "end": T(St(f"l1_daily.{last}.{key}"), "K")}],
                ymin=0, ymax=top, yticks=yt, tick_fmt=lambda t: f"{t:,.0f}", h_plot=96 if v.narrow else 104,
                vmarks=[{"i": si, "date": step, "label": T("step ", Mt("l1_step_date"))}], ml_min=ml_ab))
        return stack(panels)

    fig = dual(ctx, "chart-usage", title, desc, build)

    step_rows = []
    for tag, label in USAGE_COUNTS:
        b, a = f"l1_step_{tag}_before_k", f"l1_step_{tag}_after_k"
        step_rows.append({"k": None, "cells": [esc(label), M(b), M(a), ctx.D(f"({a}/{b}-1)*100", 0)]})
    tab_step = table_html(
        [{"h": "Daily count", "num": False}, {"h": f"On {ref}, thousand"}, {"h": f"On {step}, thousand"},
         {"h": f"Change from {ref} to {step}, %"}],
        step_rows, caption="The step: four daily counts on the two days (the change is computed from the two values shown)")
    tab_change = table_html(
        [{"h": "Daily count", "num": False}, {"h": "Average of the latest 30 days, thousand a day"},
         {"h": "Change on the same 30 days a year earlier, %"}, {"h": f"Change on the 30 days that start on {step}, %"}],
        [{"k": None, "cells": [esc("Transactions"), M("tx_per_day_30d_k"), M("tx_per_day_30d_yoy_pct"), M("tx_per_day_since_step_pct")]},
         {"k": None, "cells": [esc("Active accounts"), M("active_accounts_30d_k"), M("active_accounts_30d_yoy_pct"), M("active_accounts_since_step_pct")]}],
        caption="Year on year, and since the step")
    tab_daily = table_html(
        [{"h": "Day", "num": False, "c": "date"}, {"h": "Transactions per day, thousand", "c": "tx_k"},
         {"h": "Active accounts per day, thousand", "c": "active_accounts_k"}],
        [{"k": r["date"], "cells": [esc(r["date"]), fmt_value(r["tx_k"], 1), fmt_value(r["active_accounts_k"], 1)]} for r in rows],
        caption=f"Panels A and B: plotted values, {first} to {last}", attrs='data-series="l1_daily"')

    figs = keyfigs([(label, f'{M(f"l1_step_{tag}_before_k")} → {M(f"l1_step_{tag}_after_k")}') for tag, label in USAGE_COUNTS])
    lead = f'<p class="note">Four daily counts, in thousands, on <span class="nb">{esc(ref)}</span> and then on <span class="nb">{esc(step)}</span>, the day of the fall:</p>'
    return card(
        cid="usage", kind="exp",
        title=(f'Daily active accounts: {M("active_accounts_30d_k")}K, {M("active_accounts_30d_yoy_pct")}% on a year earlier; '
               f'{M("usage_bq_tg_share_of_signer_drop_pct")}% of the fall is one wallet app&rsquo;s Telegram accounts'),
        headline=(f'Daily active accounts averaged {M("active_accounts_30d_k")}K over the 30 days to {M("asof")}, {M("active_accounts_30d_yoy_pct")}% on the same 30 days '
                  f'a year earlier; daily transactions are {M("tx_per_day_30d_yoy_pct")}% on a year earlier, but most of that is one step on {M("l1_step_date")}, '
                  f'a single-day drop.'),
        shows=(f'Nearblocks&rsquo; counts of transactions (Panel A) and of active accounts (Panel B) on each day from {esc(first)} to {esc(last)}, in thousands. '
               f'A dashed line marks {esc(step)}, the largest one-day fall in daily transactions in the 365 days to {esc(asof)}. The headline averages are '
               f'the 30 days {window_text(ctx, 30)} against the same 30 days a year earlier.'),
        notshows=('Why the step happened. BigQuery (exploratory, <code>docs/usage.md</code>) reproduces both series exactly and shows who stopped: '
                  f'Sweat Economy&rsquo;s signers, {M("usage_bq_step_kaiching_share_pct")}% of the step. Why they stopped is not in the data. '
                  'That active accounts are people: this repository applies no sybil or bot filter to the counts. '
                  'Contract usage: the Nearblocks active-contract count falls by an order of magnitude on the same days (see the table), so it is not used; '
                  f'the BigQuery count of contracts called has a median of {M("usage_bq_contracts_called_median_30d_n")} a day, against '
                  f'{M("usage_bq_contracts_called_median_yago_n")} a year earlier.'),
        figure=fig,
        caption=(f'Window: {esc(first)} to {esc(last)} (UTC), one point per day. Unit: thousand a day. The dashed line is {esc(step)}.'),
        capnote='The lines are single days and the headline figures 30-day averages, so their last points differ.',
        extra=f'{lead}{figs}',
        notes=(f'The transactions series falls in one step, from {M("l1_step_tx_before_k")}K to {M("l1_step_tx_after_k")}K between {esc(ref)} and {esc(step)}. '
               f'Active contracts and new accounts fall with it, but active accounts barely move ({M("l1_step_active_accounts_before_k")}K to '
               f'{M("l1_step_active_accounts_after_k")}K): they fall gradually, with spikes this card does not explain, and show no single step. Since the step, the change is {M("tx_per_day_since_step_pct")}% for '
               f'daily transactions and {M("active_accounts_since_step_pct")}% for daily active accounts (the latest 30 days against the 30 days that start on {esc(step)}).',
               'Both counts are lower than a year ago, but they fall differently. This card is not a pre-registered test, and it feeds '
               'neither the rating rule nor any pre-registered test.',
               f'The track brief names daily active accounts, transaction counts and contract usage. The BigQuery queries in <code>sql/usage_*.sql</code> (exploratory, '
               f'run on 2026-11-13) reproduce the two Nearblocks series on all {M("usage_bq_nearblocks_match_days_n")} days they cover, put '
               f'{M("usage_bq_tg_share_of_signer_drop_pct")}% of the fall in active accounts in HOT Wallet&rsquo;s <code>.tg</code> accounts, and count contracts called; '
               '<code>docs/usage.md</code> has the details.'),
        source=source_p(ctx, raw=("raw/nearblocks/charts.json",), code=("pipeline/fetch_keyless.py", "pipeline/compute.py"),
                        upstream=("Nearblocks /v1/charts daily transactions, active accounts, active contracts and new accounts",)),
        query=query_details(ctx, sql=("sql/usage_daily.sql", "sql/usage_receipts.sql", "sql/usage_signer_groups.sql"), note=(
            'The chart is drawn from the Nearblocks series named at the end of this block. The three BigQuery queries are the ones the track brief '
            'asks for (daily active accounts, transaction counts, contract usage). They were run on 2026-11-13, after the freeze (exploratory), '
            'and reproduce both Nearblocks series; <code>docs/usage.md</code> has what they found.'), endpoints=(
            ("Endpoint", "GET https://api.nearblocks.io/v1/charts"),
            ("Fetcher", "python3 -m pipeline.fetch_keyless (no key), function fetch_nearblocks()"),
            ("Step and series", "pipeline/compute.py, function l1_usage(): the step day, the four counts on the two days, the change since the step, and series l1_daily in data/series.json"),
            ("Averages", "pipeline/compute.py, function build(): the 30-day averages and the year-on-year changes"))),
        data=data_details(tab_step, tab_change, tab_daily))


# ------------------------------------------------------------------ page
# ------------------------------------------------------------------ forward view (exploratory, 2026-11-13; pipeline/model.py)
FAN_TICKS = (1.0, 10.0, 100.0, 1000.0)


def fan_panel(v: Variant, *, title: object, rows: list[dict], refs: list[dict], end: Txt, hist: list[dict], asof: str,
              tag: str = "") -> tuple[str, float]:
    """Measured coverage, then percentile bands on a log axis (1% to 1,000%): p10-p90 light, p25-p75 darker, the median as a line.

    rows: the fwd_fan series ({"k", "date", "p10".."p90"}), k in model months from the as-of date. hist: the cov_hist series
    ({"date", "cov_pct"}, P3's quantity, priced daily), drawn before the as-of date. Values outside the axis are drawn at its edge.
    The panel is one <g class="panel" data-kind="fan" data-scale="log10">; the median's last dot and the last measured dot carry data-v."""
    fs = v.fs
    lo, hi = FAN_TICKS[0], FAN_TICKS[-1]
    ml = tw("1,000%", fs) + 12
    mr = 58 if v.narrow else 96
    pw = v.w - ml - mr
    h_plot = 150 if v.narrow else 190
    tb, th = title_block(v, title, tag)
    out: list[str] = [tb]
    lg, lh = legend(v, [("lk", "Measured (P3's quantity)", "line"), ("band2", "Middle half of paths", "box"),
                        ("band", "Eight paths in ten", "box"), ("l1", "Median path", "line")], th + 4 + fs)
    out.append(lg)
    top = th + 4 + lh + fs + 10
    base = top + h_plot
    a0 = date.fromisoformat(asof)
    month = 365.25 / 12
    hk = [((date.fromisoformat(h["date"]) - a0).days / month, h["cov_pct"]) for h in hist]
    kmin, kmax = min([k for k, _ in hk] + [0.0]), float(rows[-1]["k"])

    def sy(val: float) -> float:
        c = min(max(val, lo), hi)
        return base - h_plot * (math.log10(c) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))

    def sx(k: float) -> float:
        return ml + pw * (k - kmin) / (kmax - kmin)

    for t in FAN_TICKS:
        out.append(hline(ml, ml + pw, sy(t), "axis" if t == lo else "grid"))
        out.append(text(ml - 6, sy(t) + fs * 0.35, f"{t:,.0f}%", cls="tk", anchor="end", fs=fs))
    for r in rows:
        if r["k"] % (24 if v.narrow else 12) == 0:
            lx, an = clamp_anchor(sx(r["k"]), tw(r["date"][:7], fs), v.w)
            out.append(text(lx, base + fs + 7, esc(r["date"][:7]), cls="tk", anchor=an, fs=fs))
    out.append(vline(sx(0), top, base, "vmark"))
    for a, b, cls in (("p10", "p90", "band"), ("p25", "p75", "band2")):
        up = [f"{n1(sx(r['k']))},{n1(sy(r[b]))}" for r in rows]
        dn = [f"{n1(sx(r['k']))},{n1(sy(r[a]))}" for r in reversed(rows)]
        out.append(f'<path class="{cls}" d="M{"L".join(up + dn)}z" />')
    for rf in refs:
        yy = sy(rf["v"])
        out.append(hline(ml, ml + pw, yy, "refline", f' data-v="{dv(rf["v"])}"'))
        # a plain patch behind the label, so the dashed "today" marker does not run through its letters
        out.append(f'<rect class="lblbg" x="{n1(ml + 2)}" y="{n1(yy - 4 - fs)}" width="{n1(len(pl(rf["label"])) * fs * 0.47 + 6)}" height="{n1(fs + 2)}" />')
        out.append(text(ml + 4, yy - 5, mk(rf["label"]), cls="rl", fs=fs))
    if hk:
        out.append(f'<path class="ln lk" d="M{"L".join(f"{n1(sx(k))},{n1(sy(c))}" for k, c in hk)}" />')
        out.append(f'<circle class="sk ring" data-v="{dv(hk[-1][1])}" cx="{n1(sx(hk[-1][0]))}" cy="{n1(sy(hk[-1][1]))}" r="4" />')
    median = "L".join(f'{n1(sx(r["k"]))},{n1(sy(r["p50"]))}' for r in rows)   # built first: before Python 3.12 an f-string cannot reuse its own quote inside {}
    out.append(f'<path class="ln l1" d="M{median}" />')
    last = rows[-1]
    out.append(f'<circle class="s1 ring" data-v="{dv(last["p50"])}" cx="{n1(sx(last["k"]))}" cy="{n1(sy(last["p50"]))}" r="4" />')
    out.append(text(sx(last["k"]) + 9, sy(last["p50"]) + fs * 0.35, mk(end), cls="val", fs=fs))
    if not v.narrow:
        out.append(text(sx(last["k"]) + 9, sy(last["p90"]) + fs * 0.35, f'p90 {fmt_value(last["p90"], 0)}%', cls="tk", fs=fs - 0.5))
        out.append(text(sx(last["k"]) + 9, sy(last["p10"]) + fs * 0.35, f'p10 {fmt_value(last["p10"], 1)}%', cls="tk", fs=fs - 0.5))
    out.append(text(sx(0) + 5, top + fs, "today", cls="tk", fs=fs - 0.5))
    panel = (f'<g class="panel" data-kind="fan" data-scale="log10" data-lo="{dv(lo)}" data-hi="{dv(hi)}" data-base="{n1(base)}" '
             f'data-ph="{n1(h_plot)}" data-x0="{n1(ml)}" data-pw="{n1(pw)}">{"".join(out)}</g>')
    return panel, base + fs + 16


def card_fwdcov(ctx: Ctx) -> str:
    m, M, Mt = ctx.m, ctx.M, ctx.Mt
    fan = ctx.s["fwd_fan"]
    title = "Projected coverage of NEAR's dilution by captured Intents revenue, 2026 to 2031, and the chance of reaching set lines"
    desc = (f"Panel A: on a logarithmic axis, shaded percentile bands of coverage over {ctx.plain('fwd_paths_n')} simulated paths, "
            f"starting at {ctx.plain('fwd_coverage_now_pct')}% and ending with a median of {ctx.plain('fwd_cov_2031_p50_pct')}% on {m['fwd_target_date']}; "
            f"reference lines at {ctx.plain('fwd_full_line_pct')}% and {ctx.plain('fwd_p3_line_pct')}%. Panel B: bars from zero, the share of paths that reach each line.")

    def P(key: str) -> Txt:
        return T(Mt(key), "%")

    def build(v: Variant) -> tuple[str, float]:
        a, ha = fan_panel(v, tag="A", end=T(Mt("fwd_cov_2031_p50_pct"), "%"), hist=ctx.s["cov_hist"], asof=m["asof"], title="Coverage: 90-day captured revenue ÷ USD value of net new NEAR (log axis)", rows=fan,
                          refs=[{"v": m["fwd_full_line_pct"], "label": T(Mt("fwd_full_line_pct"), "%: revenue covers all dilution")},
                                {"v": m["fwd_p3_line_pct"], "label": T(Mt("fwd_p3_line_pct"), "%: P3's line")}])
        rows = [
            {"label": "Reaches P3's line by 2027-11-04: model, and P3 as frozen", "bars": [
                bar(m["fwd_p_cov_ge25_2027_pct"], "s1", P("fwd_p_cov_ge25_2027_pct"), "model"),
                bar(m["fwd_p3_frozen_prob_pct"], "sc", P("fwd_p3_frozen_prob_pct"), "P3, frozen in PREREG.md")]},
            {"label": "Covers all dilution by 2027-11", "bars": [bar(m["fwd_p_cov_ge100_2027_pct"], "s1", P("fwd_p_cov_ge100_2027_pct"))]},
            {"label": "Covers all dilution by 2028-11", "bars": [bar(m["fwd_p_cov_ge100_2028_pct"], "s1", P("fwd_p_cov_ge100_2028_pct"))]},
            {"label": "Covers all dilution by 2031-11-04 (the rating rule's date)", "bars": [bar(m["fwd_p_cov_ge100_2031_pct"], "s1", P("fwd_p_cov_ge100_2031_pct"))]},
            {"label": "Same, without HSP-029's cut", "bars": [bar(m["fwd_p_cov_ge100_2031_no_hsp029_pct"], "s2", P("fwd_p_cov_ge100_2031_no_hsp029_pct"))]},
            {"label": "Same, at half today's take rate", "bars": [bar(m["fwd_p_cov_ge100_2031_take_x0_5_pct"], "s2", P("fwd_p_cov_ge100_2031_take_x0_5_pct"))]},
            {"label": "Same, at twice today's take rate", "bars": [bar(m["fwd_p_cov_ge100_2031_take_x2_0_pct"], "s2", P("fwd_p_cov_ge100_2031_take_x2_0_pct"))]},
            {"label": "Same, if NEAR's price keeps its last-year trend", "bars": [bar(m["fwd_p_cov_ge100_2031_price_drift_pct"], "s2", P("fwd_p_cov_ge100_2031_price_drift_pct"))]},
            {"label": "Same, without the month that spans DefiLlama's counting change", "bars": [bar(m["fwd_exsep_p_cov_ge100_2031_pct"], "s2", P("fwd_exsep_p_cov_ge100_2031_pct"))]},
        ]
        b, hb = hbar_panel(v, title="Share of simulated paths that reach the line, %", tag="B", rows=rows, vmax=100,
                           ticks=[0, 25, 50, 75, 100],
                           legend_items=[("s1", "Main run", "box"), ("s2", "Sensitivity", "box"), ("sc", "Frozen probability (PREREG.md)", "box")])
        return stack([(a, ha), (b, hb)])

    fig = dual(ctx, "chart-fwdcov", title, desc, build)
    tab = table_html([{"h": "Month", "num": False, "c": "date"}] + [{"h": f"{q}th pct, %", "c": f"p{q}"} for q in (10, 25, 50, 75, 90)],
                     [{"k": r["date"], "cells": [esc(r["date"])] + [fmt_value(r[f"p{q}"], 2) for q in (10, 25, 50, 75, 90)]}
                      for r in fan if r["k"] % 3 == 0],
                     caption="Panel A: plotted percentiles, every third model month", attrs='data-series="fwd_fan"')
    figs = keyfigs([("Coverage today", f'{M("fwd_coverage_now_pct")}%'), ("Median, 2031-11-04", f'{M("fwd_cov_2031_p50_pct")}%'),
                    ("All dilution covered by 2031", f'{M("fwd_p_cov_ge100_2031_pct")}% of paths'),
                    ("Take rate held at", f'{M("fwd_take_bp")} bp')])
    return card(
        cid="fwdcov", kind="exp",
        title=(f'Monte Carlo: {M("fwd_p_cov_ge100_2031_pct")}% of paths pay for all dilution by 2031, {M("fwd_exsep_p_cov_ge100_2031_pct")}% without one month'),
        headline=(f'Captured Intents revenue covers {M("fwd_coverage_now_pct")}% of the USD value of NEAR&rsquo;s net new supply today. Over '
                  f'{M("fwd_paths_n")} paths that replay the volume and price changes of {M("fwd_boot_months_n")} months of data (price drift removed), the median reaches '
                  f'{M("fwd_cov_2027_p50_pct")}% by 2027-11, {M("fwd_cov_2028_p50_pct")}% by 2028-11 and {M("fwd_cov_2031_p50_pct")}% by 2031-11-04, and '
                  f'{M("fwd_p_cov_ge100_2031_pct")}% of paths cover all of it by then ({M("fwd_p_cov_ge100_2031_no_hsp029_pct")}% without HSP-029). If the price '
                  f'keeps its last-year trend, that falls to {M("fwd_p_cov_ge100_2031_price_drift_pct")}%; without the 2026-08 to 2026-09 month, which spans DefiLlama&rsquo;s '
                  f'change in what it counts, to {M("fwd_exsep_p_cov_ge100_2031_pct")}%. The bands are as wide as the data make them, so the thesis does not rest on these '
                  'probabilities.'),
        shows=(f'The frozen rating rule&rsquo;s question (does captured revenue reach the USD value of net new supply by 2031-11-04?) with a distribution in place of '
               f'one price and one growth rate: {M("fwd_paths_n")} paths, each month drawing one of the {M("fwd_boot_months_n")} monthly changes in Intents volume and NEAR&rsquo;s '
               f'mean price ({esc(m["fwd_boot_first"])} to {esc(m["fwd_boot_last"])}) together, against the rule&rsquo;s own supply path.'),
        notshows=('A forecast of NEAR&rsquo;s price or a valuation. Eleven months of data cannot pin a five-year trend: the bands are as wide as the data make them, '
                  'the take rate is held where it is, and no new fee stream, partner change or regime is modelled.'),
        figure=fig,
        caption=(f'Model: <code>pipeline/model.py</code>, a fixed seed, {M("fwd_months_n")} model months from {esc(m["asof"])}. Unit: percent. Panel A&rsquo;s axis is logarithmic.'),
        capnote='In Panel A, values below the axis floor are drawn at the floor. The model feeds nothing the rating rule computes.',
        extra=figs,
        notes=(f'The volume drift comes from one month: the 2026-08 to 2026-09 change spans DefiLlama&rsquo;s 2026-09-01 change in what it counts as Intents volume. '
               f'Without that month volume changed by {M("fwd_exsep_vol_monthly_mean_pct")}% a month, the 2031 median is {M("fwd_exsep_cov_2031_p50_pct")}% and '
               f'{M("fwd_exsep_p_cov_ge100_2031_pct")}% of paths cover all dilution. The forecasts M1 to M4 were dated with the month in and are scored as dated; the '
               'thesis does not rest on them (PREREG-ADDENDUM.md, 2026-11-14 entries).',
               f'Volume and price move together in the data: the correlation of their monthly log changes is {M("fwd_vol_price_corr")}, so each month&rsquo;s two changes are drawn together.',
               f'The price drift is removed because NEAR&rsquo;s mean price rose {M("fwd_price_monthly_mean_pct")}% a month on average over those months; replaying that for five '
               f'years would assume the trend continues. With it, the 2031 median is {M("fwd_cov_2031_p50_price_drift_pct")}%: a higher price means each dollar of revenue '
               'buys back less NEAR.',
               f'Volume keeps its sample drift, {M("fwd_vol_monthly_mean_pct")}% a month. The take rate is captured revenue ÷ volume over the last 90 days, {M("fwd_take_bp")} bp, '
               f'held fixed; coverage moves in proportion to it.',
               f'P3 (frozen in PREREG.md with probability {M("fwd_p3_frozen_prob_pct")}%) asks whether coverage is at least {M("fwd_p3_line_pct")}% on 2027-11-04. The model, built after the freeze, gives '
               f'{M("fwd_p_cov_ge25_2027_pct")}%; P3 is scored on the data alone.',
               f'Coverage today here is computed in USD at one price, as the rating rule does; the ladder&rsquo;s {M("ladder_all_wallets_pct_of_issuance", 2)}%-of-issuance figure counts NEAR as it arrived, '
               'so the two differ slightly.'),
        source=source_p(ctx, raw=("raw/llama/dailyRevenue_near-intents.json", "raw/llama/volume_near-intents.json",
                                  "raw/coingecko/near_market_chart_365d.json", "raw/rpc/epoch_issuance.json", "raw/rpc/rating_assumptions.json"),
                        code=("pipeline/model.py", "pipeline/h1a.py", "pipeline/compute.py")),
        query=query_details(ctx, endpoints=(("Model", "python3 -m pipeline.compute (calls pipeline.model.forward); offline, standard library, fixed seed"),
                                            ("Series", "fwd_fan in data/series.json"))),
        data=data_details(tab))


def card_fwdsupply(ctx: Ctx) -> str:
    m, M, Mt = ctx.m, ctx.M, ctx.Mt
    sup = ctx.s["fwd_supply"]
    title = "Projected NEAR supply to 2031-11-04, with and without HSP-029's issuance cut"
    desc = (f"Two lines on an axis that does not start at zero: with HSP-029, supply reaches {ctx.plain('fwd_supply_2031_m')} million; "
            f"without it, {ctx.plain('fwd_supply_2031_no_hsp029_m')} million.")

    def build(v: Variant) -> tuple[str, float]:
        return line_panel(
            v, title="Total supply, million NEAR", xlabels=[r["date"][:7] for r in sup],
            xtick_idx=[i for i, r in enumerate(sup) if r["k"] % (24 if v.narrow else 12) == 0],
            series=[{"cls": "l1", "dot": "s1", "ys": [r["hsp029_m"] for r in sup], "end": T(Mt("fwd_supply_2031_m"), "M"), "name": "With HSP-029 (as G_req assumes)"},
                    {"cls": "l2", "dot": "s2", "ys": [r["no_hsp029_m"] for r in sup], "end": T(Mt("fwd_supply_2031_no_hsp029_m"), "M"), "name": "Without HSP-029"}],
            ymin=1300.0, ymax=1500.0, yticks=[1300, 1350, 1400, 1450, 1500], h_plot=120 if v.narrow else 150,
            ynote="The vertical axis starts at 1,300M.")

    fig = dual(ctx, "chart-fwdsupply", title, desc, build)
    tab = table_html([{"h": "Date", "num": False, "c": "date"}, {"h": "With HSP-029, million NEAR", "c": "hsp029_m"},
                      {"h": "Without HSP-029, million NEAR", "c": "no_hsp029_m"}],
                     [{"k": r["date"], "cells": [esc(r["date"]), fmt_value(r["hsp029_m"], 2), fmt_value(r["no_hsp029_m"], 2)]} for r in sup],
                     caption="Plotted values, every third model month", attrs='data-series="fwd_supply"')
    return card(
        cid="fwdsupply", kind="exp",
        title=f'Supply growth to 2031: {M("fwd_supply_growth_5y_pct")}% with HSP-029, {M("fwd_supply_growth_5y_no_hsp029_pct")}% without',
        headline=(f'NEAR&rsquo;s supply grows {M("fwd_supply_growth_5y_pct")}% by 2031-11-04 if HSP-029 takes effect and {M("fwd_supply_growth_5y_no_hsp029_pct")}% if not.'),
        shows=('The supply path the frozen rating rule already uses for G_req (the realised share of the inflation cap and the post-v87 burn rate), run forward day by day, '
               'with HSP-029&rsquo;s ramp to a lower inflation cap and without it. This is the dilution the coverage paths are measured against.'),
        notshows='Whether HSP-029 is executed: its timelock ends on 2026-11-16, a Directors&rsquo; decision follows, and it needs validator adoption.',
        figure=fig,
        caption=f'Model: <code>pipeline/model.py</code> (supply_path), from {esc(m["asof"])} to {esc(m["fwd_target_date"])}. Unit: million NEAR.',
        capnote='The model uses the same arithmetic as <code>pipeline/h1a.py</code> (g_req).',
        notes=(f'Supply starts at {M("fwd_supply_now_m")}M NEAR, the archival header at the end of the supply window.',),
        source=source_p(ctx, raw=("raw/rpc/epoch_issuance.json", "raw/rpc/rating_assumptions.json"), code=("pipeline/model.py", "pipeline/h1a.py")),
        query=query_details(ctx, endpoints=(("Model", "python3 -m pipeline.compute (pipeline.model.supply_path)"), ("Series", "fwd_supply in data/series.json"))),
        data=data_details(tab))


# ------------------------------------------------------------------ the investment case (exploratory, 2026-11-14; pipeline/investment_case.py)
IC_SOURCE_RAW = ("raw/llama/dailyRevenue_near-intents.json", "raw/llama/volume_near-intents.json", "raw/llama/volume_thorchain-dex.json",
                 "raw/llama/volume_chainflip-amm.json", "raw/llama/volume_maya-protocol.json", "raw/coingecko/near_snapshot.json",
                 "raw/rpc/epoch_issuance.json", "raw/rpc/rating_assumptions.json")


def ic_query(ctx: Ctx) -> str:
    return query_details(ctx, endpoints=(("Model", "python3 -m pipeline.compute (calls pipeline.investment_case.investment_case); offline, standard library"),
                                         ("Metrics", "ic_* in data/metrics.json")))


def card_priced(ctx: Ctx) -> str:
    m, M, Mt = ctx.m, ctx.M, ctx.Mt
    title = "Growth in captured revenue that NEAR's price assumes, against the growth the market and the rating rule show"
    desc = (f"Bars from zero, percent a year: the price assumes {ctx.plain('ic_implied_cagr_r15_x25_pct')} at the base assumptions and "
            f"{ctx.plain('ic_implied_cagr_r10_x50_pct')} at the most generous in the grid; the rating rule needs {ctx.plain('rating_g_req_pct')}; "
            f"the peer set's volume grew {ctx.plain('ic_market_cagr_1y_pct')} last year and {ctx.plain('ic_market_cagr_4y_pct')} a year over four, and fell a "
            f"little a year over two; without NEAR Intents it fell last year and grew {ctx.plain('ic_market_ex_intents_cagr_4y_pct')} a year over four.")

    def P(key: str) -> Txt:
        return T(Mt(key), "% a year")

    def build(v: Variant) -> tuple[str, float]:
        rows = [
            {"label": "What the price assumes: base assumptions", "bars": [bar(m["ic_implied_cagr_r15_x25_pct"], "s2", P("ic_implied_cagr_r15_x25_pct"))]},
            {"label": "What the price assumes: the most generous assumptions in the grid", "bars": [bar(m["ic_implied_cagr_r10_x50_pct"], "s2", P("ic_implied_cagr_r10_x50_pct"))]},
            {"label": "What the rating rule needs to cover dilution (G_req)", "bars": [bar(m["rating_g_req_pct"], "sc", P("rating_g_req_pct"))]},
            {"label": "Peer set, with Intents: a year over four years", "bars": [bar(m["ic_market_cagr_4y_pct"], "s1", P("ic_market_cagr_4y_pct"))]},
            {"label": "Peer set, with Intents: last year", "bars": [bar(m["ic_market_cagr_1y_pct"], "s1", P("ic_market_cagr_1y_pct"))]},
            {"label": "Peer set, with Intents: a year over two years", "bars": [bar(max(m["ic_market_cagr_2y_pct"], 0.0), "s1", P("ic_market_cagr_2y_pct"))]},
            {"label": "The other venues: a year over four years", "bars": [bar(m["ic_market_ex_intents_cagr_4y_pct"], "s1", P("ic_market_ex_intents_cagr_4y_pct"))]},
            {"label": "The other venues: last year", "bars": [bar(max(m["ic_market_ex_intents_cagr_1y_pct"], 0.0), "s1", P("ic_market_ex_intents_cagr_1y_pct"))]},
        ]
        return hbar_panel(v, title="Growth a year to 2031, %", rows=rows, vmax=100, ticks=[0, 25, 50, 75, 100],
                          legend_items=[("s2", "What the price assumes", "box"), ("sc", "What the rating rule needs", "box"),
                                        ("s1", "What the venues did", "box")])

    fig = dual(ctx, "chart-priced", title, desc, build)
    rg, xg = (10, 15, 20), (10, 25, 50)   # pipeline.investment_case.R_GRID and X_GRID, printed from ic_grid_* below
    head = "".join(f'<th scope="col">{M(f"ic_grid_x{i}")}× revenue in 2031</th>' for i in range(3))
    body = "".join(f'<tr><td class="t">{M(f"ic_grid_r{i}_pct")}% a year</td>' + "".join(f'<td>{M(f"ic_implied_cagr_r{r}_x{x}_pct")}%</td>' for x in xg) + '</tr>'
                   for i, r in enumerate(rg))
    grid = (f'<div class="tablewrap" role="region" aria-label="Growth the market cap assumes" tabindex="0"><table><caption>Growth in captured revenue a year to '
            f'2031 that today&rsquo;s market cap assumes, %</caption><thead><tr><th scope="col" class="txt">Required return</th>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table></div>')
    figs = keyfigs([("Captured revenue now, a year", f'${M("ic_rev_90d_ann_m")}M'), ("Needed by 2031 (base)", f'${M("ic_required_rev_2031_m")}M'),
                    ("That is", f'{M("ic_required_multiple_x")}× today'), ("Market cap ÷ revenue now", f'{M("ic_near_mcap_to_rev_90d_ann_x")}×')])
    return card(
        cid="priced", kind="exp",
        title=(f'Growth the price assumes: {M("ic_implied_cagr_r15_x25_pct")}% a year to 2031'),
        headline=(f'For NEAR&rsquo;s price to rise {M("ic_base_r_pct")}% a year to 2031-11-04 and its market cap then to be {M("ic_base_x")} times its captured revenue, '
                  f'captured revenue must grow from ${M("ic_rev_90d_ann_m")}M a year to ${M("ic_required_rev_2031_m")}M, {M("ic_implied_cagr_r15_x25_pct")}% a year '
                  f'({M("ic_implied_cagr_r10_x50_pct")}% to {M("ic_implied_cagr_r20_x10_pct")}% across the grid), if Intents carried the price alone. The cross-chain '
                  f'venues tracked here grew {M("ic_market_cagr_1y_pct")}% last year, all of it Intents&rsquo; own growth (×{M("ic_intents_vol_1y_x")}): without Intents the venues&rsquo; volume '
                  f'changed by {M("ic_market_ex_intents_cagr_1y_pct")}%. Over four years the set grew {M("ic_market_cagr_4y_pct")}% a year, {M("ic_market_ex_intents_cagr_4y_pct")}% '
                  f'without Intents.'),
        shows=('A reverse DCF: the growth in captured Intents revenue that today&rsquo;s market cap implies, for a required return and a revenue multiple in 2031 '
               '(both assumptions, shown as a grid), with supply growth on the rating rule&rsquo;s own path, against what the cross-chain swap market has done.'),
        notshows=('A valuation of NEAR as a whole. NEAR&rsquo;s market cap also prices the L1 (its fees, which burn, staking and any monetary premium); here all of it '
                  'is set against Intents&rsquo; captured revenue, so the growth shown is what Intents would need if it carried the price alone.'),
        figure=fig,
        caption=(f'Market cap ${M("mcap_usd_b")}B on 2026-11-05. Captured revenue: the 90 days to {esc(m["asof"])}, annualised.'),
        capnote=(f'Supply grows {M("ic_supply_factor_x")}× to 2031-11-04 with HSP-029. Market: THORChain, Chainflip, Maya and NEAR Intents (DefiLlama, reported basis), '
                 'full years to the as-of date.'),
        extra=figs, more=grid,
        notes=(f'The required return is on NEAR&rsquo;s price. Supply grows and the buybacks burn nothing, so for the price to rise at that rate the market cap must grow '
               f'faster by the supply factor, {M("ic_supply_factor_x")}× by 2031; a holder who stakes also receives part of the new supply.',
               f'For comparison, THORChain&rsquo;s market cap is {M("ic_peer_thorchain_mcap_to_fees_x")}× its gross fees and Chainflip&rsquo;s '
               f'{M("ic_peer_chainflip_mcap_to_fees_x")}× (see the peer card). The grid&rsquo;s multiples are on captured revenue; the peers&rsquo; multiples on what '
               'reaches their token holders would be higher and are not computed here.',
               'Last year&rsquo;s growth of the set is all Intents&rsquo; growth, and part of it is DefiLlama&rsquo;s change on 2026-09-01 in what it counts as Intents '
               'volume (docs/leg-count.md): as a measure of the market it is generous to NEAR.',
               f'The market&rsquo;s growth depends on the window: {M("ic_market_cagr_3y_pct")}% a year over three years starts at the low of '
               f'${M("ic_market_y3_b")}B; the annual volumes were ${M("ic_market_y4_b")}B, ${M("ic_market_y3_b")}B, ${M("ic_market_y2_b")}B, '
               f'${M("ic_market_y1_b")}B and ${M("ic_market_y0_b")}B (oldest first). The two-year rate is negative and is drawn at zero.',
               f'G_obs, the rule&rsquo;s observed growth in captured revenue ({M("rating_g_obs_pct")}% a year), is left off the axis: it comes from a step in the share of '
               'fees captured, while gross fees and volume grew far less.'),
        source=source_p(ctx, raw=IC_SOURCE_RAW, code=("pipeline/investment_case.py", "pipeline/model.py", "pipeline/h1a.py")),
        query=ic_query(ctx), data=data_details(grid))


def card_multiply(ctx: Ctx) -> str:
    m, M, Mt = ctx.m, ctx.M, ctx.Mt
    title = "What would have to multiply by 2031 for captured revenue to reach what the price assumes"
    desc = (f"Panel A: bars from zero, multiples: captured revenue must multiply by {ctx.plain('ic_required_multiple_x')}; the market at its last-year pace gives "
            f"{ctx.plain('ic_mult_market_x')}, Intents' share at its twelve-month high {ctx.plain('ic_mult_share_x')}, leaving {ctx.plain('ic_mult_take_x')} for the take rate. "
            f"Panel B: bars from zero, basis points: NEAR's take today {ctx.plain('ic_take_90d_bp')}, Intents' gross fee {ctx.plain('ic_gross_bp_90d')}, "
            f"the take the price needs {ctx.plain('ic_take_needed_bp')}.")

    def build(v: Variant) -> tuple[str, float]:
        a, ha = hbar_panel(v, tag="A", title="Multiples by 2031", vmax=25, ticks=[0, 5, 10, 15, 20, 25], rows=[
            {"label": "Captured revenue must multiply by", "bars": [bar(m["ic_required_multiple_x"], "s2", T(Mt("ic_required_multiple_x"), "×"))]},
            {"label": "The market, at its last-year pace", "bars": [bar(m["ic_mult_market_x"], "s1", T(Mt("ic_mult_market_x"), "×"))]},
            {"label": "Intents' share, at its twelve-month high", "bars": [bar(m["ic_mult_share_x"], "s1", T(Mt("ic_mult_share_x"), "×"))]},
            {"label": "Left for NEAR's take rate", "bars": [bar(m["ic_mult_take_x"], "sc", T(Mt("ic_mult_take_x"), "×"))]}])
        b, hb = hbar_panel(v, tag="B", title="Take rate, basis points of volume", vmax=40, ticks=[0, 10, 20, 30, 40], rows=[
            {"label": "NEAR's captured take today", "bars": [bar(m["ic_take_90d_bp"], "s1", T(Mt("ic_take_90d_bp"), " bp"))]},
            {"label": "Intents' whole gross fee today", "bars": [bar(m["ic_gross_bp_90d"], "sc", T(Mt("ic_gross_bp_90d"), " bp"))]},
            {"label": "Take the price needs", "bars": [bar(m["ic_take_needed_bp"], "s2", T(Mt("ic_take_needed_bp"), " bp"))]}])
        return stack([(a, ha), (b, hb)])

    fig = dual(ctx, "chart-multiply", title, desc, build)
    figs = keyfigs([("Take needed ÷ whole gross fee", f'{M("ic_take_needed_vs_gross_x")}×'),
                    ("Market growth needed at the whole fee", f'{M("ic_market_cagr_needed_full_fee_pct")}% a year'),
                    ("Market growth, last year", f'{M("ic_market_cagr_1y_pct")}%')])
    return card(
        cid="multiply", kind="exp",
        title=(f'Take NEAR would need: {M("ic_take_needed_vs_gross_x")}× Intents&rsquo; whole gross fee'),
        headline=(f'Captured revenue = cross-chain swap volume × Intents&rsquo; share × NEAR&rsquo;s take. To multiply by {M("ic_required_multiple_x")} by 2031, with the market growing '
                  f'at its last-year pace (×{M("ic_mult_market_x")}) and Intents&rsquo; share at its twelve-month high (×{M("ic_mult_share_x")}), NEAR&rsquo;s take would have to rise '
                  f'×{M("ic_mult_take_x")}, from {M("ic_take_90d_bp")} bp to {M("ic_take_needed_bp")} bp of volume: {M("ic_take_needed_vs_gross_x")} times the whole '
                  f'{M("ic_gross_bp_90d")} bp gross fee Intents charges today. Even if NEAR kept the whole gross fee, the market would have to grow '
                  f'{M("ic_market_cagr_needed_full_fee_pct")}% a year.'),
        shows=('The required multiple from the reverse DCF (base assumptions), split into its three factors: the growth of the cross-chain swap market, Intents&rsquo; share '
               'of it, and the share of volume NEAR captures as revenue, each at a value from the data, and what is left for the take rate.'),
        notshows=('That the take rate cannot rise: fees are a policy choice. It shows how far the current fee structure is from what the price implies, if the market '
                  'grows as it has.'),
        figure=fig,
        caption=(f'Base case: {M("ic_base_r_pct")}% required return, {M("ic_base_x")}× revenue in 2031. Take and fee: the 90 days to {esc(m["asof"])}.'),
        capnote='Take and gross fee are DefiLlama revenue and fees ÷ volume, on the reported basis.',
        extra=figs,
        notes=(f'Intents&rsquo; share of the peer set over the 90 days was {M("ic_share_90d_pct")}%; its twelve-month high was {M("ic_share_max_pct")}% '
               f'({esc(m["ic_share_max_month"])}) and its low {M("ic_share_min_pct")}% ({esc(m["ic_share_min_month"])}).',
               'Each factor is on DefiLlama&rsquo;s reported volume, which counts both legs of some swaps and, from 2026-09-01, more of Intents&rsquo; volume '
               '(docs/leg-count.md). Only the full product, the revenue, is unaffected. Last year&rsquo;s market growth is all Intents&rsquo; and partly that change, '
               'so it is generous to NEAR, and the take needed is, if anything, understated.'),
        source=source_p(ctx, raw=IC_SOURCE_RAW + ("raw/llama/fees_near-intents.json",), code=("pipeline/investment_case.py",)),
        query=ic_query(ctx), data=data_details(table_html(
            [{"h": "Factor", "num": False}, {"h": "Value"}],
            [{"k": None, "cells": [a, b]} for a, b in (
                ("Required multiple of captured revenue", f'{M("ic_required_multiple_x")}×'), ("Market, last-year pace for five years", f'{M("ic_mult_market_x")}×'),
                ("Share, twelve-month high ÷ 90 days", f'{M("ic_mult_share_x")}×'), ("Left for the take rate", f'{M("ic_mult_take_x")}×'),
                ("Take today, bp", M("ic_take_90d_bp")), ("Gross fee today, bp", M("ic_gross_bp_90d")), ("Take needed, bp", M("ic_take_needed_bp")))],
            caption="Plotted values")))


def card_scenarios(ctx: Ctx) -> str:
    m, M, Mt = ctx.m, ctx.M, ctx.Mt
    title = "Bear, base and bull: coverage of NEAR's dilution on 2031-11-04, and which input moves it most"
    desc = (f"Panel A: bars from zero, percent: coverage on 2031-11-04 is {ctx.plain('ic_bear_coverage_2031_pct')} in the bear case, "
            f"{ctx.plain('ic_base_coverage_2031_pct')} in the base case and {ctx.plain('ic_bull_coverage_2031_pct')} in the bull case, against a line at "
            f"{ctx.plain('fwd_full_line_pct')}. Panel B: for each input, the base coverage with that input at its low and high value.")
    tor = (("market", "Market growth: two-year to four-year pace"), ("price", "NEAR's price: 365-day high to low"),
           ("take", "Take rate: lowest to highest month"), ("share", "Intents' share: twelve-month low to high"), ("hsp029", "HSP-029: not in force to in force"))

    def build(v: Variant) -> tuple[str, float]:
        a, ha = hbar_panel(v, tag="A", title="Coverage on 2031-11-04, %", vmax=300, ticks=[0, 100, 200, 300],
                           refs=[{"v": m["fwd_full_line_pct"], "label": T(Mt("fwd_full_line_pct"), "%: covers all dilution")}], rows=[
            {"label": f"{nm} case", "bars": [bar(m[f"ic_{k}_coverage_2031_pct"], c, T(Mt(f"ic_{k}_coverage_2031_pct"), "%"))]}
            for k, nm, c in (("bear", "Bear", "sc"), ("base", "Base", "s1"), ("bull", "Bull", "s2"))])
        rows = [{"label": lab, "bars": [{"v": m[f"ic_tor_{k}_hi_pct"], "cls": "s1",
                                         "txt": T(Mt(f"ic_tor_{k}_lo_pct"), "% to ", Mt(f"ic_tor_{k}_hi_pct"), "%"),
                                         "segs": [{"v": m[f"ic_tor_{k}_lo_pct"], "cls": "gap"},
                                                  {"v": round(m[f"ic_tor_{k}_hi_pct"] - m[f"ic_tor_{k}_lo_pct"], 1), "cls": "s1"}]}]}
                for k, lab in tor]
        b, hb = hbar_panel(v, tag="B", title="Base coverage with one input moved, % (each bar spans low to high)", vmax=200, ticks=[0, 50, 100, 150, 200],
                           refs=[{"v": m["ic_base_coverage_2031_pct"], "label": T("base ", Mt("ic_base_coverage_2031_pct"), "%")}], rows=rows)
        return stack([(a, ha), (b, hb)])

    fig = dual(ctx, "chart-scenarios", title, desc, build)
    cols = [{"h": "", "num": False}, {"h": "Bear"}, {"h": "Base"}, {"h": "Bull"}]
    spec = (("Market growth a year, %", "market_cagr_pct"), ("Intents' share, %", "share_pct"), ("NEAR's take, bp", "take_bp"),
            ("HSP-029 in force", "hsp029"), ("Captured revenue in 2031, $M a year", "rev_2031_m"), ("Captured revenue growth a year, %", "rev_cagr_pct"),
            ("Coverage of dilution on 2031-11-04, %", "coverage_2031_pct"), ("Today's market cap ÷ 2031 revenue, ×", "mcap_to_rev_2031_x"),
            ("Share of the revenue the price assumes, %", "vs_required_pct"))
    tab = table_html(cols, [{"k": None, "cells": [lab] + [M(f"ic_{s}_{key}") for s in ("bear", "base", "bull")]} for lab, key in spec],
                     caption="The three scenarios, from the data")
    return card(
        cid="scenarios", kind="exp",
        title=(f'Dilution paid for in 2031: {M("ic_bear_coverage_2031_pct")}% bear, {M("ic_base_coverage_2031_pct")}% base, {M("ic_bull_coverage_2031_pct")}% bull'),
        headline=(f'With every input at a value from the data and the price held flat, captured revenue on 2031-11-04 would pay for {M("ic_bear_coverage_2031_pct")}% '
                  f'(bear), {M("ic_base_coverage_2031_pct")}% (base) or {M("ic_bull_coverage_2031_pct")}% (bull) of the dollar value of NEAR&rsquo;s dilution. The bull '
                  f'case&rsquo;s ${M("ic_bull_rev_2031_m")}M a year is {M("ic_bull_vs_required_pct")}% of the ${M("ic_required_rev_2031_m")}M the price would assume at '
                  f'{M("ic_base_r_pct")}% and {M("ic_base_x")}×; at the three-year market pace it would be {M("ic_bull3y_vs_required_pct")}%. Market growth and NEAR&rsquo;s '
                  f'price move coverage most: from {M("ic_tor_market_lo_pct")}% to {M("ic_tor_market_hi_pct")}% and from {M("ic_tor_price_lo_pct")}% to '
                  f'{M("ic_tor_price_hi_pct")}%.'),
        shows=('Three futures for captured revenue (market growth × Intents&rsquo; share × NEAR&rsquo;s take), each input at a value from the data, run against the rating '
               'rule&rsquo;s supply path at its constant (flat) price; then the base case with one input at a time at its low and high value. Coverage is what '
               'captured revenue would pay for: not all of it reaches the buyback wallet, and none of it is burned.'),
        notshows=('Probabilities: the scenarios are not weighted (the Monte Carlo card gives a distribution). Nor a new fee stream, a partner change or a regime the '
                  'data have not seen.'),
        figure=fig,
        caption=(f'Price held at ${M("price_usd")}, the rule&rsquo;s. Where each case&rsquo;s inputs come from is under Notes and sources.'),
        notes=(f'Bear: market at its two-year pace, share at its twelve-month low ({esc(m["ic_share_min_month"])}), take at its lowest month since the fee switch '
               f'({esc(m["ic_take_min_month"])}), no HSP-029. Base: last-year market growth and the last 90 days&rsquo; share and take, with HSP-029. Bull: four-year '
               f'market pace, twelve-month-high share ({esc(m["ic_share_max_month"])}), highest month&rsquo;s take ({esc(m["ic_take_max_month"])}), with HSP-029.',
               f'Coverage moves in inverse proportion to NEAR&rsquo;s price, because each dollar of revenue buys back less NEAR at a higher price: the 365-day range, '
               f'${M("ic_price_365d_low_usd")} to ${M("ic_price_365d_high_usd")}, moves the base case from {M("ic_tor_price_lo_pct")}% to {M("ic_tor_price_hi_pct")}%.',
               'Which window anchors each case was chosen after the annual volumes, monthly shares and monthly take rates were computed (PREREG-ADDENDUM.md, '
               '2026-11-14 entries); the card on what the price assumes lists every window, so a reader can substitute another.',
               f'The bull case grows the whole peer set at its four-year pace and also lifts Intents&rsquo; share, so it counts some of Intents&rsquo; share gains twice. '
               f'Its revenue growth, {M("ic_bull_rev_cagr_pct")}% a year, falls short of what the price would assume at {M("ic_base_x")}× and exceeds it only at '
               f'{M("ic_grid_x2")}× ({M("ic_implied_cagr_r10_x50_pct")}% at {M("ic_grid_r0_pct")}% a year, {M("ic_implied_cagr_r15_x50_pct")}% at {M("ic_grid_r1_pct")}%).',
               f'At today&rsquo;s market cap, NEAR would trade at {M("ic_base_mcap_to_rev_2031_x")}× its 2031 captured revenue in the base case and '
               f'{M("ic_bull_mcap_to_rev_2031_x")}× in the bull case.'),
        source=source_p(ctx, raw=IC_SOURCE_RAW + ("raw/coingecko/near_market_chart_365d.json",), code=("pipeline/investment_case.py", "pipeline/model.py")),
        query=ic_query(ctx), data=data_details(tab))


def card_peersval(ctx: Ctx) -> str:
    m, M, Mt = ctx.m, ctx.M, ctx.Mt
    title = "Market cap per dollar of fees: NEAR against the cross-chain swap venues with a listed token"
    desc = (f"Bars from zero, multiples: NEAR's market cap is {ctx.plain('ic_near_mcap_to_intents_fees_x')} times Intents' gross fees over 365 days and "
            f"{ctx.plain('ic_near_mcap_to_rev_90d_ann_x')} times its captured revenue at the last 90 days' rate; THORChain's is "
            f"{ctx.plain('ic_peer_thorchain_mcap_to_fees_x')} times its fees and Chainflip's {ctx.plain('ic_peer_chainflip_mcap_to_fees_x')}.")

    def build(v: Variant) -> tuple[str, float]:
        return hbar_panel(v, title="Market cap ÷ annual fees or revenue, ×", vmax=250, ticks=[0, 50, 100, 150, 200, 250], rows=[
            {"label": "NEAR ÷ captured revenue", "bars": [bar(m["ic_near_mcap_to_rev_90d_ann_x"], "s2", T(Mt("ic_near_mcap_to_rev_90d_ann_x"), "×"))]},
            {"label": "NEAR ÷ Intents' gross fees", "bars": [bar(m["ic_near_mcap_to_intents_fees_x"], "s2", T(Mt("ic_near_mcap_to_intents_fees_x"), "×"))]},
            {"label": "THORChain (RUNE) ÷ fees", "bars": [bar(m["ic_peer_thorchain_mcap_to_fees_x"], "s1", T(Mt("ic_peer_thorchain_mcap_to_fees_x"), "×"))]},
            {"label": "Chainflip (FLIP) ÷ fees", "bars": [bar(m["ic_peer_chainflip_mcap_to_fees_x"], "s1", T(Mt("ic_peer_chainflip_mcap_to_fees_x"), "×"))]}])

    fig = dual(ctx, "chart-peersval", title, desc, build)
    tab = table_html([{"h": "Token", "num": False}, {"h": "Market cap, $M"}, {"h": "Fees, 365 days, $M"}, {"h": "Market cap ÷ fees, ×"}], [
        {"k": None, "cells": ["NEAR (Intents' gross fees)", M("ic_near_intents_fees_365d_m"), M("ic_near_intents_fees_365d_m"), M("ic_near_mcap_to_intents_fees_x")]},
        {"k": None, "cells": ["THORChain (RUNE)", M("ic_peer_thorchain_mcap_m"), M("ic_peer_thorchain_fees_365d_m"), M("ic_peer_thorchain_mcap_to_fees_x")]},
        {"k": None, "cells": ["Chainflip (FLIP)", M("ic_peer_chainflip_mcap_m"), M("ic_peer_chainflip_fees_365d_m"), M("ic_peer_chainflip_mcap_to_fees_x")]}],
        caption="Plotted values (NEAR's market cap is in the caption)")
    tab = tab.replace(f'<td>{M("ic_near_intents_fees_365d_m")}</td><td>{M("ic_near_intents_fees_365d_m")}</td>',
                      f'<td>{M("mcap_usd_b")}B</td><td>{M("ic_near_intents_fees_365d_m")}</td>', 1)
    return card(
        cid="peersval", kind="exp",
        title=(f'Market cap ÷ gross fees: NEAR {M("ic_near_mcap_to_intents_fees_x")}×, THORChain {M("ic_peer_thorchain_mcap_to_fees_x")}×, '
               f'Chainflip {M("ic_peer_chainflip_mcap_to_fees_x")}×'),
        headline=(f'At the same hour, NEAR&rsquo;s market cap was {M("ic_near_mcap_to_intents_fees_x")} times the gross fees NEAR Intents charged over 365 days and '
                  f'{M("ic_near_mcap_to_rev_90d_ann_x")} times its captured revenue at the last 90 days&rsquo; rate; THORChain&rsquo;s (RUNE) was '
                  f'{M("ic_peer_thorchain_mcap_to_fees_x")} times its fees and Chainflip&rsquo;s (FLIP) {M("ic_peer_chainflip_mcap_to_fees_x")} times.'),
        shows=('What the market pays per dollar of fees for the cross-chain swap venues in the peer set that have a listed token, against NEAR, on DefiLlama&rsquo;s '
               'fee series and CoinGecko&rsquo;s market caps at one hour.'),
        notshows=('Like-for-like value. NEAR&rsquo;s market cap prices the whole L1, of which Intents is one part; the peers&rsquo; multiples are on gross fees, most of which do not '
                  'reach their tokens (DefiLlama counts only the small share of THORChain&rsquo;s swap fees burned as RUNE as holders&rsquo; revenue). Maya Protocol is '
                  'left out: its token (CACAO) is not listed on CoinGecko.'),
        figure=fig,
        caption=(f'Market caps: {esc(m["ic_peer_caps_at_utc"])} UTC (NEAR ${M("mcap_usd_b")}B, 22:50). Fees: the 365 days to {esc(m["asof"])}.'),
        notes=('The peer market caps come from a fetch made on 2026-11-14 (python3 -m pipeline.fetch_peer_caps); only the hourly point nearest NEAR&rsquo;s committed '
               'snapshot is used.',),
        source=source_p(ctx, raw=("raw/coingecko/peer_caps_30d.json", "raw/coingecko/near_snapshot.json", "raw/llama/fees_near-intents.json",
                                  "raw/llama/fees_thorchain-dex.json", "raw/llama/fees_chainflip-amm.json"),
                        code=("pipeline/fetch_peer_caps.py", "pipeline/investment_case.py")),
        query=query_details(ctx, endpoints=(("Endpoint", "GET https://api.coingecko.com/api/v3/coins/{near,thorchain,chainflip}/market_chart?vs_currency=usd&days=30"),
                                            ("Fetcher", "python3 -m pipeline.fetch_peer_caps (no key)"))),
        data=data_details(tab))


def card_signposts(ctx: Ctx) -> str:
    m, M, Mt = ctx.m, ctx.M, ctx.Mt
    title = "Signposts: how far today's values are from the lines that would favour the upside"
    desc = "Bars from zero, percent of each line: 100 means today's value is at the line."
    sp = (("coverage", "Coverage of dilution (P3, M1)"), ("revenue", "Captured revenue, 90 days (P2)"), ("share", "Intents' share of the peer set (P1)"),
          ("market", "Market growth against G_req"), ("take", "NEAR's take against what the price needs"), ("staking", "Staking outflow against H1a's line"))

    def build(v: Variant) -> tuple[str, float]:
        return hbar_panel(v, title="Today as a share of the line, %", vmax=125, ticks=[0, 25, 50, 75, 100, 125],
                          refs=[{"v": m["fwd_full_line_pct"], "label": "at the line"}],
                          rows=[{"label": lab, "bars": [bar(m[f"ic_sp_{k}_pct"], "s1" if m[f"ic_sp_{k}_pct"] >= 100 else "sc", T(Mt(f"ic_sp_{k}_pct"), "%"))]}
                                for k, lab in sp])

    fig = dual(ctx, "chart-signposts", title, desc, build)
    rows = [
        ("Coverage of dilution (P3&rsquo;s quantity, 90 days)", f'{M("p3_quantity_90d_asof_pct")}%', f'at least {M("ic_p3_line_pct")}% (P3, frozen; M1, exploratory, dated after the freeze)', "2027-11-04"),
        ("Captured revenue, 90 days", f'${M("rating_r90_usd_m")}M', f'at least ${M("ic_p2_line_usd_m")}M (P2, frozen)', "2027-05-04"),
        ("Intents&rsquo; share of the peer set, 365 days", f'{M("intents_share_peerset_365d_pct")}%', f'at least {M("ic_p1_line_pct")}% (P1, frozen)', "2027-05-04"),
        ("Cross-chain swap volume, growth a year", f'{M("ic_market_cagr_1y_pct")}%', f'{M("rating_g_req_pct")}% (G_req, if share and take stay where they are)', "each year"),
        ("NEAR&rsquo;s captured take, 90 days", f'{M("ic_take_90d_bp")} bp', f'{M("ic_take_needed_bp")} bp (what the price would need, at last year&rsquo;s market pace and Intents&rsquo; twelve-month-high share)', "each month"),
        ("Net staking outflow ÷ staking rewards (H1a)", f'{M("h1a_ratio_as_written_x")}×', f'under {ctx.K("h1a_pass_below_x")}× (H1a&rsquo;s line)', "each quarter"),
        ("HSP-029&rsquo;s issuance cut", "not yet in force", "in force (a lower inflation cap)", "timelock ends 2026-11-16"),
        ("A per-stream attestation of the escrow releases", "none", "published by NEAR (collapses the ladder&rsquo;s range)", "any time"),
    ]
    fw = ctx.forward
    week = ""
    if fw and forward_word(fw, "F4") in ("PASS", "MISS"):     # the scored week, once F1-F4 are scored: the latest read of the share
        share = fmt_value(round(forward_number("F4", fw["results"]["F4"], "intents_share_pct", fw["_path"]), 1), 1)
        span = f'<span data-f="F4.intents_share_pct" data-scale="1">{share}</span>'
        rows.insert(3, (f"Intents&rsquo; share of the peer set, scoring week {esc(sf.WINDOW[0])} to {esc(sf.WINDOW[1])}", f"{span}%",
                        f'at least {ctx.K("f4_min_pct")}% (F4, frozen)', f'scored: {plain_forward(forward_word(fw, "F4"))}'))
        week = f' In the scoring week, though, Intents was {span}% of the peer set&rsquo;s volume (F4).'
    tab = table_html([{"h": "Signpost", "num": False}, {"h": "Today", "num": False}, {"h": "Line that favours the upside", "num": False}, {"h": "When", "num": False}],
                     [{"k": None, "cells": list(r)} for r in rows], caption="Signposts, with today's values and the lines")
    return card(
        cid="signposts", kind="exp",
        title="Signposts: the take rate and market growth are far from what the price needs",
        headline=(f'Of the lines that would favour the upside, Intents&rsquo; share is past its own ({M("ic_sp_share_pct")}% of P1&rsquo;s line), revenue and coverage are '
                  f'close ({M("ic_sp_revenue_pct")}% and {M("ic_sp_coverage_pct")}%), and the two that carry the price are far: market growth is '
                  f'{M("ic_sp_market_pct")}% of G_req and NEAR&rsquo;s take {M("ic_sp_take_pct")}% of what the price needs.{week}'),
        shows=('The values a reader should watch, each against the line that would favour the upside: the pre-registered P1 to P3, the model&rsquo;s M1, the rating '
               'rule&rsquo;s G_req, the take the price needs, and H1a&rsquo;s line.'),
        notshows='A score: P1 to P3 and M1 to M4 resolve on their own dates, from the data, and are scored as written.',
        figure=fig,
        caption=f'Today means the data to {esc(m["asof"])}. Lines: PREREG.md, the addendum, the cards above.',
        notes=('For staking the line is H1a&rsquo;s line (net staking outflow under half of staking rewards) divided by today&rsquo;s ratio, so a full bar would mean '
               'stakers are no longer net sellers of their rewards.',),
        source=source_p(ctx, raw=IC_SOURCE_RAW, code=("pipeline/investment_case.py", "pipeline/compute.py")),
        query=ic_query(ctx), data=data_details(tab))


FWD_CARDS = (("priced", "What the price assumes", card_priced), ("multiply", "What would have to multiply", card_multiply),
             ("scenarios", "Bear, base and bull", card_scenarios), ("peersval", "Peer valuation", card_peersval),
             ("fwdcov", "Uncertainty: Monte Carlo", card_fwdcov), ("fwdsupply", "Supply projection", card_fwdsupply),
             ("signposts", "Signposts", card_signposts))


# How the page groups the cards (every card is shown; the grouping is only where it sits):
#   the case: the six charts that carry the argument, in its order (today, what the price assumes, what would have to give, the outcomes,
#             what to watch, how uncertain the model is); the story page tells the same six;
#   the pre-registered tests;
#   supporting evidence: the other exploratory charts, paired by topic.
CASE_IDS = ("ladder", "priced", "multiply", "scenarios", "signposts", "fwdcov")
EVIDENCE = (("Market and peers", ("peers", "peersval")), ("Revenue and the take rate", ("revenue", "take", "escrow")),
            ("Who else gets paid", ("partners", "paid")), ("Supply and dilution", ("supply", "fwdsupply")), ("Network usage", ("usage",)))
EVID_IDS = tuple(c for _, ids in EVIDENCE for c in ids)


PRE_CARDS = (("h1a", "H1a: staking outflow", card_h1a), ("h1b", "H1b: net exchange inflow", card_h1b),
             ("h1c", "H1c: identified buying", card_h1c), ("rating", "Rating rule inputs", card_rating),
             ("forward", "Forward tests F1-F4", card_forward))
EXP_CARDS = (("ladder", "The value-capture ladder", card_ladder), ("escrow", "Escrow share by month", card_escrow),
             ("take", "NEAR's take in 1Click", card_take), ("partners", "Partner concentration", card_partners),
             ("paid", "Partner fees against NEAR's revenue", card_paid), ("peers", "Share of the peer set", card_peers),
             ("revenue", "Monthly revenue and take rate", card_revenue), ("supply", "Supply and net issuance", card_supply),
             ("usage", "Network usage", card_usage))


def tile(*, label: str, big: str, note: str, href: str) -> str:
    return (f'<li class="tile"><p class="tlabel">{label}</p>'
            f'<p class="big">{big}</p><p class="tnote">{note}</p><a href="{href}">Figure {fig_no(href.split("#chart-")[1])}</a></li>')


NUMBER_WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")   # index = a whole number of minutes


def first_bigquery_record(ctx: Ctx) -> tuple[str, str]:
    """(manifest path, time) of the earliest BigQuery-derived file in data/MANIFEST.json, the time as "2026-11-05 22:55:37".

    That time is when pipeline.common.record() last wrote the file, on the author's machine: it is the earliest BigQuery
    result the repository records, not proof of when the first query ran."""
    rows = sorted((e["fetched_at"], rel) for rel, e in ctx.manifest.items() if "bigquery" in str(e.get("source", "")).lower())
    if not rows:
        raise SystemExit("render: data/MANIFEST.json records no BigQuery result")
    return rows[0][1], rows[0][0].replace("T", " ").rstrip("Z")


def freeze_order(ctx: Ctx) -> tuple[str, str]:
    """(the first BigQuery record's time as a span that names its manifest entry, how long after the freeze it is, in words).

    The page says the freeze came before that record only because the manifest says so: if it ever does not, the render stops."""
    rel, stamp = first_bigquery_record(ctx)
    gap = (datetime.fromisoformat(stamp) - datetime.fromisoformat(FREEZE_UTC)).total_seconds()
    if gap <= 0:
        raise SystemExit(f"render: {rel} is recorded as written at {stamp}, not after the freeze commit ({FREEZE_UTC}); rewrite the freeze sentences")
    n = round(gap / 60)
    how_long = ("less than a minute" if n < 1 else f"about {NUMBER_WORDS[n]} minute{'s' if n != 1 else ''}" if n < len(NUMBER_WORDS)
                else "more than ten minutes")
    return f'<span data-r="stamp:{esc(rel)}">{esc(stamp)} UTC</span>', how_long


def scorecard(ctx: Ctx) -> str:
    m, M, K = ctx.m, ctx.M, ctx.K
    check_pre_results(ctx)
    fw = ctx.forward
    tiles = [
        tile(label="H1a: most staking rewards stay staked",
             big=f'{M("h1a_ratio_as_written_x")}×',
             note=f'Net staking outflow ÷ staking rewards over 90 days. H1a predicted under {K("h1a_pass_below_x")}×.', href="#chart-h1a"),
        tile(label="H1b: less NEAR reaches exchanges than is minted",
             big=f'{M("h1b_net_inflow_lower_m")}M to {M("h1b_net_inflow_upper_m")}M',
             note=(f'NEAR net into exchanges, against {M("h1a_gross_issuance_90d_m")}M minted. Labels cover {M("h1b_coverage_count_pct")}%; '
                   f'a point result needs {K("h1b_coverage_min_pct")}%.'), href="#chart-h1b"),
        tile(label="H1c: identified buyers absorb a larger share",
             big=f'{M("h1c_ratio_lower_pct")}% and {M("h1c_ratio_upper_pct")}%',
             note=f'Identified buying ÷ net exchange inflow at the lower and upper bound. H1c needs at least {K("h1c_min_pct")}% at both bounds.',
             href="#chart-h1c"),
        tile(label="Rating: the frozen rule",
             big="No signal",
             note=(f'Revenue growth {M("rating_g_obs_pct")}% a year against {M("rating_g_req_pct")}% required, but a buy also needs H1b confirmed, which '
                   f'the labels cannot settle. No view on NEAR.'), href="#chart-rating"),
    ]
    if fw:
        words = [forward_word(fw, f) for f in FORWARD_IDS]
        npass, nmiss = words.count("PASS"), words.count("MISS")
        nns = 4 - npass - nmiss
        tiles.append(tile(label="Forward tests F1 to F4",
                          big=(f'<span data-f="@count.PASS" data-scale="1">{npass}</span> came true, '
                               f'<span data-f="@count.MISS" data-scale="1">{nmiss}</span> did not'),
                          note=(f'<span data-f="@count.not scorable" data-scale="1">{nns}</span> could not be scored. Every result is published.'),
                          href="#chart-forward"))
    else:
        opens = sf.SCORE_NOT_BEFORE.strftime("%Y-%m-%d %H:%M UTC")
        tiles.append(tile(label="Forward tests F1 to F4", big="F1 to F4",
                          note=f'Four predictions frozen before the window; scored after {esc(opens)}, whatever the result.', href="#chart-forward"))
    freeze_stamp, freeze_gap = freeze_order(ctx)
    return (f'<section id="scorecard" aria-labelledby="scorecard-h"><h3 id="scorecard-h" class="sr">Scorecard</h3>'
            f'<ul class="tiles">{"".join(tiles)}</ul>'
            f'<details class="fz"><summary>When the tests were frozen</summary><p class="note">Frozen at commit <code>{FREEZE_COMMIT}</code> ({FREEZE_UTC} UTC), {freeze_gap} before the first BigQuery result the repository records '
            f'({freeze_stamp} in <code>data/MANIFEST.json</code>). Commit and manifest times are written by the author&rsquo;s machine; one external record, GitHub&rsquo;s activity log, dates the push of the freeze commit to '
            f'2026-11-05 22:53:33 UTC (<code>PREREG-ADDENDUM.md</code>, 2026-11-12 23:50 UTC entry, item 2). BigQuery job IDs, which embed their creation time, are recorded only for the H1b and H1c runs and one October escrow scan; the H1a queries '
            f'have none. The table <a href="{esc(gh("PREREG.md"))}#{PREREG_ANCHOR}">&ldquo;What we had already '
            f'seen&rdquo; in PREREG.md</a> lists the data already in hand at the freeze.</p></details></section>')


def not_computed(ctx: Ctx) -> str:
    M, m = ctx.M, ctx.m
    items = [
        ("Net exchange inflow as one number (H1b, H1c).",
         f'Only {M("h1b_coverage_count_pct")}% of the top-100 receivers carry an exchange label ({M("h1b_coverage_tier1_count_pct")}% a cited one; the rest are '
         f'labelled by our sweep rule). The binding gap is labelling: the flows are in the data, but no citable NEAR '
         f'address was found for OKX, Coinbase, Kraken, Bybit, HTX, Crypto.com, Upbit or Bithumb, and nothing is labelled from its name alone.'),
        ("Which fee stream pays the escrow releases.",
         f'{M("ladder_escrow_unshields_pct_of_issuance", 2)} points of the ladder arrive as unshields from the Confidential Intents escrow. The public chain does not show which fee '
         f'stream funds them; a per-stream attestation by NEAR would turn the range into one number.'),
        ("NEAR&rsquo;s share of partner fees.",
         f'On partner swaps with no buyback entry the ledger puts NEAR&rsquo;s share, as it reaches the buyback wallet, at no more than {M("near_share_of_partner_fees_max_pct")}% '
         f'({M("near_share_of_partner_fees_max_tight_pct")}% on the tighter reading) but does not measure it.'),
        ("The other half of Intents.",
         f'1Click is {M("explorer_vs_llama_net_pct")}% of DefiLlama&rsquo;s volume on the halved basis ({M("legcount_oneclick_share_solver_lo_pct")}% to {M("legcount_oneclick_share_solver_hi_pct")}% '
         f'on one-sided volume, taking confidential solver shields as one-sided confidential volume; exploratory, <code>docs/confidential-flow.md</code>). near.com, direct solver flow and other integrations have a fee '
         f'structure the Explorer API does not show, and we do not extrapolate.'),
        ("Why the usage step happened.",
         f'BigQuery shows that Sweat Economy&rsquo;s signers account for {M("usage_bq_step_kaiching_share_pct")}% of the fall in daily transactions on '
         f'{esc(m["l1_step_date"])}, and that HOT Wallet&rsquo;s <code>.tg</code> accounts account for {M("usage_bq_tg_share_of_signer_drop_pct")}% of the fall in active accounts '
         'over a year (exploratory, <code>docs/usage.md</code>). Why either happened is not in the data, and no sybil or bot filter is applied.'),
        ("Who the sellers were.", 'NEAR is fungible, so every flow here is a market-wide balance. Nothing says which coins were sold.'),
        ("What NEAR is worth as an L1.", 'The investment case sets NEAR&rsquo;s whole market cap against Intents&rsquo; captured revenue. What the L1 itself is worth '
         '(its fees, which burn, staking, any monetary premium) is not computed, so the growth the price assumes is what Intents would need if it carried the price alone.'),
        ("Longer-dated predictions P1 to P3.", 'They resolve on 2027-05-04 and 2027-11-04 and cannot be scored yet.'),
        ("HSP-029&rsquo;s issuance cut.",
         'Its on-chain timelock ends on 2026-11-16, after the submission deadline; we added that date up from the proposal&rsquo;s voting start, voting period and timelock period, and two published sources give the same date (<code>PREREG-ADDENDUM.md</code>, 2026-11-12 23:50 UTC entry, item 3). A House of Stake Directors&rsquo; decision on execution follows the timelock, and the proposal text also says the cut needs validator adoption through a protocol upgrade. G_req assumes the ramp; we state it as an open question and do not predict it.'),
        ("Earlier work.", f'An earlier analysis of {ctx.M("unstakers_a14_n")} accounts that reach one unlabelled hub (THESIS.md, the supply-side section, and docs/supply-side.md) is exploratory and is not reproduced here; the repository does not record when it was done or whether it preceded the freeze (PREREG-ADDENDUM.md, 2026-11-08 02:03 UTC entry, item 5). No card on this page uses it.'),
    ]
    lis = "".join(f"<li><strong>{a}</strong> {b}</li>" for a, b in items)
    return (f'<section id="not-computed" aria-labelledby="nc-h"><h2 id="nc-h">Not computed here</h2>'
            f'<details class="more lead"><summary>Questions we leave open.</summary>'
            f'<p class="note">We leave them open either because the committed data cannot answer them or because a number would claim more than the data support.</p>'
            f'<ul class="plain">{lis}</ul></details></section>')


def reproduce(ctx: Ctx) -> str:
    n_metrics = len(ctx.m)
    rows = [
        ("git clone " + REPO_URL + ".git && cd near-flow-statement",
         'A folder with README.md, THESIS.md, PREREG.md, data/, pipeline/, sql/ and site/. Python <span class="ver">3.10</span> or later is the only requirement: standard library only, no keys, no network.'),
        ("python3 -m pipeline.check --manifest",
         "check: PASS. Every raw snapshot under data/raw/ matches the SHA-256 recorded in data/MANIFEST.json."),
        ("python3 -m pipeline.compute",
         f'wrote data/metrics.json (<span data-count="metrics">{n_metrics}</span> metrics, as of {esc(ctx.m["asof"])}). data/metrics.json and data/series.json do not change: the rebuild is deterministic.'),
        ("python3 -m pipeline.check --numbers",
         "check: PASS. Every number marked in README.md, THESIS.md, PREREG-ADDENDUM.md and docs/*.md matches data/metrics.json."),
        ("python3 -m unittest discover -s tests",
         "The run ends with OK. The tests include this page: each number it prints in a data-attributed span is compared with the source it names, each bar is "
         "checked against the value it draws, and the committed page must equal a fresh render."),
        ("python3 -m pipeline.render --check",
         "render: site/ matches a fresh render. This page is exactly what the committed data produces."),
        ("python3 -m pipeline.render", "Writes site/index.html, this page, from the committed data. It has no timestamp, so the same data gives the same bytes."),
    ]
    lis = "".join(f'<li><p class="do"><strong>Do:</strong> <code>{esc(c)}</code></p><p class="see"><strong>See:</strong> {s}</p></li>'
                  for c, s in rows)
    return (f'<section id="reproduce" aria-labelledby="repro-h"><h2 id="repro-h">Reproduce</h2>'
            f'<details class="more lead"><summary>Every number and chart on this page rebuilds offline from the committed data.</summary>'
            f'<p class="note">Each step says what its command prints. <code>make reproduce</code> runs steps 2 to 4, <code>make render-check</code> runs step 6, '
            f'and <code>make site</code> runs steps 2 to 4 and then step 7, offline.</p><ol class="steps">{lis}</ol></details></section>')


def limits(ctx: Ctx) -> str:
    M = ctx.M
    traced = escrow_attribution(ctx)["traced_from"]
    items = [
        ("Collector roles.",
         f'Collector A&rsquo;s role (the explicit buyback fee) is cross-checked: its priced inflows are {M("collector_a_vs_explicit_fees_pct")}% of the fees the Explorer lists. '
         f'Collector B&rsquo;s role (a share of quote improvement) is inferred from committed, re-checkable per-swap evidence: it is paid a variable cut on '
         f'{M("fee_ev_collector_b_swaps_n")} of {M("fee_ev_swaps_n")} sampled swaps across channels. The quote it would be measured against is not in the Explorer API, '
         f'so the role is consistent with the docs and unproven.'),
        ("Partner numbers", 'rest on one key-gated source, the Explorer API.'),
        ("Sampling.",
         f'Fee mechanics come from {M("fee_ev_swaps_n")} swaps sampled from hours inside the window ({M("fee_ev_hours_with_swaps_n")} of the four sampled hours returned swaps) '
         f'across {M("fee_ev_channels_n")} channels, a small sample. The 30-day totals reconcile.'),
        ("Pro-rata assumption.",
         f'Collector B&rsquo;s quote improvement is allocated to SwapKit by volume share. SwapKit swaps do pay collector B ({M("fee_ev_collector_b_swapkit_swaps_n")} of the '
         f'{M("fee_ev_swapkit_swaps_n")} sampled), so the allocation has support, but its size is not measured.'),
        ("Unpriced tokens",
         f'are left out of the collector values: {M("collector_a_valued_transfers_pct")}% of collector A&rsquo;s transfers and {M("collector_b_valued_transfers_pct")}% of collector B&rsquo;s '
         f'are priced, so both figures are lower bounds.'),
        ("Escrow funding", f'before {traced} is mostly sample-attributed.'),
        ("Exchange labels are snapshots", 'dated 2026-11-06. Exchange addresses retired before then may be missing, which biases the lower bound down.'),
        ("The name-filter check", 'behind the lst-pool.near sensitivity read a sample of validator sets, from some of the epochs.'),
        ("Investment-case assumptions.", 'The required return and the 2031 revenue multiple are assumptions, shown as a grid; which data window anchors each '
         'scenario was chosen after the annual volumes, monthly shares and take rates were computed; the market&rsquo;s growth last year is all Intents&rsquo; and '
         'partly DefiLlama&rsquo;s 2026-09-01 counting change; the Monte Carlo&rsquo;s volume drift comes from the one month that spans that change. All of it is '
         'exploratory and dated in the addendum.'),
        ("The upper bound is mechanical.", 'It treats every unlabelled top-100 receiver as an exchange, including accounts that are probably not.'),
        ("DefiLlama&rsquo;s revenue", 'counts the NEAR delivered to the wallets, at delivery, and its volume series steps up on 2026-09-01.'),
        ("Not reproduced here.", f'An earlier analysis of {ctx.M("unstakers_a14_n")} accounts that reach one unlabelled hub (THESIS.md, the supply-side section, and docs/supply-side.md) is exploratory and is not reproduced here; the repository does not record when it was done or whether it preceded the freeze. No card on this page uses it.'),
    ]
    lis = "".join(f"<li><strong>{a}</strong> {b}</li>" for a, b in items)
    return (f'<section id="limits" aria-labelledby="limits-h"><h2 id="limits-h">Limits</h2>'
            f'<details class="more lead"><summary>Four limits matter most: exchange labels, the escrow&rsquo;s fee stream, one partner source, and two assumptions.</summary>'
            f'<p class="note">Too few exchange addresses are labelled to settle the exchange tests: {M("h1b_coverage_count_pct")}% of the '
            f'top-100 receivers, where a point result needs {ctx.K("h1b_coverage_min_pct")}%. Which fee funds the escrow releases is unattested. Partner numbers rest '
            f'on one key-gated source. And the investment case rests on two assumptions, shown as a grid. '
            f'Escrow funding hops are traced per single-use delivery from {traced}, which a test checks against <code>data/raw/escrow/deliveries.csv</code>. '
            f'The full list comes from the Limits sections of THESIS.md and docs/*.md and from PREREG-ADDENDUM.md.</p>'
            f'<ul class="plain">{lis}</ul></details></section>')


def answer_line(ctx: Ctx) -> str:
    """What the page answers, under its title (markup): the two questions, then the pre-registered result and the exploratory range.

    Every number is a metric span. The words are true of the data as committed: H1a fails, H1b and H1c are inconclusive, the frozen rule outputs
    Hold, and the three sources add up to the total (each is rounded to two decimals, so the sum may be off by up to 0.02). If the data stop
    saying that, the render stops, so the page cannot go on saying it."""
    m, M, K = ctx.m, ctx.M, ctx.K
    parts = [m["ladder_public_collectors_pct_of_issuance"], m["ladder_escrow_unshields_pct_of_issuance"], m["ladder_other_pct_of_issuance"]]
    check_pre_results(ctx)
    if not abs(sum(parts) - m["ladder_all_wallets_pct_of_issuance"]) <= 0.02 + 1e-9:
        raise SystemExit("render: the answer under the title says the three sources add up to the total; the data no longer say that, "
                         "so rewrite answer_line()")
    return (
        '<p class="questions"><strong>The pre-registered question:</strong> how much NEAR actually flows to exchanges, and how much of that do identified buyers '
        'absorb? (It makes no claim about which coins are sold.) <strong>The question the evidence can answer:</strong> how much of NEAR&rsquo;s value capture '
        'can be verified?</p>'
        '<div class="answer">'
        f'<p><strong>What the pre-registered tests found:</strong> net staking outflow was {M("h1a_ratio_as_written_x")}× staking rewards over 90 days, '
        f'where H1a (most staking rewards stay staked) predicted under {K("h1a_pass_below_x")}×. Only {M("h1b_coverage_count_pct")}% of the top-100 NEAR '
        f'receivers carry an exchange label, so how much NEAR reaches exchanges (H1b: less than is minted) and how much of it identified buyers absorb '
        f'(H1c: at least {K("h1c_min_pct")}%) come out as ranges too wide to settle either way. So the frozen rating rule gives no buy or avoid signal, '
        f'which carries no view on NEAR.</p>'
        f'<p><strong>Exploratory, chosen after the freeze:</strong> over 30 days the NEAR that verifiably reached NEAR&rsquo;s three Intents revenue wallets was '
        f'{M("ladder_all_wallets_pct_of_issuance", 2)}% of net issuance, of which {M("ladder_public_collectors_pct_of_issuance", 2)} points trace to public '
        f'fee collectors, {M("ladder_escrow_unshields_pct_of_issuance", 2)} arrived as releases from an escrow whose fee stream is unattested, and '
        f'{M("ladder_other_pct_of_issuance", 2)} came from one other source. So, if those three are all of NEAR&rsquo;s Intents revenue wallets, the value capture that can be '
        f'verified is a range. '
        f'This is not a valuation and not advice. <a href="#chart-ladder">See the value-capture ladder.</a></p></div>')


def has_update(ctx: Ctx) -> bool:
    return "upd_asof" in ctx.m


def kpis(ctx: Ctx) -> str:
    """Four headline figures under the lede, each labelled and linked to its card. Every number is a metric span. With the update to
    2026-11-13 committed, the first three show it and the value at the pre-registered cutoff (2026-11-04) under it; the ladder needs a
    BigQuery scan and stays at the cutoff."""
    M = ctx.M
    up = has_update(ctx)

    def fig(key: str, unit: str) -> tuple[str, str]:
        if not up:
            return f'{M(key)}{unit}', ""
        return f'{M("upd_" + key)}{unit}', f'<span class="kw">was {M(key)}{unit}</span>'

    # one row each: the label, under it the earlier value (or the window), and the figure at the right
    items = [
        (f'{M("ladder_all_wallets_pct_of_issuance", 2)}%', f'<span class="kw">30 days to {M("asof")}</span>',
         "NEAR reaching its revenue wallets, as a share of net new supply", "#chart-ladder"),
        (*fig("ic_implied_cagr_r15_x25_pct", "%"), "Revenue growth the price assumes, a year to 2031", "#chart-priced"),
        (*fig("ic_take_needed_vs_gross_x", "×"), "Take NEAR would need, as a multiple of Intents&rsquo; whole gross fee", "#chart-multiply"),
        (*fig("ic_base_coverage_2031_pct", "%"), "NEAR&rsquo;s dilution paid for in 2031, base case", "#chart-scenarios"),
    ]
    lis = "".join(f'<li class="kpi"><a class="kv" href="{h}">{v}</a><span class="kl">{l}</span>{w}</li>' for v, w, l, h in items)
    cap = (f'Where it stands, on data to {M("upd_asof")}. In grey: where it stood on {M("asof")}, the cutoff.' if up
           else f'Where it stands, on data to {M("asof")}')
    return f'<p class="kcap">{cap}</p><ul class="kpis" aria-label="Headline figures">{lis}</ul>'


def thesis_box(ctx: Ctx) -> str:
    """The answer to the title in one line, then the view in three sentences (exploratory; the line above the tabs says so once).
    The figures beside it carry the numbers.

    The words are true of the data as committed: Intents has the largest share of its peer set over 365 days, the ladder's top is between a
    seventh and a fifth of net issuance, and the growth the price assumes is above the peer set's growth over every window computed (one to
    four years), at the cutoff and at the update. If the data stop saying that, the render stops. The sentence is dated to the committed
    data, so the live Today row under it, which moves with the price, cannot contradict it."""
    M, m = ctx.M, ctx.m
    share = m["intents_share_peerset_365d_pct"]
    grows = [m[f"ic_market_cagr_{k}y_pct"] for k in (1, 2, 3, 4)]
    ok = (share > 50 and (not has_update(ctx) or m["upd_intents_share_peerset_365d_pct"] > 50) and 100 / 7 < m["ladder_all_wallets_pct_of_issuance"] < 100 / 5 and m["ic_implied_cagr_r15_x25_pct"] > max(grows)
          and (not has_update(ctx) or m["upd_ic_implied_cagr_r15_x25_pct"] > max(m[f"upd_ic_market_cagr_{k}y_pct"] for k in (1, 2, 3, 4))))
    if not ok:
        raise SystemExit("render: the view under the title says Intents led its peer set over the year, the ladder's top is about a sixth of net "
                         "issuance and the price assumes faster growth than any window in the data; the data no longer say that, so rewrite thesis_box()")
    return (
        '<div class="thesis" id="thesis">'
        '<p>NEAR Intents led its market over the past year, but NEAR&rsquo;s price asks for far more than its fees deliver. '
        'The NEAR those fees send to NEAR&rsquo;s revenue wallets equals, at most, about a sixth of net new supply.</p><p>For the fees alone to '
        f'carry the price NEAR had on {M("upd_asof") if has_update(ctx) else M("asof")}, they would have to grow faster each year to 2031 than '
        'cross-chain volume grew over any period in the data. Owning NEAR at that price is a bet on a bigger cut of those fees, or on value beyond them.</p>'
        '<p class="go"><a href="' + PAPER_NAME + '">Read our paper</a> or <a href="story.html">see it as slides</a>.</p></div>')


def record_strip(ctx: Ctx) -> str:
    """One line of small print above the tabs: what kind of analysis this is, where the predictions are scored, and that the page
    rebuilds offline. It carries no number, so it cannot disagree with the sections it links to; the order it states is the one
    freeze_order() checks against the manifest."""
    freeze_order(ctx)
    return ('<p class="fine">The view and figures above and the first two tabs are exploratory: we built them after freezing our predictions, which are '
            'scored as written in the <a href="#preregistered">track record</a>. Every chart and every committed number rebuilds offline with one command '
            '(<a href="#reproduce">the steps</a>); only the Today values are fetched live. Nothing here is investment advice.</p>')


def what_changed(ctx: Ctx) -> str:
    """Under the scorecard: what each result changed in the case, in plain words (exploratory reading, written after the score).

    It is drawn only for the outcomes it describes: H1a over its line, H1b and H1c unsettled, the rule giving no signal (check_pre_results),
    F1 and F2 inside their bands and F3 and F4 outside them, with the update to the latest full day committed. For any other state it
    draws nothing, so it can never describe a result the page does not show."""
    fw = ctx.forward
    if not fw or not has_update(ctx):
        return ""
    if [forward_word(fw, f) for f in FORWARD_IDS] != ["PASS", "PASS", "MISS", "MISS"]:
        return ""
    check_pre_results(ctx)
    M, m = ctx.M, ctx.m
    if not (m["upd_intents_share_peerset_30d_pct"] < m["intents_share_peerset_30d_pct"] and m["upd_ic_take_90d_bp"] > 4):
        raise SystemExit("render: what_changed() says Intents' 30-day share fell in the update and NEAR's 90-day take is above 4 bp; "
                         "the data no longer say that, so rewrite it")
    pf = ctx.prereg_forward
    lo_id = min(FORWARD_IDS, key=lambda f: float(pf[f]["p"]))   # the lowest and the highest of the four frozen probabilities
    hi_id = max(FORWARD_IDS, key=lambda f: float(pf[f]["p"]))
    items = (
        ("Where we were right.", 'The buyback wallet kept filling and net new supply ran at the pace we forecast (F1, F2). The case sets those two against each other.'),
        ("Where we were wrong in NEAR&rsquo;s favour.", f'We expected NEAR&rsquo;s take to fall back below {ctx.K("f3_max_bp")} bp, and it did not (F3). '
                                                         f'The headline figures use the measured {M("upd_ic_take_90d_bp")} bp.'),
        ("Where we were wrong against it.", 'We expected Intents to keep over half its peer set&rsquo;s volume, and THORChain out-traded it (F4). '
                                            f'The 30-day share is {M("upd_intents_share_peerset_30d_pct")}% in the update.'),
        ("Supply.", f'More NEAR left staking than rewards added (H1a): the NEAR outside the pools grew by {M("ic_float_change_vs_net_supply_x")}× '
                    'the net new supply. Whether it was sold, H1b leaves open.'),
        ("Still open.", 'Labels cover too few exchange addresses to settle H1b and H1c, so the frozen rule gives no signal and the view rests on the investment case.'),
        ("Our odds.", f'We gave the four one-week forecasts odds of <span data-p="{lo_id}">{esc(pf[lo_id]["p"])}</span> to '
                      f'<span data-p="{hi_id}">{esc(pf[hi_id]["p"])}</span>, and two came true. Four is too few to re-fit, so the longer-dated odds stay as frozen.'),
    )
    lis = "".join(f"<li><strong>{a}</strong> {b}</li>" for a, b in items)
    return (f'<section id="what-changed" aria-labelledby="wc-h"><h3 id="wc-h">What the results changed</h3>'
            f'<p class="note">Our reading, written after the score (exploratory). The headline figures on the first screen already include the week the '
            f'forecasts covered: they run to {M("upd_asof")}.</p><ul class="took">{lis}</ul></section>')


def all_cards() -> dict[str, tuple[str, object]]:
    """Every card: id -> (label in the contents, builder)."""
    return {cid: (lab, fn) for cid, lab, fn in FWD_CARDS + PRE_CARDS + EXP_CARDS}


def side_nav() -> str:
    """The contents: the page sections, then the card links in the page's three groups (the case, the pre-registered tests in a ul.toc,
    the supporting evidence in a ul.toc). On a wide screen it is a sticky sidebar; on a narrow one only the page sections show."""
    cards = all_cards()

    def links(ids) -> str:
        return "".join(f'<li><a href="#chart-{cid}">{esc(cards[cid][0])}</a></li>' for cid in ids)

    secs = "".join(f'<li><a href="#{sid}">{lab}</a></li>' for sid, lab in
                   (("thesis", "The long-term view"), ("scorecard", "Track record"), ("about", "About the data"), ("not-computed", "Not computed here"), ("reproduce", "Reproduce"), ("limits", "Limits")))
    return (f'<nav class="side" aria-label="Contents"><h2 class="sr">Contents</h2>'
            f'<p class="sidecap">Page</p><ul class="toc-more">{secs}</ul>'
            f'<p class="sidecap">The case</p><ul class="toc-more">{links(CASE_IDS)}</ul>'
            f'<p class="sidecap">Supporting evidence</p><ul class="toc">{links(EVID_IDS)}</ul>'
            f'<p class="sidecap">Track record</p><ul class="toc">{links(id_ for id_, _, _ in PRE_CARDS)}</ul></nav>')


LIVE_JS = """
(function () {
  "use strict";
  var A = __ASSUMPTIONS__;
  function el(id) { return document.getElementById(id); }
  function put(id, text) { var e = el(id); if (e) { e.textContent = text; } }
  function num(x, d) { return x.toLocaleString("en-US", {minimumFractionDigits: d, maximumFractionDigits: d}); }
  function getJSON(url, init) {
    return fetch(url, init).then(function (r) { if (!r.ok) { throw new Error("HTTP " + r.status); } return r.json(); });
  }
  function complete(chart) {
    var today = Math.floor(Date.now() / 86400000) * 86400;
    return chart.filter(function (p) { return today > p[0]; });
  }
  function sumLast(points, n) { return points.slice(-n).reduce(function (a, p) { return a + p[1]; }, 0); }
  function run() {
    var rpc = {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({jsonrpc: "2.0", id: "live",
      method: "query", params: {request_type: "view_account", finality: "final", account_id: "buybacks.multisignature.near"}})};
    Promise.allSettled([
      getJSON("https://api.coingecko.com/api/v3/simple/price?ids=near&vs_currencies=usd&include_market_cap=true"),
      getJSON("https://api.llama.fi/summary/fees/near-intents?dataType=dailyRevenue"),
      getJSON("https://api.llama.fi/summary/dexs/near-intents?dataType=dailyVolume"),
      getJSON("https://rpc.mainnet.fastnear.com", rpc)
    ]).then(function (res) {
      var mcap = null, rev = null, vol = null;
      if (res[0].status === "fulfilled") { mcap = res[0].value.near.usd_market_cap; put("lv-mcap", "$" + num(mcap / 1e9, 2) + "B"); }
      else { put("lv-mcap", "\\u2013"); }
      if (res[1].status === "fulfilled") { rev = complete(res[1].value.totalDataChart); put("lv-rev30", "$" + num(sumLast(rev, 30) / 1e6, 2) + "M"); }
      else { put("lv-rev30", "\\u2013"); }
      if (res[2].status === "fulfilled") { vol = complete(res[2].value.totalDataChart); }
      if (rev && vol) { put("lv-take", num(sumLast(rev, 30) / sumLast(vol, 30) * 1e4, 2) + " bp"); } else { put("lv-take", "\\u2013"); }
      if (res[3].status === "fulfilled") { put("lv-bb", num(Number(res[3].value.result.amount) / 1e30, 3) + "M NEAR"); }
      else { put("lv-bb", "\\u2013"); }
      if (mcap && rev) {
        var years = (A.end - Date.now()) / (365.25 * 86400000);
        var need = mcap * Math.pow(1 + A.r / 100, years) * A.supply / A.x;
        var annual = sumLast(rev, 90) * 365 / 90;
        put("lv-implied", num((Math.pow(need / annual, 1 / years) - 1) * 100, 1) + "% a year");
      } else { put("lv-implied", "\\u2013"); }
    });
  }
  run();
})();
"""


def live_script(ctx: Ctx) -> str:
    """The page's one script: the live check. It reads four public, keyless sources in the reader's browser and writes text only
    (textContent). The assumptions are the committed ones, so the recomputed growth uses the same formula as the figures."""
    m = ctx.m
    assumptions = json.dumps({"r": m["ic_base_r_pct"], "x": m["ic_base_x"], "supply": m["ic_supply_factor_x"], "end": 1951516800000})
    return "<script>" + LIVE_JS.replace("__ASSUMPTIONS__", assumptions) + "</script>"


UPDATE_ROWS = (   # (label, committed key, update key, unit, decimals or None for the metric's own)
    ("Growth the price assumes, a year to 2031", "ic_implied_cagr_r15_x25_pct", "upd_ic_implied_cagr_r15_x25_pct", "%"),
    ("Take NEAR would need, as a multiple of Intents&rsquo; whole gross fee", "ic_take_needed_vs_gross_x", "upd_ic_take_needed_vs_gross_x", "×"),
    ("Base case: NEAR&rsquo;s dilution paid for in 2031", "ic_base_coverage_2031_pct", "upd_ic_base_coverage_2031_pct", "%"),
    ("Bull case: share of the revenue the price assumes", "ic_bull_vs_required_pct", "upd_ic_bull_vs_required_pct", "%"),
    ("Coverage of dilution today (P3&rsquo;s quantity, 90 days)", "p3_quantity_90d_asof_pct", "upd_p3_quantity_90d_pct", "%"),
    ("Captured revenue, 90 days at an annual rate", "ic_rev_90d_ann_m", "upd_ic_rev_90d_ann_m", "$M"),
    ("NEAR&rsquo;s captured take, 90 days", "ic_take_90d_bp", "upd_ic_take_90d_bp", " bp"),
    ("Intents&rsquo; share of the peer set, 30 days", "intents_share_peerset_30d_pct", "upd_intents_share_peerset_30d_pct", "%"),
    ("Intents&rsquo; share of the peer set, 90 days", "ic_share_90d_pct", "upd_ic_share_90d_pct", "%"),
    ("Intents&rsquo; share of the peer set, 365 days", "intents_share_peerset_365d_pct", "upd_intents_share_peerset_365d_pct", "%"),
    ("Peer-set volume, growth over the last year", "ic_market_cagr_1y_pct", "upd_ic_market_cagr_1y_pct", "%"),
    ("NEAR market cap", "mcap_usd_b", "upd_mcap_usd_b", "$B"),
    ("NEAR&rsquo;s market cap ÷ Intents&rsquo; gross fees, 365 days", "ic_near_mcap_to_intents_fees_x", "upd_ic_near_mcap_to_intents_fees_x", "×"),
)


def update_table(ctx: Ctx) -> str:
    """The case carried to 2026-11-13 (exploratory): each figure at the pre-registered cutoff and at the update, from the same code."""
    if not has_update(ctx):
        return ""
    M, m = ctx.M, ctx.m
    thor_before = next(p["vol_30d_b"] for p in m["peers"] if p["slug"] == "thorchain-dex")
    holds = (m["upd_ic_implied_cagr_r15_x25_pct"] > max(m[f"upd_ic_market_cagr_{k}y_pct"] for k in (1, 2, 3, 4))
             and m["upd_ic_take_needed_vs_gross_x"] > 1 and m["upd_mcap_usd_b"] < m["mcap_usd_b"]
             and m["upd_ic_rev_90d_ann_m"] > m["ic_rev_90d_ann_m"] and m["upd_intents_share_peerset_30d_pct"] < m["intents_share_peerset_30d_pct"]
             and m["upd_thorchain_volume_30d_b"] > thor_before)
    if not holds:
        raise SystemExit("render: the update note says the thesis holds, the price fell, revenue rose and Intents' share fell as THORChain's "
                         "volume rose; the update no longer says that, so rewrite update_table()")

    def val(key: str, unit: str) -> str:
        if unit.startswith("$"):
            return f'${M(key)}{unit[1:]}'
        return f'{M(key)}{unit}'

    rows = "".join(f'<tr><td class="t">{lab}</td><td>{val(a, u)}</td><td>{val(b, u)}</td></tr>' for lab, a, b, u in UPDATE_ROWS)
    return (
        '<div class="update" id="update"><h3 class="updh">The case carried to the latest full day</h3>'
        f'<p class="note">The charts above stop at {M("asof")}, the pre-registered cutoff. The same code on DefiLlama, CoinGecko and Nearblocks '
        f'data fetched on 2026-11-14 runs to {M("upd_asof")}, and the conclusion stands: the price still assumes faster growth than any window in '
        f'the data, and NEAR would still need more than Intents&rsquo; whole gross fee. The gap narrowed because NEAR&rsquo;s price fell and revenue '
        f'rose. Intents&rsquo; share of the peer set fell too, as THORChain&rsquo;s volume rose ({M("upd_thorchain_share_peerset_30d_pct")}% of the '
        f'set over 30 days).</p>'
        f'<div class="tablewrap" role="region" aria-label="The case at the cutoff and at the update" tabindex="0"><table><caption>The case at the cutoff '
        f'and at the update</caption><thead><tr><th class="txt">Figure</th><th>{M("asof")}</th><th>{M("upd_asof")}</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div></div>')


def live_panel(ctx: Ctx) -> str:
    """The Today row under the headline figures: values fetched in the reader's browser, each beside the committed figure.
    How it is fetched, and that it is exploratory, is said once in the Method tab (about_data)."""
    M = ctx.M
    if has_update(ctx):
        d = M("upd_asof")
        items = (
            ("lv-implied", "Growth the price assumes", f'was {M("upd_ic_implied_cagr_r15_x25_pct")}% a year'),
            ("lv-mcap", "NEAR market cap", f'was ${M("upd_mcap_usd_b")}B'),
            ("lv-rev30", "Intents revenue, 30 days", f'was ${M("upd_intents_rev_30d_m")}M'),
            ("lv-take", "NEAR&rsquo;s take, 30 days", f'was {M("upd_take_captured_bp_30d")} bp'),
            ("lv-bb", "Buyback wallet", f'{M("buyback_wallet_near_m")}M NEAR at the freeze'),
        )
        cap = f'Today, read live in the browser. In grey: {d}.'
    else:
        items = (
            ("lv-implied", "Growth the price assumes", f'{M("asof")}: {M("ic_implied_cagr_r15_x25_pct")}% a year'),
            ("lv-mcap", "NEAR market cap", f'2026-11-05: ${M("mcap_usd_b")}B'),
            ("lv-rev30", "Intents revenue, 30 days", f'{M("asof")}: ${M("intents_rev_30d_m")}M'),
            ("lv-take", "NEAR&rsquo;s take, 30 days", f'{M("asof")}: {M("take_captured_bp_30d")} bp'),
            ("lv-bb", "Buyback wallet", f'At the freeze: {M("buyback_wallet_near_m")}M NEAR'),
        )
        cap = 'Today, read live in the browser'
    lis = "".join(f'<li><span class="tl">{lab}</span><output id="{oid}">&hellip;</output><span class="tw">{was}</span></li>' for oid, lab, was in items)
    return f'<div class="today" id="live"><p class="todaycap">{cap}</p><ul class="todayrow" aria-label="Today&rsquo;s values">{lis}</ul></div>'


AUTHORS = "Victor Song and Tharun Ekambaram"


def gauge(ctx: Ctx) -> str:
    """The cover's one graphic: a bar as wide as the page that stands for all of NEAR's net new supply over the window, filled to the
    share matched by the NEAR that reached the revenue wallets, with the part traced to public fee collectors marked inside it.
    The widths are the two metrics; the render stops if they are not a part and a whole."""
    M, m = ctx.M, ctx.m
    whole, part = m["ladder_all_wallets_pct_of_issuance"], m["ladder_public_collectors_pct_of_issuance"]
    if not 0 < part < whole < 100:
        raise SystemExit("render: the cover's bar draws the traced part inside the whole, inside all of net new supply; the data no longer fit that")
    return (
        '<div class="gauge">'
        f'<p class="gauge-head"><span class="gauge-num">{M("ladder_all_wallets_pct_of_issuance", 2)}%</span> '
        '<span class="gauge-lab">of NEAR&rsquo;s net new supply is matched by the NEAR that Intents fees send to its revenue wallets</span></p>'
        f'<div class="gauge-track" aria-hidden="true"><div class="gauge-fill" style="width:{whole:.2f}%"><div class="gauge-core" style="width:{100 * part / whole:.2f}%"></div></div></div>'
        f'<p class="gauge-foot"><span><span class="gauge-key"></span>{M("ladder_public_collectors_pct_of_issuance", 2)} points of it trace on chain to public fee collectors</span>'
        f'<span>The whole bar is all net new supply, 30 days to {M("asof")}</span></p></div>')


def header(ctx: Ctx, eyebrow: str = "NEAR Hackathon 2026, Investment Thesis track", fine: str = "") -> str:
    """The cover: the question, what the long-term case rests on, who wrote it and for what, and a small cue to scroll. Nothing else.
    (The bar that stood here, gauge() above, is no longer drawn; its two figures are in the ledger under the cover.)
    The slides page opens with the same cover, under its own first line and with one line of small print (fine).

    The subtitle says what the case rests on and does not say that it succeeds; the thesis under the cover says how far the price is
    ahead of the fees."""
    answer_line(ctx)   # drawn in the track record tab; called here so that the first screen is not drawn either once the data stop supporting it
    thesis_box(ctx)    # the same for the view under the cover: its guard covers the subtitle's claim that Intents led its market
    small = f'<p class="fine">{fine}</p>' if fine else ""
    return (
        f'<header class="top"><p class="eyebrow">{esc(eyebrow)}</p>'
        f'<h1>Can NEAR&rsquo;s Intents business grow into its dilution?</h1>'
        '<p class="sub">The long-term case for NEAR rests on Intents.</p>'
        f'<p class="byline">{esc(AUTHORS)}</p>'
        f'{small}<p class="scrollcue" aria-hidden="true">Scroll</p></header>')


def brief(ctx: Ctx) -> str:
    """Under the cover: the thesis in four sentences, with the headline figures and today's values beside it."""
    return (f'<section id="brief" aria-labelledby="brief-h"><h2 id="brief-h">Our thesis</h2>'
            f'{thesis_box(ctx)}{kpis(ctx)}{live_panel(ctx)}</section>')


DOCUMENTS = (("The full thesis", "THESIS.md"), ("Read me", "README.md"), ("Glossary", "docs/glossary.md"), ("Pre-registration", "PREREG.md"),
             ("Addendum to the pre-registration", "PREREG-ADDENDUM.md"))


def about_data(ctx: Ctx) -> str:
    """The Method tab's first section: how the page is built, the windows, data date, fingerprint and freeze, and the documents."""
    M = ctx.M
    freeze_stamp, _ = freeze_order(ctx)
    docs = "".join(f'<li><a href="{esc(gh(p))}">{esc(lab)}</a></li>' for lab, p in DOCUMENTS)
    return (
        f'<section id="about" aria-labelledby="about-h"><h2 id="about-h">About the data</h2>'
        f'<p class="lede">A token flow statement for NEAR that anyone can re-run. <code>make site</code> runs <code>python3 -m pipeline.compute</code> and '
        f'<code>python3 -m pipeline.render</code> in one command, rebuilding every number and chart from the raw snapshots in <code>data/raw/</code>, offline. Each chart carries the query behind it and the exact numbers it plots; '
        f'the steps to check one are under <a href="#reproduce">Reproduce</a>.</p>'
        f'<dl class="meta">'
        f'<dt>Windows</dt><dd>Value capture: the 30 days to {M("asof")}. Supply: the 90 days {window_text(ctx, 90)}.</dd>'
        f'<dt>Data as of</dt><dd>{M("asof")} (<code>data/metrics.json</code>). Revenue-wallet window {M("revwallets_window")}. NEAR RPC block {M("rpc_block")}.</dd>'
        f'<dt>Data fingerprint</dt><dd><code data-fingerprint="{esc(ctx.fingerprint)}">{esc(ctx.fingerprint)}</code>, the first 16 hex of the SHA-256 of <code>data/MANIFEST.json</code>, '
        f'which pins every raw snapshot.</dd>'
        f'<dt>Pre-registration</dt><dd><code>PREREG.md</code> SHA-256 <code data-prereg="{esc(ctx.prereg_sha)}">{esc(ctx.prereg_sha[:16])}…</code>, frozen at git tag '
        f'<code>{FREEZE_TAG}</code> (commit <code>{FREEZE_COMMIT}</code>, {FREEZE_UTC} UTC), before the first BigQuery result the repository records '
        f'({freeze_stamp} in <code>data/MANIFEST.json</code>); the order rests on the author&rsquo;s own commit and manifest times, and GitHub&rsquo;s activity log dates the push of the freeze commit to 2026-11-05 22:53:33 UTC. '
        f'<a href="{esc(gh("PREREG.md"))}#{PREREG_ANCHOR}">&ldquo;What we had already seen&rdquo;</a> in that file lists the data already in hand.</dd></dl>'
        f'<p class="note">The Today row is exploratory. The browser fetches it when the page opens, from CoinGecko, DefiLlama and NEAR&rsquo;s public RPC '
        f'(no keys). It recomputes the growth the price assumes from today&rsquo;s market cap and the last 90 days of captured revenue, keeping the committed '
        f'supply path ({M("ic_supply_factor_x")}× to 2031), a {M("ic_base_r_pct")}% required return and a {M("ic_base_x")}× multiple. Nothing else on the page changes.</p>'
        f'<p class="note">Documents:</p><ul class="docs">{docs}</ul></section>')


# ------------------------------------------------------------------ line breaks
# The page is built as a few very long lines (a chart card is tens of thousands of characters), which no diff or file viewer
# shows well. break_lines puts a newline only where the browser ignores whitespace, so the rendered page does not change:
#   * between two block-level tags (a closing tag and the next opening tag, or two opening tags): p, div, ul, li, table parts ...
#   * between the child elements of a chart <svg> (rect, line, path, text, circle, g, title, desc), never inside a <text>
#   * inside the path data of a chart line, which the SVG parser reads as it reads a space (before a command letter)
# It never touches the inside of a <pre>, a <text>, running text or an inline element. tests/test_render.py parses the page with
# and without the breaks and requires the same elements, attributes and text, and the same <pre> bytes.
BLOCK_TAGS = ("p", "div", "ul", "ol", "li", "dl", "dt", "dd", "h1", "h2", "h3", "h4", "h5", "h6", "section", "details", "summary", "figure",
              "figcaption", "table", "thead", "tbody", "tr", "td", "th", "caption", "nav", "header", "footer", "main")
_B = "|".join(BLOCK_TAGS)
_BLOCK_CLOSE_OPEN = re.compile(rf"(</(?:{_B})>)(?=<(?:{_B})[\s>])")
_BLOCK_OPEN_OPEN = re.compile(rf"(<(?:{_B})(?:\s[^<>]*)?>)(?=<(?:{_B})[\s>])")
_PRE_BLOCK = re.compile(r"<pre\b.*?</pre>|<script>.*?</script>", re.S)
_CHART_SVG = re.compile(r'<svg class="svg".*?</svg>', re.S)
_SVG_CHILD = re.compile(r">(?=<(?:text|line|path|circle|rect|g|title|desc)[\s>/])")
_PATH_DATA = re.compile(r'( d=")([^"]{400,})(")')
PATH_LINE = 360   # a chart line's path data is wrapped before the first command letter after this many characters


def _wrap_path(m: "re.Match[str]") -> str:
    out, cur = [], ""
    for cmd in re.findall(r"[A-Za-z][^A-Za-z]*", m.group(2).replace("\n", "")):   # without the breaks of an earlier pass: idempotent
        if len(cur) >= PATH_LINE:
            out.append(cur)
            cur = ""
        cur += cmd
    out.append(cur)
    return m.group(1) + "\n".join(out) + m.group(3)


def _break_markup(seg: str) -> str:
    seg = _BLOCK_CLOSE_OPEN.sub(r"\1\n", seg)
    seg = _BLOCK_OPEN_OPEN.sub(r"\1\n", seg)
    return _CHART_SVG.sub(lambda m: _PATH_DATA.sub(_wrap_path, _SVG_CHILD.sub(">\n", m.group(0))), seg)


def break_lines(page: str) -> str:
    """The page with newlines added where HTML and SVG ignore whitespace (see above). Pure and idempotent."""
    out: list[str] = []
    pos = 0
    for m in _PRE_BLOCK.finditer(page):
        out += [_break_markup(page[pos:m.start()]), m.group(0)]
        pos = m.end()
    out.append(_break_markup(page[pos:]))
    return "".join(out)


LADDER_HISTORY = (
    f'<details class="more"><summary>When the ladder was developed</summary><p class="note">The headline ladder was developed alongside the pre-registered tests: a first split of the buyback wallet&rsquo;s inflows into two collectors and single-use accounts funded from one account was committed on 2026-11-06 03:00 UTC, '
    f'the ladder&rsquo;s code and escrow dataset on 2026-11-06 23:19 UTC, before the H1b and H1c results (2026-11-06 23:23 UTC) and the H1a-as-written result (2026-11-06 23:49 UTC) were committed, '
    f'and it became the thesis headline on 2026-11-07 00:21 UTC (<a href="{esc(gh("PREREG-ADDENDUM.md"))}">addendum</a>, 2026-11-08 02:03 UTC entry, item 1).</p></details>')


# The tab icon: an inline SVG (a data: URI, so nothing is loaded): three bars.
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E"
           "%3Crect width='16' height='16' rx='3' fill='%2316150f'/%3E%3Cpath fill='%23f1efe7' d='M3.5 9h2v3.5h-2zM7 6h2v6.5H7zM10.5 3.5h2v9h-2z'/%3E%3C/svg%3E")


def case_lead(ctx: Ctx) -> str:
    """The lead of the Investment case tab: its main points, each figure a metric span (the charts in this tab stop at the cutoff)."""
    M = ctx.M
    return ('<p class="note">The NEAR that Intents sends to NEAR&rsquo;s revenue wallets is small next to what the price assumes. Over 30 days it equalled '
            f'{M("ladder_all_wallets_pct_of_issuance", 2)}% of net new supply, and only {M("ladder_public_collectors_pct_of_issuance", 2)} points of that trace to '
            f'public fee collectors. For those fees alone to carry NEAR&rsquo;s price, they would have to grow {M("ic_implied_cagr_r15_x25_pct")}% a year to 2031. '
            f'With the market growing at last year&rsquo;s pace and Intents at its best share, that would take {M("ic_take_needed_vs_gross_x")}× Intents&rsquo; whole '
            f'gross fee. In the base case the fees pay for {M("ic_base_coverage_2031_pct")}% of NEAR&rsquo;s dilution in 2031.</p>')


def evidence_lead(ctx: Ctx) -> str:
    """The lead of the Supporting evidence tab. The figures are in the group leads under it."""
    return ('<p class="note">Intents leads its market, but most of its fees go to others, NEAR&rsquo;s supply keeps growing and usage is down. This is context for '
            'the case, also exploratory: picked after the predictions were frozen. None of it is a test, and none of it feeds or changes a hypothesis, '
            'threshold, probability or the rating rule.</p>')


def group_lead(ctx: Ctx, head: str) -> str:
    """One or two sentences under a group heading of the Supporting evidence tab: what its charts show, each figure a metric span.
    The words are checked against the data they describe; if the data stop saying it, the render stops."""
    M, S, m = ctx.M, ctx.S, ctx.m
    if head == "Market and peers":
        return (f'Intents had {M("intents_share_peerset_30d_pct")}% of its peer set&rsquo;s reported volume over 30 days and '
                f'{M("intents_share_peerset_365d_pct")}% over a year. NEAR&rsquo;s market cap is {M("ic_near_mcap_to_intents_fees_x")}× the gross fees Intents charged '
                f'in a year; THORChain&rsquo;s is {M("ic_peer_thorchain_mcap_to_fees_x")}× its own and Chainflip&rsquo;s {M("ic_peer_chainflip_mcap_to_fees_x")}×.')
    if head == "Revenue and the take rate":
        if not (m["escrow_share_buyback_2026_09_pct"] > 50 and m["escrow_share_buyback_2026_10_pct"] > 50
                and m["take_b3_bb_explicit_bp"] > m["take_b1_bb_explicit_bp"]):
            raise SystemExit("render: the lead of 'Revenue and the take rate' says the explicit fee rose and the escrow supplied more than half of the "
                             "buyback wallet's NEAR from September; the data no longer say that, so rewrite group_lead()")
        return (f'NEAR captured ${S("intents_monthly.2026-10.rev_m")}M in October, {S("intents_monthly.2026-10.captured_bp")} bp of Intents&rsquo; reported volume. '
                f'Its explicit fee inside 1Click rose from {M("take_b1_bb_explicit_bp")} bp to {M("take_b3_bb_explicit_bp")} bp over the window. From September the '
                f'escrow supplied more than half of the buyback wallet&rsquo;s NEAR ({M("escrow_share_buyback_2026_09_pct")}% that month).')
    if head == "Who else gets paid":
        return (f'Partners&rsquo; listed fees were {M("partners_kept_vs_near_rev_floor_x")}× to {M("partners_kept_vs_near_rev_high_x")}× NEAR&rsquo;s whole captured '
                f'revenue. SwapKit alone routed {M("swapkit_vol_share_pct")}% of 1Click volume and paid NEAR ${M("swapkit_buyback_fees_usd", 0)} in explicit fees '
                'over 30 days.')
    if head == "Supply and dilution":
        return (f'Supply grew {M("net_supply_growth_365d_pct")}% in a year, about {M("net_issuance_near_per_day_30d_k")}K NEAR a day net. On the rating rule&rsquo;s '
                f'path it grows {M("fwd_supply_growth_5y_pct")}% more by 2031 if HSP-029&rsquo;s cut takes effect and {M("fwd_supply_growth_5y_no_hsp029_pct")}% if not.')
    if head == "Network usage":
        return (f'Daily active accounts averaged {M("active_accounts_30d_k")}K over 30 days, {M("active_accounts_30d_yoy_pct")}% on a year earlier. '
                f'{M("usage_bq_tg_share_of_signer_drop_pct")}% of that fall is one wallet app&rsquo;s Telegram accounts, and the number of contracts called each '
                'day did not fall.')
    raise SystemExit(f"render: no lead is written for the group {head!r}; add one to group_lead()")


def track_lead(ctx: Ctx) -> str:
    """The lead of the Track record tab: what was fixed, and how it came out, in the words the scorecard under it uses."""
    M, K = ctx.M, ctx.K
    check_pre_results(ctx)
    fw = ctx.forward
    if fw:
        words = [forward_word(fw, f) for f in FORWARD_IDS]
        npass, nmiss = words.count("PASS"), words.count("MISS")
        nns = len(FORWARD_IDS) - npass - nmiss
        forecasts = (f'Of the four one-week forecasts, <span data-f="@count.PASS" data-scale="1">{npass}</span> came true and '
                     f'<span data-f="@count.MISS" data-scale="1">{nmiss}</span> did not'
                     + (f', and <span data-f="@count.not scorable" data-scale="1">{nns}</span> could not be scored.' if nns else '.'))
    else:
        forecasts = f'The four one-week forecasts are scored after {esc(sf.SCORE_NOT_BEFORE.strftime("%Y-%m-%d %H:%M UTC"))}.'
    return (f'<p class="note">We fixed three hypotheses, a rating rule and seven dated forecasts in the <a href="{esc(gh("PREREG.md"))}">pre-registration</a> '
            'before the first BigQuery result the repository records, so that the numbers could not be bent to fit a story afterwards. One hypothesis went against '
            f'us: net staking outflow was {M("h1a_ratio_as_written_x")}× staking rewards, where we predicted under {K("h1a_pass_below_x")}×. Two could not be settled, '
            f'because only {M("h1b_coverage_count_pct")}% of the top-100 receivers carry an exchange label, so the frozen rule gives no signal. {forecasts} '
            'Everything in this tab is pre-registered except the list headed &ldquo;What the results changed&rdquo;; later method choices are dated in the '
            f'<a href="{esc(gh("PREREG-ADDENDUM.md"))}">addendum</a>.</p>')


_CHART_HEIGHT = re.compile(r'<svg class="svg" viewBox="0 0 [0-9.]+ ([0-9.]+)"')


def lay_out(ids: tuple[str, ...], cards: dict[str, tuple[str, object]], ctx: Ctx) -> str:
    """The cards of one group, in order, split so that the two columns come out as close in height as the order allows.
    (The stylesheet then lets the cards of the shorter column grow by the small difference, so both columns end on one line.)

    A wide card (WIDE_CARDS) takes a full row. The cards between two wide ones go into two columns, split where the columns come out
    closest in height; the height of a card is taken from its chart (the first, wide drawing) plus a constant for its title, caption and
    key figures. A card left on its own takes a full row. The order in the markup is the figure order, whatever the split."""
    out: list[str] = []
    run: list[str] = []

    def height(markup: str) -> float:
        m = _CHART_HEIGHT.search(markup)
        return (float(m.group(1)) if m else 300.0) + 260.0

    def flush() -> None:
        if len(run) == 1:
            out.append(run[0].replace('<section class="card"', '<section class="card span2"', 1))
        elif run:
            hs = [height(x) for x in run]
            k = min(range(1, len(run)), key=lambda i: abs(sum(hs[:i]) - sum(hs[i:])))
            out.append(f'<div class="cols"><div class="col">{"".join(run[:k])}</div><div class="col">{"".join(run[k:])}</div></div>')
        run.clear()

    for cid in ids:
        markup = cards[cid][1](ctx)
        if cid in WIDE_CARDS:
            flush()
            out.append(markup)
        else:
            run.append(markup)
    flush()
    return "".join(out)


def build_page(ctx: Ctx, breaks: bool = True) -> str:
    """The whole page. breaks=False leaves the body on a few very long lines (tests/test_render.py compares the two)."""
    cards = all_cards()
    pre = lay_out(tuple(c for c, _, _ in PRE_CARDS), cards, ctx)
    fwd = lay_out(CASE_IDS, cards, ctx)
    exp = "".join(f'<p class="gridhead">{esc(head)}</p><p class="gridlead">{keep_tail(group_lead(ctx, head))}</p>' + lay_out(ids, cards, ctx)
                  for head, ids in EVIDENCE)
    body = (
        f'<a class="skip" href="#main">Skip to the content</a>{header(ctx)}<div class="wrap">{side_nav()}'
        f'<main id="main">{brief(ctx)}{tailed(record_strip(ctx))}'
        f'<div class="tabs"><nav class="tabbar" aria-label="Sections"><a href="#forward-view" data-tab="forward-view">Investment case</a>'
        f'<a href="#exploratory" data-tab="exploratory">Supporting evidence</a><a href="#preregistered" data-tab="preregistered">Track record</a>'
        f'<a href="#method" data-tab="method">Method and limits</a></nav>'
        f'<section id="forward-view" class="panel" aria-labelledby="fwd-h"><h2 id="fwd-h">The investment case</h2>'
        f'{tailed(case_lead(ctx))}'
        f'<div class="grid">{fwd}</div>{update_table(ctx)}{LADDER_HISTORY}</section>'
        f'<section id="exploratory" class="panel" aria-labelledby="exp-h"><h2 id="exp-h">Supporting evidence</h2>'
        f'{tailed(evidence_lead(ctx))}'
        f'<div class="grid">{exp}</div></section>'
        f'<section id="preregistered" class="panel" aria-labelledby="pre-h"><h2 id="pre-h">Track record: what we predicted, and what happened</h2>'
        f'{tailed(track_lead(ctx))}'
        f'<details class="readmore"><summary>The questions and the pre-registered answer</summary>{answer_line(ctx)}</details>'
        f'{scorecard(ctx)}{what_changed(ctx)}<div class="grid">{pre}</div></section>'
        f'<div id="method" class="panel">{tailed(about_data(ctx))}{not_computed(ctx)}{reproduce(ctx)}{limits(ctx)}</div></div></main>'
        f'<footer><p><strong>Research only.</strong> Nothing here is investment advice, an offer or a recommendation. '
        f'MIT licence (<a href="{esc(gh("LICENSE"))}">terms</a>). <a href="{esc(gh("pipeline/render.py"))}">How this page is built</a>.</p></footer></div>'
        f'{live_script(ctx)}')
    head = (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n<meta name="color-scheme" content="light dark">\n'
        '<title>NEAR flow statement dashboard</title>\n'
        '<meta name="description" content="A long-term investment thesis for NEAR: what its price assumes, what the evidence supports, scenarios and signposts, on a pre-registered, re-runnable token flow statement. The pre-registered question is how much NEAR flows to exchanges and how much of that '
        'identified buyers absorb; the question the evidence can answer is how much of NEAR&#x27;s value capture can be verified. '
        'Every chart shows the query behind it and the exact numbers it plots.">\n'
        f'<link rel="icon" href="{FAVICON}">\n'
        f"<style>\n{css()}\n</style>\n</head>\n")
    return f"{head}<body>\n{break_lines(body) if breaks else body}\n</body>\n</html>\n"


# ------------------------------------------------------------------ the story page (site/story.html): the case in six charts, for the demo
STORY_NAME = "story.html"
PAPER_NAME = "NEAR_Long_Thesis.pdf"   # the written paper: a file placed in site/ by hand, linked from the first screen, not built here
STORY_CARDS = ("ladder", "priced", "multiply", "scenarios", "fwdcov", "signposts")   # in the order the story tells them
STORY_CSS = """
.story main{max-width:980px;margin:0 auto;padding:0 20px}
.story .slide{min-height:100vh;display:flex;flex-direction:column;justify-content:center;padding:36px 0;border-bottom:1px solid var(--grid)}
.story .card{border:0;background:transparent;padding:0;margin:0}
.story .sn,.story .cardfoot,.story .keyfigs,.story .tablewrap,.story figcaption,.story .cardtop a,.story .notes{display:none}
.story .card h3{font-size:clamp(1.25rem,2.6vw,1.85rem);line-height:1.25;margin:.7rem 0 1.1rem}
.story .step{margin:0;font-size:.9375rem;font-weight:600;color:var(--muted)}
.story .fignum{display:none}
.story .badge{position:static;width:auto;height:auto;overflow:visible;clip:auto;font-size:.875rem;color:var(--muted)}
.story .end p{font-size:clamp(1.05rem,1.9vw,1.3rem);max-width:none;margin:.5rem 0}
.story header.top{padding-left:max(20px,calc((100% - 940px) / 2));padding-right:max(20px,calc((100% - 940px) / 2))}
.story header.top .fine{margin:1.8rem 0 0;font-size:.875rem;max-width:none}
.story .end ul{font-size:clamp(1rem,1.7vw,1.2rem);padding-left:1.2rem}
.story .end li{max-width:none;margin:.35rem 0}
"""


def build_story(ctx: Ctx) -> str:
    """A second page with the same charts and no detail: one chart per screen, for recording the demo. Same data, same spans;
    every link points back into the dashboard."""
    M = ctx.M
    check_pre_results(ctx)
    by_id = {cid: fn for cid, _, fn in PRE_CARDS + EXP_CARDS + FWD_CARDS}
    steps = ("What reaches NEAR today", "What the price assumes", "What would have to give", "Three futures from the data",
             "How uncertain it is", "What to watch")
    cover = header(ctx, eyebrow="Built at NEAR HACKATHON 2026, Investment Thesis track",
                   fine="An exploratory analysis, built after our predictions were frozen. They are scored on the last slide.")
    slides = "".join(f'<section class="slide"><p class="step">{i + 1}. {esc(steps[i])}</p>{by_id[cid](ctx)}</section>'
                     for i, cid in enumerate(STORY_CARDS))
    update_line = ''
    if has_update(ctx):
        update_line = (f'<li>Carried to {M("upd_asof")} with the same code: the price assumes {M("upd_ic_implied_cagr_r15_x25_pct")}% a year, NEAR would need '
                       f'{M("upd_ic_take_needed_vs_gross_x")}× Intents&rsquo; whole gross fee, and the base case pays for {M("upd_ic_base_coverage_2031_pct")}% '
                       f'of the dilution in 2031.</li>')
    fw = ctx.forward
    if fw:
        words = [forward_word(fw, f) for f in FORWARD_IDS]
        forecast_line = (f'Forward tests, scored 2026-11-14: {words.count("PASS")} of the four frozen predictions came true and {words.count("MISS")} did not; '
                         f'the Monte Carlo&rsquo;s forecasts are dated in the addendum and resolve from 2027.')
    else:
        forecast_line = 'Forecasts are dated in the addendum and will be scored as written, whichever way they go.'
    end = (
        '<section class="slide end"><p class="step">The view</p>'
        f'<p class="big" style="font-size:clamp(1.3rem,2.6vw,1.8rem);font-weight:650">Intents led its market over the year to {M("asof")}, but as a claim on Intents&rsquo; fees NEAR is '
        f'priced for more growth than the data show at today&rsquo;s fees: the bull case reaches {M("ic_bull_vs_required_pct")}% of the revenue the price would assume.</p>'
        '<ul>'
        f'<li>Base case: captured revenue would pay for {M("ic_base_coverage_2031_pct")}% of NEAR&rsquo;s dilution in 2031.</li>'
        f'<li>To close the gap in today&rsquo;s market, NEAR would have to capture {M("ic_take_needed_vs_gross_x")}× Intents&rsquo; whole gross fee.</li>'
        f'<li>Pre-registered: net staking outflow was {M("h1a_ratio_as_written_x")}× staking rewards, where H1a predicted under {ctx.K("h1a_pass_below_x")}×; '
        'exchange flows come out as ranges the labels cannot settle, so the frozen rating rule gives no signal.</li>'
        f'<li>{forecast_line}</li>{update_line}</ul>'
        f'<p>Re-run it: <code>git clone {esc(REPO_URL)} &amp;&amp; cd near-flow-statement &amp;&amp; make site</code>. Research only; nothing here is investment advice.</p></section>')
    body = f'{cover}<main class="story">{slides}{end}</main>'
    body = body.replace('href="#', 'href="index.html#')
    head = (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n<meta name="color-scheme" content="light dark">\n'
        '<title>NEAR investment thesis: the story</title>\n'
        '<meta name="description" content="The NEAR investment case in six charts: what reaches NEAR, what the price assumes, what would have to give, '
        'three futures, the uncertainty and the signposts.">\n'
        f'<link rel="icon" href="{FAVICON}">\n'
        f"<style>\n{css()}\n{STORY_CSS.strip()}\n</style>\n</head>\n")
    return f"{head}<body class=\"story\">\n{break_lines(body)}\n</body>\n</html>\n"


# ------------------------------------------------------------------ build, write, check
def build_site(root: Path = ROOT, forward_dir: Path | None = None) -> tuple[dict[str, bytes], Ctx]:
    """The files of the site, as {path relative to the repo root: bytes}, and the Ctx they were built from.

    main() names the data fingerprint and the data date from that Ctx. A second Ctx would read the data again, and without the
    --forward-dir given: with a broken default data/forward it stopped the command after the page had been written elsewhere."""
    ctx = Ctx(root, forward_dir)
    return {f"{SITE_DIR}/{PAGE_NAME}": build_page(ctx).encode("utf-8"), f"{SITE_DIR}/{STORY_NAME}": build_story(ctx).encode("utf-8")}, ctx


def render(root: Path = ROOT, forward_dir: Path | None = None) -> dict[str, bytes]:
    """The files of the site, as {path relative to the repo root: bytes}. Pure: reads files, writes none."""
    return build_site(root, forward_dir)[0]


def summary(files: dict[str, bytes], ctx: Ctx | Path = ROOT, name: str | None = None) -> str:
    """`site/index.html (N bytes), data fingerprint …, data as of …`. `ctx` is the Ctx the page was built from (a repo root is
    read again, as it always was); `name` stands for site/index.html when the page was written or checked somewhere else."""
    page = files[f"{SITE_DIR}/{PAGE_NAME}"]
    if not isinstance(ctx, Ctx):
        ctx = Ctx(ctx)
    label = name if name is not None else f"{SITE_DIR}/{PAGE_NAME}"
    return f"{label} ({len(page):,} bytes), data fingerprint {ctx.fingerprint}, data as of {ctx.m['asof']}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m pipeline.render", description="Render the static dashboard from the committed data (offline, deterministic).")
    ap.add_argument("--check", action="store_true", help="exit 1 unless the committed site/ equals a fresh render, byte for byte")
    ap.add_argument("--out", type=Path, help="the site directory to write or check (default: site/ in the repo)")
    ap.add_argument("--root", type=Path, default=ROOT, help="repo root to read from (default: this repo)")
    ap.add_argument("--forward-dir", type=Path, help="directory holding score_*/result.json (default: data/forward)")
    a = ap.parse_args(argv)
    files, ctx = build_site(a.root, a.forward_dir)
    out_dir = a.out if a.out is not None else a.root / SITE_DIR
    # The site of this repository is named as the README quotes it (site/ and site/index.html); any other place by its real path. A given
    # --forward-dir is not this repository's own render: `python3 -m pipeline.render` reads data/forward, not that folder, so the hint
    # that follows a failed check must carry it.
    own = a.out is None and Path(a.root) == ROOT and a.forward_dir is None
    shown_dir = f"{SITE_DIR}/" if own else str(out_dir)
    shown_page = f"{SITE_DIR}/{PAGE_NAME}" if own else str(out_dir / PAGE_NAME)
    problems: list[str] = []
    for rel, data in files.items():
        target = out_dir / Path(rel).relative_to(SITE_DIR)
        if a.check:
            if not target.is_file():
                problems.append(f"missing: {target}")
            elif target.read_bytes() != data:
                problems.append(f"differs from a fresh render: {target}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    if a.check:
        for p in problems:
            print(f"FAIL  {p}", file=sys.stderr)
        if problems:
            again = "".join((f" --root {a.root}" if Path(a.root) != ROOT else "",
                              f" --forward-dir {a.forward_dir}" if a.forward_dir else ""))
            fix = "`python3 -m pipeline.render` and commit the result" if own else f"`python3 -m pipeline.render{again} --out {out_dir}`"
            print(f"render: {shown_dir} is out of date; run {fix}", file=sys.stderr)
            return 1
        print(f"render: {shown_dir} matches a fresh render ({summary(files, ctx, shown_page)})")
        return 0
    print(f"render: wrote {summary(files, ctx, shown_page)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
