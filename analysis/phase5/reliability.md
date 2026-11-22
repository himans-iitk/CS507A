# Human–LLM agreement (pass 1 vs blind pass 2)

Units re-coded: **338 / 338** in 40 repos. 95% CIs: repo bootstrap, 1000 draws.

| Measure | Value |
|---|---|
| Coverage, % agreement | 86.1% |
| Coverage, Cohen's κ (4 labels) | 0.78 [0.71, 0.85] |
| Coverage, linearly weighted κ (agent-only < partial < shared) | 0.80 [0.73, 0.86] |
| Categories, mean Jaccard per unit | 0.53 [0.50, 0.57] |
| D1 newcomer need, κ | n/a (pass 1 coded no needs on this set) |

## Coverage confusion (rows: pass 1, columns: pass 2)

| coverage_1     |   agent_directed |   agent_only |   partial |   shared |
|:---------------|-----------------:|-------------:|----------:|---------:|
| agent_directed |               22 |            0 |         1 |        1 |
| agent_only     |                2 |           92 |        22 |        0 |
| partial        |                1 |            7 |       145 |        4 |
| shared         |                1 |            1 |         7 |       32 |

## Per-category κ

| Category | κ | units (pass 1) |
|---|---|---|
| System Overview | 0.90 | 24 |
| AI Integration | 0.64 | 41 |
| Documentation and References | 0.41 | 30 |
| Architecture | 0.81 | 66 |
| Implementation Details | 0.40 | 58 |
| Build and Run | 0.61 | 47 |
| Testing | 0.68 | 77 |
| Configuration and Environment | 0.39 | 30 |
| DevOps | 0.37 | 7 |
| Project Management | 0.61 | 5 |
| Development Process | 0.66 | 63 |
| Performance | 0.50 | 7 |
| Security | 0.42 | 9 |
| UI/UX | 0.32 | 5 |
| Maintainability | 0.12 | 2 |
| Debugging | 0.68 | 19 |

## By agent

| Agent | Units | Agreement | κ |
|---|---|---|---|
| agents | 92 | 87.0% | 0.75 |
| claude | 116 | 89.7% | 0.85 |
| copilot-instructions | 130 | 82.3% | 0.71 |

## By repository

Agreement per repository: median 90%, mean 86%; 15 of 40 repositories agree on every unit, 32 on at least 80%, 1 below 60%.

Lowest agreement:

| repo                            | tool                 |   units |   agreement |
|:--------------------------------|:---------------------|--------:|------------:|
| zwave-js/zwave-js               | copilot-instructions |       6 |        0.33 |
| microsoft/autogen               | copilot-instructions |      10 |        0.6  |
| julep-ai/julep                  | agents               |      10 |        0.6  |
| Teri-anric/AnimeStarsExtensions | agents               |       3 |        0.67 |
| ferrisdb/ferrisdb               | claude               |      10 |        0.7  |

Interpretation (Landis & Koch): 0.61–0.80 substantial, > 0.80 almost perfect. Pass 1 coder(s): Himanshu Mishra; pass 2 coder(s): Codex (AI reviewer), so this is human-llm agreement.
