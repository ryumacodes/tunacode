# Research – Core Directory Empty/Unused Directories Cleanup
**Date:** 2025-12-02
**Owner:** Claude Agent
**Phase:** Research

## Goal
Identify empty or unused directories in `src/tunacode/core/` that should be deleted as part of the ongoing rewrite.

## Findings

### Directories to Delete

| Directory | Status | Reason |
|-----------|--------|--------|
| `src/tunacode/core/llm/` | **EMPTY** | Contains only empty `__init__.py` (0 bytes). No imports found anywhere in codebase. |
| `src/tunacode/core/background/` | **UNUSED** | Contains `manager.py` with `BackgroundTaskManager` class, but NO imports anywhere. Dead code. |

### Directory Details

#### 1. `core/llm/` - DELETE
- **Contents:** Only `__init__.py` (empty file, 0 bytes)
- **Imports found:** None
- **Action:** Safe to delete entirely

#### 2. `core/background/` - DELETE
- **Contents:**
  - `__init__.py` (empty)
  - `manager.py` (37 lines - `BackgroundTaskManager` class)
- **Imports found:** None - `BackgroundTaskManager` and `BG_MANAGER` are never imported
- **Action:** Safe to delete entirely - dead code from previous architecture

### Directories to Keep

| Directory | Status | Reason |
|-----------|--------|--------|
| `core/agents/` | **ACTIVE** | Contains main agent logic (`main.py`, `utils.py`, etc.) |
| `core/agents/agent_components/` | **ACTIVE** | Contains 14 active modules for agent processing |
| `core/logging/` | **ACTIVE** | Contains logging config, formatters, handlers |

## Key Patterns / Solutions Found

- **Verification method:** Used `grep -r` to search for any imports of these modules - zero results confirms dead code
- **Empty detection:** Directory with only `__init__.py` (empty file) indicates placeholder that was never implemented

## Recommended Deletion Commands

```bash
# Remove empty llm directory
rm -rf src/tunacode/core/llm/

# Remove unused background directory
rm -rf src/tunacode/core/background/
```

## Knowledge Gaps

- Unknown: Original intent for `llm/` directory (possibly planned LLM abstraction layer?)
- Unknown: Why `BackgroundTaskManager` was created but never integrated

## References

- `src/tunacode/core/llm/__init__.py` - empty file
- `src/tunacode/core/background/manager.py` - unused BackgroundTaskManager class
