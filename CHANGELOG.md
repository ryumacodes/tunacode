# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.72] - 2025-09-11

### Summary
This release includes a major architectural improvement with enum-based state machine implementation, enhanced system prompt updates, and improved tool validation configuration.

### Added
- **Enum-Based State Machine for Agent Completion Detection**
  - Implemented AgentState enum with 4 states: USER_INPUT, ASSISTANT, TOOL_EXECUTION, RESPONSE
  - Created AgentStateMachine with thread-safe state transition validation
  - Added state transition rules to prevent invalid state changes
  - Enhanced completion detection logic to eliminate premature completion issues
  - Maintained full backward compatibility with existing boolean flags

### Changed
- **System Prompt Updates**
  - Updated task completion marker from `TUNACODE_TASK_COMPLETE` to `TUNACODE DONE:`
  - Enhanced tool documentation and examples
  - Improved agent behavior rules and instructions
  - Fixed test cases to match new completion marker format

### Fixed
- **Test Alignment Issues** - Updated test cases to use correct completion marker format
- **System Prompt Consistency** - Ensured all documentation and tests use consistent completion signaling

## [0.0.71] - 2025-09-11

### Added
- **Configurable Tool Strict Validation** - Users can now control tool parameter validation behavior through `tool_strict_validation` setting in tunacode.json
  - Added configuration option for tool strict validation (defaults to false for backward compatibility)
  - Updated all Tool constructors to use configurable setting

### Fixed
- **Tool Constructor Validation Issues** - Added `strict=False` parameter to prevent validation failures when tool parameters don't exactly match function signatures
  - Updated Tool constructors in agent configuration to include strict parameter
  - Improved system reliability and user experience

## [0.0.70] - 2025-09-11

### Added
- **Enhanced Configuration Documentation** - Added comprehensive documentation for new tunacode.json settings
  - Documented tool validation configuration options
  - Added examples and usage guidelines

### Changed
- **Model Configuration Updates** - Updated OpenRouter model references and configurations
  - Enhanced model selection and validation logic
  - Improved integration with models.dev service

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

  - Enhanced configuration documentation with new setting details

### Fixed
- **Tool Constructor Validation Issues** - Added `strict=False` parameter to prevent validation failures when tool parameters don't exactly match function signatures
  - Updated Tool constructors in agent configuration to include strict parameter
  - Improved system reliability and user experience

## [0.0.69] - 2025-08-21

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
- **@tunahorse** - Tool validation improvements and configurable parameter handling
