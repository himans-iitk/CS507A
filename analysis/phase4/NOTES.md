# Phase 4 — Codebook, labelling tool and coding plan

Code: `src/gapstudy/{assign,labels,prelabel,docs_extra}.py`, `src/gapstudy/labeltool/`.
Tests: `tests/test_labeltool.py`, `tests/test_prelabel.py`. How to code: `coding/README.md`.

## Decisions (2026-10-25)

- **Cap: 10 agent units per repo** (seeded random subset of codable units; tables of contents
  excluded). 1,564 units; 93 repos coded in full. Each unit carries
  `weight = codable units / coded units` for repo-level estimates.
- **Sets, stratified by agent:** pilot 20 repos (161 units; 7/7/6) — also the detector's dev set;
  reliability 40 repos (338 units; 13/13/14); main 141 repos (1,065 units).
- **Reliability: intra-rater.** No second coder; the reliability set is re-coded blind ≥ 14 days
  after the first pass (the tool enforces the delay, shuffles the order with a fixed seed, and
  never shows pass-1 labels in pass 2). Report as a limitation.
- **LLM: open-source, model not yet chosen.** Used only for category suggestions (dimension A),
  through any OpenAI-compatible endpoint; never for coverage (the RQ3 gold standard).
- **No similarity-ranked suggestions in the tool.** The human docs are shown in document order with
  keyword search, so the gold labels are not anchored on the embedding detector being evaluated.
- **Deadline assumed: end of November** (proposal timeline).

## Codebook v0.1-pilot (`coding/CODEBOOK.md`)

- **A. Categories:** the 16 of Chatlatanagulchai et al., with their decision rules.
- **C. Coverage:** agent-only / partially covered / shared, plus **agent-directed (n/a)** for
  units that only address the AI (persona, response style). Those are excluded from RQ1
  denominators. Without this option they would inflate the agent-only rate. Flags: `conflict`
  (human docs contradict the unit — possible staleness), `links_out`, `unclear`. Evidence: the
  covering human sections are ticked, giving gold matches for RQ3.
- **D. Newcomer relevance (agent-only and partial only):** D1 need = one of Dagenais et al.'s 18
  landscape features (verified from the paper's Table 2); D2 barriers = the 10
  documentation-addressable barriers of Steinmacher et al.'s model.
- **B. Human-doc categories** (Prana et al.) dropped from manual coding: no RQ depends on them.

### Citation note for the paper

Steinmacher et al.'s 2015 review [6] could not be retrieved (publisher paywall; author server
down). The barrier names in D2 come from their later 58-barrier model as tabulated in Santos et
al. (2024, arXiv:2408.15989, Table 10, co-authored by Steinmacher). Cite the model paper as
well as [6], and check the names against it when you have library access.

## Sensitivity inputs

| Flag | Count | Used for |
|---|---|---|
| `stub_contributing` (< 50 words) | 13 repos | RQ1 with/without |
| `init_unedited` | 12 repos (all CLAUDE.md) | RQ1 with/without |
| docs/ Markdown present | 113 / 201 repos (median 20 files) | — |
| docs/ fetched (seeded subsample) | 30 repos, 525 files | RQ1 with docs/ as human documentation |

More than half the repos keep developer docs under `docs/`, so the README+CONTRIBUTING scope is a
real limitation. The subsample measures how much it matters.
