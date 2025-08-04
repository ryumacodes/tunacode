# Agent Empty Response Fix Summary

## Problem
The agent was giving up after empty responses due to:
1. Recursive agent calls in `check_query_satisfaction` function
2. These recursive calls produced empty responses themselves
3. The agent never knew to use `TUNACODE_TASK_COMPLETE` marker
4. Complex satisfaction checking logic causing loops

## Solution
Removed recursive satisfaction checking and simplified completion detection:

### 1. Removed Recursive Satisfaction Check
- Deprecated `check_query_satisfaction` function that was making recursive agent calls
- Removed all calls to this function
- Eliminated `satisfaction_attempts` tracking

### 2. Enhanced Empty Response Handling
- First empty response: Gentle self-reflection with reminder about completion
- Second empty response: Stronger guidance + completion reminder
- Third+ empty response: Force concrete action with explicit completion option

### 3. Updated System Prompt
- Moved completion protocol to prominent position (line 376)
- Added clear examples of when/how to use `TUNACODE_TASK_COMPLETE`
- Removed confusing self-evaluation protocol section

### 4. Simplified Completion Flow
- Agent now decides when to use `TUNACODE_TASK_COMPLETE`
- No external evaluation needed
- Similar to mini-swe-agent's simple completion pattern

## Key Changes

### src/tunacode/core/agents/main.py
- Line 771-788: Deprecated `check_query_satisfaction` to return False
- Line 1052-1058: Removed recursive satisfaction check
- Line 886-900: Added completion reminder in empty response handling
- Line 942-959: Enhanced self-correction with completion guidance
- Line 1022-1028: Added completion reminder in first empty response

### src/tunacode/prompts/system.md
- Line 376-412: Added prominent completion protocol section
- Line 625-626: Removed duplicate completion section and self-evaluation
- Added clear examples of proper completion usage

## Benefits
- No more recursive agent calls
- Agent has control over completion
- Simpler, more predictable behavior
- Reduced API calls and costs
- Clear completion signal prevents unnecessary iterations

## Testing
To test the fix:
1. Run tasks that previously caused empty responses
2. Verify agent uses `TUNACODE_TASK_COMPLETE` appropriately
3. Check that empty responses trigger self-reflection
4. Ensure no infinite loops or premature exits
