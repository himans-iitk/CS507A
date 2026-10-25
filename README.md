# What We Tell the Agent but Not the Newcomer

Mining agent context files (`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`) for
knowledge that is missing from a project's human onboarding documentation (README, CONTRIBUTING).
Course project for CS507A, University of British Columbia.

- **RQ1** What knowledge captured in agent context files is absent from the same repository's README and CONTRIBUTING?
- **RQ2** Which newcomer needs and barriers does this agent-only knowledge address?
- **RQ3** How reliably can agent-only knowledge be identified automatically?

**Status.** Data collection, unit splitting, the coding tool, the gap detector and all analyses are
implemented and tested. Manual coding is in progress. RQ1–RQ3 results will appear once the labels
are frozen. The paper draft is in [`paper/`](paper/); results print as **[TBD]** until then.

## What is in this repository

| Path | Contents |
|---|---|
| `src/gapstudy/` | The pipeline (Python package) |
| `data/processed/` | Screening results, sampling flow, the sample, the three documents per sampled repo (`corpus/`), knowledge units, detector scores |
| `coding/` | Codebook, coding queue and assignments, labels (`labels/*.jsonl`, frozen `labels_v1.csv`), [how to code](coding/README.md) |
| `analysis/phaseN/` | Decisions, notes and results per phase |
| `paper/` | LaTeX paper (ACM sigconf); every number is generated into `numbers.tex` |
| `scripts/` | Slurm jobs for embeddings and the open-source LLM |
| `tests/` | `pytest` suite |

## Pipeline

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install -e .
cp .env.example .env          # add a GitHub token (read-only public access is enough)

# Phase 1-2: source data, screening, sampling, collection
git clone https://github.com/woraamy/Agent-Context-File-Analysis data/raw/agent_context_pkg
.venv/bin/python analysis/phase1/audit_package.py
.venv/bin/python -m gapstudy.screen          # all 2,303 agent files (cached GitHub API)
.venv/bin/python -m gapstudy.sample          # exclusions + stratified sample (seed 507)
.venv/bin/python -m gapstudy.fetch           # agent file, README, CONTRIBUTING at the snapshot commit
.venv/bin/python -m gapstudy.docs_extra      # docs/ inventory and subsample

# Phase 3-5: units, coding, reliability
.venv/bin/python -m gapstudy.units
.venv/bin/python -m gapstudy.assign          # coding queue (do not re-run once coding has started)
.venv/bin/python -m gapstudy.labeltool.app   # local coding tool
.venv/bin/python -m gapstudy.reliability
.venv/bin/python -m gapstudy.freeze          # → coding/labels_v1.csv (+ sha256)

# Phase 6: gap detector (RQ3)
.venv/bin/python -m gapstudy.detector.score --matcher tfidf
sbatch scripts/detector/embed.sbatch         # embedding matchers on a GPU
sbatch --export=ALL,SCORES=data/processed/scores/<matcher>.csv scripts/llm/judge.sbatch
.venv/bin/python -m gapstudy.detector.evaluate

# Phase 7-8: analysis and paper
.venv/bin/python -m gapstudy.analysis.report
.venv/bin/python -m gapstudy.paper_numbers && (cd paper && latexmk -pdf main.tex)
```

Every step is deterministic (fixed seeds, pinned model revisions, cached API responses) and the
tests run with `.venv/bin/pytest`. Notes for the Digital Research Alliance (Compute Canada)
clusters: `pyarrow` and `opencv` come from modules, not pip, so see `scripts/llm/setup_vllm.sh`.

## gapcheck

```bash
gapcheck path/to/your/repo
```

Lists the sections of your agent context files that your README and CONTRIBUTING do not cover,
using the matcher and thresholds tuned in this study (`detector/config.json`, written by
`gapstudy.detector.evaluate`).

## Data and licensing

- **Code:** MIT (see `LICENSE`).
- **Labels, codebook, units metadata:** CC BY 4.0.
- **Documents under `data/processed/corpus/`** are copies of files from public GitHub repositories
  and remain under their owners' licenses. They are included so the study can be reproduced. Each
  is identified by repository, commit and blob SHA, so it can also be re-fetched with
  `gapstudy.fetch` instead of being redistributed. See `RELEASE.md`.
- Source dataset: the replication package of Chatlatanagulchai et al., *Agent READMEs*
  (TOSEM 2026), <https://github.com/woraamy/Agent-Context-File-Analysis>.

## Citation

See `CITATION.cff`.
