# Research – Remove ToolStatusBar and Dead Code

**Date:** 2025-11-30
**Owner:** agent
**Phase:** Research

## Goal

Identify all code related to the `ToolStatusBar` widget (the "Ready" status bar near the input) for complete removal, including all connected dead code, callbacks, constants, CSS, and message classes.

## Findings

The ToolStatusBar is a single-line widget in the bottom zone showing "Ready" when idle and tool execution status with a spinner when tools run. It requires removal across 6 files with significant dead code cleanup.

### Relevant Files & Why They Matter

| File | Reason |
|------|--------|
| `src/tunacode/cli/widgets.py` | Contains ToolStatusBar widget class + Message classes |
| `src/tunacode/cli/textual_repl.py` | Widget instantiation, event handlers, callback builder |
| `src/tunacode/cli/textual_repl.tcss` | CSS styling for ToolStatusBar and #bottom-zone |
| `src/tunacode/constants.py` | TOOL_STATUS_CLASS_* constants |
| `src/tunacode/core/agents/main.py` | tool_status_callback parameter threading |
| `src/tunacode/core/agents/agent_components/node_processor.py` | Helper functions and callback invocations |

## Detailed Removal Plan by File

### 1. `src/tunacode/cli/widgets.py`

**Remove imports (lines 23-24):**
```python
TOOL_STATUS_CLASS_ACTIVE,
TOOL_STATUS_CLASS_IDLE,
```

**Remove message classes:**
- `ToolStatusUpdate` class (lines 46-51)
- `ToolStatusClear` class (lines 54-55)

**Remove widget class:**
- `ToolStatusBar` class (lines 78-183) - entire class including:
  - SPINNER_FRAMES constant
  - IDLE_TEXT constant
  - `__init__`, `set_status`, `set_error`, `clear` methods
  - `_TOOL_NAME_PATTERNS` regex patterns
  - `_extract_tool_name`, `_update_display`, `_start_spinner`, `_stop_spinner`, `_advance_spinner` methods

### 2. `src/tunacode/cli/textual_repl.py`

**Remove from imports (lines 28-30):**
```python
ToolStatusBar,
ToolStatusClear,
ToolStatusUpdate,
```

**Remove from class attributes (line 81):**
```python
self.tool_status: ToolStatusBar
```

**Remove from compose() method:**
- Line 101: `self.tool_status = ToolStatusBar()`
- Line 114: Change `bottom_zone = Vertical(self.tool_status, command_row, id="bottom-zone")` to just yield command_row directly (remove bottom_zone wrapper)

**Remove event handlers:**
- `on_tool_status_update` method (lines 214-217)
- `on_tool_status_clear` method (lines 219-222)

**Remove from process_request call (line 155):**
```python
tool_status_callback=build_tool_status_callback(self),
```

**Remove callback builder function (lines 321-337):**
```python
def build_tool_status_callback(app: TextualReplApp):
    ...entire function...
```

### 3. `src/tunacode/cli/textual_repl.tcss`

**Remove #bottom-zone CSS (lines 51-55):**
```css
#bottom-zone {
    dock: bottom;
    height: auto;
    width: 100%;
}
```

**Remove ToolStatusBar CSS (lines 57-84):**
```css
ToolStatusBar { ... }
ToolStatusBar.active { ... }
ToolStatusBar.idle { ... }
ToolStatusBar.error { ... }
```

**Update #command-zone:** Add `dock: bottom;` since it's no longer wrapped in #bottom-zone

### 4. `src/tunacode/constants.py`

**Remove constants (lines 190-193):**
```python
# Tool status bar CSS classes
TOOL_STATUS_CLASS_ACTIVE = "active"
TOOL_STATUS_CLASS_IDLE = "idle"
TOOL_STATUS_CLASS_ERROR = "error"
```

### 5. `src/tunacode/core/agents/main.py`

**Remove from `process_request` function signature (~line 579):**
```python
tool_status_callback: Optional[Callable[[str], None]] = None,
```

**Remove from `RequestOrchestrator.__init__`:**
- Parameter (line 288-289): `tool_status_callback: Optional[Callable[[str], None]] = None,`
- Instance variable (line 296): `self.tool_status_callback = tool_status_callback`

**Remove from calls to `ac._process_node` (lines 405, 450):**
```python
self.tool_status_callback,  # remove this argument
```

**Remove from `_finalize_buffered_tasks`:**
- Parameter (line 526): `tool_status_callback: Optional[Callable[[str], None]] = None,`
- Status update try block (lines 534-542)
- Status clear try block (lines 547-552)

**Remove from calls to `_finalize_buffered_tasks` (lines ~405, ~450):**
Remove the `tool_status_callback` argument

### 6. `src/tunacode/core/agents/agent_components/node_processor.py`

**Remove helper functions:**
- `_update_tool_status` function (lines 23-42)
- `_clear_tool_status` function (lines 45-50)

**Remove from `_process_node` signature (line 86):**
```python
tool_status_callback: Optional[Callable[[str], None]] = None,
```

**Remove from `_process_tool_calls` signature (line 274-275):**
```python
tool_status_callback: Optional[Callable[[str], None]] = None,
```

**Remove all callback invocations in `_process_tool_calls`:**
- Line 327: `_update_tool_status(f"Researching: {query_preview}", tool_status_callback)`
- Line 348: `_clear_tool_status(tool_status_callback)`
- Line 360: `_update_tool_status(f"{batch_msg}...", tool_status_callback)`
- Line 380: `_clear_tool_status(tool_status_callback)`
- Line 393: `_update_tool_status(f"{tool_desc}...", tool_status_callback)`
- Line 428: `_clear_tool_status(tool_status_callback)`

**Remove from call to `_process_tool_calls` (inside `_process_node`):**
Remove `tool_status_callback` argument (~line 245)

## Data Flow Being Removed

```
UI Layer (textual_repl.py)
    │
    ├─ build_tool_status_callback() creates callback
    │
    ▼
Agent Layer (main.py)
    │
    ├─ process_request() receives callback
    ├─ RequestOrchestrator stores callback
    │
    ▼
Node Processing (node_processor.py)
    │
    ├─ _process_node() receives callback
    ├─ _process_tool_calls() receives callback
    ├─ _update_tool_status() / _clear_tool_status() invoke callback
    │
    ▼
UI Layer (textual_repl.py)
    │
    ├─ ToolStatusUpdate / ToolStatusClear messages posted
    ├─ on_tool_status_update() / on_tool_status_clear() handlers
    │
    ▼
Widget (widgets.py)
    │
    └─ ToolStatusBar.set_status() / .clear() update display
```

## Key Patterns / Solutions Found

| Pattern | Description |
|---------|-------------|
| Message passing | Uses Textual Message classes for thread-safe UI updates |
| Callback threading | Synchronous callback passed through entire agent stack |
| Best-effort updates | Status updates wrapped in try/except to not break agent |
| Rich markup stripping | Removes `[markup]` from status strings before display |

## Layout Impact

**Before removal:**
```
┌─────────────────────────────────────────────┐
│ ResourceBar (top)                           │
├─────────────────────────────────────────────┤
│ RichLog (1fr - main viewport)               │
├─────────────────────────────────────────────┤
│ ToolStatusBar ← REMOVE THIS                 │
├──────────┬──────────────────────────────────┤
│ Context  │   Editor                         │
└──────────┴──────────────────────────────────┘
```

**After removal:**
```
┌─────────────────────────────────────────────┐
│ ResourceBar (top)                           │
├─────────────────────────────────────────────┤
│ RichLog (1fr - main viewport)               │
├──────────┬──────────────────────────────────┤
│ Context  │   Editor                         │
└──────────┴──────────────────────────────────┘
```

## Knowledge Gaps

- None - all code paths are documented and understood

## Verification Checklist

After removal, verify:
- [ ] App launches without errors
- [ ] Tool execution still works (results display in RichLog via tool_result_callback)
- [ ] No orphaned imports or undefined references
- [ ] CSS compiles without warnings
- [ ] `ruff check --fix .` passes

## References

- `src/tunacode/cli/widgets.py:78-183` - ToolStatusBar widget
- `src/tunacode/cli/textual_repl.py:321-337` - build_tool_status_callback
- `src/tunacode/core/agents/agent_components/node_processor.py:23-50` - Helper functions
- `src/tunacode/cli/textual_repl.tcss:57-84` - CSS styles
