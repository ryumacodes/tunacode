# Agent Hanging Issue Analysis

## Problem Description
The agent appears to hang/freeze after the recent changes to remove recursive satisfaction checking.

## Root Cause
The issue is in how we handle empty responses in `/home/tuna/tunacode/src/tunacode/core/agents/main.py`:

### The Problematic Flow:

1. **Line 846**: Agent starts iteration with `async with agent.iter(message, message_history=mh) as agent_run:`
   - `mh` is a COPY of the message history at this point

2. **Lines 877-1049**: When empty response detected, we inject messages:
   ```python
   state_manager.session.messages.append(force_message)  # Line 913
   state_manager.session.messages.append(retry_message)  # Line 1042
   ```

3. **THE ISSUE**: These messages are added to `state_manager.session.messages` but:
   - The current `agent_run` is already using the old `mh` (message history)
   - The injected messages won't be seen until the NEXT agent.iter() call
   - But we're still inside the current async iteration loop!

4. **Result**: The agent continues with the same context, gets another empty response, and keeps adding messages that it never sees.

## Why It Appears to Hang

The agent isn't actually frozen - it's stuck in a loop where:
1. It gets an empty response
2. Injects a message asking itself to take action
3. Continues the iteration WITHOUT seeing that message
4. Gets another empty response (because context hasn't changed)
5. Repeats until hitting iteration limit

## The Key Insight

The `async for node in agent_run:` loop (line 849) is iterating over nodes from an agent run that was initialized with a specific message history. Adding messages to the session during this loop doesn't affect the current iteration - only future agent.iter() calls would see them.

## Solution Options

### Option 1: Break and Restart (Recommended)
When we detect empty responses and inject guidance messages, we should:
1. Break out of the current agent_run loop
2. Start a new agent.iter() with the updated message history
3. This ensures the agent sees the injected guidance

### Option 2: Use Direct Message Injection
Instead of appending to session messages, we need to find a way to inject messages directly into the current agent_run context.

### Option 3: Revert Empty Response Handling
Remove the message injection logic and let the agent handle empty responses naturally.

## Affected Code Locations

1. **Main Loop**: `/home/tuna/tunacode/src/tunacode/core/agents/main.py`
   - Line 846: `async with agent.iter(message, message_history=mh)`
   - Lines 877-1049: Empty response handling
   - Line 913: `state_manager.session.messages.append(force_message)`
   - Line 1042: `state_manager.session.messages.append(retry_message)`

2. **Message History**:
   - Line 800: `mh = state_manager.session.messages.copy()`
   - This copy means changes to session.messages don't affect current run

## Immediate Fix

The quickest fix is to continue the loop without injecting messages, or to break out and restart with updated context.
