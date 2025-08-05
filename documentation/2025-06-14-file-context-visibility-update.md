# File Context Visibility Update

**Date**: 2025-06-14
**Author**: TunaCode Development Team
**Type**: Enhancement

## Summary

Enhanced the @ file reference system to track referenced files in the `files_in_context` state, providing better visibility into which files have been loaded during a session.

## Changes Made

### 1. Modified `expand_file_refs()` Function

**File**: `src/tunacode/utils/text_utils.py`

- Changed return type from `str` to `Tuple[str, List[str]]`
- Now returns both the expanded text and a list of absolute file paths that were successfully expanded
- Ensures all tracked paths are absolute for consistency

### 2. Updated REPL Processing

**File**: `src/tunacode/cli/repl.py`

- Updated both architect mode and normal mode processing to capture file paths from `expand_file_refs()`
- Added logic to add @ referenced files to `state_manager.session.files_in_context`
- Maintains consistency with files tracked via the `read_file` tool

### 3. Updated Textual Bridge

**File**: `src/tunacode/cli/textual_bridge.py`

- Updated to handle the new tuple return value from `expand_file_refs()`
- Ensures @ file references are tracked in Textual UI mode as well

### 4. Updated Tests

**File**: `tests/test_file_reference_expansion.py`

- Updated all existing tests to handle the new tuple return value
- Added assertions to verify file path tracking
- Added new test `test_file_path_tracking()` to specifically test path tracking functionality

### 5. Added Integration Tests

**File**: `tests/test_file_reference_context_tracking.py` (new)

- Comprehensive tests for the integration between @ file references and `files_in_context`
- Tests for absolute path conversion, duplicate handling, and various file types

## Benefits

1. **Better Session Awareness**: All files accessed in a session (via @ references or `read_file` tool) are now tracked in one place
2. **Consistent Tracking**: Both @ file references and tool-based file reads use the same tracking mechanism
3. **Absolute Path Consistency**: All tracked paths are converted to absolute paths, preventing duplicates from relative/absolute path mismatches
4. **Enhanced Debugging**: When thoughts mode is enabled, users can see all files that have been loaded in the current context

## Usage Example

```python
# User input with @ file reference
"Please review @src/main.py and @tests/test_main.py"

# The system now:
# 1. Expands the file contents as before
# 2. Tracks both files in files_in_context
# 3. Shows them when thoughts mode is enabled
```

## Backward Compatibility

This change maintains backward compatibility:
- The @ file reference syntax remains unchanged
- File expansion behavior is identical
- Only internal tracking is enhanced

## Technical Details

### File Path Tracking Flow

1. User inputs text with @ references
2. `expand_file_refs()` processes the text:
   - Expands file contents into code blocks
   - Collects absolute paths of all referenced files
3. REPL adds these paths to `state_manager.session.files_in_context`
4. Files remain tracked for the entire session
5. Cleared only with `/clear` command

### Integration with Existing Features

- **Thoughts Mode**: When enabled, shows all files in context
- **Clear Command**: Clears both message history and file context
- **Read File Tool**: Continues to track files it reads (no changes needed)
