# Pre-commit Fixes Plan

## Overview
This document outlines the systematic approach to fix all pre-commit hook failures.

## Issues Summary

### 1. End-of-file Fixer (Auto-fixed)
- **Status**: Already fixed by the hook
- **Files affected**:
  - `todo/agent-response-improvements-complete.md`
  - `todo/agent-response-fixes-summary.md`
  - `todo/agent-response-aggressive-fixes.md`
- **Action**: None needed - hook already fixed these

### 2. MyPy Type Errors (32 errors in 20 files)
- **Critical issues**:
  - Missing type annotations for variables
  - Incorrect type usage (`any` vs `typing.Any`)
  - Incompatible type assignments
  - Multiple function redefinitions
  - Attribute access errors on None types

### 3. Ruff Format
- **File**: `tests/characterization/repl/test_repl_initialization.py`
- **Action**: Needs reformatting

### 4. Vulture (Dead Code)
- **File**: `src/tunacode/core/agents/main.py`
- **Issue**: Unused variables at lines 1016-1018 (repeated multiple times)
  - `actions_taken`
  - `current_response`
  - `iteration`

### 5. Test Failures
- **File**: `tests/characterization/agent/test_process_request.py`
- **Failures**: 7 tests failing with unpacking errors
- **Root cause**: `_process_node` returning None or incorrect number of values

## Fix Priority Order

### Phase 1: Critical Test Failures
1. **Fix `_process_node` return value issue in `main.py`**
   - Check line 1113 where unpacking occurs
   - Ensure `_process_node` always returns a tuple of 2 values
   - Handle None return case properly

### Phase 2: Type Annotations
1. **Fix `typing.Any` import**
   - `src/tunacode/utils/message_utils.py:4` - Change `any` to `typing.Any`

2. **Add missing type annotations**
   - `src/tunacode/utils/text_utils.py:84` - `expanded_files: list[str] = []`
   - `src/tunacode/utils/bm25.py:19-21` - Add dict/list type hints
   - `src/tunacode/utils/token_counter.py:11` - `_encoding_cache: dict[str, Any] = {}`
   - `scripts/startup_timer.py:42` - Add list type hint

3. **Fix type incompatibilities**
   - `src/tunacode/utils/file_utils.py:17-18` - Fix dict method type assignments
   - `src/tunacode/tools/todo.py:68,72` - Handle `str | list[str] | None` properly
   - `src/tunacode/core/background/manager.py:20` - Fix Awaitable vs Coroutine type

4. **Fix return type mismatches**
   - `src/tunacode/ui/tool_ui.py:74` - Return str instead of Markdown
   - `src/tunacode/tools/grep.py:182,231` - Fix return type consistency

5. **Fix redefinitions and attribute errors**
   - `src/tunacode/core/logging/formatters.py:35` - Remove duplicate JSONFormatter
   - `src/tunacode/ui/decorators.py:56` - Fix F.sync attribute access
   - `src/tunacode/core/agents/main.py:453,1111` - Handle None.__await__ errors

### Phase 3: Code Cleanup
1. **Remove unused variables in `main.py`**
   - Lines 1016-1018: Remove or use `actions_taken`, `current_response`, `iteration`
   - Or prefix with underscore if intentionally unused: `_actions_taken`

### Phase 4: Formatting
1. **Run ruff format on test file**
   - Format `tests/characterization/repl/test_repl_initialization.py`

## Implementation Strategy

### Step 1: Create feature branch
```bash
git checkout -b fix/pre-commit-failures
```

### Step 2: Fix test failures first
- Debug why `_process_node` returns None or wrong number of values
- Add proper error handling and default returns

### Step 3: Fix type annotations systematically
- Start with simple missing annotations
- Move to complex type fixes
- Test each fix with mypy locally

### Step 4: Clean up dead code
- Either remove unused variables or prefix with underscore
- Ensure no functionality is broken

### Step 5: Format code
```bash
ruff format tests/characterization/repl/test_repl_initialization.py
```

### Step 6: Verify all fixes
```bash
pre-commit run --all-files
```

### Step 7: Run full test suite
```bash
pytest tests/
```

## Expected Outcome
- All pre-commit hooks pass
- All tests pass
- Code is properly typed and formatted
- No dead code warnings

## Risk Mitigation
- Make atomic commits for each type of fix
- Run tests after each major change
- Keep original functionality intact
- Document any behavioral changes
