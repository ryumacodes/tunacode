# Agent Response Failures - Analysis and Solutions

## Issue Summary

The TunaCode agent is experiencing multiple failure modes when responding to user requests, particularly around:
1. Empty responses after self-evaluation prompts
2. Incomplete responses that state intentions without executing actions
3. Token counting errors causing UI crashes

## Observed Failure Patterns

### 1. Empty Response After Self-Evaluation
**Symptom**: After iteration 2+, when the self-evaluation prompt is injected, the agent returns an empty response.

**Example**:
```
ITERATION: 2/40
🔄 SELF-EVALUATION: Prompting agent to assess task completion
[ Tokens: 0 (P: 0, C: 0) | Cost: $0.0000 ]
⚠️ EMPTY RESPONSE - CONTINUING
```

**Root Cause**:
- The retry mechanism injects a plain string instead of a properly formatted message object
- The agent doesn't see the retry message in the correct format

### 2. Intention Without Action
**Symptom**: Agent describes what it will do but doesn't execute tools.

**Example**:
```
RESPONSE: Let me read the current README content and then use the correct approach to add "hello world" at the end:
[No tool calls follow]
```

**Root Cause**:
- Some models (e.g., `openrouter:moonshotai/kimi-k2`) aren't following the operational agent instructions
- They treat the interaction as conversational rather than action-oriented

### 3. Token Counting Error
**Symptom**: UI crashes with error message.

**Example**:
```
ERROR:ui:unsupported operand type(s) for +=: 'int' and 'NoneType'
```

**Root Causes** (Multiple issues found):
1. **Primary Cause**: `parse_json_tool_calls()` function was returning None instead of an integer
   - Located in `src/tunacode/core/agents/main.py`
   - The function was missing a return statement
   - When called with `tools_executed += parse_json_tool_calls(...)`, it caused the TypeError

2. **Secondary Issues**: Token counting in various places
   - In `usage_tracker.py` line 124: `prompt + completion` could fail with None values
   - In `api_response_parser.py`: Token values from API could be None

## Analysis of Current Implementation

### Self-Evaluation Mechanism
- **Working**: Prompt injection after iteration 2+
- **Not Working**: Empty response handling, retry message format

### Message Format Issues
Current code appends retry as string:
```python
retry_message = "Your previous response was empty..."
state_manager.session.messages.append(retry_message)
```

Should be proper message object:
```python
user_prompt_part = UserPromptPart(
    content=retry_content,
    part_kind="user-prompt",
)
retry_message = model_request_cls(
    parts=[user_prompt_part],
    kind="request",
)
```

### System Prompt Clarity
The prompt clearly states:
- "YOU ARE NOT A CHATBOT. YOU ARE AN OPERATIONAL AGENT WITH TOOLS."
- "Your task is to **execute real actions** via tools"

But some models still respond conversationally.

## Proposed Solutions

### 1. Fix Empty Response Retry (IMPLEMENTED)
**Status**: ✅ Already fixed in main.py
- Proper message object creation
- Detection of self-evaluation context
- Targeted retry messages

### 2. Fix Token Counting Error ✅ COMPLETED
**Location**: `src/tunacode/core/token_usage/usage_tracker.py` lines 124-130

**Status**: ✅ Implemented and verified

**Implementation**:
```python
# Safe handling for None values
prompt_safe = prompt if prompt is not None else 0
completion_safe = completion if completion is not None else 0
last_cost_safe = last_cost if last_cost is not None else 0.0
session_cost_safe = session_cost if session_cost is not None else 0.0

usage_summary = (
    f"[ Tokens: {prompt_safe + completion_safe:,} (P: {prompt_safe:,}, C: {completion_safe:,}) | "
    f"Cost: ${last_cost_safe:.4f} | "
    f"Session Total: ${session_cost_safe:.4f} ]"
)
```

**Additional safeguards confirmed**:
- Defensive normalization in `_update_state`
- Safe accumulation of session totals
- Defaults via `.get()` usage for parsed data
- Initialization of usage dicts when None

### 3. Detect and Handle "Intention Without Action"
**Approach**: Add detection after response processing

**Detection Pattern**:
```python
intention_phrases = [
    "Let me", "I'll", "I will", "I'm going to",
    "I need to", "I should", "I want to"
]
# Check if response contains intention but no tool calls
```

**Response**: Inject prompt like:
```
"You stated an intention but didn't execute any tools. Please execute the tools now to complete the action you described."
```

### 4. Strengthen System Prompt for Action
**Add to system prompt after line 7**:
```markdown
**CRITICAL**: When you say "Let me..." or "I will..." you MUST immediately execute the corresponding tool in THE SAME RESPONSE. Never describe what you'll do without doing it.

Examples:
❌ WRONG: "Let me read the file first" [no tool call]
✅ RIGHT: "Reading the file:" [followed by read_file tool call]
```

### 5. Model-Specific Handling
**For problematic models** (e.g., kimi-k2):
- Add warning when selecting these models
- Consider pre-prompt injection with stronger action emphasis
- Track failure rates per model

## Implementation Priority

1. **High Priority** (Immediate fixes) ✅ COMPLETED:
   - ✅ Fix token counting error (prevents crashes)
   - ✅ Empty response retry mechanism (proper message format)

2. **Medium Priority** (Behavior improvements) - TODO:
   - Add "intention without action" detection
   - Strengthen system prompt with action emphasis

3. **Low Priority** (Long-term) - TODO:
   - Model-specific handling
   - Failure rate tracking

## Testing Strategy

1. **Token Counting**: Test with models that don't return token counts
2. **Empty Response**: Test self-evaluation with various models
3. **Intention Detection**: Test with conversational responses
4. **Cross-Model**: Test all fixes with multiple providers

## Next Steps

### Completed ✅
1. ✅ Fixed token counting error in `usage_tracker.py` - Added None-safe handling
2. ✅ Fixed token parsing in `api_response_parser.py` - Ensures None tokens become 0
3. ✅ Fixed empty response retry mechanism - Proper message format
4. ✅ Added debug traceback for better error visibility
5. ✅ **FOUND AND FIXED THE ROOT CAUSE**: `parse_json_tool_calls` was returning None instead of int
   - Location: `src/tunacode/core/agents/main.py` line 601
   - Issue: Function didn't return a value, causing `tools_executed += None`
   - Fix: Added proper return type and return statement

### Immediate Actions Required
1. **Test the current fixes**:
   - Run TunaCode with a model that returns empty responses
   - Verify retry messages appear correctly
   - Confirm no token counting crashes

2. **Add "Intention Without Action" Detection**:
   - Location: `src/tunacode/core/agents/main.py` in `_process_node`
   - After processing response, check for intention phrases without tool calls
   - Inject retry prompt: "You stated an intention but didn't execute any tools. Please execute the tools now."

3. **Strengthen System Prompt**:
   - Location: `src/tunacode/prompts/system.md` after line 7
   - Add explicit warning about stating intentions without actions
   - Include examples of wrong vs right patterns

### Testing Checklist
- [ ] Test with `openrouter:moonshotai/kimi-k2` (known problematic model)
- [ ] Test with models that don't return token counts
- [ ] Test self-evaluation with 5+ iterations
- [ ] Test empty response retry mechanism
- [ ] Verify token counting doesn't crash

### Success Criteria
- No UI crashes from token counting
- Empty responses trigger proper retry messages
- Agents execute tools instead of just describing intentions
- Self-evaluation works correctly with TUNACODE_TASK_COMPLETE

## Notes

- The self-evaluation mechanism is conceptually sound but needs robust error handling
- Some models inherently struggle with the operational agent paradigm
- Consider adding model compatibility warnings in documentation
