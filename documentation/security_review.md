# Security Review: Shell Command Feature

## Security Concerns

1. **Command Injection**: The current implementation uses `subprocess.run(command, shell=True)` which is vulnerable to command injection attacks.
   - Example: User input like `ls; rm -rf /` would execute both commands

2. **No Input Sanitization**: Commands are executed directly without any validation or sanitization.

3. **Environment Variable Access**: Commands have full access to environment variables which may contain sensitive information.

4. **No Permission Controls**: Any command can be executed with the permissions of the TunaCode process.

## Recommendations

1. **Add a Warning**: Display a clear warning before executing shell commands about potential risks.

2. **Command Logging**: Log all executed commands for audit purposes.

3. **Consider Allowlisting**: Implement a configurable allowlist of safe commands.

4. **Escape/Quote Arguments**: If continuing with shell=True, properly escape user input.

5. **Alternative Implementation**: Consider using shell=False with proper argument parsing for safer execution.

## Code Review

The implementation in `src/tunacode/cli/repl.py` lines 276-287:
- Uses `run_in_terminal()` to ensure proper terminal handling
- Falls back to user's shell if no command provided
- No error handling for failed commands
- No timeout mechanism

## Edge Cases to Test

1. Empty command (opens shell) ✓
2. Commands with pipes and redirects ✓
3. Background processes (`command &`)
4. Interactive commands (vim, less)
5. Commands that prompt for input
6. Very long running commands
7. Commands that output large amounts of data
