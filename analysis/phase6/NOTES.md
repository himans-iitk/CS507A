# Phase 6 — Gap detector (RQ3)

Code: `src/gapstudy/detector/` (`items`, `matchers`, `score`, `llm_judge`, `evaluate`, `gapcheck`).
Tests: `tests/test_detector.py`. Jobs: `scripts/detector/embed.sbatch`, `scripts/llm/judge.sbatch`.

## Pipeline

1. **Items.** Each unit is split into list entries, sentences and code blocks (35,628 items:
   12,896 agent, 22,732 human). A checklist is judged rule by rule, and inputs stay within the
   256–512-token limits of embedding models.
2. **Scores** (`gapstudy.detector.score`, no labels used). For every agent unit, against its own
   repo's README and CONTRIBUTING sections:
   - `unit_max`: best whole-unit to whole-section cosine;
   - `item_mean`: mean over the unit's items of each item's best human-item match;
   - `item_max`: per-item best matches, so `item_cov@τ` (share of items matched at ≥ τ) can be tuned;
   - `top`: the 5 best human sections (evidence ranking; LLM candidates).
3. **Matchers.**

   | Matcher | Kind | Revision |
   |---|---|---|
   | `tfidf` | word 1–2-gram TF-IDF, IDF over the whole corpus | — |
   | `sentence-transformers/all-MiniLM-L6-v2` | 23M embedding | `1110a243` |
   | `BAAI/bge-base-en-v1.5` | 109M embedding | `a5beb1e3` |
   | `Qwen/Qwen3-Embedding-0.6B` | 596M embedding (no query instruction: the task is symmetric) | `97b0c614` |
   | + `Qwen3-Coder-30B-A3B-Instruct` | LLM judge on the top-5 candidates | `b2cff646` |

4. **Evaluation** (`gapstudy.detector.evaluate`). Dev = the 20 pilot repos; test = the other 181.
   Agent-directed units are excluded. On dev only: choose the score variant, the binary threshold
   (agent-only if score < t; midpoint of the tied-optimal range), the two 3-class thresholds,
   and the LLM band width. On test: precision / recall / F1 for agent-only, ROC-AUC, 3-class
   macro-F1, evidence hit@1/@5, with repo-bootstrap CIs; error analysis of the worst false
   positives and negatives. The best matcher on dev is saved to `detector/config.json`.
5. **LLM stage.** *Alone*: the LLM labels every unit from its top-5 candidates. *Borderline*: the
   LLM decides only where the matcher's score lies within ±w of a threshold (w tuned on dev). The
   LLM only sees the matcher's top 5, so a covering section ranked lower is invisible to it
   (report hit@5 alongside).
6. **`gapcheck <repo>`** applies the chosen matcher and thresholds to any local checkout.

## Design decisions

- Gold labels come from the manual coding only; the tool never showed similarity rankings, so the
  labels are not anchored on any matcher.
- Thresholds are tuned per matcher on dev and never on test; the test set is used once.
- `gapcheck` with TF-IDF refits IDF on the single repository, so its scores differ in scale from the
  study's; prefer an embedding matcher in `config.json` for the released tool.

## Status (2026-10-25)

- TF-IDF scores: done (`data/processed/scores/tfidf.csv`, 2,661 agent units).
- Embedding scores: GPU job running (`logs/embed-473065.out`). Full-H100 nodes were reserved, so
  the job uses a 20 GB H100 slice.
- LLM judge: ready; needs the Qwen3-Coder weights (`scripts/llm/download_model.sh`, ~61 GB).
- Evaluation: waits for labels (pilot = dev; reliability + main = test).
