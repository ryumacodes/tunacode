---
title: "pr-444 review fixes implementation plan"
link: "pr-444-review-fixes-plan"
type: implementation_plan
ontological_relations:
  - relates_to: [[pr-444-review-findings]]
tags: [plan, pr-444, review-fixes, coding]
uuid: "3de8b04b-b381-4ba1-b5f0-4205feaf6746"
created_at: "2026-03-27T18:59:20+0000"
git_commit_at_plan: "bf6ee510"
source_branch: "qa"
source_pr: "https://github.com/alchemiststudiosDOTai/tunacode/pull/444"
---

## Goal

Fix the two review regressions in PR #444 without expanding scope beyond compatibility restoration:

1. restore fault-tolerant `.gitignore` loading for filesystem listing/filtering paths
2. preserve the public `tunacode.types` import surface for `ModelConfig` and `ModelRegistry`

Out of scope: broader ignore-system redesign, new registry-type migration work, doc-site/user-facing docs updates, or unrelated cleanup in PR #444.

## Scope & Assumptions

- IN scope:
  - restore previous non-fatal behavior when `.gitignore` is unreadable or not UTF-8
  - add regression tests that prove ignore consumers fall back safely
  - reintroduce compatibility exports for `ModelConfig` and `ModelRegistry`
  - add a regression test that proves legacy imports still work from `tunacode.types`
- OUT of scope:
  - changing gitignore matching semantics beyond fault tolerance
  - removing the new typed registry schema introduced in PR #444
  - updating third-party consumers or external packages
- Assumptions:
  - default behavior should remain "use shared ignore defaults even if `.gitignore` cannot be read"
  - compatibility restoration is preferred over forcing downstream callers to migrate immediately
  - `tunacode.types` remains a backward-compatible public facade

## Deliverables

- Shared ignore loader that safely falls back when `.gitignore` is missing, unreadable, or undecodable
- Regression tests for `list_cwd`, `FileFilter`, and `IgnoreManager`-level `.gitignore` reads under failure conditions
- Restored `ModelConfig` and `ModelRegistry` definitions or aliases in the public types surface
- Regression test proving `from tunacode.types import ModelConfig, ModelRegistry` succeeds

## Readiness

- Preconditions:
  - branch `qa` is checked out
  - working tree is clean before implementation starts
  - PR #444 diff is the active target
- Existing repro evidence:
  - `list_cwd()` raises `PermissionError` when `.gitignore` is unreadable
  - `FileFilter(...)` construction raises `UnicodeDecodeError` when `.gitignore` contains invalid UTF-8 bytes
  - `from tunacode.types import ModelConfig, ModelRegistry` raises `ImportError` on PR head

## Milestones

- M1: Restore safe ignore-file loading contract
- M2: Add regression tests for ignore fault tolerance
- M3: Restore public type compatibility exports
- M4: Add regression coverage for compatibility and run targeted validation

## Work Breakdown (Tasks)

### T001: Restore shared ignore-file fallback behavior

**Summary**: Change the shared ignore-file reader so all callers fall back to empty extra patterns when `.gitignore` is absent, unreadable, or undecodable.

**Owner**: backend

**Estimate**: 45m

**Dependencies**: none

**Target milestone**: M1

**Acceptance test**: constructing `FileFilter` with an invalid-UTF8 `.gitignore` does not raise and still returns non-ignored files

**Files/modules touched**:
- src/tunacode/configuration/ignore_patterns.py

**Steps**:
1. Update `read_ignore_file_lines()` in `src/tunacode/configuration/ignore_patterns.py` to catch `PermissionError` and `UnicodeDecodeError` in addition to `FileNotFoundError`.
2. Return the existing empty-pattern constant on those failures instead of propagating the exception.
3. Keep the helper signature unchanged so existing callers in `utils.system.gitignore`, `infrastructure.file_filter`, and `tools.ignore_manager` continue using the shared path unchanged.
4. Keep any fallback behavior narrow: do not swallow unrelated exceptions beyond filesystem-access and text-decoding failures.

### T002: Add ignore fault-tolerance regression tests

**Summary**: Add focused tests proving ignore consumers keep working when `.gitignore` cannot be read as text.

**Owner**: backend

**Estimate**: 1.5h

**Dependencies**: T001

**Target milestone**: M2

**Acceptance test**: `uv run pytest tests/unit/configuration/test_ignore_patterns.py tests/unit/infrastructure/test_file_filter.py tests/unit/utils/test_gitignore.py -q`

**Files/modules touched**:
- tests/unit/configuration/test_ignore_patterns.py
- tests/unit/infrastructure/test_file_filter.py
- tests/unit/utils/test_gitignore.py
- tests/unit/tools/test_ignore_manager.py

**Steps**:
1. Extend `tests/unit/configuration/test_ignore_patterns.py` with a case showing `read_ignore_file_lines()` returns an empty tuple when `.gitignore` bytes are invalid UTF-8.
2. Add a `FileFilter` regression test that writes invalid bytes to `.gitignore`, constructs the filter, and confirms normal visible files are still listed.
3. Add a `list_cwd()` regression test that simulates an unreadable `.gitignore` and asserts listing still succeeds.
4. Add an `IgnoreManager` regression test if a unit-test file already exists for that module; otherwise create `tests/unit/tools/test_ignore_manager.py` with one targeted case covering `read_gitignore_lines()`.
5. Keep each new test narrow and single-purpose; do not add broad filesystem matrix coverage.

### T003: Restore `tunacode.types` compatibility exports

**Summary**: Reintroduce `ModelConfig` and `ModelRegistry` on the public types facade so existing imports continue to resolve.

**Owner**: backend

**Estimate**: 45m

**Dependencies**: none

**Target milestone**: M3

**Acceptance test**: `uv run python - <<'PY'` import check for `from tunacode.types import ModelConfig, ModelRegistry`

**Files/modules touched**:
- src/tunacode/types/dataclasses.py
- src/tunacode/types/__init__.py

**Steps**:
1. Restore a backward-compatible definition for `ModelConfig` in `src/tunacode/types/dataclasses.py`.
2. Restore a backward-compatible definition or alias for `ModelRegistry` in the same module.
3. Re-export both names from `src/tunacode/types/__init__.py`.
4. Keep the PR’s new registry-specific TypedDict exports intact; this task is additive compatibility, not rollback.
5. If the restored types are legacy-only, document that with a short comment rather than removing them again.

### T004: Add compatibility regression coverage and targeted validation

**Summary**: Add one import-surface regression test and run the minimum targeted checks covering both restored behaviors.

**Owner**: backend

**Estimate**: 1h

**Dependencies**: T002, T003

**Target milestone**: M4

**Acceptance test**: all targeted compatibility tests pass in one pytest invocation

**Files/modules touched**:
- tests/unit/types/test_public_type_exports.py

**Steps**:
1. Add `tests/unit/types/test_public_type_exports.py` with one test importing `ModelConfig` and `ModelRegistry` from `tunacode.types`.
2. Assert the imported names are the expected objects or aliases, not just that the import statement parses.
3. Run a targeted pytest command covering:
   - `tests/unit/configuration/test_ignore_patterns.py`
   - `tests/unit/infrastructure/test_file_filter.py`
   - `tests/unit/utils/test_gitignore.py`
   - the IgnoreManager test file touched in T002
   - `tests/unit/types/test_public_type_exports.py`
4. Run one direct Python import smoke check for `from tunacode.types import ModelConfig, ModelRegistry`.

## Risks & Mitigations

- Risk: catching too many exceptions in ignore loading could hide genuine bugs.
  - Mitigation: only catch `FileNotFoundError`, `PermissionError`, and `UnicodeDecodeError`.
- Risk: compatibility restoration could conflict with the new typed-registry work conceptually.
  - Mitigation: keep restored dataclass exports explicitly legacy-compatible and separate from the new registry schema types.
- Risk: permission-based tests may be flaky on some environments.
  - Mitigation: prefer invalid-UTF8 test coverage as the primary deterministic path; use permission mutation only where the local test harness supports it.

## Test Strategy

- One targeted regression per behavior change.
- Prefer deterministic local-file fixtures over environment-dependent setups.
- Do not run full-suite validation until targeted compatibility tests pass.

## References

- Review target: [PR #444](https://github.com/alchemiststudiosDOTai/tunacode/pull/444)
- Shared ignore reader: [src/tunacode/configuration/ignore_patterns.py](/Users/tuna/Desktop/tunacode/src/tunacode/configuration/ignore_patterns.py#L102)
- File listing caller: [src/tunacode/utils/system/gitignore.py](/Users/tuna/Desktop/tunacode/src/tunacode/utils/system/gitignore.py#L37)
- File filter caller: [src/tunacode/infrastructure/file_filter.py](/Users/tuna/Desktop/tunacode/src/tunacode/infrastructure/file_filter.py#L37)
- Ignore manager caller: [src/tunacode/tools/ignore_manager.py](/Users/tuna/Desktop/tunacode/src/tunacode/tools/ignore_manager.py#L50)
- Public types facade: [src/tunacode/types/__init__.py](/Users/tuna/Desktop/tunacode/src/tunacode/types/__init__.py#L86)
- Removed legacy dataclasses: [src/tunacode/types/dataclasses.py](/Users/tuna/Desktop/tunacode/src/tunacode/types/dataclasses.py#L1)

## Final Gate

- Output summary:
  - plan path: `.artifacts/plan/2026-03-27_13-59-15_pr-444-review-fixes/PLAN.md`
  - milestones: 4
  - tasks: 4
  - git state at planning: `bf6ee510`
- Next step: execute this plan on branch `qa`, keeping the changes limited to compatibility restoration for the two review findings
