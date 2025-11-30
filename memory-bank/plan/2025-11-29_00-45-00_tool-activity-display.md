---
title: "Tool Activity Display - Plan"
phase: Plan
date: "2025-11-29T00:45:00-05:00"
owner: "Claude"
parent_research: "memory-bank/research/2025-11-29_tool-activity-display-blueprint.md"
git_commit_at_plan: "281694d"
tags: [plan, tool-activity, coding, textual, widgets]
---

## Goal

- Restore real-time tool activity display in the Textual TUI by adding a `ToolStatusBar` widget with callback integration.

**Non-goals**:
- Deployment/observability changes
- Modifications to tool confirmation flow
- Persistent logging of tool status to RichLog

## Scope & Assumptions

**In scope**:
- New Message classes (`ToolStatusUpdate`, `ToolStatusClear`)
- New widget (`ToolStatusBar`)
- Callback wiring from `node_processor.py` to Textual app
- TCSS styling for the status bar

**Out of scope**:
- Changes to `ui/output.py` existing functions
- Research agent panel display
- Batch execution panels

**Assumptions**:
- Textual 3.x API
- Existing callback pattern (`streaming_callback`) is the model to follow
- `UICallback` type from `types.py` is appropriate for status updates

## Deliverables

1. `ToolStatusUpdate` and `ToolStatusClear` Message classes in `cli/widgets.py`
2. `ToolStatusBar` Static widget in `cli/widgets.py`
3. Handler and callback builder in `cli/textual_repl.py`
4. `tool_status_callback` parameter threaded through agent orchestration
5. Replacement of `ui.update_spinner_message()` calls in `node_processor.py`

## Readiness

- [x] Research doc complete with code samples
- [x] Git at expected commit (281694d)
- [x] Target files identified with line numbers
- [x] Pattern reference created (`.claude/patterns/tool-status-widget-pattern.md`)

## Milestones

- **M1**: Widget & Message classes in `cli/widgets.py`
- **M2**: App integration in `cli/textual_repl.py`
- **M3**: Callback threading through agent layer
- **M4**: Status updates in `node_processor.py`

## Work Breakdown (Tasks)

### M1: Widget & Message Classes

| Task ID | Summary | Files | Acceptance Test |
|---------|---------|-------|-----------------|
| T1.1 | Add `ToolStatusUpdate` Message class | `cli/widgets.py` | Class imports without error |
| T1.2 | Add `ToolStatusClear` Message class | `cli/widgets.py` | Class imports without error |
| T1.3 | Add `ToolStatusBar` widget with `set_status()` and `clear()` | `cli/widgets.py` | Widget renders empty string initially |

**Dependencies**: None

### M2: App Integration

| Task ID | Summary | Files | Acceptance Test |
|---------|---------|-------|-----------------|
| T2.1 | Add `self.tool_status` to `__init__` | `cli/textual_repl.py:54-67` | App initializes with widget |
| T2.2 | Add `tool_status` to `compose()` layout between RichLog and streaming | `cli/textual_repl.py:69-73` | Widget visible in DOM |
| T2.3 | Add `on_tool_status_update()` handler | `cli/textual_repl.py` | Handler updates widget |
| T2.4 | Add `on_tool_status_clear()` handler | `cli/textual_repl.py` | Handler clears widget |
| T2.5 | Add `build_tool_status_callback()` function | `cli/textual_repl.py` | Callback posts message |

**Dependencies**: T1.1, T1.2, T1.3

### M3: Callback Threading

| Task ID | Summary | Files | Acceptance Test |
|---------|---------|-------|-----------------|
| T3.1 | Add `tool_status_callback: Optional[UICallback]` to `process_request()` | `core/agents/main.py` | Signature accepts callback |
| T3.2 | Pass callback through `AgentOrchestrator` to node processing | `core/agents/main.py` | Callback reaches node_processor |
| T3.3 | Wire callback in `_process_request()` call site | `cli/textual_repl.py:109-110` | Callback passed at runtime |

**Dependencies**: T2.5

### M4: Status Updates in Node Processor

| Task ID | Summary | Files | Acceptance Test |
|---------|---------|-------|-----------------|
| T4.1 | Replace batch collection status (line 443-450) | `core/agents/agent_components/node_processor.py` | Status shows during batch |
| T4.2 | Replace sequential tool status (line 501-503) | `core/agents/agent_components/node_processor.py` | Status shows per tool |
| T4.3 | Replace research agent progress (line 401-404) | `core/agents/agent_components/node_processor.py` | Status shows research progress |
| T4.4 | Clear status after tool execution completes | `core/agents/agent_components/node_processor.py` | Status clears after completion |

**Dependencies**: T3.2

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Callback not reaching node_processor | Status never updates | Trace callback path; add logging |
| Widget not in Textual DOM | No visual output | Verify compose() order |
| Thread safety with post_message | Race conditions | post_message is thread-safe per Textual docs |

## Test Strategy

- **T1.3**: Unit test - `ToolStatusBar.set_status("test")` updates content
- **T4.4**: Integration test - Run `read_file` tool, verify status appears and clears

## References

- Research: `memory-bank/research/2025-11-29_tool-activity-display-blueprint.md`
- Pattern: `.claude/patterns/tool-status-widget-pattern.md`
- Code refs:
  - `cli/widgets.py:21-35` - existing Message pattern
  - `cli/textual_repl.py:157-165` - streaming_callback pattern
  - `core/agents/agent_components/node_processor.py:309-561` - tool processing

## Final Gate

- **Plan path**: `memory-bank/plan/2025-11-29_00-45-00_tool-activity-display.md`
- **Milestones**: 4
- **Tasks**: 14 (ready for coding)
- **Next command**: `/ce:execute "memory-bank/plan/2025-11-29_00-45-00_tool-activity-display.md"`
