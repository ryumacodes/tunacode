# Summary of Fixes for Failing Tests After PR Merges

## Fixed Issues

### 1. Duplicate Tool Recovery Logic (2 test failures)
**Problem**: The tool recovery logic was being called twice in the exception handler, causing `extract_tool_calls_mock.assert_called_once()` to fail.

**Fix**: Removed the duplicate inline tool recovery logic (lines 350-374 in `repl.py`) and kept only the call to `_attempt_tool_recovery` function. This ensures tool recovery is attempted only once.

**Files Modified**:
- `src/tunacode/cli/repl.py`: Removed duplicate tool recovery code

### 2. Token Count Formatting with MagicMock (4 test failures)
**Problem**: Tests were failing with `TypeError: '>=' not supported between instances of 'MagicMock' and 'int'` because the mock sessions were missing the `max_tokens` property.

**Fixes**:
1. Added defensive type checking in `get_context_window_display` to handle non-integer inputs gracefully
2. Updated all failing tests to properly mock `max_tokens` on the session object

**Files Modified**:
- `src/tunacode/ui/output.py`: Added type conversion and error handling in `get_context_window_display`
- `tests/characterization/repl/test_repl_initialization.py`: Added `max_tokens` mock
- `tests/characterization/repl/test_command_parsing.py`: Added `max_tokens` mock
- `tests/characterization/repl/test_keyboard_interrupts.py`: Added `max_tokens` mock
- `tests/characterization/repl/test_session_flow.py`: Added `max_tokens` mock (2 instances)

## Test Results
All 12 error handling tests and 6 REPL tests are now passing:
- ✅ Tool recovery logic tests (7 tests)
- ✅ Simple error handling tests (5 tests)
- ✅ REPL initialization test
- ✅ Command parsing tests (2 tests)
- ✅ Keyboard interrupt test
- ✅ Session flow tests (2 tests)

## Key Changes
1. **Cleaner code**: Removed duplicate error recovery logic, making the code more maintainable
2. **More robust**: Added defensive type checking to handle edge cases with mock objects
3. **Better tests**: Updated tests to properly mock all required session attributes