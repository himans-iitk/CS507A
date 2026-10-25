# Phase 3 — Splitting documents into knowledge units

Code: `src/gapstudy/units.py` (tests: `tests/test_units.py`). Output: `data/processed/units.csv`.

    python -m gapstudy.units

## Splitting rule

Parsed with `markdown-it-py` (CommonMark + tables), so `#` lines inside code fences, headings
nested in lists/blockquotes, and setext (underlined) headings are handled correctly.

- **Title:** a single top-level heading at the start of the document is its title, not a section.
- **Section levels:** H2 and H3, as in the proposal; plus H1 when the document uses several H1s
  as sections (8 agent files); documents whose headings start at H3 or deeper use their top two
  levels. H4+ stay inside their section. *Pilot change:* a first version used "top level + next",
  which folded H3s into H2s in multi-H1 files (e.g. `Azure/azure-rest-api-specs` produced a
  2,000-word unit).
- **Preamble:** text before the first section heading (excluding the title) is its own unit.
- **Empty headings:** a heading whose content is entirely in its subsections is not a unit; its
  title survives in the children's `heading_path` (e.g. `Commands > Build`).
- **No section headings** (22 agent files, 24 CONTRIBUTING, 8 README): split into top-level blocks
  (paragraph, list, code, table). A lead-in ending in `:` or a lone bold line (`**Guardrails**`)
  is merged with the block that follows.
- **Cleaning:** BOM, CRLF, YAML front matter (Copilot `applyTo:`) and HTML comments are removed,
  except comments inside code fences, which are content.

## Fields per unit

`unit_id` (`owner/repo::doc::n`, stable), `repo`, `tool`, `doc` (agent/README/CONTRIBUTING), `n`,
`kind` (section/preamble/block), `level`, `heading`, `heading_path`, `text`, and flags:
`words`, `prose_words` (outside code fences), `has_code`, `code_only` (< 5 prose words),
`list_items`, `long` (> 300 words), `toc`.

**`toc`** marks tables of contents (heading "Table of Contents"/"Contents", or ≥ 80% of lines are
anchor links `[x](#y)`). They are navigation, not knowledge: excluded from coding and from
denominators.

## Result

| Document | Units | Codable (not TOC) | Median words | Code-only | > 300 words |
|---|---|---|---|---|---|
| Agent file | 2,664 | 2,661 | 39 | 246 | 34 |
| README | 2,594 | 2,578 | 52 | 130 | 133 |
| CONTRIBUTING | 1,862 | 1,849 | 44 | 71 | 69 |

Agent units per repo: median 11, p90 26, max 45, min 1.
By agent: CLAUDE.md 1,078 units (median 36 words), AGENTS.md 725 (42), Copilot 858 (40).

One README (`ssilve1989/ulti-project`) is an empty file at the snapshot commit, so it yields no
units; the repo stays in the sample with CONTRIBUTING as its only human document.

## Pilot (15 repos, 5 per agent, 210 agent units) — granularity decision

Sections are mostly coherent single topics (median 36 words, 75th percentile 57). The exceptions
are checklists and rule lists that bundle several independent rules under one heading (e.g.
`valkey-io/valkey-glide` "Quality Gates": build, lint, tests, DCO sign-off, commit format, …);
12.5% of agent units have ≥ 8 list items.

**Decision: the section stays the coding unit; no bullet-level split for coding.** A section
whose rules are only partly in the human docs is labelled *partially covered* — that is what the
label is for. Splitting at bullets would roughly triple the coding load and turn many headings
and lead-ins into fragments. For the gap detector (Phase 6) the matcher may still compare at
sentence/bullet level inside a unit (max similarity over items) — that is a modelling choice and
does not change the labels.

## Coding load (input to Phase 4)

2,661 codable agent units. With the proposed cap of 10 randomly chosen units per repo:
**1,564 units**, 93 repos coded completely (cap 12: 1,772 units, 108 repos). The cap and its
weighting are set in Phase 4.
