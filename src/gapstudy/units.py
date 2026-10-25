"""Phase 3: split each document into knowledge units.

A unit is an H2 or H3 section, plus H1 sections when a document uses H1 for
sections rather than as a single title (documents whose headings start at H3
or deeper use their top two levels). Deeper headings stay inside their
section. Text before the first section heading is a "preamble" unit.
Documents without section headings fall back to top-level blocks (paragraphs,
lists, code); a lead-in line ending in ':' or a lone bold line is merged into
the block that follows it.

    python -m gapstudy.units      # writes data/processed/units.csv
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass

import pandas as pd
from markdown_it import MarkdownIt

from gapstudy.github_client import PROJECT_ROOT

PROCESSED = PROJECT_ROOT / "data" / "processed"
CORPUS = PROCESSED / "corpus"
DOCS = ("agent", "README", "CONTRIBUTING")

MD = MarkdownIt("commonmark").enable("table")
FRONT_MATTER = re.compile(r"\A﻿?---[ \t]*\n.*?\n---[ \t]*\n", re.S)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
FENCE = re.compile(r"^(```|~~~).*?^\1", re.S | re.M)
WORD = re.compile(r"\w+")
PSEUDO_HEADING = re.compile(r"^(\*\*|__)[^*_\n]+\1:?$")  # a paragraph that is one bold line
ANCHOR_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[[^\]]+\]\(#[^)]*\)\s*$")
TOC_HEADING = re.compile(r"^(table of contents|contents|toc)$", re.I)
BLOCK_OPENERS = {"paragraph_open", "bullet_list_open", "ordered_list_open", "fence", "code_block",
                 "table_open", "html_block", "blockquote_open"}
LONG_WORDS = 300


@dataclass
class Unit:
    n: int
    kind: str  # "section" | "preamble" | "block"
    level: int | None
    heading: str
    heading_path: str
    text: str


def clean(text: str) -> str:
    """Drop BOM, YAML front matter and HTML comments outside code fences,
    keeping line numbers stable."""
    blank = lambda m: "\n" * m.group().count("\n")
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    text = FRONT_MATTER.sub(blank, text)
    out, pos = [], 0
    for fence in FENCE.finditer(text):
        out += [HTML_COMMENT.sub(blank, text[pos:fence.start()]), fence.group()]
        pos = fence.end()
    return "".join(out + [HTML_COMMENT.sub(blank, text[pos:])])


def headings(tokens) -> list[tuple[int, int, int, str]]:
    """(first line, end line, level, title) of top-level headings."""
    out = []
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and tok.level == 0:
            out.append((tok.map[0], tok.map[1], int(tok.tag[1]), tokens[i + 1].content.strip()))
    return out


def split_levels(hs) -> tuple[list[int], int | None]:
    """Section levels and the line of the title heading, if any.

    H2 and H3 as in the proposal, plus H1 when the document uses H1 for
    sections; documents whose headings start deeper use their top two levels.
    """
    title_line = None
    levels = [lvl for _, _, lvl, _ in hs]
    if levels and levels[0] == min(levels) and levels.count(levels[0]) == 1:
        title_line = hs[0][0]  # a single top-level heading at the start is the title
        levels = levels[1:]
    if not levels:
        return [], title_line
    top = min(levels)
    return list(range(top, max(top + 1, 3) + 1)), title_line


def body(lines: list[str], start: int, end: int) -> str:
    return "\n".join(lines[start:end]).strip()


def section_units(lines, hs, levels, title_line) -> list[Unit]:
    units, path = [], {}
    cuts = [h for h in hs if h[2] in levels and h[0] != title_line]
    heading_lines = {i for start, end, _, _ in hs for i in range(start, end)}
    first = cuts[0][0]
    pre = "\n".join(l for i, l in enumerate(lines[:first]) if i not in heading_lines).strip()
    if pre:
        units.append(Unit(0, "preamble", None, "", "", pre))
    for k, (line, line_end, lvl, title) in enumerate(cuts):
        path = {l: t for l, t in path.items() if l < lvl}
        path[lvl] = title
        end = cuts[k + 1][0] if k + 1 < len(cuts) else len(lines)
        text = body(lines, line_end, end)
        if text:  # a heading whose content is all in its subsections is not a unit
            units.append(Unit(len(units), "section", lvl, title, " > ".join(path[l] for l in sorted(path)), text))
    return units


def block_units(tokens, lines, title_line) -> list[Unit]:
    spans = [tok.map for tok in tokens if tok.level == 0 and tok.type in BLOCK_OPENERS and tok.map]
    spans = [(a, b) for a, b in spans if a != title_line]
    units, carry = [], None
    for a, b in spans:
        if carry is not None:
            a, carry = carry, None
        text = body(lines, a, b)
        if text.endswith(":") or PSEUDO_HEADING.match(text):  # belongs with the next block
            carry = a
            continue
        units.append(Unit(len(units), "block", None, "", "", text))
    if carry is not None:
        units.append(Unit(len(units), "block", None, "", "", body(lines, carry, len(lines))))
    return units


def split(text: str) -> list[Unit]:
    text = clean(text)
    lines = text.split("\n")
    tokens = MD.parse(text)
    hs = headings(tokens)
    levels, title_line = split_levels(hs)
    if levels:
        return section_units(lines, hs, levels, title_line)
    return block_units(tokens, lines, title_line)


def is_toc(heading: str, text: str) -> bool:
    lines = [l for l in text.split("\n") if l.strip()]
    anchors = sum(bool(ANCHOR_ITEM.match(l)) for l in lines)
    return bool(TOC_HEADING.match(heading.strip())) or (anchors >= 3 and anchors >= 0.8 * len(lines))


def features(heading: str, text: str) -> dict:
    prose = FENCE.sub(" ", text)
    words, prose_words = len(WORD.findall(text)), len(WORD.findall(prose))
    return {
        "toc": is_toc(heading, text),
        "words": words,
        "prose_words": prose_words,
        "has_code": bool(FENCE.search(text) or "`" in text),
        "code_only": prose_words < 5 and words > prose_words,
        "list_items": len(re.findall(r"^\s*(?:[-*+]|\d+[.)])\s", text, re.M)),
        "long": words > LONG_WORDS,
    }


def build() -> pd.DataFrame:
    rows = []
    for folder in sorted(CORPUS.iterdir()):
        meta = json.loads((folder / "meta.json").read_text())
        for doc in DOCS:
            for u in split((folder / meta[doc]["file"]).read_text()):
                rows.append({
                    "unit_id": f"{meta['repo']}::{doc}::{u.n}",
                    "repo": meta["repo"], "tool": meta["tool"], "doc": doc,
                    **asdict(u), **features(u.heading, u.text),
                })
    return pd.DataFrame(rows)


def main() -> None:
    units = build()
    units.to_csv(PROCESSED / "units.csv", index=False)
    print(f"{len(units)} units from {units.repo.nunique()} repos")
    print(units.groupby("doc").agg(units=("unit_id", "size"), median_words=("words", "median"),
                                   blocks=("kind", lambda k: (k == "block").sum()),
                                   preambles=("kind", lambda k: (k == "preamble").sum()),
                                   code_only=("code_only", "sum"), toc=("toc", "sum"),
                                   long=("long", "sum")).to_string())
    per_doc = units.groupby(["repo", "doc"]).size().unstack()
    missing = [(r, d) for r in per_doc.index for d in DOCS if pd.isna(per_doc.loc[r, d])]
    print(f"documents yielding no units: {len(missing)} {missing[:5]}")


if __name__ == "__main__":
    main()
