# Phase 7 — Analysis

Code: `src/gapstudy/analysis/` (`data`, `rq1`, `rq2`, `sensitivity`, `corpus`, `report`).
Tests: `tests/test_analysis.py` (synthetic labels with known rates). One command:

    python -m gapstudy.analysis.report        # → analysis/phase7/results.md + one CSV per table

It reads the frozen `coding/labels_v1.csv`; before the freeze it uses the current pass-1 labels
and marks everything provisional.

## Methods (as implemented)

**Unit of analysis.** Knowledge units = coded units labelled agent-only, partial or shared.
Agent-directed units are excluded from denominators and reported separately as a share of all
units.

**RQ1 headline.** For each repo, the share of its knowledge units that are agent-only (also
partial, shared, and agent-only-or-partial). The per-repo cap does not bias this, because all coded
units of a repo carry the same weight. Mean over repos per agent; overall = post-stratified to the
eligible frame (Copilot 289, CLAUDE.md 252, AGENTS.md 214 files → 38.3% / 33.4% / 28.3%), because
the sample has equal allocation (67 per agent). 95% CI: 1,000 bootstrap draws resampling repos
within each agent. A pooled unit-level share (cap-weighted) is reported alongside.

**RQ1 by category and agent.** Agent-only share among units containing each category (multi-label,
cap-weighted). Logistic GEE (statsmodels): agent-only ~ category dummies + agent (CLAUDE.md =
reference), clusters = repos, exchangeable working correlation, robust SEs, cap weights. Category
dummies are dropped if they have < 15 units, no outcome variation, or are perfectly collinear with
the columns already in the model; the report lists what was dropped. χ² (agent × coverage) is
reported as descriptive only, because it ignores clustering.

**RQ2.** Among agent-only and partial units: distribution of D1 needs (Dagenais et al. landscape
features, grouped as Product / Processes and Practices / Team / Documentation / Context) and of D2
barriers (Steinmacher et al., multi-label), cap-weighted, plus needs by agent. Example excerpts
(≤ 60 words, agent-only, seeded) for the five most frequent needs.

**Sensitivity.** Headline recomputed without unedited `/init` files (12 repos), without stub
CONTRIBUTING files (13 repos), and without units flagged `links_out`. The docs/ check re-scores
the agent-only units of the 30-repo docs/ subsample against README + CONTRIBUTING + docs/*.md with
the tuned detector and counts those whose best match is a docs/ section. It needs
`detector/config.json` and is an automatic estimate, since manual coding used README and
CONTRIBUTING only. `conflict` flags are counted as evidence of possibly stale human docs.

## Result available now (no labels needed): length and readability

All 201 repos; Flesch Reading Ease via textstat (as in the Agent READMEs paper) on prose with code
removed.

| Document | Median words | Median Flesch |
|---|---|---|
| Agent file | 608 | 28.5 |
| README | 682 | 27.8 |
| CONTRIBUTING | 445 | 51.0 |

- Agent files are as hard to read as READMEs (median within-repo difference −0.9, p = 0.36) and
  much harder than CONTRIBUTING (−22.4 points; harder in 81% of repos; Wilcoxon p < 0.0001).
- Agent files are longer than CONTRIBUTING (+101 words median, p = 0.008) and similar to README.
- By agent: CLAUDE.md 18.6, Copilot 28.1, AGENTS.md 37.6. The CLAUDE.md figure is close to the
  Agent READMEs paper's 16.6, which supports comparability.

This bears on the motivation: knowledge that exists only in agent files is also written in a
harder register than the CONTRIBUTING files a newcomer would read.

## Matcher agreement (input to RQ3)

All four matchers have scored the 2,661 agent units (`data/processed/scores/`). Spearman
correlations of `item_mean` between matchers are 0.78–0.91, so the matcher choice matters and
the RQ3 evaluation decides it.
