# Research - Subagent UI Loading States & NeXTSTEP Compliance

**Date:** 2025-12-16
**Owner:** Research Agent
**Phase:** Research

## Goal

Map out the current subagent UI implementation, identify NeXTSTEP principle violations in loading state handling, and document gaps where users lack visibility during long subagent operations.

## Findings

### Current Architecture

#### Relevant Files & Why They Matter

| File | Purpose |
|------|---------|
| `src/tunacode/ui/app.py` | Main TUI - loading indicator control (lines 274-275, 311-312), tool callbacks (lines 582-619) |
| `src/tunacode/ui/widgets/status_bar.py` | Three-zone status bar with `update_running_action()` (line 48) |
| `src/tunacode/ui/renderers/panels.py` | Generic panel renderer via `tool_panel_smart()` (lines 476-521) |
| `src/tunacode/ui/components/tool_panel.py` | ToolPanel widget with status CSS classes (running, completed, failed) |
| `src/tunacode/core/agents/delegation_tools.py` | Research agent factory - NO streaming callback passed (line 75-82) |
| `src/tunacode/core/agents/agent_components/node_processor.py` | Tool categorization, research phase execution (lines 275-290) |
| `src/tunacode/core/agents/research_agent.py` | Read-only agent with limited tools (grep, glob, list_dir, read_file) |

#### What User Sees During Subagent Execution

**Current Flow:**
1. User sends request triggering `research_codebase` tool
2. `LoadingIndicator` appears (1-line spinner animation)
3. Status bar shows: `"running: research"`
4. **BLACK BOX** - No streaming, no progress, no visibility into internal operations
5. After completion: Panel appears with truncated results (max 30 lines)
6. Status bar updates: `"last: research_codebase"`

**The Problem:**
- Research agent can run for 30+ seconds doing multiple grep/read operations
- User sees ONLY "running: research" and a spinner during entire duration
- Internal tool calls (grep, glob, read_file) are NOT surfaced to UI
- No way to know if agent is stuck, working, or nearly done

### NeXTSTEP Principle Violations

#### 1. User Informed Principle - VIOLATED

> "A core tenet is to keep the user constantly informed of the agent's state, actions, and reasoning. No 'magic' should happen in the background without visual feedback."

**Current State:** Research agent operates as complete black box. User has zero visibility into what files are being searched, what patterns are being analyzed, or how many operations remain.

**Evidence:**
- `research_agent.run()` called WITHOUT streaming callback (`delegation_tools.py:75-82`)
- Internal tools execute in isolation with no UI propagation
- Only completion triggers any display update

#### 2. Visual Feedback Principle - VIOLATED

> "Controls change appearance immediately on mouse-down... User must always see result of their action."

**Current State:** After initiating a request, the only feedback is a static spinner and unchanging status text for potentially minutes.

**Evidence:**
- `LoadingIndicator` is a simple spinner with no progress indication
- Status bar stuck on "running: research" until completion
- No intermediate state changes during long operations

#### 3. State Indication Principle - VIOLATED

> "Current state shown through highlighting, position, or imagery. Never rely solely on labels to show state."

**Current State:** State is shown ONLY via text label ("running: research"). No visual progress, no phase indicators, no operation count.

**Evidence:**
- No progress bar or percentage indicator
- No count of operations completed vs remaining
- No visual indication of which file is being processed

#### 4. Information Hunting Anti-Pattern - PRESENT

> "Critical info in inconsistent locations"

**Current State:** When results finally appear, they're truncated to 30 lines and use generic formatting. User must hunt through collapsed content to find relevant information.

**Evidence:**
- `MAX_PANEL_LINES = 30` truncation (`constants.py:31`)
- No specialized renderer for `research_codebase` results
- Structured dict output rendered as generic JSON-like text

### Technical Root Causes

#### 1. No Streaming Callback for Subagents

```python
# delegation_tools.py:75-82
result = await research_agent.run(
    prompt,
    usage=ctx.usage,  # Only usage tracking passed
    # NO streaming_callback parameter
)
```

The research agent executes without any streaming callback, making it impossible for the UI to receive intermediate updates.

#### 2. No Tool Progress Propagation

```python
# node_processor.py:282-290
if research_agent_tasks and tool_callback:
    if tool_start_callback:
        tool_start_callback("research")  # Single notification at start
    await execute_tools_parallel(research_agent_tasks, tool_callback)
    # No progress updates during execution
```

The tool_start_callback fires ONCE at the beginning. No mechanism exists to surface internal tool progress.

#### 3. Generic Panel Renderer

```python
# panels.py:504-512
TOOL_RENDERERS = {
    "bash": render_bash_panel,
    "grep": render_grep_panel,
    "glob": render_glob_panel,
    # ... other tools
    # research_codebase NOT listed - falls back to generic
}
```

Research results use the generic `tool_panel()` function instead of a specialized renderer that could better format the structured output.

#### 4. No Subagent Panel Component

The codebase has NO dedicated "subagent panel" - only generic tool panels exist. Subagent operations are treated identically to simple tool calls despite being fundamentally different in duration and complexity.

### Current Status Bar Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ [branch/location]    │ [edited files]     │ running: research       │
└─────────────────────────────────────────────────────────────────────┘
```

Three zones exist but only rightmost is used for tool feedback. No space allocated for progress indication.

## Key Patterns / Solutions Found

### Pattern 1: Callback Chain Already Exists
- `tool_start_callback` fires at tool start
- `tool_result_callback` fires at tool completion
- **Gap:** No `tool_progress_callback` for intermediate updates

### Pattern 2: Streaming Infrastructure Exists
- Main agent HAS streaming via `streaming_callback` in `app.py:399-415`
- `streaming_output` widget exists and can display live text
- **Gap:** Research agent not wired to use it

### Pattern 3: Phased Execution Model
- `node_processor.py` already categorizes tools into phases
- Research agents execute in dedicated Phase 2
- **Gap:** Phase boundaries not communicated to UI

### Pattern 4: ToolPanel Widget Has Status States
- CSS classes: `.running`, `.completed`, `.failed`
- Widget can show active state
- **Gap:** Not used for long-running operations (only final state)

## Knowledge Gaps

1. **Subagent Internal Tool Visibility:** Can we propagate internal tool calls (grep, read_file) to the parent UI without major architectural changes?

2. **Progress Estimation:** Research agent operations are unpredictable. How to show meaningful progress without knowing total work?

3. **Panel Placement:** Should subagent panels appear inline in chat flow or in a dedicated sidebar/overlay?

4. **Partial Results:** Should intermediate findings stream as they're discovered, or only show complete results?

5. **Multiple Subagents:** When multiple research agents run in parallel, how should UI handle overlapping progress?

## NeXTSTEP-Compliant Design Considerations

Based on the NeXTSTEP User Interface Guidelines, a compliant solution should:

### Information Hierarchy & Zoning

```
┌─────────────────────────────────────────────────┐
│ Model: gpt-4  │  Tokens: 1.2k  │  Status: ready │  <- PERSISTENT STATUS
├─────────────────────────────────────────────────┤
│                                                 │
│  Main conversation / output                     │  <- PRIMARY VIEWPORT
│                                                 │
├─────────────────────────────────────────────────┤
│  SUBAGENT ACTIVITY PANEL (when active)          │  <- NEW ZONE
│  ┌───────────────────────────────────────────┐  │
│  │ Research Agent [running]         3/5 ops  │  │
│  │ > grep "callback" src/           [done]   │  │
│  │ > read_file app.py               [done]   │  │
│  │ > grep "streaming" src/          [active] │  │
│  └───────────────────────────────────────────┘  │
├─────────────────────────────────────────────────┤
│ ~/tunacode  │  app.py, status.py   │ running:3 │  <- STATUS BAR
├─────────────────────────────────────────────────┤
│ >                                               │  <- INPUT
└─────────────────────────────────────────────────┘
```

### Key Design Principles to Apply

1. **User Control:** Allow cancellation of subagent operations
2. **Visible State:** Show operation queue and current item
3. **Feedback:** Update on each internal operation completion
4. **Naturalness:** Progress should feel continuous, not stuck
5. **Consistency:** Subagent panels should follow same styling as tool panels

## References

- `src/tunacode/ui/app.py` - Main TUI application
- `src/tunacode/ui/widgets/status_bar.py` - Status bar implementation
- `src/tunacode/ui/renderers/panels.py` - Panel rendering system
- `src/tunacode/ui/components/tool_panel.py` - Tool panel widget
- `src/tunacode/core/agents/delegation_tools.py` - Research agent factory
- `src/tunacode/core/agents/research_agent.py` - Research agent implementation
- `src/tunacode/core/agents/agent_components/node_processor.py` - Tool execution phases
- `~/.claude/skills/neXTSTEP-ui/` - NeXTSTEP design principles
- PR #177 - Recent tool-start-callback-ui-feedback implementation
