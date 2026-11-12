# Phase 7 results

Coded units: 1564 in 201 repos; knowledge units (excluding agent-directed): 1423. Overall figures are post-stratified to the eligible frame (copilot-instructions.md 38.3%, CLAUDE.md 33.4%, AGENTS.md 28.3%). 95% CIs: 1000 bootstrap draws resampling repos within each agent.

## RQ1 — How much agent-file knowledge is absent from README and CONTRIBUTING?

| Outcome (mean share per repo) | All (post-stratified) | CLAUDE.md | AGENTS.md | copilot-instructions.md |
|---|---|---|---|---|
| Agent-only | 41.8% [37.6%, 46.1%] | 40.0% [33.8%, 46.7%] | 33.4% [26.2%, 40.7%] | 49.5% [41.6%, 57.6%] |
| Partially covered | 43.5% [39.9%, 47.1%] | 45.0% [39.0%, 51.0%] | 52.0% [45.9%, 58.3%] | 35.9% [28.8%, 43.3%] |
| Shared | 14.7% [12.0%, 17.6%] | 15.0% [11.2%, 19.0%] | 14.6% [10.4%, 19.3%] | 14.6% [9.4%, 20.5%] |
| Agent-only or partial | 85.3% [82.4%, 88.0%] | 85.0% [81.0%, 88.8%] | 85.4% [80.7%, 89.6%] | 85.4% [79.5%, 90.6%] |
| Agent-directed (share of all units) | 9.1% [7.1%, 11.2%] | 8.6% [6.4%, 11.2%] | 9.4% [6.0%, 13.0%] | 9.3% [5.1%, 13.8%] |
| Repos | 197 | 66 | 66 | 65 |

Pooled over units (cap-weighted): agent-only 41.7%, partial 43.9%, shared 14.4%.

### By instruction category

| Category | Units | Repos | Agent-only | Agent-only or partial |
|---|---|---|---|---|
| UI/UX | 36 | 24 | 68.4% | 89.4% |
| Performance | 27 | 24 | 65.6% | 92.0% |
| Debugging | 57 | 43 | 61.7% | 87.6% |
| Documentation and References | 145 | 89 | 53.9% | 88.8% |
| Implementation Details | 331 | 161 | 51.5% | 90.6% |
| AI Integration | 55 | 43 | 47.8% | 83.1% |
| DevOps | 53 | 38 | 46.3% | 85.5% |
| Architecture | 310 | 146 | 41.7% | 92.9% |
| Project Management | 18 | 13 | 41.3% | 68.8% |
| Configuration and Environment | 175 | 104 | 39.9% | 87.2% |
| Build and Run | 249 | 143 | 38.7% | 88.4% |
| Maintainability | 24 | 20 | 38.0% | 100.0% |
| Testing | 354 | 163 | 36.7% | 89.7% |
| Development Process | 223 | 130 | 32.3% | 84.4% |
| Security | 41 | 34 | 30.8% | 79.2% |
| System Overview | 124 | 96 | 6.8% | 55.2% |

### Logistic GEE: agent-only ~ categories + agent (clustered by repo)

n = 1423 units in 197 repos; exchangeable working correlation; robust SEs. Dropped (too rare or no variation): none.

| Term | Odds ratio [95% CI] | p |
|---|---|---|
| AGENTS.md (vs CLAUDE.md) | 0.90 [0.53, 1.50] | 0.677 |
| copilot-instructions.md (vs CLAUDE.md) | 1.25 [0.74, 2.11] | 0.413 |
| Testing | 0.73 [0.53, 1.01] | 0.0604 |
| Implementation Details | 1.22 [0.89, 1.65] | 0.212 |
| Architecture | 0.81 [0.54, 1.20] | 0.298 |
| Build and Run | 0.71 [0.52, 0.97] | 0.0288 |
| Development Process | 0.50 [0.35, 0.73] | 0.000297 |
| Configuration and Environment | 0.66 [0.47, 0.93] | 0.0176 |
| Documentation and References | 0.98 [0.63, 1.54] | 0.941 |
| System Overview | 0.07 [0.03, 0.20] | 5.61e-07 |
| Debugging | 1.35 [0.75, 2.42] | 0.311 |
| AI Integration | 1.38 [0.88, 2.14] | 0.157 |
| DevOps | 1.12 [0.66, 1.92] | 0.667 |
| Security | 0.72 [0.33, 1.58] | 0.413 |
| UI/UX | 1.90 [0.70, 5.17] | 0.21 |
| Performance | 2.60 [0.81, 8.36] | 0.11 |
| Maintainability | 0.52 [0.23, 1.16] | 0.109 |
| Project Management | 1.38 [0.41, 4.59] | 0.601 |

Descriptive χ² (agent × coverage, units; ignores clustering): χ²(4) = 20.5, p = 0.000406.

## RQ2 — Which newcomer needs and barriers does this knowledge address?

Units coded agent-only or partially covered.

### Newcomer need (Dagenais et al. landscape features)

| Group | Need | Units | Repos | Share |
|---|---|---|---|---|
| Processes and Practices | Development Process | 278 | 120 | 27.2% |
| Processes and Practices | Development Environment and Tools | 237 | 117 | 26.6% |
| Product | Software Architecture | 121 | 89 | 12.0% |
| Processes and Practices | Task Process | 67 | 48 | 7.3% |
| Product | Low-level Design & Runtime Behavior | 62 | 45 | 6.9% |
| Product | Technologies Used | 47 | 36 | 4.8% |
| Product | Product/Domain | 29 | 23 | 3.6% |
| Documentation | Repository, Indexes, and Search | 31 | 27 | 3.0% |
| Processes and Practices | Software Configuration Management | 25 | 19 | 2.8% |
| Product | Design & Implementation Rationale | 14 | 12 | 2.1% |
| Documentation | Developer-Oriented Documentation | 21 | 20 | 1.7% |
| Documentation | Learning Material | 8 | 8 | 1.4% |
| Context | Organization | 1 | 1 | 0.3% |
| Team | Communication Strategies | 1 | 1 | 0.1% |
| Team | Roles and Expertise | 1 | 1 | 0.1% |

By group: Processes and Practices 64.0%; Product 29.4%; Documentation 6.2%; Context 0.3%; Team 0.2%

### Barriers mitigated (Steinmacher et al.; multi-label)

| Group | Barrier | Units | Repos | Share of gap units |
|---|---|---|---|---|
| Newcomers' characteristics | Lack of knowledge in project process and practices | 325 | 133 | 25.0% |
| — | (no barrier coded) | 273 | 39 | 23.1% |
| Technical hurdles | Local environment setup hurdles | 232 | 114 | 19.7% |
| Technical hurdles | Code/architecture hurdles | 176 | 96 | 14.0% |
| Newcomers' orientation | Finding the correct artifacts to fix an issue | 151 | 99 | 11.6% |
| Newcomers' characteristics | Lack of technical background | 72 | 49 | 6.1% |
| Newcomers' characteristics | Lack of domain expertise | 44 | 28 | 4.8% |
| Newcomers' orientation | Newcomers don't know what is the contribution flow | 61 | 49 | 4.6% |
| Newcomers' orientation | Poor “How to Contribute” available | 3 | 2 | 0.2% |
| Newcomers' orientation | Finding a task to start with | 4 | 3 | 0.2% |
| Technical hurdles | Understanding flow of information | 2 | 1 | 0.2% |

### Example agent-only knowledge (seeded sample, ≤ 60 words)

- **Development Process** — bancolombia/bc_golden_plugin (copilot-instructions.md), *🔧 Critical CI/CD Considerations > Device Consistency*:
  > ALWAYS use the same device configuration between local and CI: ```dart // Consistent device across environments device: GoldenDeviceData.galaxyS25  // Same locally and in CI ```
- **Development Process** — shopware/shopware (AGENTS.md), *Coding Guidelines*:
  > **MANDATORY**: All code must follow the guidelines in `coding-guidelines/`.
- **Development Environment and Tools** — netz98/n98-magerun2 (AGENTS.md), *Testing Information > Test Environment Setup*:
  > The tests require a Magento 2 installation to run properly. The test suite is configured to use the Magento installation specified by the `N98_MAGERUN2_TEST_MAGENTO_ROOT` environment variable.  1. **Set Up Magento**:    - Install a compatible version of Magento 2 (see README.md for supported versions)    - Configure the database and other required services  2. **Configure Test Environment**:    ``
- **Development Environment and Tools** — dagster-io/dagster (CLAUDE.md), *Make Command Guidelines*:
  > - Whenever there is an instruction to run a make command, ALWAYS cd to $DAGSTER_GIT_REPO_DIR, as the Makefile is at the root of the repository
- **Software Architecture** — netz98/n98-magerun2 (AGENTS.md), *Additional Development Information > Project Structure*:
  > - `src/N98/Magento/Command/`: Contains all the commands - `src/N98/Util/`: More general utility classes - `src/N98/Magento/Application.php`: Main application class - `config.yaml`: Configuration for commands and other settings - `tests/N98`: Unit Test classes to cover src/N98 classes - `tests/bats`: Functional tests using BATS (Bash Automated Testing System) - `res/`: Resources like autocompletion
- **Software Architecture** — remotion-dev/remotion (copilot-instructions.md), *Monorepo setup*:
  > There are multiple folders in the `packages` folder, which correspond to the packages in the monorepo.  The **package name** for each folder is `@remotion/[folder-name]`, except for the `core` package, which has the package name `remotion`, and for `create-video`, which has the package name `create-video`.
- **Task Process** — microsoft/poml (CLAUDE.md), *Common Development Tasks > Updating Language Grammar*:
  > 1. Modify `poml.tmLanguage.json` 2. Test in VS Code with sample files 3. Update syntax test cases
- **Task Process** — microsoft/azure-devops-mcp (copilot-instructions.md), *Adding new prompts*:
  > Ensure the instructions for the language model are clear and concise so that the language model can follow them reliably. The prompts are located in the `src/prompts.ts` file.
- **Low-level Design & Runtime Behavior** — sbalci/ClinicoPathJamoviModule (CLAUDE.md), *CLAUDE.md > Core Architecture > Key Backend Pattern*:
  > All analysis classes inherit from auto-generated base classes and use R6 class system:  ```r crosstableClass <- R6::R6Class(     "crosstableClass",      inherit = crosstableBase,  # Auto-generated from .yaml files     private = list(         .init = function() { ... },         .run = function() { ... }     ) ) ```
- **Low-level Design & Runtime Behavior** — paradigmxyz/reth (CLAUDE.md), *Development Workflow > Debugging Tips*:
  > 1. **Logging**: Use `tracing` crate with appropriate levels    ```rust    tracing::debug!(target: "reth::component", ?value, "description");    ```  2. **Metrics**: Add metrics for monitoring    ```rust    metrics::counter!("reth_component_operations").increment(1);    ```  3. **Test Isolation**: Use separate test databases/directories

## Sensitivity

| Variant | Repos | Agent-only (post-stratified) |
|---|---|---|
| all coded repos (primary) | 197 | 41.8% |
| without unedited /init files | 185 | 42.5% |
| without stub CONTRIBUTING | 184 | 39.2% |
| without links_out units | 191 | 38.8% |

docs/ check: needs the tuned detector (detector/config.json from gapstudy.detector.evaluate).

Flags: conflict (human docs contradict the agent file) on 38 units; links_out on 180.

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

