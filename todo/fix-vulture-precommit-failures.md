# Fix Vulture Pre-commit Hook Failures

## Overview
The vulture dead code detection pre-commit hook is failing due to unused variables, parameters, and imports. This document outlines the files and specific locations that need fixes.

## Files and Locations to Fix

### 1. Abstract Method Parameters - `force_setup`
**Files:**
- `src/tunacode/core/setup/agent_setup.py`
  - Line 25: `async def should_run(self, force_setup: bool = False) -> bool:`
  - Line 29: `async def execute(self, force_setup: bool = False) -> None:`

- `src/tunacode/core/setup/base.py`
  - Line 25: `async def should_run(self, force_setup: bool = False) -> bool:`
  - Line 30: `async def execute(self, force_setup: bool = False) -> None:`

**Fix:** Change parameter name from `force_setup` to `_force_setup`

### 2. Abstract Method Parameters - `force`
**File:**
- `src/tunacode/core/setup/git_safety_setup.py`
  - Line 35: `async def should_run(self, force: bool = False) -> bool:`
  - Line 40: `async def execute(self, force: bool = False) -> None:`

**Fix:** Change parameter name from `force` to `_force`

### 3. Abstract Method Parameters - `args`
**Files:**
- `src/tunacode/cli/commands/base.py`
  - Line 47: `async def execute(self, args: CommandArgs, context: CommandContext) -> CommandResult:`

- `src/tunacode/types.py`
  - Line 108: `async def __call__(self, *args, **kwargs) -> str: ...`

**Fix:** Change parameter name from `args` to `_args`

### 4. Callback Function Parameters - `node`
**Files:**
- `src/tunacode/cli/commands/implementations/debug.py`
  - Line 172: `def tool_callback_with_state(part, node):`

- `src/tunacode/cli/repl.py`
  - Line 210: `def tool_callback_with_state(part, node):`
  - Line 282: `def tool_callback_with_state(part, node):`

**Fix:** Change parameter name from `node` to `_node`

### 5. Unused Variables
**Files:**
- `src/tunacode/core/logging/__init__.py`
  - Line 18: `def emit(self, record):`
  - **Fix:** Change `record` to `_record` (it's a stub implementation)

- `src/tunacode/core/logging/config.py`
  - Line 35: `def load(config_path=None):`
  - **Fix:** Remove the unused `config_path` parameter or use it

### 6. Unused Import
**File:**
- `src/tunacode/core/state.py`
  - Line 25: `from tunacode.core.tool_handler import ToolHandler`
  - **Note:** This is in a TYPE_CHECKING block and IS used for type hints on lines 97, 104, 107
  - **Fix:** Keep as-is, this is a false positive

## Implementation Strategy

1. Use underscore prefix (`_`) for intentionally unused parameters in abstract methods and callbacks
2. This maintains the interface contract while signaling to vulture that the parameter is intentionally unused
3. No need for `del` statements or complex whitelist files
4. The underscore convention is Pythonic and widely understood

## Verification
After making changes, run:
```bash
pre-commit run vulture-changed --all-files
```

## Notes
- The `_` prefix is the standard Python convention for unused variables
- This approach is cleaner than using `# noqa` comments or whitelist files
- All fixes maintain backward compatibility since parameter names don't affect the API
