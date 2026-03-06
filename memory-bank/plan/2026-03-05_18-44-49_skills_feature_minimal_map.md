---
title: "Skills Feature – Minimal Implementation Plan"
phase: Plan
date: "2026-03-05T18:44:49"
owner: "pi"
parent_research: "memory-bank/research/2026-03-05_skills_feature_minimal_map.md"
git_commit_at_plan: "6cab24a2"
tags: [plan, skills, tunacode, lazy-loading, slash-command]
---

## Goal

Add a minimal TunaCode skills subsystem that:

- discovers skills from project-local `.claude/skills/` and user-global `~/.claude/skills/`
- exposes only `name` + `description` at startup
- injects full `SKILL.md` content only after `/skill <name>` selection
- keeps selected skills attached for later requests in the same session
- shows attached skills in the UI so the user can verify what is active

## Scope & Assumptions

### In Scope

- Skill discovery from local and global roots with local-over-global precedence
- Metadata-only startup load (`name`, `description`, source, absolute paths)
- Lazy full-file load for explicitly selected skills
- Slash command `/skill` for listing, selecting, and clearing attached skills
- Session persistence for selected skills so they remain attached after load/resume
- Prompt assembly changes so available skills are advertised by metadata and selected skills inject full instructions
- Fail-loud validation for malformed or missing skills
- Unit and integration tests for discovery, loading, selection, prompt attachment, and UI command behavior

### Out of Scope

- Remote skill registries or network sync
- Skill execution as a tool call
- Generic natural-language auto-routing that attaches full skills without `/skill`
- Background file watchers for skills; discovery can rescan roots on demand
- New core dependencies

### Assumptions

- Minimal startup behavior means TunaCode may scan skill roots and parse only `name`/`description`; it must not eagerly load full `SKILL.md` bodies
- Selected skills should remain attached for the rest of the session until cleared explicitly or the session is reset
- Discovery root scans are cheap enough to run per request/command; file-content caching should be applied to `SKILL.md` reads, not to root traversal
- The UI should show active skills in the Session Inspector, not the status bar, to preserve a stable NeXTSTEP-style information hierarchy
- When a selected skill later becomes invalid or disappears, TunaCode must fail loudly instead of silently falling back to the global copy or silently detaching it

## Deliverables

- `src/tunacode/skills/__init__.py`
- `src/tunacode/skills/models.py`
- `src/tunacode/skills/discovery.py`
- `src/tunacode/skills/loader.py`
- `src/tunacode/skills/registry.py`
- `src/tunacode/skills/selection.py`
- `src/tunacode/skills/prompting.py`
- `src/tunacode/infrastructure/cache/caches/skills.py`
- `src/tunacode/ui/commands/skill.py`
- Modified `src/tunacode/core/session/state.py`
- Modified `src/tunacode/core/agents/agent_components/agent_config.py`
- Modified `src/tunacode/ui/commands/__init__.py`
- Modified `src/tunacode/ui/context_panel.py`
- Modified `src/tunacode/ui/app.py`
- Tests under `tests/unit/skills/`, `tests/unit/ui/`, and `tests/integration/core/`

## Readiness

### Preconditions

- Current repository commit: `6cab24a2`
- Research source exists at `memory-bank/research/2026-03-05_skills_feature_minimal_map.md`
- Existing slash-command framework exists in `src/tunacode/ui/commands/__init__.py`
- Existing session persistence exists in `src/tunacode/core/session/state.py`
- Existing prompt assembly exists in `src/tunacode/core/agents/agent_components/agent_config.py`

### Existing Code Anchors

- `src/tunacode/core/agents/agent_components/agent_config.py:160` loads the system prompt
- `src/tunacode/core/agents/agent_components/agent_config.py:182` loads `AGENTS.md`
- `src/tunacode/core/agents/agent_components/agent_config.py:425-496` builds and sets the final agent system prompt
- `src/tunacode/ui/commands/__init__.py:24-56` registers and dispatches slash commands
- `src/tunacode/ui/app.py:317-326` routes editor submission into command handling vs agent requests
- `src/tunacode/core/session/state.py:37-78` defines session state
- `src/tunacode/core/session/state.py:309-388` saves and reloads persisted session data
- `src/tunacode/ui/context_panel.py:27-71` builds Session Inspector fields
- `src/tunacode/ui/widgets/command_autocomplete.py:11-52` reads command registry metadata automatically

### Constraints

- Preserve current behavior when no skill is selected, except for adding the lightweight available-skills metadata block to the agent prompt
- Keep diffs small and layered: discovery/loader first, runtime wiring second, UI last
- Fail fast on malformed local skills; do not silently drop to global fallback when the local override is broken

## Milestones

### M1: Skill Domain Types and Discovery

Add explicit types plus deterministic filesystem discovery with local-over-global precedence.

### M2: Lazy Loading and File Cache

Load only skill summaries at startup; load full `SKILL.md` content on demand with mtime-aware caching.

### M3: Session and Prompt Attachment

Persist selected skill names, render metadata and attached skill prompt blocks, and include skill state in agent cache invalidation.

### M4: `/skill` Command and UI Visibility

Add a slash command for selecting skills and show active skills in the Session Inspector.

### M5: Verification

Prove precedence, lazy loading, persistence, prompt attachment, and command behavior with unit and integration tests.

## Work Breakdown (Tasks)

| ID | Task | Owner | Estimate | Dependencies | Milestone | Acceptance Test | Files Touched |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Define explicit skill dataclasses and enums for source, summary, loaded content, and selected attachment state | pi | 25min | - | M1 | Importing `SkillSummary`, `LoadedSkill`, and `SelectedSkill` from `tunacode.skills.models` succeeds and each type constructs with explicit fields only | `src/tunacode/skills/__init__.py`, `src/tunacode/skills/models.py` |
| T002 | Implement root discovery for `.claude/skills/` and `~/.claude/skills/`, detect same-root duplicates, and apply deterministic local-over-global precedence | pi | 50min | T001 | M1 | Given matching `local/demo/SKILL.md` and `global/demo/SKILL.md`, discovery returns only the local entry for `demo` | `src/tunacode/skills/discovery.py` |
| T003 | Write discovery tests covering local-only, global-only, local override, and ignore-without-`SKILL.md` cases | pi | 35min | T002 | M1 | `uv run pytest tests/unit/skills/test_discovery.py` passes with four fixtures proving the discovery matrix | `tests/unit/skills/test_discovery.py` |
| T004 | Implement a summary/full loader that parses only `name` and `description` for startup metadata, then lazily loads full `SKILL.md` content only on explicit selection | pi | 55min | T001 | M2 | Loading summary metadata for a valid skill returns `name` and `description` without returning the full markdown body text | `src/tunacode/skills/loader.py` |
| T005 | Add fail-loud full-load validation for missing `SKILL.md`, malformed frontmatter, and missing referenced relative files resolved against the skill directory | pi | 45min | T004 | M2 | Loading a skill whose `SKILL.md` references a missing relative file raises a typed error instead of returning partial content | `src/tunacode/skills/loader.py` |
| T006 | Add an mtime-aware skill cache plus high-level registry APIs for list/get/load operations that rescan roots but cache individual file reads | pi | 60min | T002, T004, T005 | M2 | After editing a selected skill’s `SKILL.md`, the next registry load returns updated content without restarting TunaCode | `src/tunacode/infrastructure/cache/caches/skills.py`, `src/tunacode/skills/registry.py` |
| T007 | Extend session state and session persistence to store selected skill names and their stable attachment order across save/load cycles | pi | 45min | T001, T006 | M3 | Saving a session with selected skills `['nextstep-ui', 'foo']` and reloading it restores the same ordered selection list | `src/tunacode/core/session/state.py` |
| T008 | Implement selection and prompt rendering helpers that build (a) a startup available-skills metadata block with only name/description and (b) a selected-skills block containing full `SKILL.md` bodies in stable order | pi | 60min | T006, T007 | M3 | Rendering a prompt with one selected skill includes all available summaries but injects full markdown only for the selected skill name | `src/tunacode/skills/selection.py`, `src/tunacode/skills/prompting.py` |
| T009 | Integrate skills into agent construction by appending metadata and selected-skill prompt blocks, updating the agent cache version/fingerprint with selected skill state, and failing loudly when a persisted selection no longer resolves | pi | 70min | T007, T008 | M3 | A mocked `get_or_create_agent()` call produces a system prompt that always contains skill summaries and contains full `SKILL.md` text only after `/skill demo` has been selected | `src/tunacode/core/agents/agent_components/agent_config.py` |
| T010 | Add `/skill` slash command with three explicit behaviors: `/skill` lists available skills, `/skill <name>` attaches one skill, and `/skill clear` removes all attached skills | pi | 60min | T006, T007 | M4 | Running `/skill demo` updates session selection and emits a visible confirmation that includes `demo` and its source (`local` or `global`) | `src/tunacode/ui/commands/skill.py`, `src/tunacode/ui/commands/__init__.py` |
| T011 | Add a dedicated `Skills` field to the Session Inspector and refresh it from the app so active skills are always visible without overloading the status bar | pi | 55min | T007, T010 | M4 | With two selected skills, the Session Inspector shows `Skills [2]` and lists both entries in sorted stable order with their source labels | `src/tunacode/ui/context_panel.py`, `src/tunacode/ui/app.py` |
| T012 | Add UI command tests covering registration, help visibility, autocomplete compatibility, and `/skill` command state changes | pi | 45min | T010, T011 | M4 | `uv run pytest tests/unit/ui/test_skill_command.py tests/unit/ui/test_command_contracts.py` passes and includes `/skill` in the command registry contract | `tests/unit/ui/test_skill_command.py`, `tests/unit/ui/test_command_contracts.py` |
| T013 | Add integration tests for prompt attachment, local-over-global override, and selected-skill persistence across a saved/resumed session | pi | 70min | T009, T010, T011 | M5 | `uv run pytest tests/integration/core/test_skills_integration.py` passes proving override precedence and persisted attachment state | `tests/integration/core/test_skills_integration.py` |
| T014 | Run formatting and targeted verification for the new skills slice, then run the project gates required for feature completion | pi | 30min | T003, T006, T012, T013 | M5 | `ruff check --fix .`, `uv run pytest`, and `uv run python scripts/run_gates.py` complete without skills-related failures | repository-wide |

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Startup prompt metadata changes model behavior unexpectedly | Medium | Keep the metadata block minimal, deterministic, and limited to `name` + `description`; do not inject full skill text until explicit selection |
| Persisted selected skills can break future sessions if files disappear | High | Resolve selected skills during agent creation and fail loudly with the missing skill name and expected path |
| Cache invalidation misses add/remove events | Medium | Re-scan skill roots on each registry query and cache only per-file reads, not root listings |
| Relative-path validation becomes heuristic and flaky | Medium | Restrict validation to explicit relative path tokens defined by the loader contract and raise on ambiguous malformed input |
| UI signal becomes noisy if active skills are shown in multiple places | Low | Show active skills in one dedicated Session Inspector field and emit a concise chat confirmation only on command execution |

## Test Strategy

- `tests/unit/skills/test_discovery.py` for root traversal and precedence
- `tests/unit/skills/test_loader.py` for summary parsing, lazy full load, and fail-loud validation
- `tests/unit/skills/test_registry.py` for cache invalidation and stable list/get behavior
- `tests/unit/ui/test_skill_command.py` for `/skill`, `/skill clear`, and missing-skill handling
- `tests/integration/core/test_skills_integration.py` for end-to-end prompt attachment, override precedence, and session persistence
- Re-run existing command contract tests to prove slash-command compatibility is preserved

## References

### Research

- `memory-bank/research/2026-03-05_skills_feature_minimal_map.md`

### Code References

- `src/tunacode/core/agents/agent_components/agent_config.py:160` — current system-prompt load
- `src/tunacode/core/agents/agent_components/agent_config.py:182` — current `AGENTS.md` load
- `src/tunacode/core/agents/agent_components/agent_config.py:425-496` — final prompt assembly and agent creation
- `src/tunacode/ui/commands/__init__.py:24-56` — slash-command registry/dispatch
- `src/tunacode/ui/app.py:317-326` — editor submission routing
- `src/tunacode/core/session/state.py:37-78` — session dataclass
- `src/tunacode/core/session/state.py:309-388` — save/load persistence
- `src/tunacode/ui/context_panel.py:27-71` — Session Inspector composition
- `src/tunacode/ui/widgets/command_autocomplete.py:11-52` — command autocomplete based on registry
- `src/tunacode/infrastructure/cache/caches/tunacode_context.py:1-45` — existing mtime-aware cache pattern to mirror

## Final Gate

**Output Summary:**

- Plan path: `memory-bank/plan/2026-03-05_18-44-49_skills_feature_minimal_map.md`
- Milestones: 5
- Tasks: 14 ready for coding
- Git state at planning: `6cab24a2` plus untracked research file

**Next Command:**

```bash
/execute "memory-bank/plan/2026-03-05_18-44-49_skills_feature_minimal_map.md"
```
