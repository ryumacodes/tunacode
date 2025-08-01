# File Context Visibility Improvements

**Date**: 2025-06-14
**Title**: Always Show Files in Context and Simplify Thoughts Display

## Overview

This update addresses visibility issues with file context tracking. Previously, files in context were only shown when `/thoughts on` was enabled, and the tool arguments display was too verbose. The good news is that files referenced with `@` syntax were already being properly tracked.

## Issues Identified

1. **Hidden File Context**: Files loaded into the agent's context (via `@` mentions or read_file tool) were only visible when thoughts mode was enabled
2. **Verbose Tool Display**: Tool arguments were shown as full JSON dumps, making the output hard to read
3. **Poor User Experience**: Users couldn't see what files the agent had access to unless they enabled thoughts mode

## Changes Implemented

### 1. Always Display File Context
**File**: `src/tunacode/core/agents/main.py`

Modified the agent's response handling to always show files in context after each response, regardless of thoughts mode:
- Added a new section after agent responses showing "Files in context: [list]"
- Shows only filenames (not full paths) for better readability
- Updates after every file read operation

### 2. Simplified Tool Arguments Display
**File**: `src/tunacode/core/agents/main.py`

When thoughts mode is enabled, tool arguments are now displayed more concisely:
- `read_file`: Shows only "Reading: filename.py" instead of full JSON
- `write_file`: Shows "Writing: filename.py"
- `update_file`: Shows "Updating: filename.py"
- `run_command`: Shows the command being run
- Other tools: Show simplified argument summary

### 3. @ Reference Tracking (Already Working)
**Files**: `src/tunacode/utils/text_utils.py`, `src/tunacode/cli/repl.py`

Verified that files referenced with `@` syntax were already properly tracked:
- `expand_file_refs()` already returns both expanded text and list of referenced files
- REPL already adds @ referenced files to `state_manager.session.files_in_context`
- Consistency between @ references and read_file tool was already maintained

### 4. Display Format

The new display format shows:

**Without thoughts mode:**
```
[Agent response here]

Files in context: config.json, main.py, utils.py
```

**With thoughts mode enabled:**
```
THOUGHT: I need to check the configuration

TOOL: read_file
Reading: config.json

FILES IN CONTEXT: [config.json, main.py, utils.py]

[Rest of thoughts display...]
```

## Benefits

1. **Transparency**: Users always know what files the agent has access to
2. **Clarity**: Simplified tool display reduces noise while maintaining detail when needed
3. **Consistency**: All file access methods (@ references and tools) are tracked uniformly
4. **Better UX**: Critical information is always visible without requiring special modes

## Testing

- Verified @ file references are tracked correctly
- Confirmed file context displays after each agent response
- Tested thoughts mode shows simplified tool arguments
- Ensured backward compatibility with existing functionality
