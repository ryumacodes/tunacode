<!-- This document explains TunaCode's core architecture including StateManager, Agent system, Tool handler, and Setup coordinator -->

# TunaCode Core Architecture Deep Dive

## Overview

The core architecture of TunaCode is built around a central state management system with modular components for agent interaction, tool execution, and user interface coordination. This document provides an in-depth analysis of each core component.

## StateManager (core/state.py)

The `StateManager` is the central nervous system of TunaCode, maintaining all runtime state in a single, coherent structure.

### SessionState Dataclass

```python
@dataclass
class SessionState:
    """Comprehensive session state container"""

    # User configuration and model state
    user_config: Dict[str, Any]          # ~/.config/tunacode.json contents
    default_model: Optional[str]         # Current model (provider:model format)
    model_override: Optional[str]        # Temporary model override
    api_keys: Dict[str, Optional[str]]   # Validated API keys by provider

    # Agent and tool state
    agent_instances: Dict[str, Any]      # Cached pydantic-ai agents by model
    registry: Optional[Any]              # Command registry instance
    mcp_manager: Optional[Any]           # MCP server manager
    tools: List[Any]                     # Available tools (internal + MCP)
    allowed_tools: Set[str]              # Pre-approved tools from templates

    # Conversation and message state
    messages: List[Message]              # Full conversation history
    last_assistant_message: Optional[str] # Latest assistant response

    # UI and interaction state
    streaming_panel: Optional[Any]       # Active streaming panel
    is_streaming: bool                   # Streaming display mode
    yolo_mode: bool                      # Skip confirmations
    show_thoughts: bool                  # Display agent reasoning

    # Token usage and limits
    total_tokens_used: int               # Session token count
    total_cost: float                    # Session cost in USD
    context_window: int                  # Model context limit
    max_response_tokens: int             # Response token limit
    max_iterations: Optional[int]        # ReAct iteration limit

    # Execution context
    in_sub_agent: bool                   # Recursive agent execution
    top_level_iterations_used: int       # Top-level iteration count
    top_level_max_iterations: int        # Top-level iteration limit

    # Task management
    current_task: Optional[Any]          # Active asyncio task
    task_cancelled: bool                 # Cancellation flag
    code_base_path: Optional[Path]       # Project root path
```

### Key Methods

#### get_model()
```python
def get_model(self) -> Optional[str]:
    """Get current model with override support"""
    # Returns model_override if set, else default_model
    # Handles validation and format checking
```

#### update_config()
```python
def update_config(self, config: Dict[str, Any]) -> None:
    """Update configuration and persist to disk"""
    # Merges new config with existing
    # Writes to ~/.config/tunacode.json
    # Updates internal state
```

#### add_message()
```python
def add_message(self, message: Message) -> None:
    """Add message with token estimation"""
    # Appends to message history
    # Estimates tokens for context management
    # Tracks assistant responses
```

#### estimate_tokens_in_messages()
```python
def estimate_tokens_in_messages(self) -> int:
    """Calculate total tokens in conversation"""
    # Uses token_counter utility
    # Includes system prompts
    # Accounts for message formatting
```

## Agent System (core/agents/)

### Main Agent (main.py)

The main agent is built on pydantic-ai with sophisticated request processing:

#### Key Features

1. **Tool Integration**
   - All internal tools registered
   - MCP tool discovery and registration
   - Dynamic tool availability based on context

2. **Parallel Execution**
   - Read-only tools execute concurrently
   - Automatic batching of consecutive reads
   - Configurable parallelism (TUNACODE_MAX_PARALLEL)

3. **Iteration Management**
   - Tracks productive vs unproductive iterations
   - Intervenes when stuck in loops
   - Respects user-configured limits

4. **Task Completion Detection**
   - TUNACODE_TASK_COMPLETE marker
   - Graceful completion handling
   - Result extraction

#### Request Processing Flow

```python
async def process_request(request: str, state: StateManager, ...) -> str:
    """Main request processing pipeline"""

    # 1. Context preparation
    - Load TUNACODE.md if present
    - Prepare system prompt
    - Initialize iteration tracking

    # 2. Agent execution
    - Create/retrieve agent instance
    - Execute with tools and context
    - Handle streaming/static display

    # 3. Tool execution
    - Batch read-only tools
    - Execute writes sequentially
    - Handle confirmations

    # 4. Response handling
    - Extract final response
    - Update token usage
    - Handle task completion
```

### Agent Utilities (utils.py)

#### batch_consecutive_read_only_tools()
```python
def batch_consecutive_read_only_tools(tool_calls: List[Any]) -> List[List[Any]]:
    """Group read-only tools for parallel execution"""
    # Identifies consecutive read operations
    # Creates execution batches
    # Preserves order for writes
```

#### execute_tool_calls_with_parallel_batching()
```python
async def execute_tool_calls_with_parallel_batching(...):
    """Execute tools with optimized parallelism"""
    # Processes batches from batch_consecutive_read_only_tools
    # Executes reads in parallel
    # Maintains sequential writes
    # Handles UI feedback
```

#### patch_orphaned_tool_calls()
```python
def patch_orphaned_tool_calls(messages: List[Message]) -> List[Message]:
    """Fix orphaned tool calls in message history"""
    # Identifies tool calls without results
    # Creates placeholder results
    # Maintains message integrity
```

## Tool Handler (core/tool_handler.py)

The `ToolHandler` manages tool execution with security and UI coordination:

### Key Responsibilities

1. **Permission Management**
   - Tracks tool approvals
   - Integrates with YOLO mode
   - Respects template allowlists

2. **Confirmation Workflows**
   - Generates confirmation prompts
   - Handles user responses
   - Provides skip options

3. **Tool Registration**
   - Internal tool discovery
   - MCP tool integration
   - Dynamic availability

### Core Methods

#### get_tools()
```python
def get_tools(self) -> List[Any]:
    """Get all available tools"""
    # Combines internal tools
    # Adds MCP tools if available
    # Returns unified tool list
```

#### check_tool_permission()
```python
async def check_tool_permission(tool_name: str, args: Dict) -> bool:
    """Check if tool execution is permitted"""
    # Checks YOLO mode
    # Consults allowed_tools set
    # Prompts for confirmation
```

## Background Task Management (core/background/)

The `BackgroundTaskManager` handles async operations:

### Features

1. **Task Lifecycle**
   - Creation and tracking
   - Graceful cancellation
   - Error propagation

2. **Cleanup Coordination**
   - Shutdown handlers
   - Resource cleanup
   - State persistence

### Implementation

```python
class BackgroundTaskManager:
    def __init__(self):
        self.tasks: List[asyncio.Task] = []
        self.shutdown_handlers: List[Callable] = []

    async def create_task(self, coro: Coroutine) -> asyncio.Task:
        """Create and track background task"""
        task = asyncio.create_task(coro)
        self.tasks.append(task)
        return task

    async def shutdown(self):
        """Graceful shutdown of all tasks"""
        for handler in self.shutdown_handlers:
            await handler()
        for task in self.tasks:
            task.cancel()
```

## Setup System (core/setup/)

### Setup Coordinator (coordinator.py)

The setup system uses a modular approach with validation steps:

#### Setup Steps

1. **EnvironmentSetup**
   - API key detection
   - Provider validation
   - Environment preparation

2. **ConfigSetup**
   - User configuration creation
   - Default value population
   - Path resolution

3. **GitSafetySetup**
   - Repository detection
   - Safety warnings
   - Branch recommendations

4. **TemplateSetup**
   - Directory creation
   - Example templates
   - Permission setup

### Parallel Execution

```python
async def run_setup_steps():
    """Execute setup with parallelism"""
    # Groups independent steps
    # Runs in parallel where possible
    # Maintains dependencies
```

## Token Usage Tracking (core/token_usage/)

### Usage Tracker (usage_tracker.py)

Comprehensive token and cost tracking:

```python
class UsageTracker:
    """Track token usage and costs"""

    def update_usage(self, response: Any, model: str):
        """Update usage from API response"""
        # Parses provider-specific formats
        # Calculates costs
        # Updates totals

    def get_usage_string(self) -> str:
        """Format usage for display"""
        # Shows tokens used
        # Displays costs
        # Indicates context usage
```

### API Response Parser (api_response_parser.py)

Provider-specific parsing logic:

```python
def parse_response_usage(response: Any, provider: str) -> Dict:
    """Extract usage from provider response"""
    # Handles Anthropic format
    # Handles OpenAI format
    # Handles streaming updates
```

## Logging Infrastructure (core/logging/)

### Unified Logging System

The logging system provides consistent output across all components:

#### Features

1. **Multiple Handlers**
   - Console output with formatting
   - File logging with rotation
   - Debug mode support

2. **Custom Formatters**
   - Timestamp formatting
   - Level-based coloring
   - Component identification

3. **Async Support**
   - Thread-safe operations
   - Async context preservation
   - Performance optimization

## Integration Points

### 1. StateManager ↔ Agent
- State provides configuration and context
- Agent updates token usage and messages
- Bidirectional data flow

### 2. Agent ↔ ToolHandler
- Agent requests tool execution
- ToolHandler manages permissions
- Results flow back to agent

### 3. ToolHandler ↔ UI
- UI displays confirmations
- User input flows to handler
- Visual feedback coordination

### 4. Background Manager ↔ All Components
- Manages long-running operations
- Coordinates shutdown
- Handles async lifecycle

## Performance Considerations

### 1. Caching
- Agent instances cached by model
- Import caching for performance
- Configuration caching

### 2. Parallel Execution
- Read operations parallelized
- Independent setup steps concurrent
- Async throughout

### 3. Memory Management
- Message history pruning
- Token estimation for limits
- Resource cleanup

## Security Architecture

### 1. Permission System
- Explicit tool approval
- Template-based allowlists
- YOLO mode for power users

### 2. Input Validation
- Command sanitization
- Path validation
- Git boundary enforcement

### 3. Error Isolation
- Component error boundaries
- Graceful degradation
- User notification

## Future Extensibility

### 1. Plugin System
- Tool plugin interface
- Command plugin support
- Provider plugins

### 2. State Persistence
- Session save/restore
- Conversation export
- Settings profiles

### 3. Advanced Features
- Multi-agent coordination
- Task scheduling
- Workflow automation
