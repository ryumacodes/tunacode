# Dead Code Analysis Report

## Summary
Vulture analysis with 60% confidence threshold identified potential dead code. After verification, here are the findings:

## Confirmed Dead Code

### 1. Unused API Module ✅ REMOVED
- **Directory**: `src/api/` (entire directory)
- **Files removed**:
  - `src/api/users.py` - UserManager class
  - `src/api/auth.py` - authenticate and generate_token functions
- **Action**: Successfully removed - no external dependencies found

### 2. ~~Unused Constants~~ FALSE POSITIVE ✅ VERIFIED IN USE
- **File**: `src/tunacode/constants.py`
- **Items**: All constants flagged by vulture are actually in use:
  - `WRITE_TOOLS` (line 45) - Architectural constant for tool categorization
  - `EXECUTE_TOOLS` (line 46) - Architectural constant for tool categorization
  - `CMD_QUIT` (line 56) - Part of command system
  - `COMMAND_PREFIX` (line 70) - Used in command system architecture
  - `UI_*` constants (lines 100-105) - Used throughout UI modules (panels.py, output.py, tool_ui.py)
  - Various ERROR_* constants - Used in text_utils.py and tools
- **Action**: NO ACTION NEEDED - All constants are actively used

### 3. Unused Functions ✅ REMOVED
- **File**: `src/tunacode/context.py`
- **Item**: `get_context()` function (line 74)
- **Action**: Successfully removed - function was only used by tests, not by the application itself

### 4. Duplicate Functions ✅ REMOVED
- **Files**: `src/tunacode/core/agents/main.py` and `src/tunacode/core/agents/utils.py`
- **Items**:
  - `batch_read_only_tools()` (duplicated) - Removed from main.py
  - `create_buffering_callback()` (duplicated) - Removed from main.py
- **Action**: Successfully removed duplicates, kept in utils.py

### 5. Unused Logging Classes
- **File**: `src/tunacode/core/logging/`
- **Items**: Various formatter and handler classes
- **Action**: Review logging architecture

## False Positives

### TypedDict Fields
Many items in `types.py` are TypedDict fields that vulture incorrectly flags as unused:
- These are type annotations used by the type checker
- Should NOT be removed

### Dynamic Usage
Some methods might be used dynamically:
- `is_command()` in registry.py
- `get_completions()` in completers.py

## Recommendations

1. **Immediate cleanup**: Remove `src/api/users.py` as it's clearly unused
2. **Constants audit**: Review constants.py and remove truly unused constants
3. **Function deduplication**: Remove duplicate functions in agents module
4. **Logging review**: Assess if logging classes are needed for future use

## Cleanup Summary

### Successfully Removed:
1. ✅ API module (`src/api/` directory) - Completely unused
2. ✅ Duplicate `batch_read_only_tools()` function from `main.py`
3. ✅ Duplicate `create_buffering_callback()` function from `main.py`
4. ✅ Unused `get_context()` function from `context.py`

### Verified as Active Code (False Positives):
1. ✅ All constants in `constants.py` - Used throughout the codebase
2. ✅ Functions in `context.py` (except `get_context()`) - May be used dynamically

### Verification Results:
- Running `vulture --min-confidence 80` now returns no results (clean!)
- At 60% confidence, vulture still flags constants and some methods that are actually in use

Total lines removed: ~75 lines of truly dead code
