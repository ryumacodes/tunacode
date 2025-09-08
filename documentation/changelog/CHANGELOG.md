# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.69] - 2025-08-21

### Summary
This release includes comprehensive command system documentation, updated model configurations, and builds upon recent community contributions including the slash command system by @Lftobs (#85) and onboarding improvements by @ryumacodes (#88).

### Changed
- Updated OpenRouter GPT model reference from `gpt-4o` to `gpt-4.1` in setup configuration

### Added
- Additional development documentation in `.claude/` directory
  - Model updates documentation
  - Slash commands documentation
  - Onboarding improvements documentation

## [0.0.68] - 2025-08-21

### Added
- **Comprehensive Command System Documentation**
  - Created `command-system-architecture.md` with technical overview of command infrastructure
  - Created `creating-custom-commands.md` with step-by-step guide for developers
  - Updated user documentation with slash command information
  - Added `/command-reload` command documentation

### Fixed
- Removed broken link to non-existent `templates.md` file in documentation

## [Unreleased] - 2025-08-20

### Added

- **Comprehensive Onboarding Experience Improvements** (#88) - Thanks to **@ryumacodes**!
  - Enhanced user onboarding flow and setup experience
  - Improved first-time user guidance and documentation
  - Streamlined installation and configuration process
  - Resolved issue #55

### Recent Pull Requests

- **Slash Command System for Custom Automation Workflows** (#85) - Thanks to **@Lftobs**!
  - Implemented flexible slash command infrastructure
  - Enabled custom automation workflows
  - Extended CLI capabilities with user-defined commands

- **User Documentation and README Index** (#83) - Thanks to **@MclPio**!
  - Added comprehensive user documentation
  - Updated main README with organized index
  - Improved documentation structure and accessibility

### Contributors

Special thanks to our recent contributors:
- **@ryumacodes** - Onboarding improvements and multiple feature implementations
- **@Lftobs** - Slash command system and workflow automation
- **@MclPio** - Documentation improvements and organization
