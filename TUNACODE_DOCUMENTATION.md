<!-- This is a comprehensive all-in-one documentation file covering architecture, API reference, and development guide -->

# TunaCode CLI - Comprehensive Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Module Documentation](#module-documentation)
5. [API Reference](#api-reference)
6. [Development Guide](#development-guide)
7. [Configuration](#configuration)
8. [Tools and Commands](#tools-and-commands)

## Project Overview

TunaCode CLI is an AI-powered command-line coding assistant that enables developers to interact with their codebase using natural language. Built on top of `pydantic-ai`, it provides an interactive REPL environment where developers can ask questions, make changes, and execute commands with AI assistance.

### Key Features

- **Multi-Provider LLM Support**: Works with Anthropic, OpenAI, Google, OpenRouter, and other providers
- **Parallel Tool Execution**: Read-only operations execute concurrently for 3x performance improvement
- **MCP Integration**: Supports Model Context Protocol for external tool integration
- **Interactive REPL**: Rich terminal interface with syntax highlighting and multiline input
- **Safety-First Design**: Requires confirmation for file modifications and encourages Git branching
- **Extensible Tool System**: Seven built-in tools with support for external MCP tools

### Technology Stack

- **Python 3.10+**: Core language
- **pydantic-ai**: LLM agent framework
- **prompt_toolkit**: Interactive terminal UI
- **rich**: Terminal formatting and output
- **typer**: CLI framework
- **tiktoken**: Token counting for context management

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Entry Point                        │
│                     (tunacode.cli.main)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                         Setup Flow                           │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Environment  │  │    Model     │  │  Configuration  │  │
│  │    Setup     │  │  Validation  │  │     Setup       │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                          REPL Loop                           │
│                    (tunacode.cli.repl)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ User Input   │  │   Command    │  │     Agent       │  │
│  │   Handler    │  │   Registry   │  │   Processing    │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                      Core Components                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │    Agent     │  │     Tool     │  │     State       │  │
│  │    System    │  │   Handler    │  │    Manager      │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Relationships

1. **Entry Flow**: `main.py` → `setup` → `repl` → user interaction loop
2. **Agent Flow**: user input → agent processing → tool execution → response
3. **Tool Flow**: tool request → confirmation UI → execution → result
4. **State Flow**: all components access centralized `StateManager`

## Core Components

### 1. State Management (`core/state.py`)

The `StateManager` is the central hub for all session data:

```python
@dataclass
class SessionState:
    user_config: UserConfig
    agents: dict[str, Any]
    messages: MessageHistory
    total_cost: float
    current_model: ModelName
    spinner: Optional[Any]
    tool_ignore: list[ToolName]
    yolo: bool
    show_thoughts: bool
    session_id: SessionId
    todos: list[TodoItem]
    files_in_context: set[str]
    tool_calls: list[dict[str, Any]]
    iteration_count: int
    # ... additional fields
```

Key responsibilities:
- Maintains conversation history
- Tracks token usage and costs
- Manages UI state (spinner, streaming)
- Handles recursive execution contexts
- Stores todo items and file context

### 2. Agent System (`core/agents/main.py`)

The main agent orchestrates LLM interactions:

- **Model Support**: Unified interface for multiple providers
- **Tool Integration**: Manages tool registration and execution
- **Parallel Execution**: Batches read-only tools for concurrent execution
- **Streaming Support**: Handles streaming responses with proper UI coordination
- **Error Recovery**: Includes JSON fallback parsing for tool calls

Key functions:
- `create_agent()`: Initializes pydantic-ai agent with tools
- `process_request()`: Main entry point for processing user requests
- `execute_tools_parallel()`: Concurrent execution of read-only tools
- `patch_tool_messages()`: Error recovery for incomplete tool executions

### 3. Tool System (`tools/`)

Base tool architecture:

```python
class BaseTool(ABC):
    async def execute(self, *args, **kwargs) -> ToolResult:
        # Common error handling and logging
        # Calls tool-specific _execute()

    @abstractmethod
    async def _execute(self, *args, **kwargs) -> ToolResult:
        # Tool-specific implementation
```

Built-in tools:
- **read_file**: Read file contents with line numbers
- **write_file**: Create new files (fails if exists)
- **update_file**: Modify existing files with target/patch pattern
- **bash/run_command**: Execute shell commands
- **grep**: Fast regex searching with ripgrep
- **list_dir**: Directory listing without shell
- **glob**: File pattern matching
- **todo**: Task management within session

### 4. Command System (`cli/commands/`)

Extensible command registry pattern:

```python
class CommandRegistry:
    def register(self, command: Command) -> None
    def discover_commands(self) -> None
    def execute(self, command_text: str, context: CommandContext) -> Any
```

Command categories:
- **System**: `/help`, `/clear`, `/exit`, `/update`
- **Configuration**: `/model`, `/refresh-config`
- **Development**: `/branch`, `/init`, `/template`
- **Debug**: `/dump`, `/thoughts`, `/iterations`, `/fix`
- **State**: `/yolo`, `/compact`, `/streaming`
- **Todo**: `/todo` (list, add, update, remove)

### 5. UI Components (`ui/`)

Rich terminal interface components:
- **Console**: Central output handling with color theming
- **Input Manager**: Multiline input with syntax highlighting
- **Tool UI**: Confirmation dialogs with diff display
- **Panels**: Formatted output for errors, models, help
- **Keybindings**: Vi-mode support, ESC handling

## Module Documentation

### CLI Layer (`cli/`)

- **main.py**: Entry point, argument parsing, async coordination
- **repl.py**: Interactive loop, command processing, tool handling
- **commands/**: Command implementations and registry

### Core Layer (`core/`)

- **agents/**: LLM agent implementation and utilities
- **background/**: Async task management
- **logging/**: Unified logging system
- **setup/**: Modular setup steps
- **state.py**: Centralized state management
- **tool_handler.py**: Tool execution coordination
- **token_usage/**: Usage tracking and cost calculation

### Services Layer (`services/`)

- **mcp.py**: Model Context Protocol server management

### Tools Layer (`tools/`)

- **base.py**: Abstract base class for all tools
- Individual tool implementations

### UI Layer (`ui/`)

- **console.py**: Output formatting and display
- **input.py**: User input handling
- **tool_ui.py**: Tool confirmation interfaces
- **panels.py**: Rich panel formatting

### Utils Layer (`utils/`)

- **token_counter.py**: Token estimation using tiktoken
- **diff_utils.py**: File diff generation
- **ripgrep.py**: Fast file search wrapper
- **retry.py**: Retry logic for operations
- **security.py**: Command execution safety

## API Reference

### Key Classes

#### StateManager
```python
class StateManager:
    def __init__(self)
    @property session(self) -> SessionState
    def add_todo(self, todo: TodoItem) -> None
    def update_todo(self, todo_id: str, status: str) -> None
    def push_recursive_context(self, context: dict[str, Any]) -> None
    def can_recurse_deeper(self) -> bool
```

#### BaseTool
```python
class BaseTool(ABC):
    async def execute(self, *args, **kwargs) -> ToolResult
    @property tool_name(self) -> ToolName
    @abstractmethod async def _execute(self, *args, **kwargs) -> ToolResult
```

#### CommandRegistry
```python
class CommandRegistry:
    def register(self, command: Command) -> None
    def discover_commands(self) -> None
    async def execute(self, command_text: str, context: CommandContext) -> Any
    def is_command(self, text: str) -> bool
```

### Key Functions

#### Agent Functions
```python
async def create_agent(state_manager: StateManager) -> Agent
async def process_request(prompt: str, state_manager: StateManager) -> AgentResponse
async def execute_tools_parallel(tool_calls: List, callback: ToolCallback) -> List[Any]
```

#### Setup Functions
```python
async def setup(force_setup: bool, state_manager: StateManager, cli_config: dict)
```

## Development Guide

### Project Structure
```
tunacode/
├── src/
│   └── tunacode/
│       ├── cli/              # CLI interface
│       ├── configuration/    # Settings and defaults
│       ├── core/            # Core functionality
│       ├── services/        # External services
│       ├── tools/          # Tool implementations
│       ├── ui/             # User interface
│       └── utils/          # Utilities
├── tests/                  # Test suite
├── scripts/               # Development scripts
└── pyproject.toml        # Project configuration
```

### Adding New Tools

1. Create tool class inheriting from `BaseTool`:
```python
from tunacode.tools.base import BaseTool

class MyTool(BaseTool):
    @property
    def tool_name(self) -> str:
        return "my_tool"

    async def _execute(self, param: str) -> str:
        # Implementation
        return f"Executed with {param}"
```

2. Register in agent creation
3. Add to READ_ONLY_TOOLS if applicable

### Adding New Commands

1. Create command class inheriting from `Command`:
```python
from tunacode.cli.commands.base import Command, CommandCategory

class MyCommand(Command):
    name = "mycommand"
    description = "My custom command"
    category = CommandCategory.CUSTOM

    async def execute(self, args: List[str], context: CommandContext):
        # Implementation
```

2. Register in `CommandRegistry.discover_commands()`

### Code Style

- Follow existing patterns in codebase
- Use type hints throughout
- Implement proper error handling
- Add docstrings to public methods
- Use async/await for I/O operations

## Configuration

### User Configuration (`~/.config/tunacode.json`)

```json
{
  "default_model": "provider:model-name",
  "env": {
    "ANTHROPIC_API_KEY": "...",
    "OPENAI_API_KEY": "..."
  },
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["server-package"]
    }
  }
}
```

### Environment Variables

- `TUNACODE_MAX_PARALLEL`: Max concurrent read-only tools (default: CPU count)
- Provider API keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.

### Model Configuration

Format: `provider:model-name`

Examples:
- `openai:gpt-4o`
- `anthropic:claude-3-opus`
- `google:gemini-pro`
- `openrouter:meta-llama/llama-2-70b-chat`

## Tools and Commands

### Tool Categories

**Read-Only Tools** (can execute in parallel):
- `read_file`: Read file contents
- `grep`: Search file contents
- `list_dir`: List directory contents
- `glob`: Find files by pattern

**Write Tools** (execute sequentially):
- `write_file`: Create new files
- `update_file`: Modify existing files

**Execute Tools** (execute sequentially):
- `bash`: Execute bash commands
- `run_command`: Execute shell commands

### Command Reference

**System Commands**:
- `/help` - Show available commands
- `/clear` - Clear conversation history
- `/exit` - Exit application

**Configuration**:
- `/model [provider:name]` - List or switch models
- `/refresh-config` - Reload configuration

**Development**:
- `/branch <name>` - Create Git branch
- `/template [name]` - Use code templates

**State Management**:
- `/yolo` - Toggle confirmation prompts
- `/compact` - Summarize conversation
- `/thoughts` - Toggle detailed agent thoughts

### Safety Features

1. **Confirmation Required**: All file modifications require explicit confirmation
2. **Git Integration**: Encourages branching before changes
3. **Operation Cancellation**: ESC key handling for aborting operations
4. **Yolo Mode**: Optional bypass for confirmations (use with caution)

## Performance Optimizations

1. **Parallel Execution**: Read-only tools execute concurrently
2. **Token Management**: Efficient token counting with tiktoken
3. **Streaming Responses**: Real-time output display
4. **Background Tasks**: Non-blocking operations
5. **Context Window Tracking**: Prevents exceeding model limits

## Error Handling

Custom exception hierarchy:
- `TunaCodeError`: Base exception
- `ConfigurationError`: Setup issues
- `ToolExecutionError`: Tool failures
- `AgentError`: LLM operation failures
- `FileOperationError`: File system issues
- `MCPError`: External tool failures

## Testing

Test categories:
- Unit tests: Individual component testing
- Integration tests: System interaction testing
- Characterization tests: Behavior preservation
- Async tests: Async operation testing

Run tests:
```bash
pytest tests/                    # All tests
pytest -m "not slow"            # Skip slow tests
pytest --cov=tunacode           # With coverage
```

---

This documentation provides a comprehensive overview of the TunaCode CLI codebase, its architecture, and implementation details. For specific implementation examples or additional details about any component, refer to the source code files referenced throughout this document.
