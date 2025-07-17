# Fix Plan for Failing Tests After PR Merges

## Issue 1: Duplicate Tool Recovery Logic

**Problem**: Tool recovery is attempted twice in the exception handler, causing test failures.

**Root Cause**: In `repl.py`, there are two separate tool recovery attempts:
1. Lines 350-374: Inline recovery logic
2. Line 378: Call to `_attempt_tool_recovery` function

**Solution**: Remove the duplicate inline recovery logic (lines 350-374) and keep only the `_attempt_tool_recovery` function call.

## Issue 2: MagicMock Type Error in Token Formatting

**Problem**: Tests fail with `TypeError: '>=' not supported between instances of 'MagicMock' and 'int'` in `format_token_count`.

**Root Cause**: Some tests are not properly setting up `state_manager.session.total_tokens` and `state_manager.session.max_tokens`, leaving them as MagicMock objects or not setting them at all.

**Solution**: Fix the failing tests to properly mock `total_tokens` and `max_tokens` as integers, and add defensive checks in the code.

## Implementation Steps

1. **Fix duplicate tool recovery in repl.py**:
   - Remove lines 350-374 (the inline recovery logic)
   - Keep only the call to `_attempt_tool_recovery` at line 378

2. **Fix token count mocking in tests**:
   - Ensure all tests properly set `total_tokens` as an integer
   - Add `max_tokens` property to mock sessions where needed
   - Consider adding type checking in `get_context_window_display` for defensive programming

3. **Update test expectations**:
   - Tests should expect only one call to `extract_tool_calls_mock`
   - Ensure all token-related properties are properly mocked as integers