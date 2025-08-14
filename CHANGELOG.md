# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Performance

- **Tool Prompt Micro-Injection System**: XML-based prompt loading for tools
  - Tool prompts now loaded from dedicated XML files in `tools/prompts/`
  - Uses `defusedxml` for secure XML parsing with fallback mechanisms
  - Added specialized prompts for grep and glob tools
  - Tool parameters loaded from XML with fallbacks to hardcoded defaults
  - Reduced overall context size through targeted prompt injection

- **Agent Initialization Caching**: Multiple caching optimizations for startup speed
  - Added `@lru_cache` to XML parsing methods in 8 tool files (~200ms improvement)
  - Module-level agent caching with config validation (~1s improvement)
  - MCP server connection caching with config hash validation (~500ms improvement)
  - Added `clear_all_caches()` function for testing
  - Total improvement: 1.7-2s faster agent initialization

- **Directory Caching System**: Intelligent directory caching using CodeIndex infrastructure
  - Added singleton pattern to CodeIndex with public API and cache freshness tracking
  - Background pre-warming of directory cache during REPL startup (non-blocking)
  - Smart `list_dir` tool integration with CodeIndex cache lookup
  - **50-500x faster** directory operations for cached paths (0.0001s vs 10-200ms)
  - Graceful fallback to filesystem scanning when cache unavailable
  - Automatic cache invalidation with 5-second TTL
  - Memory efficient: ~1-5MB overhead for typical projects

- **System Prompt Caching**: File-based caching for system prompts and TUNACODE.md
  - **9x faster** system prompt loading with modification time checking
  - **3-8 second reduction** in agent initialization time
  - Zero-risk automatic cache invalidation on file changes

- **Search Infrastructure Foundation**: Base implementation for ripgrep binary management
  - Added foundation for search tool improvements
  - Cross-platform binary management infrastructure
  - Preparation for future search optimizations

### Added

- **Tool Enhancement Infrastructure**: XML-based tool prompt system
  - Created `src/tunacode/tools/prompts/` directory for prompt files
  - Added XML prompt files for grep and glob tools
  - Enhanced tool base classes with dynamic prompt loading

### Documentation

- Added performance optimization documentation
- Documented XML-based tool prompt system
- Updated directory caching technical documentation
- Added performance guides to documentation index

## [0.0.62] - 2025-08-14

### Added

- **Enhanced Installation Experience**: Complete overhaul of user onboarding
  - **Automatic Config Creation**: Install script now creates `~/.config/tunacode.json` with sensible defaults
  - **Comprehensive Setup Guidance**: Post-install messages with clear next steps for API key configuration
  - **Setup Wizard Integration**: Prominent mention of `tunacode --setup` for guided configuration
  - **Default Model Update**: Changed default from OpenAI to `openrouter:openai/gpt-4.1` for broader model access

- **UV+Hatch Integration Improvements**: Complete build system enhancements
  - **Dependency Management**: Fixed runtime vs dev dependency issues (moved `defusedxml` to runtime)
  - **Build System**: Migrated to `hatchling` build backend with proper wheel configuration
  - **Publishing Pipeline**: Streamlined publish workflow with pure Hatch+UV integration

- **Robust Installation Scripts**: Professional-grade installation and maintenance
  - **Smart Detection**: Install script distinguishes wrapper scripts from actual binaries
  - **Update Logic**: Intelligent update detection for venv, global, and system installations
  - **Comprehensive Uninstall**: Complete removal tool with multi-installation detection
  - **UV Acceleration**: 10-100x faster installs when UV is available with graceful pip fallback

### Changed

- **Pre-commit Hook Optimization**: Consistent tool usage strategy
  - Use `hatch run` for commands defined in pyproject.toml scripts
  - Use `uv run` for standalone tools not managed by hatch environments
  - Updated test runner from `uv run pytest` to `hatch run test` for consistency
  - Enhanced CI configuration with appropriate hook skipping

- **Development Workflow**: Improved developer experience
  - All 298 tests passing with new build system
  - Optimized pre-commit hooks for faster development cycles
  - Better documentation maintenance with automated quality checks

### Fixed

- **Build System Issues**: Resolved setuptools to hatchling migration problems
- **Dependency Resolution**: Fixed missing runtime dependencies in hatch environments
- **Install Script**: Added missing print helper functions for consistent colored output
- **Documentation**: Updated UV+Hatch setup documentation with recent improvements

### Documentation

- **UV+Hatch Setup Guide**: Comprehensive documentation of build system migration
- **Installation Experience**: Documented automatic config creation and user guidance
- **Development Workflow**: Updated all build, test, and deployment procedures
- **Pre-commit Strategy**: Clear guidelines for tool selection and usage

## [0.0.56] - 2025-08-11

### Added

- **Plan Mode**: New read-only research phase for implementation planning (#81) - Thanks to **ryumacodes**!
  - `/plan` command to enter Plan Mode for research and planning
  - `/exit-plan` command to manually exit Plan Mode
  - `present_plan` tool for structured plan presentation with user approval
  - Visual indicators in status bar, input prompt, and placeholder text
  - Tool restrictions - only read-only tools available in Plan Mode
  - Shift+Tab keyboard shortcut to toggle Plan Mode
  - Clean UI with "⏸ PLAN MODE ON" indicator above input

### Changed

- **BREAKING**: Migrated from Makefile to Hatch for cross-platform compatibility - Thanks to **ryumacodes**!
- Modified CLI commands processing
- Updated REPL functionality
- Enhanced output display formatting
- Refactored main.py to reduce file size from 691 to 447 lines
- Improved ESC key handling with double-press safety and unified abort behavior
- Added comprehensive ESC key investigation documentation

### Fixed

- Restored Thinking dots animation with faster timing

### Migration Guide

**Makefile → Hatch Command Migration:**

| Old Command | New Command | Notes |
|-------------|-------------|--------|
| `make install` | `hatch run install` | Install dev dependencies |
| `make run` | `hatch run run` | Run TunaCode CLI |
| `make clean` | `hatch run clean` | Clean build artifacts |
| `make lint` | `hatch run lint` | Run linting and formatting |
| `make test` | `hatch run test` | Run test suite |
| `make coverage` | `hatch run coverage` | Run tests with coverage |
| `make build` | `hatch build` | Build distribution packages |
| `make vulture` | `hatch run vulture` | Dead code analysis |
| `make remove-playwright-binaries` | `hatch run remove-playwright` | Remove Playwright cache |

**Benefits:**
- Windows compatibility without WSL or MinGW
- No external make dependency required
- Better Python ecosystem integration
- Consistent cross-platform behavior

### Fixed

- ESC key double-press safety restoration
- Unified ESC and Ctrl+C abort handling in REPL
- Pre-commit hook configuration for file length checks

### Contributors

Special thanks to our community contributors:
- **mohaidoss** - ESC key interrupt functionality (#29)
- **MclPio** - Token cost tracking feature (#17)
- **prudentbird** - Context window management (#17)
- **Lftobs** - Todo tool functionality and @-file-ref enhancements (#17, #2)
- **ColeMurray** - Security fix for B108 vulnerability (#25)
- **ryumacodes** - Plan Mode implementation (#81), Hatch migration for cross-platform support, and RuntimeWarnings fix (#71)

## [0.0.55] - 2025-08-08

### Added
- Activity indicator with animated dots during operations
- Spinner update infrastructure for better tool execution status feedback

### Changed
- Simplified type hint for asyncio.Task in StreamingAgentPanel
- Extracted truncation checking to separate module (node_processor.py reduced to 438 lines)

### Fixed
- JSON string args handling in get_tool_description call
- Debug print statements causing console pollution
- Dynamic spinner messages by keeping spinner running during tool execution

## [0.0.54] - 2025-08-08

### Fixed
- Made publish script idempotent and handle partial completions
- Moved cleanup section after version calculation in publish script

## [0.0.23] - 2025-01-06

### Added

- Fallback response handling for agent iterations

## [0.0.22] - 2025-01-06

### Added

- Control-C handling improvements for smooth exit

## [0.0.21] - 2025-01-06

### Fixed

- Various bug fixes and improvements

## [0.0.19] - 2025-01-06

### Added

- Orchestrator features with planning visibility
- Background manager implementation

### Changed

- Updated README with orchestrator features
- System prompt updates

## [0.0.18] - 2025-01-05

### Fixed

- Circular import in ReadOnlyAgent
- Orchestrator integration to use TunaCode's LLM infrastructure

## [0.0.17] - 2025-01-05

### Changed

- General codebase cleanup

## [0.0.16] - 2025-01-05

### Fixed

- Publish script to use temporary deploy venv
- Improved .gitignore

## [0.0.15] - 2025-01-05

### Added

- Shell command support with `!` prefix
- Updated yolomode message

### Fixed

- Escape-enter keybinding test

## [0.0.14] - 2025-01-04

### Changed

- Various improvements and bug fixes

## [0.0.13] - 2025-01-04

### Changed

- Initial stable release with core features
