---
title: "Textual TUI Modernization - Plan"
phase: Plan
date: "2025-11-29T17:15:00-06:00"
owner: "claude-opus"
parent_research: "memory-bank/research/2025-11-29_textual-repl-tui-modernization.md"
git_commit_at_plan: "6ea5926"
tags: [plan, textual, tui, css, styling, coding]
---

## Goal

- **ONE singular outcome**: Apply professional styling to the TextualReplApp using external TCSS and a custom Textual Theme derived from the existing `UI_COLORS` palette.

### Non-goals (explicitly excluded)

- No orchestrator logic changes
- No new features beyond visual styling
- No deployment/packaging changes
- No additional test coverage beyond verifying app launches with new styles

## Scope & Assumptions

### In Scope

- Create external `.tcss` stylesheet for the Textual app
- Register custom Textual Theme using `UI_COLORS` from `constants.py`
- Style `ToolConfirmationModal` (currently unstyled, noted as "looks terrible")
- Fix streaming output wrapping issues (width/layout)
- Add borders, padding, and visual hierarchy to widgets
- Ensure Editor widget has appropriate fixed/constrained height

### Out of Scope

- Orchestrator wiring (covered by separate migration plan Tasks 5-8)
- Functionality changes to Editor, ResourceBar, or Modal
- Token/cost display in ResourceBar (marked as TODO, separate concern)
- Completion popover UI (deferred feature)

### Assumptions

- Textual CSS supports the styling patterns documented in research
- `UI_COLORS` values are valid for Textual theme registration
- No Textual version upgrade required

## Deliverables

1. **External stylesheet**: `src/tunacode/cli/textual_repl.tcss`
2. **Theme registration**: Custom "tunacode" theme in `TextualReplApp.on_mount()`
3. **Modal styling**: `ToolConfirmationModal` with proper borders, padding, centered layout
4. **Layout fixes**: Correct wrapping behavior for streaming output and chat history

## Readiness

### Preconditions

- [x] Branch `textual_repl` exists at commit `6ea5926`
- [x] `textual_repl.py` has working app structure (454 lines)
- [x] `UI_COLORS` palette defined in `constants.py:110-130`
- [x] Research doc completed with Textual CSS patterns

### Required Knowledge

- Textual CSS (TCSS) syntax
- Textual Theme API
- Widget docking and fractional sizing

## Milestones

- **M1**: External stylesheet created and linked
- **M2**: Custom theme registered with UI_COLORS
- **M3**: Modal and widget styling applied
- **M4**: Layout/wrapping issues resolved

## Work Breakdown (Tasks)

### Task 1: Create External TCSS Stylesheet

**Summary**: Create `textual_repl.tcss` with base layout rules
**Owner**: claude
**Dependencies**: None
**Target Milestone**: M1

**Acceptance Test**:
- App launches with `CSS_PATH = "textual_repl.tcss"` without errors

**Files/Modules Touched**:
- `src/tunacode/cli/textual_repl.tcss` (new)
- `src/tunacode/cli/textual_repl.py:242` (change `CSS_PATH = None` to path)

**Implementation Details**:
```tcss
/* Base layout */
#body {
    height: 1fr;
}

RichLog {
    height: 1fr;
    border: solid $primary;
    padding: 0 1;
}

#streaming-output {
    height: auto;
    max-height: 30%;
    padding: 0 1;
}

Editor {
    height: 5;
    border: solid $accent;
    padding: 0 1;
}
```

---

### Task 2: Register Custom Textual Theme

**Summary**: Create and register "tunacode" theme using `UI_COLORS`
**Owner**: claude
**Dependencies**: Task 1
**Target Milestone**: M2

**Acceptance Test**:
- App uses cyan-themed colors matching `UI_COLORS` palette

**Files/Modules Touched**:
- `src/tunacode/cli/textual_repl.py:269-272` (extend `on_mount`)

**Implementation Details**:
```python
from textual.theme import Theme

def on_mount(self) -> None:
    theme = Theme(
        name="tunacode",
        primary="#00d7ff",      # UI_COLORS["primary"]
        secondary="#0ea5e9",    # UI_COLORS["accent"]
        accent="#4de4ff",       # UI_COLORS["primary_light"]
        background="#0d1720",   # UI_COLORS["background"]
        surface="#162332",      # UI_COLORS["surface"]
        panel="#1e2d3f",        # UI_COLORS["border_light"]
        success="#059669",      # UI_COLORS["success"]
        warning="#d97706",      # UI_COLORS["warning"]
        error="#dc2626",        # UI_COLORS["error"]
    )
    self.register_theme(theme)
    self.theme = "tunacode"

    self.set_focus(self.editor)
    self.run_worker(self._request_worker, exclusive=False)
    self._update_resource_bar()
```

---

### Task 3: Style ToolConfirmationModal

**Summary**: Add professional styling to the confirmation modal
**Owner**: claude
**Dependencies**: Task 1
**Target Milestone**: M3

**Acceptance Test**:
- Modal displays centered with borders, proper padding, readable layout

**Files/Modules Touched**:
- `src/tunacode/cli/textual_repl.tcss` (add modal rules)
- `src/tunacode/cli/textual_repl.py:402-431` (add CSS classes if needed)

**Implementation Details**:
```tcss
ToolConfirmationModal {
    align: center middle;
}

#modal-body {
    width: 60;
    height: auto;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#tool-title {
    text-style: bold;
    color: $primary;
    margin-bottom: 1;
}

#actions {
    margin-top: 1;
    align: center middle;
}

#actions Button {
    margin: 0 1;
}
```

---

### Task 4: Fix Layout and Wrapping Issues

**Summary**: Resolve word-by-word line breaking in streaming output
**Owner**: claude
**Dependencies**: Tasks 1-3
**Target Milestone**: M4

**Acceptance Test**:
- Streaming text displays with proper word wrapping (not word-per-line)
- RichLog history renders correctly

**Files/Modules Touched**:
- `src/tunacode/cli/textual_repl.tcss` (width rules)
- `src/tunacode/cli/textual_repl.py:261` (Static widget configuration)

**Implementation Details**:

The word-by-word issue likely stems from `Static` widget not having explicit width. Fix:

```tcss
#streaming-output {
    width: 100%;
    height: auto;
    max-height: 30%;
}
```

If persists, investigate whether `Static.update()` needs markup disabled or content wrapped in a `Text` object with proper wrapping.

---

### Task 5: Remove ResourceBar Inline CSS

**Summary**: Move ResourceBar styles to external stylesheet
**Owner**: claude
**Dependencies**: Task 1
**Target Milestone**: M3

**Acceptance Test**:
- ResourceBar styling works from external file, `DEFAULT_CSS` removed

**Files/Modules Touched**:
- `src/tunacode/cli/textual_repl.py:70-78` (remove DEFAULT_CSS)
- `src/tunacode/cli/textual_repl.tcss` (add ResourceBar rules)

**Implementation Details**:
```tcss
ResourceBar {
    dock: top;
    height: 1;
    background: $surface;
    color: $text-muted;
    padding: 0 1;
}
```

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Textual Theme API differs from research | Medium | Low | Check Textual docs; fall back to CSS variables |
| Streaming wrapping is content issue not CSS | Medium | Medium | Test with plain text; may need markup changes |
| TCSS path resolution fails | Low | Low | Use relative path; verify with `textual devtools` |

## Test Strategy

- **Manual verification**: Launch app, submit request, confirm modal displays
- **No new automated tests**: This is styling-only; existing launch test sufficient
- **Visual inspection**: Compare before/after screenshots

## References

- Research: `memory-bank/research/2025-11-29_textual-repl-tui-modernization.md`
- Source: `src/tunacode/cli/textual_repl.py`
- Palette: `src/tunacode/constants.py:110-130`
- Textual CSS docs: https://textual.textualize.io/guide/CSS/

## Final Gate

- **Output**: This plan at `memory-bank/plan/2025-11-29_17-15-00_textual-tui-modernization.md`
- **Milestones**: 4 (M1-M4)
- **Tasks**: 5 tasks ready for immediate coding
- **Next command**: `/ce:execute "memory-bank/plan/2025-11-29_17-15-00_textual-tui-modernization.md"`
