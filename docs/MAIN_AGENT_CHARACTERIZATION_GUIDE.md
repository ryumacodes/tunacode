# Main Agent Characterization Test Guide

## Overview

This document provides a comprehensive guide for understanding and testing the main agent (`src/tunacode/core/agents/main.py`) through characterization tests. The main agent is the core orchestrator of TunaCode, handling LLM interactions, tool execution, and request processing.

## Architecture Overview

### Key Components

1. **Agent Creation & Management**
   - `get_or_create_agent()`: Singleton pattern for agent instances per model
   - Lazy imports for pydantic-ai dependencies
   - System prompt loading hierarchy

2. **Request Processing Pipeline**
   - `process_request()`: Main entry point for processing user messages
   - `_process_node()`: Handles individual agent response nodes
   - Iteration tracking and limits

3. **Tool Execution**
   - Structured tool calling via pydantic-ai
   - Fallback JSON parsing for compatibility
   - Tool call tracking and file context management

4. **Error Recovery**
   - `patch_tool_messages()`: Handles orphaned tool calls
   - Fallback response generation when max iterations reached
   - Graceful handling of missing attributes

## All Functions and Their Behaviors

### 1. `get_agent_tool()`
**Purpose**: Lazy import of pydantic_ai Agent and Tool classes
**Behavior**:
- Returns tuple: (Agent, Tool)
- Used to avoid circular imports
- No error handling (will raise ImportError if pydantic_ai not installed)

### 2. `get_model_messages()`
**Purpose**: Lazy import of pydantic_ai message types
**Behavior**:
- Returns tuple: (ModelRequest, ToolReturnPart)
- Used for creating synthetic tool responses

### 3. `_process_node(node, tool_callback, state_manager)`
**Purpose**: Process individual response nodes from the agent
**Key Behaviors**:
- Appends request/thought/model_response to session messages
- Displays thoughts immediately if `show_thoughts` enabled
- Extracts thoughts from JSON patterns in response content
- Handles tool calls via callback
- Tracks tool calls and files in context
- Falls back to JSON parsing if no structured tool calls

**Quirks**:
- Tool args can be dict or string - handles both cases
- Multiple thought extraction patterns (inline JSON, standalone, multi-line)
- Files only tracked from `read_file` tool calls
- Token counting displayed for responses when thoughts enabled

### 4. `get_or_create_agent(model, state_manager)`
**Purpose**: Create or retrieve agent instance for a model
**Key Behaviors**:
- Singleton pattern - one agent per model
- Loads system prompt from files in order:
  1. `prompts/system.md`
  2. `prompts/system.txt` (fallback)
  3. Default hardcoded prompt (final fallback)
- Registers all 7 tools with max_retries from config
- Attaches MCP servers if available

**Configuration Dependencies**:
- `settings.max_retries` (default: 3)

### 5. `patch_tool_messages(error_message, state_manager)`
**Purpose**: Add synthetic error responses for orphaned tool calls
**Key Behaviors**:
- Scans messages for tool calls without responses
- Ignores tools with retry prompts
- Creates synthetic ToolReturnPart with error message
- Uses current timestamp for synthetic responses

**Quirks**:
- Requires state_manager (raises ValueError if None)
- Only patches tools without returns OR retry prompts

### 6. `parse_json_tool_calls(text, tool_callback, state_manager)`
**Purpose**: Parse and execute tool calls from JSON in text
**Key Behaviors**:
- Finds JSON objects with "tool" and "args" keys
- Handles nested braces correctly
- Creates MockToolCall objects for execution
- Displays fallback execution in thoughts mode

**JSON Format Expected**:
```json
{"tool": "tool_name", "args": {...}}
```

### 7. `extract_and_execute_tool_calls(text, tool_callback, state_manager)`
**Purpose**: Extract tool calls from multiple text formats
**Key Behaviors**:
- Calls `parse_json_tool_calls()` for inline JSON
- Also parses JSON from markdown code blocks
- Supports ```json code blocks

### 8. `process_request(model, message, state_manager, tool_callback)`
**Purpose**: Main entry point for processing user requests
**Key Behaviors**:
- Creates/retrieves agent for model
- Copies message history for context
- Resets iteration tracking per request
- Processes nodes via `_process_node()`
- Enforces max_iterations limit
- Generates fallback response if needed
- Wraps result with response_state

**Configuration Dependencies**:
- `settings.max_iterations` (default: 20)
- `settings.fallback_response` (default: True)
- `settings.fallback_verbosity` (default: "normal")

**Fallback Response Details**:
- Only generated if no user response and max iterations reached
- Verbosity levels: "minimal", "normal", "detailed"
- Tracks files modified, commands run, tool usage
- Provides helpful next steps

## Critical Quirks and Edge Cases

### 1. Tool Args Handling
```python
# Args can be dict or string
if isinstance(part.args, dict):
    # Handle as dict
else:
    # Display as-is (string)
```

### 2. None Args Protection
```python
# None args converted to empty dict
"args": part.args if hasattr(part, "args") else {}
```

### 3. File Context Tracking
- Only `read_file` tool calls add to files_in_context
- Other tools don't affect file context
- Files displayed immediately in thoughts mode

### 4. Iteration Tracking
- `iteration_count` resets to 0 for each request
- `current_iteration` is 1-indexed (i + 1)
- Both stored in state_manager.session

### 5. Tool Call ID Generation
- Structured calls: Use provided tool_call_id
- Fallback JSON: `f"fallback_{datetime.now().timestamp()}"`
- Code block JSON: `f"codeblock_{datetime.now().timestamp()}"`

### 6. Thought Extraction Patterns
1. Inline JSON: `{"thought": "..."}`
2. Standalone JSON objects
3. Multi-line with escapes: Handles `\"` and `\n`
4. Deduplication of thoughts

### 7. Message History Handling
- Always copies message history: `mh = state_manager.session.messages.copy()`
- Prevents mutations affecting original

### 8. Wrapper Class Behavior
- `AgentRunWrapper`: Used for fallback responses
- `AgentRunWithState`: Used for normal responses
- Both preserve original attributes via `__getattribute__`

## Test Implementation Details

### Mock Objects Required

```python
class MockNode:
    """Mock agent response node"""
    def __init__(self):
        self.request = None
        self.thought = None
        self.model_response = None
        self.result = None

class MockToolCall:
    """Mock tool call part"""
    def __init__(self, tool_name, args=None, tool_call_id=None):
        self.part_kind = "tool-call"
        self.tool_name = tool_name
        self.args = args or {}
        self.tool_call_id = tool_call_id or f"test_{time.time()}"

class MockModelResponse:
    """Mock model response with parts"""
    def __init__(self, parts):
        self.parts = parts

class MockAgentRun:
    """Mock agent run for testing"""
    def __init__(self, nodes):
        self.nodes = nodes
        self.result = None
```

### State Manager Setup

```python
@pytest.fixture
def state_manager():
    """Create a mock state manager for testing"""
    sm = Mock()
    sm.session = Mock()
    sm.session.messages = []
    sm.session.agents = {}
    sm.session.user_config = {
        "settings": {
            "max_retries": 3,
            "max_iterations": 20,
            "fallback_response": True,
            "fallback_verbosity": "normal"
        }
    }
    sm.session.show_thoughts = False
    sm.session.tool_calls = []
    sm.session.files_in_context = set()
    sm.session.iteration_count = 0
    sm.session.current_iteration = 0
    return sm
```

### Key Test Scenarios

1. **System Prompt Loading**
   - Test all three loading paths
   - Verify fallback behavior
   - Check encoding handling

2. **Tool Registration**
   - Verify all 7 tools registered
   - Check max_retries configuration
   - Test MCP server integration

3. **Thought Extraction**
   - Test all three JSON patterns
   - Verify deduplication
   - Check display behavior

4. **Tool Execution**
   - Test structured tool calls
   - Test JSON fallback parsing
   - Test code block parsing
   - Verify tool tracking

5. **Iteration Limits**
   - Test max_iterations enforcement
   - Verify fallback response generation
   - Check verbosity modes

6. **Error Handling**
   - Test orphaned tool calls
   - Test missing attributes
   - Test type mismatches

## File Structure

```
tests/characterization/agent/
├── __init__.py                      # Package marker
├── conftest.py                      # Shared fixtures
├── test_agent_creation.py           # Agent creation tests
├── test_tool_message_patching.py    # Tool message patching tests
├── test_json_tool_parsing.py        # JSON tool parsing tests
├── test_process_node.py             # Node processing tests
└── test_process_request.py          # Request processing tests
```

## Running the Tests

```bash
# Run all agent characterization tests
pytest tests/characterization/agent/ -v

# Run specific test file
pytest tests/characterization/agent/test_agent_creation.py -v

# Run specific test
pytest tests/characterization/agent/test_agent_creation.py::TestAgentCreation::test_get_or_create_agent_first_time -v

# Run with coverage
pytest tests/characterization/agent/ --cov=tunacode.core.agents.main --cov-report=html
```

## Important Notes

1. **Golden Master Approach**: These tests capture CURRENT behavior, including bugs
2. **No Bug Fixes**: Don't fix issues found during characterization
3. **Mock Everything**: Use mocks to isolate the unit under test
4. **Async Testing**: Use `@pytest.mark.asyncio` for async functions
5. **State Preservation**: Always verify state changes in state_manager

## Common Pitfalls

1. **Forgetting to mock lazy imports**: The get_agent_tool() and get_model_messages() functions need mocking
2. **Not handling both dict and string args**: Tool args can be either type
3. **Missing async context**: Many functions are async and need proper testing
4. **State mutation**: Always copy message history to avoid mutations
5. **Tool call ID uniqueness**: Ensure unique IDs for mock tool calls

## Future Considerations

1. **Performance**: Current implementation creates wrapper classes for every request
2. **Memory**: Message history grows unbounded
3. **Concurrency**: No explicit thread safety for agent instances
4. **Error Recovery**: Limited retry mechanisms beyond tool retries
5. **Extensibility**: Hard-coded tool list (not dynamically extensible)

This guide should enable anyone to understand and test the main agent's behavior comprehensively. The characterization tests will serve as a safety net for future refactoring and improvements.