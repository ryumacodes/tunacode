# Small Wins Audit Report

**Repository:** tunacode
**Version:** 0.1.2
**Branch:** master (clean)
**Commit:** 2013dde
**Date:** 2025-12-05
**Scope:** Read-only detection and documentation

---

## 1. Executive Summary (Top Quick Wins)

| # | Win | Effort | Impact | Files |
|---|-----|--------|--------|-------|
| 1 | Fix version mismatch in pyproject.toml (line 178: 0.1.1 -> 0.1.2) | XS | L | 1 |
| 2 | Fix mypy python_version (3.10 -> 3.11) | XS | M | 1 |
| 3 | Delete orphaned `.claude/` dirs in src/ | XS | M | 2 dirs |
| 4 | Remove unused `state_transition.py` (117 lines dead code) | S | M | 1 |
| 5 | Remove unused constants in `constants.py` | S | S | 1 |
| 6 | Rename duplicate `FileFilter` classes for clarity | S | M | 2 |
| 7 | Flatten `ui/commands/` directory (single file in dir) | XS | S | 1 dir |

**Total estimated cleanup time:** ~45 minutes for all wins

---

## 2. Findings by Category

### A. Structure & Naming

#### A.1 Orphaned Configuration Directories (MEDIUM)
**Issue:** Nested `.claude/` directories inside source tree
- `/root/tunacode/src/tunacode/.claude/settings.local.json`
- `/root/tunacode/src/tunacode/core/.claude/settings.local.json`

**Problem:** Config files should only exist at repo root
**Fix:** Delete both directories - only root `.claude/` should exist

#### A.2 Duplicate Class Names (HIGH)
**Issue:** Two `FileFilter` classes with different purposes
- `src/tunacode/tools/grep_components/file_filter.py` - Glob-based filtering for grep
- `src/tunacode/utils/ui/file_filter.py` - Gitignore-aware autocomplete filtering

**Problem:** Same class name, different functionality, potential import confusion
**Fix:** Rename to `GlobFilter` and `GitignoreFileFilter` respectively

#### A.3 Directory Could Be Flattened (LOW)
**Issue:** `src/tunacode/ui/commands/` contains only `__init__.py` with all code inline
**Fix:** Either flatten to `ui/commands.py` or split into individual command files

#### A.4 Vague Helper Naming (LOW)
Multiple "helpers" files with vague names:
- `utils/ui/helpers.py` -> Consider `utils/ui/formatting.py`
- `core/agents/agent_components/agent_helpers.py` -> Consider `message_factory.py`
- `tools/xml_helper.py` -> Consider `prompt_loader.py`

### B. Dead Code & Orphans

#### B.1 Completely Unused Module (HIGH)
**File:** `/root/tunacode/src/tunacode/core/agents/agent_components/state_transition.py`
**Lines:** 117 lines
**Content:** Full state machine implementation never imported anywhere
- `InvalidStateTransitionError` (lines 14-21)
- `StateTransitionRules` (lines 24-37)
- `AgentStateMachine` (lines 40-106)
- `AGENT_TRANSITION_RULES` (lines 109-116)

**Fix:** Either integrate into agent logic or delete entirely

#### B.2 Unused Constants (MEDIUM)
**File:** `/root/tunacode/src/tunacode/constants.py`

Backward-compat constants never used externally:
- Line 59: `TOOL_REACT = ToolName.REACT`
- Line 60: `TOOL_RESEARCH_CODEBASE = ToolName.RESEARCH_CODEBASE`

Unused command-related constants:
- Line 77: `CMD_DUMP = "/dump"`
- Line 86: `DESC_DUMP = "Show the current conversation history"`
- Line 89: `DESC_MODEL_SWITCH = "Switch to a specific model"`
- Line 90: `DESC_MODEL_DEFAULT = "Set a model as the default"`
- Lines 95-100: `COMMAND_CATEGORIES` dict

**Fix:** Remove these constants after verifying no external usage

#### B.3 Empty/Minimal `__init__.py` Files (LOW)
- `src/tunacode/configuration/__init__.py` - Only contains `# Config package` comment
- `src/tunacode/tools/utils/__init__.py` - Only docstring, no exports

**Fix:** Either add `__all__` exports or leave truly empty

### C. Lint & Config Drifts

#### C.1 Version Mismatch (CRITICAL)
**File:** `/root/tunacode/pyproject.toml`
- Line 8: `version = "0.1.2"` (correct)
- Line 178: `version = "0.1.1"` in hatch scripts (stale)

**Fix:** Update line 178 to `"0.1.2"`

#### C.2 Python Version Mismatch (HIGH)
**File:** `/root/tunacode/pyproject.toml`
- Line 12: `requires-python = ">=3.11,<3.14"`
- Line 143: `python_version = "3.10"` in mypy config

**Fix:** Update mypy `python_version` to `"3.11"`

#### C.3 Linter Status
- **ruff check:** All checks passed
- **ruff format:** 119 files already formatted
- **TODO/FIXME in source:** None found (only in example XML prompts)

### D. Test Gaps

#### D.1 Current Test Coverage
```
tests/
  conftest.py          - Shared fixtures
  __init__.py          - Package marker
  test_compaction.py   - Compaction logic tests
  test_tool_decorators.py - Tool decorator tests
  test_tool_conformance.py - Tool conformance tests
```

**Coverage:** 5 test files for 107+ source files (~5% file coverage)

#### D.2 Untested Critical Modules
| Module | Lines | Risk |
|--------|-------|------|
| `tools/bash.py` | 231 | HIGH - Security critical |
| `core/agents/main.py` | 563 | HIGH - Core logic |
| `tools/update_file.py` | ~200 | MEDIUM - File mutations |
| `tools/write_file.py` | ~150 | MEDIUM - File creation |
| `ui/main.py` | ~400 | MEDIUM - Entry point |

**Note:** Per CLAUDE.md, minimal tests are intentional during rewrite phase

---

## 3. Per-File Suggestions

| Path | Issue | Action | Risk | Effort |
|------|-------|--------|------|--------|
| `pyproject.toml:178` | Stale version | Change 0.1.1 -> 0.1.2 | None | XS |
| `pyproject.toml:143` | Wrong python_version | Change 3.10 -> 3.11 | None | XS |
| `src/tunacode/.claude/` | Orphaned config | Delete directory | None | XS |
| `src/tunacode/core/.claude/` | Orphaned config | Delete directory | None | XS |
| `core/agents/agent_components/state_transition.py` | Dead code | Delete file | Low | S |
| `constants.py:59-60` | Unused exports | Remove lines | Low | XS |
| `constants.py:77,86,89-90,95-100` | Unused constants | Remove lines | Low | XS |
| `tools/grep_components/file_filter.py` | Confusing name | Rename class to GlobFilter | Low | S |
| `utils/ui/file_filter.py` | Confusing name | Rename to GitignoreFileFilter | Low | S |
| `ui/commands/__init__.py` | Dir structure | Flatten to commands.py | Low | S |
| `configuration/__init__.py` | Useless comment | Remove or add exports | None | XS |

---

## 4. Guardrails & Next Steps

### Batch 1: Config Fixes (10 min, 1 file)
1. Fix `pyproject.toml` version mismatch (line 178)
2. Fix `pyproject.toml` mypy python_version (line 143)
3. Commit: "fix: align pyproject.toml versions and mypy config"

### Batch 2: Orphan Cleanup (5 min, 2 dirs)
1. Delete `src/tunacode/.claude/`
2. Delete `src/tunacode/core/.claude/`
3. Commit: "chore: remove orphaned .claude config directories"

### Batch 3: Dead Code Removal (15 min, 2 files)
1. Delete `state_transition.py`
2. Remove unused constants from `constants.py`
3. Run `ruff check .` to verify no import errors
4. Commit: "chore: remove unused state_transition module and stale constants"

### Batch 4: Naming Clarity (20 min, 2+ files)
1. Rename `FileFilter` classes for disambiguation
2. Update all imports
3. Run tests: `hatch run test`
4. Commit: "refactor: disambiguate FileFilter class names"

### Rules for Each PR
- Max 10 files per PR
- Max 30 minutes implementation time
- Add tests if deleting functional code
- Run full test suite before merge

---

## 5. Positive Findings

What's working well:
1. All Python files follow snake_case convention
2. No TODO/FIXME debt in source code (only in example prompts)
3. ruff linting passes with no issues
4. All 119 files properly formatted
5. Clean package structure with proper `__all__` declarations
6. Lazy loading implemented for performance in `tools/__init__.py`
7. Authorization subsystem is complete and well-organized
8. No circular dependencies detected
9. Security validation in bash.py is comprehensive (lines 105-161)
10. Early return pattern consistently used throughout

---

## Validation

- Repository state: Clean (no uncommitted changes)
- This report: READ-ONLY - no modifications performed
- Report location: `reports/SMALL_WINS_AUDIT.md`
