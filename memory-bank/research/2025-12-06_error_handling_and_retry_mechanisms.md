# Research - Error Handling and Retry Mechanisms

**Date:** 2025-12-06
**Owner:** claude-agent
**Phase:** Research
**Git Commit:** ec22347

## Goal

Map the complete error handling and retry mechanism architecture in tunacode to understand why tool execution errors halt the system instead of triggering retries.

## Executive Summary

The system currently implements a **fail-fast, fail-loud** architecture by design. Tool execution errors **intentionally halt** the agent iteration to surface problems to the user. The only retry mechanism is `ModelRetry` (pydantic-ai), which allows the LLM to self-correct within the same iteration. There is **no automatic application-level retry** for tool failures.

**PLANNED CHANGE:** Implement automatic tool retry (max 3 attempts) with exponential backoff before surfacing errors to the user. See [SPECIFICATION](#specification-automatic-tool-retry-max-3-attempts) section below.

---

## Complete Error Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TOOL LAYER (src/tunacode/tools/)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Tool Implementation                                                       │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────┐               │
│   │  @base_tool decorator (decorators.py:24-60)             │               │
│   │                                                         │               │
│   │  try:                                                   │               │
│   │      return await func(*args)                           │               │
│   │  except ModelRetry:                                     │               │
│   │      raise  ──────────────────────────────┐             │               │
│   │  except ToolExecutionError:               │             │               │
│   │      raise  ─────────────────────────────►│─► PROPAGATE │               │
│   │  except FileOperationError:               │             │               │
│   │      raise  ─────────────────────────────►│             │               │
│   │  except Exception as e:                   │             │               │
│   │      raise ToolExecutionError(...)  ─────►│             │               │
│   └─────────────────────────────────────────────────────────┘               │
│                                                │                            │
└────────────────────────────────────────────────│────────────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CORE LAYER (src/tunacode/core/)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────┐               │
│   │  Tool Executor (tool_executor.py:32-65)                 │               │
│   │                                                         │               │
│   │  async def execute_with_error_handling():               │               │
│   │      try:                                               │               │
│   │          return await callback(part, node)              │               │
│   │      except Exception as e:                             │               │
│   │          logger.error("Error executing tool")           │               │
│   │          raise  # Fail fast - line 38                   │               │
│   └─────────────────────────────────────────────────────────┘               │
│                                   │                                         │
│                                   ▼                                         │
│   ┌─────────────────────────────────────────────────────────┐               │
│   │  Node Processor (node_processor.py:326-342)             │               │
│   │                                                         │               │
│   │  try:                                                   │               │
│   │      await tool_callback(part, node)                    │               │
│   │  except UserAbortError:                                 │               │
│   │      raise  # Preserve user intent                      │               │
│   │  except Exception as tool_err:                          │               │
│   │      logger.error("Tool callback failed")               │               │
│   │      raise  # Fail fast - line 342                      │               │
│   └─────────────────────────────────────────────────────────┘               │
│                                   │                                         │
│                                   ▼                                         │
│   ┌─────────────────────────────────────────────────────────┐               │
│   │  Main Agent Loop (main.py:381-472)                      │               │
│   │                                                         │               │
│   │  async for node in agent_run:                           │               │
│   │      await _process_node(node, ...)  ────► Error breaks │               │
│   │                                           the loop      │               │
│   │  except UserAbortError:                                 │               │
│   │      raise                                              │               │
│   │  except ToolBatchingJSONError:                          │               │
│   │      logger.error("fail fast, fail loud")               │               │
│   │      raise                                              │               │
│   │  except Exception:                                      │               │
│   │      logger.error("fail fast, fail loud")               │               │
│   │      raise  # line 472                                  │               │
│   └─────────────────────────────────────────────────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UI LAYER (src/tunacode/ui/)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────┐               │
│   │  App Request Processor (app.py:221-262)                 │               │
│   │                                                         │               │
│   │  try:                                                   │               │
│   │      await self._current_request_task                   │               │
│   │  except asyncio.CancelledError:                         │               │
│   │      self.notify("Cancelled")                           │               │
│   │  except Exception as e:                                 │               │
│   │      patch_tool_messages(...)  # Fix orphaned calls     │               │
│   │      error_renderable = render_exception(e)             │               │
│   │      self.rich_log.write(error_renderable)              │               │
│   │      ◄──────────────────── REQUEST TERMINATED           │               │
│   └─────────────────────────────────────────────────────────┘               │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────┐               │
│   │  Error Renderers (renderers/errors.py)                  │               │
│   │                                                         │               │
│   │  Severity Map:                                          │               │
│   │   - ToolExecutionError → "error" (red panel)            │               │
│   │   - FileOperationError → "error" (red panel)            │               │
│   │   - UserAbortError     → "info" (blue panel)            │               │
│   │   - ValidationError    → "warning" (yellow panel)       │               │
│   └─────────────────────────────────────────────────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Exception Hierarchy

```
Exception
│
├── ModelRetry (pydantic-ai) ──────────────► LLM gets retry opportunity
│                                            Same iteration continues
│
└── TunaCodeError (exceptions.py)
    │
    ├── UserAbortError ────────────────────► Propagates unchanged
    │                                        Represents user intent
    │
    ├── ToolExecutionError ────────────────► Halts request, shows error
    │   └── .suggested_fix                   Includes recovery hints
    │   └── .recovery_commands
    │
    ├── FileOperationError ────────────────► Halts request, shows error
    │
    ├── TooBroadPatternError ──────────────► Grep timeout (3s deadline)
    │
    ├── GlobalRequestTimeoutError ─────────► Entire request timed out
    │
    ├── ToolBatchingJSONError ─────────────► JSON parse failed
    │
    ├── ConfigurationError ────────────────► Setup/config issues
    │
    ├── ValidationError ───────────────────► Input validation failed
    │
    └── StateError ────────────────────────► Invalid state transition
```

---

## Retry Mechanisms

### 1. ModelRetry (LLM-Driven) - THE ONLY RETRY

**Location:** `pydantic-ai` framework, integrated via decorators

**How it works:**
```python
# decorators.py:85-86 (file_tool decorator)
except FileNotFoundError as err:
    raise ModelRetry(f"File not found: {filepath}. Check the path.") from err

# bash.py:83-86
except TimeoutError as err:
    raise ModelRetry(f"Command timed out after {timeout} seconds...")
```

**Flow:**
1. Tool raises `ModelRetry` with descriptive error message
2. pydantic-ai catches it internally
3. LLM receives the error as feedback
4. LLM can issue corrected tool call
5. Same iteration continues

**When it triggers:**
- `FileNotFoundError` → LLM can try different path
- `TimeoutError` → LLM can suggest longer timeout
- Security violations → LLM can modify command

### 2. JSON Parsing Retry (Transient Failures Only)

**Location:** `utils/parsing/retry.py`

**Configuration:**
- `JSON_PARSE_MAX_RETRIES = 10` (constants.py)
- Exponential backoff between retries

**Scope:** Only for parsing LLM output, NOT for tool execution errors

### 3. NO Application-Level Tool Retry

**Design Decision (from CLAUDE.md):**
```
## Error Handling
- Fail fast, fail loud. No silent fallbacks.
```

Every layer in the stack uses bare `raise` with logging - no retry wrapper.

---

## Key Files Reference

### Exception Definitions
| File | Purpose |
|------|---------|
| `src/tunacode/exceptions.py` | All exception classes with hierarchy |

### Tool Layer
| File | Lines | Purpose |
|------|-------|---------|
| `src/tunacode/tools/decorators.py` | 24-60 | `@base_tool` - wraps all tools |
| `src/tunacode/tools/decorators.py` | 63-100 | `@file_tool` - file ops with ModelRetry |
| `src/tunacode/tools/bash.py` | 83-99 | Timeout and shell error handling |
| `src/tunacode/tools/read_file.py` | 33-37 | File size limit handling |
| `src/tunacode/tools/grep.py` | - | TooBroadPatternError for timeouts |

### Core Layer
| File | Lines | Purpose |
|------|-------|---------|
| `src/tunacode/core/agents/agent_components/tool_executor.py` | 32-65 | Parallel tool execution with fail-fast |
| `src/tunacode/core/agents/agent_components/node_processor.py` | 326-342 | Tool callback with error propagation |
| `src/tunacode/core/agents/main.py` | 381-472 | Main loop with exception handlers |

### UI Layer
| File | Lines | Purpose |
|------|-------|---------|
| `src/tunacode/ui/app.py` | 201-210 | Request worker error catching |
| `src/tunacode/ui/app.py` | 221-262 | Request processor with patch_tool_messages |
| `src/tunacode/ui/renderers/errors.py` | 9-95 | Exception rendering with severity |
| `src/tunacode/ui/components/error_display.py` | - | ErrorDisplay widget |

### Message Handling
| File | Lines | Purpose |
|------|-------|---------|
| `src/tunacode/core/agents/agent_components/message_handler.py` | 42-100 | `patch_tool_messages()` - orphan cleanup |

---

## Why System "Just Stops"

### The Critical Path
1. Tool error occurs (any layer)
2. Error wrapped in `ToolExecutionError` if not already
3. `tool_executor.py:38` - `raise  # Re-raise to fail fast`
4. `node_processor.py:342` - `raise  # Fail fast - surface error to user`
5. `main.py:472` - `raise  # fail fast, fail loud`
6. `app.py:244` - **Exception caught**, error panel rendered
7. `app.py:245` - `rich_log.write(error_renderable)` - **User sees red panel**
8. Request terminates, worker waits for next user input

### No Recovery Path Exists
- Every `except` block uses `raise` (not `return` or retry)
- `patch_tool_messages()` only fixes message history for next request
- No loop wrapping tool execution for automatic retry
- Design explicitly forbids "silent fallbacks"

---

## Knowledge Gaps

1. **What specific error is the user seeing?** - Need to see actual error message
2. **Is ModelRetry being raised but not working?** - Could be pydantic-ai issue
3. **Is the error happening before or after tool execution?** - Different fix needed
4. **Are there race conditions in parallel tool execution?** - Possible timing issue

---

## Potential Issues to Investigate

### Issue 1: ModelRetry Not Triggering Correctly
Some tool errors may raise `ToolExecutionError` when they should raise `ModelRetry`:
- Check if file operation errors are getting wrapped incorrectly
- Verify ModelRetry propagation through decorator chain

### Issue 2: Parallel Execution Fail-Fast
`tool_executor.py:54-56`:
```python
for result in batch_results:
    if isinstance(result, Exception):
        raise result  # First error kills entire batch
```
- One failing tool cancels all parallel tools
- No graceful degradation

### Issue 3: Missing Error Context
When error is displayed, user may not understand:
- Which tool failed
- What parameters caused failure
- How to retry manually

---

## SPECIFICATION: Automatic Tool Retry (Max 3 Attempts)

### Requirement

Tool execution errors should automatically retry up to 3 times before surfacing the error to the user. This changes the current fail-fast behavior to fail-after-retry.

### Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     NEW: RETRY WRAPPER LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────┐               │
│   │  Tool Executor with Retry (tool_executor.py)            │               │
│   │                                                         │               │
│   │  MAX_TOOL_RETRIES = 3                                   │               │
│   │                                                         │               │
│   │  async def execute_with_retry(part, node, callback):    │               │
│   │      for attempt in range(1, MAX_TOOL_RETRIES + 1):     │               │
│   │          try:                                           │               │
│   │              return await callback(part, node)          │               │
│   │          except NON_RETRYABLE_ERRORS:                   │               │
│   │              raise  # Don't retry these                 │               │
│   │          except Exception as e:                         │               │
│   │              if attempt == MAX_TOOL_RETRIES:            │               │
│   │                  raise  # Final attempt failed          │               │
│   │              logger.warning(                            │               │
│   │                  "Tool %s failed (attempt %d/%d): %s",  │               │
│   │                  tool_name, attempt, MAX_TOOL_RETRIES   │               │
│   │              )                                          │               │
│   │              await asyncio.sleep(backoff(attempt))      │               │
│   └─────────────────────────────────────────────────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementation Location

**Primary file:** `src/tunacode/core/agents/agent_components/tool_executor.py`

The retry logic should wrap the existing `execute_with_error_handling` function at lines 32-38.

### Non-Retryable Exceptions

These errors should NOT be retried (immediate propagation):

```python
NON_RETRYABLE_ERRORS = (
    UserAbortError,      # User intent - never retry
    ModelRetry,          # pydantic-ai handles this
    KeyboardInterrupt,   # User wants to stop
    SystemExit,          # Process exit
    ValidationError,     # Bad input won't fix itself
    ConfigurationError,  # Config issues need user action
    SecurityError,       # Security violations shouldn't retry
)
```

### Retryable Exceptions

These errors SHOULD be retried:

```python
RETRYABLE_ERRORS = (
    ToolExecutionError,       # Transient tool failures
    FileOperationError,       # File system hiccups
    TooBroadPatternError,     # Grep timeout (might work on retry)
    TimeoutError,             # Transient timeout
    ConnectionError,          # Network issues
    OSError,                  # System resource issues
)
```

### Backoff Strategy

```python
def calculate_backoff(attempt: int) -> float:
    """Exponential backoff with jitter."""
    base_delay = 0.5  # 500ms
    max_delay = 5.0   # 5 seconds
    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
    jitter = random.uniform(0, delay * 0.1)  # 10% jitter
    return delay + jitter

# Attempt 1: ~0.5s delay before retry
# Attempt 2: ~1.0s delay before retry
# Attempt 3: ~2.0s delay before retry (then fail)
```

### Configuration

Add to `src/tunacode/constants.py`:

```python
# Tool retry configuration
TOOL_MAX_RETRIES = 3
TOOL_RETRY_BASE_DELAY = 0.5  # seconds
TOOL_RETRY_MAX_DELAY = 5.0   # seconds
```

Add to `src/tunacode/configuration/key_descriptions.py`:

```python
"tool_max_retries": KeyDescription(
    type="integer",
    default=3,
    description="Maximum retry attempts for failed tool executions",
),
```

### Logging Requirements

Each retry should log:
- Tool name
- Attempt number (e.g., "2/3")
- Error type and message
- Backoff delay

```python
logger.warning(
    "Tool '%s' failed (attempt %d/%d), retrying in %.1fs: %s",
    tool_name,
    attempt,
    max_retries,
    backoff_delay,
    str(error),
)
```

### UI Feedback (Optional Enhancement)

Consider showing retry status in UI:
- "Tool 'read_file' failed, retrying (2/3)..."
- Could use existing streaming output mechanism

### Parallel Execution Considerations

For `execute_tools_parallel`:
- Each parallel tool gets its own retry budget (3 attempts each)
- Don't fail entire batch on first error
- Collect all results, retry failed ones individually
- Only raise after all retries exhausted

```python
# Current behavior (fail-fast):
for result in batch_results:
    if isinstance(result, Exception):
        raise result  # First error kills all

# New behavior (retry-then-fail):
failed_tools = []
for tool, result in zip(tools, batch_results):
    if isinstance(result, Exception):
        # Retry this specific tool up to MAX_RETRIES
        retry_result = await retry_single_tool(tool, result)
        if isinstance(retry_result, Exception):
            failed_tools.append((tool, retry_result))

if failed_tools:
    raise AggregateToolError(failed_tools)  # New exception type
```

### Testing Requirements

1. Unit test: Verify retry count (exactly 3 attempts)
2. Unit test: Verify non-retryable exceptions propagate immediately
3. Unit test: Verify backoff delays are applied
4. Unit test: Verify success on retry clears error state
5. Integration test: Tool failure → retry → success flow
6. Integration test: Tool failure → 3 retries → error display

### Files to Modify

| File | Changes |
|------|---------|
| `src/tunacode/constants.py` | Add `TOOL_MAX_RETRIES`, backoff constants |
| `src/tunacode/configuration/key_descriptions.py` | Add `tool_max_retries` config |
| `src/tunacode/exceptions.py` | Add `AggregateToolError` for parallel failures |
| `src/tunacode/core/agents/agent_components/tool_executor.py` | Add retry wrapper |
| `src/tunacode/core/agents/agent_components/node_processor.py` | Use retry wrapper |
| `tests/test_tool_retry.py` | New test file for retry logic |

### Migration Notes

- This changes the "fail fast" philosophy to "fail after retry"
- Update `CLAUDE.md` error handling section to reflect new behavior
- Existing `ModelRetry` mechanism remains unchanged (LLM-driven retry)
- Application-level retry is separate from LLM retry

---

## References

- `/home/tuna/tunacode/CLAUDE.md` - Design philosophy ("fail fast, fail loud")
- `/home/tuna/tunacode/src/tunacode/exceptions.py` - Exception hierarchy
- `/home/tuna/tunacode/src/tunacode/tools/decorators.py` - Tool wrappers
- `/home/tuna/tunacode/src/tunacode/core/agents/main.py` - Main loop
- `/home/tuna/tunacode/src/tunacode/ui/app.py` - UI error handling
- `/home/tuna/tunacode/memory-bank/execute/2025-11-19_error_handling_hardening_REPORT.md` - Previous hardening work
