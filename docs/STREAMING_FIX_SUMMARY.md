# Fix for "Only one live display may be active at once" Error

## Problem Summary

After PR #41 implemented streaming-first UI, users encountered the error "Only one live display may be active at once" when trying to edit files or perform operations that require tool confirmations.

## Root Cause

The issue occurred because:
1. Rich library only allows one `Live` display at a time
2. Both the spinner (via `console.status()`) and the new `StreamingAgentPanel` use Rich's Live display system
3. During streaming, when a tool required confirmation, the code tried to manipulate the spinner while the streaming panel's Live display was active

## Solution Implemented

### 1. Added Streaming State Tracking

Added `is_streaming_active` flag to `SessionState` in `src/tunacode/core/state.py`:
```python
# Track streaming state to prevent spinner conflicts
is_streaming_active: bool = False
```

### 2. Updated Streaming Flow

Modified `process_request()` in `src/tunacode/cli/repl.py` to:
- Set `is_streaming_active = True` when streaming starts
- Set `is_streaming_active = False` when streaming ends

### 3. Protected Spinner Operations

Updated both `_tool_confirm()` and `_tool_handler()` to check the streaming state:
```python
# Stop spinner only if not streaming
if not state_manager.session.is_streaming_active and state_manager.session.spinner:
    state_manager.session.spinner.stop()
```

## Files Modified

1. `src/tunacode/core/state.py` - Added `is_streaming_active` flag
2. `src/tunacode/cli/repl.py` - Added streaming state management and spinner protection
3. `tests/test_streaming_spinner_conflict.py` - New test file to verify the fix

## Testing

Created comprehensive tests to verify:
1. Spinner operations are skipped when streaming is active
2. Spinner operations work normally when streaming is inactive
3. StreamingAgentPanel lifecycle works correctly
4. Integration test confirms no Rich.Live conflicts occur

## Result

The fix ensures that:
- When streaming is active, spinner operations are safely skipped
- Tool confirmations work properly during streaming without conflicts
- The user experience remains smooth with real-time token streaming
- No "Only one live display may be active at once" errors occur
