# Pre-commit Fixes Plan

## Overview
This document outlines the systematic approach to fix all pre-commit hook failures. Last updated after completing all 4 phases of fixes, resolving most type errors and formatting issues.

## Completed Fixes ✅

### 1. Test Failures - FIXED
- **File**: `tests/characterization/agent/test_process_request.py`
- **Issue**: 7 tests failing with `ValueError: not enough values to unpack`
- **Root cause**: `_process_node` mock not configured to return expected tuple
- **Solution**: Configured all mock instances to return `(False, None)`
- **Result**: All 8 tests now pass

### 2. Agent Response Handling - FIXED
- **File**: `src/tunacode/core/agents/main.py`
- **Issue**: UserPromptPart import errors causing ImportError
- **Solution**: Updated imports to use `get_model_messages()` helper and getattr pattern
- **Result**: Import errors resolved, agent runs properly

### 3. Formatting Issues - FIXED
- **File**: `tests/characterization/repl/test_repl_initialization.py`
- **Issue**: Ruff format violations
- **Solution**: Applied ruff formatting
- **Result**: File properly formatted

### 4. Import Fix - FIXED
- **File**: `src/tunacode/utils/message_utils.py`
- **Issue**: Using `any` instead of `typing.Any`
- **Solution**: Changed to proper `from typing import Any`
- **Result**: Type annotation corrected

### 5. Trailing Whitespace & EOF - FIXED
- **Files**: Various markdown files
- **Issue**: Missing newlines at end of files
- **Solution**: Auto-fixed by pre-commit hooks
- **Result**: All files have proper endings

## Newly Completed Fixes ✅

### 6. Simple Type Annotations (Phase 1) - FIXED
- Fixed `expanded_files: list[str] = []` in text_utils.py
- Fixed `doc_freqs: list[dict] = []` in bm25.py
- Fixed `doc_lens: list[int] = []` in bm25.py
- Fixed `idf: dict[str, float] = {}` in bm25.py
- Fixed `df: dict[str, int]` in bm25.py
- Fixed `_encoding_cache: dict[str, Any] = {}` in token_counter.py
- Fixed `results: list[Dict[str, Any]] = []` in startup_timer.py
- Fixed `matches: list[Path] = []` in grep.py
- Fixed `task: asyncio.Task` annotation in background manager

### 7. Complex Type Issues (Phase 2) - FIXED
- Added type ignore comments for OrderedDict incompatibilities in file_utils.py
- Fixed MessagePart and ModelResponse type annotations in types.py
- Added type checks for Union types in todo.py to ensure correct types
- Fixed Awaitable vs Coroutine mismatch in background manager
- Fixed F.sync attribute issue using setattr() in decorators.py

### 8. Return Type Mismatches (Phase 3) - FIXED
- Fixed tool_ui.py Markdown to str conversion
- Fixed grep.py return type to Union[str, List[str]]
- Added type ignore for duplicate JSONFormatter in formatters.py
- Fixed None __await__ issues by adding proper None checks
- Fixed missing return statement in repl.py error handler

### 9. Dead Code Cleanup (Phase 4) - FIXED
- Prefixed unused parameters with underscore in deprecated check_query_satisfaction function
- All vulture warnings addressed

### 10. Additional Fixes
- Added missing imports: Any, Awaitable where needed
- Fixed import sorting issues with ruff
- Removed unused Type import from types.py
- Fixed process_request callback calls with proper None checks

## Remaining Issues 🔧

### 1. MyPy Type Errors (4 remaining)
- `src/tunacode/types.py:36,38` - Type alias redefinition in try/except blocks (partially addressed with type: ignore)
- `src/tunacode/cli/commands/template_shortcut.py:87` - "process_request" instance variable issue
- `src/tunacode/cli/commands/implementations/development.py:76` - "process_request" instance variable issue
- Various `note:` warnings about untyped function bodies (non-critical)

### 2. Test Failures (1 remaining)
- `test_help_command_shows_commands` - Help command output format has changed

## Summary of Completed Work

### What Was Done
1. **Phase 1: Simple Type Annotations** ✅
   - Added type annotations for all list and dict initializations
   - Fixed missing Any imports where needed
   - All basic type hints now in place

2. **Phase 2: Complex Type Issues** ✅
   - Fixed OrderedDict issues with type: ignore comments
   - Resolved Union type mismatches in todo.py with runtime checks
   - Fixed Awaitable/Coroutine types in background manager
   - Resolved F.sync attribute issue using setattr()

3. **Phase 3: Return Type Fixes** ✅
   - Fixed Markdown to str conversions in tool_ui.py
   - Updated grep.py return type to Union[str, List[str]]
   - Added type: ignore for intentional duplicate definitions
   - Fixed None checks for streaming callbacks

4. **Phase 4: Dead Code Cleanup** ✅
   - Prefixed unused parameters in deprecated functions
   - All vulture warnings addressed

### Current Status
- ✅ Ruff checks pass (formatting and imports)
- ✅ Most MyPy errors resolved (from 30 down to 4)
- ✅ All dead code warnings addressed
- ✅ Import sorting fixed
- 🔧 4 MyPy errors remain (mostly edge cases)
- 🔧 1 test needs updating for new output format

## Lessons Learned

### 1. Mock Configuration in Tests
**Issue**: Tests failing with "not enough values to unpack"
**Lesson**: When mocking functions that return tuples, always configure the mock's return_value:
```python
mock_process.return_value = (False, None)  # For functions returning (bool, Optional[str])
```

### 2. Dynamic Import Patterns
**Issue**: ImportError for UserPromptPart in test environments
**Solution**: Use dynamic imports with fallbacks:
```python
import importlib
messages = importlib.import_module("pydantic_ai.messages")
UserPromptPart = getattr(messages, "UserPromptPart", messages.UserPromptPart)
```

### 3. Pre-commit Hook Behavior
- Some hooks auto-fix issues (trailing whitespace, EOF)
- Others require manual intervention (mypy, complex formatting)
- Running with `--no-verify` skips hooks but should be used sparingly

### 4. Test Characterization
The characterization tests capture existing behavior, so when fixing issues:
- Update test expectations to match new behavior
- Don't change behavior unless necessary
- Document any behavioral changes

## Next Steps for Remaining Issues

1. **Fix remaining MyPy errors**:
   - The process_request instance variable warnings may need ClassVar annotation
   - Consider refactoring how process_request callback is handled

2. **Update failing test**:
   - Fix `test_help_command_shows_commands` to match new output format

3. **Final validation**:
   - Run `pre-commit run --all-files` to ensure all hooks pass
   - Commit the changes with detailed message

## Files Modified

### Type Annotations Added/Fixed:
- `src/tunacode/utils/text_utils.py`
- `src/tunacode/utils/bm25.py`
- `src/tunacode/utils/token_counter.py`
- `scripts/startup_timer.py`
- `src/tunacode/tools/grep.py`
- `src/tunacode/core/background/manager.py`
- `src/tunacode/utils/file_utils.py`
- `src/tunacode/types.py`
- `src/tunacode/tools/todo.py`
- `src/tunacode/ui/decorators.py`
- `src/tunacode/ui/tool_ui.py`
- `src/tunacode/core/logging/formatters.py`
- `src/tunacode/core/agents/main.py`
- `src/tunacode/ui/panels.py`
- `src/tunacode/cli/commands/template_shortcut.py`
- `src/tunacode/cli/commands/implementations/development.py`
- `src/tunacode/cli/commands/implementations/conversation.py`
- `src/tunacode/cli/commands/registry.py`
- `src/tunacode/cli/repl.py`
