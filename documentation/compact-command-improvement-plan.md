# Compact Command Improvement Plan

## Overview
The `/compact` command currently summarizes conversation history but does so silently, making it difficult for users to understand what was compacted. This plan outlines improvements to add verification and visibility.

## Current Implementation Issues

1. **No visibility**: Summary happens with `output=False`, users don't see what was summarized
2. **No verification**: Users can't confirm the summary captures important context
3. **Abrupt truncation**: History is cut to last 2 messages without user awareness
4. **No summary display**: The generated summary is discarded after use

## Implementation Status

### ✅ Phase 1: Capture and Display Summary (COMPLETED - 2025-01-08)
- Modified `process_request` call to capture output
- Display summary in a cyan-bordered panel
- Show message count before/after compaction
- Implementation in `/home/tuna/tunacode/src/tunacode/cli/commands.py` (lines 516-569)

## Proposed Improvements

### 1. Display Summary to User
- Show the AI-generated summary before truncating history
- Allow users to see what context is being preserved

### 2. Add Verification Step
- Ask for user confirmation before truncating
- Option to cancel if summary is inadequate
- Allow editing/refining the summary

### 3. Preserve Summary in History
- Keep the summary as part of the conversation
- Add it as a system message or special marker

## Key Files and Locations

### Primary Files
- `/home/tuna/tunacode/src/tunacode/cli/commands.py` (lines 502-530)
  - `CompactCommand` class implementation
  - Currently uses `process_request` callback with `output=False`

### Dependencies
- `/home/tuna/tunacode/src/tunacode/cli/repl.py`
  - Contains `process_request` function that CompactCommand uses
  - Need to understand how to capture output

- `/home/tuna/tunacode/src/tunacode/core/agents/main.py`
  - Agent implementation that generates the summary
  - May need to modify to return summary text

- `/home/tuna/tunacode/src/tunacode/ui/output.py`
  - UI components for displaying formatted output
  - Use for showing summary in a nice panel

### Related Components
- `/home/tuna/tunacode/src/tunacode/core/state.py`
  - StateManager handles message history
  - Need to understand message structure

- `/home/tuna/tunacode/src/tunacode/types.py`
  - Message types and data structures
  - Important for creating proper summary messages

## Implementation Approach

### Phase 1: Capture and Display Summary ✅
1. Modify `process_request` call to capture output ✅
2. Display summary in a formatted panel ✅
3. Show message count before/after compaction ✅

### Phase 2: Add Verification
1. Prompt user: "Compact conversation with this summary? [y/N]"
2. Only truncate on confirmation
3. Allow cancellation

### Phase 3: Preserve Summary
1. Create special "summary" message type
2. Insert summary as first message after truncation
3. Mark it visually distinct in history

## Code Quirks and Considerations

1. **Dependency Injection**: CompactCommand uses factory pattern with injected `process_request_callback`
2. **Message Structure**: Need to understand pydantic-ai message format
3. **Async Flow**: All command execution is async
4. **UI Consistency**: Use existing ui module functions for output

## Phase 1 Implementation (Completed)

The actual implementation for Phase 1 is now in `/home/tuna/tunacode/src/tunacode/cli/commands.py`:

```python
async def execute(self, args: List[str], context: CommandContext) -> None:
    # Count current messages
    original_count = len(context.state_manager.session.messages)
    
    # Generate summary with output captured
    summary_prompt = (
        "Summarize the conversation so far in a concise paragraph, "
        "focusing on the main topics discussed and any important context "
        "that should be preserved."
    )
    result = await process_request(
        summary_prompt,
        context.state_manager,
        output=False,  # We handle the output ourselves
    )
    
    # Extract summary text from result
    summary_text = ""
    if (
        result
        and hasattr(result, "result")
        and result.result
        and hasattr(result.result, "output")
    ):
        summary_text = result.result.output
    else:
        # Fallback logic for different message formats
        ...
    
    # Display summary in a formatted panel
    from tunacode.ui import panels
    await panels.panel("Conversation Summary", summary_text, border_style="cyan")
    
    # Show statistics
    await ui.info(f"Current message count: {original_count}")
    await ui.info("After compaction: 3 (summary + last 2 messages)")
    
    # Truncate the conversation history
    context.state_manager.session.messages = context.state_manager.session.messages[-2:]
    
    await ui.success("Context history has been summarized and truncated.")
```

## Phase 2 & 3 Implementation Sketch (Future Work)

```python
# Phase 2: Add verification
if await ui.confirm("Proceed with compaction?"):
    # Truncate only after confirmation
    ...
else:
    await ui.info("Compaction cancelled")

# Phase 3: Preserve summary in history
summary_msg = {
    "role": "system",
    "content": f"[Previous conversation summary]: {summary_text}",
    "metadata": {"type": "summary", "timestamp": datetime.now()}
}
context.state_manager.session.messages = [
    summary_msg,
    *context.state_manager.session.messages[-2:]
]
```

## Testing Considerations

1. Test with various conversation lengths
2. Verify summary quality for different types of conversations
3. Ensure message history integrity
4. Test cancellation flow
5. Verify UI formatting across terminals