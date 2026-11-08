"""Static dashboard: one self-contained page, site/index.html, rebuilt offline from the committed data.

  python3 -m pipeline.render            write site/index.html
  python3 -m pipeline.render --check    exit 1 unless the committed site/ equals a fresh render, byte for byte
                                        (files in site/ that the renderer does not produce are ignored)
  --out DIR          write or check DIR instead of site/ (the tests use a temporary directory)
  --forward-dir DIR  read score_*/result.json from DIR instead of data/forward (the tests inject fixtures)
  --root DIR         read the committed data from another checkout of this repo

Standard library only (Python 3.10+). The page loads nothing: no script, font, image or stylesheet from any
other file or host, and no JavaScript at all, so it opens from file:// and from GitHub Pages alike. It is
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
                         cuts from it (cut:), an endpoint block height in a raw snapshot (block:), or the time
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
from .h1b import COVERAGE_MIN_PCT, H1C_MIN

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

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

# Smallest drawn sizes, so a tiny value stays visible (the tests expect exactly these floors).
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


def wrap_words(text: str, max_chars: int) -> list[str]:
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


def load_forward(forward_dir: Path) -> dict | None:
    """The newest data/forward/score_*/result.json, only if it is a real score (is_score true, mode "score").

    Dry-run output (dry-run_*/DRY_RUN_result_NOT_A_SCORE.json) is never opened: only files named result.json
    inside score_* directories are considered, and a result whose mode is not "score" is ignored."""
    if not forward_dir.is_dir():
        return None
    cands = sorted(p for p in forward_dir.glob("score_*/result.json") if p.is_file())
    if not cands:
        return None
    path = cands[-1]
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not (isinstance(d, dict) and d.get("is_score") is True and d.get("mode") == "score"
            and isinstance(d.get("results"), dict)):
        return None
    d["_path"] = f"data/forward/{path.parent.name}/result.json"
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
        lg_h += 4
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
               footnote: str | None = None, tag: str = "") -> tuple[str, float]:
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
    ml = max(tw(tick_fmt(t), fs) for t in yticks) + 12
    mr = 8
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
               annots: list[dict] | None = None, vmarks: list[dict] | None = None, tag: str = "") -> tuple[str, float]:
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
    ml = max(tw(tick_fmt(t), fs) for t in yticks) + 12
    mr = max(58 if v.narrow else 76, max([tw(pl(s["end"]), fs, True) for s in series if s.get("end")] or [0]) + 14)
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
    "color-scheme:dark;--bg:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--muted:#a3a299;"
    "--grid:#2c2c2a;--axis:#4a4a46;--border:rgba(255,255,255,.14);--code:#232321;--s1:#3987e5;--s2:#d95926;"
    "--ctx:#898781;--link:#86b6ef;--focus:#6da7ec;--ok:#0ca30c;--warn:#fab219;--bad:#d03b3b;--shade:rgba(255,255,255,.22);"
)

CSS = """
:root{color-scheme:light;--bg:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#66655f;--grid:#e1e0d9;
--axis:#b3b1a8;--border:rgba(11,11,11,.14);--code:#f1f0ec;--s1:#2a78d6;--s2:#eb6834;--ctx:#898781;
--link:#1c5cab;--focus:#2a78d6;--ok:#0ca30c;--warn:#fab219;--bad:#d03b3b;--shade:rgba(11,11,11,.2)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){/*DARK*/}}
:root[data-theme="dark"]{/*DARK*/}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-padding-top:12px}
@media (prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;overflow-wrap:break-word}
.wrap{max-width:792px;margin:0 auto;padding:0 16px}
a{color:var(--link);text-underline-offset:2px}
a:focus-visible,summary:focus-visible,.tablewrap:focus-visible,pre:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.skip{position:absolute;left:-9999px;top:8px;background:var(--ink);color:var(--surface);padding:8px 14px;border-radius:6px;z-index:20}
.skip:focus{left:8px}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;font-size:.85em}
code{overflow-wrap:anywhere}
p,li{max-width:74ch}
header.top{padding:28px 0 6px}
.eyebrow{margin:0;font-size:.8125rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
h1{font-size:clamp(1.65rem,5.2vw,2.3rem);line-height:1.15;margin:.25em 0 .35em;letter-spacing:-.01em}
.lede{font-size:1.0625rem;margin:0 0 1rem}
.meta{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:4px 14px;font-size:.9rem;margin:1rem 0;padding:12px 14px;background:var(--surface);border:1px solid var(--border);border-radius:10px}
.meta dt{color:var(--muted);font-weight:600}
.meta dd{margin:0;min-width:0}
@media (max-width:560px){.meta{grid-template-columns:minmax(0,1fr)}.meta dd{margin-bottom:6px}}
.docs,.toc{display:flex;flex-wrap:wrap;gap:4px 18px;list-style:none;padding:0;margin:.6rem 0}
h2{font-size:1.45rem;line-height:1.25;margin:2.6rem 0 .5rem}
h3{font-size:1.15rem;line-height:1.35;margin:.5rem 0 .6rem}
.note{color:var(--ink2);font-size:.95rem}
.tiles{display:grid;gap:10px;list-style:none;padding:0;margin:.9rem 0}
.tile{display:grid;grid-template-columns:12.5rem minmax(0,1fr);gap:2px 18px;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px 16px;align-items:start;max-width:none}
.tile p{margin:0;max-width:none}
.tlabel{font-size:.8125rem;font-weight:700;color:var(--ink2)}
.st{display:flex;align-items:center;gap:8px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;font-size:1.05rem}
.tile .st{grid-row:1 / span 4;align-self:center}
.tile>:not(.st){grid-column:2}
.ico{flex:none}
.i-bad{fill:var(--bad)}.i-ok{fill:var(--ok)}.i-warn{fill:var(--warn)}.i-ink2{fill:var(--ink2)}
.i-line{fill:none;stroke:var(--ink2);stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.big{font-size:1.45rem;font-weight:750;line-height:1.2}
.tnote{font-size:.875rem;color:var(--ink2)}
.tile a{font-size:.875rem}
@media (max-width:640px){.tile{grid-template-columns:minmax(0,1fr)}.tile .st{grid-row:auto}.tile>:not(.st){grid-column:1}}
.badge{display:inline-flex;align-items:center;gap:6px;font-size:.75rem;font-weight:800;letter-spacing:.05em;text-transform:uppercase;padding:3px 10px 3px 8px;border-radius:999px;line-height:1.3}
.badge-pre{background:var(--ink);color:var(--surface)}
.badge-pre .i-line{stroke:var(--surface)}
.badge-exp{border:1.5px dashed var(--ink2);color:var(--ink)}
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:18px 20px 14px;margin:0 0 22px;min-width:0}
.cardtop{display:flex;justify-content:space-between;align-items:center;gap:10px}
.cardtop a{font-size:.875rem;color:var(--muted)}
.shows,.notshows{margin:.35rem 0}
.notshows{color:var(--ink2)}
figure.chart-fig{margin:1rem 0 .4rem}
.chart{margin:0}
.cv{max-width:100%}
.cv-narrow{display:none;max-width:430px}
@media (max-width:699px){.cv-wide{display:none}.cv-narrow{display:block}.card{padding:14px 12px 10px}}
figcaption{font-size:.8125rem;color:var(--muted);margin-top:6px}
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
.svg .vmark{stroke:var(--ink);stroke-width:1.5;stroke-dasharray:5 4;shape-rendering:crispEdges}
.svg .bracket{fill:none;stroke:var(--axis);stroke-width:1.2}
.svg .s1{fill:var(--s1)}.svg .s2{fill:var(--s2)}.svg .sc{fill:var(--ctx)}.svg .sk{fill:var(--ink)}.svg .st2{fill:var(--ink2)}
.svg .track{fill:var(--grid)}
.svg .band{fill:var(--s1);opacity:.22}
.svg .bandedge{stroke:var(--s1);stroke-width:2}
.svg .ln{fill:none;stroke-width:2.2;stroke-linejoin:round;stroke-linecap:round}
.svg .l1{stroke:var(--s1)}.svg .l2{stroke:var(--s2)}.svg .lc{stroke:var(--ctx)}
.svg .lg{stroke-width:2.2;stroke-linecap:round}
.svg .lg.refline{stroke-width:1.5}
.svg .wash{opacity:.12}
.svg .ring{stroke:var(--surface);stroke-width:2}
.svg .ghost{fill:none;stroke:var(--ctx);stroke-width:1.6}
.source,.qnote{font-size:.875rem;color:var(--ink2);margin:.7rem 0 .3rem}
.source p{margin:0 0 .2rem}
.source ul{margin:.1rem 0 .3rem;padding-left:1.1rem}
.source li{margin:.15rem 0;max-width:none}
.source ul ul{padding-left:.9rem}
.notes{font-size:.9rem;color:var(--ink2);margin:.8rem 0 .4rem;padding-left:1.1rem}
.notes li{margin:.3rem 0}
ul.rule{margin:.8rem 0;padding-left:1.1rem}
ul.rule li{margin:.35rem 0}
.sha{color:var(--muted);font-size:.8125rem;white-space:nowrap}
details{margin:.45rem 0;border-top:1px solid var(--grid);padding-top:.35rem}
summary{cursor:pointer;font-weight:650;padding:4px 0}
pre{margin:.5rem 0 .6rem;padding:12px 14px;background:var(--code);border-radius:8px;overflow:auto;max-height:440px;line-height:1.45;tab-size:2}
.qh{margin:.7rem 0 0;font-size:.875rem}
.tablewrap{overflow:auto;max-height:420px;border:1px solid var(--border);border-radius:8px;margin:.5rem 0 .7rem;
background:linear-gradient(to right,var(--surface) 30%,transparent) 0 0/34px 100% no-repeat local,
linear-gradient(to left,var(--surface) 30%,transparent) 100% 0/34px 100% no-repeat local,
linear-gradient(to right,var(--shade),transparent) 0 0/14px 100% no-repeat scroll,
linear-gradient(to left,var(--shade),transparent) 100% 0/14px 100% no-repeat scroll}
.scrollhint{display:none;font-size:.8125rem;color:var(--muted);margin:.4rem 0 0}
table{border-collapse:collapse;width:100%;font-size:.8125rem}
caption{text-align:left;font-weight:650;padding:6px 10px;color:var(--ink2)}
th,td{padding:5px 10px;border-bottom:1px solid var(--grid);white-space:nowrap;vertical-align:top;text-align:right;font-variant-numeric:tabular-nums}
th{white-space:normal}
th.txt,td.t{text-align:left;font-variant-numeric:normal;white-space:normal;min-width:10rem}
@media (max-width:699px){th.txt,td.t{min-width:6.5rem}th,td{padding:5px 8px}.scrollhint{display:block}}
thead th{position:sticky;top:0;background:var(--surface);z-index:1;border-bottom:1px solid var(--axis)}
.keyfigs{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px 14px;margin:.7rem 0 .2rem}
.keyfigs div{min-width:0}
.keyfigs dt{font-size:.8125rem;color:var(--muted)}
.keyfigs dd{margin:0;font-weight:700;font-size:1.05rem;font-variant-numeric:tabular-nums}
ol.fwd{list-style:none;padding:0;margin:.9rem 0;display:grid;gap:10px}
ol.fwd li{border:1px solid var(--border);border-radius:10px;padding:10px 12px;min-width:0;max-width:none}
ol.fwd p{margin:.2rem 0}
.fhead{display:flex;flex-wrap:wrap;gap:4px 8px;align-items:center}
.fhead .st{display:inline-flex;font-size:.9rem}
.fword{text-transform:uppercase}
.verbatim{font-size:.9rem}
ol.steps{padding-left:1.5rem;margin:.6rem 0}
ol.steps li{margin:.9rem 0;max-width:none;padding-left:.2rem}
ol.steps p{margin:.2rem 0}
.do code{display:inline-block;max-width:100%;white-space:pre-wrap;overflow-wrap:anywhere;background:var(--code);padding:3px 9px;border-radius:6px}
ul.plain{padding-left:1.2rem}
ul.plain li{margin:.35rem 0}
footer{margin:3rem 0 2rem;padding-top:1rem;border-top:1px solid var(--grid);font-size:.9rem;color:var(--ink2)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
"""


def css() -> str:
    return CSS.replace("/*DARK*/", DARK_TOKENS).strip()


# ------------------------------------------------------------------ icons (shape + label, never colour alone)
ICONS = {
    "fail": '<circle class="i-bad" cx="10" cy="10" r="9" /><path d="M6.6 6.6l6.8 6.8M13.4 6.6l-6.8 6.8" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" />',
    "pass": '<circle class="i-ok" cx="10" cy="10" r="9" /><path d="M5.8 10.4l2.8 2.8 5.6-6.2" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />',
    "inconclusive": '<path class="i-warn" d="M10 .9l9.1 9.1-9.1 9.1L.9 10z" /><path d="M7.7 7.9a2.3 2.3 0 1 1 3.5 1.9c-.8.5-1.2 1-1.2 1.9" fill="none" stroke="#0b0b0b" stroke-width="2" stroke-linecap="round" /><circle cx="10" cy="14.5" r="1.2" fill="#0b0b0b" />',
    "hold": '<circle class="i-ink2" cx="10" cy="10" r="9" /><path d="M5.6 10h8.8" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" />',
    "pending": '<circle class="i-line" cx="10" cy="10" r="8.2" /><path class="i-line" d="M10 5.4V10l3.2 2" />',
    "scored": '<circle class="i-line" cx="10" cy="10" r="8.2" /><circle class="i-ink2" cx="10" cy="10" r="3.4" />',
    "na": '<circle class="i-line" cx="10" cy="10" r="8.2" /><path class="i-line" d="M4.6 15.4l10.8-10.8" />',
    "lock": '<rect class="i-line" x="4.5" y="9" width="11" height="8" rx="1.6" /><path class="i-line" d="M7 9V6.6a3 3 0 0 1 6 0V9" />',
    "compass": '<circle class="i-line" cx="10" cy="10" r="8" /><path class="i-line" d="M12.9 7.1l-1.7 4.1-4.1 1.7 1.7-4.1z" />',
}


def icon(kind: str, size: int = 20) -> str:
    return (f'<svg class="ico" viewBox="0 0 20 20" width="{size}" height="{size}" aria-hidden="true" focusable="false">'
            f"{ICONS[kind]}</svg>")


def status_kind(word: str) -> str:
    w = word.lower()
    if w.startswith(("pass", "buy")):
        return "pass"
    if w.startswith(("fail", "miss", "avoid")):
        return "fail"
    if w.startswith("inconclusive"):
        return "inconclusive"
    if w.startswith("hold"):
        return "hold"
    if w.startswith("not scorable"):
        return "na"
    if w.startswith("scored"):
        return "scored"
    return "pending"


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


def card(*, cid: str, kind: str, headline: str, shows: str, notshows: str, figure: str, caption: str,
         source: str, query: str, data: str, extra: str = "", notes: tuple[str, ...] = ()) -> str:
    """One chart card. kind is "pre" (pre-registered) or "exp" (exploratory, chosen after the freeze)."""
    badge = (f'<span class="badge badge-pre">{icon("lock", 14)} Pre-registered</span>' if kind == "pre"
             else f'<span class="badge badge-exp">{icon("compass", 14)} Exploratory, chosen after the freeze</span>')
    note_ul = f'<ul class="notes">{"".join(f"<li>{n}</li>" for n in notes)}</ul>' if notes else ""
    return (
        f'<section class="card" id="chart-{cid}" aria-labelledby="chart-{cid}-h">'
        f'<div class="cardtop">{badge}<a href="#chart-{cid}" aria-label="Link to this chart">#</a></div>'
        f'<h3 id="chart-{cid}-h">{headline}</h3>'
        f'<p class="shows"><strong>What it shows:</strong> {shows}</p>'
        f'<p class="notshows"><strong>What it does not show:</strong> {notshows}</p>'
        f'<figure class="chart-fig">{figure}<figcaption>{caption}</figcaption></figure>'
        f"{extra}{note_ul}{source}{query}{data}</section>"
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
        a, ha = hbar_panel(v, title="90-day totals, million NEAR (bars start at zero)", tag="A", rows=a_rows, vmax=250,
                           ticks=[0, 50, 100, 150, 200, 250],
                           refs=[{"v": pass_line, "label": T("H1a pass line: net outflow below ",
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
         {"k": None, "cells": [f'Pass line ({ctx.K("h1a_pass_below_x")} x staking rewards)', ctx.D("0.5*h1a_staking_rewards_90d_m", 2)]}],
        caption="Panel A: 90-day totals in million NEAR")
    figs = keyfigs([
        ("Net outflow ÷ staking rewards", f'{ctx.M("h1a_ratio_as_written_x")}×'),
        ("A pass needed", f'under {ctx.K("h1a_pass_below_x")}×'),
        ("Same ratio, archival pool state", f'{ctx.M("h1a_ratio_endpoint_archival_x")}×')])
    return card(
        cid="h1a", kind="pre",
        headline=f'H1a fails: net staking outflow was {ctx.M("h1a_ratio_as_written_x")}× staking rewards, '
                 f'where a pass needed under {ctx.K("h1a_pass_below_x")}×.',
        shows=(f'Over the 90 days {window_text(ctx, 90)}, delegators withdrew {ctx.M("pool_outflow_90d_m")}M NEAR from staking pools and '
               f'deposited {ctx.M("pool_inflow_90d_m")}M, a net outflow of {ctx.M("pool_net_outflow_90d_m")}M NEAR against '
               f'{ctx.M("h1a_staking_rewards_90d_m")}M NEAR of staking rewards ({ctx.K("staking_rewards_share_pct")}% of the '
               f'{ctx.M("h1a_gross_issuance_90d_m")}M NEAR minted).'),
        notshows=('Who withdrew or where the NEAR went: NEAR is fungible, so nothing here says which coins were sold, and whether the NEAR '
                  'reached exchanges is H1b, which is inconclusive.'),
        figure=fig,
        caption=f'Window: 90 days, {window_text(ctx, 90)} (UTC). Unit: million NEAR. Panel A bars start at zero; Panel B accumulates the daily flows.',
        extra=figs,
        notes=(f'The {ctx.M("h1a_gross_issuance_90d_m")}M NEAR minted is read from {ctx.M("h1a_epochs_in_window")} epoch-boundary block headers. '
               f'Panel B uses the {ctx.M("pool_rewards_90d_m")}M NEAR of rewards credited to pools in the daily series, so on that denominator the '
               f'ratio is {ctx.M("pool_net_outflow_to_rewards_x")}×, not the pre-registered {ctx.M("h1a_ratio_as_written_x")}×.',
               f'With <code>lst-pool.near</code>, the only validator the pool-name filter misses in the validator sets sampled, added (post hoc; the test is '
               f'not redefined), the ratio is {ctx.M("h1a_ratio_with_lst_pool_x")}×. H1a fails either way.'),
        source=source_p(ctx, sql=("sql/staking_flows_daily.sql", "sql/staking_pool_totals_endpoints.sql"),
                        raw=("raw/bq/staking_flows_daily.json", "raw/bq/staking_pool_totals_endpoints.json",
                             "raw/rpc/epoch_issuance.json", "raw/rpc/pool_endpoints_archival.json"),
                        code=("pipeline/h1a.py", "pipeline/fetch_issuance.py"),
                        upstream=("BigQuery public dataset bigquery-public-data.crypto_near_mainnet_us, table account_changes",
                                  "NEAR archival RPC epoch-boundary block headers")),
        query=query_details(ctx, sql=("sql/staking_flows_daily.sql", "sql/staking_pool_totals_endpoints.sql")),
        data=data_details(totals, daily))


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
        a, ha = hbar_panel(v, title="Net exchange inflow, 90 days, million NEAR (bars start at zero)", tag="A", rows=a_rows, vmax=200,
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
        b, hb = hbar_panel(v, title="Labelled share of the top-100 native-NEAR receivers, % (bars start at zero)", tag="B", rows=b_rows,
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
        headline=(f'H1b is {ctx.M("h1b_verdict")}: net exchange inflow lies between {ctx.M("h1b_net_inflow_lower_m")}M and '
                  f'{ctx.M("h1b_net_inflow_upper_m")}M NEAR, on either side of the {ctx.M("h1a_gross_issuance_90d_m")}M NEAR minted.'),
        shows=(f'Net exchange inflow of NEAR (native plus wNEAR) into labelled exchange accounts over the 90 days {window_text(ctx, 90)}, as a range: '
               f'{ctx.M("h1b_net_inflow_lower_m")}M NEAR if unlabelled receivers are not exchange-bound, {ctx.M("h1b_net_inflow_upper_m")}M NEAR if every '
               f'unlabelled top-100 receiver is.'),
        notshows=('That any of this NEAR was sold, or by whom (NEAR is fungible): it counts only labelled centralized-exchange accounts, so '
                  '1Click, a non-custodial route out of NEAR, is reported beside H1b and never inside it.'),
        figure=fig,
        caption=f'Window: 90 days, {window_text(ctx, 90)} (UTC). Units: million NEAR (Panel A) and percent of the top-100 receivers (Panel B). Both axes start at zero.',
        notes=(f'Only {ctx.M("h1b_coverage_count_pct")}% of the top-100 native-NEAR receivers carry an exchange label ({ctx.M("h1b_coverage_tier1_count_pct")}% a cited '
               f'one; the rest are labelled by our sweep rule), below the '
               f'{ctx.K("h1b_coverage_min_pct")}% the pre-registration requires, so the test passes only if it passes under both bounds. The lower '
               f'bound is under gross issuance and the upper bound is far over it, so the result is inconclusive.',
               'The upper bound is mechanical: it treats every unlabelled top-100 receiver as an exchange, including accounts that are probably not.',
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
            f"{CONSTS['h1c_min_pct'][1]} percent pass bar.")

    def build(v: Variant) -> tuple[str, float]:
        rows = [
            {"label": "Identified buying ÷ lower bound of net exchange inflow",
             "bars": [bar(m["h1c_ratio_lower_pct"], "s1", T(Mt("h1c_ratio_lower_pct"), "%"),
                          f"Against the lower bound: {ctx.plain('h1c_ratio_lower_pct')}%")]},
            {"label": "Identified buying ÷ upper bound of net exchange inflow",
             "bars": [bar(m["h1c_ratio_upper_pct"], "s2", T(Mt("h1c_ratio_upper_pct"), "%"),
                          f"Against the upper bound: {ctx.plain('h1c_ratio_upper_pct')}%")]},
        ]
        return hbar_panel(v, title="Identified buying ÷ net exchange inflow, % (bars start at zero)", rows=rows, vmax=40,
                          ticks=[0, 10, 20, 30, 40], tick_fmt=lambda t: f"{t:g}%",
                          refs=[{"v": CONSTS["h1c_min_pct"][0], "label": T("pass bar: ", ctx.Kt("h1c_min_pct"), "% under both bounds")}])

    fig = dual(ctx, "chart-h1c", title, desc, build)
    tab = table_html(
        [{"h": "Measure", "num": False}, {"h": "Value"}, {"h": "Unit", "num": False}],
        [{"k": None, "cells": [esc("Identified buying: increase in the buyback wallet's balance"), ctx.M("h1c_identified_buying_m"),
                               esc("million NEAR")]},
         {"k": None, "cells": [esc("Net exchange inflow, lower bound"), ctx.M("h1b_net_inflow_lower_m"), esc("million NEAR")]},
         {"k": None, "cells": [esc("Net exchange inflow, upper bound"), ctx.M("h1b_net_inflow_upper_m"), esc("million NEAR")]},
         {"k": None, "cells": [esc("Identified buying ÷ lower bound"), ctx.M("h1c_ratio_lower_pct"), esc("%")]},
         {"k": None, "cells": [esc("Identified buying ÷ upper bound"), ctx.M("h1c_ratio_upper_pct"), esc("%")]},
         {"k": None, "cells": [esc("Pass bar"), ctx.K("h1c_min_pct"), esc("%")]}],
        caption="Plotted values")
    figs = keyfigs([("Identified buying", f'{ctx.M("h1c_identified_buying_m")}M NEAR'),
                    ("Lower bound of net inflow", f'{ctx.M("h1b_net_inflow_lower_m")}M NEAR'),
                    ("Upper bound of net inflow", f'{ctx.M("h1b_net_inflow_upper_m")}M NEAR')])
    pointer = ('The net exchange inflow bounds in the denominator come from these two BigQuery queries, the same text as in the Query block of '
               '<a href="#chart-h1b">the H1b chart</a>; this chart adds one RPC read, below.')
    return card(
        cid="h1c", kind="pre",
        headline=(f'H1c is {ctx.M("h1c_verdict")}: the buyback wallet grew by {ctx.M("h1c_identified_buying_m")}M NEAR, '
                  f'{ctx.M("h1c_ratio_lower_pct")}% of the lower bound of net exchange inflow but {ctx.M("h1c_ratio_upper_pct")}% of the upper; '
                  f'a pass needs {ctx.K("h1c_min_pct")}% under both.'),
        shows=(f'Identified buying, the balance increase of <code>buybacks.multisignature.near</code> between the window&rsquo;s end-point blocks '
               f'({ctx.M("h1c_identified_buying_m")}M NEAR), as a share of the two net exchange inflow bounds from H1b.'),
        notshows=('That the buyback wallet&rsquo;s NEAR came from exchanges: NEAR is fungible, so the ratio is a market-wide balance, not a trace.'),
        figure=fig,
        caption=f'Window: 90 days, {window_text(ctx, 90)} (UTC). Unit: percent. The axis starts at zero.',
        extra=figs,
        notes=(f'With label coverage below {ctx.K("h1b_coverage_min_pct")}%, H1c passes only if it clears {ctx.K("h1c_min_pct")}% under both bounds. '
               f'It clears the bar against the lower bound and falls far short against the upper, so it is inconclusive; it inherits every limit of '
               f'H1b, including the {ctx.M("h1b_coverage_count_pct")}% label coverage.',
               'ETF and treasury-company holdings are not part of the test. The buyback wallet&rsquo;s NEAR is held, not burned.'),
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

    The sentence is true of the data as committed: observed growth is above the Avoid line, so a failed H1b would also
    give Hold, and coverage is below the pre-registered 50%, where (under the range rule as read before the results) H1b
    cannot fail. If the data stop supporting it the render stops, so the page cannot go on saying it."""
    m = ctx.m
    if not (m["rating_output"] == "Hold" and m["rating_if_h1b_fail"] == "Hold"
            and min(m["rating_g_obs_pct"], m["rating_g_obs_near_pct"]) >= m["rating_g_avoid_line_pct"]
            and m["h1b_coverage_count_pct"] < CONSTS["h1b_coverage_min_pct"][0]):
        raise SystemExit("render: the rating card explains the Hold with facts the data no longer support; rewrite hold_explanation()")
    M, K = ctx.M, ctx.K
    return (f'The frozen rule outputs {M("rating_output")}, and that carries no view on NEAR. Below {K("h1b_coverage_min_pct")}% label coverage H1b can come '
            f'out pass or inconclusive but never fail (the range rule as read before the results; <a href="{esc(gh("PREREG-ADDENDUM.md"))}">PREREG-ADDENDUM.md</a>, '
            f'2026-11-06 23:11 UTC entry, item 6), and observed revenue growth ({M("rating_g_obs_pct")}% a year; {M("rating_g_obs_near_pct")}% in NEAR terms) '
            f'is far above the Avoid line ({M("rating_g_avoid_line_pct")}% a year, half of G_req {M("rating_g_req_pct")}%), so the rule could only ever have '
            f'output Buy or Hold; had H1b failed it would also have been {M("rating_if_h1b_fail")}.')


def card_rating(ctx: Ctx) -> str:
    m, Mt = ctx.m, ctx.Mt
    go, gr = m["rating_g_obs_pct"], m["rating_g_req_pct"]
    h1b_word = str(m["h1b_verdict"])
    h1b_pass, h1b_fail = h1b_word.startswith("pass"), h1b_word.startswith("fail")
    title = "Rating rule inputs: required against observed growth in captured revenue"
    desc = (f"Bars from zero in percent a year: required growth G_req {ctx.plain('rating_g_req_pct')}, or "
            f"{ctx.plain('rating_g_req_no_hsp029_pct')} without HSP-029; observed growth G_obs {ctx.plain('rating_g_obs_pct')} in USD "
            f"and {ctx.plain('rating_g_obs_near_pct')} in NEAR terms. The frozen rule outputs {m['rating_output']}.")

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
        return hbar_panel(v, title="Growth in captured Intents revenue, % a year (bars start at zero)", rows=rows, vmax=700,
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

    rule = (
        '<ul class="rule">'
        f'<li><strong>Buy</strong> needs G_obs ≥ G_req and H1b to pass. Now: G_obs ≥ G_req is {yn(ge)} ({ctx.M("rating_g_obs_pct")} against '
        f'{ctx.M("rating_g_req_pct")}) and H1b passes is {yn(h1b_pass)} ({ctx.M("h1b_verdict")}), so Buy is {met(buy_met)}.</li>'
        f'<li><strong>Avoid</strong> needs G_obs &lt; G_req ÷ 2 and H1b to fail. Now: G_obs &lt; G_req ÷ 2 is {yn(avoid_g)} and H1b fails is '
        f'{yn(h1b_fail)} ({ctx.M("h1b_verdict")}), so Avoid is {met(avoid_met)}.</li>'
        f'<li><strong>Hold</strong> is anything else, so Hold is {met(hold_met)}. Output: <strong>{ctx.M("rating_output")}</strong>.</li></ul>')
    tab = table_html(
        [{"h": "Input", "num": False}, {"h": "Value"}, {"h": "Unit", "num": False}],
        [{"k": None, "cells": [esc("G_req"), ctx.M("rating_g_req_pct"), esc("% a year")]},
         {"k": None, "cells": [esc("G_req without HSP-029"), ctx.M("rating_g_req_no_hsp029_pct"), esc("% a year")]},
         {"k": None, "cells": [esc("G_obs, USD"), ctx.M("rating_g_obs_pct"), esc("% a year")]},
         {"k": None, "cells": [esc("G_obs, NEAR terms"), ctx.M("rating_g_obs_near_pct"), esc("% a year")]},
         {"k": None, "cells": [esc("Captured revenue, last 90 days"), ctx.M("rating_r90_usd_m"), esc("USD million")]}],
        caption="Plotted values")
    figs = keyfigs([("Rule output", ctx.M("rating_output")),
                    ("If H1b had passed", ctx.M("rating_if_h1b_pass")),
                    ("If H1b had failed", ctx.M("rating_if_h1b_fail"))])
    return card(
        cid="rating", kind="pre",
        headline=(f'The frozen rule outputs {ctx.M("rating_output")}, which carries no view on NEAR: Buy needs H1b to pass, Avoid needs it to fail and observed '
                  f'growth under half the required growth, and H1b is {ctx.M("h1b_verdict")}.'),
        shows=(f'The two inputs of the pre-registered rating rule: required growth G_req of {ctx.M("rating_g_req_pct")}% a year '
               f'({ctx.M("rating_g_req_no_hsp029_pct")}% without HSP-029) against observed growth G_obs of {ctx.M("rating_g_obs_pct")}% a year in USD '
               f'({ctx.M("rating_g_obs_near_pct")}% in NEAR terms).'),
        notshows=(f'A view on the token. {hold_explanation(ctx)} Nor does it show that the inputs are firm: G_req rests on constants committed after the freeze, '
                  f'with the as-written H1a result (the price, the length of HSP-029&rsquo;s ramp and its activation date; '
                  f'<code>data/raw/rpc/rating_assumptions.json</code>), and G_obs compares the last 180 days with the 180 before, a base window that straddles the '
                  f'2026-02-23 fee switch (pre-switch revenue counts as captured, as DefiLlama labels it), so it does not separate the switch from other causes, '
                  f'and most of the USD growth is the NEAR price.'),
        figure=fig,
        caption=f'Unit: percent a year. The axis starts at zero, so the observed USD growth dwarfs the other bars. Observed growth compares the last 180 days with the 180 before, to {ctx.m["asof"]}.',
        extra=f'{rule}{figs}',
        notes=(f'G_req is the annual growth in captured Intents revenue ({ctx.M("rating_r90_usd_m")}M USD over the last 90 days, DefiLlama) needed for it to equal '
               f'the USD value of net new supply by 2031-11-04. G_obs is the growth of the last 180 days over the 180 before, annualized.',
               'G_req assumes HSP-029&rsquo;s issuance ramp. Its on-chain timelock ends on 2026-11-16, after the submission deadline, and the proposal text also says the cut needs validator adoption through a protocol upgrade; we state it as a pending resolver and do not predict it.',
               f'Under the range rule as read before the results, a low-coverage H1b can come out pass or inconclusive, never fail, so the Avoid branch cannot be '
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
    opens = sf.SCORE_NOT_BEFORE.strftime("%Y-%m-%d %H:%M UTC")
    w0, w1 = sf.WINDOW

    def result_of(fid: str) -> dict:
        r = res.get(fid)
        return r if isinstance(r, dict) else {}

    def word_of(fid: str) -> str:
        if not fw:
            return "pending"
        w = str(result_of(fid).get("result", "not scorable"))
        return w if w in ("PASS", "MISS") else "not scorable"

    def obs_of(fid: str, key: str):
        v = result_of(fid).get(key)
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    def ftxt(fid: str, key: str, dec: int, scale: float = 1.0, suffix: str = "") -> Txt | None:
        v = obs_of(fid, key)
        if v is None:
            return None
        text_ = fmt_value(round(v / scale, dec), dec)
        return f'<tspan data-f="{fid}.{key}" data-scale="{n1(scale) if scale != 1 else 1}">{esc(text_)}</tspan>{esc(suffix)}', text_ + suffix

    # axes: the frozen band plus the reference value, widened if an observed value falls outside
    def axis(lo: float, hi: float, step: float, ob: float | None) -> tuple[float, float, list[float]]:
        if ob is not None:
            lo, hi = min(lo, math.floor((ob - step) / step) * step), max(hi, math.ceil((ob + step) / step) * step)
        k = int(math.ceil((hi - lo) / step - 1e-9))
        return lo, lo + k * step, [lo + i * step for i in range(k + 1)]

    o1, o2, o3, o4 = (obs_of("F1", "balance_near"), obs_of("F2", "mean_near_per_day"),
                      obs_of("F3", "take_rate_bp"), obs_of("F4", "intents_share_pct"))
    a1 = axis(2.0, 2.6, 0.2, o1 / 1e6 if o1 is not None else None)
    a2 = axis(82.0, 94.0, 4.0, o2 / 1e3 if o2 is not None else None)
    a3 = axis(0.0, 8.0, 2.0, o3)
    a4 = axis(0.0, 100.0, 25.0, o4)

    def mk_obs(fid: str, key: str, val: float | None, dec: int, scale: float, suffix: str):
        t = ftxt(fid, key, dec, scale, suffix)
        return {"v": val, "label": T("observed ", t)} if (t and val is not None) else None

    title = "Forward tests F1 to F4: the frozen predictions" + (", with the scored results" if fw else ", pending")
    if fw:
        desc = "Four number lines, one per forward test. Each shows the frozen prediction as a shaded band and the observed value as a dot."
    else:
        desc = ("Four number lines, one per forward test. Each shows the frozen prediction as a shaded band and, as a diamond, the "
                "last value committed before the window opened. No test is scored yet, so there is no observed value.")

    def build(v: Variant) -> tuple[str, float]:
        rows = [
            {"id": "F1", "title": T("F1 · buyback wallet balance at the first final block after ", opens.split(" UTC")[0], " (million NEAR, axis does not start at zero)"),
             "lo": a1[0], "hi": a1[1], "ticks": a1[2], "tick_fmt": lambda t: f"{t:.1f}",
             "band": (CONSTS["f1_lo"][0] / 1e6, CONSTS["f1_hi"][0] / 1e6),
             "band_label": T("predicted ", ctx.Kt("f1_lo"), "M to ", ctx.Kt("f1_hi"), "M"),
             "refs": [] if fw else [{"v": m["buyback_wallet_near_m"], "label": T("read at block ", Mt("rpc_block", 0), ": ", Mt("buyback_wallet_near_m"), "M")}],
             "obs": mk_obs("F1", "balance_near", o1 / 1e6 if o1 is not None else None, 3, 1e6, "M")},
            {"id": "F2", "title": T("F2 · mean net supply increase per day, ", w0, " to ", w1, " (thousand NEAR a day, axis does not start at zero)"),
             "lo": a2[0], "hi": a2[1], "ticks": a2[2], "tick_fmt": lambda t: f"{t:g}",
             "band": (CONSTS["f2_lo"][0] / 1e3, CONSTS["f2_hi"][0] / 1e3),
             "band_label": T("predicted ", ctx.Kt("f2_lo"), "K to ", ctx.Kt("f2_hi"), "K"),
             "refs": [] if fw else [{"v": m["net_issuance_near_per_day_30d_k"], "label": T("30 days to ", m["asof"], ": ", Mt("net_issuance_near_per_day_30d_k"), "K")}],
             "obs": mk_obs("F2", "mean_near_per_day", o2 / 1e3 if o2 is not None else None, 1, 1e3, "K")},
            {"id": "F3", "title": T("F3 · captured take rate, DefiLlama revenue ÷ volume, ", w0, " to ", w1, " (basis points)"),
             "lo": a3[0], "hi": a3[1], "ticks": a3[2], "tick_fmt": lambda t: f"{t:g}",
             "band": (a3[0], CONSTS["f3_max_bp"][0]),
             "band_label": T("pass: below ", ctx.Kt("f3_max_bp"), " bp"),
             "refs": [] if fw else [{"v": m["take_captured_bp_30d"], "label": T("30 days to ", m["asof"], ": ", Mt("take_captured_bp_30d"), " bp")}],
             "obs": mk_obs("F3", "take_rate_bp", o3, 2, 1.0, " bp")},
            {"id": "F4", "title": T("F4 · NEAR Intents' share of peer-set volume, reported basis, ", w0, " to ", w1, " (percent)"),
             "lo": a4[0], "hi": a4[1], "ticks": a4[2], "tick_fmt": lambda t: f"{t:g}%",
             "band": (CONSTS["f4_min_pct"][0], a4[1]),
             "band_label": T("pass: ", ctx.Kt("f4_min_pct"), "% or more"),
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
            why = (f'<span data-f="{fid}.why" data-scale="1">{esc(r["why"])}</span>' if "why" in r else "no reason recorded")
            nums = f'Not scorable: {why}. It is never estimated.'
        else:
            nums = f"Scored after {esc(opens)}."
        items.append(
            f'<li data-k="{fid}"><p class="fhead"><strong>{fid}</strong> · prior probability '
            f'<span data-p="{fid}">{esc(pr["p"])}</span> · <span class="st">{icon(status_kind(word), 18)}'
            f'<span class="fword" data-status="{fid}">{esc(word)}</span></span></p>'
            f'<p class="verbatim">{md_inline(pr["text"])}</p><p class="tnote">{nums}</p></li>')
    lst = f'<ol class="fwd">{"".join(items)}</ol>'

    if fw:
        counts = {k: sum(1 for f_ in ("F1", "F2", "F3", "F4") if word_of(f_) == k) for k in ("PASS", "MISS", "not scorable")}
        headline = (f'Forward tests scored: <span data-f="@count.PASS" data-scale="1">{counts["PASS"]}</span> passed, '
                    f'<span data-f="@count.MISS" data-scale="1">{counts["MISS"]}</span> missed and '
                    f'<span data-f="@count.not scorable" data-scale="1">{counts["not scorable"]}</span> not scorable of 4.')
        shows = (f'The four predictions frozen in PREREG.md before the window {esc(w0)} to {esc(w1)}, scored exactly as written by '
                 f'<code>python3 -m pipeline.score_forward --score</code> on <span data-f="scored_at" data-scale="1">{esc(fw.get("scored_at", ""))}</span> '
                 f'from data fetched at <span data-f="snapshot_fetched_at" data-scale="1">{esc(fw.get("snapshot_fetched_at", ""))}</span>.')
        notes = ('Every result is published, misses included. A test with missing data is scored "not scorable" and never estimated.',
                 'The bands are the frozen predictions and the dot is the observed value. The predictions were frozen before the window; the scorer was '
                 'written on 2026-11-06, after the window opened, and its first dry run read no scoring-window day for F2 to F4 and only the window-opening '
                 'block for F1 (PREREG-ADDENDUM.md, 2026-11-06 23:49 UTC entry, item 7).')
    else:
        headline = (f'Forward tests F1 to F4 are pending: the window is {esc(w0)} to {esc(w1)} and scoring opens {esc(opens)}.')
        shows = (f'The four predictions frozen in PREREG.md before the window {esc(w0)} to {esc(w1)}, each with its prior probability; '
                 f'nothing is scored yet, so each test is pending.')
        notes = ('The bands are the frozen predictions. The diamonds are the last values committed before the window opened, shown for scale and not as forecasts.',
                 'Every result will be published, including misses. A test with missing data is scored "not scorable" and never estimated. The predictions were '
                 'frozen before the window; the scorer was written on 2026-11-06, after the window opened, and its first dry run read no scoring-window day for F2 to F4 '
                 'and only the window-opening block for F1 (PREREG-ADDENDUM.md, 2026-11-06 23:49 UTC entry, item 7).')
    notshows = ('A score before scoring opens: a dry run of the scorer is not a score and is never shown here.')
    tab_rows = []
    for fid in ("F1", "F2", "F3", "F4"):
        pr = ctx.prereg_forward[fid]
        tab_rows.append({"k": fid, "cells": [esc(fid), f'<span data-p="{fid}">{esc(pr["p"])}</span>', esc(word_of(fid)),
                                             f'<span class="verbatim">{esc(pr["text"].replace("**", "").replace("`", ""))}</span>']})
    tab = table_html([{"h": "Test", "num": False, "c": "id"}, {"h": "Prior probability", "c": "p"},
                      {"h": "Status", "num": False, "c": "status"}, {"h": "Frozen prediction (PREREG.md, verbatim)", "num": False, "c": "text"}],
                     tab_rows, caption="Forward tests as frozen")
    src_extra = (f'Scored result: <code>{esc(fw["_path"])}</code>.' if fw else
                 'No scored result is committed yet (<code>data/forward/score_*/result.json</code> with <code>is_score: true</code>).')
    return card(
        cid="forward", kind="pre", headline=headline, shows=shows, notshows=notshows, figure=fig,
        caption=(f'Window: {esc(w0)} to {esc(w1)} (UTC). Scoring opens {esc(opens)}. Units differ by line and are named in each title; '
                 f'axes do not start at zero because they show a band, not a magnitude.'),
        extra=lst, notes=notes,
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
    """Where the funding hop of an escrow unshield is traced per delivery and where it is attributed from samples, read
    from data/raw/escrow/deliveries.csv. Before the boundary the file mixes both kinds of row; from the first day
    after the last sample-attributed row on, every delivery is traced (attribution "row"). Returns that first day, and
    the first and last sampled day in the same calendar month before it (None when there are none)."""
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
            v, title="Share of net issuance offset, % (full scale: 100% is all of net issuance)", tag="A",
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
                  {"label": "Of which the buyback wallet alone (a subset, not an extra rung)",
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
                               esc("sum of the three rows below")]},
         {"k": None, "cells": [esc("Of which the buyback wallet alone"), ctx.M("ladder_buyback_only_pct_of_issuance", 2),
                               esc("a subset of the total, not nested with the rows below")]},
         {"k": None, "cells": [esc("Traceable to two recurring public fee collectors"), ctx.M("ladder_public_collectors_pct_of_issuance", 2),
                               esc("fee collectors A and B")]},
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
        headline=(f'NEAR delivered to NEAR&rsquo;s three Intents revenue wallets offset {ctx.M("ladder_all_wallets_pct_of_issuance", 2)}% of net '
                  f'issuance; only {ctx.M("ladder_public_collectors_pct_of_issuance", 2)} points trace to public fee collectors and '
                  f'{ctx.M("ladder_escrow_unshields_pct_of_issuance", 2)} arrive as unshields from the Confidential Intents escrow, fee stream unattested.'),
        shows=(f'How much of NEAR&rsquo;s net issuance ({ctx.M("net_issuance_near_per_day_window", 0)} NEAR a day over the 30 days {window_text(ctx, 30)}) '
               f'was matched by NEAR delivered to the three revenue wallets, split by how it arrived: '
               f'{ctx.M("ladder_public_collectors_pct_of_issuance", 2)}% from two recurring public fee collectors and '
               f'{ctx.M("ladder_escrow_unshields_pct_of_issuance", 2)}% released from the Confidential Intents escrow, plus '
               f'{ctx.M("ladder_other_pct_of_issuance", 2)}% from one other source.'),
        notshows=(f'Which fee stream pays for the escrow releases: the NEAR verifiably arrived, but the public chain cannot split the '
                  f'{ctx.M("ladder_escrow_unshields_pct_of_issuance", 2)} points between the two candidate NEAR-side streams that fit, so measured value capture is a '
                  f'range, {ctx.M("ladder_public_collectors_pct_of_issuance", 2)}% to {ctx.M("ladder_all_wallets_pct_of_issuance", 2)}% of issuance.'),
        figure=fig,
        caption=(f'Window: the 30 days {window_text(ctx, 30)} (UTC). Unit: percent of net issuance. Both panels start at zero; Panel B is a zoom of Panel A.'),
        extra=figs,
        notes=('The two candidate readings are near.com&rsquo;s fees and the Confidential Infrastructure Fee. A per-stream attestation by NEAR would turn the '
               'range into one number. Nothing here alleges misconduct: it is a privacy feature working as designed, and the question is auditability.',
               'The rungs are not nested: collectors, escrow and one other source add up to all three wallets, and the buyback-wallet rung is a subset of the total.',
               f'The total reconciles with DefiLlama: {ctx.M("revwallets_near_k")}K NEAR is {ctx.M("revwallets_vs_llama_rev_pct")}% of its reported Intents revenue '
               f'for the same days. Even the top of the range covers about a sixth of issuance, and the buyback wallet&rsquo;s NEAR is held, not burned.',
               f'No valuation is made here. The range is the finding: {ctx.M("ladder_all_wallets_pct_of_issuance", 2)}% is what reached the three wallets and '
               f'{ctx.M("ladder_public_collectors_pct_of_issuance", 2)}% is what is traced to public fee collectors. None of this feeds the rating rule.'),
        source=source_p(ctx, sql=("sql/buyback_withdraw_sources.sql",),
                        raw=("raw/escrow/deliveries.csv", "raw/escrow/issuance_reads.json", "raw/escrow/verify_sample.json",
                             "raw/bq/buyback_withdraw_sources.json"),
                        code=("pipeline/compute.py", "pipeline/fetch_escrow.py"),
                        upstream=("BigQuery public dataset bigquery-public-data.crypto_near_mainnet_us, table execution_outcomes (intents.near native_withdraw events)",
                                  "FastNEAR transaction API and NEAR archival RPC (keyless) for the funding hops and the two total_supply reads")),
        query=query_details(ctx, sql=("sql/buyback_withdraw_sources.sql",),
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
    where = (f"Earlier deliveries, and the funding hop of every delivery, come from the sources that <code>data/MANIFEST.json</code> records "
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
            brackets.append({"i0": traced[0], "i1": traced[-1], "label": f"funding hop traced per delivery from {traced_from}"})
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
        headline=(f'The escrow&rsquo;s share of the buyback wallet&rsquo;s NEAR rose from {ctx.M("escrow_share_buyback_2026_07_pct")}% in July to '
                  f'{ctx.M("escrow_share_buyback_2026_10_pct")}% in October, and is {ctx.M("escrow_share_buyback_2026_11_pct")}% for {partial_month_note(ctx)}.'),
        shows=('For each calendar month, the share of NEAR delivered to <code>buybacks.multisignature.near</code> that came from single-use accounts '
               'funded by the Confidential Intents escrow (unshields) rather than from the recurring fee collectors.'),
        notshows='Which fee stream the escrow NEAR comes from, which is unattested, and any share in USD terms: these are shares of NEAR delivered.',
        figure=fig,
        caption=f'Window: 2026-07-07 to {esc(asof)} (UTC), by calendar month. Unit: percent of NEAR delivered. The axis starts at zero.',
        extra=figs,
        notes=(f'Before {traced_from} the funding of each delivery is attributed from samples; from that date every delivery&rsquo;s funding hop is traced, so the '
               f'earlier months are less firmly established. July starts on 2026-07-07 and November covers {partial_month_note(ctx)} only.',
               f'In the 30-day window all {ctx.M("escrow_funded_exact_30d_n")} single-use deliveries are recorded as funded by the escrow for the exact amount, to the '
               f'yoctoNEAR ({ctx.M("escrow_funded_exact_30d_pct")}%). It tallies two columns of the per-delivery table over the window&rsquo;s single-use accounts, a set that the committed BigQuery output defines without them; '
               f'the funding scan that filled the columns is not in this repository.',
               f'The re-read against the chain on 2026-11-08 (<code>python3 -m pipeline.fetch_escrow verify --all</code>, output in '
               f'<code>data/raw/escrow/verify_all.json</code>): {ctx.M("escrow_recheck_rows_ok_n")} of {ctx.M("escrow_recheck_rows_n")} rows pass every check, the other '
               f'{ctx.M("escrow_recheck_failed_n")} fail on block height alone (one to three blocks off), and all {ctx.M("escrow_recheck_funding_hops_n")} funding '
               f'transfers pass, {ctx.M("escrow_recheck_window_funding_ok_n")} of them in the window. The command therefore ends with a failing exit status on these data.',
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
        headline=(f'NEAR&rsquo;s explicit fee inside 1Click rose from {ctx.M("take_b1_bb_explicit_bp")} bp of volume ({esc(labels[0])}) to '
                  f'{ctx.M("take_b3_bb_explicit_bp")} bp ({esc(labels[2])}), mostly because more volume carries a buyback fee entry; partner '
                  f'fees were {ctx.M("take_b3_partner_bp")} bp in the last block.'),
        shows=('NEAR&rsquo;s explicit buyback fee, partner fees and, on a different basis, captured revenue, in basis points of volume, over three '
               '30-day blocks of 1Click swaps from the NEAR Intents Explorer API.'),
        notshows=('The period since the 2026-02-23 fee switch (this covers 90 days), and a like-for-like comparison of the captured-revenue bars, because '
                  'DefiLlama&rsquo;s volume series steps up on 2026-09-01.'),
        figure=fig,
        caption=('Windows: 2026-08-07 to 2026-11-04 in three 30-day blocks (UTC). Unit: basis points. The axis starts at zero. Grey bars use a '
                 'different denominator and are not like-for-like with the other two.'),
        notes=(f'NEAR&rsquo;s explicit take rose mainly because more volume carries a buyback fee entry ({ctx.M("take_b1_vol_with_bb_pct")}% of volume in the first block, '
               f'{ctx.M("take_b3_vol_with_bb_pct")}% in the last), not because SwapKit&rsquo;s share fell: it stayed between {ctx.M("take_b1_swapkit_vol_pct")}% and '
               f'{ctx.M("take_b3_swapkit_vol_pct")}%.',
               f'1Click&rsquo;s share of DefiLlama&rsquo;s volume falls from {ctx.M("oneclick_share_of_llama_week_before_0901_pct")}% in the week before 2026-09-01 to '
               f'{ctx.M("oneclick_share_of_llama_week_after_0901_pct")}% in the week from that day, with no matching change in 1Click&rsquo;s own volume. That is consistent with '
               f'DefiLlama counting more of Intents&rsquo; volume from that date; if so, the first block&rsquo;s {ctx.M("take_b1_captured_bp")} bp is overstated and the true '
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
        a, ha = hbar_panel(v, title="Share of 1Click volume and of NEAR's explicit buyback fees, 30 days, % (bars start at zero)", tag="A",
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
                    ("SwapKit share of all Intents volume, one-sided", f'{ctx.M("swapkit_share_of_intents_net_pct")}%'),
                    ("Volume HHI, SwapKit as one channel / split", f'{ctx.M("volume_channel_hhi_swapkit_merged", 3)} / {ctx.M("volume_channel_hhi", 3)}'),
                    ("Explicit buyback fee HHI", ctx.M("buyback_fee_hhi", 3))])
    return card(
        cid="partners", kind="exp",
        headline=(f'SwapKit routes {ctx.M("swapkit_vol_share_pct")}% of 1Click volume but paid NEAR ${ctx.M("swapkit_buyback_fees_usd", 0)} in explicit fees '
                  f'over 30 days; if it left, NEAR would lose about {ctx.M("swapkit_exit_traceable_pct")}% of captured revenue on the traceable '
                  f'streams. The ceiling is {ctx.M("swapkit_exit_ceiling_pct")}% if all the escrow NEAR delivered to the buyback wallet counts as SwapKit&rsquo;s, '
                  f'and {ctx.M("swapkit_exit_ceiling_all_escrow_pct")}% if the escrow NEAR reaching the front-end fund is counted too.'),
        shows=(f'For SwapKit and for the channels that pay NEAR the most explicit buyback fees, each channel&rsquo;s share of 1Click volume against its share of '
               f'NEAR&rsquo;s explicit buyback fees over the 30 days {window_text(ctx, 30)}, and what NEAR would lose if SwapKit stopped routing through 1Click.'),
        notshows=(f'Most of the NEAR the buyback wallet receives cannot be traced to any channel on chain, so that part of the exposure is unknown, not zero: '
                  f'the ceilings count every escrow unshield as if it came from SwapKit, which neither candidate reading of that stream supports, and the ledger '
                  f'cannot tell 0% from about {ctx.M("near_share_of_partner_fees_max_pct")}% for SwapKit ({ctx.M("near_share_of_partner_fees_max_tight_pct")}% on the tighter reading).'),
        figure=fig,
        caption=(f'Window: the 30 days {window_text(ctx, 30)} (UTC). Unit: percent. Both panels start at zero. SwapKit&rsquo;s fee bar is drawn to scale and is too short to see. '
                 f'Blue and orange mean volume share and fee share in Panel A only; Panel B uses one colour.'),
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
    if m["fee_ev_partner_fees_nonzero_unmatched_escrow_n"] != m["fee_ev_partner_fees_nonzero_unmatched_n"]:
        raise SystemExit("render: not every unmatched partner fee is in an escrow-routed swap; rewrite the note on the per-swap sample in card_paid()")
    unmatched_word = "entry" if m["fee_ev_partner_fees_nonzero_unmatched_n"] == 1 else "entries"
    title = "Who keeps the listed 1Click fees, and which way 1Click moves NEAR"
    desc = (f"Panel A, bars from zero in multiples of NEAR's entire captured revenue, with a reference line at 1: partners kept {ctx.plain('partners_kept_vs_near_rev_low_x')} "
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
        a, ha = hbar_panel(v, title="Partners' listed fees ÷ NEAR's entire captured revenue (bars start at zero)", tag="A", rows=a_rows, vmax=2.5,
                           ticks=[0, 0.5, 1, 1.5, 2, 2.5], tick_fmt=lambda t: f"{t:g}×",
                           refs=[{"v": 1.0, "label": T("1×: equal to NEAR's whole captured revenue")}])
        b_rows = [
            {"label": "1Click swaps into NEAR", "bars": [bar(m["explorer_into_near_usd_m"], "st2", T("$", Mt("explorer_into_near_usd_m"), "M"),
                                                           f"Into NEAR: ${ctx.plain('explorer_into_near_usd_m')}M")]},
            {"label": "1Click swaps out of NEAR", "bars": [bar(m["explorer_out_of_near_usd_m"], "st2", T("$", Mt("explorer_out_of_near_usd_m"), "M"),
                                                              f"Out of NEAR: ${ctx.plain('explorer_out_of_near_usd_m')}M")]},
        ]
        b, hb = hbar_panel(v, title="1Click swaps with NEAR on one side, USD million, 30 days (bars start at zero)", tag="B", rows=b_rows, vmax=30,
                           ticks=[0, 10, 20, 30])
        return stack([(a, ha), (b, hb)])

    fig = dual(ctx, "chart-paid", title, desc, build)
    tab = table_html(
        [{"h": "Measure", "num": False}, {"h": "Value"}, {"h": "Unit", "num": False}],
        [{"k": None, "cells": [esc("Partner fees listed on 1Click swaps"), ctx.M("explorer_partner_fees_all_usd_k"), esc("USD thousand")]},
         {"k": None, "cells": [esc("NEAR's captured revenue, three revenue wallets"), ctx.M("revwallets_usd_k"), esc("USD thousand")]},
         {"k": None, "cells": [esc("Partners kept ÷ NEAR's revenue, wide lower bound"), ctx.M("partners_kept_vs_near_rev_low_x"), esc("×")]},
         {"k": None, "cells": [esc("Partners kept ÷ NEAR's revenue, tight lower bound"), ctx.M("partners_kept_vs_near_rev_low_tight_x"), esc("×")]},
         {"k": None, "cells": [esc("Partners kept ÷ NEAR's revenue, upper"), ctx.M("partners_kept_vs_near_rev_high_x"), esc("×")]},
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
        headline=(f'Partners kept at least {ctx.M("partners_kept_vs_near_rev_low_x")}× NEAR&rsquo;s entire captured revenue ({ctx.M("partners_kept_vs_near_rev_low_tight_x")}× '
                  f'on the tighter reading), and 1Click was a net route out of NEAR: ${ctx.M("explorer_out_of_near_usd_m")}M out against '
                  f'${ctx.M("explorer_into_near_usd_m")}M in over 30 days.'),
        shows=(f'The fees 1Click swaps listed for partners (${ctx.M("explorer_partner_fees_all_usd_k")}K) as a multiple of NEAR&rsquo;s entire captured Intents revenue '
               f'(${ctx.M("revwallets_usd_k")}K), between {ctx.M("partners_kept_vs_near_rev_low_x")}× and {ctx.M("partners_kept_vs_near_rev_high_x")}×, and 1Click swap volume '
               f'into and out of NEAR, over the 30 days {window_text(ctx, 30)}.'),
        notshows=(f'The other half of Intents: 1Click is {ctx.M("explorer_vs_llama_net_pct")}% of DefiLlama&rsquo;s volume on a one-sided basis, and near.com, direct solver flow '
                  f'and other integrations have a fee structure the Explorer API does not show, so we do not extrapolate.'),
        figure=fig,
        caption=(f'Window: the 30 days {window_text(ctx, 30)} (UTC). Units: a multiple of NEAR&rsquo;s revenue (Panel A) and USD million (Panel B). Both axes start at zero. '
                 f'In Panel A the blue bar is the wide lower bound the headline quotes and the grey bars are the tight reading and the upper bound; Panel B uses one colour for both bars.'),
        extra=figs,
        notes=(f'The wide reading counts all the NEAR in the buyback wallet that the explicit fee entries do not explain as partner fees passed on to NEAR: partners kept '
               f'at least {ctx.M("partners_kept_vs_near_rev_low_x")}×, and at most {ctx.M("near_share_of_partner_fees_max_pct")}% of the fees on partner swaps with no buyback fee '
               f'entry reached NEAR. The tight reading counts only the escrow unshields, reading collector B&rsquo;s NEAR as quote improvement, a role that is inferred, '
               f'not proven: {ctx.M("partners_kept_vs_near_rev_low_tight_x")}× and {ctx.M("near_share_of_partner_fees_max_tight_pct")}%. Both leave out the escrow NEAR '
               f'that reached the front-end fund, where the ledger cannot exclude a partner settlement.',
               f'In the per-swap sample ({ctx.M("fee_ev_swaps_n")} swaps from {ctx.M("fee_ev_hours_with_swaps_n")} sampled hours) every non-zero partner fee entry was matched '
               f'on chain by a payment of the listed amount, except {ctx.M("fee_ev_partner_fees_nonzero_unmatched_n")} unmatched {unmatched_word}, in a swap whose tokens went '
               f'into the Confidential Intents escrow, where the public chain shows no fee on that route. A further {ctx.M("fee_ev_swapkit_fees_zero_rate_n")} SwapKit entries '
               f'and {ctx.D("fee_ev_other_partner_fees_zero_rate_n+fee_ev_zodl_fees_zero_rate_n", 0)} others list a zero rate, so nothing is owed on them and no amount can '
               f'match. So no split comes out of a listed fee in that sample; whatever 1Click charges on top, and whether it forwards any of it to NEAR, is not visible.',
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
            v, title="NEAR Intents' share of Intents + THORChain + Chainflip + Maya volume, % (axis starts at zero)",
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
        headline=(f'NEAR Intents is {ctx.M("intents_share_peerset_30d_pct")}% of its cross-chain peer set by reported volume over 30 days and '
                  f'{ctx.M("intents_share_peerset_365d_pct")}% over 365 days.'),
        shows=(f'NEAR Intents&rsquo; share of the combined reported volume of Intents, THORChain, Chainflip and Maya (DefiLlama), by calendar month from '
               f'{esc(rows[0]["month"])} to {esc(last)}; the monthly peak was {ctx.S("peer_share_monthly." + peak + ".near-intents")}% in {esc(peak)}.'),
        notshows=(f'Volume is not the token: only {ctx.M("explorer_near_side_swap_share_pct")}% of 1Click volume has NEAR on one side, and a share of volume says '
                  f'nothing about revenue.'),
        figure=fig,
        caption=f'Window: {esc(rows[0]["month"])} to {esc(last)} (UTC), by calendar month. Unit: percent of the peer set&rsquo;s reported volume. The axis starts at zero.',
        extra=figs,
        notes=(f'Reported volume appears to count both legs of an Intents swap (DefiLlama&rsquo;s adapter states no methodology); on a net, halved basis the 30-day share is {ctx.M("intents_share_peerset_30d_net_pct")}%.',
               f'The last month covers {partial_month_note(ctx)} only. Forward test F4 asks whether the share over 2026-11-06 to 2026-11-13 is at least '
               f'{ctx.K("f4_min_pct")}% on the reported basis; this chart is context for it, not the test.'),
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
        a, ha = vcol_panel(v, title="Captured revenue per month, USD million (bars start at zero)", tag="A", cats=cats,
                           series=[{"cls": "s1", "name": "Captured revenue"}], ymax=top, yticks=ticks,
                           h_plot=96 if not v.narrow else 90, label_step=6 if v.narrow else 3)
        bticks, btop = nice_axis(max(r["captured_bp"] for r in rows), 4)
        b, hb = line_panel(
            v, title="Captured revenue ÷ DefiLlama reported volume, basis points (axis starts at zero)", tag="B",
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
        headline=(f'Captured Intents revenue was ${ctx.S("intents_monthly.2026-10.rev_m")}M in October 2026, '
                  f'{ctx.S("intents_monthly.2026-10.captured_bp")} bp of reported volume, up from '
                  f'{ctx.S("intents_monthly.2026-09.captured_bp")} bp in September.'),
        shows=('Monthly captured revenue (DefiLlama dailyRevenue, which counts NEAR delivered to NEAR&rsquo;s revenue wallets) and captured revenue as basis '
               'points of DefiLlama&rsquo;s reported Intents volume.'),
        notshows=('Fees accrued: DefiLlama&rsquo;s revenue is NEAR delivered to the wallets, so a month&rsquo;s figure depends on when deliveries land, and the chart '
                  'does not say which fee stream paid.'),
        figure=fig,
        caption=(f'Window: {esc(rows[0]["month"])} to {esc(last)} (UTC), by calendar month; the last month covers {partial_month_note(ctx)} only. '
                 f'Units: USD million (Panel A) and basis points (Panel B). Both axes start at zero.'),
        extra=figs,
        notes=(f'Revenue before the 2026-02-23 fee switch counts as captured, as DefiLlama labels it. Reported volume was ${ctx.S("intents_monthly.2026-10.vol_b")}B in October. '
               f'The volume is DefiLlama&rsquo;s reported leg-sum, which steps up on 2026-09-01 (see the take chart above).',
               f'The last month covers {partial_month_note(ctx)} only. Forward test F3 asks whether the captured take over 2026-11-06 to 2026-11-13 is below '
               f'{ctx.K("f3_max_bp")} bp; this chart is context for it, not the test.'),
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
        a, ha = line_panel(
            v, title="Total supply at each month end, million NEAR", tag="A", xlabels=[d[:7] for d in me_dates],
            xtick_idx=tick_every(len(me_dates), 6 if v.narrow else 3),
            series=[{"cls": "l1", "dot": "s1", "ys": [by_date[d] for d in me_dates],
                     "end": T(St(f"supply_daily.{me_dates[-1]}.supply_m"), "M")}],
            ymin=lo, ymax=hi, yticks=[1200, 1240, 1280, 1320], h_plot=96 if not v.narrow else 90, area_first=True,
            ynote="The vertical axis starts at 1,200M, not zero.")
        cats = [{"label": date_short(r["date"]), "vals": [r["change_k"]], "txts": [None]} for r in daily]
        b, hb = vcol_panel(v, title="Net issuance per day, thousand NEAR (bars start at zero)", tag="B", cats=cats,
                           series=[{"cls": "s1", "name": "Net issuance"}], ymax=120, yticks=[0, 40, 80, 120],
                           h_plot=96 if not v.narrow else 90, label_step=30 if v.narrow else 15,
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
        headline=(f'NEAR&rsquo;s supply grew {ctx.M("net_supply_growth_365d_pct")}% over 365 days; net issuance ran at {ctx.M("net_issuance_near_per_day_30d_k")}K NEAR a day '
                  f'over the last 30 days.'),
        shows=(f'Total NEAR supply at each month end and day-to-day net issuance (mint minus burn) over the 90 days {window_text(ctx, 90)}; net issuance is the quantity the ladder is measured against.'),
        notshows=('Who receives the issuance, or what changes after HSP-029, an issuance cut whose on-chain timelock ends on 2026-11-16, after the deadline, and which also needs validator adoption.'),
        figure=fig,
        caption=f'Window: Panel A, month ends from {esc(me_dates[0])} to {esc(me_dates[-1])} (the last point is the as-of date); Panel B, the 90 days {window_text(ctx, 90)} (UTC). Units: million NEAR and thousand NEAR a day.',
        extra=figs,
        notes=(f'In those 90 days {ctx.M("h1a_gross_issuance_90d_m")}M NEAR were minted (read from {ctx.M("h1a_epochs_in_window")} epoch-boundary block headers), '
               f'{ctx.M("h1a_burn_90d_k")}K NEAR burned and the net supply change was {ctx.M("h1a_net_supply_change_90d_m")}M NEAR.',
               f'NEAR mints once per epoch, and a UTC day holds three or four epoch starts, so the daily bars come in two heights: the taller bars are the four-epoch days. '
               f'Daily values are differences between Nearblocks <code>total_supply</code> values that this repo keeps to the nearest thousand NEAR, so each carries up to about '
               f'a thousand NEAR of rounding. The ladder uses {ctx.M("net_issuance_near_per_day_window", 0)} NEAR a day from two archival reads, a slightly different '
               f'denominator from the {ctx.M("net_issuance_near_per_day_30d_k")}K here.',
               f'Forward test F2 asks whether the mean net increase over 2026-11-06 to 2026-11-13 is between {ctx.K("f2_lo")}K and {ctx.K("f2_hi")}K a day; this chart is '
               f'context for it, not the test.'),
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
        for key, name, tag in (("tx_k", "Transactions per day, thousand (axis starts at zero)", "A"),
                               ("active_accounts_k", "Active accounts per day, thousand (axis starts at zero)", "B")):
            ys = [r[key] for r in rows]
            yt, top = nice_axis(max(ys), 5)
            panels.append(line_panel(
                v, title=name, tag=tag, xlabels=labels, xtick_idx=ticks_x,
                series=[{"cls": "l1", "dot": "s1", "ys": ys, "end": T(St(f"l1_daily.{last}.{key}"), "K")}],
                ymin=0, ymax=top, yticks=yt, tick_fmt=lambda t: f"{t:,.0f}", h_plot=96 if v.narrow else 104,
                vmarks=[{"i": si, "date": step, "label": T("step ", Mt("l1_step_date"))}]))
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
    lead = f'<p class="note">Four daily counts, in thousands, on {esc(ref)} and then on {esc(step)}, the day of the fall:</p>'
    return card(
        cid="usage", kind="exp",
        headline=(f'Daily active accounts averaged {M("active_accounts_30d_k")}K over the 30 days to {M("asof")}, {M("active_accounts_30d_yoy_pct")}% on the same 30 days '
                  f'a year earlier; daily transactions are {M("tx_per_day_30d_yoy_pct")}% on a year earlier, but most of that is one step on {M("l1_step_date")}, '
                  f'not a gradual decline.'),
        shows=(f'Nearblocks&rsquo; counts of transactions (Panel A) and of active accounts (Panel B) on each day from {esc(first)} to {esc(last)}, in thousands. '
               f'A dashed line marks {esc(step)}, the largest one-day fall in daily transactions in the 365 days to {esc(asof)}. The headline averages are '
               f'the 30 days {window_text(ctx, 30)} against the same 30 days a year earlier.'),
        notshows=('Why the step happened: this repository holds no definition of what Nearblocks counts, and these data cannot tell a change in what is counted, '
                  'or the end of automated traffic, from a real fall in usage. That active accounts are people: this repository applies no sybil or bot filter to the counts. '
                  'Contract usage: the active-contract count falls by an order of magnitude on the same days (see the table), so it is not used. Anything from '
                  'BigQuery: these are Nearblocks aggregates, not the BigQuery queries the track brief names. A cause for any of it.'),
        figure=fig,
        caption=(f'Window: {esc(first)} to {esc(last)} (UTC), one point per day. Unit: thousand a day. Both axes start at zero. The dashed line is {esc(step)}. '
                 f'The headline figures are 30-day averages; each line shows single days, so its last point, the as-of date, differs from them.'),
        extra=f'{lead}{figs}',
        notes=(f'The transactions series falls in one step, from {M("l1_step_tx_before_k")}K to {M("l1_step_tx_after_k")}K between {esc(ref)} and {esc(step)}. '
               f'Active contracts and new accounts fall with it, but active accounts barely move ({M("l1_step_active_accounts_before_k")}K to '
               f'{M("l1_step_active_accounts_after_k")}K): they fall gradually, with spikes this card does not explain, not in a step. Since the step, the change is {M("tx_per_day_since_step_pct")}% for '
               f'daily transactions and {M("active_accounts_since_step_pct")}% for daily active accounts (the latest 30 days against the 30 days that start on {esc(step)}).',
               'Both counts are lower than a year ago, but they fall differently. This card does not decompose either fall, it is not a pre-registered test, and it feeds '
               'neither the rating rule nor any other result.',
               'The track brief names daily active accounts, transaction counts and contract usage. This card reports the first two from Nearblocks aggregates and says why '
               'it does not use the third; none of the committed BigQuery queries counts any of them.'),
        source=source_p(ctx, raw=("raw/nearblocks/charts.json",), code=("pipeline/fetch_keyless.py", "pipeline/compute.py"),
                        upstream=("Nearblocks /v1/charts daily transactions, active accounts, active contracts and new accounts",)),
        query=query_details(ctx, endpoints=(
            ("Endpoint", "GET https://api.nearblocks.io/v1/charts"),
            ("Fetcher", "python3 -m pipeline.fetch_keyless (no key), function fetch_nearblocks()"),
            ("Step and series", "pipeline/compute.py, function l1_usage(): the step day, the four counts on the two days, the change since the step, and series l1_daily in data/series.json"),
            ("Averages", "pipeline/compute.py, function build(): the 30-day averages and the year-on-year changes"))),
        data=data_details(tab_step, tab_change, tab_daily))


# ------------------------------------------------------------------ page
PRE_CARDS = (("h1a", "H1a: staking outflow", card_h1a), ("h1b", "H1b: net exchange inflow", card_h1b),
             ("h1c", "H1c: identified buying", card_h1c), ("rating", "Rating rule inputs", card_rating),
             ("forward", "Forward tests F1-F4", card_forward))
EXP_CARDS = (("ladder", "The value-capture ladder", card_ladder), ("escrow", "Escrow share by month", card_escrow),
             ("take", "NEAR's take in 1Click", card_take), ("partners", "Partner concentration", card_partners),
             ("paid", "Who keeps the fees", card_paid), ("peers", "Share of the peer set", card_peers),
             ("revenue", "Monthly revenue and take rate", card_revenue), ("supply", "Supply and net issuance", card_supply),
             ("usage", "Network usage", card_usage))


def tile(*, label: str, status_markup: str, kind: str, big: str, note: str, href: str) -> str:
    return (f'<li class="tile"><p class="st">{icon(kind, 24)}{status_markup}</p><p class="tlabel">{label}</p>'
            f'<p class="big">{big}</p><p class="tnote">{note}</p><a href="{href}">See the chart</a></li>')


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
    fw = ctx.forward
    tiles = [
        tile(label="H1a · most staking rewards stay staked", status_markup=M("h1a_pass_as_written"),
             kind=status_kind("pass" if m["h1a_pass_as_written"] else "fail"),
             big=f'{M("h1a_ratio_as_written_x")}×',
             note=f'Net staking outflow ÷ staking rewards over 90 days. A pass needed under {K("h1a_pass_below_x")}×.', href="#chart-h1a"),
        tile(label="H1b · less NEAR reaches exchanges than is minted", status_markup=M("h1b_verdict"), kind=status_kind(str(m["h1b_verdict"])),
             big=f'{M("h1b_net_inflow_lower_m")}M to {M("h1b_net_inflow_upper_m")}M',
             note=(f'Net exchange inflow in NEAR, against {M("h1a_gross_issuance_90d_m")}M NEAR minted. Label coverage is {M("h1b_coverage_count_pct")}%, '
                   f'below the {K("h1b_coverage_min_pct")}% required for a point result.'), href="#chart-h1b"),
        tile(label="H1c · identified buyers absorb a larger share", status_markup=M("h1c_verdict"), kind=status_kind(str(m["h1c_verdict"])),
             big=f'{M("h1c_ratio_lower_pct")}% and {M("h1c_ratio_upper_pct")}%',
             note=f'Identified buying ÷ net exchange inflow at the lower and upper bound. A pass needs {K("h1c_min_pct")}% under both.',
             href="#chart-h1c"),
        tile(label="Rating · the frozen rule", status_markup=M("rating_output"), kind=status_kind(str(m["rating_output"])),
             big=f'{M("rating_g_obs_pct")}% against {M("rating_g_req_pct")}%',
             note=(f'Observed against required growth in captured revenue, a year. Buy needs H1b to pass; Avoid needs it to fail and observed growth under '
                   f'half the required. H1b is {M("h1b_verdict")}, so the rule outputs {M("rating_output")}, which carries no view on NEAR.'), href="#chart-rating"),
    ]
    if fw:
        words = [str(fw["results"].get(f, {}).get("result", "not scorable")) for f in ("F1", "F2", "F3", "F4")]
        npass, nmiss = words.count("PASS"), words.count("MISS")
        nns = 4 - npass - nmiss
        tiles.append(tile(label="Forward tests F1 to F4", status_markup="scored", kind="scored",
                          big=(f'<span data-f="@count.PASS" data-scale="1">{npass}</span> pass, '
                               f'<span data-f="@count.MISS" data-scale="1">{nmiss}</span> miss'),
                          note=(f'<span data-f="@count.not scorable" data-scale="1">{nns}</span> not scorable. '
                                f'Scored by <code>python3 -m pipeline.score_forward --score</code>; misses included.'),
                          href="#chart-forward"))
    else:
        opens = sf.SCORE_NOT_BEFORE.strftime("%Y-%m-%d %H:%M UTC")
        tiles.append(tile(label="Forward tests F1 to F4", status_markup="pending", kind="pending", big="F1 to F4",
                          note=(f'Window {esc(sf.WINDOW[0])} to {esc(sf.WINDOW[1])}. Scored after {esc(opens)} by '
                                f'<code>python3 -m pipeline.score_forward --score</code>, misses included.'), href="#chart-forward"))
    freeze_stamp, freeze_gap = freeze_order(ctx)
    return (f'<section id="scorecard" aria-labelledby="scorecard-h"><h2 id="scorecard-h">Scorecard (pre-registered)</h2>'
            f'<p class="note">Frozen at commit <code>{FREEZE_COMMIT}</code> ({FREEZE_UTC} UTC), {freeze_gap} before the first BigQuery result the repository records '
            f'({freeze_stamp} in <code>data/MANIFEST.json</code>). Commit and manifest times are written by the author&rsquo;s machine, and nothing external '
            f'attests them; BigQuery job IDs, which embed their creation time, are recorded only for the H1b and H1c runs and one October escrow scan, not for the '
            f'H1a queries. The table <a href="{esc(gh("PREREG.md"))}#{PREREG_ANCHOR}">&ldquo;What we had already '
            f'seen&rdquo; in PREREG.md</a> lists the data already in hand at the freeze. Each status is shown by a shape and a word, not by colour alone.</p>'
            f'<ul class="tiles">{"".join(tiles)}</ul></section>')


def not_computed(ctx: Ctx) -> str:
    M, m = ctx.M, ctx.m
    items = [
        ("Net exchange inflow as one number (H1b, H1c).",
         f'Only {M("h1b_coverage_count_pct")}% of the top-100 receivers carry an exchange label ({M("h1b_coverage_tier1_count_pct")}% a cited one; the rest are '
         f'labelled by our sweep rule). The binding gap is labelling, not data: no citable NEAR '
         f'address was found for OKX, Coinbase, Kraken, Bybit, HTX, Crypto.com, Upbit or Bithumb, and nothing is labelled from its name alone.'),
        ("Which fee stream pays the escrow releases.",
         f'{M("ladder_escrow_unshields_pct_of_issuance", 2)} points of the ladder arrive as unshields from the Confidential Intents escrow. The public chain does not show which fee '
         f'stream funds them; a per-stream attestation by NEAR would turn the range into one number.'),
        ("NEAR&rsquo;s share of partner fees.",
         f'On partner swaps with no buyback entry the ledger puts NEAR&rsquo;s share, as it reaches the buyback wallet, at no more than {M("near_share_of_partner_fees_max_pct")}% '
         f'({M("near_share_of_partner_fees_max_tight_pct")}% on the tighter reading) but does not measure it.'),
        ("The other half of Intents.",
         f'1Click is {M("explorer_vs_llama_net_pct")}% of DefiLlama&rsquo;s volume on a one-sided basis. near.com, direct solver flow and other integrations have a fee '
         f'structure the Explorer API does not show, and we do not extrapolate.'),
        ("Contract usage.",
         f'The track brief names it, and the Nearblocks snapshot has an active-contract count, but that count falls from {M("l1_step_contracts_before_k")}K on '
         f'{esc(m["l1_step_ref_date"])} to {M("l1_step_contracts_after_k")}K on {esc(m["l1_step_date"])}, an order of magnitude in two days, while this repository holds no '
         f'definition of what is counted. The usage card&rsquo;s table shows the step; no finding rests on it.'),
        ("The track brief&rsquo;s BigQuery topics for daily active accounts and transaction counts.",
         'No BigQuery query was written for them: the committed queries cover staking, exchange and Intents flows. The usage card uses Nearblocks aggregates instead, '
         'and says so; this repository applies no sybil or bot filter to them.'),
        ("Who the sellers were.", 'NEAR is fungible, so every flow here is a market-wide balance. Nothing says which coins were sold.'),
        ("Longer-dated predictions P1 to P3.", 'They resolve on 2027-05-04 and 2027-11-04 and cannot be scored yet.'),
        ("HSP-029&rsquo;s issuance cut.",
         'Its on-chain timelock ends on 2026-11-16, after the submission deadline, and the proposal text also says the cut needs validator adoption through a protocol upgrade. G_req assumes the ramp; we state it as a pending resolver and do not predict it.'),
        ("Earlier work.", 'Prior exploratory work on NEAR&rsquo;s revenue dashboard and the front-end fund&rsquo;s history is not in this repo and is not cited.'),
    ]
    lis = "".join(f"<li><strong>{a}</strong> {b}</li>" for a, b in items)
    return (f'<section id="not-computed" aria-labelledby="nc-h"><h2 id="nc-h">Not computed here</h2>'
            f'<p class="note">The page shows no finding for these: some cannot be computed from the committed sources, and for the others a number would claim more '
            f'than the data support.</p>'
            f'<ul class="plain">{lis}</ul></section>')


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
            f'<p class="note">Do each step in order and compare with what you should see. <code>make reproduce</code> runs steps 2 to 4; '
            f'<code>make render-check</code> runs step 6; <code>make site</code> runs steps 2 to 4 and then step 7, from the raw data to every chart in '
            f'one offline command.</p><ol class="steps">{lis}</ol></section>')


def limits(ctx: Ctx) -> str:
    M = ctx.M
    traced = escrow_attribution(ctx)["traced_from"]
    items = [
        ("Collector roles.",
         f'Collector A&rsquo;s role (the explicit buyback fee) is cross-checked: its priced inflows are {M("collector_a_vs_explicit_fees_pct")}% of the fees the Explorer lists. '
         f'Collector B&rsquo;s role (a share of quote improvement) is inferred from committed, re-checkable per-swap evidence: it is paid a variable cut on '
         f'{M("fee_ev_collector_b_swaps_n")} of {M("fee_ev_swaps_n")} sampled swaps across channels. The quote it would be measured against is not in the Explorer API, '
         f'so the role is consistent with the docs rather than proven.'),
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
        ("Escrow funding", f'before {traced} is sample-attributed.'),
        ("Exchange labels are snapshots", 'dated 2026-11-06. Exchange addresses retired before then may be missing, which biases the lower bound down.'),
        ("The name-filter check", 'behind the lst-pool.near sensitivity read sampled validator sets, not every epoch.'),
        ("The upper bound is mechanical.", 'It treats every unlabelled top-100 receiver as an exchange, including accounts that are probably not.'),
        ("DefiLlama&rsquo;s revenue", 'is NEAR delivered to the wallets, not fees accrued, and its volume series steps up on 2026-09-01.'),
        ("Not reproduced here.", 'Prior exploratory work on NEAR&rsquo;s revenue dashboard and the front-end fund&rsquo;s history is not in this repo and is not cited.'),
    ]
    lis = "".join(f"<li><strong>{a}</strong> {b}</li>" for a, b in items)
    return (f'<section id="limits" aria-labelledby="limits-h"><h2 id="limits-h">Limits</h2>'
            f'<p class="note">These come from the Limits sections of THESIS.md and docs/*.md and from PREREG-ADDENDUM.md. One date is sharper than in THESIS.md: '
            f'escrow funding hops are traced per delivery from {traced}, which a test checks against <code>data/raw/escrow/deliveries.csv</code>.</p>'
            f'<ul class="plain">{lis}</ul></section>')


def header(ctx: Ctx) -> str:
    M = ctx.M
    freeze_stamp, _ = freeze_order(ctx)
    docs = "".join(f'<li><a href="{esc(gh(p))}">{esc(p)}</a></li>' for p in ("THESIS.md", "README.md", "PREREG.md", "PREREG-ADDENDUM.md"))
    return (
        f'<header class="top"><p class="eyebrow">NEAR Hackathon 2026 · Investment Thesis track</p>'
        f'<h1>Who buys and who sells NEAR?</h1>'
        f'<p class="lede">A pre-registered, re-runnable token flow statement for NEAR. <code>python3 -m pipeline.compute</code> recomputes every number from the raw '
        f'snapshots in <code>data/raw/</code>, <code>python3 -m pipeline.render</code> redraws every chart from the committed metrics and snapshots, and <code>make site</code> runs both '
        f'offline in one command. Each chart shows the query behind it, the exact numbers it plots, and one plain sentence on what it shows and what it does not.</p>'
        f'<p class="note">To check any number, open the Data table under its chart, then follow the steps under <a href="#reproduce">Reproduce</a>.</p>'
        f'<dl class="meta">'
        f'<dt>Windows</dt><dd>Value capture: the 30 days to {M("asof")}. Supply: the 90 days {window_text(ctx, 90)}.</dd>'
        f'<dt>Data as of</dt><dd>{M("asof")} (<code>data/metrics.json</code>). Revenue-wallet window {M("revwallets_window")}. NEAR RPC block {M("rpc_block")}.</dd>'
        f'<dt>Data fingerprint</dt><dd><code data-fingerprint="{esc(ctx.fingerprint)}">{esc(ctx.fingerprint)}</code>, the first 16 hex of the SHA-256 of <code>data/MANIFEST.json</code>, '
        f'which pins every raw snapshot.</dd>'
        f'<dt>Pre-registration</dt><dd><code>PREREG.md</code> SHA-256 <code data-prereg="{esc(ctx.prereg_sha)}">{esc(ctx.prereg_sha[:16])}…</code>, frozen at git tag '
        f'<code>{FREEZE_TAG}</code> (commit <code>{FREEZE_COMMIT}</code>, {FREEZE_UTC} UTC), before the first BigQuery result the repository records '
        f'({freeze_stamp} in <code>data/MANIFEST.json</code>); the order rests on the author&rsquo;s own commit and manifest times. '
        f'<a href="{esc(gh("PREREG.md"))}#{PREREG_ANCHOR}">&ldquo;What we had already seen&rdquo;</a> in that file lists the data already in hand.</dd></dl>'
        f'<nav aria-label="Project documents"><ul class="docs">{docs}</ul></nav></header>')


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
_PRE_BLOCK = re.compile(r"<pre\b.*?</pre>", re.S)
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


def build_page(ctx: Ctx, breaks: bool = True) -> str:
    """The whole page. breaks=False leaves the body on a few very long lines (tests/test_render.py compares the two)."""
    pre = "".join(fn(ctx) for _, _, fn in PRE_CARDS)
    exp = "".join(fn(ctx) for _, _, fn in EXP_CARDS)
    toc_pre = "".join(f'<li><a href="#chart-{cid}">{esc(lab)}</a></li>' for cid, lab, _ in PRE_CARDS)
    toc_exp = "".join(f'<li><a href="#chart-{cid}">{esc(lab)}</a></li>' for cid, lab, _ in EXP_CARDS)
    body = (
        f'<a class="skip" href="#main">Skip to the content</a><div class="wrap">{header(ctx)}'
        f'<main id="main">{scorecard(ctx)}'
        f'<nav aria-label="Contents"><h2 class="sr">Contents</h2><p class="note"><strong>Pre-registered:</strong></p><ul class="toc">{toc_pre}</ul>'
        f'<p class="note"><strong>Exploratory:</strong></p><ul class="toc">{toc_exp}</ul></nav>'
        f'<section id="preregistered" aria-labelledby="pre-h"><h2 id="pre-h">Pre-registered results</h2>'
        f'<p class="note">Hypotheses, thresholds and probabilities were fixed in <a href="{esc(gh("PREREG.md"))}">PREREG.md</a> before the first BigQuery result the '
        f'repository records (the scorecard note gives both times and what they rest on). '
        f'Method choices made afterwards are dated in <a href="{esc(gh("PREREG-ADDENDUM.md"))}">PREREG-ADDENDUM.md</a>. Results are published whether they pass, fail or are inconclusive.</p>'
        f'{pre}</section>'
        f'<section id="exploratory" aria-labelledby="exp-h"><h2 id="exp-h">Exploratory (chosen after the freeze)</h2>'
        f'<p class="note">These exhibits were not pre-registered: the author chose them after the freeze. The headline ladder was chosen on 2026-11-07, after H1a, '
        f'H1b and H1c had been scored (<a href="{esc(gh("PREREG-ADDENDUM.md"))}">addendum</a>, 2026-11-07 00:21 UTC entry). None changes a hypothesis, threshold, '
        f'probability or the rating rule, and none feeds it. Treat them as evidence the author chose to show, not as tests.</p>'
        f'{exp}</section>'
        f'{not_computed(ctx)}{reproduce(ctx)}{limits(ctx)}</main>'
        f'<footer><p><strong>Research, not investment advice.</strong> Nothing here is an offer or a recommendation. '
        f'Licence: MIT (<a href="{esc(gh("LICENSE"))}">LICENSE</a>). Source of this page: <a href="{esc(gh("pipeline/render.py"))}">pipeline/render.py</a>.</p></footer></div>')
    head = (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n<meta name="color-scheme" content="light dark">\n'
        '<title>NEAR flow statement dashboard</title>\n'
        '<meta name="description" content="Pre-registered, re-runnable token flow statement for NEAR: who buys and who sells NEAR. '
        'Every chart shows the query behind it and the exact numbers it plots.">\n'
        '<link rel="icon" href="data:,">\n'
        f"<style>\n{css()}\n</style>\n</head>\n")
    return f"{head}<body>\n{break_lines(body) if breaks else body}\n</body>\n</html>\n"


# ------------------------------------------------------------------ build, write, check
def render(root: Path = ROOT, forward_dir: Path | None = None) -> dict[str, bytes]:
    """The files of the site, as {path relative to the repo root: bytes}. Pure: reads files, writes none."""
    ctx = Ctx(root, forward_dir)
    return {f"{SITE_DIR}/{PAGE_NAME}": build_page(ctx).encode("utf-8")}


def summary(files: dict[str, bytes], ctx_root: Path = ROOT) -> str:
    page = files[f"{SITE_DIR}/{PAGE_NAME}"]
    ctx = Ctx(ctx_root)
    return f"{SITE_DIR}/{PAGE_NAME} ({len(page):,} bytes), data fingerprint {ctx.fingerprint}, data as of {ctx.m['asof']}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render the static dashboard from the committed data (offline, deterministic).")
    ap.add_argument("--check", action="store_true", help="exit 1 unless the committed site/ equals a fresh render, byte for byte")
    ap.add_argument("--out", type=Path, help="the site directory to write or check (default: site/ in the repo)")
    ap.add_argument("--root", type=Path, default=ROOT, help="repo root to read from (default: this repo)")
    ap.add_argument("--forward-dir", type=Path, help="directory holding score_*/result.json (default: data/forward)")
    a = ap.parse_args(argv)
    files = render(a.root, a.forward_dir)
    out_dir = a.out if a.out is not None else a.root / SITE_DIR
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
            print("render: site/ is out of date; run `python3 -m pipeline.render` and commit the result", file=sys.stderr)
            return 1
        print(f"render: site/ matches a fresh render ({summary(files, a.root)})")
        return 0
    print(f"render: wrote {summary(files, a.root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
