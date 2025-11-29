---
title: "Textual TUI Architecture Refactor - Plan"
phase: Plan
date: "2025-11-29T17:20:38-06:00"
owner: "claude-opus"
parent_research: "memory-bank/research/2025-11-29_textual-tui-architecture-diagrams.md"
git_commit_at_plan: "fa89d57"
tags: [plan, textual, tui, refactor, architecture, coding]
---

# Textual TUI Architecture Refactor - Implementation Plan

## Goal

- **ONE singular outcome**: Extract the 478-line `textual_repl.py` "junk drawer" into a clean, separated-concerns architecture where widgets, screens, theme, and completion logic live in their proper conceptual homes.

### Non-goals

- No deployment/ops work
- No new features (streaming, tool handling remains unchanged)
- No changes to Rich/prompt_toolkit legacy UI files
- No backwards compatibility shims

## Scope & Assumptions

### In Scope

1. Extract `_build_tunacode_theme()` to `constants.py`
2. Create `cli/widgets.py` for `ResourceBar` and `Editor`
3. Create `cli/screens.py` for `ToolConfirmationModal`
4. Consolidate completion logic with existing `ui/completers.py`
5. Replace hardcoded colors in TCSS with theme variables
6. Clean up imports and reduce `textual_repl.py` to app shell only

### Out of Scope

- Modifying orchestrator/core logic
- Changes to message flow architecture
- New widget features
- Performance optimization

### Assumptions

- Python 3.11+ environment
- Textual library already installed (1.0+)
- `hatch run test` available for validation
- All existing tests pass before refactor

## Deliverables

| Deliverable | Type | Description |
|-------------|------|-------------|
| `constants.py` | Modified | Add `build_tunacode_theme()` function |
| `cli/widgets.py` | New | Contains `ResourceBar`, `Editor` classes |
| `cli/screens.py` | New | Contains `ToolConfirmationModal` screen |
| `cli/textual_repl.py` | Modified | Reduced to app shell + messages + entry point |
| `cli/textual_repl.tcss` | Modified | Replace hardcoded colors with `$surface`, `$primary` |
| `ui/completers.py` | Modified | Add Textual-compatible completion helpers |

## Readiness

### Preconditions

- [x] Git repository clean (current: M on research files only)
- [x] Research documents complete
- [x] `textual_repl.py` exists at 478 lines
- [x] `ui/completers.py` exists with `CommandCompleter`, `FileReferenceCompleter`
- [x] `constants.py` exists with `UI_COLORS` palette

### Required Context

- File: `src/tunacode/cli/textual_repl.py:221-245` - Theme builder to extract
- File: `src/tunacode/cli/textual_repl.py:69-110` - ResourceBar widget
- File: `src/tunacode/cli/textual_repl.py:112-186` - Editor widget
- File: `src/tunacode/cli/textual_repl.py:426-455` - ToolConfirmationModal
- File: `src/tunacode/cli/textual_repl.py:40-66` - Completion helpers
- File: `src/tunacode/ui/completers.py` - Existing completion infrastructure

## Milestones

| ID | Milestone | Description |
|----|-----------|-------------|
| M1 | Theme Extraction | Move theme builder to constants.py |
| M2 | Widget Extraction | Create widgets.py with ResourceBar + Editor |
| M3 | Screen Extraction | Create screens.py with ToolConfirmationModal |
| M4 | Style Unification | Replace hardcoded TCSS colors with theme vars |
| M5 | Completion Consolidation | Merge completion logic into ui/completers.py |
| M6 | Final Cleanup | Reduce textual_repl.py to ~200 lines |

## Work Breakdown (Tasks)

### M1: Theme Extraction

| ID | Task | Owner | Est | Deps | Files |
|----|------|-------|-----|------|-------|
| T1.1 | Extract `_build_tunacode_theme()` and `THEME_NAME` to `constants.py` | dev | 15m | - | `constants.py` |
| T1.2 | Update imports in `textual_repl.py` to use `constants.build_tunacode_theme` | dev | 5m | T1.1 | `textual_repl.py` |
| T1.3 | Run app to verify theme still applies | dev | 5m | T1.2 | - |

**Acceptance**: App launches with correct cyan theme colors

### M2: Widget Extraction

| ID | Task | Owner | Est | Deps | Files |
|----|------|-------|-----|------|-------|
| T2.1 | Create `cli/widgets.py` with `ResourceBar` class (lines 69-110) | dev | 20m | M1 | `cli/widgets.py` |
| T2.2 | Move `Editor` class (lines 112-186) to `widgets.py` | dev | 20m | T2.1 | `cli/widgets.py` |
| T2.3 | Update `textual_repl.py` imports to use `from .widgets import ResourceBar, Editor` | dev | 5m | T2.2 | `textual_repl.py` |
| T2.4 | Verify widget rendering and bindings work | dev | 10m | T2.3 | - |

**Acceptance**: Editor submits text, ResourceBar displays model name, tab completion works

### M3: Screen Extraction

| ID | Task | Owner | Est | Deps | Files |
|----|------|-------|-----|------|-------|
| T3.1 | Create `cli/screens.py` with `ToolConfirmationModal` (lines 426-455) | dev | 15m | M2 | `cli/screens.py` |
| T3.2 | Move `ToolConfirmationRequest`, `ToolConfirmationResponse` dataclasses | dev | 10m | T3.1 | `cli/screens.py` |
| T3.3 | Update imports in `textual_repl.py` | dev | 5m | T3.2 | `textual_repl.py` |
| T3.4 | Test tool confirmation flow (use a test command that triggers confirmation) | dev | 10m | T3.3 | - |

**Acceptance**: Tool confirmation modal appears, Yes/No buttons respond correctly

### M4: Style Unification

| ID | Task | Owner | Est | Deps | Files |
|----|------|-------|-----|------|-------|
| T4.1 | Replace `#162332` with `$surface` in ResourceBar TCSS | dev | 5m | M3 | `textual_repl.tcss` |
| T4.2 | Replace `#00d7ff` with `$primary` in ResourceBar TCSS | dev | 5m | T4.1 | `textual_repl.tcss` |
| T4.3 | Replace `#2d4461` with `$border` in ResourceBar TCSS | dev | 5m | T4.2 | `textual_repl.tcss` |
| T4.4 | Visual inspection of all widgets with theme | dev | 10m | T4.3 | - |

**Acceptance**: ResourceBar uses theme variables; visually identical to before

### M5: Completion Consolidation

| ID | Task | Owner | Est | Deps | Files |
|----|------|-------|-----|------|-------|
| T5.1 | Add `textual_complete_paths()` function to `ui/completers.py` | dev | 20m | M4 | `ui/completers.py` |
| T5.2 | Add `get_command_names()` function to registry or completers | dev | 15m | T5.1 | `ui/completers.py` |
| T5.3 | Update `Editor._complete()` to use consolidated completers | dev | 10m | T5.2 | `cli/widgets.py` |
| T5.4 | Remove `_complete_paths()`, `_gather_command_names()`, `_replace_token()` from textual_repl.py | dev | 5m | T5.3 | `textual_repl.py` |
| T5.5 | Test /command and @file completion | dev | 10m | T5.4 | - |

**Acceptance**: `/help` and `@src/` completions work as before

### M6: Final Cleanup

| ID | Task | Owner | Est | Deps | Files |
|----|------|-------|-----|------|-------|
| T6.1 | Move `build_textual_tool_callback()` to `core/tool_handler.py` or keep in app (decision: keep if tightly coupled) | dev | 15m | M5 | TBD |
| T6.2 | Clean up unused imports in `textual_repl.py` | dev | 5m | T6.1 | `textual_repl.py` |
| T6.3 | Run `ruff check --fix .` on all modified files | dev | 5m | T6.2 | all |
| T6.4 | Run `hatch run test` to verify all tests pass | dev | 10m | T6.3 | - |
| T6.5 | Verify line count of `textual_repl.py` is ~200-250 lines | dev | 2m | T6.4 | `textual_repl.py` |

**Acceptance**: `textual_repl.py` reduced to ~200-250 lines; all tests pass; ruff clean

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Circular imports between cli modules | Medium | High | Use TYPE_CHECKING imports; keep messages in textual_repl.py |
| Widget bindings lost during extraction | Low | High | Copy BINDINGS exactly; test each widget after move |
| Completion logic has hidden state | Low | Medium | Read completers.py thoroughly before consolidation |
| TCSS variables not resolving | Low | Medium | Verify variable names match theme.variables dict |

## Test Strategy

One focused integration test per milestone:

| Milestone | Test |
|-----------|------|
| M1 | Manual: App launches with cyan theme |
| M2 | Manual: Type text, press Enter, verify submission |
| M3 | Manual: Trigger tool requiring confirmation, verify modal |
| M4 | Manual: Visual diff before/after TCSS changes |
| M5 | Manual: Type `/h<tab>` and `@sr<tab>`, verify completions |
| M6 | `hatch run test` - all existing tests pass |

## References

### Research Documents

- `memory-bank/research/2025-11-29_textual-tui-architecture-diagrams.md` - Widget hierarchy, message flow, theme architecture diagrams
- `memory-bank/research/2025-11-29_textual-tui-architecture-and-style-guide.md` - Detailed component analysis, misplaced components table

### Key Code References

- `src/tunacode/cli/textual_repl.py:221-245` - `_build_tunacode_theme()` to extract
- `src/tunacode/cli/textual_repl.py:69-110` - `ResourceBar` widget
- `src/tunacode/cli/textual_repl.py:112-186` - `Editor` widget
- `src/tunacode/cli/textual_repl.py:426-455` - `ToolConfirmationModal`
- `src/tunacode/cli/textual_repl.py:40-66` - Completion helpers
- `src/tunacode/constants.py:110-130` - `UI_COLORS` palette
- `src/tunacode/ui/completers.py` - Existing `CommandCompleter`, `FileReferenceCompleter`

### Architecture Diagrams

From research doc, key diagrams:
- Diagram 5: Current vs Unified Style Architecture (hardcoded -> theme vars)
- Diagram 7: Current vs Target File Architecture (junk drawer -> separated concerns)

## Final Gate

| Metric | Target |
|--------|--------|
| Plan path | `memory-bank/plan/2025-11-29_17-20-38_textual-tui-architecture-refactor.md` |
| Milestones | 6 |
| Tasks | 21 |
| New files | 2 (`widgets.py`, `screens.py`) |
| Modified files | 4 (`constants.py`, `textual_repl.py`, `textual_repl.tcss`, `ui/completers.py`) |
| Target LOC reduction | 478 -> ~200-250 lines in textual_repl.py |

**Next command**: `/ce:execute "memory-bank/plan/2025-11-29_17-20-38_textual-tui-architecture-refactor.md"`
