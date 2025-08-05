# Template Shortcut System - Known Issues

## Overview
The template shortcut system has been implemented but has several issues that need to be resolved before it can be considered production-ready.

## Issues

### 1. Double Execution
- **Problem**: When executing a template shortcut (e.g., `/debug`), the agent output appears twice
- **Cause**: The template shortcut command executes the prompt via `process_request`, but the REPL may also be processing it
- **Status**: Attempted fix by removing the return of prompt string, but issue persists

### 2. Application Restart Loop
- **Problem**: The application enters a restart loop when executing template shortcuts
- **Symptoms**:
  - TunaCode banner appears multiple times
  - Safety branch prompt appears repeatedly
  - The shortcut command seems to trigger a full application restart
- **Impact**: Makes the shortcut system unusable in practice

### 3. Invalid JSON Generation
- **Problem**: The agent generates invalid JSON when trying to execute multiple tool calls
- **Example**: `{"filepath": "docs/DEVELOPMENT.md"}{"filepath": "docs/FEATURES.md"}...`
- **Expected**: Should be a proper JSON array or separate tool calls
- **Impact**: Tool calls fail with JSON parsing errors

### 4. Type Checking Issues
- **Problem**: Pre-commit hooks fail due to mypy errors
- **Fixed**: Changed `list[str]` to `List[str]` for Python 3.8 compatibility

## Implementation Files

### Added
- `src/tunacode/cli/commands/template_shortcut.py` - New command class for template shortcuts

### Modified
- `src/tunacode/templates/loader.py` - Added shortcut field to Template dataclass
- `src/tunacode/cli/commands/implementations/template.py` - Updated to show shortcuts
- `src/tunacode/cli/commands/registry.py` - Added dynamic shortcut loading
- `src/tunacode/cli/repl.py` - Modified to handle template shortcut returns

### Template Files Updated
- `~/.config/tunacode/templates/debug.json` - Added `/debug` shortcut
- `~/.config/tunacode/templates/refactor.json` - Added `/refactor` shortcut
- `~/.config/tunacode/templates/web-dev.json` - Added `/webdev` shortcut
- `~/.config/tunacode/templates/data-analysis.json` - Added `/analyze` shortcut

## Next Steps

1. **Debug Restart Loop**: Investigate why template shortcuts trigger application restarts
2. **Fix Double Execution**: Ensure prompts are only executed once
3. **Fix JSON Generation**: Investigate the agent's tool call generation
4. **Test Integration**: Comprehensive testing of the shortcut system
5. **Documentation**: Update documentation once issues are resolved
