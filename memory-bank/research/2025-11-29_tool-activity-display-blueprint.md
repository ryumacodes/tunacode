---
date: 2025-11-29T00:00:00-05:00
researcher: Claude
git_commit: 281694d31f881498fd5002621b2d08d7926b1cb0
branch: textual_repl
repository: tunacode
topic: "Tool Activity Display Integration for Textual TUI"
tags: [research, codebase, textual, tool-output, ui-patterns, blueprint]
status: complete
last_updated: 2025-11-29
last_updated_by: Claude
---

# Research: Tool Activity Display Integration for Textual TUI

**Date**: 2025-11-29
**Researcher**: Claude
**Git Commit**: 281694d31f881498fd5002621b2d08d7926b1cb0
**Branch**: textual_repl
**Repository**: tunacode

## Research Question

After migrating from promptkit+Rich to Textual, real-time tool activity feedback (e.g., "Reading file: X", "Searching for: pattern") was lost. Where should this be integrated and what pattern should be used?

## Summary

The Textual app currently has:
- `streaming_callback` for text content from the agent
- `tool_callback` for tool confirmation modals only

Missing: A mechanism to display real-time tool activity status. The old Rich REPL used `ui.muted()` and `ui.update_spinner_message()` which wrote directly to console - incompatible with Textual's managed display.

**Solution**: Add a `ToolStatusWidget` with a `tool_status_callback` following the same pattern as `streaming_callback`.

## Detailed Findings

### Current Textual App Structure

**File**: `src/tunacode/cli/textual_repl.py`

```
TextualReplApp
  - Header()
  - ResourceBar()              # Custom widget: shows model, tokens, cost
  - Vertical(id="body")
    - RichLog()                # Persistent message history
    - Static(id="streaming-output")  # Live streaming text
    - Editor()                 # User input
  - Footer()
```

**Key Components**:
- `TextualReplApp` (line 44): Main app class
- `streaming_callback` (line 157-165): Receives text chunks, updates `current_stream_text`
- `build_textual_tool_callback` (line 222-242): Only handles tool confirmation, not activity display

### Where Tool Activity Originates

**File**: `src/tunacode/core/agents/agent_components/node_processor.py`

The `_process_tool_calls()` function (line 309) generates tool activity messages:

| Line | Function Call | Purpose |
|------|--------------|---------|
| 344 | `ui.muted("STATE -> TOOL_EXECUTION")` | Debug state transition |
| 352 | `ui.muted(f"COLLECTED: {tool_name}")` | Tool collection notification |
| 397 | `ui.research_agent(panel_text)` | Research agent panel |
| 401-404 | `ui.update_spinner_message()` | Research progress |
| 443-450 | `ui.update_spinner_message()` | Batch collection/execution |
| 478 | `ui.batch(batch_content)` | Batch execution panel |
| 501-503 | `ui.update_spinner_message()` | Sequential tool status |

### Current UI Output Functions

**File**: `src/tunacode/ui/output.py`

```python
# Line 93-95: muted() writes to Rich console
async def muted(text: str) -> None:
    await print(text, style=colors.muted)

# Line 177-188: update_spinner_message() updates Rich Status
async def update_spinner_message(message: str, state_manager: StateManager = None):
    if state_manager and state_manager.session.spinner:
        await run_in_terminal(lambda: spinner_obj.update(message))
```

**Problem**: These use `run_in_terminal()` which writes to Rich console directly, bypassing Textual's display management.

### Tool Description Helpers

**File**: `src/tunacode/ui/tool_descriptions.py`

Provides human-readable tool descriptions:

```python
# Line 6-88: get_tool_description()
"read_file" -> "Reading file: {file_path}"
"grep" -> "Searching files for: {pattern}"
"run_command" -> "Executing command: {cmd}"

# Line 91-115: get_batch_description()
"Reading 5 files in parallel"
"Executing 3 tools in parallel"
```

### Existing Message Pattern

**File**: `src/tunacode/cli/widgets.py` and `textual_repl.py`

The codebase already uses Textual Messages for component communication:

```python
# widgets.py line 21-35
class EditorCompletionsAvailable(Message):
    def __init__(self, *, candidates: Iterable[str]) -> None:
        self.candidates = list(candidates)

class EditorSubmitRequested(Message):
    def __init__(self, *, text: str, raw_text: str) -> None:
        self.text = text

# textual_repl.py line 36-41
class ShowToolConfirmationModal(Message):
    def __init__(self, *, request: ToolConfirmationRequest) -> None:
        self.request = request
```

### Callback Type Definition

**File**: `src/tunacode/types.py`

```python
# Line 86
ToolCallback = Callable[[Any, Any], Awaitable[None]]

# Line 135
UICallback = Callable[[str], Awaitable[None]]  # <-- Use this pattern
```

## Blueprint: ToolStatusWidget Pattern

### 1. Define Message Class

**Add to**: `src/tunacode/cli/widgets.py`

```python
class ToolStatusUpdate(Message):
    """Update the tool status display."""

    def __init__(self, *, status: str, tool_name: str = "", is_batch: bool = False) -> None:
        super().__init__()
        self.status = status
        self.tool_name = tool_name
        self.is_batch = is_batch


class ToolStatusClear(Message):
    """Clear the tool status display."""
    pass
```

### 2. Create Widget Class

**Add to**: `src/tunacode/cli/widgets.py`

```python
class ToolStatusBar(Static):
    """Widget displaying current tool activity status."""

    DEFAULT_CSS = """
    ToolStatusBar {
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    ToolStatusBar.active {
        color: $primary;
    }
    """

    def __init__(self) -> None:
        super().__init__("")
        self._status: str = ""

    def set_status(self, status: str) -> None:
        self._status = status
        if status:
            self.add_class("active")
            self.update(Text(status, style="dim cyan"))
        else:
            self.remove_class("active")
            self.update("")

    def clear(self) -> None:
        self.set_status("")
```

### 3. Integrate into App

**Modify**: `src/tunacode/cli/textual_repl.py`

```python
# In __init__:
self.tool_status: ToolStatusBar = ToolStatusBar()

# In compose():
yield Vertical(
    self.rich_log,
    self.tool_status,        # <-- Add between log and streaming
    self.streaming_output,
    self.editor,
    id="body"
)

# Add handler:
def on_tool_status_update(self, message: ToolStatusUpdate) -> None:
    self.tool_status.set_status(message.status)

def on_tool_status_clear(self, message: ToolStatusClear) -> None:
    self.tool_status.clear()
```

### 4. Create Callback Builder

**Add to**: `src/tunacode/cli/textual_repl.py`

```python
def build_tool_status_callback(app: TextualReplApp):
    """Create a callback that updates tool status in the Textual app."""

    async def _status_callback(status: str) -> None:
        app.post_message(ToolStatusUpdate(status=status))

    return _status_callback
```

### 5. Wire into Agent Orchestration

**Modify**: `src/tunacode/core/agents/main.py`

Add a new parameter `tool_status_callback: Optional[UICallback] = None` to `process_request()`.

**Modify**: `src/tunacode/core/agents/agent_components/node_processor.py`

Replace `ui.update_spinner_message()` calls with the callback:

```python
# Before (line 448-450):
await ui.update_spinner_message(
    f"[bold {colors.primary}]{batch_msg}...[/bold {colors.primary}]", state_manager
)

# After:
if tool_status_callback:
    await tool_status_callback(batch_msg)
```

## Alternative Approaches

### A. Status Line Above Streaming (Recommended)
- Add `ToolStatusBar` between `RichLog` and `streaming_output`
- Minimal visual footprint, always visible during activity
- Auto-clears when tool execution completes

### B. Overlay on Streaming Output
- Modify `streaming_output` Static to include status prefix
- More integrated but may conflict with content display

### C. Use ResourceBar
- Add tool status to existing `ResourceBar` widget
- Reuses existing component but may overcrowd the bar

### D. Log to RichLog
- Write tool activity to `rich_log.write()`
- Creates permanent history but clutters conversation log

## Code References

| File | Line | Purpose |
|------|------|---------|
| `cli/textual_repl.py` | 44 | TextualReplApp class |
| `cli/textual_repl.py` | 69-73 | compose() widget layout |
| `cli/textual_repl.py` | 109-110 | Callback wiring in process_request |
| `cli/textual_repl.py` | 157-165 | streaming_callback implementation |
| `cli/widgets.py` | 21-35 | Message class pattern |
| `cli/widgets.py` | 38-78 | ResourceBar widget pattern |
| `core/agents/agent_components/node_processor.py` | 309-561 | Tool processing with status updates |
| `ui/output.py` | 177-188 | Current update_spinner_message |
| `ui/tool_descriptions.py` | 6-88 | Human-readable tool descriptions |
| `types.py` | 135 | UICallback type definition |

## Architecture Documentation

### Callback Flow (Current)
```
User Input -> Editor.action_submit() -> EditorSubmitRequested
           -> on_editor_submit_requested() -> request_queue
           -> _process_request() -> process_request()
           -> AgentOrchestrator -> node_processor
           -> tool_callback (confirmation only)
           -> streaming_callback (text content)
```

### Callback Flow (With Tool Status)
```
node_processor._process_tool_calls()
    -> tool_status_callback(status_message)
    -> app.post_message(ToolStatusUpdate)
    -> on_tool_status_update()
    -> tool_status.set_status()
```

## Implementation Checklist

1. [ ] Add `ToolStatusUpdate` and `ToolStatusClear` messages to `widgets.py`
2. [ ] Add `ToolStatusBar` widget to `widgets.py`
3. [ ] Add `tool_status` to `TextualReplApp.__init__`
4. [ ] Add `tool_status` to `compose()` layout
5. [ ] Add `on_tool_status_update` handler
6. [ ] Add `build_tool_status_callback` function
7. [ ] Add `tool_status_callback` parameter to `process_request()`
8. [ ] Replace `ui.update_spinner_message()` calls in `node_processor.py`
9. [ ] Add TCSS styling for `ToolStatusBar`
10. [ ] Test with read-only tool batches
11. [ ] Test with sequential write tools
12. [ ] Test with research agent

## Open Questions

1. Should tool status persist briefly after completion or clear immediately?
2. Should batch execution show individual tool progress or just "Executing N tools"?
3. Should errors in tool execution be shown in the status bar or only in RichLog?
