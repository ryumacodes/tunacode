# TunaCode CLI Agent Flows Documentation

## Agent Tooling System Overview

The TunaCode CLI provides a robust tooling system for AI agents to interact with the filesystem and execute commands. This document explains the architecture, available tools, and execution flows.

## Available Tools

The TunaCode CLI provides **4 internal tools** out of the box:

### 1. Read File Tool (`read_file`)
- Reads file contents with UTF-8 encoding
- Has a 100KB file size limit
- Returns file content or specific error messages for common issues
- Location: `src/tunacode/tools/read_file.py`

### 2. Write File Tool (`write_file`)
- Creates new files only (fails if file exists)
- Automatically creates parent directories
- Guides the agent to use `update_file` for existing files via ModelRetry
- Location: `src/tunacode/tools/write_file.py`

### 3. Update File Tool (`update_file`)
- Updates existing files using target/patch semantics
- Replaces exact text blocks (first occurrence only)
- Provides helpful context when target text is not found
- Location: `src/tunacode/tools/update_file.py`

### 4. Run Command Tool (`run_command`)
- Executes shell commands via subprocess
- Captures both stdout and stderr
- Truncates output if it exceeds 5000 characters (shows beginning and end)
- Location: `src/tunacode/tools/run_command.py`

## Tool Implementation Architecture

### Base Classes

1. **`BaseTool`** (`src/tunacode/tools/base.py:19`)
   - Abstract base class providing:
   - Error handling with structured exceptions
   - UI logging of tool operations
   - ModelRetry support for guiding the LLM
   - Argument formatting for display
   - Template method pattern with `execute()` wrapper calling `_execute()`

2. **`FileBasedTool`** - Extends BaseTool for file operations:
   - File-specific error handling (IOError, PermissionError, etc.)
   - Specialized error context for file paths
   - Converts file errors to `FileOperationError`

### Key Methods
- `execute()`: Public wrapper with error handling and logging
- `_execute()`: Tool-specific implementation (abstract)
- `_handle_error()`: Error processing and exception raising
- `_format_args()`: Formats arguments for UI display (truncates long strings)
- `tool_name`: Property defining the tool's display name

## Tool Execution Flow

1. **Agent calls tool** via pydantic-ai framework
2. **Tool callback** (`_tool_handler` in `src/tunacode/cli/repl.py`) is invoked
3. **Confirmation check** via `ToolHandler`:
   - Checks if tool requires confirmation (based on YOLO mode and ignored tools)
   - Skips confirmation for previously approved tool types
4. **UI confirmation** (if needed):
   - Shows tool name, arguments, and relevant content
   - Special rendering for file updates (diffs) and writes (code blocks)
   - User can: approve, approve & skip future, or abort
5. **Tool execution**:
   - Tool's `execute()` method called
   - Logs operation to UI
   - Executes tool-specific logic
   - Returns result or raises exceptions
6. **Error handling**:
   - `ModelRetry`: Re-raised to guide LLM
   - `ToolExecutionError`: Structured error with tool context
   - Other exceptions: Wrapped in ToolExecutionError

## UI Display of Tool Usage

The **`ToolUI`** class (`src/tunacode/ui/tool_ui.py`) handles all tool-related UI:

### Tool Titles
- Internal tools: `Tool(read_file)`
- MCP tools: `MCP(tool_name)`

### Argument Rendering
- **Update tool**: Shows colored diff between target and patch
- **Write tool**: Shows syntax-highlighted code block
- **Other tools**: Key-value pairs with smart formatting

### Confirmation Panel
Rich-styled panel with:
- Tool name in title
- Formatted arguments as content
- File path shown separately below panel
- Three options: Yes / Yes & skip future / No & abort

### MCP Tool Logging
When confirmation is skipped, MCP tools still log their arguments

## Confirmation/Approval Flow

### ToolHandler Management
- `should_confirm()`: Checks YOLO mode and ignored tools list
- `process_confirmation()`: Handles user response
- `create_confirmation_request()`: Packages tool info for UI

### Confirmation States
- **YOLO mode** (`/yolo` command): Skips all confirmations
- **Tool ignore list**: Tools marked "don't ask again"
- **Per-request approval**: Default behavior

### User Responses
- **Option 1 (Yes)**: Execute tool once
- **Option 2 (Yes & skip)**: Execute and add to ignore list
- **Option 3 (No & abort)**: Raise UserAbortError

### Sync vs Async Handling
- REPL uses `run_in_terminal` with sync confirmation to avoid event loop conflicts
- Direct CLI uses async confirmation flow

## Diff Generation System

The tunacode CLI uses **Python's built-in `difflib` library** for diff generation and display.

### Diff Creation Process
Location: `src/tunacode/utils/diff_utils.py:11`

The `render_file_diff()` function:
1. Takes `target` (original text) and `patch` (new text) as inputs
2. Splits both texts into lines
3. Uses `difflib.SequenceMatcher` to compare line sequences
4. Returns a Rich `Text` object with styled diff output

### Diff Formatting
The function processes opcodes from SequenceMatcher:
- **"equal"**: Unchanged lines shown with "  " prefix
- **"delete"**: Removed lines shown with "- " prefix (red if colors enabled)
- **"insert"**: Added lines shown with "+ " prefix (green if colors enabled)
- **"replace"**: Shows both deletions and insertions

### Integration with Tools
- The `update_file` tool uses simple `str.replace()` for the actual update
- Diffs are purely for visualization in the confirmation UI
- Colors: red for deletions, green for additions (when colors enabled)

## MCP (Model Context Protocol) Integration

- MCP servers provide additional tools beyond the 4 internal ones
- Configured in user's config file under `mcpServers`
- Tools from MCP servers are automatically discovered and made available
- MCP tools follow the same confirmation flow but are labeled differently in UI

## Error Handling

### Exception Hierarchy
- `TunaCodeError`: Base for all TunaCode exceptions
- `ToolExecutionError`: Tool-specific failures with context
- `FileOperationError`: File-related errors with operation and path
- `UserAbortError`: User cancelled the operation
- `ValidationError`: Invalid tool arguments

### Error Messages
- Structured with tool name, operation context, and original error
- File operations include the specific operation type and file path
- ModelRetry exceptions guide the LLM to correct behavior

## Summary

This architecture provides a robust, extensible tool system with:
- Clear separation between business logic, UI concerns, and error handling
- Safe-by-default operation with user confirmations
- Power user features (YOLO mode, tool ignore lists)
- Clean visualization of changes before execution
- Easy extensibility for new tools or MCP integrations