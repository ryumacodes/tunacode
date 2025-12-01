---
title: "Dead Code Removal - Utils Directory Cleanup"
phase: Plan
date: "2025-12-01"
owner: "Agent"
parent_research: "memory-bank/research/2025-12-01_utils-directory-mapping.md"
git_commit_at_plan: "3d9e9cd"
tags: [plan, dead-code, cleanup, utils]
---

## Goal

Remove all dead code from `src/tunacode/utils/` - modules and functions that are not wired into the application. This reduces maintenance burden and clarifies the actual dependency graph.

**Non-goals:** Refactoring alive code, adding features, changing behavior.

## Scope & Assumptions

**In scope:**
- Delete entire unused module files
- Remove dead functions from partially-alive modules
- Clean up stale imports in `__init__.py`

**Out of scope:**
- Test coverage changes
- Documentation updates beyond this plan
- Refactoring alive code

**Assumptions:**
- Research analysis from 2025-12-01 is accurate (verified by 3 sub-agents)
- No dynamic imports exist (grepped for string-based imports - none found)
- Git history preserves deleted code if rollback needed

## Deliverables (DoD)

1. All dead module files removed from filesystem
2. Dead functions removed from partially-alive modules
3. `ruff check` passes
4. Application still runs (`hatch run tunacode --help`)

## Readiness (DoR)

- [x] Research doc complete with module analysis
- [x] Sub-agent verification of imports/usage complete
- [x] Current branch: `textual_repl` (clean working tree except research doc)

## Milestones

- **M1:** Delete entire dead modules (6 files, ~1223 lines)
- **M2:** Clean partial dead code (2 files, ~60 lines)
- **M3:** Verify & commit

## Work Breakdown (Tasks)

### Task 1: Delete Dead Module Files (M1)

**Summary:** Remove 6 entire files with zero imports

| File | Lines | Status |
|------|-------|--------|
| `utils/models_registry.py` | 594 | DEAD - entire module unused |
| `utils/config_comparator.py` | 340 | DEAD - entire module unused |
| `utils/tool_descriptions.py` | 115 | DEAD - duplicate in agent_helpers.py is active |
| `utils/api_key_validation.py` | 93 | DEAD - entire module unused |
| `utils/diff_utils.py` | 70 | DEAD - render_file_diff() never called |
| `utils/text_utils.py` | 223 | DEAD - 0 imports found |
| `utils/import_cache.py` | 11 | DEAD - lazy_import() never used |

**Acceptance:**
- Files deleted from filesystem
- No import errors when running `python -c "import tunacode"`

**Files touched:** 7 files deleted

### Task 2: Clean Dead Functions in Alive Modules (M2)

**Summary:** Remove dead functions from modules that have other alive code

| File | Dead Function | Lines | Keep |
|------|--------------|-------|------|
| `utils/token_counter.py` | `format_token_count()` | 86-92 | `estimate_tokens()`, `get_encoding()` |
| `utils/security.py` | `safe_subprocess_run()` | 121-173 | `validate_command_safety()`, `safe_subprocess_popen()` |

**Acceptance:**
- Dead functions removed
- Alive functions still work

**Files touched:** 2 files edited

### Task 3: Clean Stale Import in agent_components (M2)

**Summary:** Remove unused import of `get_batch_description`

| File | Issue |
|------|-------|
| `core/agents/agent_components/__init__.py:3` | Imports `get_batch_description` but never uses it |

**Acceptance:**
- Import removed
- `__all__` list updated if needed

**Files touched:** 1 file edited

### Task 4: Verify & Commit (M3)

**Summary:** Run lints and verify app works

**Acceptance:**
- `ruff check .` passes
- `python -c "import tunacode"` succeeds
- `hatch run tunacode --help` works
- Git commit with focused diff

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation | Trigger |
|------|--------|------------|------------|---------|
| Dynamic import exists | High | Low | Grep for `importlib`, `__import__` | Import error at runtime |
| Function used via reflection | High | Low | App smoke test | Runtime AttributeError |
| Rollback needed | Medium | Low | All deleted code in git history | Any test failure |

## Test Strategy

- **ONE test:** Run `hatch run tunacode --help` to verify app boots
- No new unit tests needed - we're removing code, not adding

## References

- Research doc: `memory-bank/research/2025-12-01_utils-directory-mapping.md`
- Sub-agent analysis confirming:
  - models_registry.py: DEAD (0 imports)
  - config_comparator.py: DEAD (0 imports)
  - tool_descriptions.py: DEAD (duplicate in agent_helpers.py)
  - api_key_validation.py: DEAD (0 imports)
  - diff_utils.py: DEAD (0 imports)
  - text_utils.py: DEAD (0 imports)
  - import_cache.py: DEAD (0 imports)
  - token_counter.py: PARTIAL (format_token_count dead)
  - security.py: PARTIAL (safe_subprocess_run dead)

---

## Alternative Option

If conservative approach preferred: Delete only the 3 largest dead modules first:
1. `models_registry.py` (594 lines)
2. `config_comparator.py` (340 lines)
3. `text_utils.py` (223 lines)

This removes 1157 lines with minimal risk, leaving smaller modules for later verification.

---

## Summary

| Metric | Value |
|--------|-------|
| Plan path | `memory-bank/plan/2025-12-01_dead-code-removal.md` |
| Milestones | 3 |
| Files to delete | 7 |
| Files to edit | 3 |
| Total dead lines | ~1283 |
| Gates | ruff check, import test, app smoke test |

**Next:** `/execute "memory-bank/plan/2025-12-01_dead-code-removal.md"`
