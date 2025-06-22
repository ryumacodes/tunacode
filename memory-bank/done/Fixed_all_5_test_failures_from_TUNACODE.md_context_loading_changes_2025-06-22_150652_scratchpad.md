# Fix test failures from TUNACODE.md context loading changes
_Started: 2025-06-22 15:01:06_

## Plan — 2025-06-22 15:01:14
1. Fix agent creation tests - they expect system prompt without TUNACODE.md
2. Fix process request test - iteration count changed
3. Fix tunacode preview test - we removed the preview storage
4. Update tests to account for TUNACODE.md being loaded

[1] Found issue: Tests expect exact system prompt but we're appending TUNACODE.md content
[2] Fixed first test by mocking Path.exists to return False
[3] Fixed 3 agent creation tests by mocking Path.exists to return False
[4] Fixed process request test - updated iteration count from 20 to 40 and fixed call extraction
[5] Fixed tunacode logging tests - updated to test print output instead of preview storage
[6] Updated test config to use new default max_iterations=40
