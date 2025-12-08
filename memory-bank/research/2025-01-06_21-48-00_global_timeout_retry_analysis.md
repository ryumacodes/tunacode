# Research – Global Timeout and Retry Mechanism Analysis

**Date:** 2025-01-06
**Owner:** Claude
**Phase:** Research
**Git Commit:** 7815bf8
**Tags:** [timeout, retry, GlobalRequestTimeoutError, tool_executor]

## Goal
Analyze the timeout and retry mechanism after a GlobalRequestTimeoutError occurred, to understand why the retry mechanism didn't prevent the timeout and how these systems interact.

- Additional Search:
  - `grep -ri "GlobalRequestTimeoutError" .claude/`

## Findings

### Root Cause: GlobalRequestTimeoutError is NOT in NON_RETRYABLE_ERRORS

The critical issue is in `/home/tuna/tunacode/src/tunacode/core/agents/agent_components/tool_executor.py:28-37`:
```python
NON_RETRYABLE_ERRORS = (
    UserAbortError,
    ModelRetry,
    KeyboardInterrupt,
    SystemExit,
    ValidationError,
    ConfigurationError,
    ToolExecutionError,
    FileOperationError,
)
```

`GlobalRequestTimeoutError` is missing from this tuple, which means:
- When a global timeout occurs, the tool executor WILL retry the operation
- This leads to extended total execution time beyond the 90s limit
- Users experience what appears to be an unresponsive agent

### Relevant files & why they matter:

- `/home/tuna/tunacode/src/tunacode/core/agents/agent_components/tool_executor.py` → **Lines 28-37**: Contains NON_RETRYABLE_ERRORS definition that's missing GlobalRequestTimeoutError
- `/home/tuna/tunacode/src/tunacode/core/agents/agent_components/tool_executor.py` → **Lines 71-104**: Retry logic that incorrectly retries global timeouts
- `/home/tuna/tunacode/src/tunacode/core/agents/main.py` → **Lines 344-357**: Main execution loop with global timeout wrapper using asyncio.wait_for
- `/home/tuna/tunacode/src/tunacode/exceptions.py` → **Lines 199-210**: GlobalRequestTimeoutError definition
- `/home/tuna/tunacode/src/tunacode/core/agents/agent_components/agent_config.py` → **Lines 90-103**: Global timeout configuration (default 90.0s)
- `/home/tuna/tunacode/tests/test_tool_retry.py` → **Test coverage for retry mechanism**

## Key Patterns / Solutions Found

### Two-Layer Timeout/Retry System

1. **Tool-Level Retries** (`tool_executor.py`):
   - Handles transient tool failures
   - Uses exponential backoff with jitter
   - Maximum retries defined by `TOOL_MAX_RETRIES`
   - Should NOT retry global timeouts

2. **Global Request Timeout** (`main.py`):
   - Hard limit of 90.0 seconds by default
   - Wrapped around entire agent execution using `asyncio.wait_for`
   - Should immediately terminate, never retry

### Timeout Hierarchy Confusion

- Tool-level timeouts (e.g., ripgrep 10s) are transient and worth retrying
- Global timeout (90s) is a hard limit that should never be retried
- Current implementation doesn't distinguish between these types

## Knowledge Gaps

- Need to verify if GlobalRequestTimeoutError import is already present in tool_executor.py
- Check if there are existing tests for GlobalRequestTimeoutError retry behavior
- Determine if there are other timeout-related errors that should be non-retryable

## References

- https://github.com/alchemiststudiosDOTai/tunacode/blob/7815bf8/src/tunacode/core/agents/agent_components/tool_executor.py#L28-L37
- https://github.com/alchemiststudiosDOTai/tunacode/blob/7815bf8/src/tunacode/core/agents/main.py#L344-L357
- https://github.com/alchemiststudiosDOTai/tunacode/blob/7815bf8/src/tunacode/exceptions.py#L199-L210
