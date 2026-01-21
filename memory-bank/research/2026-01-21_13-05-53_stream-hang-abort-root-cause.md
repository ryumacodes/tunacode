# Research - Stream Hang After Abort: Root Cause Analysis

**Date:** 2026-01-21
**Owner:** Agent
**Phase:** Research

## Goal

Identify the root cause of model requests hanging after user abort (ESC), even when the message history is clean and the model works fine when called directly.

## Evidence from Debug Logs

```
Stream init: node=ModelRequestNode request_id=f3551347 iteration=2 ctx_messages=0 ctx_messages_type=None
Stream request parts: count=1 type=ModelRequest
Stream request part[0]: kind=user-prompt content=gm gm (5 chars)
Stream watchdog timeout after 30.0s; falling back to non-streaming
GlobalRequestTimeoutError: Request exceeded global timeout of 120.0s
```

Key observations:
1. **iteration=2** - This is the second iteration, meaning iteration 1 completed
2. **ctx_messages=0** - The pydantic-ai run context has ZERO messages during iteration 2
3. Both streaming AND non-streaming modes hang
4. Model works fine when called directly (user confirmed)
5. Issue persists even on fresh session/process

## Findings

### 1. Critical Bug: CancelledError Not Caught in Streaming Code

**File:** `src/tunacode/core/agents/agent_components/streaming.py:381`

```python
except Exception as e:
    # Reset node state to allow graceful degradation to non-streaming mode
    logger.warning(f"Stream failed, falling back to non-streaming: {e}")
```

**Problem:** In Python 3.8+, `asyncio.CancelledError` inherits from `BaseException`, NOT `Exception`. This means:
- When user aborts with ESC
- `task.cancel()` is called
- `CancelledError` propagates through the stream loop
- The `except Exception` block does NOT catch it
- The stream context manager exits without proper cleanup
- The httpx connection may be left in an inconsistent state

### 2. Message History Cleanup is Correct

**Files:**
- `src/tunacode/core/agents/main.py:788-800` - `_find_dangling_tool_call_ids()`
- `src/tunacode/core/agents/main.py:945-979` - `_remove_dangling_tool_calls()`

The cleanup logic correctly:
- Scans the ENTIRE message history (not just trailing messages)
- Matches tool call IDs to tool return IDs using set difference
- Removes dangling tool calls and their cached args
- Runs BEFORE every API request (line 364-372)
- Runs in exception handler on abort (line 498-507)

This is NOT the root cause - the history cleanup is working correctly.

### 3. Agent Cache Invalidation Works

**File:** `src/tunacode/core/agents/agent_components/agent_config.py:148-184`

Cache invalidation:
- Clears both module-level and session-level caches
- Called on UserAbortError and CancelledError (line 509-512 in main.py)
- Fresh process = empty cache anyway

This is NOT the root cause.

### 4. Potential pydantic-ai Agent State Corruption

**File:** `src/tunacode/core/agents/main.py:420`

```python
async with agent.iter(self.message, message_history=message_history) as run_handle:
```

The debug log shows `ctx_messages=0` during iteration 2. This is the pydantic-ai run context (`agent_run_ctx.messages`), which is different from `session_messages`.

**Hypothesis:** The pydantic-ai Agent object maintains internal state across iterations. If abort happens mid-iteration, this state may be corrupted. The cached agent is invalidated, but on the NEXT request, a new agent is created. However, if the abort happened during `agent.iter()` context manager, the context manager exit may not clean up properly.

### 5. AsyncTenacityTransport May Interfere

**File:** `src/tunacode/core/agents/agent_components/agent_config.py:455-465`

```python
transport = AsyncTenacityTransport(
    config=RetryConfig(
        retry=retry_if_exception_type(HTTPStatusError),
        wait=wait_retry_after(max_wait=60),
        stop=stop_after_attempt(max_retries),
        reraise=True,
    ),
    validate_response=lambda r: r.raise_for_status(),
)
http_client = AsyncClient(transport=transport, event_hooks=event_hooks)
```

The custom transport wraps httpx with tenacity retry logic. If abort/cancellation happens mid-retry, the transport may not handle `CancelledError` properly.

## Key Patterns / Solutions Found

| Pattern | Location | Relevance |
|---------|----------|-----------|
| `except Exception` doesn't catch `CancelledError` | streaming.py:381 | HIGH - likely root cause |
| Pre-request cleanup | main.py:364-372 | Working correctly |
| Exception handler cleanup | main.py:498-507 | Working correctly |
| Cache invalidation | agent_config.py:148-184 | Working correctly |
| pydantic-ai context messages | streaming.py:141-148 | Suspicious - 0 in iteration 2 |

## Root Cause Analysis

**ACTUAL ROOT CAUSE: Consecutive Request Messages**

The debug logs revealed the real issue:
```
msg[-3]: kind=request, parts=[retry-prompt, retry-prompt, retry-prompt, user-prompt, user-prompt]
msg[-2]: kind=request, parts=[user-prompt:5chars]
msg[-1]: kind=request, parts=[user-prompt:5chars]
```

THREE consecutive `kind=request` messages with NO `kind=response` between them. The API expects alternating request/response messages.

**How it happens:**
1. User sends message
2. Abort happens BEFORE model responds
3. `_persist_run_messages()` saves the user prompt from `agent_run.all_messages()`
4. User sends another message
5. New user prompt is added to history
6. Now there are 2+ consecutive request messages
7. API receives invalid message sequence and hangs

The CancelledError fix (streaming.py) was also needed but wasn't the primary cause.

## Implemented Fixes

### Fix 1: CancelledError handling (streaming.py:381-396) - APPLIED

```python
except asyncio.CancelledError:
    logger.lifecycle("Stream cancelled")
    # ... cleanup and re-raise
    raise
except Exception as e:
    # ... existing fallback logic
```

### Fix 2: Remove consecutive request messages (main.py) - APPLIED

Added `_remove_consecutive_requests()` function that:
- Scans message history for consecutive `kind=request` messages
- Removes all but the last in any consecutive run
- Called in pre-request cleanup (line ~375)
- Called in exception handler on abort (line ~516)

## Knowledge Gaps

1. **pydantic-ai internals:** How does `agent.iter()` handle mid-iteration cancellation? Does it clean up its internal state?

2. **httpx cancellation:** What happens to an httpx AsyncClient when a request is cancelled mid-flight? Is the connection pool left in a bad state?

3. **AsyncTenacityTransport:** How does the custom transport handle `CancelledError`? Does it propagate correctly or get swallowed?

4. **Why iteration 2?** The hang happens on iteration 2, not iteration 1. This suggests something about the agent's iteration state machine.

## References

- Debug history: `.claude/debug_history/2026-01-21_stream-hang-timeout.md`
- Debug history: `.claude/debug_history/2026-01-21_abort-hang-investigation.md`
- Streaming code: `src/tunacode/core/agents/agent_components/streaming.py`
- Main agent loop: `src/tunacode/core/agents/main.py`
- Agent config: `src/tunacode/core/agents/agent_components/agent_config.py`
- Related PR: #246 (UserAbortError dangling tool calls)

## Next Steps

1. **Immediate:** Fix `except Exception` to also catch `CancelledError` in streaming.py
2. **Verify:** Add logging to confirm cancellation is being caught properly
3. **Investigate:** Check pydantic-ai's behavior on mid-iteration cancellation
4. **Test:** Reproduce the bug with verbose logging, then test the fix
