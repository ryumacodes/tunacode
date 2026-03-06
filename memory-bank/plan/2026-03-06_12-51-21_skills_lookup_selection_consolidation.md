---
title: "Skills Lookup and Selection Consolidation – Implementation Plan"
phase: Plan
date: "2026-03-06T12:51:21-0600"
owner: "pi"
parent_research: "memory-bank/research/2026-03-06_skills_module_map.md"
git_commit_at_plan: "f7465ade"
tags: [plan, skills, registry, selection, refactor]
---

## Goal

Consolidate TunaCode's skills lookup, load, and selected-skill projection paths so every caller uses one cache-backed resolution flow.

This plan is complete when:

- `selection.py` no longer re-implements case-insensitive discovery or bypasses registry-backed loaded-skill caching
- `/skills loaded`, the Session Inspector, and prompt assembly all consume the same canonical skill names and selection ordering
- missing selected skills still surface clearly in UI display paths while prompt-building remains fail-loud

Out of scope:

- new skill roots or precedence rules
- `/skills` UX changes or new subcommands
- prompt copy rewrites unrelated to lookup consolidation
- session persistence schema changes
- autocomplete ranking changes

## Scope & Assumptions

### In Scope

- Registry-level canonical name resolution for skills
- Selection-path refactor so loaded skill access always goes through registry APIs
- A shared selected-skill summary resolution helper for UI display paths
- `/skills loaded` and Session Inspector adoption of the shared helper
- Regression tests for registry lookup, selection dedupe, UI rendering, and prompt injection invariants

### Out of Scope

- Changes to `src/tunacode/skills/discovery.py` precedence behavior
- Changes to `src/tunacode/skills/loader.py` reference parsing behavior
- Changes to `src/tunacode/core/session/state.py` persistence fields
- Any new automatic skill selection behavior
- Any new prompt sections beyond preserving the existing selected/available blocks

### Assumptions

- `selected_skill_names` remains the persisted source of truth for session attachments
- Existing local-over-global precedence remains unchanged
- UI display paths may show missing selected skills without raising, but prompt assembly must continue to raise on unresolved active skills
- `load_skill_by_name()` remains the correct cache-backed API for fully loaded skills
- The current untracked research document (`?? memory-bank/research/2026-03-06_skills_module_map.md`) is intentional and should not block planning

## Deliverables

- Updated `src/tunacode/skills/registry.py`
- Updated `src/tunacode/skills/selection.py`
- Updated `src/tunacode/skills/models.py`
- Updated `src/tunacode/ui/commands/skills.py`
- Updated `src/tunacode/ui/app.py`
- New `tests/unit/skills/test_registry.py`
- New `tests/unit/skills/test_selection.py`
- New `tests/unit/ui/test_skills_command.py`
- New `tests/unit/ui/test_app_skills_entries.py`
- Updated `tests/unit/core/test_agent_skills_prompt_injection.py`

## Readiness

### Preconditions

- Repository root: `/root/tunacode`
- Planning commit: `f7465ade`
- Research source exists at `memory-bank/research/2026-03-06_skills_module_map.md`
- Working tree at planning time contains one untracked research file:
  - `?? memory-bank/research/2026-03-06_skills_module_map.md`

### Existing Code Anchors

- `src/tunacode/skills/selection.py:11` — duplicated case-insensitive discovered-skill lookup
- `src/tunacode/skills/selection.py:28` — attach flow currently discovers first, then loads directly
- `src/tunacode/skills/selection.py:67` — selected-skill prompt materialization path
- `src/tunacode/skills/registry.py:34` — summary lookup entry point
- `src/tunacode/skills/registry.py:50` — cache-backed full-load entry point
- `src/tunacode/core/agents/agent_components/agent_config.py:439` — prompt-state builder using selected skills
- `src/tunacode/ui/commands/skills.py:135` — attach-or-search route
- `src/tunacode/ui/commands/skills.py:196` — loaded-skills panel row builder
- `src/tunacode/ui/app.py:520` — Session Inspector skill-entry builder
- `tests/unit/core/test_agent_skills_prompt_injection.py:40` — selected-skills prompt block assertions

### Current Validation Gap

- The repository currently has prompt-injection coverage for selected skills, but no source test modules under `tests/unit/skills/` and no checked-in UI tests for `/skills` rendering paths.
- This refactor should add those tests before any broader subsystem change.

## Milestones

### M1: Canonical Lookup Path

Make `registry.py` the only place that resolves skill names to discovered paths for summary and full-load access.

### M2: Shared Selected-Skill Projections

Add one shared selected-skill summary resolution path for display consumers while keeping prompt resolution fail-loud.

### M3: Consumer Adoption and Regression Coverage

Move `/skills loaded`, Session Inspector, and prompt regression tests onto the consolidated helpers.

### M4: Targeted Verification

Run focused formatting and pytest gates for the skills slice and affected UI/core contracts.

## Work Breakdown (Tasks)

### T001: Add a canonical registry resolver for case-insensitive skill lookup

- **Summary**: Add `resolve_discovered_skill(name, *, local_root=None, global_root=None)` to `src/tunacode/skills/registry.py` and reuse it from both `get_skill_summary()` and `load_skill_by_name()` so the case-insensitive local-over-global lookup exists in one place only.
- **Owner**: pi
- **Estimate**: 45 minutes
- **Dependencies**: -
- **Target milestone**: M1
- **Acceptance test**: In `tests/unit/skills/test_registry.py`, a test with local `Demo` and global `demo` asserts that `get_skill_summary("dEmO")` and `load_skill_by_name("DEMO")` both return the local `Demo` record.
- **Files/modules touched**:
  - `src/tunacode/skills/registry.py`
  - `tests/unit/skills/test_registry.py`

### T002: Refactor selection to use registry-backed full loads only

- **Summary**: Remove `_find_discovered_skill_by_name()` from `src/tunacode/skills/selection.py` and replace direct `discover_skills()` / `load_skill()` usage with `get_skill_summary()` and `load_skill_by_name()`, keeping `list_skill_related_paths()` as the only direct loader helper used by selection.
- **Owner**: pi
- **Estimate**: 50 minutes
- **Dependencies**: T001
- **Target milestone**: M1
- **Acceptance test**: In `tests/unit/skills/test_selection.py`, attaching `demo` twice with different casing returns one canonical `Demo` entry and `resolve_selected_skills(["DEMO"])` returns a single selected skill with populated `content` and `related_paths`.
- **Files/modules touched**:
  - `src/tunacode/skills/selection.py`
  - `tests/unit/skills/test_selection.py`

### T003: Add a shared selected-skill summary resolution model and helper

- **Summary**: Add `ResolvedSelectedSkillSummary` to `src/tunacode/skills/models.py` with `requested_name` and `summary` fields, then implement `resolve_selected_skill_summaries()` in `src/tunacode/skills/selection.py` so UI consumers can preserve selection order, use canonical summary names when available, and carry unresolved selections as `summary=None` instead of raising.
- **Owner**: pi
- **Estimate**: 55 minutes
- **Dependencies**: T002
- **Target milestone**: M2
- **Acceptance test**: In `tests/unit/skills/test_selection.py`, resolving `["Demo", "ghost"]` returns two results in the same order, with `summary.name == "Demo"` for the first item and `summary is None` for the second.
- **Files/modules touched**:
  - `src/tunacode/skills/models.py`
  - `src/tunacode/skills/selection.py`
  - `tests/unit/skills/test_selection.py`

### T004: Adopt the shared selected-skill summary helper in `/skills loaded`

- **Summary**: Update `SkillsCommand._build_loaded_skill_rows()` in `src/tunacode/ui/commands/skills.py` to consume `resolve_selected_skill_summaries()` instead of calling `get_skill_summary()` in a per-item loop, while preserving the current `loaded` and `missing` row labels.
- **Owner**: pi
- **Estimate**: 40 minutes
- **Dependencies**: T003
- **Target milestone**: M2
- **Acceptance test**: In `tests/unit/ui/test_skills_command.py`, a session with `selected_skill_names=["demo", "ghost"]` renders one row as `demo`/`local`/`loaded` and one row as `ghost`/`---`/`missing`.
- **Files/modules touched**:
  - `src/tunacode/ui/commands/skills.py`
  - `tests/unit/ui/test_skills_command.py`

### T005: Adopt the shared selected-skill summary helper in the Session Inspector

- **Summary**: Update `TextualReplApp._build_skill_entries()` in `src/tunacode/ui/app.py` to consume `resolve_selected_skill_summaries()` so the inspector uses the same canonical-name and missing-skill logic as `/skills loaded`.
- **Owner**: pi
- **Estimate**: 35 minutes
- **Dependencies**: T003
- **Target milestone**: M2
- **Acceptance test**: In `tests/unit/ui/test_app_skills_entries.py`, building entries from `selected_skill_names=["DEMO", "ghost"]` returns `[('Demo', 'local'), ('ghost', 'missing')]` in that order.
- **Files/modules touched**:
  - `src/tunacode/ui/app.py`
  - `tests/unit/ui/test_app_skills_entries.py`

### T006: Add focused registry and selection regression tests

- **Summary**: Create source test modules under `tests/unit/skills/` that cover canonical lookup, local-over-global precedence, case-insensitive attach dedupe, and selected-skill summary resolution with missing entries.
- **Owner**: pi
- **Estimate**: 60 minutes
- **Dependencies**: T001, T002, T003
- **Target milestone**: M3
- **Acceptance test**: `uv run pytest tests/unit/skills/test_registry.py tests/unit/skills/test_selection.py -q`
- **Files/modules touched**:
  - `tests/unit/skills/test_registry.py`
  - `tests/unit/skills/test_selection.py`

### T007: Add UI regression tests for `/skills loaded` and Session Inspector display

- **Summary**: Add UI tests that verify loaded and missing selected skills render consistently across the `/skills loaded` panel and Session Inspector after the shared selected-skill summary refactor.
- **Owner**: pi
- **Estimate**: 55 minutes
- **Dependencies**: T004, T005
- **Target milestone**: M3
- **Acceptance test**: `uv run pytest tests/unit/ui/test_skills_command.py tests/unit/ui/test_app_skills_entries.py -q`
- **Files/modules touched**:
  - `tests/unit/ui/test_skills_command.py`
  - `tests/unit/ui/test_app_skills_entries.py`

### T008: Extend prompt-injection coverage to protect refactor invariants

- **Summary**: Update `tests/unit/core/test_agent_skills_prompt_injection.py` so prompt-building coverage explicitly proves that case-insensitive selected skill names still resolve to canonical skill paths and that selected-skill prompt content still includes absolute paths and full `SKILL.md` content after the registry-only refactor.
- **Owner**: pi
- **Estimate**: 35 minutes
- **Dependencies**: T002
- **Target milestone**: M3
- **Acceptance test**: `uv run pytest tests/unit/core/test_agent_skills_prompt_injection.py -q`
- **Files/modules touched**:
  - `tests/unit/core/test_agent_skills_prompt_injection.py`

### T009: Run targeted formatting and contract checks for the skills slice

- **Summary**: Run `ruff` and the focused pytest set for the touched skills/UI/core files, including the existing command contract test, before treating the consolidation as ready for execution.
- **Owner**: pi
- **Estimate**: 25 minutes
- **Dependencies**: T006, T007, T008
- **Target milestone**: M4
- **Acceptance test**: `uv run ruff check src/tunacode/skills src/tunacode/ui/commands/skills.py src/tunacode/ui/app.py tests/unit/skills tests/unit/ui/test_skills_command.py tests/unit/ui/test_app_skills_entries.py tests/unit/core/test_agent_skills_prompt_injection.py && uv run pytest tests/unit/skills/test_registry.py tests/unit/skills/test_selection.py tests/unit/ui/test_skills_command.py tests/unit/ui/test_app_skills_entries.py tests/unit/ui/test_command_contracts.py tests/unit/core/test_agent_skills_prompt_injection.py -q`
- **Files/modules touched**:
  - `src/tunacode/skills/registry.py`
  - `src/tunacode/skills/selection.py`
  - `src/tunacode/skills/models.py`
  - `src/tunacode/ui/commands/skills.py`
  - `src/tunacode/ui/app.py`
  - `tests/unit/skills/test_registry.py`
  - `tests/unit/skills/test_selection.py`
  - `tests/unit/ui/test_skills_command.py`
  - `tests/unit/ui/test_app_skills_entries.py`
  - `tests/unit/core/test_agent_skills_prompt_injection.py`

## Risks & Mitigations

- **Risk**: UI display helpers accidentally change prompt-building behavior by making missing selected skills non-fatal everywhere.
  - **Mitigation**: Keep `resolve_selected_skills()` fail-loud for prompt assembly and use `resolve_selected_skill_summaries()` only for display paths.
- **Risk**: Canonical casing changes (`demo` → `Demo`) could alter visible UI output unexpectedly.
  - **Mitigation**: Preserve selection order, display `summary.name` only when a real summary exists, and test loaded vs missing paths explicitly.
- **Risk**: Registry consolidation could skip cache-backed full-load behavior if selection imports low-level loader functions again.
  - **Mitigation**: Make `load_skill_by_name()` the only full-load entry point used by selection and protect it with unit tests.
- **Risk**: New UI tests may become brittle if they depend on full Textual rendering.
  - **Mitigation**: Test row builders and entry builders directly where possible; reserve full app mounting only for behavior that requires it.

## Test Strategy

- Add focused source tests under `tests/unit/skills/` for registry and selection behavior.
- Add one UI test module for `/skills loaded` row generation and one for Session Inspector skill-entry generation.
- Update the existing prompt injection test instead of creating a second overlapping core prompt test file.
- Re-run `tests/unit/ui/test_command_contracts.py` to ensure command-module changes do not break slash-command registration assumptions.

## References

### Research Doc Sections

- `memory-bank/research/2026-03-06_skills_module_map.md` — Summary
- `memory-bank/research/2026-03-06_skills_module_map.md` — Integration Points
- `memory-bank/research/2026-03-06_skills_module_map.md` — Call Chains
- `memory-bank/research/2026-03-06_skills_module_map.md` — Observed Structural Facts

### Key Code References

- `src/tunacode/skills/selection.py:11`
- `src/tunacode/skills/selection.py:28`
- `src/tunacode/skills/selection.py:67`
- `src/tunacode/skills/registry.py:34`
- `src/tunacode/skills/registry.py:50`
- `src/tunacode/ui/commands/skills.py:135`
- `src/tunacode/ui/commands/skills.py:196`
- `src/tunacode/ui/app.py:520`
- `src/tunacode/core/agents/agent_components/agent_config.py:439`
- `tests/unit/core/test_agent_skills_prompt_injection.py:40`

## Final Gate

- **Output summary**: plan path, milestone count, tasks ready
- **Next command**: `/execute "memory-bank/plan/2026-03-06_12-51-21_skills_lookup_selection_consolidation.md"`
