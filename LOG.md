---
title: Headless Code Removal Log
summary: Change log for the headless code removal work and related cleanup notes.
when_to_read:
  - When tracing headless-mode cleanup history
  - When reviewing prior removal work
last_updated: "2026-04-04"
---

# Headless Code Removal Log

**Date:** 2026-03-29
**Task:** Remove existing headless mode code in preparation for RPC implementation

## Changes Made

### Deleted Files

1. **`src/tunacode/ui/headless/`** (entire directory)
   - `__init__.py` - Module initialization with `resolve_output` export
   - `output.py` - Headless output extraction logic (74 lines)
   - `__pycache__/` - Compiled Python cache

### Modified Files

1. **`src/tunacode/ui/main.py`**
   - Removed import: `from tunacode.ui.headless import resolve_output`
   - Removed unused imports: `import json`, `from tinyagent.agent_types import dump_model_dumpable`
   - Removed unused import: `import os` (only used by `_validate_cwd`)
   - Removed constant: `HEADLESS_NO_RESPONSE_ERROR = "Error: No response generated"`
   - Removed function: `_build_trajectory_json()` - JSON trajectory builder for headless output
   - Removed function: `_print_headless_error()` - Error formatting for headless mode
   - Removed function: `run_headless()` - The `@app.command(name="run")` entry point
   - Removed function: `_validate_cwd()` - Working directory validation (only used by headless)

2. **`tests/system/cli/test_startup.py`**
   - Removed headless-related imports: `AsyncMock`, `MagicMock`, `patch`, `CliRunner`, `subprocess`, `pytest`
   - Removed `json` and `os` imports (no longer needed)
   - Removed constant: `HEADLESS_TIMEOUT_SECONDS = 60`
   - Removed helper: `_build_invalid_config_env()` - Only used by headless tests
   - Removed entire class: `TestHeadlessModeStartup` (7 test methods)
   - Removed entire class: `TestHeadlessModeMocked` (4 test methods)
   - Updated docstring to reflect TUI-only focus

## Verification

All relevant tests pass:

```bash
uv run pytest tests/system/cli/test_startup.py -v
# 4 passed - All TUI initialization tests

uv run pytest tests/test_dependency_layers.py -v
# 1 passed - Dependency layer enforcement
```

## Code Statistics

- **Lines removed:** ~330 (headless module + main.py functions + tests)
- **Files deleted:** 1 directory (2 Python files + cache)
- **Functions removed:** 4
- **Test classes removed:** 2
- **Test methods removed:** 11

## Notes

- This is step 1 of the RPC implementation plan (see `plan.md`)
- The old `tunacode run` command is now completely removed
- Session metadata initialization in `lifecycle.py` was preserved (will be extracted to `session_metadata.py` in step 3)
- TUI mode continues to work through the same `process_request()` core path
- No breaking changes to TUI functionality

## Next Steps (from plan.md)

1. ✅ Remove headless code (completed)
2. Add runtime event types in `types/runtime_events.py`
3. Refactor `RequestOrchestrator` to emit runtime events
4. Extract shared session metadata initialization
5. Adapt TUI to new runtime event flow
6. Build RPC transport/protocol/session
7. Replace tests with RPC tests
8. Update documentation
