"""Tests for pipeline/render.py: the static dashboard cannot drift from the data it is built from.

What they guarantee, and what they do not:
  * every number the page prints in a data-attributed span equals the source it names;
  * every other number in the text is a date, an identifier or a named window length, or the test fails;
  * every bar, column, band and dot is drawn at the position its value gives on the axis the panel declares, and the axes
    are the ones written down below (GOLDEN_AXES), so doubling an axis maximum or swapping two bars fails;
  * every headline, scorecard tile, key figure, bar row and column is bound to the metric written down below
    (HEADLINE_REFS, TILE_REFS, KEYFIGS, ROWS, COLS), so a label that reads another metric fails;
  * the committed page equals a fresh render, byte for byte.
They do not check wording beyond the phrases in CARD_PHRASES, and they cannot say that a metric itself is right: that is
what pipeline/compute.py, pipeline/check.py and the raw-data manifest are for.

The page is rendered for four states of the forward-test card (the committed state, no score yet, and two scored fixtures)
so that the suite stays green when data/forward/score_*/result.json is committed on 2026-11-14. Standard library only.
Run: make test
"""
from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import re
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import render as R  # noqa: E402
from pipeline import score_forward as sf  # noqa: E402

METRICS = json.loads((ROOT / "data" / "metrics.json").read_text(encoding="utf-8"))
SERIES = json.loads((ROOT / "data" / "series.json").read_text(encoding="utf-8"))
MANIFEST_BYTES = (ROOT / "data" / "MANIFEST.json").read_bytes()
MANIFEST = json.loads(MANIFEST_BYTES)["files"]
PAGE_KEY = f"{R.SITE_DIR}/{R.PAGE_NAME}"

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
CARD_IDS = ("h1a", "h1b", "h1c", "rating", "forward", "ladder", "escrow", "take", "partners", "paid", "peers", "revenue", "supply")
PRE_IDS = ("h1a", "h1b", "h1c", "rating", "forward")


# ------------------------------------------------------------------ a small DOM
class Node:
    def __init__(self, tag: str, attrs: dict, parent: "Node | None") -> None:
        self.tag, self.attrs, self.parent, self.children = tag, attrs, parent, []

    def iter(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.iter()

    def text(self) -> str:
        return "".join(c if isinstance(c, str) else c.text() for c in self.children)

    def classes(self) -> set[str]:
        return set(self.attrs.get("class", "").split())

    def find_all(self, tag: str | None = None, cls: str | None = None) -> list["Node"]:
        return [n for n in self.iter() if (tag is None or n.tag == tag) and (cls is None or cls in n.classes())]

    def find(self, tag: str | None = None, cls: str | None = None) -> "Node | None":
        r = self.find_all(tag, cls)
        return r[0] if r else None

    def ancestors(self):
        n = self.parent
        while n is not None:
            yield n
            n = n.parent


class DomBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        n = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.cur))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.cur.tag == tag:
            self.cur = self.cur.parent
        else:
            self.errors.append(f"unexpected </{tag}> inside <{self.cur.tag}>")

    def handle_data(self, data):
        self.cur.children.append(data)


def parse(page: str) -> tuple[Node, list[str]]:
    b = DomBuilder()
    b.feed(page)
    b.close()
    if b.cur is not b.root:
        b.errors.append(f"unclosed <{b.cur.tag}>")
    return b.root, b.errors


FILES: dict[str, bytes] = {}
PAGE = ""
DOM: Node
DOM_ERRORS: list[str] = []
LIVE_SCORE: dict | None = None
PENDING_DOM: Node
PENDING_PAGE = ""
VARIANTS: list[tuple[str, Node, str, dict | None]] = []   # (name, dom, page, forward result or None)


def committed_score() -> dict | None:
    """The page's source of truth for the forward tests, read independently of the renderer: the newest (by directory name)
    data/forward/score_*/result.json, if it is a real score. An older real score does not count when a newer file is not one."""
    paths = sorted((ROOT / "data" / "forward").glob("score_*/result.json"))
    if not paths:
        return None
    try:
        d = json.loads(paths[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    ok = isinstance(d, dict) and d.get("is_score") is True and d.get("mode") == "score" and isinstance(d.get("results"), dict)
    return d if ok else None


def setUpModule() -> None:
    """Render the page as committed (whatever is in data/forward) and in three fixed states of the forward-test card."""
    global FILES, PAGE, DOM, DOM_ERRORS, LIVE_SCORE, PENDING_DOM, PENDING_PAGE, VARIANTS
    FILES = R.render()
    PAGE = FILES[PAGE_KEY].decode("utf-8")
    DOM, DOM_ERRORS = parse(PAGE)
    LIVE_SCORE = committed_score()
    with tempfile.TemporaryDirectory() as d:          # an empty forward directory: nothing scored, whatever is committed
        PENDING_DOM, PENDING_PAGE = forward_dom(Path(d))
    VARIANTS = [("live", DOM, PAGE, LIVE_SCORE), ("pending", PENDING_DOM, PENDING_PAGE, None)]
    for name, result in (("scored", fixture_result()), ("scored-real", realistic_result())):
        with tempfile.TemporaryDirectory() as d:
            write_forward(Path(d), "score_20261114T010203Z", result)
            dom, page = forward_dom(Path(d))
        VARIANTS.append((name, dom, page, result))


def metric(path: str):
    cur = METRICS
    for part in path.split("."):
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    return cur


def series_value(path: str):
    name, key, field = path.split(".")
    for row in SERIES[name]:
        if row.get("month", row.get("date")) == key:
            return row[field]
    raise KeyError(path)


def num(text: str) -> float:
    return float(text.strip().replace(",", ""))


def decimals(text: str) -> int:
    t = text.strip()
    return len(t.split(".")[1]) if "." in t else 0


# ------------------------------------------------------------------ helpers shared by the golden, geometry and text tests
NUM_TOKEN = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)")
VALUE_ATTRS = ("data-m", "data-s", "data-d", "data-k")
REF_ATTRS = VALUE_ATTRS + ("data-f", "data-p", "data-count", "data-fingerprint", "data-prereg", "data-r")


def card_node(dom: Node, cid: str) -> Node:
    return next(n for n in dom.find_all("section") if n.attrs.get("id") == f"chart-{cid}")


def refs_in(node: Node, attrs: tuple[str, ...] = VALUE_ATTRS) -> list[tuple[str, str]]:
    """The data references under a node, in document order, as (kind, reference): ("m", "h1a_ratio_as_written_x")."""
    return [(a[5:], n.attrs[a]) for n in node.iter() for a in attrs if a in n.attrs]


def shown_number(node: Node) -> tuple[float, int]:
    """The number a label prints (the first numeric data-referenced span, else the first plain number) and its decimals."""
    for n in node.iter():
        if any(a in n.attrs for a in ("data-m", "data-s", "data-d", "data-f")):
            t = n.text().strip()
            if NUM_TOKEN.fullmatch(t):
                return num(t), decimals(t)
    m = NUM_TOKEN.search(node.text())
    if not m:
        raise AssertionError(f"no number in {node.text()!r}")
    return num(m.group(1)), decimals(m.group(1))


def numbers_in(text: str) -> list[tuple[float, int]]:
    return [(num(m.group(1)), decimals(m.group(1))) for m in NUM_TOKEN.finditer(text)]


def same_number(want: float, got: float, dec: int) -> bool:
    """True when `got`, printed with `dec` decimals, is `want` rounded (the page prints rounded numbers)."""
    return abs(want - got) <= 0.5 * 10 ** -dec + 1e-9


PATH_CMD = re.compile(r"([MmLlHhVvAaZz])([^MmLlHhVvAaZz]*)")


def path_points(d: str) -> list[tuple[float, float]]:
    """The vertices of a path built from the commands pipeline/render.py emits: M L H V h v l a z.

    Arc end points count as vertices. Every arc is a quarter circle, so the extremes of the shape are at its end points."""
    pts: list[tuple[float, float]] = []
    x = y = 0.0
    for cmd, args in PATH_CMD.findall(d):
        a = [float(t) for t in re.findall(r"-?\d+(?:\.\d+)?", args)]
        if cmd in "ML":
            for i in range(0, len(a), 2):
                x, y = a[i], a[i + 1]
                pts.append((x, y))
        elif cmd == "l":
            for i in range(0, len(a), 2):
                x, y = x + a[i], y + a[i + 1]
                pts.append((x, y))
        elif cmd == "H":
            x = a[0]
            pts.append((x, y))
        elif cmd == "V":
            y = a[0]
            pts.append((x, y))
        elif cmd == "h":
            x += a[0]
            pts.append((x, y))
        elif cmd == "v":
            y += a[0]
            pts.append((x, y))
        elif cmd == "a":
            x, y = x + a[5], y + a[6]
            pts.append((x, y))
    return pts


def check_forward_numbers(tc: unittest.TestCase, dom: Node, result: dict) -> int:
    """Every data-f span in the page equals the number (or text) in the scored result it names. Returns how many there are."""
    res = result["results"]
    seen = 0
    for n in dom.iter():
        if "data-f" not in n.attrs:
            continue
        path, scale, text = n.attrs["data-f"], float(n.attrs["data-scale"]), n.text().strip()
        if path.startswith("@count."):
            want = sum(1 for r in res.values() if r["result"] == path.split(".", 1)[1])
            tc.assertEqual(int(text), want, path)
        elif path in ("scored_at", "snapshot_fetched_at"):
            tc.assertEqual(text, result[path], path)
        else:
            fid, key = path.split(".")
            value = res[fid][key]
            if isinstance(value, str):
                tc.assertEqual(text, value, path)
            else:
                tc.assertAlmostEqual(num(text), value / scale, delta=0.5 * 10 ** -decimals(text) + 1e-9, msg=path)
        seen += 1
    return seen


# ------------------------------------------------------------------ fixtures for the forward-test card
def fixture_result(is_score: bool = True, mode: str = "score") -> dict:
    return {"mode": mode, "is_score": is_score, "window": list(sf.WINDOW), "f1_block_target_utc": "2026-11-14T00:00:00Z",
            "scored_at": "2026-11-14T01:02:03Z", "snapshot_fetched_at": "2026-11-14T01:00:00Z", "fetch_errors": {},
            "urls": {}, "results": {
                "F1": {"result": "PASS", "balance_near": 2_303_456.789, "locked_near": 0.0, "band": [2210000.0, 2400000.0],
                       "block_height": 224_000_001, "block_hash": "x", "block_timestamp_ns": 1, "target_utc": "2026-11-14T00:00:00Z"},
                "F2": {"result": "MISS", "mean_near_per_day": 91_234.5, "band": [86000.0, 89500.0], "daily_deltas": {}, "n_deltas": 8},
                "F3": {"result": "PASS", "take_rate_bp": 3.456, "revenue_usd": 1_234_567.0, "volume_usd": 3_571_428_571.0, "threshold_bp": 4.0},
                "F4": {"result": "not scorable", "why": "a DefiLlama peer fetch is missing or before 2026-11-14"}}}


REPO_RAW = ROOT / "data" / "raw"
SCORED_WINDOW = ("2026-10-28", "2026-11-04")  # eight days the committed snapshots cover


def realistic_result() -> dict:
    """What `python3 -m pipeline.score_forward --score` writes, with the real scorer run on the committed snapshots.

    The same field layout as score_forward.main() builds, so a change there that the page does not follow fails here."""
    fetched = "2026-11-14T01:00:00Z"
    src: dict = {}
    for peer in sf.PEERS:
        src[f"llama_volume_{peer}"] = {"url": "repo", "fetched_at": fetched,
                                       "data": json.loads((REPO_RAW / f"llama/volume_{peer}.json").read_text(encoding="utf-8"))}
    src["llama_revenue_near-intents"] = {"url": "repo", "fetched_at": fetched, "data": json.loads(
        (REPO_RAW / "llama/dailyRevenue_near-intents.json").read_text(encoding="utf-8"))}
    src["nearblocks_charts"] = {"url": "repo", "fetched_at": fetched,
                                "data": json.loads((REPO_RAW / "nearblocks/charts.json").read_text(encoding="utf-8"))}
    wallets = json.loads((REPO_RAW / "rpc/wallets.json").read_text(encoding="utf-8"))
    src["rpc_f1"] = {"url": "repo", "fetched_at": fetched, "data": {
        "target_utc": "2026-11-14T00:00:00Z", "block_height": wallets["at_block"], "block_hash": "x", "block_timestamp_ns": 0,
        "view_account": wallets["accounts"][sf.BUYBACK]}}
    snap = {"fetched_at": fetched, "sources": src, "errors": {}}
    res = sf.score(snap, SCORED_WINDOW, sf.SCORE_NOT_BEFORE)
    out = {"mode": "score", "is_score": True, "window": SCORED_WINDOW, "f1_block_target_utc": sf.iso(sf.F1_T),
           "scored_at": "2026-11-14T01:02:03Z", "snapshot_fetched_at": snap["fetched_at"], "fetch_errors": snap["errors"],
           "urls": {k: v["url"] for k, v in snap["sources"].items()}, "results": res}
    return json.loads(json.dumps(out, default=str))     # the scorer writes json.dumps(out, default=str)


def write_forward(tmp: Path, name: str, obj: dict, fname: str = "result.json") -> None:
    d = tmp / name
    d.mkdir(parents=True)
    (d / fname).write_text(json.dumps(obj), encoding="utf-8")


def forward_dom(tmp: Path) -> tuple[Node, str]:
    page = R.render(forward_dir=tmp)[PAGE_KEY].decode("utf-8")
    dom, errors = parse(page)
    assert not errors, errors
    return dom, page


# ------------------------------------------------------------------ tests
class Determinism(unittest.TestCase):
    def test_two_renders_are_identical(self):
        self.assertEqual(R.render(), R.render())
        self.assertEqual(R.render()[PAGE_KEY], FILES[PAGE_KEY])

    def test_no_timestamps_or_hashes_of_the_environment(self):
        # The only 16-hex string is the data fingerprint; no ISO timestamps with a clock time outside the data.
        self.assertIn(R.Ctx().fingerprint, PAGE)
        self.assertEqual(R.Ctx().fingerprint, hashlib.sha256(MANIFEST_BYTES).hexdigest()[:16])

    def test_size_budget(self):
        # One self-contained file: the SQL text, the data tables and every chart drawn twice (wide and phone) are the bulk.
        self.assertLess(len(FILES[PAGE_KEY]), 450 * 1024)

    def test_committed_site_is_current(self):
        committed = ROOT / R.SITE_DIR / R.PAGE_NAME
        if not committed.exists():
            self.skipTest("site/index.html is not committed yet")
        self.assertEqual(committed.read_bytes(), FILES[PAGE_KEY],
                         "site/index.html is out of date: run `python3 -m pipeline.render` and commit the result")


class Structure(unittest.TestCase):
    def test_tags_balanced(self):
        self.assertEqual(DOM_ERRORS, [])

    def test_ids_unique_and_anchors_resolve(self):
        ids = [n.attrs["id"] for n in DOM.iter() if "id" in n.attrs]
        self.assertEqual(len(ids), len(set(ids)), [i for i in ids if ids.count(i) > 1][:5])
        for a in DOM.find_all("a"):
            href = a.attrs.get("href", "")
            if href.startswith("#"):
                self.assertIn(href[1:], ids, href)

    def test_document_basics(self):
        html_el = DOM.find("html")
        self.assertEqual(html_el.attrs.get("lang"), "en")
        self.assertTrue(any(m.attrs.get("name") == "viewport" for m in DOM.find_all("meta")))
        self.assertTrue(DOM.find("title").text().strip())
        self.assertEqual(len(DOM.find_all("h1")), 1)
        self.assertTrue(DOM.find("main"))
        skip = DOM.find("a", "skip")
        self.assertEqual(skip.attrs["href"], "#main")
        body_links = [n for n in DOM.find("body").iter() if n.tag == "a"]
        self.assertIs(body_links[0], skip, "the skip link must be the first link")

    def test_heading_order(self):
        levels = [int(n.tag[1]) for n in DOM.iter() if re.fullmatch(r"h[1-6]", n.tag)]
        self.assertEqual(levels[0], 1)
        for a, b in zip(levels, levels[1:]):
            self.assertLessEqual(b, a + 1, f"heading level jumps from h{a} to h{b}")

    def test_css_supports_dark_and_reduced_motion(self):
        css = DOM.find("style").text()
        self.assertIn("prefers-color-scheme:dark", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn(':root:not([data-theme="light"])', css)
        self.assertIn(':root[data-theme="dark"]', css)
        self.assertRegex(css, r"\.tablewrap\{[^}]*overflow:auto")

    def test_css_text_contrast(self):
        css = DOM.find("style").text()

        def lum(h: str) -> float:
            h = h.lstrip("#")
            r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
            f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
            return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

        def ratio(a: str, b: str) -> float:
            la, lb = sorted((lum(a), lum(b)), reverse=True)
            return (la + 0.05) / (lb + 0.05)

        def tokens(block: str) -> dict[str, str]:
            return dict(re.findall(r"--([a-z0-9]+):(#[0-9a-fA-F]{6})", block))

        light = tokens(re.search(r":root\{(.*?)\}", css, re.S).group(1))
        dark = tokens(re.search(r':root\[data-theme="dark"\]\{(.*?)\}', css, re.S).group(1))
        for name, t in (("light", light), ("dark", dark)):
            for fg in ("ink", "ink2", "muted", "link"):
                for bg in ("surface", "bg"):
                    self.assertGreaterEqual(ratio(t[fg], t[bg]), 4.5, f"{name}: {fg} on {bg}")
            for mark in ("s1", "s2", "ctx"):
                self.assertGreaterEqual(ratio(t[mark], t["surface"]), 3.0, f"{name}: mark {mark}")
        # The dark block in the media query is the same as the data-theme one.
        media = re.search(r"prefers-color-scheme:dark\)\{:root:not\(\[data-theme=\"light\"\]\)\{(.*?)\}\}", css, re.S).group(1)
        self.assertEqual(tokens(media), dark)


class NoExternalResources(unittest.TestCase):
    def test_no_script_at_all(self):
        self.assertEqual(DOM.find_all("script"), [])

    def test_no_remote_or_protocol_relative_urls_in_resources(self):
        for n in DOM.iter():
            for attr in ("src", "srcset", "poster", "data", "action", "formaction", "ping", "manifest"):
                self.assertNotIn(attr, n.attrs, f"<{n.tag}> has {attr}")
            if n.tag == "link":
                self.assertTrue(n.attrs.get("href", "").startswith("data:"), n.attrs)
            for k in n.attrs:
                self.assertFalse(k.startswith("on"), f"inline event handler {k} on <{n.tag}>")
        css = DOM.find("style").text()
        self.assertNotIn("@import", css)
        for m in re.finditer(r"url\(([^)]*)\)", css):
            self.assertNotRegex(m.group(1).strip("'\" "), r"^(https?:)?//", css[max(0, m.start() - 30):m.end()])
        self.assertNotRegex(PAGE, r"""(?:src|href)\s*=\s*["']\s*(?:https?:)?//(?!github\.com/notveiker/)""")

    def test_links_are_anchors_or_repo_urls(self):
        for a in DOM.find_all("a"):
            href = a.attrs["href"]
            self.assertTrue(href.startswith("#") or href.startswith(R.REPO_URL + "/"), href)
            self.assertNotIn("javascript:", href.lower())
        for a in DOM.find_all("a"):
            if a.attrs["href"].startswith("http"):
                self.assertTrue(a.attrs["href"].startswith(f"{R.REPO_URL}/blob/{R.BRANCH}/"), a.attrs["href"])


class DataAttributes(unittest.TestCase):
    """Every number the page prints names its source, and the printed text equals that source."""

    def check_text(self, text: str, value, label: str) -> None:
        if isinstance(value, bool):
            self.assertEqual(text, "pass" if value else "fail", label)
        elif isinstance(value, str):
            self.assertEqual(text, value, label)
        else:
            self.assertEqual(num(text), float(value), label)

    def test_metric_spans(self):
        spans = [n for n in DOM.iter() if "data-m" in n.attrs]
        self.assertGreater(len(spans), 250)
        for n in spans:
            self.check_text(n.text().strip(), metric(n.attrs["data-m"]), f"data-m={n.attrs['data-m']}")

    def test_series_spans(self):
        spans = [n for n in DOM.iter() if "data-s" in n.attrs]
        self.assertGreater(len(spans), 3)
        for n in spans:
            self.check_text(n.text().strip(), series_value(n.attrs["data-s"]), f"data-s={n.attrs['data-s']}")

    def test_derived_spans(self):
        spans = [n for n in DOM.iter() if "data-d" in n.attrs]
        self.assertGreaterEqual(len(spans), 2)
        for n in spans:
            text = n.text().strip()
            self.assertEqual(num(text), round(R.eval_expr(n.attrs["data-d"], METRICS), decimals(text)), n.attrs["data-d"])

    def test_expression_evaluator_is_arithmetic_only(self):
        self.assertEqual(R.eval_expr("0.5*a+b/2-(c)", {"a": 4, "b": 6, "c": 1}), 4.0)
        for bad in ("__import__('os')", "a.real", "a[0]", "f(1)", "1 if a else 2", "a**2", "'x'"):
            with self.assertRaises((ValueError, KeyError, SyntaxError, TypeError)):
                R.eval_expr(bad, {"a": 1})

    def test_threshold_constants_match_the_frozen_text(self):
        prereg = (ROOT / "PREREG.md").read_text(encoding="utf-8")
        patterns = {
            "h1a_pass_below_x": r"Net staking outflow < 50% of staking rewards",
            "staking_rewards_share_pct": r"Staking rewards:\*\s+90% of gross issuance",
            "h1b_coverage_min_pct": r"If labelled coverage is below 50%",
            "h1c_min_pct": r"Identified buying ÷ net exchange inflow ≥ 25%",
            "f1_lo": r"\[2\.21M, 2\.40M\] NEAR", "f1_hi": r"\[2\.21M, 2\.40M\] NEAR",
            "f2_lo": r"\[86\.0K, 89\.5K\] NEAR/day", "f2_hi": r"\[86\.0K, 89\.5K\] NEAR/day",
            "f3_max_bp": r"\*\*below 4\.0 bp\*\*", "f4_min_pct": r"\*\*≥ 50%\*\*",
        }
        self.assertEqual(set(patterns), set(R.CONSTS))
        for name, pat in patterns.items():
            self.assertRegex(prereg, pat, name)
            value, text, scale = R.CONSTS[name]
            self.assertAlmostEqual(float(text) * scale, value, places=6, msg=name)
        # the fractions and percentages agree with the numbers in the text
        self.assertEqual(R.CONSTS["h1a_pass_below_x"][0], 50 / 100)
        self.assertEqual(R.CONSTS["f1_lo"][0], sf.F1_BAND[0])
        self.assertEqual(R.CONSTS["f2_hi"][0], sf.F2_BAND[1])
        for n in (n for n in DOM.iter() if "data-k" in n.attrs and n.tag in ("span", "tspan")):
            self.assertEqual(n.text().strip(), R.CONSTS[n.attrs["data-k"]][1])

    def test_window_dates_agree_with_the_data(self):
        ctx = R.Ctx()
        self.assertEqual(R.window_text(ctx, 30).replace(" to ", ".."), METRICS["revwallets_window"])
        self.assertEqual(R.window_text(ctx, 90).split(" to ")[0], METRICS["take_b1_window"].split("..")[0])
        self.assertEqual(R.window_text(ctx, 90).split(" to ")[1], METRICS["asof"])

    def test_unwrapped_metric_numbers_in_prose(self):
        """A number in running text that equals a metric must sit in a span that names it (as check.py does for markdown)."""
        values: set[float] = set()

        def collect(v) -> None:
            if isinstance(v, bool):
                return
            if isinstance(v, (int, float)):
                values.add(float(v))
            elif isinstance(v, list):
                for x in v:
                    collect(x)
            elif isinstance(v, dict):
                for x in v.values():
                    collect(x)

        collect(METRICS)
        token = re.compile(r"(?<![\w.\-/#$])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+)(?![\w\-])")
        skip_tags = {"svg", "table", "pre", "code", "style", "head", "details"}
        skip_classes = {"verbatim", "sha", "docs", "toc", "ver"}  # PREREG's own words, hashes, links, a Python version
        problems: list[str] = []

        def walk(n: Node, wrapped: bool, skipping: bool) -> None:
            now_wrapped = wrapped or any(k in n.attrs for k in ("data-m", "data-s", "data-d", "data-k", "data-f", "data-p", "data-count", "data-fingerprint", "data-prereg"))
            now_skip = skipping or n.tag in skip_tags or bool(n.classes() & skip_classes)
            for c in n.children:
                if isinstance(c, Node):
                    walk(c, now_wrapped, now_skip)
                elif not now_wrapped and not now_skip:
                    for m in token.finditer(c):
                        if float(m.group(1).replace(",", "")) in values:
                            problems.append(f"{m.group(1)!r} in {c.strip()[:70]!r}")

        walk(DOM.find("body"), False, False)
        self.assertEqual(problems, [])

    def test_table_cells_match_their_sources(self):
        checked = 0
        for t in DOM.find_all("table"):
            if "data-series" in t.attrs:
                name = t.attrs["data-series"]
                heads = [th.attrs.get("data-c") for th in t.find_all("th")]
                for tr in t.find_all("tr"):
                    if "data-k" not in tr.attrs:
                        continue
                    key = tr.attrs["data-k"]
                    cells = [td.text().strip() for td in tr.find_all("td")]
                    for h, cell in zip(heads, cells):
                        if h and not h.startswith("d:") and h not in ("date", "month"):
                            self.assertEqual(num(cell), float(series_value(f"{name}.{key}.{h}")), f"{name} {key} {h}")
                            checked += 1
                        if h == "d:change_k":  # each day's change from the day before, in thousand NEAR
                            prev = R.date.fromordinal(R.date.fromisoformat(key).toordinal() - 1).isoformat()
                            want = round((series_value(f"supply_daily.{key}.supply_m") - series_value(f"supply_daily.{prev}.supply_m")) * 1000, 1)
                            self.assertEqual(num(cell), want, f"change {key}")
                            checked += 1
        self.assertGreater(checked, 300)

    def test_staking_table_ties_to_raw_and_metrics(self):
        raw = json.loads((ROOT / "data/raw/bq/staking_flows_daily.json").read_text(encoding="utf-8"))
        table = next(t for t in DOM.find_all("table") if t.attrs.get("data-raw") == "raw/bq/staking_flows_daily.json")
        rows = [tr for tr in table.find_all("tr") if "data-k" in tr.attrs]
        self.assertEqual([tr.attrs["data-k"] for tr in rows], [x["block_date"] for x in raw])
        cn = cr = 0.0
        for tr, x in zip(rows, raw):
            cells = [num(td.text()) for td in tr.find_all("td")[1:]]
            out, inn, rw = float(x["outflow_near"]), float(x["inflow_near"]), float(x["rewards_near"])
            cn += out - inn
            cr += rw
            self.assertEqual(cells, [round(v) for v in (out, inn, out - inn, rw)] + [round(cn), round(cr)])
        self.assertEqual(round(cn / 1e6, 1), METRICS["pool_net_outflow_90d_m"])
        self.assertEqual(round(cr / 1e6, 2), METRICS["pool_rewards_90d_m"])

    def test_header_facts(self):
        want = hashlib.sha256(MANIFEST_BYTES).hexdigest()[:16]
        self.assertIn("first 16 hex", DOM.find("header").text())
        fingerprints = [n for n in DOM.find_all("code") if "data-fingerprint" in n.attrs]
        self.assertEqual([(n.attrs["data-fingerprint"], n.text()) for n in fingerprints], [(want, want)])
        pre = [n for n in DOM.find_all("code") if "data-prereg" in n.attrs][0]
        self.assertEqual(pre.attrs["data-prereg"], hashlib.sha256((ROOT / "PREREG.md").read_bytes()).hexdigest())
        count = [n for n in DOM.iter() if "data-count" in n.attrs][0]
        self.assertEqual(int(count.text()), len(METRICS))

    def test_prereg_is_still_the_frozen_file(self):
        self.assertEqual(hashlib.sha256((ROOT / "PREREG.md").read_bytes()).hexdigest(), R.FROZEN_PREREG_SHA256)
        self.assertIn(R.FREEZE_COMMIT, (ROOT / "PREREG-ADDENDUM.md").read_text(encoding="utf-8"))


class Cards(unittest.TestCase):
    def cards(self) -> dict[str, Node]:
        return {n.attrs["id"][len("chart-"):]: n for n in DOM.find_all("section") if n.attrs.get("id", "").startswith("chart-")}

    def test_every_chart_is_present_in_the_right_part(self):
        cards = self.cards()
        self.assertEqual(tuple(cards), PRE_IDS + tuple(c for c in CARD_IDS if c not in PRE_IDS))
        part = {n.attrs["id"]: n for n in DOM.find_all("section") if n.attrs.get("id") in ("preregistered", "exploratory")}
        for cid, node in cards.items():
            owner = "preregistered" if cid in PRE_IDS else "exploratory"
            self.assertIn(node, list(part[owner].iter()), cid)
            badge = node.find("span", "badge")
            self.assertIsNotNone(badge, cid)
            self.assertIn("badge-pre" if cid in PRE_IDS else "badge-exp", badge.classes(), cid)
            text = badge.text().strip()
            self.assertEqual(text, "Pre-registered" if cid in PRE_IDS else "Exploratory, chosen after the freeze", cid)

    def test_card_anatomy(self):
        for cid, node in self.cards().items():
            self.assertEqual(len(node.find_all("h3")), 1, cid)
            self.assertTrue(node.find("h3").text().strip(), cid)
            self.assertTrue(node.find("p", "shows").text().startswith("What it shows:"), cid)
            self.assertTrue(node.find("p", "notshows").text().startswith("What it does not show:"), cid)
            self.assertIn("Source:", node.find("div", "source").text(), cid)
            figure = node.find("figure")
            self.assertIsNotNone(figure.find("figcaption"), cid)
            details = {d.find("summary").text().strip(): d for d in node.find_all("details")}
            self.assertEqual(set(details), {"Query", "Data"}, cid)
            self.assertTrue(details["Data"].find_all("table"), cid)
            for table in details["Data"].find_all("table"):
                self.assertGreaterEqual(len(table.find_all("tr")), 3, cid)
            svgs = node.find_all("svg", "svg")
            self.assertEqual(len(svgs), 2, cid)  # one for wide screens, one for phones
            for svg in svgs:
                self.assertEqual(svg.attrs.get("role"), "img", cid)
                ids = svg.attrs["aria-labelledby"].split()
                self.assertEqual(len(ids), 2, cid)
                for ref, tag in zip(ids, ("title", "desc")):
                    target = [n for n in svg.iter() if n.attrs.get("id") == ref]
                    self.assertEqual(len(target), 1, (cid, ref))
                    self.assertEqual(target[0].tag, tag)
                    self.assertTrue(target[0].text().strip())
                self.assertIn("viewbox", svg.attrs)

    def test_page_sections_and_scorecard(self):
        """The four pre-registered tiles are the same in every state; the fifth says pending until a score is committed."""
        for name, dom, _, result in VARIANTS:
            with self.subTest(variant=name):
                sections = [n.attrs.get("id") for n in dom.find("main").find_all("section")]
                for sid in ("scorecard", "preregistered", "exploratory", "not-computed", "reproduce", "limits"):
                    self.assertIn(sid, sections)
                tiles = [n for n in dom.find_all("li") if "tile" in n.classes()]
                self.assertEqual(len(tiles), 5)
                for t in tiles:
                    self.assertIsNotNone(t.find("svg", "ico"), "every status carries a shape")
                    self.assertTrue(t.find("p", "st").text().strip(), "and a word")
                words = [t.find("p", "st").text().strip() for t in tiles]
                self.assertEqual(words[:4], ["fail", "inconclusive", "inconclusive", "Hold"])
                self.assertEqual(words[4], "scored" if result else "pending")
                icons = [[c for c in t.find("svg", "ico").iter() if c.tag in ("circle", "path")][0].classes() for t in tiles]
                for got, want in zip(icons[:4], ("i-bad", "i-warn", "i-warn", "i-ink2")):
                    self.assertIn(want, got)
                self.assertIn("i-line", icons[4])   # an outline: neither a pass nor a fail
                shapes = {c for el in tiles[4].find("svg", "ico").iter() for c in el.classes()}
                self.assertEqual("i-ink2" in shapes, result is not None, "a scored tile has a dot in the circle, a pending one the clock hands")

    def test_the_pending_state_is_what_an_empty_forward_directory_renders(self):
        """The page as committed is pending exactly when no real score is committed, and scored when one is."""
        tile = [n for n in DOM.find_all("li") if "tile" in n.classes()][4]
        word = tile.find("p", "st").text().strip()
        self.assertEqual(word, "scored" if LIVE_SCORE else "pending")
        if not LIVE_SCORE:
            self.assertEqual(PAGE, PENDING_PAGE)

    def test_scorecard_values_come_from_the_metrics(self):
        self.assertIs(METRICS["h1a_pass_as_written"], False)
        self.assertEqual((METRICS["h1b_verdict"], METRICS["h1c_verdict"], METRICS["rating_output"]), ("inconclusive", "inconclusive", "Hold"))

    def test_reproduce_block_lists_the_exact_commands(self):
        sec = next(n for n in DOM.find_all("section") if n.attrs.get("id") == "reproduce")
        cmds = [c.text() for c in sec.find_all("code")]
        for want in ("python3 -m pipeline.check --manifest", "python3 -m pipeline.compute", "python3 -m pipeline.check --numbers",
                     "python3 -m unittest discover -s tests", "python3 -m pipeline.render --check"):
            self.assertIn(want, cmds)
        self.assertLess(cmds.index("python3 -m pipeline.check --manifest"), cmds.index("python3 -m pipeline.compute"))
        footer = DOM.find("footer").text()
        self.assertIn("Research, not investment advice", footer)
        self.assertIn("MIT", footer)

    def test_every_pre_registered_label_survives(self):
        """Hedges are part of the claims; they must not be dropped by a template change."""
        text = DOM.find("main").text()
        for phrase in ("unattested", "inferred", "consistent with", "ceiling", "is a subset of the total",
                       "not scorable", "never estimated"):
            self.assertIn(phrase, text, phrase)


class SourcesAndQueries(unittest.TestCase):
    def test_repo_links_point_at_existing_files(self):
        prefix = f"{R.REPO_URL}/blob/{R.BRANCH}/"
        paths = {a.attrs["href"][len(prefix):].split("#")[0] for a in DOM.find_all("a") if a.attrs["href"].startswith(prefix)}
        self.assertGreater(len(paths), 30)
        for p in sorted(paths):
            self.assertTrue((ROOT / p).is_file(), p)

    def test_raw_snapshots_exist_and_show_their_hash(self):
        shown = [(n.text().strip(), n) for n in DOM.find_all("code", "rawref")]
        self.assertGreater(len(shown), 30)
        sha_spans = {n.attrs["data-sha-of"]: n.text().strip() for n in DOM.find_all("span", "sha") if "data-sha-of" in n.attrs}
        for path, _ in shown:
            self.assertTrue(path.startswith("data/raw/"), path)
            f = ROOT / path
            self.assertTrue(f.is_file(), path)
            rel = path[len("data/"):]
            self.assertIn(rel, MANIFEST, path)
            first12 = hashlib.sha256(f.read_bytes()).hexdigest()[:12]
            self.assertEqual(first12, MANIFEST[rel]["sha256"][:12], path)
            self.assertEqual(sha_spans[rel], f"sha256 {first12}", path)

    def test_sql_is_shown_verbatim(self):
        sql_files = sorted({a.attrs["href"].rsplit("/blob/" + R.BRANCH + "/", 1)[1] for a in DOM.find_all("a")
                            if a.attrs["href"].endswith(".sql")})
        self.assertGreaterEqual(len(sql_files), 9)
        shown: dict[str, str] = {}
        for q in DOM.find_all("details", None):
            if q.find("summary").text().strip() != "Query":
                continue
            heads = [n for n in q.iter() if n.tag == "p" and "qh" in n.classes()]
            pres = [n for n in q.iter() if n.tag == "pre"]
            self.assertEqual(len(heads), len(pres))
            for h, pre in zip(heads, pres):
                path = h.find("code").text().strip()
                shown.setdefault(path, pre.text())
        self.assertGreaterEqual(len(shown), 9)
        for path, body in shown.items():
            original = (ROOT / path).read_text(encoding="utf-8")
            expected, cut = R.sql_display(original)
            self.assertEqual(body, expected, path)
            if not cut:
                self.assertEqual(body, original, f"{path} must be shown exactly as stored")
        self.assertIn("sql/h1b_b_wnear_logs.sql", shown)
        self.assertLess(len(shown["sql/h1b_b_wnear_logs.sql"]), 40_000)
        self.assertIn("characters omitted on this line", shown["sql/h1b_b_wnear_logs.sql"])

    def test_h1b_queries_carry_the_run_record_note(self):
        notes = [n.text() for n in DOM.iter() if n.tag == "p" and "qnote" in n.classes() and "NOT run" in n.text()]
        self.assertEqual(len(notes), 5)  # h1b_a, h1b_b and h1b_c under H1b; h1b_a and h1b_b again under H1c
        for t in notes:
            self.assertIn("2026-11-06 23:23 UTC", t)
            self.assertIn("PREREG-ADDENDUM.md", t)

    def test_h1c_shows_its_two_queries_and_points_to_h1b(self):
        card = next(n for n in DOM.find_all("section") if n.attrs.get("id") == "chart-h1c")
        query = next(d for d in card.find_all("details") if d.find("summary").text().strip() == "Query")
        heads = [h.find("code").text().strip() for h in query.iter() if h.tag == "p" and "qh" in h.classes()]
        self.assertEqual(heads, ["sql/h1b_a_native_flows.sql", "sql/h1b_b_wnear_logs.sql"])
        self.assertEqual(len(query.find_all("pre")), 2)
        self.assertTrue(any(a.attrs["href"] == "#chart-h1b" for a in query.find_all("a")))
        self.assertIn("view_account", query.text())

    def test_keyless_charts_show_endpoint_and_fetcher(self):
        for cid in ("peers", "revenue", "supply"):
            card = next(n for n in DOM.find_all("section") if n.attrs.get("id") == f"chart-{cid}")
            query = next(d for d in card.find_all("details") if d.find("summary").text().strip() == "Query")
            text = query.text()
            self.assertIn("https://", text, cid)
            self.assertIn("pipeline.fetch_keyless", text, cid)

    def test_escrow_attribution_claim_matches_the_csv(self):
        """The page says funding hops are traced per delivery from 2026-10-06 and attributed from samples before."""
        import csv
        with open(ROOT / "data/raw/escrow/deliveries.csv", newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        late = [r for r in rows if r["path"] == "escrow_unshield" and r["day"] >= "2026-10-06"]
        early = [r for r in rows if r["path"] == "escrow_unshield" and r["day"] < "2026-10-06"]
        self.assertGreater(len(late), 800)
        self.assertTrue(all(r["attribution"] == "row" and r["funding_tx_hash"] for r in late))
        self.assertTrue(any(r["attribution"] == "sample" for r in early))
        self.assertEqual(len(late), METRICS["escrow_funded_exact_30d_n"])


class Safety(unittest.TestCase):
    def test_escape_helpers(self):
        hostile = '<script>alert(1)</script> & " \''
        for out in (R.esc(hostile), R.md_inline(f"**{hostile}** `{hostile}`")):
            self.assertNotIn("<script", out)
            self.assertNotIn("alert(1)</script>", out)
        self.assertEqual(R.T(hostile)[0], R.esc(hostile))

    def test_sql_text_is_escaped(self):
        class Stub:
            def read_text(self, rel: str) -> str:
                return "SELECT '<b>' || \"&\" -- </pre><script>x()</script>\n" + "x" * 500 + "\n"

        out = R.query_details(Stub(), sql=("sql/evil.sql",))  # type: ignore[arg-type]
        self.assertNotIn("<script>", out)
        self.assertNotIn("</pre><script", out)
        self.assertIn("&lt;/pre&gt;&lt;script&gt;x()&lt;/script&gt;", out)
        self.assertIn("characters omitted", out)
        self.assertNotIn("x" * 400, out)

    def test_every_data_attribute_value_is_a_known_reference(self):
        for n in DOM.iter():
            if "data-m" in n.attrs:
                metric(n.attrs["data-m"])
            if "data-s" in n.attrs:
                series_value(n.attrs["data-s"])
            if "data-k" in n.attrs and n.tag in ("span", "tspan"):
                self.assertIn(n.attrs["data-k"], R.CONSTS)


class ForwardTests(unittest.TestCase):
    def card(self, dom: Node) -> Node:
        return next(n for n in dom.find_all("section") if n.attrs.get("id") == "chart-forward")

    def test_pending_without_a_scored_result(self):
        """Built from an empty forward directory, so it does not depend on what is committed under data/forward."""
        card = self.card(PENDING_DOM)
        self.assertIn("pending", card.find("h3").text())
        self.assertIn("2026-11-14 00:00 UTC", card.find("h3").text())
        words = [n.text().strip() for n in card.find_all("span") if "data-status" in n.attrs]
        self.assertEqual(words, ["pending"] * 4)
        self.assertEqual([n for n in PENDING_DOM.iter() if "data-f" in n.attrs], [])
        probs = {n.attrs["data-p"]: n.text() for n in card.find_all("span") if "data-p" in n.attrs}
        self.assertEqual(probs, {"F1": "0.70", "F2": "0.75", "F3": "0.65", "F4": "0.70"})
        prereg = R.prereg_forward((ROOT / "PREREG.md").read_text(encoding="utf-8"))
        self.assertEqual({k: v["p"] for k, v in prereg.items()}, probs)
        text = card.text()
        for want in ("[2.21M, 2.40M] NEAR", "[86.0K, 89.5K] NEAR/day", "below 4.0 bp", "≥ 50%"):
            self.assertIn(want, text)

    def test_the_live_page_ties_to_the_committed_score_if_there_is_one(self):
        """Before 2026-11-14 nothing is committed and the card is pending. After `score_forward --score` and a re-render,
        every data-f number on the page equals the committed result.json, and the card says it is scored."""
        card = self.card(DOM)
        if LIVE_SCORE is None:
            self.assertIn("pending", card.find("h3").text())
            self.assertEqual([n for n in DOM.iter() if "data-f" in n.attrs], [])
            return
        self.assertGreater(check_forward_numbers(self, DOM, LIVE_SCORE), 5)
        self.assertNotIn("pending", card.find("h3").text())
        words = [n.text().strip() for n in card.find_all("span") if "data-status" in n.attrs]
        self.assertEqual(words, [str(LIVE_SCORE["results"][f]["result"]) for f in ("F1", "F2", "F3", "F4")])

    def test_scored_fixture(self):
        dom = {n: d for n, d, _, _ in VARIANTS}["scored"]
        card = self.card(dom)
        words = {n.attrs["data-status"]: n.text().strip() for n in card.find_all("span") if "data-status" in n.attrs}
        self.assertEqual(words, {"F1": "PASS", "F2": "MISS", "F3": "PASS", "F4": "not scorable"})
        self.assertGreater(check_forward_numbers(self, dom, fixture_result()), 10)
        self.assertIn("passed", card.find("h3").text())
        self.assertIn("not scorable", card.find("h3").text())
        self.assertIn("a DefiLlama peer fetch is missing", card.text())
        self.assertIn("score_20261114T010203Z/result.json", card.find("div", "source").text())
        self.assertNotIn("pending", " ".join(words.values()))
        tile = [n for n in dom.find_all("li") if "tile" in n.classes()][4]
        self.assertEqual(tile.find("p", "st").text().strip(), "scored")
        self.assertIn("2 pass, 1 miss", tile.text())

    def test_dry_run_output_is_never_read_or_shown(self):
        dry = fixture_result(is_score=False, mode="DRY-RUN")
        dry["results"]["F1"]["balance_near"] = 1_111_111.0
        dry["results"]["F3"]["take_rate_bp"] = 9.8765
        opened: list[str] = []
        real_read_text = Path.read_text

        def spy(self_: Path, *a, **k):
            opened.append(str(self_))
            return real_read_text(self_, *a, **k)

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            write_forward(tmp, "dry-run_20261110T000000Z", dry, "DRY_RUN_result_NOT_A_SCORE.json")
            write_forward(tmp, "score_20261114T000000Z", dry)  # a result.json that says it is not a score
            with mock.patch.object(Path, "read_text", spy):
                dom, page = forward_dom(tmp)
        self.assertFalse([p for p in opened if "DRY_RUN_result_NOT_A_SCORE" in p])
        self.assertEqual([n for n in dom.iter() if "data-f" in n.attrs], [])
        for needle in ("1,111,111", "9.88", "9.8765", "1111111"):
            self.assertNotIn(needle, page)
        self.assertIn("pending", self.card(dom).find("h3").text())

    def test_only_the_newest_score_directory_counts(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            write_forward(tmp, "score_20261114T010000Z", fixture_result())
            write_forward(tmp, "score_20261115T010000Z", fixture_result(is_score=False, mode="DRY-RUN"))
            dom, _ = forward_dom(tmp)
        self.assertIn("pending", self.card(dom).find("h3").text())

    def test_a_score_made_by_the_real_scorer_renders_and_ties_to_its_result(self):
        """The layout comes from pipeline/score_forward.py, not from this file, so a change there cannot slip past."""
        result = realistic_result()
        dom = {n: d for n, d, _, _ in VARIANTS}["scored-real"]
        words = {n.attrs["data-status"]: n.text().strip() for n in self.card(dom).find_all("span") if "data-status" in n.attrs}
        self.assertEqual(words, {f: result["results"][f]["result"] for f in ("F1", "F2", "F3", "F4")})
        self.assertGreater(check_forward_numbers(self, dom, result), 10)

    def test_unreadable_or_odd_files_are_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "score_20261114T010000Z").mkdir()
            (tmp / "score_20261114T010000Z" / "result.json").write_text("{not json", encoding="utf-8")
            self.assertIsNone(R.load_forward(tmp))
            write_forward(tmp, "score_20261114T020000Z", {"is_score": True, "mode": "score"})  # no results
            self.assertIsNone(R.load_forward(tmp))
            self.assertIsNone(R.load_forward(tmp / "missing"))


class CheckMode(unittest.TestCase):
    def run_main(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = R.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_write_then_check_then_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            site = Path(d) / "site"
            code, out, _ = self.run_main("--out", str(site))
            self.assertEqual(code, 0)
            self.assertIn("render: wrote", out)
            page = site / R.PAGE_NAME
            self.assertEqual(page.read_bytes(), FILES[PAGE_KEY])
            code, out, _ = self.run_main("--check", "--out", str(site))
            self.assertEqual(code, 0)
            self.assertIn("matches a fresh render", out)
            self.assertIn(R.Ctx().fingerprint, out)
            data = bytearray(page.read_bytes())
            data[len(data) // 2] ^= 0x01  # flip one bit
            page.write_bytes(bytes(data))
            code, _, err = self.run_main("--check", "--out", str(site))
            self.assertEqual(code, 1)
            self.assertIn("differs from a fresh render", err)
            page.unlink()
            code, _, err = self.run_main("--check", "--out", str(site))
            self.assertEqual(code, 1)
            self.assertIn("missing", err)

    def test_extra_files_in_the_site_directory_are_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            site = Path(d)
            self.run_main("--out", str(site))
            (site / ".nojekyll").write_text("", encoding="utf-8")
            self.assertEqual(self.run_main("--check", "--out", str(site))[0], 0)

    def test_output_has_no_trailing_clock_or_path_dependence(self):
        self.assertTrue(FILES[PAGE_KEY].endswith(b"</html>\n"))
        self.assertNotIn(str(ROOT).encode(), FILES[PAGE_KEY])


class Helpers(unittest.TestCase):
    def test_number_formatting(self):
        self.assertEqual(R.fmt_value(6.56), "6.56")
        self.assertEqual(R.fmt_value(20.0), "20.0")
        self.assertEqual(R.fmt_value(88295.0, 0), "88,295")
        self.assertEqual(R.fmt_value(909), "909")
        self.assertEqual(R.fmt_value(4454.2), "4,454.2")
        self.assertEqual(R.fmt_value(-0.0, 1), "0")
        self.assertEqual(R.n1(-0.04), "0")
        with self.assertRaises(TypeError):
            R.fmt_value(True)

    def test_nice_axis(self):
        ticks, top = R.nice_axis(83.6)
        self.assertEqual((ticks[0], ticks[-1], top), (0, 100, 100))
        ticks, lo, top = R.nice_range(-10.7, 83.6)
        self.assertEqual((lo, top), (-25, 100))
        self.assertIn(0, ticks)

    def test_wrap_and_clamp(self):
        self.assertEqual(R.wrap_words("aaa bbb ccc", 7), ["aaa bbb", "ccc"])
        self.assertEqual(R.clamp_anchor(2, 30, 100), (0.0, "start"))
        self.assertEqual(R.clamp_anchor(98, 30, 100), (100, "end"))
        self.assertEqual(R.clamp_anchor(50, 30, 100), (50, "middle"))

    def test_prereg_table_parser(self):
        rows = R.prereg_forward("| F1 | text `x` **y** | 0.70 |\n| F9 | no | 0.1 |\n| F2 | b | 0.75 |\n")
        self.assertEqual(rows["F1"], {"text": "text `x` **y**", "p": "0.70"})
        self.assertNotIn("F9", rows)


# ------------------------------------------------------------------ what each number is bound to (written by hand)
# Each table below was written from the card text in pipeline/render.py, not generated from it. If a template edit swaps
# two numbers, makes a label read another metric, or changes an axis, the page still renders and still matches a fresh
# render: these tables are what fail. Change one only together with the card it describes.

# The data references in each card headline, in the order they are printed.
HEADLINE_REFS = {
    "h1a": [("m", "h1a_ratio_as_written_x"), ("k", "h1a_pass_below_x")],
    "h1b": [("m", "h1b_verdict"), ("m", "h1b_net_inflow_lower_m"), ("m", "h1b_net_inflow_upper_m"), ("m", "h1a_gross_issuance_90d_m")],
    "h1c": [("m", "h1c_verdict"), ("m", "h1c_identified_buying_m"), ("m", "h1c_ratio_lower_pct"), ("m", "h1c_ratio_upper_pct"),
            ("k", "h1c_min_pct")],
    "rating": [("m", "rating_output"), ("m", "h1b_verdict")],
    "ladder": [("m", "ladder_all_wallets_pct_of_issuance"), ("m", "ladder_public_collectors_pct_of_issuance"),
               ("m", "ladder_escrow_unshields_pct_of_issuance")],
    "escrow": [("m", "escrow_share_buyback_2026_07_pct"), ("m", "escrow_share_buyback_2026_10_pct"), ("m", "escrow_share_buyback_2026_11_pct")],
    "take": [("m", "take_b1_bb_explicit_bp"), ("m", "take_b3_bb_explicit_bp"), ("m", "take_b3_partner_bp")],
    "partners": [("m", "swapkit_vol_share_pct"), ("m", "swapkit_buyback_fees_usd"), ("m", "swapkit_exit_traceable_pct"),
                 ("m", "swapkit_exit_ceiling_pct"), ("m", "swapkit_exit_ceiling_all_escrow_pct")],
    "paid": [("m", "partners_kept_vs_near_rev_low_tight_x"), ("m", "explorer_out_of_near_usd_m"), ("m", "explorer_into_near_usd_m")],
    "peers": [("m", "intents_share_peerset_30d_pct"), ("m", "intents_share_peerset_365d_pct")],
    "revenue": [("s", "intents_monthly.2026-10.rev_m"), ("s", "intents_monthly.2026-10.captured_bp"),
                ("s", "intents_monthly.2026-09.captured_bp")],
    "supply": [("m", "net_supply_growth_365d_pct"), ("m", "net_issuance_near_per_day_30d_k")],
}

# The four pre-registered scorecard tiles: label, then the data references in the tile in the order they are printed.
TILE_REFS = [
    ("H1a · most staking rewards stay staked",
     [("m", "h1a_pass_as_written"), ("m", "h1a_ratio_as_written_x"), ("k", "h1a_pass_below_x")]),
    ("H1b · less NEAR reaches exchanges than is minted",
     [("m", "h1b_verdict"), ("m", "h1b_net_inflow_lower_m"), ("m", "h1b_net_inflow_upper_m"), ("m", "h1a_gross_issuance_90d_m"),
      ("m", "h1b_coverage_count_pct"), ("k", "h1b_coverage_min_pct")]),
    ("H1c · identified buyers absorb a larger share",
     [("m", "h1c_verdict"), ("m", "h1c_ratio_lower_pct"), ("m", "h1c_ratio_upper_pct"), ("k", "h1c_min_pct")]),
    ("Rating · the frozen rule",
     [("m", "rating_output"), ("m", "rating_g_obs_pct"), ("m", "rating_g_req_pct"), ("m", "h1b_verdict"), ("m", "rating_output")]),
]

# The key-figure blocks: card -> [(label, references in the value)].
KEYFIGS = {
    "h1a": [("Net outflow ÷ staking rewards", [("m", "h1a_ratio_as_written_x")]), ("A pass needed", [("k", "h1a_pass_below_x")]),
            ("Same ratio, archival pool state", [("m", "h1a_ratio_endpoint_archival_x")])],
    "h1c": [("Identified buying", [("m", "h1c_identified_buying_m")]), ("Lower bound of net inflow", [("m", "h1b_net_inflow_lower_m")]),
            ("Upper bound of net inflow", [("m", "h1b_net_inflow_upper_m")])],
    "rating": [("Rule output", [("m", "rating_output")]), ("If H1b had passed", [("m", "rating_if_h1b_pass")]),
               ("If H1b had failed", [("m", "rating_if_h1b_fail")])],
    "ladder": [("Three-wallet total", [("m", "revwallets_near_k")]),
               ("Share of DefiLlama's reported Intents revenue, same days", [("m", "revwallets_vs_llama_rev_pct")]),
               ("Net issuance", [("m", "net_issuance_near_per_day_window")])],
    "escrow": [("Single-use deliveries in the 30-day window", [("m", "escrow_single_use_30d_n")]),
               ("Funded by the escrow for the exact amount", [("m", "escrow_funded_exact_30d_n"), ("m", "escrow_funded_exact_30d_pct")]),
               ("Escrow share, 30-day window", [("m", "escrow_share_of_buyback_near_30d_pct")])],
    "partners": [("SwapKit share of 1Click volume", [("m", "swapkit_vol_share_pct")]),
                 ("SwapKit share of all Intents volume, one-sided", [("m", "swapkit_share_of_intents_net_pct")]),
                 ("Volume HHI, SwapKit as one channel / split", [("m", "volume_channel_hhi_swapkit_merged"), ("m", "volume_channel_hhi")]),
                 ("Explicit buyback fee HHI", [("m", "buyback_fee_hhi")])],
    "paid": [("Partner fees listed", [("m", "explorer_partner_fees_all_usd_k")]), ("NEAR's captured revenue", [("m", "revwallets_usd_k")]),
             ("Net NEAR sold through 1Click", [("m", "explorer_net_near_sold_usd_m")]),
             ("Share of 1Click volume with NEAR on one side", [("m", "explorer_near_side_swap_share_pct")])],
    "peers": [("Intents share, 30 days", [("m", "intents_share_peerset_30d_pct")]),
              ("Intents share, 365 days", [("m", "intents_share_peerset_365d_pct")]),
              ("30 days, net (halved) basis", [("m", "intents_share_peerset_30d_net_pct")])],
    "revenue": [("Captured revenue, last 30 days", [("m", "intents_rev_30d_m")]), ("Captured take, last 30 days", [("m", "take_captured_bp_30d")]),
                ("Captured share of gross fees, 30 days", [("m", "capture_share_30d_pct")])],
    "supply": [("Net supply growth, 365 days", [("m", "net_supply_growth_365d_pct")]),
               ("Net issuance, 30-day mean", [("m", "net_issuance_near_per_day_30d_k")]),
               ("Gross issuance, 90 days", [("m", "h1a_gross_issuance_90d_m")]), ("Burn, 90 days", [("m", "h1a_burn_90d_k")])],
}

# Every chart panel, in order: (card, panel index) -> (kind, axis low, axis high). None means the axis is chosen from the
# data (nice_range, nice_axis), and the geometry test checks only that every point lies inside the plot.
GOLDEN_AXES = {
    ("h1a", 0): ("hbar", 0, 250), ("h1a", 1): ("line", None, None),
    ("h1b", 0): ("hbar", 0, 200), ("h1b", 1): ("hbar", 0, 100),
    ("h1c", 0): ("hbar", 0, 40),
    ("rating", 0): ("hbar", 0, 700),
    ("ladder", 0): ("hbar", 0, 100), ("ladder", 1): ("hbar", 0, 20),
    ("escrow", 0): ("vcol", 0, 100),
    ("take", 0): ("vcol", 0, 50),
    ("partners", 0): ("hbar", 0, 50), ("partners", 1): ("hbar", 0, 100),
    ("paid", 0): ("hbar", 0, 2.5), ("paid", 1): ("hbar", 0, 30),
    ("peers", 0): ("line", 0, 100),
    ("revenue", 0): ("vcol", 0, None), ("revenue", 1): ("line", 0, None),
    ("supply", 0): ("line", 1200, 1320), ("supply", 1): ("vcol", 0, 120),
}

# Bar rows: (card, panel index) -> [(row label, [the metric each bar's label prints, in order])].
ROWS = {
    ("h1a", 0): [("Withdrawals from staking pools by delegators", ["pool_outflow_90d_m"]),
                 ("Deposits into staking pools by delegators", ["pool_inflow_90d_m"]),
                 ("Net staking outflow (withdrawals minus deposits)", ["pool_net_outflow_90d_m"]),
                 ("Staking rewards (the pre-registered denominator)", ["h1a_staking_rewards_90d_m"])],
    ("h1b", 0): [("Lower bound: unlabelled receivers count as 0% exchange-bound", ["h1b_net_inflow_lower_m"]),
                 ("Upper bound: every unlabelled top-100 receiver counts as exchange-bound", ["h1b_net_inflow_upper_m"]),
                 ("Side measure: cited tier-1 accounts only", ["h1b_net_inflow_tier1_m"]),
                 ("Side measure: upper bound without sourced non-exchange accounts", ["h1b_net_inflow_upper_ex_nonexchange_m"])],
    ("h1b", 1): [("Tiers 1-3 by count (the pre-registered measure)", ["h1b_coverage_count_pct"]),
                 ("Tier 1 only, by count", ["h1b_coverage_tier1_count_pct"]),
                 ("Tiers 1-3, weighted by inflow", ["h1b_coverage_inflow_pct"])],
    ("h1c", 0): [("Identified buying ÷ lower bound of net exchange inflow", ["h1c_ratio_lower_pct"]),
                 ("Identified buying ÷ upper bound of net exchange inflow", ["h1c_ratio_upper_pct"])],
    ("rating", 0): [("G_req: growth needed for captured revenue to equal net issuance by 2031-11-04", ["rating_g_req_pct"]),
                    ("G_req without HSP-029's issuance cut", ["rating_g_req_no_hsp029_pct"]),
                    ("G_obs in USD: last 180 days against the 180 before, annualized", ["rating_g_obs_pct"]),
                    ("G_obs in NEAR terms (sensitivity)", ["rating_g_obs_near_pct"])],
    ("ladder", 0): [("NEAR delivered to the three revenue wallets", ["ladder_all_wallets_pct_of_issuance"])],
    ("ladder", 1): [("All three revenue wallets, by how the NEAR arrived", ["ladder_all_wallets_pct_of_issuance"]),
                    ("Of which the buyback wallet alone (a subset, not an extra rung)", ["ladder_buyback_only_pct_of_issuance"])],
    ("partners", 1): [("Traceable streams: explicit fees plus quote-improvement share, pro rata", ["swapkit_exit_traceable_pct"]),
                      ("Ceiling: also all escrow NEAR unshielded to the buyback wallet", ["swapkit_exit_ceiling_pct"]),
                      ("Wider ceiling: also the escrow NEAR that reached fefundsadmin", ["swapkit_exit_ceiling_all_escrow_pct"])],
    ("paid", 0): [("Loose lower bound: all unexplained NEAR in the buyback wallet counted as partner fees passed on",
                   ["partners_kept_vs_near_rev_low_x"]),
                  ("Tight lower bound: only escrow unshields counted as passed on", ["partners_kept_vs_near_rev_low_tight_x"]),
                  ("Upper: all listed partner fees, none passed on", ["partners_kept_vs_near_rev_high_x"])],
    ("paid", 1): [("1Click swaps into NEAR", ["explorer_into_near_usd_m"]), ("1Click swaps out of NEAR", ["explorer_out_of_near_usd_m"])],
}


# The plotted-value tables under each chart: (card, table index) -> [(row label, [the references in the row's cells])].
# The tables of series or raw rows (peers, revenue, supply, staking) are checked against their sources in DataAttributes.
TABLE_ROWS = {
    ('h1a', 0): [
        ('Withdrawals from staking pools', ['pool_outflow_90d_m']),
        ('Deposits into staking pools', ['pool_inflow_90d_m']),
        ('Net staking outflow', ['pool_net_outflow_90d_m']),
        ('Staking rewards (90% of gross issuance)', ['staking_rewards_share_pct', 'h1a_staking_rewards_90d_m']),
        ('Pass line (0.5 x staking rewards)', ['h1a_pass_below_x', '0.5*h1a_staking_rewards_90d_m']),
    ],
    ('h1b', 0): [
        ('Net exchange inflow, lower bound', ['h1b_net_inflow_lower_m']),
        ('Net exchange inflow, upper bound', ['h1b_net_inflow_upper_m']),
        ('Side: tier 1 only', ['h1b_net_inflow_tier1_m']),
        ('Side: upper bound without sourced non-exchange accounts', ['h1b_net_inflow_upper_ex_nonexchange_m']),
        ('Gross issuance, 90 days (the H1b bar)', ['h1a_gross_issuance_90d_m']),
        ('Native NEAR, lower bound', ['h1b_native_lower_m']),
        ('Native NEAR, upper bound', ['h1b_native_upper_m']),
        ('Coverage, tiers 1-3 by count (primary)', ['h1b_coverage_count_pct']),
        ('Coverage, tier 1 by count', ['h1b_coverage_tier1_count_pct']),
        ('Coverage, tiers 1-3 by inflow', ['h1b_coverage_inflow_pct']),
        ('Coverage required for a point result', ['h1b_coverage_min_pct']),
    ],
    ('h1c', 0): [
        ("Identified buying: increase in the buyback wallet's balance", ['h1c_identified_buying_m']),
        ('Net exchange inflow, lower bound', ['h1b_net_inflow_lower_m']),
        ('Net exchange inflow, upper bound', ['h1b_net_inflow_upper_m']),
        ('Identified buying ÷ lower bound', ['h1c_ratio_lower_pct']),
        ('Identified buying ÷ upper bound', ['h1c_ratio_upper_pct']),
        ('Pass bar', ['h1c_min_pct']),
    ],
    ('rating', 0): [
        ('G_req', ['rating_g_req_pct']),
        ('G_req without HSP-029', ['rating_g_req_no_hsp029_pct']),
        ('G_obs, USD', ['rating_g_obs_pct']),
        ('G_obs, NEAR terms', ['rating_g_obs_near_pct']),
        ('Captured revenue, last 90 days', ['rating_r90_usd_m']),
    ],
    ('ladder', 0): [
        ('All three revenue wallets (base case for valuation)', ['ladder_all_wallets_pct_of_issuance']),
        ('Of which the buyback wallet alone', ['ladder_buyback_only_pct_of_issuance']),
        ('Traceable to two recurring public fee collectors', ['ladder_public_collectors_pct_of_issuance']),
        ('Released from the Confidential Intents escrow', ['ladder_escrow_unshields_pct_of_issuance']),
        ('One other recurring source', ['ladder_other_pct_of_issuance']),
        ('Net issuance, NEAR a day (denominator)', ['net_issuance_near_per_day_window']),
    ],
    ('escrow', 0): [
        ('Jul 2026', ['escrow_share_of_buyback_by_month.0.share_pct', 'escrow_share_of_buyback_by_month.0.note']),
        ('Aug 2026', ['escrow_share_of_buyback_by_month.1.share_pct']),
        ('Sep 2026', ['escrow_share_of_buyback_by_month.2.share_pct']),
        ('Oct 2026', ['escrow_share_of_buyback_by_month.3.share_pct']),
        ('Nov 2026', ['escrow_share_of_buyback_by_month.4.share_pct']),
    ],
    ('take', 0): [
        ('Aug 7 – Sep 5 (2026-08-07..2026-09-05)', ['take_b1_bb_explicit_bp', 'take_b1_partner_bp', 'take_b1_vol_with_bb_pct', 'take_b1_swapkit_vol_pct', 'take_b1_captured_bp', 'take_b1_oneclick_usd_m']),
        ('Sep 6 – Oct 5 (2026-09-06..2026-10-05)', ['take_b2_bb_explicit_bp', 'take_b2_partner_bp', 'take_b2_vol_with_bb_pct', 'take_b2_swapkit_vol_pct', 'take_b2_captured_bp', 'take_b2_oneclick_usd_m']),
        ('Oct 6 – Nov 4 (2026-10-06..2026-11-04)', ['take_b3_bb_explicit_bp', 'take_b3_partner_bp', 'take_b3_vol_with_bb_pct', 'take_b3_swapkit_vol_pct', 'take_b3_captured_bp', 'take_b3_oneclick_usd_m']),
    ],
    ('partners', 0): [
        ('SwapKit', ['swapkit_vol_share_pct', 'swapkit_buyback_fees_usd']),
        ('(none)', ['buyback_fee_by_channel.0.vol_share_pct', 'buyback_fee_by_channel.0.share_pct']),
        ('trustwallet', ['buyback_fee_by_channel.1.vol_share_pct', 'buyback_fee_by_channel.1.share_pct']),
        ('e1a72603-64b3-4be1-8265-8bae5970d396', ['buyback_fee_by_channel.2.vol_share_pct', 'buyback_fee_by_channel.2.share_pct']),
        ('lifi', ['buyback_fee_by_channel.3.vol_share_pct', 'buyback_fee_by_channel.3.share_pct']),
        ('arbie', ['buyback_fee_by_channel.4.vol_share_pct', 'buyback_fee_by_channel.4.share_pct']),
        ('rango', ['buyback_fee_by_channel.5.vol_share_pct', 'buyback_fee_by_channel.5.share_pct']),
        ('leodex', ['buyback_fee_by_channel.6.vol_share_pct', 'buyback_fee_by_channel.6.share_pct']),
        ('enot', ['buyback_fee_by_channel.7.vol_share_pct', 'buyback_fee_by_channel.7.share_pct']),
    ],
    ('partners', 1): [
        ('Traceable streams', ['swapkit_exit_traceable_pct']),
        ('Ceiling (all escrow NEAR to the buyback wallet)', ['swapkit_exit_ceiling_pct']),
        ('Wider ceiling (also the escrow NEAR to fefundsadmin)', ['swapkit_exit_ceiling_all_escrow_pct']),
    ],
    ('paid', 0): [
        ('Partner fees listed on 1Click swaps', ['explorer_partner_fees_all_usd_k']),
        ("NEAR's captured revenue, three revenue wallets", ['revwallets_usd_k']),
        ("Partners kept ÷ NEAR's revenue, loose lower bound", ['partners_kept_vs_near_rev_low_x']),
        ("Partners kept ÷ NEAR's revenue, tight lower bound", ['partners_kept_vs_near_rev_low_tight_x']),
        ("Partners kept ÷ NEAR's revenue, upper", ['partners_kept_vs_near_rev_high_x']),
        ('1Click swaps into NEAR', ['explorer_into_near_usd_m']),
        ('1Click swaps out of NEAR', ['explorer_out_of_near_usd_m']),
        ('Net NEAR sold through 1Click', ['explorer_net_near_sold_usd_m']),
    ],
    ('peers', 0): [
        ('NEAR Intents', ['peers.0.vol_30d_b', 'peers.0.vol_365d_b', 'peers.0.share_30d_pct']),
        ('THORChain', ['peers.1.vol_30d_b', 'peers.1.vol_365d_b', 'peers.1.share_30d_pct']),
        ('Chainflip', ['peers.2.vol_30d_b', 'peers.2.vol_365d_b', 'peers.2.share_30d_pct']),
        ('Maya', ['peers.3.vol_30d_b', 'peers.3.vol_365d_b', 'peers.3.share_30d_pct']),
    ],
}


def partners_rows_golden() -> list[tuple[str, list[str]]]:
    """Panel A of the partners chart: SwapKit, then each channel in metrics.json, in the order of buyback_fee_by_channel."""
    rows = [("SwapKit (Ledger, Trust, Tangem and others)", ["swapkit_vol_share_pct", "swapkit_buyback_fees_usd"])]
    for i, c in enumerate(METRICS["buyback_fee_by_channel"]):
        ch = c["channel"]
        label = ("No referrer (default fee)" if ch == "(none)" else
                 f"Unnamed integrator ({ch[:8]}…)" if re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f-]+", ch) else ch)
        rows.append((label, [f"buyback_fee_by_channel.{i}.vol_share_pct", f"buyback_fee_by_channel.{i}.share_pct"]))
    return rows


def block_label(window: str) -> str:
    """'2026-08-07..2026-09-05' as 'Aug 7 – Sep 5', written independently of pipeline/render.py."""
    def short(iso: str) -> str:
        return f"{R.MONTHS[int(iso[5:7]) - 1]} {int(iso[8:10])}"

    a, b = window.split("..")
    return f"{short(a)} – {short(b)}"


# Columns: (card, panel index) -> [(category label, [the metric each column's label prints, in order])].
COLS = {
    ("escrow", 0): [("Jul (from 07-07)", ["escrow_share_buyback_2026_07_pct"]), ("Aug", ["escrow_share_buyback_2026_08_pct"]),
                    ("Sep", ["escrow_share_buyback_2026_09_pct"]), ("Oct", ["escrow_share_buyback_2026_10_pct"]),
                    ("Nov (to 11-04)", ["escrow_share_buyback_2026_11_pct"])],
    ("take", 0): [(block_label(METRICS[f"take_b{i}_window"]),
                   [f"take_b{i}_bb_explicit_bp", f"take_b{i}_partner_bp", f"take_b{i}_captured_bp"]) for i in (1, 2, 3)],
}

# Phrases each card must keep: the hedges and the labels that say what kind of result it is.
CARD_PHRASES = {
    "h1a": ("fungible", "inconclusive", "post hoc"),
    "h1b": ("inconclusive", "mechanical", "snapshots dated", "biases the lower bound down", "never inside it"),
    "h1c": ("inconclusive", "market-wide balance, not a trace", "held, not burned"),
    "rating": ("pending resolver", "do not predict it", "never fail", "does not feed the rule"),
    "forward": ("never estimated", "not scorable", "is not a score"),
    "ladder": ("unattested", "attestation", "Nothing here alleges misconduct", "labelled sensitivity", "subset"),
    "escrow": ("unattested", "attributed from samples", "less firmly established"),
    "take": ("like-for-like", "consistent with", "overstated"),
    "partners": ("ceiling", "unknown, not zero", "its size is not measured", "neither documented reading"),
    "paid": ("is not visible", "do not extrapolate", "non-custodial"),
    "peers": ("context for it, not the test", "reported volume"),
    "revenue": ("NEAR delivered to the wallets", "context for it, not the test"),
    "supply": ("HSP-029", "context for it, not the test", "rounding"),
}
# The hedges the headline itself carries (the headline is what a reader sees first).
HEADLINE_PHRASES = {
    "ladder": ("fee stream unattested",),
    "partners": ("about", "at most", "if the escrow NEAR reaching the front-end fund is counted too"),
    "paid": ("at least",),
    "h1b": ("on either side of",),
    "h1c": ("a pass needs",),
    "rating": ("Buy needs H1b to pass, Avoid needs it to fail",),
    "take": ("mostly because more volume carries a buyback fee entry",),
}
# And the sections of the page that carry hedges of their own.
SECTION_PHRASES = {
    "limits": ("inferred", "consistent with the docs rather than proven", "sample-attributed", "lower bounds", "mechanical"),
    "not-computed": ("attestation", "fungible", "pending resolver"),
}


# ------------------------------------------------------------------ headlines, tiles, key figures, hedges
class Golden(unittest.TestCase):
    """Which number each headline, tile and key figure prints, and which phrases each card keeps."""

    def test_headlines_print_the_expected_numbers_in_order(self):
        for name, dom, _, _ in VARIANTS:
            for cid, want in HEADLINE_REFS.items():
                with self.subTest(variant=name, card=cid):
                    self.assertEqual(refs_in(card_node(dom, cid).find("h3")), want)

    def test_scorecard_tiles_print_the_expected_numbers(self):
        for name, dom, _, _ in VARIANTS:
            tiles = [n for n in dom.find_all("li") if "tile" in n.classes()]
            self.assertEqual([t.find("p", "tlabel").text() for t in tiles[:4]], [lab for lab, _ in TILE_REFS])
            for tile, (lab, want), cid in zip(tiles, TILE_REFS, ("h1a", "h1b", "h1c", "rating")):
                with self.subTest(variant=name, tile=lab):
                    self.assertEqual(refs_in(tile), want)
                    self.assertEqual(tile.find("a").attrs["href"], "#chart-" + cid)

    def test_the_forward_headline_and_tile_follow_the_state(self):
        for name, dom, _, result in VARIANTS:
            with self.subTest(variant=name):
                tile = [n for n in dom.find_all("li") if "tile" in n.classes()][4]
                want = ([("f", "@count.PASS"), ("f", "@count.MISS"), ("f", "@count.not scorable")] if result else [])
                self.assertEqual(refs_in(card_node(dom, "forward").find("h3"), ("data-f",)), want)
                self.assertEqual(refs_in(tile, ("data-f",)), want)
                self.assertEqual(tile.find("a").attrs["href"], "#chart-forward")

    def test_key_figures_print_the_expected_numbers(self):
        for name, dom, _, _ in VARIANTS:
            for cid, want in KEYFIGS.items():
                with self.subTest(variant=name, card=cid):
                    kf = card_node(dom, cid).find("dl", "keyfigs")
                    got = [(d.find("dt").text(), refs_in(d.find("dd"))) for d in kf.find_all("div")]
                    self.assertEqual(got, want)
        for cid in set(CARD_IDS) - set(KEYFIGS):
            self.assertIsNone(card_node(DOM, cid).find("dl", "keyfigs"), f"{cid} has key figures that are not in KEYFIGS")

    def test_headlines_say_what_the_numbers_are_about(self):
        want = {"revenue": ("October 2026", "September"), "escrow": ("July", "October", "November"),
                "peers": ("30 days", "365 days"), "take": ("bp of volume", "partner fees"), "rating": ("Buy needs", "Avoid needs")}
        for cid, phrases in want.items():
            h3 = card_node(DOM, cid).find("h3").text()
            for ph in phrases:
                self.assertIn(ph, h3, cid)
        # in the peers headline the 30-day figure comes first, then the 365-day one
        h3 = card_node(DOM, "peers").find("h3")
        text = h3.text()
        self.assertLess(text.index("30 days"), text.index("365 days"))
        self.assertEqual([r for _, r in refs_in(h3)], ["intents_share_peerset_30d_pct", "intents_share_peerset_365d_pct"])

    def test_each_headline_keeps_its_hedge(self):
        for name, dom, _, _ in VARIANTS:
            for cid, phrases in HEADLINE_PHRASES.items():
                h3 = re.sub(r"\s+", " ", card_node(dom, cid).find("h3").text())
                for ph in phrases:
                    self.assertIn(ph, h3, f"{name}: the {cid} headline lost {ph!r}")

    def test_the_h1a_headline_verdict_word_agrees_with_the_metric(self):
        self.assertIs(METRICS["h1a_pass_as_written"], False)
        h3 = card_node(DOM, "h1a").find("h3").text()
        self.assertTrue(h3.startswith("H1a fails:"), h3)
        for cid, key, word in (("h1b", "h1b_verdict", "inconclusive"), ("h1c", "h1c_verdict", "inconclusive"), ("rating", "rating_output", "Hold")):
            self.assertEqual(METRICS[key], word)
            self.assertIn(word, card_node(DOM, cid).find("h3").text())

    def test_every_card_has_text_after_what_it_does_not_show(self):
        for name, dom, _, _ in VARIANTS:
            for cid in CARD_IDS:
                with self.subTest(variant=name, card=cid):
                    for cls, label in (("shows", "What it shows:"), ("notshows", "What it does not show:")):
                        t = card_node(dom, cid).find("p", cls).text().strip()
                        self.assertTrue(t.startswith(label), (cid, t[:40]))
                        body = t[len(label):].strip()
                        self.assertGreaterEqual(len(body), 60, (cid, cls, body))
                        self.assertTrue(body.endswith((".", ")")), (cid, cls, body[-20:]))

    def test_each_card_keeps_its_hedges(self):
        for name, dom, _, _ in VARIANTS:
            for cid, phrases in CARD_PHRASES.items():
                text = card_node(dom, cid).text()
                for ph in phrases:
                    self.assertIn(ph, text, f"{name}: {cid} lost the phrase {ph!r}")

    def test_the_limits_and_not_computed_sections_keep_their_hedges(self):
        for sid, phrases in SECTION_PHRASES.items():
            sec = next(n for n in DOM.find_all("section") if n.attrs.get("id") == sid)
            for ph in phrases:
                self.assertIn(ph, sec.text(), f"{sid}: {ph}")

    def test_plotted_value_tables_bind_each_row_to_its_metric(self):
        for name, dom, _, _ in VARIANTS:
            for (cid, i), want in TABLE_ROWS.items():
                with self.subTest(variant=name, card=cid, table=i):
                    tables = [t for t in card_node(dom, cid).find_all("table") if "data-series" not in t.attrs and "data-raw" not in t.attrs]
                    got = [(tr.find_all("td")[0].text().strip(), [r for td in tr.find_all("td") for _, r in refs_in(td)])
                           for tr in tables[i].find_all("tr") if tr.find_all("td")]
                    self.assertEqual(got, want)
        for cid in CARD_IDS:   # a card with plain tables of metrics has them in TABLE_ROWS
            plain = [t for t in card_node(DOM, cid).find_all("table") if "data-series" not in t.attrs and "data-raw" not in t.attrs]
            listed = sum(1 for (c, _) in TABLE_ROWS if c == cid)
            if cid != "forward":
                self.assertEqual(listed, len(plain), f"{cid}: a table is missing from TABLE_ROWS")

    def test_card_phrases_cover_every_card(self):
        self.assertEqual(set(CARD_PHRASES), set(CARD_IDS))
        self.assertEqual(set(HEADLINE_REFS) | {"forward"}, set(CARD_IDS))


# ------------------------------------------------------------------ geometry: bars, columns, lines, bands and dots
class Geometry(unittest.TestCase):
    """Every mark is drawn where its value puts it on the axis its panel declares, and the declared axes are the golden ones.

    Panels, rows, columns and marks are read from the page (class panel, row, col, data-v ...), and the drawn size is read
    from the path itself, not from an attribute the renderer computed, so the check is against the picture."""

    TOL = 0.35     # SVG user units: coordinates are rounded to 0.1, and a bar sums two or three of them

    def panels(self, dom: Node, cid: str) -> list[list[Node]]:
        """For each of the card's two SVGs (wide, phone), its chart panels in order."""
        svgs = card_node(dom, cid).find_all("svg", "svg")
        self.assertEqual(len(svgs), 2, cid)
        return [sv.find_all("g", "panel") for sv in svgs]

    def where(self, name: str, cid: str, svg: int, pi: int) -> str:
        return f"{name}/{cid}/{'wide' if svg == 0 else 'phone'}/panel {pi}"

    # ---- the declared axes
    def test_every_panel_declares_the_golden_axis(self):
        for name, dom, _, _ in VARIANTS:
            for cid in CARD_IDS:
                if cid == "forward":
                    continue
                want = sorted(pi for (c, pi) in GOLDEN_AXES if c == cid)
                for si, panels in enumerate(self.panels(dom, cid)):
                    where = f"{name}/{cid}/svg {si}"
                    self.assertEqual(len(panels), len(want), where)
                    for pi, panel in enumerate(panels):
                        kind, lo, hi = GOLDEN_AXES[(cid, pi)]
                        self.assertEqual(panel.attrs["data-kind"], kind, where)
                        if lo is not None:
                            self.assertEqual(float(panel.attrs["data-lo"]), lo, where)
                        if hi is not None:
                            self.assertEqual(float(panel.attrs["data-hi"]), hi, where)

    # ---- horizontal bars
    def label_matches(self, node: Node, want: float, where: str) -> None:
        got, dec = shown_number(node)
        self.assertTrue(same_number(want, got, dec), f"{where}: label prints {got}, the bar draws {want}")

    def tip_matches(self, path: Node, want: float, where: str) -> None:
        title = path.find("title")
        self.assertIsNotNone(title, where)
        self.assertTrue(any(same_number(want, v, d) for v, d in numbers_in(title.text())),
                        f"{where}: the tooltip {title.text()!r} does not carry {want}")

    def check_hbar(self, panel: Node, where: str) -> None:
        x0, pw, hi = (float(panel.attrs[k]) for k in ("data-x0", "data-pw", "data-hi"))
        zero = [ln for ln in panel.find_all("line", "axis") if ln.attrs["x1"] == ln.attrs["x2"]]
        self.assertTrue(zero, where)
        self.assertAlmostEqual(float(zero[0].attrs["x1"]), x0, delta=0.15, msg=f"{where}: the zero line is not where the bars start")
        rows = panel.find_all("g", "row")
        self.assertTrue(rows, where)
        for row in rows:
            label = row.attrs["data-row"]
            at = f"{where}/{label[:40]}"
            paths = [pt for pt in row.find_all("path") if "data-v" in pt.attrs]
            vals = row.find_all("text", "val")
            track = row.find("rect", "track")
            if track is not None:   # the full-scale track behind a bar spans the whole axis
                self.assertAlmostEqual(float(track.attrs["x"]), x0, delta=0.15, msg=at)
                self.assertAlmostEqual(float(track.attrs["width"]), pw, delta=0.15, msg=at)
            if len(paths) > 1 and len(vals) == 1:
                self.check_stacked(paths, vals[0], x0, pw, hi, at)
                continue
            self.assertEqual(len(paths), len(vals), at)
            for pt, val in zip(paths, vals):
                v = float(pt.attrs["data-v"])
                shown = float(pt.attrs.get("data-lv", pt.attrs["data-v"]))
                self.assertLessEqual(v, hi, f"{at}: the axis does not hold the value {v}")
                xs = [x for x, _ in path_points(pt.attrs["d"])]
                self.assertAlmostEqual(min(xs), x0, delta=self.TOL, msg=f"{at}: a bar does not start at zero")
                self.assertAlmostEqual(max(xs) - min(xs), max(pw * v / hi, R.MIN_BAR), delta=self.TOL,
                                       msg=f"{at}: a bar of {v} is drawn at the wrong length")
                self.label_matches(val, shown, at)
                self.tip_matches(pt, shown, at)
        self.check_hbar_refs(panel, x0, pw, hi, where)

    def check_stacked(self, segs: list[Node], total_label: Node, x0: float, pw: float, hi: float, at: str) -> None:
        start = x0
        total = 0.0
        for i, sg in enumerate(segs):
            v = float(sg.attrs["data-v"])
            xs = [x for x, _ in path_points(sg.attrs["d"])]
            last = i == len(segs) - 1
            self.assertAlmostEqual(min(xs), start, delta=self.TOL, msg=f"{at}: segment {i} does not start where the one before ends")
            want = max(pw * v / hi if last else pw * v / hi - R.SEG_GAP, R.MIN_SEG)
            self.assertAlmostEqual(max(xs) - min(xs), want, delta=self.TOL, msg=f"{at}: segment {i} of {v} has the wrong length")
            self.tip_matches(sg, v, at)
            start += pw * v / hi
            total += v
        self.assertLessEqual(total, hi, f"{at}: the axis does not hold the stacked total {total}")
        self.label_matches(total_label, total, at)

    def check_hbar_refs(self, panel: Node, x0: float, pw: float, hi: float, where: str) -> None:
        lines = [ln for ln in panel.find_all("line", "refline") if "data-v" in ln.attrs]
        in_rows = {id(t) for row in panel.find_all("g", "row") for t in row.iter()}
        labels = [t for t in panel.find_all("text", "rl") if id(t) not in in_rows]
        self.assertEqual(len(lines) > 0, len(labels) > 0, where)
        for ln in lines:
            v = float(ln.attrs["data-v"])
            self.assertAlmostEqual(float(ln.attrs["x1"]), x0 + pw * v / hi, delta=0.15, msg=f"{where}: a reference line is misplaced")
            self.assertEqual(ln.attrs["x1"], ln.attrs["x2"], where)
            self.assertTrue(any(same_number(v, *shown_number(t)) for t in labels), f"{where}: no reference label says {v}")

    def test_horizontal_bars_are_drawn_to_their_values(self):
        checked = 0
        for name, dom, _, _ in VARIANTS:
            for cid in CARD_IDS:
                if cid == "forward":
                    continue
                for si, panels in enumerate(self.panels(dom, cid)):
                    for pi, panel in enumerate(panels):
                        if panel.attrs["data-kind"] == "hbar":
                            self.check_hbar(panel, self.where(name, cid, si, pi))
                            checked += 1
        self.assertGreaterEqual(checked, 4 * 2 * 10)

    def test_every_bar_row_is_bound_to_its_metric(self):
        golden = dict(ROWS)
        golden[("partners", 0)] = partners_rows_golden()
        for name, dom, _, _ in VARIANTS:
            for (cid, pi), want in golden.items():
                for si, panels in enumerate(self.panels(dom, cid)):
                    with self.subTest(where=self.where(name, cid, si, pi)):
                        rows = panels[pi].find_all("g", "row")
                        got = [(r.attrs["data-row"], [ref for _, ref in refs_in(r)]) for r in rows]
                        self.assertEqual(got, want)

    def test_the_swapkit_fee_bar_is_drawn_as_a_share_and_labelled_in_dollars(self):
        want = METRICS["swapkit_buyback_fees_usd"] / (METRICS["explorer_appfees_to_buybacks_usd_k"] * 1000) * 100
        for name, dom, _, _ in VARIANTS:
            for si, panels in enumerate(self.panels(dom, "partners")):
                bars = [pt for pt in panels[0].find_all("g", "row")[0].find_all("path") if "data-v" in pt.attrs]
                self.assertEqual(len(bars), 2)
                self.assertAlmostEqual(float(bars[0].attrs["data-v"]), METRICS["swapkit_vol_share_pct"], places=6)
                self.assertAlmostEqual(float(bars[1].attrs["data-v"]), want, places=5)
                self.assertEqual(float(bars[1].attrs["data-lv"]), METRICS["swapkit_buyback_fees_usd"])

    def test_the_ladder_segments_match_their_legend_and_the_total(self):
        key = {"s1": "ladder_public_collectors_pct_of_issuance", "s2": "ladder_escrow_unshields_pct_of_issuance",
               "sc": "ladder_other_pct_of_issuance"}
        for name, dom, _, _ in VARIANTS:
            for si, panels in enumerate(self.panels(dom, "ladder")):
                at = f"{name}/svg {si}"
                panel = panels[1]
                segs = panel.find_all("g", "row")[0].find_all("path")
                self.assertEqual([sg.classes() - {"st2"} for sg in segs], [{"s1"}, {"s2"}, {"sc"}], at)
                for sg in segs:
                    cls = (sg.classes() & set(key)).pop()
                    self.assertAlmostEqual(float(sg.attrs["data-v"]), METRICS[key[cls]], places=6, msg=f"{at}: segment {cls}")
                # the legend: a swatch of each class, then the label that prints the metric of the segment with that class
                pairs: list[tuple[str, str]] = []
                swatch = None
                for n in panel.iter():
                    if n.tag == "rect" and n.classes() & set(key):
                        swatch = next(iter(n.classes() & set(key)))
                    elif n.tag == "text" and swatch is not None and refs_in(n):
                        pairs.append((swatch, refs_in(n)[0][1]))
                        swatch = None
                self.assertEqual(pairs, [(c, key[c]) for c in ("s1", "s2", "sc")], at)
        # the panel titles state the axis they sit on
        panels = self.panels(DOM, "ladder")[0]
        self.assertRegex(" ".join(t.text() for t in panels[1].find_all("text", "ttl")), r"0 to 20% axis")
        self.assertRegex(" ".join(t.text() for t in panels[0].find_all("text", "ttl")), r"100% is all of net issuance")
        for panel, hi in zip(panels, (100, 20)):
            self.assertEqual(float(panel.attrs["data-hi"]), hi)

    # ---- columns
    def check_vcol(self, panel: Node, where: str) -> None:
        base, ph, hi = (float(panel.attrs[k]) for k in ("data-base", "data-ph", "data-hi"))
        zero = [ln for ln in panel.find_all("line", "axis") if ln.attrs["y1"] == ln.attrs["y2"]]
        self.assertAlmostEqual(float(zero[0].attrs["y1"]), base, delta=0.15, msg=f"{where}: the zero line is not where the columns start")
        for col in panel.find_all("g", "col"):
            at = f"{where}/{col.attrs['data-cat']}"
            paths = [pt for pt in col.find_all("path") if "data-v" in pt.attrs]
            vals = col.find_all("text", "val")
            for pt in paths:
                v = float(pt.attrs["data-v"])
                self.assertLessEqual(v, hi, f"{at}: the axis does not hold the value {v}")
                ys = [y for _, y in path_points(pt.attrs["d"])]
                self.assertAlmostEqual(max(ys), base, delta=self.TOL, msg=f"{at}: a column does not stand on zero")
                self.assertAlmostEqual(max(ys) - min(ys), max(ph * v / hi, R.MIN_COL), delta=self.TOL,
                                       msg=f"{at}: a column of {v} is drawn at the wrong height")
                if pt.find("title") is not None:
                    self.tip_matches(pt, v, at)
            if len(vals) == len(paths):
                for pt, val in zip(paths, vals):
                    self.label_matches(val, float(pt.attrs["data-v"]), at)
            else:
                self.assertLess(len(vals), len(paths), at)
                for val in vals:
                    self.assertTrue(any(same_number(float(pt.attrs["data-v"]), *shown_number(val)) for pt in paths), at)
        for ln in (ln for ln in panel.find_all("line", "refline") if "data-v" in ln.attrs):
            v = float(ln.attrs["data-v"])
            self.assertAlmostEqual(float(ln.attrs["y1"]), base - ph * v / hi, delta=0.15, msg=f"{where}: a reference line is misplaced")

    def test_columns_are_drawn_to_their_values(self):
        checked = 0
        for name, dom, _, _ in VARIANTS:
            for cid in CARD_IDS:
                if cid == "forward":
                    continue
                for si, panels in enumerate(self.panels(dom, cid)):
                    for pi, panel in enumerate(panels):
                        if panel.attrs["data-kind"] == "vcol":
                            self.check_vcol(panel, self.where(name, cid, si, pi))
                            checked += 1
        self.assertEqual(checked, 4 * 2 * 4)

    def test_every_column_is_bound_to_its_metric_or_series_row(self):
        for name, dom, _, _ in VARIANTS:
            for (cid, pi), want in COLS.items():
                for si, panels in enumerate(self.panels(dom, cid)):
                    with self.subTest(where=self.where(name, cid, si, pi)):
                        got = [(c.attrs["data-cat"], [ref for _, ref in refs_in(c)]) for c in panels[pi].find_all("g", "col")]
                        self.assertEqual(got, want)
                        for (cat, keys), col in zip(want, panels[pi].find_all("g", "col")):
                            values = [float(pt.attrs["data-v"]) for pt in col.find_all("path") if "data-v" in pt.attrs]
                            self.assertEqual(values, [float(METRICS[k]) for k in keys], cat)

    def test_series_columns_are_bound_to_the_series_rows(self):
        end = date.fromisoformat(METRICS["asof"])
        days = [(end - timedelta(days=i)) for i in range(89, -1, -1)]
        supply = {r["date"]: r["supply_m"] for r in SERIES["supply_daily"]}
        for name, dom, _, _ in VARIANTS:
            for si, panels in enumerate(self.panels(dom, "supply")):
                cols = panels[1].find_all("g", "col")
                self.assertEqual([c.attrs["data-cat"] for c in cols], [f"{R.MONTHS[d.month - 1]} {d.day}" for d in days])
                got = [float(c.find("path").attrs["data-v"]) for c in cols]
                want = [round((supply[d.isoformat()] - supply[(d - timedelta(days=1)).isoformat()]) * 1000, 1) for d in days]
                self.assertEqual(got, want)
            for si, panels in enumerate(self.panels(dom, "revenue")):
                cols = panels[0].find_all("g", "col")
                self.assertEqual([c.attrs["data-cat"] for c in cols], [r["month"] for r in SERIES["intents_monthly"]])
                # a month with no revenue draws no column
                got = [[float(pt.attrs["data-v"]) for pt in c.find_all("path")] for c in cols]
                self.assertEqual(got, [[r["rev_m"]] if r["rev_m"] > 0 else [] for r in SERIES["intents_monthly"]])

    # ---- lines
    def check_line(self, panel: Node, where: str) -> None:
        lo, hi, base, ph = (float(panel.attrs[k]) for k in ("data-lo", "data-hi", "data-base", "data-ph"))

        def y_of(v: float) -> float:
            return base - ph * (v - lo) / (hi - lo)

        axis = [ln for ln in panel.find_all("line", "axis") if ln.attrs["y1"] == ln.attrs["y2"]]
        self.assertAlmostEqual(float(axis[0].attrs["y1"]), y_of(max(0, lo)), delta=0.15, msg=f"{where}: the axis line")
        dots = [c for c in panel.find_all("circle") if "data-v" in c.attrs]
        self.assertTrue(dots, where)
        for d in dots:
            self.assertAlmostEqual(float(d.attrs["cy"]), y_of(float(d.attrs["data-v"])), delta=0.2, msg=f"{where}: a dot is misplaced")
        lines = [pt for pt in panel.find_all("path") if "ln" in pt.classes()]
        self.assertTrue(lines, where)
        for ln in lines:
            pts = path_points(ln.attrs["d"])
            for _, y in pts:
                self.assertTrue(base - ph - 0.3 <= y <= base + 0.3, f"{where}: a point of the line is outside the plot")
            self.assertTrue(any(abs(pts[-1][0] - float(d.attrs["cx"])) < 0.2 and abs(pts[-1][1] - float(d.attrs["cy"])) < 0.2 for d in dots),
                            f"{where}: the end of a line has no dot")
        # every label printed at a dot says that dot's value
        for lab in (t for t in panel.find_all("text", "val") if refs_in(t, VALUE_ATTRS)):
            got, dec = shown_number(lab)
            self.assertTrue(any(same_number(float(d.attrs["data-v"]), got, dec) for d in dots), f"{where}: no dot at {got}")
        for ln in (ln for ln in panel.find_all("line", "refline") if "data-v" in ln.attrs):
            v = float(ln.attrs["data-v"])
            self.assertAlmostEqual(float(ln.attrs["y1"]), y_of(v), delta=0.15, msg=f"{where}: a reference line is misplaced")

    def test_lines_end_where_their_labels_say(self):
        checked = 0
        for name, dom, _, _ in VARIANTS:
            for cid in CARD_IDS:
                if cid == "forward":
                    continue
                for si, panels in enumerate(self.panels(dom, cid)):
                    for pi, panel in enumerate(panels):
                        if panel.attrs["data-kind"] == "line":
                            self.check_line(panel, self.where(name, cid, si, pi))
                            checked += 1
        self.assertEqual(checked, 4 * 2 * 4)

    def test_line_end_values_are_the_series_end_values(self):
        for name, dom, _, _ in VARIANTS:
            for si, panels in enumerate(self.panels(dom, "peers")):
                d = [c for c in panels[0].find_all("circle") if "data-v" in c.attrs]
                self.assertEqual([float(c.attrs["data-v"]) for c in d], [SERIES["peer_share_monthly"][-1]["near-intents"]])
            for si, panels in enumerate(self.panels(dom, "revenue")):
                d = [float(c.attrs["data-v"]) for c in panels[1].find_all("circle") if "data-v" in c.attrs]
                rows = SERIES["intents_monthly"]
                self.assertEqual(sorted(d), sorted([rows[-1]["captured_bp"], max(r["captured_bp"] for r in rows)]))
            for si, panels in enumerate(self.panels(dom, "supply")):
                d = [float(c.attrs["data-v"]) for c in panels[0].find_all("circle") if "data-v" in c.attrs]
                self.assertEqual(d, [SERIES["supply_daily"][-1]["supply_m"]])
            for si, panels in enumerate(self.panels(dom, "h1a")):
                d = sorted(float(c.attrs["data-v"]) for c in panels[1].find_all("circle") if "data-v" in c.attrs)
                self.assertEqual([round(x, 1) for x in d[-1:]], [METRICS["pool_net_outflow_90d_m"]])
                self.assertEqual(round(d[0], 2), METRICS["pool_rewards_90d_m"])

    # ---- tick labels
    def tick_pairs(self, group: Node, horizontal: bool) -> list[tuple[float, float, int]]:
        """(gridline position, the number its label prints, that number's decimals) for each gridline directly followed by a tick label."""
        kids = [c for c in group.children if isinstance(c, Node)]
        out = []
        for ln, label in zip(kids, kids[1:]):
            if ln.tag != "line" or not (ln.classes() & {"axis", "grid"}) or label.tag != "text" or "tk" not in label.classes():
                continue
            if (ln.attrs["y1"] == ln.attrs["y2"]) != horizontal:
                continue
            m = re.fullmatch(r"(-?\d[\d,]*(?:\.\d+)?)\D*", label.text().strip())
            self.assertIsNotNone(m, f"tick label {label.text()!r}")
            pos = float(ln.attrs["y1"] if horizontal else ln.attrs["x1"])
            out.append((pos, num(m.group(1)), decimals(m.group(1))))
        return out

    def test_tick_labels_are_the_values_of_the_gridlines_they_sit_on(self):
        """A label that says 200 sits on the gridline that is 200 on the axis the panel declares (so a changed tick format or a
        label list that no longer matches the scale fails)."""
        checked = 0
        for name, dom, _, _ in VARIANTS:
            for cid in CARD_IDS:
                for si, sv in enumerate(card_node(dom, cid).find_all("svg", "svg")):
                    for pi, panel in enumerate(sv.find_all("g", "panel")):
                        at = self.where(name, cid, si, pi)
                        lo, hi = float(panel.attrs["data-lo"]), float(panel.attrs["data-hi"])
                        kind = panel.attrs["data-kind"]
                        if kind == "hbar":
                            x0, pw = float(panel.attrs["data-x0"]), float(panel.attrs["data-pw"])
                            pairs = [(lo + (pos - x0) / pw * (hi - lo), v, d) for pos, v, d in self.tick_pairs(panel, False)]
                        else:
                            base, ph = float(panel.attrs["data-base"]), float(panel.attrs["data-ph"])
                            pairs = [(lo + (base - pos) / ph * (hi - lo), v, d) for pos, v, d in self.tick_pairs(panel, True)]
                        self.assertGreaterEqual(len(pairs), 3, at)
                        for at_axis, label, dec in pairs:
                            self.assertTrue(abs(at_axis - label) <= 0.5 * 10 ** -dec + 1e-6 * (hi - lo), f"{at}: a tick says {label} at {at_axis:.3f}")
                            checked += 1
                    for g in sv.find_all("g", "nl"):
                        at = f"{name}/{cid}/{g.attrs['data-id']}/svg {si}"
                        lo, hi, x0, pw = (float(g.attrs[k]) for k in ("data-lo", "data-hi", "data-x0", "data-pw"))
                        for pos, label, dec in self.tick_pairs(g, False):
                            at_axis = lo + (pos - x0) / pw * (hi - lo)
                            self.assertTrue(abs(at_axis - label) <= 0.5 * 10 ** -dec + 1e-6 * (hi - lo), f"{at}: a tick says {label} at {at_axis:.3f}")
                            checked += 1
        self.assertGreater(checked, 800)     # about nine hundred ticks over 19 panels and four forward lines, in 2 drawings of 4 pages

    # ---- forward-test number lines
    def test_forward_bands_diamonds_and_dots_sit_where_their_values_put_them(self):
        bands = {"F1": (R.CONSTS["f1_lo"][0] / 1e6, R.CONSTS["f1_hi"][0] / 1e6), "F2": (R.CONSTS["f2_lo"][0] / 1e3, R.CONSTS["f2_hi"][0] / 1e3)}
        refs = {"F1": METRICS["buyback_wallet_near_m"], "F2": METRICS["net_issuance_near_per_day_30d_k"],
                "F3": METRICS["take_captured_bp_30d"], "F4": METRICS["intents_share_peerset_30d_pct"]}
        for name, dom, _, result in VARIANTS:
            for si, sv in enumerate(card_node(dom, "forward").find_all("svg", "svg")):
                nls = sv.find_all("g", "nl")
                self.assertEqual([g.attrs["data-id"] for g in nls], ["F1", "F2", "F3", "F4"])
                for g in nls:
                    fid = g.attrs["data-id"]
                    at = f"{name}/{fid}/svg {si}"
                    lo, hi, x0, pw = (float(g.attrs[k]) for k in ("data-lo", "data-hi", "data-x0", "data-pw"))

                    def x_of(v: float, lo: float = lo, hi: float = hi, x0: float = x0, pw: float = pw) -> float:
                        return x0 + pw * (v - lo) / (hi - lo)

                    band = g.find("rect", "band")
                    a, b = float(band.attrs["data-a"]), float(band.attrs["data-b"])
                    if fid in bands:
                        self.assertEqual((a, b), bands[fid], at)
                    elif fid == "F3":
                        self.assertEqual((a, b), (lo, R.CONSTS["f3_max_bp"][0]), at)
                    else:
                        self.assertEqual((a, b), (R.CONSTS["f4_min_pct"][0], hi), at)
                    self.assertAlmostEqual(float(band.attrs["x"]), x_of(a), delta=0.2, msg=at)
                    self.assertAlmostEqual(float(band.attrs["width"]), x_of(b) - x_of(a), delta=0.2, msg=at)
                    diamonds = g.find_all("path", "ghost")
                    obs = g.find_all("circle", "sk")
                    if result is None:   # nothing scored: the last committed value, for scale, and no observed dot
                        self.assertEqual((len(diamonds), len(obs)), (1, 0), at)
                        self.assertAlmostEqual(float(diamonds[0].attrs["data-v"]), refs[fid], places=6, msg=at)
                        self.assertAlmostEqual(path_points(diamonds[0].attrs["d"])[0][0], x_of(refs[fid]), delta=0.2, msg=at)
                    else:
                        self.assertEqual(len(diamonds), 0, at)
                        r = result["results"][fid]
                        if r["result"] in ("PASS", "MISS"):
                            key, scale = {"F1": ("balance_near", 1e6), "F2": ("mean_near_per_day", 1e3), "F3": ("take_rate_bp", 1),
                                          "F4": ("intents_share_pct", 1)}[fid]
                            self.assertEqual(len(obs), 1, at)
                            v = r[key] / scale
                            self.assertAlmostEqual(float(obs[0].attrs["data-v"]), v, places=6, msg=at)
                            self.assertAlmostEqual(float(obs[0].attrs["cx"]), x_of(v), delta=0.2, msg=at)
                            self.assertTrue(lo <= v <= hi, f"{at}: the axis was not widened to hold the observed value")
                            labels = [t for t in g.find_all("text", "val") if refs_in(t, ("data-f",))]
                            self.assertEqual(len(labels), 1, at)
                            self.label_matches(labels[0], v, at)
                        else:
                            self.assertEqual(len(obs), 0, at)


# ------------------------------------------------------------------ numbers that are not in a data-attributed span
MONTH3 = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
MONTHF = "January|February|March|April|May|June|July|August|September|October|November|December"
# A number in the text may be one of these and nothing else. Each is either an identifier, a date or a time, or a window
# length the pre-registration and the README name. Everything that is a value (a count, a share, a dollar figure, a block
# height, a byte count) must sit in a span that names its source.
DATE_MASKS = [re.compile(p) for p in (
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",                                   # a timestamp quoted from result.json
    r"\d{4}-\d{2}-\d{2}", r"(?<![\d.])\d{4}-\d{2}(?!\d)", r"(?<![\d-])\d{2}-\d{2}(?![\d-])",   # dates, months, "07-07"
    r"\b\d{2}:\d{2}\b",                                                        # a clock time, as in 00:00 UTC
    rf"\b(?:{MONTH3}) \d{{1,2}}\b", rf"\b1-\d{{1,2}} (?:{MONTHF})\b",          # "Aug 7", "1-4 November"
    r"(?<![\d.,])20\d{2}(?![\d]|[.,]\d)",                                       # a year
)]
NAME_MASKS = [re.compile(p) for p in (
    r"\b[A-Za-z]+[-_]?\d+[A-Za-z0-9]*\b",                                      # identifiers: H1a, F1, P3, HSP-029, SHA-256, top-100
    r"\b1Click\b", r"(?i:\btiers? \d(?:-\d)?\b)",                              # a product name, and PREREG's tier numbers
)]
TEXT_ALLOWED = DATE_MASKS + NAME_MASKS + [re.compile(p) for p in (
    r"\b(?:30|90|180|365)(?:-day| days?| before)\b",                           # window lengths
    r"\bfirst 16 hex\b", r"\bsteps? \d(?: to \d)?\b", r"÷ 2\b",                # the fingerprint length, step numbers, the rule
    r"\bof 4\b", r"(?<![\d.])0%",                                               # "not scorable of 4" (F1 to F4), "0%"
)]
TEXT_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
SKIP_TAGS = {"style", "head", "pre", "code", "svg"}
SKIP_CLASSES = {"verbatim", "sha", "ver"}   # PREREG's own words, a hash and a byte count (data-r), a Python version


def carries_ref(n: Node) -> bool:
    """True for an element that names the source of the number it holds. A data-k on a <li> or <tr> is a row key, not a
    reference: the text under it is not exempt."""
    return any(a in n.attrs for a in REF_ATTRS if not (a == "data-k" and n.tag in ("li", "tr")))


def unexplained_numbers(dom: Node) -> list[str]:
    """Every number in the page text that is outside a data-attributed span, a code element, a chart or a verified table
    and is not one of TEXT_ALLOWED."""
    problems: list[str] = []

    def walk(n: Node, wrapped: bool, skipping: bool) -> None:
        wrapped = wrapped or carries_ref(n)
        skipping = (skipping or n.tag in SKIP_TAGS or bool(n.classes() & SKIP_CLASSES)
                    or (n.tag == "table" and ("data-series" in n.attrs or "data-raw" in n.attrs)))
        for c in n.children:
            if isinstance(c, Node):
                walk(c, wrapped, skipping)
            elif not wrapped and not skipping:
                masked = c
                for rx in TEXT_ALLOWED:
                    masked = rx.sub(lambda m: " " * len(m.group(0)), masked)
                for m in TEXT_NUMBER.finditer(masked):
                    a, b = max(0, m.start() - 30), min(len(c), m.end() + 30)
                    problems.append(f"{m.group(0)!r} in ...{c[a:b].strip()}...")

    walk(dom.find("body"), False, False)
    return problems


class Numbers(unittest.TestCase):
    """No number reaches the reader unless it is in a span that names its source or is a date, an identifier or a window length."""

    def test_no_unexplained_number_in_the_text(self):
        for name, dom, _, _ in VARIANTS:
            with self.subTest(variant=name):
                self.assertEqual(unexplained_numbers(dom), [])

    def test_the_scan_catches_a_hard_coded_number(self):
        """The scan is not vacuous: a plain 909 or a plain 910 where a span belongs is found."""
        dom, _ = parse('<html><body><main><p>In the window all <span data-m="escrow_funded_exact_30d_n">909</span> were funded.</p>'
                       '<p>In the window all 909 were funded, 910 or 15.81% of them, on 2026-10-06 (30 days), see H1b and 1Click.</p>'
                       '<p>Take <code>--sample 60</code> and <span class="sha">1,162 bytes</span>.</p></main></body></html>')
        found = unexplained_numbers(dom)
        self.assertEqual(len(found), 3, found)
        self.assertTrue(found[0].startswith("'909'") and found[1].startswith("'910'") and found[2].startswith("'15.81'"), found)

    def test_no_unexplained_number_in_chart_text(self):
        """Text drawn inside a chart: axis ticks and a few named constants only. Values are in data-referenced tspans."""
        phrases = ("0 to 20% axis", "100% is all of net issuance", "1 bp = 0.01%", "1×: equal to")   # named, and tested with the axes
        allowed = TEXT_ALLOWED + [re.compile(re.escape(p)) for p in phrases]

        def own_text(n: Node) -> str:
            return "".join(c if isinstance(c, str) else ("" if carries_ref(c) else own_text(c)) for c in n.children)

        for name, dom, _, _ in VARIANTS:
            bad = []
            for sv in dom.find_all("svg", "svg"):
                for t in sv.find_all("text"):
                    if "tk" in t.classes():   # tick and category labels: checked against the axes and the golden categories
                        continue
                    masked = own_text(t)
                    for rx in allowed:
                        masked = rx.sub(lambda m: " " * len(m.group(0)), masked)
                    bad += [f"{m.group(0)!r} in {own_text(t).strip()[:60]!r}" for m in TEXT_NUMBER.finditer(masked)]
            self.assertEqual(bad, [], name)

    def test_numbers_in_chart_titles_descriptions_and_tooltips_are_source_values(self):
        """The accessible text of a chart quotes plain numbers; each must be a value in metrics.json or series.json (or a
        constant the page names), so a wrong or hard-coded number there fails."""
        values: set[float] = set()

        def collect(v) -> None:
            if isinstance(v, bool):
                return
            if isinstance(v, (int, float)):
                values.add(float(v))
            elif isinstance(v, list):
                for x in v:
                    collect(x)
            elif isinstance(v, dict):
                for x in v.values():
                    collect(x)

        collect(METRICS)
        collect(SERIES)
        for value, text, _ in R.CONSTS.values():
            values.update({value, float(text)})
        values.update(float(x) for x in (0, 1, 20, 25, 30, 50, 90, 100, 180, 365, 1200))     # axis ends and window lengths
        values.update(float(len(rows)) for rows in SERIES.values())                           # "over 24 months"
        masks = DATE_MASKS + NAME_MASKS
        for name, dom, _, _ in VARIANTS:
            bad = []
            for sv in dom.find_all("svg", "svg"):
                for n in sv.iter():
                    if n.tag in ("title", "desc"):
                        masked = n.text()
                        for rx in masks:
                            masked = rx.sub(lambda m: " " * len(m.group(0)), masked)
                        for m in TEXT_NUMBER.finditer(masked):
                            if num(m.group(0)) not in values:
                                bad.append(f"{m.group(0)!r} in {n.text()[:70]!r}")
            self.assertEqual(bad, [], name)

    def test_facts_read_from_repo_files_equal_the_files(self):
        """data-r spans: a byte count, the number of very long lines the page cuts, or an endpoint block height."""
        seen = {"bytes": 0, "cut": 0}
        for n in DOM.iter():
            if "data-r" not in n.attrs:
                continue
            kind, _, rel = n.attrs["data-r"].partition(":")
            text = n.text().replace("bytes", "").strip()
            raw = (ROOT / rel).read_text(encoding="utf-8")
            if kind == "bytes":
                self.assertEqual(num(text), len(raw.encode("utf-8")), rel)
            elif kind == "cut":
                self.assertEqual(num(text), sum(1 for line in raw.split("\n") if len(line) > 400), rel)
            else:
                self.fail(f"unknown data-r kind {kind}")
            seen[kind] += 1
        self.assertGreaterEqual(seen["bytes"], 12)
        self.assertGreaterEqual(seen["cut"], 1)    # sql/h1b_b_wnear_logs.sql, under H1b and again under H1c

    def test_the_end_point_blocks_in_the_h1c_query_come_from_the_raw_snapshot(self):
        blocks = sorted(json.loads((ROOT / "data/raw/rpc/buyback_balance_endpoints.json").read_text(encoding="utf-8"))["blocks"], key=int)
        self.assertEqual(len(blocks), 2)
        query = next(d for d in card_node(DOM, "h1c").find_all("details") if d.find("summary").text().strip() == "Query")
        self.assertIn(f"block_id {blocks[0]} and {blocks[1]}", query.text())
        self.assertIn("end-point blocks", card_node(DOM, "h1c").find("div", "source").text())

    def test_the_partial_month_note_is_the_as_of_date(self):
        asof = date.fromisoformat(METRICS["asof"])
        want = f"1-{asof.day} {MONTHF.split('|')[asof.month - 1]}"
        found = re.findall(rf"\b1-\d{{1,2}} (?:{MONTHF})\b", re.sub(r"\s+", " ", DOM.find("body").text()))
        self.assertGreaterEqual(len(found), 6)
        self.assertEqual(set(found), {want})

    def test_take_block_labels_are_the_metric_windows(self):
        h3 = card_node(DOM, "take").find("h3").text()
        self.assertIn(f"({block_label(METRICS['take_b1_window'])})", h3)
        self.assertIn(f"({block_label(METRICS['take_b3_window'])})", h3)


# ------------------------------------------------------------------ claims the page makes about itself
def make_recipe(name: str) -> list[str]:
    """The commands of a Makefile target, with $(PY) read as python3."""
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    for i, ln in enumerate(lines):
        if re.match(rf"^{re.escape(name)}:", ln):
            out = []
            for later in lines[i + 1:]:
                if not later.startswith("\t"):
                    break
                out.append(later[1:].replace("$(PY)", "python3"))
            return out
    raise AssertionError(f"no Makefile target {name}")


def delivery_rows() -> list[dict]:
    """Every row of data/raw/escrow/deliveries.csv (all paths: collectors, escrow unshields, other)."""
    with open(ROOT / "data/raw/escrow/deliveries.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class PageClaims(unittest.TestCase):
    """What the page says about how it is built and what it shows is true, and says no more than is true."""

    def test_the_page_says_bigquery_where_it_says_what_was_frozen_before(self):
        text = re.sub(r"\s+", " ", DOM.find("body").text())
        self.assertNotIn("before any flow query", text)
        self.assertGreaterEqual(text.count("before any BigQuery flow query ran"), 3)   # scorecard, header, pre-registered section
        prereg = (ROOT / "PREREG.md").read_text(encoding="utf-8")
        heading = next(line for line in prereg.splitlines() if line.startswith("## What we had already seen"))
        self.assertEqual(re.sub(r"[^a-z0-9 -]", "", heading[3:].lower()).replace(" ", "-"), R.PREREG_ANCHOR)
        links = [a for a in DOM.find_all("a") if a.attrs["href"] == f"{R.REPO_URL}/blob/{R.BRANCH}/PREREG.md#{R.PREREG_ANCHOR}"]
        self.assertEqual(len(links), 2)    # the scorecard note and the header

    def test_the_lede_names_the_two_commands_and_the_one_that_runs_both(self):
        lede = DOM.find("p", "lede").text()
        for want in ("python3 -m pipeline.compute", "data/raw/", "python3 -m pipeline.render", "make site", "one command"):
            self.assertIn(want, lede)
        self.assertNotIn("rebuilt from committed data by one command", lede)

    def test_make_site_is_the_reproduce_steps_then_render(self):
        self.assertEqual(make_recipe("site"), make_recipe("reproduce") + make_recipe("render"))
        self.assertEqual(make_recipe("render-check"), ["python3 -m pipeline.render --check"])
        self.assertIn("site", re.search(r"^\.PHONY:(.*)$", (ROOT / "Makefile").read_text(encoding="utf-8"), re.MULTILINE).group(1).split())

    def test_the_reproduce_steps_are_the_make_targets_they_cite(self):
        sec = next(n for n in DOM.find_all("section") if n.attrs.get("id") == "reproduce")
        steps = [li.find("p", "do").find("code").text() for li in sec.find_all("li")]
        self.assertEqual(len(steps), 7)
        self.assertEqual(steps[1:4], make_recipe("reproduce"))      # "make reproduce runs steps 2 to 4"
        self.assertEqual(steps[5:6], make_recipe("render-check"))   # "make render-check runs step 6"
        self.assertEqual(steps[6:7], make_recipe("render"))         # "then step 7"
        self.assertEqual(steps[1:4] + steps[6:7], make_recipe("site"))
        note = sec.find("p", "note").text()
        for want in ("make reproduce runs steps 2 to 4", "make render-check runs step 6", "make site runs steps 2 to 4 and then step 7"):
            self.assertIn(want, note)

    def test_the_test_step_does_not_claim_more_than_the_tests_check(self):
        sec = next(n for n in DOM.find_all("section") if n.attrs.get("id") == "reproduce")
        step = next(li for li in sec.find_all("li") if "unittest" in li.find("p", "do").text()).find("p", "see").text()
        self.assertIn("each number it prints in a data-attributed span is compared with the source it names", step)
        self.assertIn("the committed page must equal a fresh render", step)
        self.assertNotIn("every number in it is checked", DOM.find("body").text())

    # ---- the supply chart
    def test_the_supply_reference_label_is_above_the_plot_not_on_the_columns(self):
        key = "net_issuance_near_per_day_30d_k"
        for name, dom, _, _ in VARIANTS:
            for si, sv in enumerate(card_node(dom, "supply").find_all("svg", "svg")):
                panel = sv.find_all("g", "panel")[1]
                top = float(panel.attrs["data-base"]) - float(panel.attrs["data-ph"])
                label = [t for t in panel.find_all("text") if (("m", key) in refs_in(t))]
                self.assertEqual(len(label), 1, name)
                self.assertLess(float(label[0].attrs["y"]), top, f"{name}/svg {si}: the label sits inside the plot")
                self.assertEqual(panel.find_all("text", "rl"), [], "no label inside the plot of this chart")
                swatch = [ln for ln in panel.find_all("line", "refline") if "lg" in ln.classes()]
                self.assertEqual(len(swatch), 1)
                self.assertLess(float(swatch[0].attrs["y1"]), top)

    def test_the_two_heights_of_the_daily_supply_bars_are_the_epoch_starts(self):
        """'NEAR mints once per epoch and a UTC day holds three or four epoch starts, so the daily bars come in two heights:
        the taller bars are the four-epoch days.' Checked against the epoch boundaries in data/raw/rpc/epoch_issuance.json."""
        text = card_node(DOM, "supply").text()
        for want in ("NEAR mints once per epoch", "three or four epoch starts", "the taller bars are the four-epoch days"):
            self.assertIn(want, re.sub(r"\s+", " ", text))
        raw = json.loads((ROOT / "data/raw/rpc/epoch_issuance.json").read_text(encoding="utf-8"))
        col = raw["epoch_fields"].index("start_timestamp_ns")
        starts: dict[str, int] = {}
        for row in raw["epochs"]:
            d = datetime.fromtimestamp(int(row[col]) / 1e9, tz=timezone.utc).date().isoformat()
            starts[d] = starts.get(d, 0) + 1
        end = date.fromisoformat(METRICS["asof"])
        days = [end - timedelta(days=i) for i in range(89, -1, -1)]
        supply = {r["date"]: r["supply_m"] for r in SERIES["supply_daily"]}
        change = {d: (supply[d.isoformat()] - supply[(d - timedelta(days=1)).isoformat()]) * 1000 for d in days}
        per_day = {d: starts[d.isoformat()] for d in days}
        self.assertEqual(set(per_day.values()), {3, 4})
        tall = [change[d] for d in days if per_day[d] == 4]
        short = [change[d] for d in days if per_day[d] == 3]
        self.assertGreater(min(tall), max(short), "a four-epoch day is not always taller than a three-epoch day")

    # ---- the escrow chart
    def test_the_escrow_query_note_the_footnote_and_the_source_list(self):
        with open(ROOT / "data/raw/escrow/deliveries.csv", newline="", encoding="utf-8") as fh:
            unshields = [r for r in csv.DictReader(fh) if r["path"] == "escrow_unshield"]
        last_sample = max(r["day"] for r in unshields if r["attribution"] == "sample")
        traced_from = min(r["day"] for r in unshields if r["day"] > last_sample)
        self.assertEqual(traced_from, "2026-10-06")
        self.assertTrue(all(r["attribution"] == "row" for r in unshields if r["day"] >= traced_from))
        early = sorted(r["day"] for r in unshields if r["attribution"] == "sample" and r["day"][:7] == traced_from[:7])
        self.assertEqual((early[0], early[-1]), ("2026-10-01", "2026-10-05"))
        card = card_node(DOM, "escrow")
        footnote = f"October includes {early[0]} to {early[-1]}, attributed from samples."
        for sv in card.find_all("svg", "svg"):
            drawn = re.sub(r"\s+", " ", " ".join(t.text() for t in sv.find_all("text")))
            self.assertIn(footnote, drawn)
            self.assertIn(f"funding hop traced per delivery from {traced_from}", drawn)
        # the Query block says what its SQL covers and where the rest comes from
        sql = (ROOT / "sql/buyback_withdraw_sources.sql").read_text(encoding="utf-8")
        d0, d1 = re.search(r"BETWEEN '(\d{4}-\d{2}-\d{2})' AND '(\d{4}-\d{2}-\d{2})'", sql).groups()
        query = next(d for d in card.find_all("details") if d.find("summary").text().strip() == "Query")
        note = re.sub(r"\s+", " ", query.find("p", "qnote").text())
        self.assertIn(f"This SQL covers only {d0} to {d1}.", note)
        self.assertIn(MANIFEST["raw/escrow/deliveries.csv"]["source"], note)
        self.assertIn("data/MANIFEST.json", note)
        self.assertIn("it does not trace funding hops", note)
        source = card.find("div", "source").text()
        for want in ("sql/buyback_withdraw_sources.sql", "data/raw/bq/buyback_withdraw_sources.json", "data/raw/escrow/deliveries.csv"):
            self.assertIn(want, source)
        # the sentence "the SQL's output has the same NEAR per day and wallet as the per-delivery table over those days" is true
        self.assertIn("has the same NEAR per day and wallet as the per-delivery table", note)
        from fractions import Fraction
        sql_out: dict[tuple[str, str], Fraction] = {}
        for x in json.loads((ROOT / "data/raw/bq/buyback_withdraw_sources.json").read_text(encoding="utf-8")):
            sql_out[(x["day"], x["wallet"])] = sql_out.get((x["day"], x["wallet"]), Fraction(0)) + Fraction(x["near"])
        table: dict[tuple[str, str], Fraction] = {}
        for r in delivery_rows():
            if d0 <= r["day"] <= d1:
                table[(r["day"], r["wallet"])] = table.get((r["day"], r["wallet"]), Fraction(0)) + Fraction(int(r["amount_yocto"]), 10**24)
        self.assertEqual(set(sql_out), set(table))
        for k, v in sql_out.items():
            self.assertLess(abs(v - table[k]), Fraction(1, 10**6), k)

    # ---- colour
    def test_blue_and_orange_keep_one_meaning_inside_each_figure(self):
        """The reading of s1 and s2 in a chart's first panel is not reused in its second panel (the cards the review named)."""
        for name, dom, _, _ in VARIANTS:
            for cid in ("partners", "paid", "h1b"):
                for si, panels in enumerate(self.panels_of(dom, cid)):
                    used = [{c for pt in pn.find_all("path") if "data-v" in pt.attrs for c in pt.classes() & {"s1", "s2"}} for pn in panels]
                    self.assertTrue(used[0], (name, cid))
                    self.assertEqual(used[1], set(), f"{name}/{cid}: panel B reuses a colour panel A gives a meaning")

    @staticmethod
    def panels_of(dom: Node, cid: str) -> list[list[Node]]:
        return [sv.find_all("g", "panel") for sv in card_node(dom, cid).find_all("svg", "svg")]

    # ---- phone tables
    def test_wide_tables_scroll_sideways_and_say_so_on_phones(self):
        css = DOM.find("style").text()
        self.assertIn("th{white-space:normal}", css)
        self.assertRegex(css, r"@media \(max-width:699px\)\{th\.txt,td\.t\{min-width:6\.5rem\}")
        self.assertIn("no-repeat local", css)        # the edge shadows that show a table scrolls
        self.assertRegex(css, r"\.scrollhint\{display:none")
        self.assertRegex(css, r"@media \(max-width:699px\)\{[^@]*\.scrollhint\{display:block\}")
        for cid in CARD_IDS:
            data = next(d for d in card_node(DOM, cid).find_all("details") if d.find("summary").text().strip() == "Data")
            self.assertIn("scrolls sideways", data.find("p", "scrollhint").text(), cid)

    def test_partners_channel_names_in_the_table_are_code(self):
        tables = [t for t in card_node(DOM, "partners").find_all("table")]
        first = [tr.find_all("td")[0] for tr in tables[0].find_all("tr") if tr.find_all("td")]
        self.assertEqual(first[0].text(), "SwapKit")
        for td, c in zip(first[1:], METRICS["buyback_fee_by_channel"]):
            self.assertEqual(td.find("code").text(), c["channel"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
