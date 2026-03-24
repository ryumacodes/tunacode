---
title: "Command autocomplete dropdown positioning fix"
link: "command-autocomplete-positioning-plan"
type: implementation_plan
ontological_relations:
  - relates_to: [[command-autocomplete-positioning-research]]
tags: [plan, ui, autocomplete, positioning]
uuid: "cmd-pos-plan-2026-03-23"
created_at: "2026-03-23T15:35:00Z"
parent_research: ".artifacts/research/2026-03-23_15-30-00_command-autocomplete-positioning.md"
git_commit_at_plan: "ba7df663"
---

## Goal

Fix the CommandAutoComplete dropdown positioning by always displaying it **above** the Editor input bar instead of below it, ensuring it's never cut off at the bottom of the terminal.

**OUT of scope:**
- CSS styling changes (colors, borders)
- Other autocomplete widgets (FileAutoComplete, SkillsAutoComplete)
- Terminal resizing handling improvements
- Performance optimizations

## Scope & Assumptions

**IN scope:**
- Override `_align_to_target()` method in `CommandAutoComplete` class
- Position dropdown above the Editor widget (always, no calculation needed)
- Verify fix works

**OUT of scope:**
- Changes to upstream textual-autocomplete library
- CSS modifications for dropdown appearance
- Changes to Editor widget dimensions
- Changes to other autocomplete widgets

**Assumptions:**
- textual-autocomplete==4.0.6 is installed
- Editor widget remains at bottom of screen with height: 6
- Target widget (`self.editor`) provides `cursor_screen_offset` property

## Deliverables

1. Modified `src/tunacode/ui/widgets/command_autocomplete.py` with custom positioning logic
2. Single verification test demonstrating dropdown appears above the input bar

## Readiness

**Preconditions (verified by research):**
- Repository cloned and dependencies installed
- `src/tunacode/ui/widgets/command_autocomplete.py` exists at lines 20-94
- `textual-autocomplete` package provides `AutoComplete` base class with `_align_to_target()` method
- `Editor` widget has `cursor_screen_offset` property at lines 147-150

## Milestones

- **M1**: Implementation - Override positioning method to place dropdown above input
- **M2**: Verification - Test dropdown appears above the Editor

## Work Breakdown (Tasks)

### Task T001: Override `_align_to_target()` to position above input

**Summary**: Add custom positioning logic to `CommandAutoComplete` class that always positions the dropdown above the Editor input bar.

**Files**:
- `src/tunacode/ui/widgets/command_autocomplete.py` (modify)

**Changes**:
1. Override the `_align_to_target()` method in `CommandAutoComplete` class (after `__init__`)
2. Implementation: Position dropdown at `(cursor_x - 1, cursor_y - dropdown_height - 1)` to appear above the cursor

**Code to add** (insert after `__init__` method, before class end):
```python
def _align_to_target(self) -> None:
    """Align dropdown above the input bar instead of below."""
    from textual.geometry import Offset

    x, y = self.target.cursor_screen_offset
    dropdown = self.option_list
    _width, height = dropdown.outer_size

    # Position above the cursor (y - height - 1)
    self.absolute_offset = Offset(x - 1, y - height - 1)
```

**Acceptance Test**:
1. Launch TunaCode: `make run` or `uv run tunacode`
2. Type "/" in the editor
3. **Verify**: Dropdown appears fully visible, positioned **above** the input bar (not below)

**Dependencies**: None
**Milestone**: M1
**Estimate**: 15 minutes

### Task T002: Verify dropdown is fully visible

**Summary**: Confirm the dropdown is never cut off and displays correctly above the input.

**Files**: None (verification only)

**Changes**: None

**Acceptance Test**:
1. Launch TunaCode in terminal of any height
2. Type "/" in the editor
3. **Verify**: Dropdown appears above the input bar, fully visible, not extending below screen

**Dependencies**: T001
**Milestone**: M2
**Estimate**: 5 minutes

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Upstream library API changes in future versions | Simple Offset-based positioning, easy to update |
| Dropdown extends above top of screen | Acceptable - terminal can scroll; better than being cut off at bottom |

## Test Strategy

**Manual testing only** (UI positioning requires visual verification):

1. **Positioning test** (T001 acceptance): Type "/", verify dropdown appears above input bar
2. **Visibility test** (T002 acceptance): Verify dropdown is fully visible, not cut off

No automated unit tests required for this visual/UI positioning fix.

## References

- Research: `.artifacts/research/2026-03-23_15-30-00_command-autocomplete-positioning.md`
- Target file: `src/tunacode/ui/widgets/command_autocomplete.py:20-94`
- Upstream logic: `.venv/lib/python3.11/site-packages/textual_autocomplete/_autocomplete.py:288-302`
- Editor dimensions: `src/tunacode/ui/styles/layout.tcss:85-95`
- Autocomplete styles: `src/tunacode/ui/styles/widgets.tcss:1-10`

## Final Gate

- **Plan written to**: `.artifacts/plan/2026-03-23_15-35-00_command-autocomplete-positioning.md`
- **Milestones**: 2 (M1: Implementation, M2: Verification)
- **Tasks**: 2 (T001: Positioning override, T002: Visibility verification)
- **Git state**: ba7df663
- **Estimated total time**: 20 minutes

**Next step**: Proceed to execute-phase using plan path `.artifacts/plan/2026-03-23_15-35-00_command-autocomplete-positioning.md`
