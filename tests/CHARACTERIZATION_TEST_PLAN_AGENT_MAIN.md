# Characterization Test Plan for Main Agent (core.agents.main)

## Overview
This document provides a comprehensive analysis of the Main Agent module (`src/tunacode/core/agents/main.py`) and details all behaviors, quirks, and edge cases that need to be captured in characterization tests.

## Key Components and Behaviors

### 1. Agent Creation (`get_or_create_agent`)

**Purpose**: Lazy creation and caching of pydantic-ai agents

**Behaviors to Test**:
- ✅ First-time agent creation with all 7 tools registered
- ✅ Caching - returns existing agent for same model
- ✅ System prompt loading hierarchy:
  1. Try `prompts/system.md` first
  2. Fall back to `prompts/system.txt`
  3. Use hardcoded default: "You are a helpful AI assistant for software development tasks."
- ✅ Tool registration with max_retries from config (default: 3)
- ✅ MCP server integration via `get_mcp_servers()`
- ✅ Multiple concurrent model agents in session

**Edge Cases**:
- ✅ Missing prompt files (both .md and .txt)
- ✅ File read errors during prompt loading
- ✅ Config missing max_retries setting

### 2. Process Node (`_process_node`)

**Purpose**: Process individual nodes from agent iteration

**Behaviors to Test**:
- ✅ Request handling - appends to messages
- ✅ Thought handling - creates {"thought": "..."} message
- ✅ Thought display when `show_thoughts` enabled
- ✅ Model response processing with multiple parts
- ✅ Tool call tracking in session.tool_calls with iteration number
- ✅ Files in context tracking for read_file tool
- ✅ Tool return observations (truncated to 2000 chars)
- ✅ Fallback JSON parsing when no structured tool calls

**Thought Display Behaviors**:
- ✅ Displays "THOUGHT: ..." for node thoughts
- ✅ Extracts inline JSON thoughts: `{"thought": "..."}`
- ✅ Handles multiline thoughts with escape sequences
- ✅ Shows tool details (name, args) when thoughts enabled
- ✅ Special formatting for common tools (read_file, write_file, etc.)
- ✅ Shows "FILES IN CONTEXT" after read_file
- ✅ Truncates long responses to 500 chars for display
- ✅ Shows token estimates for responses

**Edge Cases**:
- ✅ Node with no attributes set
- ✅ Tool args as string instead of dict
- ✅ Tool args as None
- ✅ Empty model response parts
- ✅ Invalid JSON in thought extraction

### 3. Tool Message Patching (`patch_tool_messages`)

**Purpose**: Add synthetic error responses for orphaned tool calls

**Behaviors to Test**:
- ✅ No action when all tools have responses
- ✅ Creates synthetic tool-return for orphaned calls
- ✅ Ignores tools with retry-prompt (model is handling)
- ✅ Preserves tool_call_id mapping
- ✅ Uses provided error message in synthetic response
- ✅ Raises ValueError if state_manager is None

**Edge Cases**:
- ✅ Empty message list
- ✅ Messages without parts attribute
- ✅ Multiple orphaned tools

### 4. JSON Tool Parsing (`parse_json_tool_calls`)

**Purpose**: Fallback parser for JSON tool calls when structured calling fails

**Behaviors to Test**:
- ✅ Parses simple JSON: `{"tool": "name", "args": {...}}`
- ✅ Handles multiple JSON objects in text
- ✅ Nested JSON with escaped quotes
- ✅ Creates MockToolCall with fallback timestamp ID
- ✅ Executes via tool_callback
- ✅ Silently ignores invalid JSON
- ✅ No-op when tool_callback is None
- ✅ Logs "FALLBACK: Executed..." when thoughts enabled
- ✅ Error logging when tool execution fails

**JSON Parsing Algorithm**:
- Tracks brace count to find complete JSON objects
- Only parses objects with both "tool" and "args" keys
- Handles nested objects correctly

**Edge Cases**:
- ✅ Malformed JSON
- ✅ JSON without required keys
- ✅ Exception in tool callback
- ✅ Empty args object

### 5. Extract and Execute Tool Calls (`extract_and_execute_tool_calls`)

**Purpose**: Multi-format tool call extraction

**Behaviors to Test**:
- ✅ Format 1: Inline JSON via `parse_json_tool_calls`
- ✅ Format 2: JSON in code blocks with regex
- ✅ Both formats in same text
- ✅ Code block regex pattern matching
- ✅ Creates MockToolCall with codeblock timestamp ID
- ✅ Error handling for invalid code block JSON

**Code Block Pattern**:
```regex
```json\s*(\{(?:[^{}]|"[^"]*"|(?:\{[^}]*\}))*"tool"(?:[^{}]|"[^"]*"|(?:\{[^}]*\}))*\})\s*```
```

**Edge Cases**:
- ✅ No tool calls in text
- ✅ Invalid JSON in code blocks
- ✅ Mixed valid and invalid formats

### 6. Process Request (`process_request`)

**Purpose**: Main agent request processing loop

**Behaviors to Test**:
- ✅ Agent creation/retrieval
- ✅ Message history copying
- ✅ Max iterations enforcement (default: 20)
- ✅ Iteration counting and tracking
- ✅ Response state tracking (has_user_response)
- ✅ Fallback response generation when max iterations reached
- ✅ Fallback verbosity levels: "normal" and "detailed"
- ✅ Tool call analysis for fallback context
- ✅ AgentRunWrapper creation for response_state
- ✅ Iteration progress display when thoughts enabled

**Fallback Response Components**:
- Summary: "Reached maximum iterations without producing a final response."
- Progress: Shows iterations completed
- What happened: Tool execution summary
- Suggested next steps: Helpful guidance

**Detailed Verbosity Additions**:
- Files modified list (max 5 shown)
- Commands executed list (max 3 shown)
- Truncates long commands to 60 chars

**Edge Cases**:
- ✅ No user response produced
- ✅ Fallback disabled in config
- ✅ Empty tool calls
- ✅ Very long file lists or command lists

### 7. Configuration Dependencies

**Expected Config Structure**:
```python
{
    "settings": {
        "max_retries": 3,      # For tool retries
        "max_iterations": 20,   # Agent loop limit
        "fallback_response": True,  # Enable fallback
        "fallback_verbosity": "normal"  # or "detailed"
    }
}
```

**Defaults**:
- max_retries: 3
- max_iterations: 20
- fallback_response: True
- fallback_verbosity: "normal"

### 8. State Manager Integration

**Session Attributes Used**:
- `agents`: Dict[model_name, agent] cache
- `messages`: Message history list
- `user_config`: Configuration dict
- `current_model`: Active model name
- `show_thoughts`: Boolean for debug display
- `tool_calls`: List of tool execution records
- `files_in_context`: Set of file paths from read_file
- `iteration_count`: Total iterations in request
- `current_iteration`: Current iteration number

### 9. Quirks and Special Behaviors

1. **Tool Args Handling**:
   - Expects dict but handles string gracefully
   - None args converted to empty dict
   - Non-dict args displayed as-is in thoughts

2. **Message Appending**:
   - Tool observations prefixed with "OBSERVATION[tool_name]: "
   - Thoughts stored as {"thought": "..."}
   - Raw node.request and node.model_response appended

3. **File Path Tracking**:
   - Only tracks read_file operations
   - Uses set to avoid duplicates
   - Displayed when thoughts enabled

4. **Iteration Behavior**:
   - Resets iteration_count at start
   - Tracks current_iteration during loop
   - Breaks immediately when max reached

5. **Wrapper Classes**:
   - AgentRunWrapper for fallback responses
   - AgentRunWithState for normal responses
   - Both preserve original attributes via __getattribute__

## Mock Objects Needed

1. **MockToolCall**: Simulates tool call with tool_name, args, tool_call_id
2. **MockToolReturn**: Simulates tool return with content
3. **MockRetryPrompt**: Simulates retry prompt
4. **MockModelResponse**: Contains parts list
5. **MockNode**: Flexible node with optional attributes
6. **MockAgentRun**: Simulates agent iteration
7. **MockStateManager**: Minimal state manager for unit tests

## Test File Structure

```python
tests/test_characterization_agent_main.py
├── TestMainAgentCharacterization
│   ├── setup_method() - Initialize state manager
│   ├── # Agent Creation Tests
│   ├── test_get_or_create_agent_first_time()
│   ├── test_get_or_create_agent_cached()
│   ├── test_get_or_create_agent_system_prompt_fallback()
│   ├── test_get_or_create_agent_default_prompt()
│   ├── # Tool Message Patching Tests
│   ├── test_patch_tool_messages_no_orphans()
│   ├── test_patch_tool_messages_with_orphans()
│   ├── test_patch_tool_messages_with_retry_prompts()
│   ├── test_patch_tool_messages_no_state_manager()
│   ├── # JSON Tool Parsing Tests
│   ├── test_parse_json_tool_calls_simple()
│   ├── test_parse_json_tool_calls_multiple()
│   ├── test_parse_json_tool_calls_nested_braces()
│   ├── test_parse_json_tool_calls_invalid_json()
│   ├── test_parse_json_tool_calls_no_callback()
│   ├── test_parse_json_tool_calls_with_thoughts_enabled()
│   ├── test_parse_json_tool_calls_exception_handling()
│   ├── # Extract and Execute Tests
│   ├── test_extract_and_execute_tool_calls_inline_json()
│   ├── test_extract_and_execute_tool_calls_code_blocks()
│   ├── test_extract_and_execute_tool_calls_mixed_formats()
│   ├── test_extract_and_execute_tool_calls_invalid_code_block()
│   ├── # Process Node Tests
│   ├── test_process_node_with_request()
│   ├── test_process_node_with_thought()
│   ├── test_process_node_with_thought_display_enabled()
│   ├── test_process_node_with_tool_calls()
│   ├── test_process_node_tool_call_with_string_args()
│   ├── test_process_node_tool_return()
│   ├── test_process_node_model_response_thoughts_enabled()
│   ├── test_process_node_fallback_json_parsing()
│   ├── # Process Request Tests
│   ├── test_process_request_basic_flow()
│   ├── test_process_request_max_iterations_reached()
│   ├── test_process_request_fallback_response_detailed()
│   ├── test_process_request_fallback_disabled()
│   ├── test_process_request_with_thoughts_enabled()
│   ├── test_process_request_iteration_tracking()
│   ├── # Edge Cases and Quirks
│   ├── test_empty_messages_handling()
│   ├── test_malformed_node_handling()
│   ├── test_concurrent_model_agents()
│   └── test_tool_call_args_edge_cases()
```

## Coverage Goals

- **Critical Paths**: 100% coverage
  - get_or_create_agent
  - process_request main loop
  - patch_tool_messages
  - _process_node

- **Fallback Mechanisms**: 100% coverage
  - JSON tool parsing
  - Fallback response generation
  - Error handling paths

- **Edge Cases**: Comprehensive
  - File not found scenarios
  - Invalid JSON handling
  - Missing attributes
  - Type mismatches

## Implementation Notes

1. Use `pytest.mark.asyncio` for all async tests
2. Mock external dependencies (Agent, Tool, UI console)
3. Capture exact behavior including error messages
4. Test both success and failure paths
5. Verify state mutations (messages, tool_calls, etc.)
6. Check all branches in conditional logic

## Success Criteria

- [x] All main functions have characterization tests
- [x] Edge cases and quirks are documented and tested
- [x] Mock objects simulate real behavior accurately
- [x] Tests pass without modifying source code
- [x] Coverage includes all critical paths
- [x] Fallback mechanisms are thoroughly tested
- [x] State manager integration is verified
- [x] Configuration handling is tested with defaults
