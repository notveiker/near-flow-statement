"""docs/sources-checked.md puts the repository's own wording next to what each external source says. This test keeps the
repository half of that comparison from going stale unnoticed.

Section 1 of that file is a table. Its second column, "Statement in this repository", and its last column, "Verdict",
quote the repository in double quotes. Until this test existed nothing compared those quotes with the repository: a row
could go on saying "the repository hedges X with this sentence" after the sentence was rewritten, and the file whose job
is to quote the repository exactly would be wrong without a failing check (row 22 was, after d947e75 rewrote the
sentence it quoted).

What is checked, with the standard library only and no git:

* every double-quoted string in those two columns occurs verbatim in README.md, THESIS.md, docs/*.md (not this file),
  pipeline/*.py, sql/**/*.sql, site/index.html or PREREG-ADDENDUM.md, after the same normalisation on both sides: markdown links become their
  text, backticks and HTML comments (the `<!--n:key-->` markers) disappear, HTML tags and entities are removed for the
  page and the code, SQL comment markers are removed, typographic quotes become plain ones, whitespace collapses;
* it also occurs in at least one of the files that its row names in the third column, "Where it is" (the dashboard means
  site/index.html or pipeline/render.py). Without this, a row
  that says "THESIS.md hedges X" would go on passing after THESIS.md lost the hedge, as long as the dashboard still had it;
* a quote that is not the repository's current wording is exempt only through ALLOW below, each entry with a kind and a
  one-line reason: an OLDER wording (quoted as superseded, so it must NOT be in the repository any more), the SOURCE's own
  words, or a single LABEL word. An ALLOW entry that matches no quote in the file is itself a failure;
* the sentences the file lists as "not quoted" by the repository are not quoted in it: no run of eight consecutive words
  of any quoted string in that list occurs in the corpus (a shorter quote must not occur whole).

The addendum counts as a place where a quote may be found, but not for the OLDER check and not for the "not quoted" list: its
first entries are pinned by SHA-256 and cannot change, so a quote found there stays found, while a later dated entry may
legitimately repeat an old wording when it corrects it.

The matcher is not loosened to make a row pass. A row that fails is re-quoted from the current text, or, if it is
deliberately an older version or the source's words, allowlisted here with the reason.

Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import fnmatch
import html
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "docs" / "sources-checked.md"
SECTION_1 = "## 1. Statements attributed to external documents"
SECTION_2 = "\n## 2. "
NOT_QUOTED = "Sentences on the same pages that the repository does not quote"
COLUMNS = ("Statement in this repository", "Verdict")           # the two columns whose quotes are the repository's words
CELLS = 6                                                         # #, Statement, Where, Source, What the source says, Verdict
WINDOW = 8                                                        # words of a "not quoted" sentence that must not occur
ADDENDUM = "PREREG-ADDENDUM.md"
NAMED = re.compile(r"README\.md|THESIS\.md|AGENTS\.md|PREREG-ADDENDUM\.md|docs/[a-z-]+\.md|pipeline/[a-z_]+\.py|"
                   r"sql/[A-Za-z0-9_*/]+\.sql|dashboard")

OLDER = "older"     # an earlier wording of the repository, quoted as superseded: it must be gone from the repository
SOURCE = "source"   # the external source's own words (the row contrasts them with the repository's), not the repository's
LABEL = "label"     # one word quoted to name a correction, not a statement of the repository's

# (row number, the quoted string exactly as the table writes it, with \" read as ") -> (kind, reason)
ALLOW = {
    (4, "keeps user balances in Confidential Intents"):
        (OLDER, "row 4 quotes what docs/partner-concentration.md said before the 2026-11-08 correction"),
    (5, "Developer"):
        (SOURCE, "the Terms' own word, which the verdict contrasts with the repository's word 'integrator'"),
    (7, "would be a choice, and a documented possibility, not a documented fact"):
        (OLDER, "the last sentence of THESIS.md section 2 before it was corrected; row 7 names the correction"),
    (15, "House of Stake ratification is necessary, however validator adoption is ultimately what makes it binding"):
        (SOURCE, "the governance post's words, quoted in the verdict to show what the text does not define"),
    (15, "ratifies, then governs the covenant thereafter; cannot bind validators"):
        (SOURCE, "the governance post's words about the House of Stake"),
    (16, "clears its timelock on 2026-11-16"):
        (OLDER, "THESIS.md's wording before the 2026-11-08 correction, which row 16 names"),
    (16, "Timelock"):
        (SOURCE, "the status string that the proposal contract returns, quoted in the verdict"),
}
KINDS = {OLDER, SOURCE, LABEL}

_FOLD = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def norm(text: str, kind: str = "md") -> str:
    """The same normalisation for a quote and for the files it is looked up in."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    if kind == "sql":
        text = re.sub(r"(?m)^\s*--\s?", "", text)
    if kind == "html":
        text = re.sub(r"<(script|style)\b.*?</\1>", "", text, flags=re.S)
        text = re.sub(r"<[^>]+>", "", text)
    if kind in ("html", "py"):
        text = html.unescape(text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.replace("`", "").replace('\\"', '"').translate(_FOLD)
    return re.sub(r"\s+", " ", text).strip()


def corpus() -> dict[str, str]:
    """README.md, THESIS.md, docs/*.md except the file under test, pipeline/*.py, sql/**/*.sql and site/index.html."""
    files = [ROOT / "README.md", ROOT / "THESIS.md"]
    files += [p for p in sorted((ROOT / "docs").glob("*.md")) if p != SOURCES]
    files += sorted((ROOT / "pipeline").glob("*.py")) + sorted((ROOT / "sql").rglob("*.sql")) + [ROOT / "site" / "index.html"]
    return {p.relative_to(ROOT).as_posix(): norm(p.read_text(encoding="utf-8"),
                                           {".html": "html", ".py": "py", ".sql": "sql"}.get(p.suffix, "md"))
            for p in files}


def split_row(line: str) -> list[str]:
    """The cells of one table row. A pipe inside a backtick span, or written \\|, does not split."""
    body = line.strip()
    if not (body.startswith("|") and body.endswith("|")):
        raise ValueError(f"not a table row: {line[:60]!r}")
    body, cells, cur, in_code, i = body[1:-1], [], [], False, 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and body[i + 1:i + 2] == "|":
            cur.append("|")
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def quoted(cell: str) -> list[str]:
    """Every double-quoted string in a cell; a \\" inside one is a quote mark of the quoted text, not its end."""
    out, i = [], 0
    while i < len(cell):
        if cell[i] == '"' and (i == 0 or cell[i - 1] != "\\"):
            j, buf = i + 1, []
            while j < len(cell):
                if cell[j] == "\\" and cell[j + 1:j + 2] == '"':
                    buf.append('"')
                    j += 2
                    continue
                if cell[j] == '"':
                    break
                buf.append(cell[j])
                j += 1
            else:
                raise ValueError(f"an opening quote with no end in: {cell[:80]!r}")
            out.append("".join(buf))
            i = j + 1
        else:
            i += 1
    return out


def rows(text: str) -> list[tuple[int, list[str]]]:
    """(row number, cells) of the table in section 1."""
    start = text.index(SECTION_1)
    block = text[start:text.index(SECTION_2, start)]
    lines = [ln for ln in block.splitlines() if ln.startswith("|")]
    header, _rule, *body = lines
    head = split_row(header)
    if len(head) != CELLS or head[1] != COLUMNS[0] or head[5] != COLUMNS[1]:
        raise ValueError(f"the columns of section 1 changed: {head}")
    out = []
    for ln in body:
        cells = split_row(ln)
        if len(cells) != CELLS:
            raise ValueError(f"row {cells[0]!r} has {len(cells)} cells, not {CELLS}")
        out.append((int(cells[0]), cells))
    return out


def occurs(q: str, files: dict[str, str]) -> bool:
    nq = norm(q)
    return bool(nq) and any(nq in body for body in files.values())


def named_files(cell: str, files: dict[str, str]) -> set[str]:
    """The files that a 'Where it is' cell names, as keys of `files`; the dashboard is the page and the code that renders it."""
    out = set()
    for token in NAMED.findall(cell):
        if token == "dashboard":
            out |= {"site/index.html", "pipeline/render.py"}
        elif "*" in token:
            out |= {k for k in files if fnmatch.fnmatch(k, token)}
        else:
            out.add(token)
    return out


def problems(text: str, files: dict[str, str], allow=ALLOW) -> list[str]:
    """What is wrong with the quotes of section 1: one line per problem, empty if the file is current."""
    out, used = [], set()
    lookup = {**files, ADDENDUM: ADDENDUM_TEXT}
    for number, cells in rows(text):
        named = named_files(cells[2], lookup)
        for name in sorted(named - set(lookup)):
            out.append(f"row {number} (column 3): names {name}, which this test cannot read")
        for col in (1, 5):
            for q in quoted(cells[col]):
                key = (number, q)
                if key in allow:
                    used.add(key)
                    if allow[key][0] == OLDER and occurs(q, files):
                        out.append(f"row {number} (column {col + 1}): the superseded wording {q!r} is in the repository again")
                elif not occurs(q, lookup):
                    out.append(f"row {number} (column {col + 1}): {q!r} is not in the repository")
                elif named & set(lookup) and not occurs(q, {k: lookup[k] for k in named & set(lookup)}):
                    where = ", ".join(sorted(k for k, v in lookup.items() if norm(q) in v))
                    out.append(f"row {number} (column {col + 1}): {q!r} is in {where} but not in the files the row names "
                               f"({', '.join(sorted(named))})")
    out += [f"ALLOW entry {key!r} matches no quote in the file" for key in sorted(set(allow) - used)]
    return out


def not_quoted_windows(text: str) -> list[tuple[str, str]]:
    """(quote, window) pairs for the quoted strings of the 'not quoted' list: each run of WINDOW words, or the whole quote if shorter."""
    start = text.index(NOT_QUOTED)
    region = text[start:text.index(SECTION_2, start)]
    out = []
    for ln in region.splitlines():
        if not ln.startswith("- "):
            continue
        for q in quoted(ln):
            words = norm(q).split()
            if not words:
                continue
            for i in range(max(1, len(words) - WINDOW + 1)):
                out.append((q, " ".join(words[i:i + WINDOW])))
    return out


def quoted_after_all(text: str, files: dict[str, str]) -> list[str]:
    return [f"{q[:70]!r}: {w!r} is in the repository" for q, w in not_quoted_windows(text) if any(w in b for b in files.values())]


TEXT = SOURCES.read_text(encoding="utf-8")
FILES = corpus()
ADDENDUM_TEXT = norm((ROOT / ADDENDUM).read_text(encoding="utf-8"))


def replace_once(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, (text.count(old), old[:80])
    return text.replace(old, new)


def introduced(text: str, files: dict[str, str]) -> list[str]:
    """The problems that a mutated copy has and the real file does not, so that a bite test measures the checker, not the file."""
    base = problems(TEXT, FILES)
    return [p for p in problems(text, files) if p not in base]


class SourcesCheckedIsCurrent(unittest.TestCase):
    def test_the_table_parses_and_is_numbered_from_one(self):
        table = rows(TEXT)
        self.assertEqual([n for n, _ in table], list(range(1, len(table) + 1)))
        self.assertGreaterEqual(len(table), 32)
        n_quotes = sum(len(quoted(c[col])) for _, c in table for col in (1, 5))
        self.assertGreaterEqual(n_quotes, 40, "the quote parser found almost nothing: the table changed shape, or the parser broke")

    def test_this_file_is_not_its_own_evidence(self):
        self.assertNotIn("docs/sources-checked.md", FILES)
        self.assertIn("THESIS.md", FILES)
        self.assertIn("site/index.html", FILES)
        self.assertTrue(any(k.startswith("sql/") for k in FILES))

    def test_every_quote_of_the_repository_is_in_the_repository(self):
        self.assertEqual(problems(TEXT, FILES), [])

    def test_every_exemption_has_a_known_kind_and_a_reason(self):
        for key, (kind, reason) in ALLOW.items():
            with self.subTest(key=key):
                self.assertIn(kind, KINDS)
                self.assertGreaterEqual(len(reason.split()), 5, "say why, in a line")
                self.assertNotIn("\n", reason)

    def test_the_sentences_listed_as_not_quoted_are_not_quoted(self):
        self.assertGreaterEqual(len(not_quoted_windows(TEXT)), 4, "the list parsed to nothing")
        self.assertEqual(quoted_after_all(TEXT, FILES), [])


class TheCheckerBites(unittest.TestCase):
    """Each test puts a real staleness into an in-memory copy of the file (or of the corpus) and expects it to be reported.
    Without these, a parser that silently found no quotes would let the test above pass for ever."""

    # What row 22's verdict said until it was corrected: THESIS.md had hedged the halving, and the sentence had been rewritten.
    STALE_ROW_22 = ('| not found: this is an inference. docs/intents-fee-flows.md hedges it ("The Dune query behind it could not be '
                    'read directly."); THESIS.md states it without that hedge |')

    def current_row_22_verdict(self) -> str:
        cells = dict(rows(TEXT))[22]
        return "| " + cells[5] + " |"

    def test_the_old_row_22_wording_is_caught(self):
        stale = replace_once(TEXT, self.current_row_22_verdict(), self.STALE_ROW_22)
        found = introduced(stale, FILES)
        self.assertEqual(len(found), 1, found)
        self.assertIn("row 22 (column 6)", found[0])
        self.assertIn("The Dune query behind it could not be read directly.", found[0])

    def test_a_one_word_change_in_a_quote_is_caught(self):
        old = "shows on chain as the escrow paying the exact amount to a fresh account"
        found = introduced(replace_once(TEXT, old, old.replace("fresh", "new")), FILES)
        self.assertEqual(len(found), 1, found)
        self.assertIn("row 3 (column 2)", found[0])

    def test_a_quote_dropped_from_the_repository_is_caught(self):
        thin = {k: v.replace("a production constant shared by all participants", "x") for k, v in FILES.items()}
        found = [p for p in problems(TEXT, thin) if p not in problems(TEXT, FILES)]
        self.assertTrue(found and all(p.startswith("row 1 (column 2)") for p in found), found)

    def test_a_superseded_wording_that_comes_back_is_caught(self):
        back = {**FILES, "THESIS.md": FILES["THESIS.md"] + " it clears its timelock on 2026-11-16 again"}
        found = [p for p in problems(TEXT, back) if p not in problems(TEXT, FILES)]
        self.assertEqual(len(found), 1, found)
        self.assertIn("row 16 (column 2): the superseded wording", found[0])

    def test_an_allowlist_entry_that_matches_nothing_is_caught(self):
        extra = {**ALLOW, (9, "a quote that is not in row nine"): (SOURCE, "a dead entry, to show that it is reported")}
        found = [p for p in problems(TEXT, FILES, extra) if p not in problems(TEXT, FILES)]
        self.assertEqual(len(found), 1, found)
        self.assertIn("matches no quote", found[0])

    def test_a_quote_the_table_cannot_close_is_an_error_not_a_pass(self):
        with self.assertRaises(ValueError):
            quoted('a statement with "an opening quote and no end')

    def test_a_hedge_lost_in_the_file_a_row_names_is_caught_even_if_the_dashboard_still_has_it(self):
        # Row 22 says THESIS.md hedges the halving. The dashboard's code carries the same words, so a check against the
        # whole corpus alone would pass after THESIS.md dropped the hedge. (Found by mutation: the first version of this test
        # passed that mutant.)
        hedge = "appears to count both legs of a swap; its adapter states no methodology"
        self.assertIn(hedge, FILES["pipeline/render.py"], "premise: the renderer has the same words")
        dropped = {**FILES, "THESIS.md": FILES["THESIS.md"].replace(hedge, "counts both legs of a swap; its adapter states no methodology")}
        found = [p for p in problems(TEXT, dropped) if p not in problems(TEXT, FILES)]
        self.assertEqual(len(found), 1, found)
        self.assertIn("row 22 (column 2)", found[0])
        self.assertIn("not in the files the row names", found[0])

    def test_a_row_that_names_a_file_this_test_cannot_read_is_caught(self):
        bad = replace_once(TEXT, "| THESIS.md section 3 (\"Volume is not the token\"); docs/intents-fee-flows.md",
                           "| THESIS.md section 3 (\"Volume is not the token\"); docs/intents-fee-flowz.md")
        found = [p for p in problems(bad, FILES) if p not in problems(TEXT, FILES)]
        self.assertTrue(any("names docs/intents-fee-flowz.md" in p for p in found), found)

    def test_the_schedule_1_7_sentence_listed_as_not_quoted_again_is_caught(self):
        # THESIS.md section 2 quotes "may be directed by the 1Click Service to a designated fee recipient ...", so the
        # sentence may not sit in the 'not quoted' list (it was there, wrongly, until row 32 took it over).
        sentence = ('"The Infrastructure Fees may be directed by the 1Click Service to a designated fee recipient in connection '
                    'with NEAR ecosystem infrastructure, development and growth activities."')
        marker = "- Terms of use, definitions:"
        bad = replace_once(TEXT, marker, f"- Terms of use, Schedule 1, 1.7 (read 01:35:08Z): {sentence} It names no recipient.\n{marker}")
        found = [p for p in quoted_after_all(bad, FILES) if p not in quoted_after_all(TEXT, FILES)]
        self.assertTrue(found, "the sentence is in THESIS.md, so listing it as not quoted must fail")

    def test_the_section_one_quotes_are_found_in_the_columns_the_file_names(self):
        table = dict(rows(TEXT))
        self.assertIn('"direct 100% of fees to a NEAR revenue wallet"', table[12][1])
        self.assertIn('"split 50/50 between NEAR and the partner"', table[12][1])
        self.assertIn('"republish the data in any form without permission"', table[30][5])
        self.assertIn('"may be directed by the 1Click Service', table[32][1])
        self.assertIn('("if any", §6.3)', quoted(table[7][1])[0], "the \\\" escapes inside a quote are read as quote marks")


if __name__ == "__main__":
    unittest.main(verbosity=2)
