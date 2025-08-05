# Task 17: Fix message history cleanup in patch_tool_messages()
_Started: 2025-07-29 15:14:58_
_Agent: task17

[1] Analyzing current patch_tool_messages() implementation in src/tunacode/core/agents/main.py to understand existing logic
[2] Found patch_tool_messages() function. Current implementation already handles retry prompts (lines 611-672) and adds synthetic error responses when retry limit is exceeded. Need to examine if messages with retry prompts are being properly cleaned up.
[3] Found that patch_tool_messages tracks retry prompts but does not remove them from message history. The function only adds synthetic error responses when retry limit is exceeded, but the original retry prompt messages remain in the history, causing contamination.
[4] Implementing message cleanup logic to remove retry prompts that led to failures. Will filter out messages containing retry prompts when retry limit is exceeded.
[5] Implemented message cleanup logic that: 1) Tracks failed retry prompts (those exceeding retry limit), 2) Filters them out of message history, 3) Preserves message structure while removing only the failed retry prompt parts. The synthetic error response generation already exists via synthesize_error_response().
[6] Writing unit tests for patch_tool_messages() to verify: 1) Retry prompts are removed when limit exceeded, 2) Successful responses preserved, 3) Message chronology maintained, 4) Different failure types handled correctly
[7] Task completed successfully! Summary of changes:
[7] 1. Enhanced patch_tool_messages() to track and remove failed retry prompts
[7] 2. Added logic to filter out retry prompt parts when retry limit is exceeded
[7] 3. Preserved message structure while removing only problematic parts
[7] 4. Maintained chronological order and message integrity
[7] 5. Added comprehensive logging for debugging
[7] 6. Created 6 unit tests covering all scenarios including:
[7]    - Failed retry prompt cleanup
[7]    - Preservation of successful responses
[7]    - Multiple retry prompt handling
[7]    - Mixed message parts cleanup
[7]    - No cleanup when retries allowed
[7]    - Error type extraction from retry prompts
[7] All tests passing and code is properly linted.
