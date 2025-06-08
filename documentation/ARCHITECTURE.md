# Architecture

This document describes the internal architecture and design of TunaCode.

## Directory Structure

```
src/tunacode/
├── cli/                    # Command Line Interface
│   ├── commands.py        # Command registry and implementations
│   ├── main.py           # Entry point and CLI setup (Typer)
│   └── repl.py           # Interactive REPL loop
│
├── configuration/         # Configuration Management
│   ├── defaults.py       # Default configuration values
│   ├── models.py         # Configuration data models
│   └── settings.py       # Settings loader and validator
│
├── core/                 # Core Application Logic
│   ├── agents/           # AI Agent System
│   │   ├── main.py       # Primary agent implementation (pydantic-ai)
│   │   ├── orchestrator.py # Complex task orchestration and planning
│   │   ├── planner_schema.py # Planning data models
│   │   └── readonly.py   # Read-only agent for safe exploration
│   ├── background/       # Background Task Management
│   │   └── manager.py    # Async background task execution
│   ├── llm/              # LLM Integration
│   │   └── planner.py    # LLM-based task planning
│   ├── setup/            # Application Setup & Initialization
│   │   ├── agent_setup.py     # Agent configuration
│   │   ├── base.py           # Setup step base class
│   │   ├── config_setup.py   # Configuration setup
│   │   ├── coordinator.py    # Setup orchestration
│   │   ├── environment_setup.py  # Environment validation
│   │   └── git_safety_setup.py   # Git safety checks
│   ├── state.py          # Application state management
│   └── tool_handler.py   # Tool execution and validation
│
├── services/             # External Services
│   └── mcp.py           # Model Context Protocol integration
│
├── tools/               # AI Agent Tools
│   ├── base.py         # Tool base classes
│   ├── bash.py         # Enhanced shell command execution
│   ├── grep.py         # Parallel content search tool
│   ├── read_file.py    # File reading tool
│   ├── run_command.py  # Basic command execution tool
│   ├── update_file.py  # File modification tool
│   └── write_file.py   # File creation tool
│
├── ui/                 # User Interface Components
│   ├── completers.py   # Tab completion
│   ├── console.py      # Rich console setup
│   ├── input.py        # Input handling
│   ├── keybindings.py  # Keyboard shortcuts
│   ├── lexers.py       # Syntax highlighting
│   ├── output.py       # Output formatting and banner
│   ├── panels.py       # UI panels and layouts
│   ├── prompt_manager.py # Prompt toolkit integration
│   ├── tool_ui.py      # Tool confirmation dialogs
│   └── validators.py   # Input validation
│
├── utils/              # Utility Functions
│   ├── bm25.py        # BM25 search algorithm (beta)
│   ├── diff_utils.py  # Diff generation and formatting
│   ├── file_utils.py  # File system operations
│   ├── ripgrep.py     # Code search utilities
│   ├── system.py      # System information
│   ├── text_utils.py  # Text processing
│   └── user_configuration.py # User config management
│
├── constants.py        # Application constants
├── context.py         # Context management
├── exceptions.py      # Custom exceptions
├── types.py           # Type definitions
└── prompts/
    └── system.md      # System prompts for AI agent
```

## Key Components

| Component            | Purpose                  | Key Files                       |
| -------------------- | ------------------------ | ------------------------------- |
| **CLI Layer**        | Command parsing and REPL | `cli/main.py`, `cli/repl.py`    |
| **Agent System**     | AI-powered assistance    | `core/agents/main.py`           |
| **Orchestrator**     | Complex task planning    | `core/agents/orchestrator.py`   |
| **Background Tasks** | Async task execution     | `core/background/manager.py`    |
| **Tool System**      | File/command operations  | `tools/*.py`                    |
| **State Management** | Session state tracking   | `core/state.py`                 |
| **UI Framework**     | Rich terminal interface  | `ui/output.py`, `ui/console.py` |
| **Configuration**    | User settings & models   | `configuration/*.py`            |
| **Setup System**     | Initial configuration    | `core/setup/*.py`               |

## Data Flow

```
CLI Input → Command Registry → REPL → Agent → Tools → UI Output
     ↓              ↓           ↓       ↓       ↓        ↑
State Manager ←────────────────────────────────────────┘
```

## Architectural Decisions

### Agent System
- Uses `pydantic-ai` for LLM agent implementation
- Central agent in `src/tunacode/core/agents/main.py` with retryable tools
- Supports multiple LLM providers (Anthropic, OpenAI, Google, OpenRouter) through unified interface
- Model format: `provider:model-name` (e.g., `openai:gpt-4`, `anthropic:claude-3-opus`)

### Tool System
Four internal tools with confirmation UI:
1. `read_file` - Read file contents
2. `write_file` - Create new files (fails if exists)
3. `update_file` - Update existing files with target/patch pattern
4. `run_command` - Execute shell commands

Tools extend `BaseTool` or `FileBasedTool` base classes. External tools supported via MCP (Model Context Protocol).

### State Management
- `StateManager` (core/state.py) maintains all session state
- Includes user config, agent instances, message history, costs, permissions
- Single source of truth passed throughout the application

### Command System
- Command registry pattern in `cli/commands.py`
- Commands implement `BaseCommand` with `matches()` and `execute()` methods
- Registered via `@CommandRegistry.register` decorator
- Process flow: REPL → CommandRegistry → Command → Action

### Setup Coordinator
Modular setup with validation steps:
1. Environment detection
2. Model validation
3. Configuration setup
4. Git safety checks

Each step implements `BaseSetupStep` interface.

### UI Components
- REPL uses `prompt_toolkit` for multiline input with syntax highlighting
- Output formatting via `rich` library
- Tool confirmations show diffs for file operations
- Spinner during agent processing

## Key Design Patterns

### Error Handling
- Custom exceptions in `exceptions.py`
- `ModelRetry` from pydantic-ai for retryable errors
- Graceful degradation for missing features

### Permissions
- File operation permissions tracked per session
- "Yolo mode" to skip confirmations: `/yolo`
- Permissions stored in StateManager

### Async Architecture
- All agent operations are async
- Tool executions use async/await
- REPL handles async with prompt_toolkit integration

### Safety Design
- No automatic git commits (removed for safety)
- File operations require explicit confirmation
- Encourages git branches for experiments: `/branch <name>`

## Technical Stack

- **Python 3.10+**: Core language
- **pydantic-ai**: AI agent framework
- **Typer**: CLI framework
- **prompt_toolkit**: Interactive REPL
- **Rich**: Terminal formatting
- **asyncio**: Async operations

## Extension Points

1. **Custom Tools**: Add new tools by extending `BaseTool`
2. **New Commands**: Register commands with `@CommandRegistry.register`
3. **LLM Providers**: Add providers by implementing pydantic-ai model interface
4. **MCP Servers**: Configure external tools via MCP protocol