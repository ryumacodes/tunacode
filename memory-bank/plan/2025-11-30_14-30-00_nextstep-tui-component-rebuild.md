---
title: "NeXTSTEP TUI Component Rebuild - Plan"
phase: Plan
date: "2025-11-30T14:30:00-06:00"
owner: "claude-opus"
parent_research: "memory-bank/research/2025-11-30_13-45-00_tui-architecture-map.md"
git_commit_at_plan: "d7affa4"
tags: [plan, textual, tui, nextstep, components, ui-design]
---

# NeXTSTEP TUI Component Rebuild - Implementation Plan

## Goal

**SINGULAR OUTCOME**: Rebuild all TUI components following NeXTSTEP UI principles with proper information hierarchy zoning, consistent visual feedback, and user-controlled interactions.

The current architecture is 85% aligned. This rebuild focuses on the 15% gap:
1. ResourceBar only displays model name (tracks tokens/cost but doesn't render)
2. Streaming-output zone creates viewport duplication
3. ToolStatusBar lacks visual prominence
4. No persistent pause mode indicator

### Non-goals

- No new features beyond existing functionality
- No backend/orchestrator changes
- No legacy ui/ file modifications
- No test suite expansion (ONE test max)

## Scope & Assumptions

### In Scope

1. **ResourceBar enhancement** - Display all tracked metrics (model, tokens, cost, session_cost)
2. **Zone consolidation** - Merge streaming-output into RichLog viewport
3. **ToolStatusBar elevation** - Add visual prominence with state-based styling
4. **Pause mode indicator** - Persistent visual mode indicator
5. **TCSS refinement** - Apply NeXTSTEP zone-based styling

### Out of Scope

- Completion popover (acknowledged TODO, separate effort)
- Error zone separation (enhancement, not required)
- Modal enhancements (current implementation is NeXTSTEP compliant)
- New widget features

### Assumptions

- Current architecture is sound (85% NeXTSTEP aligned per analysis)
- All existing tests pass before rebuild
- Textual 1.0+ already installed
- Python 3.11+ environment

## Deliverables (DoD)

| Deliverable | Type | Acceptance Criteria |
|-------------|------|---------------------|
| `cli/widgets.py` | Modified | ResourceBar renders all 4 metrics; ToolStatusBar has state classes |
| `cli/textual_repl.py` | Modified | Streaming merged into RichLog; pause indicator via CSS class |
| `cli/textual_repl.tcss` | Modified | Zone-based styling; state classes for pause/active |
| `constants.py` | Modified | Symbolic constants for all dimensions |

## Readiness (DoR)

### Preconditions

- [x] Git repository at d7affa4
- [x] Research document complete: `memory-bank/research/2025-11-30_13-45-00_tui-architecture-map.md`
- [x] NeXTSTEP skill reviewed
- [x] Current widgets exist in `cli/widgets.py` (ResourceBar, ToolStatusBar, Editor)
- [x] Theme system operational with `UI_COLORS` and `build_tunacode_theme()`

### Required Context

- File: `src/tunacode/cli/widgets.py:77-118` - ResourceBar (tracks but doesn't display metrics)
- File: `src/tunacode/cli/widgets.py:50-75` - ToolStatusBar (minimal styling)
- File: `src/tunacode/cli/textual_repl.py:78-92` - compose() with separate streaming zone
- File: `src/tunacode/cli/textual_repl.py:186-194` - streaming_callback implementation
- File: `src/tunacode/cli/textual_repl.tcss` - Current styling (80 lines)

## Milestones

| ID | Milestone | Description |
|----|-----------|-------------|
| M1 | ResourceBar NeXTSTEP | Display all metrics in persistent status zone |
| M2 | Zone Consolidation | Merge streaming into RichLog viewport |
| M3 | ToolStatusBar Elevation | State-based styling with visual prominence |
| M4 | Mode Visualization | Persistent pause indicator |

## Work Breakdown (Tasks)

### M1: ResourceBar NeXTSTEP (Persistent Status Zone)

**NeXTSTEP Principle**: "Glanceable, rarely changes" - status should show all critical metrics

| ID | Task | Files | Deps |
|----|------|-------|------|
| T1.1 | Add symbolic constants for ResourceBar dimensions in constants.py | `constants.py` | - |
| T1.2 | Update `_refresh_display()` to render: model, tokens/max, last_cost, session_cost | `cli/widgets.py` | T1.1 |
| T1.3 | Style ResourceBar sections with separators (pipe or vertical bar) | `cli/widgets.py` | T1.2 |
| T1.4 | Verify ResourceBar displays correctly after request completion | manual | T1.3 |

**Acceptance**: ResourceBar shows `TunaCode │ gpt-4o │ 1.2k/200k │ $0.03 │ $0.45`

### M2: Zone Consolidation (Primary Viewport)

**NeXTSTEP Principle**: "Divide interface into zones with distinct purposes" - single viewport for content

| ID | Task | Files | Deps |
|----|------|-------|------|
| T2.1 | Remove `Static#streaming-output` from compose() | `cli/textual_repl.py` | M1 |
| T2.2 | Update `streaming_callback()` to write directly to RichLog with dim/italic styling | `cli/textual_repl.py` | T2.1 |
| T2.3 | Modify `_process_request()` completion to update RichLog styling (remove dim) | `cli/textual_repl.py` | T2.2 |
| T2.4 | Remove `#streaming-output` selector from TCSS | `cli/textual_repl.tcss` | T2.3 |
| T2.5 | Add `.streaming` CSS class for in-progress text styling | `cli/textual_repl.tcss` | T2.4 |
| T2.6 | Verify streaming renders in RichLog, completes with normal styling | manual | T2.5 |

**Acceptance**: Single viewport (RichLog) shows all content; streaming text distinct during generation

### M3: ToolStatusBar Elevation (Context Zone)

**NeXTSTEP Principle**: "Current state shown through highlighting, position, or imagery"

| ID | Task | Files | Deps |
|----|------|-------|------|
| T3.1 | Add state classes to ToolStatusBar: `.active`, `.idle`, `.error` | `cli/widgets.py` | M2 |
| T3.2 | Modify `set_status()` to add `.active` class | `cli/widgets.py` | T3.1 |
| T3.3 | Modify `clear()` to remove `.active` class, set `.idle` | `cli/widgets.py` | T3.2 |
| T3.4 | Add TCSS rules for ToolStatusBar states (border-left accent, color changes) | `cli/textual_repl.tcss` | T3.3 |
| T3.5 | Verify ToolStatusBar shows visual state changes during tool execution | manual | T3.4 |

**Acceptance**: ToolStatusBar has visible left-border accent when active; distinct styling per state

### M4: Mode Visualization (Pause Indicator)

**NeXTSTEP Principle**: "Modes must be visually apparent at all times"

| ID | Task | Files | Deps |
|----|------|-------|------|
| T4.1 | Add `.paused` CSS class definition for RichLog | `cli/textual_repl.tcss` | M3 |
| T4.2 | Modify `pause_streaming()` to add `.paused` class to RichLog | `cli/textual_repl.py` | T4.1 |
| T4.3 | Modify `resume_streaming()` to remove `.paused` class | `cli/textual_repl.py` | T4.2 |
| T4.4 | Style `.paused` with warning border color | `cli/textual_repl.tcss` | T4.3 |
| T4.5 | Verify pause/resume shows persistent visual indicator | manual | T4.4 |

**Acceptance**: RichLog border changes to warning color when paused; returns to normal on resume

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation | Trigger |
|------|--------|------------|------------|---------|
| RichLog doesn't support partial styling | High | Low | Use Rich markup for streaming text instead of CSS class | First streaming test fails |
| Class manipulation not available on Static | Medium | Low | Use `add_class()`/`remove_class()` Textual methods | Compiler error |
| Streaming update causes scroll jitter | Medium | Medium | Buffer updates, use `call_later()` for debouncing | Visual observation |

## Test Strategy

**ONE integration test** (as specified):

| Test | Type | Description |
|------|------|-------------|
| Visual inspection | Manual | Launch app, verify zones, trigger tool, check states |

Full test suite deferred to post-rebuild phase per instructions.

## References

### Research Documents

- `memory-bank/research/2025-11-30_13-45-00_tui-architecture-map.md` - Architecture analysis, widget hierarchy, migration status

### NeXTSTEP Principles Applied

1. **Information Hierarchy & Zoning**: Status (top), Viewport (center), Context, Input (bottom)
2. **Consistency**: Objects that look same act same
3. **User Control**: User decides what happens next
4. **Visual Feedback**: Controls change appearance immediately
5. **Mode Visibility**: Modes visually apparent at all times

### Key Code References

- `src/tunacode/cli/widgets.py:77-118` - ResourceBar class
- `src/tunacode/cli/widgets.py:50-75` - ToolStatusBar class
- `src/tunacode/cli/textual_repl.py:78-92` - compose() method
- `src/tunacode/cli/textual_repl.py:186-222` - Streaming architecture
- `src/tunacode/cli/textual_repl.py:203-214` - Pause/resume logic
- `src/tunacode/cli/textual_repl.tcss` - Current styling
- `src/tunacode/constants.py:110-130` - UI_COLORS palette

### NeXTSTEP Zone Layout Target

```
┌─────────────────────────────────────────────────────────────┐
│ TunaCode │ gpt-4o │ 1.2k/200k │ $0.03 │ $0.45 session      │  ← PERSISTENT STATUS
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  > User message here                                        │  ← PRIMARY VIEWPORT
│                                                             │     (unified RichLog)
│  Agent response streaming here...                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ ⚙ Reading: /home/user/config.py                            │  ← CONTEXT ZONE
├─────────────────────────────────────────────────────────────┤     (ToolStatusBar)
│ >                                                           │  ← INPUT ZONE
│                                                             │     (Editor)
├─────────────────────────────────────────────────────────────┤
│ ^P Pause │ Tab Complete │ Enter Submit                      │  ← META CONTROLS
└─────────────────────────────────────────────────────────────┘     (Footer)
```

## Alternative Approach (Optional)

**Streaming Overlay Pattern**: Instead of merging streaming into RichLog, keep `#streaming-output` as an overlay that appears during streaming and hides after. This preserves scroll position in RichLog.

**Pros**: No scroll position management; cleaner separation
**Cons**: Two zones for same content type (violates NeXTSTEP zoning)

**Recommendation**: Use primary approach (merge into RichLog) unless scroll jitter becomes problematic.

## Final Gate

| Metric | Value |
|--------|-------|
| Plan path | `memory-bank/plan/2025-11-30_14-30-00_nextstep-tui-component-rebuild.md` |
| Milestones | 4 |
| Tasks | 18 |
| Modified files | 4 (`widgets.py`, `textual_repl.py`, `textual_repl.tcss`, `constants.py`) |
| New files | 0 |
| Tests | 1 (manual visual inspection) |

**Next command**: `/context-engineer:execute "memory-bank/plan/2025-11-30_14-30-00_nextstep-tui-component-rebuild.md"`
