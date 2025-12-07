# Research – /debug Command & Unified Logging System

**Date:** 2025-12-06
**Owner:** claude-agent
**Phase:** Research
**git_commit:** 7815bf8fcc284f159a7eaab483f2711a8592f863

## Goal

Map the current logging infrastructure and command system to understand how to implement a `/debug` command that provides developer-like debug output with unified logging visibility.

## Findings

### 1. Current Logging Infrastructure

**Core Logging Location:** `src/tunacode/core/logging/`

| File | Purpose |
|------|---------|
| [`__init__.py`](https://github.com/alchemiststudiosDOTai/tunacode/blob/7815bf8/src/tunacode/core/logging/__init__.py) | Main logging setup, custom `thought` log level |
| [`config.py`](https://github.com/alchemiststudiosDOTai/tunacode/blob/7815bf8/src/tunacode/core/logging/config.py) | Logging configuration with DEBUG mode and handlers |
| [`logger.py`](https://github.com/alchemiststudiosDOTai/tunacode/blob/7815bf8/src/tunacode/core/logging/logger.py) | Logger factory `get_logger()` |
| [`formatters.py`](https://github.com/alchemiststudiosDOTai/tunacode/blob/7815bf8/src/tunacode/core/logging/formatters.py) | Custom log formatters |

**Key Patterns:**
- `setup_logging()` called at package import in `src/tunacode/__init__.py`
- `get_logger()` factory used throughout codebase
- Custom `thought` log level for agent reasoning
- 77+ log statements across 20 source files

**Heavy Logging Usage:**
- `tools/bash.py` - 8 log statements
- `tools/utils/ripgrep.py` - 13 log statements
- `indexing/code_index.py` - 12 log statements

**Current Gap:** Logs go to handlers (file/stream) but are NOT visible in the TUI. No way for developers to see live log output while using the application.

### 2. Command System Architecture

**Entry Point:** [`src/tunacode/ui/commands/__init__.py`](https://github.com/alchemiststudiosDOTai/tunacode/blob/7815bf8/src/tunacode/ui/commands/__init__.py)

**Pattern:**
```python
class Command(ABC):
    name: str
    description: str
    usage: str = ""

    @abstractmethod
    async def execute(self, app: TextualReplApp, args: str) -> None:
        pass

COMMANDS: dict[str, Command] = {
    "help": HelpCommand(),
    "clear": ClearCommand(),
    # ... register new commands here
}
```

**Dispatch Flow:**
1. User input → `Editor.action_submit()`
2. `EditorSubmitRequested` message → `app.on_editor_submit_requested()`
3. `handle_command(app, text)` → checks for `/` prefix
4. Parses command name, looks up in `COMMANDS` dict
5. Calls `command.execute(app, args)`

**Commands Have Access To:**
- `app.state_manager.session` - All session state (tokens, messages, tool_calls, etc.)
- `app.rich_log` - Main output widget (`.write()`, `.clear()`)
- `app.notify()` - Toast notifications
- `app.status_bar`, `app.resource_bar` - UI widgets

### 3. UI Output System

**Primary Output Widget:** `RichLog` in [`src/tunacode/ui/app.py`](https://github.com/alchemiststudiosDOTai/tunacode/blob/7815bf8/src/tunacode/ui/app.py)

**Renderers:** `src/tunacode/ui/renderers/`
- `panels.py` - `PanelType` enum (TOOL, ERROR, SEARCH, INFO, SUCCESS, WARNING)
- `errors.py` - Exception rendering with severity mapping
- `search.py` - Search result formatting

**Styling:**
- `src/tunacode/ui/styles.py` - Style constants (STYLE_ERROR, STYLE_WARNING, etc.)
- `src/tunacode/ui/app.tcss` - CSS styling for widgets

**Display Methods:**
- `app.rich_log.write(renderable)` - Write Rich objects to output
- `app.notify(message, severity)` - Toast notifications
- `tool_panel_smart()` - Create formatted tool execution panels

### 4. Session State Available for Debug Display

From `app.state_manager.session`:

| Field | Type | Description |
|-------|------|-------------|
| `total_tokens` | int | Current context window tokens |
| `max_tokens` | int | Maximum context size |
| `messages` | list | Conversation history |
| `tool_calls` | list | Recent tool invocations |
| `files_in_context` | set | Files in context window |
| `iteration_count` | int | Total agent iterations |
| `current_recursion_depth` | int | Current nesting level |
| `session_total_usage` | dict | API usage (cost, tokens) |
| `react_scratchpad` | dict | ReAct tool state |
| `yolo` | bool | Auto-confirm mode |

## Simplified Scope: Unified Log Viewer

**Goal:** `/debug` toggles unified log output in TUI. All logging from all modules visible in one place.

### Core Concept
```
/debug  → Toggle debug mode ON/OFF
```

When ON: All logs from `get_logger()` appear in `RichLog` with:
- Timestamp
- Level (color-coded)
- Module name
- Message

### Implementation Pattern

**1. MemoryHandler + TUI Bridge**
```python
# In logging config
class TUIHandler(logging.Handler):
    def __init__(self, callback):
        self.callback = callback  # Posts to TUI

    def emit(self, record):
        if self.callback:
            self.callback(self.format(record))
```

**2. Session State Toggle**
```python
# In state.py SessionState
debug_mode: bool = False
```

**3. Command**
```python
class DebugCommand(Command):
    name = "debug"
    description = "Toggle unified log output"

    async def execute(self, app, args):
        session = app.state_manager.session
        session.debug_mode = not session.debug_mode
        status = "ON" if session.debug_mode else "OFF"
        app.notify(f"Debug: {status}")
```

**4. Log Display** (when debug_mode is True)
- Logs render as muted text in RichLog
- Color by level: DEBUG=dim, INFO=blue, WARNING=yellow, ERROR=red
- Format: `[HH:MM:SS] [LEVEL] module: message`

## Implementation Checklist

- [ ] Add `debug_mode: bool` to `SessionState` in `src/tunacode/core/state.py`
- [ ] Create `TUIHandler` in `src/tunacode/core/logging/config.py`
- [ ] Wire handler to post messages to TUI when `debug_mode=True`
- [ ] Create `DebugCommand` in `src/tunacode/ui/commands/__init__.py`
- [ ] Register in `COMMANDS` dict
- [ ] Add log rendering with level-based colors

## References

### Core Files
- Logging: [`src/tunacode/core/logging/`](https://github.com/alchemiststudiosDOTai/tunacode/tree/7815bf8/src/tunacode/core/logging)
- Commands: [`src/tunacode/ui/commands/__init__.py`](https://github.com/alchemiststudiosDOTai/tunacode/blob/7815bf8/src/tunacode/ui/commands/__init__.py)
- App: [`src/tunacode/ui/app.py`](https://github.com/alchemiststudiosDOTai/tunacode/blob/7815bf8/src/tunacode/ui/app.py)
- Renderers: [`src/tunacode/ui/renderers/`](https://github.com/alchemiststudiosDOTai/tunacode/tree/7815bf8/src/tunacode/ui/renderers)
- Styles: [`src/tunacode/ui/styles.py`](https://github.com/alchemiststudiosDOTai/tunacode/blob/7815bf8/src/tunacode/ui/styles.py)

### Session State
- State: [`src/tunacode/core/state.py`](https://github.com/alchemiststudiosDOTai/tunacode/blob/7815bf8/src/tunacode/core/state.py)
