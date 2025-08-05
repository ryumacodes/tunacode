# Task 14 Completed: Defensive Type Checking in _attempt_tool_recovery()
_Started: 2025-07-29 14:45:06_
_Agent: tunacode

[1] Successfully implemented robust type checking and attribute validation in the _attempt_tool_recovery() method to handle TextPart objects correctly and prevent AttributeError crashes when processing retry responses.
[2] Updated _attempt_tool_recovery() in src/tunacode/cli/repl.py (lines 192-216):
[2] - Added defensive type checking for different part types
[2] - Check for text attribute (TextPart objects from retry scenarios)
[2] - Check for content attribute (standard message parts)
[2] - Added try-catch block around attribute access
[2] - Added debug logging for unexpected object types
[2] - Gracefully skip parts without valid string content
[3] Created comprehensive unit tests in tests/test_textpart_handling.py:
[3] - Test TextPart objects with text attribute
[3] - Test standard parts with content attribute
[3] - Test parts with neither attribute
[3] - Test mixed part types
[3] - Test AttributeError handling
[3] - Test debug logging
[3] - Test non-string content handling
