# TunaCode Agent Architecture & Flow

This document outlines the complete flow of how the TunaCode agent system works, from request initiation to tool execution and response generation.

## Overview

TunaCode is a **tool-centric AI agent** built on pydantic-ai that operates as a senior software developer assistant in your terminal. Rather than being a simple chatbot, it's an operational agent that executes real actions through specialized tools.

## Core Architecture Components

### 1. Agent System (`src/tunacode/core/agents/main.py`)
- **Framework**: Built on pydantic-ai for LLM agent implementation
- **Multi-Provider Support**: Works with Anthropic, OpenAI, Google, OpenRouter
- **Model Format**: `provider:model-name` (e.g., `anthropic:claude-3-opus`)
- **State Management**: Centralized through `StateManager` class
- **Background Tasks**: Managed via `core/background/manager.py`

### 2. Tool System Architecture
The agent operates through **8 core tools** divided into two performance categories:

#### Read-Only Tools (Parallel Execution)
- `read_file` - Read file contents with line numbers (4KB limit)
- `grep` - Fast parallel text search with context
- `list_dir` - Efficient directory listing
- `glob` - File pattern matching

#### Write/Execute Tools (Sequential with Confirmation)
- `write_file` - Create new files (fails if exists)
- `update_file` - Modify existing files with diff preview
- `run_command` - Execute shell commands
- `bash` - Advanced shell with enhanced security

## Request Processing Flow

### Phase 1: Agent Initialization

```
User Request → process_request() → get_or_create_agent()
```

1. **Agent Retrieval/Creation** (`get_or_create_agent()`)
   - Check if agent exists for specified model in `state_manager.session.agents`
   - If not exists:
     - Load system prompt from `src/tunacode/prompts/system.md`
     - Load project context from `TUNACODE.md` if present
     - Register 8 core tools with retry capabilities
     - Initialize MCP servers for external tools
     - Store agent in session state

2. **System Prompt Construction**
   ```
   Base System Prompt + Project Context (TUNACODE.md) → Complete System Prompt
   ```

### Phase 2: Request Processing Setup

1. **Session State Preparation**
   - Copy message history: `mh = state_manager.session.messages.copy()`
   - Get max iterations from config (default: 40)
   - Reset iteration counter: `state_manager.session.iteration_count = 0`
   - Create tool buffer: `tool_buffer = ToolBuffer()`

2. **Configuration Loading**
   - Max retries per tool (default: 3)
   - Fallback response enabled (default: true)
   - Parallel execution limits (`TUNACODE_MAX_PARALLEL`)

### Phase 3: Agent Execution Loop

```
for i in range(max_iterations):
    node = await agent.arun_stream(message, message_history=mh)
    await _process_node(node, tool_callback, state_manager, tool_buffer)
```

#### Node Processing (`_process_node()`)

1. **Message Tracking**
   - Append request to message history
   - Track thoughts if present: `{"thought": node.thought}`
   - Store model response: `node.model_response`

2. **Thought Processing** (when `/thoughts on`)
   - Display raw API response data
   - Show reasoning patterns
   - Extract and display JSON thoughts
   - Count tool calls in response

3. **Tool Call Collection**
   ```python
   for part in node.model_response.parts:
       if part.part_kind == "tool-call":
           tool_parts.append(part)
           # Track tool call in session
           # Update files in context for read_file calls
   ```

4. **Parallel Execution Decision**
   ```python
   all_read_only = all(part.tool_name in READ_ONLY_TOOLS for part in tool_parts)

   if all_read_only and len(tool_parts) > 1:
       # Execute in parallel batch
       await execute_tools_parallel(tool_parts, tool_callback)
   else:
       # Execute sequentially
       for part in tool_parts:
           await tool_callback(part, node)
   ```

### Phase 4: Tool Execution System

#### Parallel Execution (`execute_tools_parallel()`)

1. **Concurrency Control**
   ```python
   max_parallel = int(os.environ.get("TUNACODE_MAX_PARALLEL", os.cpu_count() or 4))
   ```

2. **Batch Processing**
   ```python
   if len(tool_calls) > max_parallel:
       # Execute in batches of max_parallel
       for i in range(0, len(tool_calls), max_parallel):
           batch = tool_calls[i:i + max_parallel]
           batch_results = await asyncio.gather(*batch_tasks)
   ```

3. **Error Handling**
   - Wrap each tool execution with error handling
   - Return exceptions rather than raising them
   - Continue processing remaining tools

#### Sequential Execution (Write/Execute Tools)

1. **User Confirmation**
   - Show diff for file operations
   - Display command for shell operations
   - Wait for user approval (unless in yolo mode)

2. **Safety Checks**
   - Validate file paths
   - Check permissions
   - Prevent dangerous operations

### Phase 5: Tool Buffering & Batching

#### ToolBuffer System

```python
class ToolBuffer:
    def __init__(self):
        self.read_only_tasks: List[Tuple[Any, Any]] = []

    def add(self, part, node):
        # Buffer read-only tools

    def flush(self):
        # Return and clear buffered tasks
```

#### Batching Strategy (`batch_read_only_tools()`)

```python
def batch_read_only_tools(tool_calls):
    current_batch = []
    for tool_call in tool_calls:
        if tool_name in READ_ONLY_TOOLS:
            current_batch.append(tool_call)  # Add to batch
        else:
            yield current_batch  # Yield read-only batch
            yield [tool_call]    # Yield write tool alone
```

### Phase 6: Response Generation & Cleanup

1. **Final Tool Buffer Flush**
   ```python
   if tool_buffer.has_tasks():
       buffered_tasks = tool_buffer.flush()
       await execute_tools_parallel(buffered_tasks, tool_callback)
   ```

2. **Fallback Response Handling**
   ```python
   if not response_state.has_user_response and i >= max_iterations:
       patch_tool_messages("Task incomplete", state_manager)
       # Generate fallback summary
   ```

3. **Context Updates**
   - Update files in context set
   - Track tool call statistics
   - Update cost tracking
   - Preserve message history

## Performance Optimizations

### 1. Parallel Tool Execution
- **3x-10x Performance Gain**: Read-only tools execute concurrently
- **Smart Batching**: Groups consecutive read-only operations
- **Resource Management**: Respects CPU limits and memory constraints

### 2. Tool-Specific Optimizations
- **Grep Tool**: Fast-glob prefiltering with 3-second deadline
- **Read File**: 4KB content limit per file
- **Directory Listing**: Efficient without shell commands
- **Pattern Matching**: Optimized glob patterns

### 3. Memory Management
- **Lazy Imports**: Dynamic loading of pydantic-ai components
- **Message Truncation**: Long content truncated for display
- **Context Limits**: Bounded message history and file context

## Safety & Security Features

### 1. File Operation Safety
- **No Overwrites**: `write_file` fails if file exists
- **Diff Preview**: `update_file` shows changes before applying
- **Permission Tracking**: Per-session file operation permissions
- **Git Safety**: No automatic commits, encourages branching

### 2. Command Execution Safety
- **Full Confirmation**: Shell commands require explicit approval
- **Output Limits**: 5KB limit on bash command output
- **Environment Control**: Enhanced security in bash tool
- **Yolo Mode**: Option to skip confirmations for power users

### 3. Error Handling
- **Graceful Degradation**: Continues on tool failures
- **Retry Logic**: Configurable retry attempts per tool
- **Fallback Mechanisms**: JSON tool parsing for incompatible providers
- **Tool Response Patching**: Synthetic responses for orphaned calls

## Integration Points

### 1. State Management (`core/state.py`)
- **Single Source of Truth**: All session state centralized
- **User Configuration**: Stored in `~/.config/tunacode.json`
- **Message History**: Persistent conversation context
- **Agent Instances**: Cached per model type

### 2. UI Components
- **REPL Interface**: `prompt_toolkit` for multiline input
- **Rich Output**: Formatted using `rich` library
- **Confirmation Dialogs**: Interactive tool approval
- **Progress Indicators**: Spinners during processing

### 3. External Integrations
- **MCP Protocol**: Support for external tools via Model Context Protocol
- **Git Integration**: Safety checks and branch operations
- **Package Managers**: Support for various language ecosystems
- **IDE Integration**: Bridge components for editor integration

## Configuration & Customization

### 1. User Configuration
```json
{
  "default_model": "provider:model-name",
  "settings": {
    "max_iterations": 40,
    "max_retries": 3,
    "fallback_response": true
  },
  "env": {
    "ANTHROPIC_API_KEY": "...",
    "OPENAI_API_KEY": "..."
  }
}
```

### 2. Environment Variables
- `TUNACODE_MAX_PARALLEL`: Parallel execution limit
- `TUNACODE_SHOW_THOUGHTS`: Debug mode toggle
- Provider API keys for LLM access

### 3. Project Configuration
- `TUNACODE.md`: Project-specific context and conventions
- `.tunacode/`: Local configuration directory
- Tool-specific configuration files

This architecture enables TunaCode to operate as a powerful, safe, and efficient AI coding assistant that can understand complex codebases and execute sophisticated development tasks while maintaining security and performance.
