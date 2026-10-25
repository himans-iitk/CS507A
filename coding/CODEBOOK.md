# Codebook (v0.1-pilot)

One record per **agent-file unit** in `coding/queue.csv`. The labelling tool reads the same
definitions from `codebook.json`; keep both in sync and bump the version after the pilot.

## A. Instruction category (multi-label)

The 16 categories of Chatlatanagulchai et al. (2026), Table 3. Pick **every** category the unit
contains. If the tool shows LLM pre-labels, treat them as suggestions and correct them.

Decision rules carried over from that paper:
- **Documentation and References** is for documentation artifacts or pointers to other docs;
  documentation-related *coding conventions* (e.g. "write JSDoc for public functions") are
  **Implementation Details**.
- **Development Process** is Git and review practice; build/test commands are **Build and Run** /
  **Testing** even when they appear in a "before you commit" checklist (pick all that apply).
- **AI Integration** covers instructions about the agent itself (role, behaviour, tools); it does
  not by itself make a unit agent-directed (see C4).

## C. Coverage in the human docs (single choice) — the RQ1 label

Compare the unit with the **README and CONTRIBUTING at the snapshot commit only**. Judge
*knowledge*, not wording: paraphrases count; a link to somewhere else does not.

| Key | Label | Use when |
|---|---|---|
| 1 | **Agent-only** | None of the unit's knowledge is in either human doc. Mentioning the same *topic* without any of the unit's specifics is still agent-only. |
| 2 | **Partially covered** | Some of the unit's facts/rules are present but not all (typical for checklists), **or** the human doc covers it less specifically (e.g. "run the tests" vs `make test-unit -race`). |
| 3 | **Shared** | Every actionable fact, command or rule in the unit is in the human docs, possibly in other words or spread over several sections. |
| 4 | **Agent-directed (n/a)** | The unit only concerns the AI agent: persona ("You are an expert…"), response style ("be concise"), agent tooling or prompt mechanics. It carries nothing a human contributor would need. Excluded from RQ1 denominators. |

Rules of thumb:
- **Mixed units:** if a unit mixes agent-directed sentences with project knowledge, ignore the
  agent-directed part and label the project knowledge with 1–3.
- **Evidence:** for 2 and 3, tick the human-doc section(s) that cover it. These are the gold
  matches for the RQ3 detector — tick all that apply, not just the first one you find.
- **Code-only units** (a command block): the knowledge is the command and its purpose.
- **Overviews / preambles:** compare with the README's description of the project; shared if the
  same facts are there.
- **Generic advice** with no project-specific content ("write clean code", "add tests"): code
  normally — usually *shared* if CONTRIBUTING says the same, otherwise agent-only — but note
  `generic` in the notes field so it can be separated in the analysis.

Flags (any number):
- `conflict` — the human docs contradict the unit (different command, rule or version). Still
  choose 1–3 for coverage; conflicts are reported separately as possible staleness.
- `links_out` — the human docs only point elsewhere for this topic (website, wiki, other file).
  Coverage stays 1 or 2; the flag drives the sensitivity analysis.
- `unclear` — hard to judge; revisit after the pilot.

## D. Newcomer relevance — only for agent-only and partially covered units (RQ2)

**D1. Newcomer need (single choice):** which landscape feature of Dagenais et al. (2010, Table 2)
the knowledge belongs to — Product (Software Architecture; Low-level Design & Runtime Behavior;
Design & Implementation Rationale; Product/Domain; Technologies Used), Processes and Practices
(Development Process; Task Process; Development Environment and Tools; Software Configuration
Management), Team (Roles and Expertise; Formal Meetings; Communication Strategies;
Assistance/Mentoring Culture), Documentation (Developer-Oriented Documentation; Learning
Material; Repository, Indexes, and Search), Context (Organization; Inter-Team Organization).

**D2. Barrier mitigated (multi, may be empty):** which of Steinmacher et al.'s barriers this
knowledge would reduce if it were in the human docs. Only the barriers documentation can address
are listed: *Newcomers' orientation* (finding a task to start with; finding the correct artifacts
to fix an issue; poor "how to contribute" available; not knowing the contribution flow),
*Newcomers' characteristics* (lack of domain expertise; lack of knowledge in project process and
practices; lack of technical background), *Technical hurdles* (local environment setup hurdles;
code/architecture hurdles; understanding flow of information).

Sources: the barrier names come from the 58-barrier model of Steinmacher et al., as tabulated in
Santos et al. (2024, arXiv:2408.15989, Table 10). The proposal cites only the 2015 review [6]; add
the model's own citation (Steinmacher et al., ICSE 2016 / CSCW 2018) to the paper.

## B. Human-document categories (optional)

The proposal also classifies README/CONTRIBUTING units with Prana et al.'s README categories.
This does not feed any RQ directly, so it is **not** part of manual coding; if needed for a
descriptive table it can be LLM-labelled and spot-checked later.

## Protocol

1. **Pilot (20 repos, 161 units):** code, write down every hard case in the notes field, refine
   these rules, bump the version to 1.0, then **re-check the pilot units against v1.0**.
2. **Reliability set (40 repos, 338 units):** code right after the pilot so the 14-day clock for
   the blind re-code starts early.
3. **Main set (141 repos, 1,065 units).**
4. **Re-code (pass 2):** the tool shows only reliability units whose pass-1 label is ≥ 14 days
   old, in shuffled order, with pass-1 labels hidden. Report Cohen's κ (coverage, weighted for the
   ordinal 1–3 scale) and per-category κ.
