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

### Repository level (unweighted, knowledge units)

| Share per repository | Mean | Median | Q1 | Q3 |
|---|---|---|---|---|
| Agent-only | 40.9% | 37.5% | 16.7% | 66.7% |
| Partially covered | 44.4% | 50.0% | 25.0% | 60.0% |
| Shared | 14.7% | 10.0% | 0.0% | 22.2% |
| Agent-only or partial | 85.3% | 90.0% | 77.8% | 100.0% |

Repositories by agent-only share: 0%: 33, 1–25%: 41, 26–50%: 56, 51–75%: 38, 76–99%: 14, 100%: 15. 164 of 197 repositories have at least one agent-only unit; 97 share no unit fully with their human docs. Median agent-only share by agent: AGENTS.md 33.3%, CLAUDE.md 33.3%, copilot-instructions.md 50.0%.

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
| Processes and Practices | Development Process | 362 | 153 | 28.1% |
| Processes and Practices | Development Environment and Tools | 313 | 147 | 26.3% |
| Product | Software Architecture | 148 | 105 | 11.4% |
| Product | Low-level Design & Runtime Behavior | 103 | 62 | 9.3% |
| Processes and Practices | Task Process | 67 | 48 | 5.6% |
| Product | Technologies Used | 52 | 41 | 4.1% |
| Product | Product/Domain | 38 | 32 | 3.5% |
| Documentation | Repository, Indexes, and Search | 44 | 38 | 3.3% |
| Documentation | Developer-Oriented Documentation | 36 | 27 | 2.9% |
| Processes and Practices | Software Configuration Management | 27 | 21 | 2.3% |
| Product | Design & Implementation Rationale | 15 | 13 | 1.7% |
| Documentation | Learning Material | 8 | 8 | 1.1% |
| Context | Organization | 1 | 1 | 0.2% |
| Team | Communication Strategies | 1 | 1 | 0.1% |
| Team | Roles and Expertise | 1 | 1 | 0.1% |

By group: Processes and Practices 62.4%; Product 29.9%; Documentation 7.3%; Context 0.2%; Team 0.2%

### Barriers mitigated (Steinmacher et al.; multi-label)

| Group | Barrier | Units | Repos | Share of gap units |
|---|---|---|---|---|
| Newcomers' characteristics | Lack of knowledge in project process and practices | 453 | 170 | 35.8% |
| Technical hurdles | Local environment setup hurdles | 317 | 143 | 26.0% |
| Technical hurdles | Code/architecture hurdles | 269 | 128 | 22.1% |
| Newcomers' orientation | Finding the correct artifacts to fix an issue | 206 | 126 | 16.3% |
| Newcomers' characteristics | Lack of technical background | 125 | 74 | 11.3% |
| Newcomers' orientation | Newcomers don't know what is the contribution flow | 87 | 67 | 7.1% |
| Newcomers' characteristics | Lack of domain expertise | 56 | 40 | 5.8% |
| Technical hurdles | Understanding flow of information | 20 | 11 | 1.7% |
| Newcomers' orientation | Poor “How to Contribute” available | 3 | 2 | 0.2% |
| Newcomers' orientation | Finding a task to start with | 4 | 3 | 0.2% |
| — | (no barrier coded) | 0 | 0 | 0.0% |

### Example agent-only knowledge (seeded sample, ≤ 60 words)

- **Development Process** — paradigmxyz/reth (CLAUDE.md), *Development Workflow > Common Pitfalls*:
  > 1. **Don't Block Async Tasks**: Use `spawn_blocking` for CPU-intensive work or work with lots of blocking I/O 2. **Handle Errors Properly**: Use `?` operator and proper error types
- **Development Process** — dotnet/docs-desktop (copilot-instructions.md), *Writing Style > Formatting Conventions*:
  > - **Bold** for UI elements. - `Code style` for file names, folders, custom types, non-localizable text. - Raw URLs in angle brackets. - Use relative links for files in this repo. - Remove `https://learn.microsoft.com/en-us` from learn.microsoft.com links.
- **Development Environment and Tools** — microsoft/generative-ai-with-javascript (AGENTS.md), *Development Workflow > Local Development*:
  > 1. Ensure Node.js 20+ is installed 2. Set `GITHUB_TOKEN` environment variable 3. Navigate to the directory you want to work with 4. Run `npm install` followed by `npm start`
- **Development Environment and Tools** — stellar/stellar-cli (copilot-instructions.md), *Common Tasks > Known Issues*:
  > - **Network timeouts**: `make install` frequently encounters network timeouts with crates.io. This is normal in CI environments. - **Memory constraints**: Full workspace build and test may fail with OOM or "No space left on device" errors in constrained environments. - **Documentation generation**: `make docs` may fail due to disk space constraints.
- **Low-level Design & Runtime Behavior** — mkwatson/ai-fastify-template (AGENTS.md), *🚨 MANDATORY Architecture Rules > Error Handling: Fastify Patterns Only*:
  > ```typescript // ✅ Good: Fastify error handling if (!user) {   throw fastify.httpErrors.notFound('User not found'); }  // ❌ Bad: Generic error throwing throw new Error('Something went wrong'); // Too generic! ```
- **Low-level Design & Runtime Behavior** — logancyang/obsidian-copilot (AGENTS.md), *Important Notes > Obsidian Plugin Environment*:
  > - **Global `app` variable**: In Obsidian plugins, `app` is a globally available variable that provides access to the Obsidian API. It's automatically available in all files without needing to import or declare it.
- **Software Architecture** — netz98/n98-magerun2 (AGENTS.md), *Additional Development Information > Project Structure*:
  > - `src/N98/Magento/Command/`: Contains all the commands - `src/N98/Util/`: More general utility classes - `src/N98/Magento/Application.php`: Main application class - `config.yaml`: Configuration for commands and other settings - `tests/N98`: Unit Test classes to cover src/N98 classes - `tests/bats`: Functional tests using BATS (Bash Automated Testing System) - `res/`: Resources like autocompletion
- **Software Architecture** — tech-systems/panes (CLAUDE.md), *Code Architecture > Core Structure*:
  > - **Main Class**: `CupertinoPane` in `/src/cupertino-pane.ts` - Primary API class - **Settings**: Configuration managed through `/src/settings.ts` with TypeScript interfaces in `/src/models.ts` - **Module System**: Modular architecture with feature modules in `/src/modules/`
- **Task Process** — microsoft/poml (CLAUDE.md), *Common Development Tasks > Updating Language Grammar*:
  > 1. Modify `poml.tmLanguage.json` 2. Test in VS Code with sample files 3. Update syntax test cases
- **Task Process** — microsoft/azure-devops-mcp (copilot-instructions.md), *Adding new prompts*:
  > Ensure the instructions for the language model are clear and concise so that the language model can follow them reliably. The prompts are located in the `src/prompts.ts` file.

## Sensitivity

| Variant | Repos | Agent-only (post-stratified) |
|---|---|---|
| all coded repos (primary) | 197 | 41.8% |
| without unedited /init files | 185 | 42.5% |
| without stub CONTRIBUTING | 184 | 39.2% |
| without links_out units | 191 | 38.8% |

docs/ check (detector estimate, 24 repos): 52 of 87 agent-only units (59.8%) match a docs/ section.

Flags: conflict (human docs contradict the agent file) on 38 units; links_out on 180.

## Label provenance

How each frozen label was produced (single annotator: Himanshu Mishra).

| Origin | Units |
|---|---|
| AI draft accepted unchanged | 1161 |
| AI draft, coverage kept, other fields edited | 1 |
| AI draft, coverage corrected by the annotator | 64 |
| Coded without an AI draft (blind) | 338 |

Of 1226 AI drafts reviewed, 94.8% kept the drafted coverage. After a coverage correction, 58 labels had missing evidence or newcomer-need fields completed by the model (marked `filled_by` in the data).

### By coding set

| set         |   draft_accepted |   draft_details_edited |   draft_corrected |   blind |
|:------------|-----------------:|-----------------------:|------------------:|--------:|
| main        |             1001 |                      0 |                64 |       0 |
| pilot       |              160 |                      1 |                 0 |       0 |
| reliability |                0 |                      0 |                 0 |     338 |

### Correction rate by drafted coverage

| draft_coverage   |   drafts |   corrected | correction_rate   |
|:-----------------|---------:|------------:|:------------------|
| agent_directed   |      127 |          10 | 7.9%              |
| agent_only       |      501 |          37 | 7.4%              |
| partial          |      432 |          13 | 3.0%              |
| shared           |      166 |           4 | 2.4%              |

### Source of the newcomer need (D1/D2) for gap units

| need_source                          |   units |
|:-------------------------------------|--------:|
| first annotator                      |     930 |
| second annotator (both coded a gap)  |     266 |
| model fill after a correction or gap |      20 |

### Corrected drafts (rows: draft, columns: final)

| draft_coverage   |   agent_only |   partial |   shared |
|:-----------------|-------------:|----------:|---------:|
| agent_directed   |            6 |         3 |        1 |
| agent_only       |            0 |        37 |        0 |
| partial          |           10 |         0 |        3 |
| shared           |            0 |         4 |        0 |

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

