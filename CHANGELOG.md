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
