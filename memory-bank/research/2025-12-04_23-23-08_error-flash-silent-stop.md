# Research – Error Flash and Silent Agent Stop Bug

**Date:** 2025-12-04
**Owner:** claude-agent
**Phase:** Research

## Goal

Investigate why the agent sometimes runs a few tools, shows a faint flash of an error (modal or red box), and then silently stops without further output or explanation.

## Findings

### 1. Error Display Mechanisms

The codebase has **two distinct error display systems**:

| Method | Location | Persistence | Auto-Dismiss |
|--------|----------|-------------|--------------|
| Rich Panel | RichLog viewport | Permanent | No |
| Toast Notification | Top/bottom overlay | 2-3 seconds | **Yes** |

**The "flash" is almost certainly Textual's `notify()` system:**
- `src/tunacode/ui/app.py:185` - "Cancelled" toast
- `src/tunacode/ui/commands/__init__.py:247` - "Command timed out" toast (severity="error")
- Textual's built-in timeout (~2-3 seconds) is NOT configurable in current code
- 23 total `notify()` calls across UI code

**Persistent error panels** use `rich_log.write()` at:
- `src/tunacode/ui/app.py:158` - Exception rendering in request worker
- `src/tunacode/ui/app.py:194` - Exception rendering in request processing

### 2. Silent Error Handling Patterns (Root Cause)

**CRITICAL: Multiple locations catch exceptions but DO NOT re-raise them:**

#### Pattern A: Exception Returned as Value
`src/tunacode/core/agents/agent_components/tool_executor.py:31-36`
```python
async def execute_with_error_handling(part, node):
    try:
        return await callback(part, node)
    except Exception as e:
        logger.error(f"Error executing parallel tool: {e}", exc_info=True)
        return e  # Returns exception instead of raising!
```
- Parallel tool execution uses `return_exceptions=True`
- Exceptions become return values - **user never sees them**

#### Pattern B: Catch Without Re-raise
`src/tunacode/core/agents/agent_components/node_processor.py:338-352`
```python
except Exception as tool_err:
    tool_status = "failed"
    logger.error("Tool callback failed: tool=%s ...", ...)
    # NO re-raise - execution continues to next tool
```
- User sees tool "failed" but **not why**

#### Pattern C: Return Wrapper Instead of Raise
`src/tunacode/core/agents/main.py:465-479`
```python
except Exception as e:
    logger.error("Error in process_request [req=%s iter=%s]: %s", ...)
    error_msg = f"Request processing failed: {str(e)[:100]}..."  # Truncated!
    fallback = ac.SimpleResult(error_msg)
    return ac.AgentRunWrapper(None, fallback, response_state)  # Returns, not raises
```
- Generic exceptions return gracefully with **truncated 100-char message**

#### Pattern D: Research Agent Error Dict
`src/tunacode/core/agents/delegation_tools.py:90-107`
```python
except Exception as e:
    logger.error(error_msg, exc_info=True)
    return {
        "error": True,
        "error_type": type(e).__name__,
        ...
    }  # Returns dict instead of raising
```

### 3. Silent Agent Stop Points

**Main Loop Can Exit Without User Notification:**

`src/tunacode/core/agents/main.py:383-452`
```python
async for node in agent_run:  # Line 383
    # ... process tools ...
    if response_state.task_completed:
        break  # Line 438
    i += 1
# Loop exits here - NO validation, NO logging, NO user notification
return ac.AgentRunWithState(agent_run, response_state)  # Line 452
```

**Problems:**
1. If pydantic-ai iterator stops producing nodes, loop exits **silently**
2. No check if user received a response
3. No logging when loop completes naturally
4. Empty response intervention at line 410 can't run if iterator exhausts on last iteration

### 4. Streaming Error Suppression

`src/tunacode/core/agents/agent_components/streaming.py:270-296`
```python
except Exception as stream_err:
    logger.warning(  # WARNING, not ERROR
        "Streaming error req=%s iter=%s: %s", ...
    )
    # Reset and degrade gracefully - NO user notification
```

### Summary: Error Flow Analysis

| Error Location | Logged? | Re-raised? | User Sees? |
|---------------|---------|------------|------------|
| Tool decorator | Yes | Yes | Depends |
| Parallel executor | Yes | **No** (returned) | **No** |
| Sequential write tools | Yes | **No** | Status only |
| Request orchestrator | Yes | **No** (wrapped) | Truncated |
| Research agent | Yes | **No** (dict) | **No** |
| Streaming errors | Yes | **No** | **No** |

## Key Patterns / Solutions Found

1. **`return_exceptions=True` in asyncio.gather()** - Hardcoded at `tool_executor.py:15`, converts exceptions to values
2. **Toast notifications auto-dismiss** - Textual default ~2-3 seconds, no override in tunacode
3. **Natural loop exhaustion** - No validation when `async for node in agent_run` completes
4. **Error truncation** - Messages cut to 100 chars at `main.py:460, 475`

## Knowledge Gaps

1. Exact scenario triggering the flash (which notify() call?)
2. Whether pydantic-ai is stopping iteration prematurely
3. What specific tool execution causes the silent stop
4. Need to add logging at loop exit to capture state

## Recommended Fixes

### Immediate Debugging

Add logging at these locations to capture the failure:

```python
# main.py:444 - Before natural loop exit
logger.info(f"Loop exiting: iteration={i}, task_completed={response_state.task_completed}")

# main.py:452 - After loop
logger.info(f"Returning from run(): response_state={response_state.__dict__}")

# app.py:183 - After awaiting request task
logger.info(f"Request task completed: {self._current_request_task}")
```

### Permanent Fixes

1. **Validate loop exit** - Check `response_state.has_user_response` before returning
2. **Extend toast timeout** - Use custom notification widget or configure Textual
3. **Propagate errors** - Change `return e` to `raise` in parallel executor (or accumulate and display)
4. **Log loop completion** - Add explicit logging when agent loop exits

## References

- `src/tunacode/ui/app.py` - Main UI application, error rendering
- `src/tunacode/ui/renderers/errors.py` - Error panel rendering
- `src/tunacode/core/agents/main.py` - Agent execution loop, error handling
- `src/tunacode/core/agents/agent_components/tool_executor.py` - Parallel tool execution
- `src/tunacode/core/agents/agent_components/node_processor.py` - Tool processing, silent catches
- `src/tunacode/core/agents/agent_components/streaming.py` - Streaming error suppression
- `src/tunacode/core/agents/delegation_tools.py` - Research agent error handling
