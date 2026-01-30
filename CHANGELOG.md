# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.52] - 2026-01-30

### Added

- **Architecture:** Introduced `ToolRetryError` domain exception for framework-agnostic retry signaling (#326)
  - Decorator acts as adapter, converting `ToolRetryError` → `pydantic_ai.ModelRetry`
  - All tools (`bash`, `glob`, `grep`, `list_dir`, `update_file`, `web_fetch`, `write_file`) now raise `ToolRetryError`
- **Architecture:** Reorganized LLM framework types to infrastructure layer (#332)
  - Created `tunacode/infrastructure/llm_types.py` for pydantic-ai specific types
  - Moved `PydanticAgent`, `AgentRun`, `MessageHistory` to infrastructure layer
  - Added protocol-based types (`ToolCallPartProtocol`, `StreamResultProtocol`) for framework-agnostic callbacks
  - Deleted `tunacode/types/pydantic_ai.py` (moved to canonical and infrastructure)
  - Core layers now depend on framework-agnostic protocols, not pydantic-ai directly

### Changed

- **UI:** Removed streaming lifecycle from TUI for cleaner architecture (#327)
  - Streaming callback disabled; responses render as single final panel
  - `ChatContainer` simplified: removed `start_stream/update_stream/end_stream/cancel_stream`
  - Added explicit insertion-anchor APIs: `clear_insertion_anchor()` and `set_insertion_anchor()`
  - Renamed `action_cancel_stream` → `action_cancel_request` for clarity
- **Architecture:** Moved dependency layer artifacts to `docs/architecture/dependencies/` (#325)
  - Centralized dependency visualization (DOT files, generated PNGs) under architecture docs
  - Updated all scripts and tools to reference new paths
- **Architecture:** Removed `tools.messaging` facade, core now imports directly from `utils.messaging` (#322)
  - Deleted `src/tunacode/tools/messaging/__init__.py` (29 lines of pure re-exports)
  - Simplified dependency graph by removing unnecessary indirection layer

### Removed

- **UI:** Incremental streaming display and per-request streaming state (#327)
  - No more `paused/cancelled/buffer/current_stream_text` fields in app.py
  - Final response derived from conversation history via `_get_latest_response_text()`

### Fixed

- **UI:** ChatContainer widget with insertion anchor tracking for tool panels (#319)
  - Fixes race condition where tool panels appeared at wrong position after stream cancel/end
  - New stream lifecycle: `start_stream()`, `end_stream()`, `cancel_stream()`, `insert_before_stream()`
  - Tool panels now position correctly regardless of async timing
- **UI:** LSP server status indicator in ResourceBar showing running/stopped state
- **LSP:** Centralized diagnostics helper `maybe_prepend_lsp_diagnostics()` in `tools/lsp/diagnostics.py`
  - Tools now explicitly call diagnostics after file writes
  - Prepends LSP errors/warnings as XML to tool results
- **Architecture:** Dependency layer visualization with auto-generated PNG (`scripts/grimp_layers_report.py`)
- **Core:** Preserve partial response on user abort during streaming (#323)
  - Captures accumulated stream text from `_debug_raw_stream_accum` on Escape/Ctrl+C
  - Persists partial response with `[INTERRUPTED]` prefix to conversation history
  - Prevents data loss when aborting mid-stream

## [0.1.50] - 2026-01-25

### Changed

- **Architecture:** Delete indexing system (~620 lines) and fix LSP lateral coupling (#318)
  - Removed entire `indexing/` module and `core/indexing_service.py`
  - Merged `tools/lsp_status.py` into `core/lsp_status.py`
  - Simplified `file_tool` decorator (removed LSP orchestration and `writes` parameter)
  - `glob.py` now always uses filesystem scanning (removed index optimization path)
- **Architecture:** Resolve layer violations — eliminated 24 direct `core` → `utils` imports (#317)
  - Moved `utils/parsing/` → `tools/parsing/`
  - Moved `utils/config/` → `configuration/`
  - Moved `utils/limits.py`, `utils/system/paths.py` → `configuration/`
  - Created `tools/messaging/` facade that re-exports from `utils/messaging/`
  - Moved `utils/ui/file_filter.py` → `infrastructure/file_filter.py` (standalone, zero internal deps)
  - Deleted empty utility packages
- **Architecture:** Resolve core types layering and namespace collision (#316)
  - Introduced `core/shared_types` facade for UI-shared types
  - Created `core/types` package for core-only state types (`AgentState`, `ResponseState`, protocols)
  - Added `AgentState` enum for explicit state machine transitions
  - Made `ResponseState` thread-safe with `threading.RLock`
- **UI:** Replaced `RichLog` with `ChatContainer` in main app (backward-compatible `rich_log` alias)

### Fixed

- **UI:** Tool panels no longer appear at bottom after stream cancellation
- **Core:** Preserve partial response on user abort during streaming (#323)
  - Captures accumulated stream text from `_debug_raw_stream_accum` on Escape/Ctrl+C
  - Persists partial response with `[INTERRUPTED]` prefix to conversation history
  - Prevents data loss when aborting mid-stream
- **Types:** Resolved mypy errors across configuration, core, and tools modules
- **Autocomplete:** Fixed fuzzy matching in file filter

## [0.1.43] - 2026-01-22

### Added

- Naming conventions documentation and pre-commit enforcement hook
- GitHub issue templates for bug reports and feature requests
- Dependabot configuration for automated dependency updates (#277)

### Fixed

- Preserve conversation messages in `/clear` command (#275)
- Enable strict mypy for core/agents module, fixing 25 type errors (#278)

### Changed

- Exclude agents directory from mypy pre-commit hook

## [0.1.42] - 2026-01-21

### Added

- Extract session resume logic into dedicated `resume/` module (#272)

### Changed

- Remove streaming watchdog and silent fallback for cleaner architecture

## [0.1.41] - 2026-01-20

### Added

- Enhanced debug mode with actionable logs and colors (#263)

### Fixed

- Resolve session resume hangs after user abort

## [0.1.40] - 2026-01-20

### Fixed

- `/update` command crashes when update is available
- Agent loop no longer breaks when submit tool is called
- Correct wiki-link to nextstep_panels documentation

## [0.1.39] - 2026-01-20

### Added

- Better error handling for shell commands (#248)

### Changed

- Default behavior of `/update` command now installs updates (#247)

## [0.1.38] - 2026-01-19

### Fixed

- Persist messages on abort to prevent data loss (#257)
- Handle dangling tool calls after user abort

## [0.1.37] - 2026-01-19

### Added

- Lifecycle debug logging for better observability (#256)
- Hypothesis marker for property-based tests

### Fixed

- Handle CancelledError in timeout cleanup path
- Remove lambda wrapper around async run_startup_index
- Add submit tool to READ_ONLY_TOOLS (#254)

### Changed

- Remove duplicate startup index worker from app.py (#253)

## [0.1.36] - 2026-01-17

### Changed

- Tool call handling, debug diagnostics, and panel width fixes (#246)
- Remove unused local config and screenshot files

## [0.1.35] - 2026-01-16

### Changed

- Centralize panel width handling and simplify tool renderers (#244)
- Hook-arrow params across tool panels (#243)

## [0.1.26] - 2026-01-09

### Added

- NeXTSTEP agent response panels with streaming support (#218)

## [0.1.25] - 2026-01-08

### Added

- Local mode for small context window models with configurable tool limits (#215, #216)
- BaseToolRenderer pattern for compact NeXTSTEP panels (#214)
- Local mode documentation and README link

### Changed

- Tool improvements and unified BaseToolRenderer pattern

## [0.1.24] - 2026-01-07

### Added

- Plan mode feature with gitignore-aware grep (#213)
- Dynamic provider config from registry, OpenAI-only for non-Anthropic

### Fixed

- Restore plan mode feature (accidentally deleted in d816ff2)

## [0.1.23] - 2026-01-06

### Fixed

- Include models_registry.json in wheel distribution

## [0.1.22] - 2026-01-06

### Fixed

- Use load_models_registry instead of cached version for provider config
- Resolve async/sync mismatch in _normalize_tool_args

## [0.1.21] - 2026-01-03

### Added

- Comprehensive codebase map with SEAMS analysis

### Changed

- Refactor exception formatting
- Cleanup obsolete memory-bank and audit files

## [0.1.20] - 2026-01-02

### Added

- Lazy-load models registry and guardrail picker for faster startup
- UI refinements and research documentation (#204)
- neXTSTEP UI guidelines PDF and reader skill
- Discord server link to README (#194)
- Consolidated default prompt document

### Fixed

- Headless run output extraction (#208)
- Base URL overrides and CLI baseurl flag (#200)
- File size handling refactoring (#155, #154)
- TOOL_VIEWPORT_LINES and DEFAULT_IGNORE_PATTERNS_COUNT (#197)

### Changed

- Refactor headless output extraction to dedicated module
- Remove dead code: callbacks.py, 3 unused UI components (#205), 35 unused constants (#206)
- Refactor types.py to package structure
- Replace magic numbers with symbolic constants
- Reduce MIN_VIEWPORT_LINES to 5 for more compact tool panels
- Uniform tool panel width with fixed TOOL_PANEL_WIDTH

### Contributors

Thanks to our community contributors:

- @ryumacodes - issue fixes and standardization

## [0.1.16] - 2025-12-19

### Added

- Minimum viewport padding to tool panels for better readability (#192) - thanks @larock22
- Standardized tool panel viewport sizing across all renderers (#190)

### Fixed

- Eliminate UI freezes during update_file operations
- LSP diagnostics truncation and hardened diff rendering (#191)
- Tool return arg hydration issue (#189)

### Changed

- Remove inline comments from LSP module for cleaner code

### Contributors

Thanks to our community contributors for this release:

- @larock22 - viewport padding improvements and subagent loading states
- @ryumacodes - update command implementation

## [0.1.12] - 2025-12-18

### Fixed

- Prevent TUI hangs when rendering large tool confirmation diffs (e.g., `write_file` with minified content)

## [0.1.11] - 2025-12-18

### Added

- `/update` command to check for and install updates from TUI (#182) - thanks @ryumacodes
- TodoWrite and TodoRead tools for task tracking (#181)
- LSP status indicator in resource bar showing server name
- Switched Python LSP from pyright to ruff for better integration

### Fixed

- Paste buffer flow with improved user input wrapping (#188)
- LSP diagnostics display with NeXTSTEP 4-zone layout (#186)
- Escape key now cancels shell command input (#187)
- Paste indicator shows inline with "..." for continued content

### Changed

- Simplify concatenated JSON parsing with fail-loud error handling (#175)
- Reduced streaming throttle for smoother output
- Refactored app.py under 600 lines

## [0.1.10] - 2025-12-16

### Added

- Subagent UI loading states with progress feedback (#180)
- Tool start callback for UI feedback (#177)
- Headless CLI mode for benchmark execution (#174)

### Fixed

- Default tunacode to TUI when no subcommand (#178)
- Pass parent state_manager to research agent for API key access (#170)

### Changed

- Pin ruff to 0.14.9 (#179)
- Remove unused GUIDE_FILE_PATTERN constant (#173)
- Remove unused typing scaffolding from state transition (#171)

## [0.1.9] - 2025-12-12

### Added

- Multi-line paste support with collapsed display (#168)

### Changed

- Refactored watch_value editor for better single responsibility (#169)
- Export screen classes from ui/screens package for external access

## [0.1.7] - 2025-12-11

### Added

- NeXTSTEP-style tool panel renderers for consistent UI (#165)
- web_fetch tool for HTTP GET with HTML-to-text conversion
- list_dir tree connectors for better directory visualization
- Section-based prompting engine with template composition
- Slash command autocompletion in TUI (#160) - thanks @coltonsteinbeck
- Model-specific context window from registry (#158) - thanks @vincitamore

### Changed

- Tightened XML prompt loading (#164)
- Removed Python loggers in favor of structured output (#159) - thanks @xan

### Contributors

Thanks to our community contributors for this release:

- @coltonsteinbeck - slash command autocompletion
- @xan - logger cleanup
- @vincitamore - model context windows
- @ryu - real pricing and Textual repl improvements

## [0.1.6] - 2025-12-08

### Added

- Session resume feature (`/resume`) to restore previous conversation sessions
- Write file preview in confirmation dialog showing file contents before creation
- CONTRIBUTING.md for open source contributors

### Changed

- Consolidated ruff config and removed redundant .ruffignore
- Removed stale documentation and knowledge base files
- Removed unused command security constants and XML schema loader

## [0.1.5] - 2025-12-07

### Added

- CHANGELOG.md for tracking version history
- Enhanced update_file tool with diff preview and result display

### Fixed

- Additional lint error fixes

## [0.1.4] - 2025-12-06

### Added

- Tool execution retry mechanism with exponential backoff (max 3 attempts) for improved reliability
- Clear diff display for edit tool operations showing before/after changes
- Uniform truncation with NeXTSTEP information hierarchy for better UX
- Dynamic startup index with progressive loading for faster application launch

### Changed

- Improved error handling to surface retries to user with visual feedback
- Removed dead code and consolidated ToolCallback type alias
- Fixed 40+ ruff lint errors for cleaner codebase

### Fixed

- Edit tool now provides proper visual feedback showing what changed in files
- Tool execution failures no longer halt system immediately, allowing retry attempts
