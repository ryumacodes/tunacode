# Bash Tool Research Document

## Overview

The `bash` tool is an execute-type tool in TunaCode that provides secure shell command execution for agent operations. It uses Python's `asyncio` subprocess APIs for asynchronous execution with comprehensive security validation.

## Tool Definition

**Location:** `src/tunacode/tools/bash.py`

**Tool Signature:**
```python
@base_tool
async def bash(
    command: str,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    timeout: int | None = 30,
    capture_output: bool = True,
) -> str:
```

## Input Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `command` | `str` | Required | The bash command to execute |
| `cwd` | `str \| None` | `None` | Working directory for the command |
| `env` | `dict[str, str] \| None` | `None` | Additional environment variables |
| `timeout` | `int \| None` | `30` | Command timeout in seconds (1-300) |
| `capture_output` | `bool` | `True` | Whether to capture stdout/stderr |

## Security Validation

The bash tool implements multi-layer security validation:

### 1. Destructive Pattern Detection
```python
DESTRUCTIVE_PATTERNS = ["rm -rf", "rm -r", "rm /", "dd if=", "mkfs", "fdisk"]
```

### 2. Dangerous Regex Patterns
```python
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",      # Dangerous rm commands
    r"sudo\s+rm",         # Sudo rm commands
    r">\s*/dev/sd[a-z]",  # Writing to disk devices
    r"dd\s+.*of=/dev/",   # DD to devices
    r"mkfs\.",            # Format filesystem
    r"fdisk",             # Partition manipulation
    r":\(\)\{.*\}\;",     # Fork bomb pattern
]
```

### 3. Command Injection Detection
- Semicolon command chaining to `rm`
- AND command chaining to `rm`
- Command substitution with `rm`
- Fork bomb patterns

### 4. Restricted Character Checks
- `$` - Only allowed for valid variable expansions (`$VAR` or `${VAR}`)
- `{`, `}` - Blocked unless part of valid variable expansion
- `;`, `&`, `` ` `` - Blocked entirely

## Execution Flow

```
bash(command, cwd, env, timeout, capture_output)
  ↓
_validate_inputs(command, cwd, timeout)
  ↓
_validate_command_security(command)
  ↓
Prepare environment (os.environ.copy + env overrides)
  ↓
asyncio.create_subprocess_shell(
    command,
    stdout=subprocess.PIPE if capture_output else None,
    stderr=subprocess.PIPE if capture_output else None,
    cwd=exec_cwd,
    env=exec_env,
)
  ↓
await process.communicate() with timeout
  ↓
Decode stdout/stderr (UTF-8 with error replacement)
  ↓
_check_common_errors(command, returncode, stderr)
  ↓
_format_output(command, return_code, stdout_text, stderr_text, cwd)
  ↓
Cleanup process (terminate/kill if needed)
```

## Input/Output Handling

### Input Handling

1. **Environment Variables:**
   - Inherits current process environment via `os.environ.copy()`
   - Merges user-provided `env` dict on top
   - Only string key-value pairs are accepted

2. **Working Directory:**
   - Defaults to current working directory (`os.getcwd()`) if `cwd` is None
   - Validates directory exists before execution

3. **Timeout Enforcement:**
   - Uses `asyncio.wait_for()` with configurable timeout
   - On timeout: kills process and raises `ModelRetry`

### Output Handling

1. **Stream Capture:**
   - `stdout` and `stderr` captured via `subprocess.PIPE`
   - Can be disabled with `capture_output=False`

2. **Decoding:**
   - UTF-8 with error replacement (malformed chars replaced)
   - Results stripped of leading/trailing whitespace

3. **Output Formatting:**
   ```python
   def _format_output(command, exit_code, stdout, stderr, cwd) -> str:
       lines = [
           f"Command: {command}",
           f"Exit Code: {exit_code}",
           f"Working Directory: {cwd}",
           "",
           "STDOUT:",
           stdout or "(no output)",
           "",
           "STDERR:",
           stderr or "(no errors)",
       ]
       return "\n".join(lines)
   ```

4. **Output Truncation:**
   - Max output size: `get_command_limit()` (5000 chars standard, 1500 in local_mode)
   - Truncation threshold: 3500 chars
   - Start index: 2500 chars preserved
   - End size: 1000 chars preserved
   - Truncation marker: `"\n...\n[truncated]\n...\n"`

## Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `MAX_COMMAND_OUTPUT` | 5000 | Standard max output length |
| `LOCAL_MAX_COMMAND_OUTPUT` | 1500 | Local mode max output |
| `COMMAND_OUTPUT_THRESHOLD` | 3500 | Truncation trigger point |
| `COMMAND_OUTPUT_START_INDEX` | 2500 | Chars preserved at start |
| `COMMAND_OUTPUT_END_SIZE` | 1000 | Chars preserved at end |
| `CMD_OUTPUT_TRUNCATED` | `"\n...\n[truncated]\n...\n"` | Truncation marker |

## Error Handling

### Validation Errors (raise `ModelRetry`)
- Empty command
- Timeout outside 1-300 range
- Non-existent working directory
- Destructive patterns detected
- Security violations

### Execution Errors
- **TimeoutError:** Process killed, user retry suggestion
- **FileNotFoundError:** Shell not found, system config issue

### Process Cleanup
```python
async def _cleanup_process(process):
    if process is None or process.returncode is not None:
        return
    try:
        process.terminate()
        await asyncio.wait_for(process.wait(), timeout=5.0)
    except TimeoutError:
        process.kill()
        await asyncio.wait_for(process.wait(), timeout=1.0)
```

## Tool Classification

- **Category:** `EXECUTE_TOOLS`
- **Tool Name:** `ToolName.BASH = "bash"`
- **Decorator:** `@base_tool` (error handling wrapper)
- **Is Read-Only:** No

## UI Rendering

**Location:** `src/tunacode/ui/renderers/tools/bash.py`

### 4-Zone Layout Pattern

1. **Zone 1 (Header):** Command + exit status
   - Format: `$ {command}` truncated to 50 chars
   - Status: "ok" (green) or "exit {code}" (red)

2. **Zone 2 (Params):** Working directory and timeout
   - Format: `cwd: {path}  timeout: {N}s`

3. **Zone 3 (Viewport):** stdout/stderr with syntax highlighting
   - Smart lexer detection (JSON, diff, etc.)
   - stderr shown in red

4. **Zone 4 (Status):** Truncation, line counts, duration
   - Format: `(truncated) stdout: N lines stderr: M lines {duration}ms`

### Parsed Data Structure

```python
@dataclass
class BashData:
    command: str
    exit_code: int
    working_dir: str
    stdout: str
    stderr: str
    is_truncated: bool
    timeout: int
```

### Output Format Parsing

The renderer parses the tool's formatted output using regex:
```python
command_match = re.search(r"Command: (.+)", result)
exit_match = re.search(r"Exit Code: (\d+)", result)
cwd_match = re.search(r"Working Directory: (.+)", result)
stdout_match = re.search(r"STDOUT:\n(.*?)(?=\n\nSTDERR:|\Z)", result, re.DOTALL)
stderr_match = re.search(r"STDERR:\n(.*?)(?:\Z)", result, re.DOTALL)
```

## Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Return formatted output |
| Non-zero | Command failure | Return output with exit code |
| N/A | Timeout | Raise `ModelRetry` with timeout message |
| N/A | Security violation | Raise `ModelRetry` with pattern details |

## Dependencies

- `asyncio` - Async subprocess management
- `subprocess` - Process creation
- `pydantic_ai.exceptions.ModelRetry` - User-retry exceptions
- `tunacode.tools.decorators.base_tool` - Error handling wrapper
- `tunacode.core.limits.get_command_limit()` - Output size limits

## Key Design Patterns

1. **Fail Fast, Fail Loud:** Security violations raise immediately; no silent fallbacks
2. **Contract-Based Validation:** Preconditions checked before execution
3. **Resource Limits:** Output truncation prevents memory issues
4. **Graceful Cleanup:** Process termination with fallback to kill
5. **Unicode Safety:** UTF-8 with replacement for malformed input
6. **Environment Isolation:** Inherits parent env but can override
