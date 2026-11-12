# Error analysis — tfidf (test set)

## False agent-only (labelled covered, scored low): 200

- **jonobr1/two.js::agent::20** (partial, score 0.018) · Architecture Patterns
  > - All shapes inherit from Path or Shape classes - Use factory methods (makeRectangle, makeCircle) instead of direct constructors - Effects (gradients, textures) are applied via fill/stroke properties - Memory management: always call release() for complex objects - Event binding: use bind/unbind patt
- **Rello/audioplayer::agent::2** (partial, score 0.019) · General Guidance
  > Agents should focus on the core application logic and ignore files or folders marked as third-party, sample, or media-related. All changes should preserve the integrity of external dependencies and translations.  For every change, add a meaningful one-liner to the corresponding section (Added, Chang
- **Azure/azqr::agent::8** (partial, score 0.020) · Development Workflow > 4. Building and Distribution
  > ```bash # Build for current platform make build  # Build for specific OS/architecture GOOS=linux GOARCH=amd64 make build GOOS=windows GOARCH=amd64 make build  # Build Docker image make build-image  # Build with version information PRODUCT_VERSION=1.0.0 make build ```
- **omnistrate-oss/omnistrate-ctl::agent::3** (partial, score 0.021) · Documentation Generation Workflow > Documentation System:
  > - Uses `go run doc-gen/main.go` to auto-generate markdown files - Outputs to `mkdocs/docs/` directory - Automatically removes old docs and regenerates fresh content - Documentation must stay synchronized with actual CLI behavior
- **microsoft/poml::agent::11** (partial, score 0.023) · Important Implementation Details > Data Component Loading
  > - Images: Supports base64 encoding, sharp processing for resizing - Documents: Handles PDF, Word, Excel, CSV with specialized parsers - Tables: CSV/Excel processing with D3-dsv - Webpages: URL fetching with content extraction
- **jonobr1/two.js::agent::10** (partial, score 0.023) · Development Patterns > Event System
  > - All objects inherit from Events class - Common events: update, render, resize, play, pause - Use `bind()`, `unbind()`, `trigger()` for event handling
- **callstack/react-native-testing-library::agent::8** (partial, score 0.024) · Architecture Overview > Query System
  > The library provides three query variants for each selector:  - `get*` - Throws if not found (for assertions) - `query*` - Returns null if not found (for conditional logic) - `find*` - Returns Promise, waits for element (for async operations)
- **adaptive/pops::agent::1** (partial, score 0.024) · Build, Test, and Development Commands
  > Run `pnpm install` before contributing. `pnpm run prebuild` formats JSON and JavaScript and should precede any commit touching data. Build the distributable bundle with `pnpm run build`, which executes Rollup using `rollup.config.js`. Execute `pnpm test` to load the compiled bundle and assert key lo
- **equalizedigital/accessibility-checker::agent::25** (partial, score 0.025) · Security Considerations
  > - Sanitize all user inputs - Validate and escape all outputs - Use WordPress nonces for form submissions - Follow WordPress security guidelines - Implement proper capability checks
- **dotnet/docs-desktop::agent::7** (partial, score 0.026) · Code Snippets
  > For snippets >6 lines: 1. Create `./snippets/my-doc/language` folder in same directory as document (for a document named `my-doc.md`) where language is either vb (for visual basic) or csharp (for c#). Omit the `language` component when the document is in the `docs/visual-basic`, `docs/csharp`, or `d
- **Nugine/const-str::agent::9** (partial, score 0.026) · Copilot-Specific Notes
  > - This crate heavily uses const generics and const evaluation - Pay attention to const fn requirements and limitations - When suggesting code changes, ensure they work at compile time - Be aware of Rust edition differences and MSRV constraints - Test suggestions should include both regular tests and
- **lumen-notes/lumen::agent::9** (partial, score 0.027) · Architecture > Data Flow
  > 1. Markdown files are stored in a Git repository (GitHub integration) 2. Files are parsed into Note objects with extracted metadata (tags, links, dates) 3. Notes are indexed and made searchable using fast-fuzzy 4. UI components subscribe to state changes via Jotai atoms 5. Changes are automatically 
- **bennypowers/cem::agent::0** (partial, score 0.028) · (no heading)
  > - Always use Makefile targets for running tests or builds, since they export the necessary env vars
- **adaptive/pops::agent::4** (partial, score 0.028) · Commit & Pull Request Guidelines
  > Follow the Conventional Commit style observed in history (`build(deps-dev): bump rollup…`), using scopes like `data`, `build`, or `docs`. Each PR should describe dataset sources, tooling changes, and any scripts executed. Link tracking issues when available and attach screenshots only when UI artifa
- **Azure/dalec::agent::11** (partial, score 0.028) · Development Environment Requirements > Required Tools
  > - Go 1.24+ (check with `go version`) - Docker with BuildKit support (check with `docker buildx version`) - Standard Unix tools (git, make, etc.)

## Missed agent-only (labelled agent-only, scored high): 81

- **gofiber/fiber::agent::1** (agent_only, score 0.277) · Startup script (reference only – do not run)
  > - Fetch dependencies:    ```bash   go mod tidy && go mod download && go mod vendor   ```  - Install CLI tools referenced in Makefile:    ```bash   go install gotest.tools/gotestsum@latest                 # test runner   go install golang.org/x/vuln/cmd/govulncheck@latest      # vulnerability scanner
- **bancolombia/bc_golden_plugin::agent::7** (agent_only, score 0.221) · 🔧 Critical CI/CD Considerations > Device Consistency
  > ALWAYS use the same device configuration between local and CI: ```dart // Consistent device across environments device: GoldenDeviceData.galaxyS25  // Same locally and in CI ```
- **jdx/mise::agent::5** (agent_only, score 0.216) · Development Commands > Development
  > - `mise run install-dev` - Install development version locally - `mise run clean` - Clean cargo build artifacts
- **inline-chat/inline::agent::25** (agent_only, score 0.197) · Testing & Quality > Code Quality
  > - **Linting**: `bun run lint` (root level), `bun run lint` (server) - **Type Checking**: `bun run typecheck` (verifies TypeScript across projects) - **Testing**: `bun test` (backend), `swift test` (Swift packages) - **Database**: `bun run db:studio` for visual database inspection
- **imfing/hextra::agent::4** (agent_only, score 0.195) · Development Commands > Alternative Task Commands
  > The project uses Task runner (`taskfile.yaml`) for simplified commands:  - `task dev` - Start development server (runs `npm run dev:theme`) - `task build` - Build example site - `task css` - Compile CSS (depends on build)
- **llbbl/codeigniter-chat::agent::3** (agent_only, score 0.194) · Commands > WebSocket Server
  > - `php spark websocket:start` - Start the WebSocket server for real-time chat
- **microsoft/azure-devops-mcp::agent::2** (agent_only, score 0.187) · Adding new tools
  > When adding new tool, always prioritize using an Azure DevOps Typescript client that corresponds the the given Azure DevOps API. Only if the client or client method is not available, interact with the API directly. The tools are located in the `src/tools.ts` file.
- **jdx/mise::agent::3** (agent_only, score 0.178) · Development Commands > Code Quality and Testing
  > - `mise run lint` - Run all linting tasks - `mise run lint-fix` - Run linting and automatically fix issues - `mise run format` - Format code (part of CI task) - `mise run ci` - Run format, build, and test - `mise run test:e2e [test_filename]...` - Run specific e2e tests (use this instead of executin
- **openai/openai-agents-js::agent::7** (agent_only, score 0.170) · Testing & Automated Checks > Code Coverage
  > - Generate coverage report:   ```bash   pnpm test:coverage   ``` - Reports output to `coverage/`.
- **567-labs/kura::agent::11** (agent_only, score 0.166) · Commands > Checkpoint Management
  > ```bash # Analyze existing JSONL checkpoints and estimate migration benefits kura analyze-checkpoints ./checkpoints  # Migrate JSONL checkpoints to HuggingFace datasets format kura migrate-checkpoints ./old_checkpoints ./new_hf_checkpoints  # Migrate with HuggingFace Hub upload and compression kura 
- **culstrup/fireflies-raycast::agent::9** (agent_only, score 0.164) · API Documentation
  > - The Fireflies API documentation is here: https://docs.fireflies.ai/ in case you need to reference it, especially while debugging.
- **typedef-ai/fenic::agent::4** (agent_only, score 0.164) · Development Commands > Linting and Formatting
  > ```bash # Ruff is configured for linting (Google-style docstrings) # Auto-formats code examples in docstrings uv run ruff check . uv run ruff format . ```
- **bruin-data/bruin::agent::26** (agent_only, score 0.155) · Common Development Tasks > Working with Templates
  > ```bash # Test template rendering ./bin/bruin render path/to/template.sql  # Test complete pipeline parsing ./bin/bruin internal parse-pipeline path/to/pipeline ```
- **Uniswap/interface::agent::5** (agent_only, score 0.154) · CLAUDE.md > Common Development Commands > Testing
  > ```bash bun g:test                      # Run all tests bun g:test:coverage             # With coverage bun web playwright:test         # Web E2E tests bun mobile e2e                  # Mobile E2E tests ```
- **basicmachines-co/basic-memory::agent::14** (agent_only, score 0.153) · GitHub Integration > GitHub MCP Tools
  > Using the GitHub Model Context Protocol server, Claude can now:  - **Repository Management**:   - View repository files and structure   - Read file contents   - Create new branches   - Create and update files  - **Issue Management**:   - Create new issues   - Comment on existing issues   - Close and
