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
