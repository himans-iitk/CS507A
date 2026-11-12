# Inter-rater reliability (pass 1 vs blind pass 2, different coders)

Units re-coded: **338 / 338** in 40 repos. 95% CIs: repo bootstrap, 1000 draws.

| Measure | Value |
|---|---|
| Coverage, % agreement | 34.3% |
| Coverage, Cohen's κ (4 labels) | 0.00 [0.00, 0.01] |
| Coverage, linearly weighted κ (agent-only < partial < shared) | 0.00 [0.00, 0.01] |
| Categories, mean Jaccard per unit | 0.26 [0.23, 0.30] |
| D1 newcomer need, κ | nan |

## Coverage confusion (rows: pass 1, columns: pass 2)

| coverage_1     |   agent_only |   shared |
|:---------------|-------------:|---------:|
| agent_directed |           23 |        1 |
| agent_only     |          116 |        0 |
| partial        |          156 |        1 |
| shared         |           41 |        0 |

## Per-category κ

| Category | κ | units (pass 1) |
|---|---|---|
| System Overview | 0.00 | 24 |
| AI Integration | 0.08 | 41 |
| Documentation and References | 0.10 | 30 |
| Architecture | 0.07 | 66 |
| Implementation Details | 0.06 | 58 |
| Build and Run | 0.23 | 47 |
| Testing | 0.63 | 77 |
| Configuration and Environment | 0.24 | 30 |
| DevOps | 0.00 | 7 |
| Project Management | 0.00 | 5 |
| Development Process | 0.12 | 63 |
| Performance | 0.00 | 7 |
| Security | 0.23 | 9 |
| UI/UX | 0.11 | 5 |
| Maintainability | 0.00 | 2 |
| Debugging | 0.06 | 19 |

Interpretation (Landis & Koch): 0.61–0.80 substantial, > 0.80 almost perfect. Pass 1 and pass 2 were done by different coders, so this is inter-rater agreement.
