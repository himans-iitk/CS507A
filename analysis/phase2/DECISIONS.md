# Phase 2 — Sampling and collection decisions

Code: `src/gapstudy/{snapshot,screen,filters,sample,fetch}.py`. Outputs: `data/processed/`.

## Pipeline

1. `python -m gapstudy.screen` — for all 2,303 agent files: repo status, snapshot commit,
   README/CONTRIBUTING at that commit → `screen.csv`.
2. `python -m gapstudy.sample` — content flags, exclusions in a fixed order, stratified draw
   → `candidates.csv`, `sampling_flow.csv`, `sample.csv`.
3. `python -m gapstudy.fetch` — the three documents at the snapshot commit → `corpus/`,
   `corpus_manifest.csv`.

All GitHub responses are cached under `data/cache/github/`; re-running is free and deterministic.

## Snapshot commit

The package stores a blob SHA, not a commit (see `analysis/phase1/FINDINGS.md`). The snapshot
commit is the newest commit in the agent file's history at which the file has that blob: package
history first, then the API's `commits?path=` list (up to 20 candidates each). README and
CONTRIBUTING are taken from the same commit's tree, so all three documents are mutually
consistent: the human docs as they stood when this version of the agent file was committed.

## Locating README and CONTRIBUTING

GitHub's own lookup order: `.github/`, then the repo root, then `docs/`. Case-insensitive names
with extension `.md`, `.markdown`, `.rst`, `.txt`, `.adoc` or none. `CONTRIBUTORS*` does not match.
Format is recorded; non-Markdown files are kept and handled in Phase 3.

## Exclusions (applied in this order; each file counted once, at its first failing rule)

| # | Rule | Rationale |
|---|---|---|
| 1 | Repo no longer exists | cannot fetch human docs |
| 2 | Fork | duplicates its upstream |
| 3 | Archived | no longer onboards contributors |
| 4 | Snapshot commit not found | cannot guarantee same-commit comparison |
| 5 | Agent file is a symlink | its content is just the target path (e.g. `CLAUDE.md → AGENTS.md`) |
| 6 | Agent file only links elsewhere | ≤ 15 substantive words and a pointer (`@AGENTS.md`, "See X.md") — proposal: "agent files that only link to external content" |
| 7 | Agent file not in English | `langdetect`, as in [1] |
| 8 | Copy of another repo's agent file | TF-IDF (1–3-grams) cosine ≥ 0.9 with a file in another repo; the most-starred file of each cluster is kept |
| 9 | No README at snapshot | nothing to compare against |
| 10 | No CONTRIBUTING at snapshot | proposal's inclusion criterion |

Fork/archived status is today's, not the snapshot's — a stated limitation.

**Deviation from the proposal — `/init` files are flagged, not excluded.** The proposal set aside
"unedited tool-generated boilerplate". Rule 8 removes true boilerplate (text copied across repos).
Files from Claude Code's `/init` start with a fixed header but the body is generated from that
repository's code, and a single-commit history does not show whether the maintainer edited it
before committing. These files are kept with `init_unedited = True` (`/init` header and only one
commit) and analysed in a sensitivity check (RQ1 with and without them).

## Sample design

- **Stratified by agent, equal allocation:** 67 files per agent (201 total), so that per-agent
  comparisons (χ²/GEE in Phase 7) have equal power. Population-level estimates are reweighted by
  each agent's share of the eligible frame (`sampling_flow.csv`, last row).
- **One file per repo.** 347 repos have several agent files; drawing proceeds round-robin across
  agents, and a repo drawn for one agent is skipped by the others. This keeps observations
  independent and stops multi-tool repos from being over-represented.
- **Seed 507.** Every eligible file receives a rank within its agent; files beyond rank 67 are
  the ordered reserve list. If a sampled file has to be dropped during coding (e.g. it turns out
  to be generated), replace it with the next reserve of the same agent and log it.

## Results (seed 507, run 2026-10-25)

Sampling flow (`data/processed/sampling_flow.csv`):

| Step | CLAUDE.md | AGENTS.md | Copilot | Total |
|---|---|---|---|---|
| All agent files in package | 922 | 694 | 687 | 2,303 |
| − repo no longer exists | 891 | 672 | 675 | 2,238 |
| − fork | 878 | 656 | 666 | 2,200 |
| − archived | 846 | 638 | 639 | 2,123 |
| − snapshot commit not found | 816 | 603 | 629 | 2,048 |
| − agent file is a symlink | 761 | 588 | 616 | 1,965 |
| − agent file only links elsewhere | 738 | 583 | 604 | 1,925 |
| − agent file not in English | 714 | 567 | 588 | 1,869 |
| − copy of another repo's agent file | 710 | 555 | 570 | 1,835 |
| − no README at snapshot | 705 | 551 | 568 | 1,824 |
| − no CONTRIBUTING at snapshot | **252** | **214** | **289** | **755** |
| Sampled (one file per repo) | 67 | 67 | 67 | 201 |

- Requiring CONTRIBUTING is by far the largest cut (1,824 → 755). Eligible-frame shares for
  reweighting: Copilot 0.383, Claude 0.334, AGENTS 0.283.
- **Selection effect:** median stars in the sample is 445 vs 51–96 in the package. Projects with a
  CONTRIBUTING file are larger and more established; findings generalise to those, not to all
  repos with agent files. State this in threats to validity.
- Snapshot commits: 178 from package history, 23 from the API fallback; dates 2025-03-22 →
  2025-10-31 (so the package's content crawl ran later than its metadata crawl of ~2025-10-19).
- All 603 documents (201 × 3) match their git blob SHA. One agent file
  (`microsoft/FluidFramework`) is stored as UTF-16 and was converted to UTF-8; formats: 200 README
  `.md` + 1 `.txt`, 201 CONTRIBUTING `.md`.
- 12 sampled files are `init_unedited` (all CLAUDE.md) — the sensitivity subset.
- Duplicate rule check: the 34 files it dropped are tool-installed rule packs (e.g. Pipelex,
  Ultracite) and mirrored projects (`kubefleet-dev/kubefleet` ↔ `Azure/fleet`), as intended.

**Carry into Phase 4 — stub CONTRIBUTING files.** 13 sampled repos have a CONTRIBUTING file under
50 words (e.g. `dagster-io/dagster`, `PrefectHQ/prefect`, `dotnet/core`, `jdx/mise` with 1 word);
these usually point to a docs website. Their human docs live elsewhere, so they would inflate the
agent-only rate. Keep them in the sample, flag them, and report RQ1 with and without them —
together with the `docs/` sensitivity check (plan step 17).

## Unit of analysis (step 10)

Knowledge units (H2/H3 sections) are nested in repos, so they are not independent observations;
the ±7 pp precision in the proposal holds for 200 independent repos, not for units.

- **Primary RQ1 estimate — repo level.** For each repo, the share of its agent-file units that are
  agent-only; report the (weighted) mean across repos with a 95% CI from a bootstrap that
  resamples repos. With n ≈ 200 repos the ±7 pp figure applies to this estimate.
- **Unit-level comparisons (categories, agents) — clustered models.** Logistic GEE
  (`statsmodels`, exchangeable correlation, clusters = repos) for agent-only ~ category + agent,
  reporting odds ratios with cluster-robust CIs. A plain χ² on unit counts is reported only as
  descriptive, since it ignores clustering and overstates significance.
- **Reliability (κ)** is computed on units, but the 20% overlap is drawn as whole repos,
  stratified by agent.
