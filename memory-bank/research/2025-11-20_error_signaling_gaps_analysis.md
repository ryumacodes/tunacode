# Research – Error Signaling Gaps in TunaCode
**Date:** 2025-11-20
**Owner:** Claude Research Agent
**Phase:** Research

## Goal
Summarize findings on why errors (including rate limiting) are not properly signaled to users in the TunaCode application, despite recent error handling improvements.

## Additional Search:
- `grep -ri "429\|rate.*limit\|token.*quota" src/` - Found only rate limiting prevention configuration
- `grep -ri "RateLimitError\|openai.RateLimitError" src/` - No direct handling of OpenAI rate limit exceptions

## Findings

### Relevant Files & Why They Matter:

#### Core Error Handling Files:
- `src/tunacode/core/agents/main.py:476-490` - **Critical**: Main error boundary that catches exceptions but only logs them, doesn't show users
- `src/tunacode/cli/repl.py:268-270` - **Critical**: REPL error handler that only shows errors if recovery fails
- `src/tunacode/cli/repl_components/error_recovery.py:93-169` - **Important**: Error recovery system that silently fixes problems without notifying users
- `src/tunacode/ui/console.py:76-77` - UI error display functions exist but are underutilized

#### Configuration & Prevention:
- `src/tunacode/configuration/key_descriptions.py:106` - Shows rate limiting is prevented via delays, but errors aren't handled when prevention fails

### Key Patterns / Solutions Found:

#### 1. **Silent Error Suppression Pattern**
The system prioritizes graceful degradation over user awareness:
```python
# main.py:476-490 - Generic exception handling
except Exception as e:
    logger.error("Error in process_request...", e, exc_info=True)
    error_msg = f"Request processing failed: {str(e)[:100]}..."
    patch_tool_messages(error_msg, state_manager=self.state_manager)
    # Returns fallback result WITHOUT showing user any error
    return AgentRunWrapper(None, fallback, response_state)
```

#### 2. **Recovery Success Masks Problems**
Error recovery works too well - when it succeeds, users never know an error occurred:
```python
# error_recovery.py:147-153
await ui.muted("⚠️ Model response error. Attempting to recover...")
# ... recovery succeeds ...
# No notification sent to user about the original error
```

#### 3. **Debug-Only Error Visibility**
Many error messages only shown in debug mode (`show_thoughts=True`):
```python
# streaming.py:265-296
if getattr(state_manager.session, "show_thoughts", False):
    await ui.warning("Streaming failed; falling back to non-streaming mode")
```

#### 4. **No Specific Rate Limit Error Handling**
- OpenAI `RateLimitError` exceptions are not specifically caught
- They fall through to the generic exception handler
- No special handling for token quota exceeded scenarios
- No user guidance for rate limiting issues

## Knowledge Gaps

### Missing Error Signaling:
1. **Rate Limit Errors**: No specific handling or user messaging for 429/token quota errors
2. **API Failures**: Generic API errors are logged but not shown to users
3. **Partial Failures**: When some tools fail but others succeed, users aren't informed
4. **Recovery Notifications**: Users aren't told when automatic recovery occurs
5. **Degraded Mode**: Users aren't warned when the system falls back to reduced functionality

### Missing User Guidance:
1. **Rate Limiting**: No guidance on waiting periods or token usage
2. **API Configuration**: No clear error messages for configuration issues
3. **Token Count**: Users can't monitor their token usage approaching limits
4. **Recovery Actions**: No indication when automatic fixes are applied

## References

### Implementation Files:
- `src/tunacode/core/agents/main.py:476-490` - Main error boundary (silent failure)
- `src/tunacode/cli/repl.py:268-270` - REPL error handler
- `src/tunacode/cli/repl_components/error_recovery.py` - Silent recovery system
- `src/tunacode/ui/console.py` - Available UI error functions (underutilized)

### Documentation:
- `memory-bank/execute/2025-11-19_error_handling_hardening_REPORT.md` - Recent hardening work
- `memory-bank/research/2025-11-19_09-45-17_main_agent_error_handling_analysis.md` - Previous error analysis

### External Dependencies:
- OpenAI RateLimitError from `openai` package (not specifically handled)
- PydanticAI agent error propagation (handled generically)

## Root Cause Analysis

The fundamental issue is a **design philosophy that prioritizes uninterrupted operation over user awareness**. The error handling system is technically sophisticated but fails at user experience by:

1. **Catching all exceptions** but only logging them internally
2. **Implementing successful recovery** without notifying users
3. **Preventing rate limiting** via delays but not handling when it occurs anyway
4. **Having UI error functions** but consistently failing to call them

The rate limit error you experienced was caught by the generic exception handler in `main.py:476-490`, logged to the backend system, and then silently replaced with a fallback response. The user saw no indication of the 429 error or token quota exhaustion.

## Recommended Next Steps

1. **Add specific RateLimitError handling** in main error boundary
2. **Implement user notifications** for all error recovery attempts
3. **Add rate limit specific user guidance** (wait times, token usage)
4. **Create error severity classification** (critical vs. recoverable)
5. **Add error aggregation** for multiple related failures
6. **Implement optional debug mode** that shows all internal errors
