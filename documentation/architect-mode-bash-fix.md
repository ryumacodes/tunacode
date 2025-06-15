# Architect Mode Bash Tool Integration Fix

## Date: 2025-01-15

## Problem Statement

The architect mode was failing with timeout errors when trying to execute tasks that required filesystem operations. The specific issues were:

1. **ReadOnlyAgent lacked bash tool access** - When architect mode used ReadOnlyAgent for non-mutating tasks, it couldn't execute shell commands like `ls`
2. **Planner prompt didn't list bash as available** - The constrained planner wasn't aware bash was an option
3. **Broad grep patterns caused timeouts** - Single-letter searches would scan entire repositories
4. **No fallback for directory listing** - When bash wasn't available, there was no alternative

Example of the failing behavior:
```
User: tell me about @TUNACODE.md and how it relates to the codebase

[Task 2] READ
  → List all files and directories to understand the overall structure of the codebase.

╭─ ● TunaCode ─────────────────────────────────────────────────────────────────╮
│  I am sorry, I cannot fulfill your request. The ls command is not available  │
│  in the current environment. I can, however, read files or search for        │
│  content within them using the read_file and grep commands.                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Solution Overview

We implemented a comprehensive fix following Claude Code's architecture patterns:

### 1. Added Bash Tool to ReadOnlyAgent
- Updated `/src/tunacode/core/agents/readonly.py` to include bash tool
- Modified system prompt to clarify bash capability for inspection purposes
- Enables read-only operations like `ls`, `find`, `pwd` in parallel execution

### 2. Updated Architect Planner Prompt
- Added bash to available tools list in `/src/tunacode/prompts/architect_planner.md`
- Added examples showing bash usage for filesystem operations
- Added critical rules clarifying bash can be used for both read/write operations

### 3. Enhanced Orchestrator Tool Formatting
- Added bash case to `_format_tool_request()` in adaptive_orchestrator.py
- Properly formats bash commands for execution

### 4. Created Code Index System
- Implemented `/src/tunacode/core/code_index.py` for fast file lookups
- Maintains in-memory indices:
  - Basename to path mappings
  - Python import tracking
  - Class and function definitions
  - Directory content caching
- Prevents O(n) repository scans for every query

### 5. Updated RequestAnalyzer
- Replaced first-letter fallback with CodeIndex lookups
- Generates precise patterns like `\bFILENAME\b` instead of single letters
- Returns None for ambiguous short terms to trigger LLM clarification

### 6. Added Grep Timeout Handling
- Implemented 3-second timeout for first match (FIRST_MATCH_DEADLINE)
- Added `TooBroadPatternError` exception
- Properly kills hanging grep processes
- Integrates with retry mechanism

### 7. Enhanced Feedback Loop
- Added handling for `TooBroadPatternError`
- Implements retry budget (max 2 retries per pattern)
- Pattern narrowing logic adds word boundaries or anchors
- Added "reason" field for better diagnostics

### 8. Created list_dir Tool
- Lightweight alternative to bash ls using os.scandir
- Supports pagination (200 entries max)
- Shows file type indicators (/, *, @)
- Handles permission errors gracefully

## Technical Implementation Details

### Code Index Architecture
```python
class CodeIndex:
    def __init__(self):
        self._basename_to_paths = {}  # {basename: [paths]}
        self._path_to_imports = {}    # {path: [imports]}
        self._class_definitions = {}  # {class_name: [paths]}
        self._function_definitions = {}  # {func_name: [paths]}
        self._dir_cache = {}  # {dir: [contents]}
```

### Grep Timeout Flow
```python
# In grep tool
if time.time() > deadline and not first_match_found:
    process.kill()
    raise TooBroadPatternError(f"Pattern too broad, timeout after {timeout}s")

# In feedback loop
if isinstance(error, TooBroadPatternError):
    if self.retry_budget.get(pattern, 0) < 2:
        return FeedbackDecision.RETRY with narrowed_pattern
    else:
        return FeedbackDecision.ERROR
```

### Tool Integration
All agents now have access to 7 internal tools:
1. `read_file` - Read file contents
2. `write_file` - Create new files
3. `update_file` - Modify existing files
4. `run_command` - Execute shell commands
5. `bash` - Enhanced bash execution
6. `grep` - Pattern search with timeout
7. `list_dir` - Directory listing

## Results

After implementation, the same query works correctly:

```
User: tell me about @TUNACODE.md and how it relates to the codebase

[Task 1] READ
  → Read the contents of TUNACODE.md
[Task 2] READ  
  → Execute bash command: ls -la
[Task 3] READ
  → Analyze the content and project structure

All tasks complete successfully without timeouts.
```

## Performance Improvements

1. **File lookups**: O(n) grep searches → O(1) index lookups
2. **Timeout prevention**: Broad patterns fail fast (3s) instead of hanging
3. **Parallel execution**: Read-only tasks with bash execute concurrently
4. **Fallback options**: list_dir provides alternative when bash unavailable

## Files Modified

- `/src/tunacode/core/agents/readonly.py` - Added bash tool
- `/src/tunacode/prompts/architect_planner.md` - Updated available tools
- `/src/tunacode/core/agents/adaptive_orchestrator.py` - Added bash formatting
- `/src/tunacode/core/code_index.py` - New file index system
- `/src/tunacode/core/analysis/request_analyzer.py` - Use CodeIndex
- `/src/tunacode/tools/grep.py` - Added timeout handling
- `/src/tunacode/exceptions.py` - Added TooBroadPatternError
- `/src/tunacode/core/analysis/feedback_loop.py` - Handle timeouts
- `/src/tunacode/tools/list_dir.py` - New directory listing tool
- `/src/tunacode/core/agents/main.py` - Integrated list_dir tool
- `/src/tunacode/constants.py` - Added TOOL_LIST_DIR constant

## Testing

Created comprehensive tests:
- `/tests/test_grep_timeout.py` - Tests grep timeout behavior
- `/tests/test_list_dir.py` - Tests directory listing tool

All tests pass successfully, confirming the implementation works as expected.

## Conclusion

This fix ensures architect mode can properly execute filesystem operations through:
1. Proper bash tool integration in all agents
2. Fast file lookups preventing timeout-prone searches  
3. Graceful timeout handling with automatic retry
4. Fallback tools for common operations

The implementation follows Claude Code's patterns for reliability and performance.