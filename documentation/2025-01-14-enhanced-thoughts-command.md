# Enhanced /thoughts Command Implementation

**Date**: 2025-01-14
**Title**: Comprehensive LLM Process Visibility Enhancement

## Overview

Enhanced the `/thoughts` command to provide complete visibility into the LLM's reasoning process, tool usage, and context management. When enabled, it now displays all relevant information inline during agent processing without requiring additional commands or complexity.

## Changes Implemented

### 1. State Management Enhancement
**File**: `src/tunacode/core/state.py`

Added new tracking fields to `SessionState`:
- `files_in_context: set[str]` - Tracks all files read during the session
- `tool_calls: list[dict[str, Any]]` - Records all tool calls with their arguments
- `iteration_count: int` - Total iterations for current request
- `current_iteration: int` - Current iteration number

### 2. Token Counting Utility
**File**: `src/tunacode/utils/token_counter.py` (new)

Created simple token estimation utility:
- Character-based approximation (~4 characters per token)
- Provides rough token counts for LLM responses
- Can be upgraded to use tiktoken for more accuracy

### 3. Enhanced Process Node Display
**File**: `src/tunacode/core/agents/main.py`

Modified `_process_node()` to display comprehensive information when thoughts are enabled:
- **LLM Responses**: Shows actual response text (truncated to 500 chars)
- **Token Counts**: Displays estimated tokens for each response
- **Tool Calls**: Shows tool name and full arguments in JSON format
- **File Tracking**: Updates and displays files in context when read_file is called
- **Tool Results**: Shows truncated results (200 chars) from tool executions
- **No Emojis**: Removed all emoji indicators per requirements

### 4. Iteration Tracking
**File**: `src/tunacode/core/agents/main.py`

Enhanced `process_request()` to:
- Track and display iteration progress
- Show cumulative tool usage summary
- Reset tracking for each new request
- Display warnings when reaching max iterations

### 5. Request Processing Updates
**File**: `src/tunacode/cli/repl.py`

Modified to:
- Clear tool tracking at start of each request
- Maintain cumulative file context across session
- Initialize tracking state when thoughts are enabled

## Display Format

When `/thoughts on` is enabled, users see:

```
THOUGHT: I need to read the configuration file

TOOL: read_file
ARGS: {
  "file_path": "/home/user/config.json"
}

FILES IN CONTEXT: ['/home/user/config.json']

TOOL RESULT: {"api_key": "...", "model": "gpt-4"}...

RESPONSE: The configuration shows that the API key is set...
TOKENS: ~125

ITERATION: 1/20
TOOLS USED: read_file: 1

TOOL: write_file
ARGS: {
  "file_path": "/home/user/output.txt",
  "content": "Analysis complete..."
}

ITERATION: 2/20
TOOLS USED: read_file: 1, write_file: 1
```

## Benefits

1. **Complete Visibility**: Users can see exactly what the LLM is thinking and doing
2. **Tool Transparency**: Full arguments for all tool calls are displayed
3. **Context Awareness**: Track which files are loaded into the agent's context
4. **Performance Insights**: Token counts and iteration tracking help understand costs
5. **Simple Interface**: Just `/thoughts on` - no additional commands needed

## Testing

- All existing tests pass
- Code has been linted and formatted
- Manual testing confirms enhanced display works correctly

## Future Enhancements

- More accurate token counting with tiktoken
- Configurable verbosity levels
- Export thoughts to file for debugging
- Real-time cost estimation based on token usage
