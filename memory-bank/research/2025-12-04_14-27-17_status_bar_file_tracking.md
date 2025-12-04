# Research – Status Bar File Tracking

**Date:** 2025-12-04
**Owner:** Claude Agent
**Phase:** Research

## Goal

Understand how to track files edited by tunacode and display them in the status bar's `#status-mid` section.

## Findings

### Relevant Files & Why They Matter

| File | Purpose |
|------|---------|
| `src/tunacode/ui/widgets/status_bar.py` | Status bar widget with 3 zones: left (branch/dir), mid (bg status), right (files edited placeholder) |
| `src/tunacode/ui/app.py:287-307` | `build_tool_result_callback()` - receives tool completion events with name, status, args |
| `src/tunacode/ui/app.py:310-314` | `build_tool_start_callback()` - receives tool start events |
| `src/tunacode/tools/write_file.py` | `write_file(filepath, content)` - creates new files |
| `src/tunacode/tools/update_file.py` | `update_file(filepath, target, patch)` - modifies existing files |
| `src/tunacode/core/agents/agent_components/node_processor.py:359-369` | Tracks all tool calls in `session.tool_calls` |
| `src/tunacode/core/agents/agent_components/agent_helpers.py:197-208` | Existing file extraction logic (has bug: looks for `file_path` not `filepath`) |

### Current Architecture

**Status Bar Layout** (`status_bar.py:16-19`):
```python
def compose(self) -> ComposeResult:
    yield Static("main ● ~/proj", id="status-left")   # Branch & directory
    yield Static("bg: idle", id="status-mid")         # Currently: tool name
    yield Static("files edited: -", id="status-right") # Placeholder!
```

**Tool Result Callback Flow**:
1. Tool executes in `node_processor.py:321-357`
2. `tool_result_callback(tool_name, status, args)` called at line 352-357
3. `build_tool_result_callback()` in `app.py:287-307` receives this
4. Currently only updates `status_bar.update_last_action(tool_name)` at line 295

**Tool Args Structure**:
- `write_file` args: `{"filepath": str, "content": str}`
- `update_file` args: `{"filepath": str, "target": str, "patch": str}`
- Key: `filepath` (NOT `file_path`)

### Data Flow Diagram

```
Tool Execution (node_processor.py:352)
    │
    ├── tool_result_callback(tool_name="write_file", args={"filepath": "/path/to/file.py", ...})
    │       │
    │       └── build_tool_result_callback (app.py:287)
    │               │
    │               ├── app.status_bar.update_last_action(tool_name)  # Current
    │               │
    │               └── [NEW] if tool_name in ["write_file", "update_file"]:
    │                         app.status_bar.add_edited_file(args["filepath"])
    │
    └── session.tool_calls.append({"tool": tool_name, "args": args})
```

## Key Patterns / Solutions Found

### Pattern 1: File Extraction from Args
```python
# In tool_result_callback
if tool_name in ["write_file", "update_file"] and "filepath" in args:
    filepath = args["filepath"]
    # Extract filename: os.path.basename(filepath)
```

### Pattern 2: Status Bar State Management
```python
class StatusBar(Horizontal):
    _edited_files: set[str] = set()  # Track unique files

    def add_edited_file(self, filepath: str) -> None:
        self._edited_files.add(os.path.basename(filepath))
        count = len(self._edited_files)
        display = ", ".join(sorted(self._edited_files)[:3])  # Show first 3
        if count > 3:
            display += f" +{count - 3}"
        self.query_one("#status-mid", Static).update(f"edited: {display}")

    def clear_edited_files(self) -> None:
        self._edited_files.clear()
        self.query_one("#status-mid", Static).update("bg: idle")
```

### Pattern 3: Alternative - Use Right Zone
The `#status-right` already has "files edited: -" placeholder. Could update that instead:
```python
def update_files_edited(self, count: int, files: list[str]) -> None:
    if count == 0:
        self.query_one("#status-right", Static).update("files edited: -")
    else:
        names = ", ".join(files[:2])
        text = f"files: {names}" + (f" +{count-2}" if count > 2 else "")
        self.query_one("#status-right", Static).update(text)
```

## Implementation Options

### Option A: Track in StatusBar (Recommended)
- Add `_edited_files: set[str]` to StatusBar class
- Add `add_edited_file()` and `clear_edited_files()` methods
- Modify `build_tool_result_callback()` to check tool name and extract filepath
- Clear on new request start

**Pros**: Simple, self-contained in status bar
**Cons**: State duplicated (also in session.tool_calls)

### Option B: Query Session State
- Pull from `state_manager.session.tool_calls` periodically
- Filter for write_file/update_file tools
- Extract filepaths

**Pros**: Single source of truth
**Cons**: Requires access to state_manager from StatusBar

### Option C: Use Textual Message
- Create `FileEditedMessage(filename: str)` message type
- Post message from tool_result_callback
- StatusBar handles message and updates display

**Pros**: Decoupled, follows Textual patterns
**Cons**: More complex, additional message type

## Knowledge Gaps

1. **Clearing**: When should the file list be cleared? Per request? Per session?
2. **Display Limit**: How many files should be shown before truncating?
3. **Zone Choice**: Should this use `#status-mid` (replacing bg status) or `#status-right` (replacing files edited placeholder)?
4. **Bash Tool**: Should files modified via `bash` commands also be tracked? (Much harder to detect)

## References

- `src/tunacode/ui/widgets/status_bar.py` - Current status bar implementation
- `src/tunacode/ui/app.py:287-314` - Callback builders
- `src/tunacode/core/agents/agent_components/node_processor.py:321-369` - Tool execution flow
- `src/tunacode/constants.py:63-72` - WRITE_TOOLS constant definition
