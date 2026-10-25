"""Split a unit's text into items: list entries, sentences and code blocks.

Items let a matcher judge a checklist rule by rule (partial coverage) and keep
inputs short enough for embedding models with 256-512 token limits.
"""

from __future__ import annotations

import re

FENCE = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.S | re.M)
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(\[[ xX]\]\s+)?")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z`*_(\[])")
HEADING = re.compile(r"^#{1,6}\s+")
WORD = re.compile(r"\w+")
MIN_WORDS = 3


def split_items(text: str) -> list[str]:
    items: list[str] = []
    pos = 0
    for m in FENCE.finditer(text):
        items += prose_items(text[pos:m.start()])
        items.append(m.group().strip())  # a code block is one item: the command and its purpose
        pos = m.end()
    items += prose_items(text[pos:])
    kept = [i for i in items if len(WORD.findall(i)) >= MIN_WORDS]
    return kept or ([text.strip()] if text.strip() else [])


def prose_items(text: str) -> list[str]:
    out, para = [], []

    def flush():
        if para:
            out.extend(s.strip() for s in SENTENCE_END.split(" ".join(para)) if s.strip())
            para.clear()

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or HEADING.match(stripped) or set(stripped) <= set("|-: "):
            flush()
            continue
        if LIST_ITEM.match(line):
            flush()
            out.append(LIST_ITEM.sub("", line).strip())
        elif out and not para and line.startswith(("  ", "\t")):
            out[-1] += " " + stripped  # continuation of the previous list item
        else:
            para.append(stripped)
    flush()
    return out
