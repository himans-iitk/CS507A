# Phase 7 results

> **Provisional:** computed from unfrozen pass-1 labels; do not report.

No labels yet: RQ1, RQ2 and the sensitivity checks run once coding has started.

## Corpus: length and readability (all 201 repos, no labels needed)

Flesch Reading Ease (textstat) on prose with code removed; higher = easier. Documents with < 30 prose words are skipped.

| doc          |   median words |   median Flesch |
|:-------------|---------------:|----------------:|
| agent        |            608 |            28.5 |
| README       |            682 |            27.8 |
| CONTRIBUTING |            445 |            51   |

Within-repo comparisons (Wilcoxon signed-rank):

| metric   | comparison            |   repos |   median_difference |   agent_higher_share | p        |
|:---------|:----------------------|--------:|--------------------:|---------------------:|:---------|
| words    | agent vs README       |     201 |             -60     |                0.463 | 0.14     |
| words    | agent vs CONTRIBUTING |     201 |             101     |                0.567 | 0.008    |
| flesch   | agent vs README       |     191 |              -0.899 |                0.497 | 0.363    |
| flesch   | agent vs CONTRIBUTING |     189 |             -22.357 |                0.19  | < 0.0001 |

Agent-file Flesch median by agent: AGENTS.md 37.6, CLAUDE.md 18.6, copilot-instructions.md 28.1

