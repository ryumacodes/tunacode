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
│   │   ├── agent_components/ # Agent internal components
│   │   │   ├── tool_executor.py # Parallel tool execution
│   │   │   ├── node_processor.py # Request processing
│   │   │   ├── tool_buffer.py   # Tool call buffering
│   │   │   └── ...          # Other agent components
│   │   └── utils.py      # Agent utilities
│   ├── background/       # Background Task Management
│   │   └── manager.py    # Async background task execution
│   ├── code_index.py     # Fast in-memory code indexing system
│   ├── llm/              # LLM Integration
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
│   ├── grep_components/ # Grep tool components
│   │   ├── file_filter.py    # File filtering and glob support
│   │   ├── pattern_matcher.py # Pattern matching strategies
│   │   ├── result_formatter.py # Result formatting
│   │   └── search_result.py   # Search result data structures
│   ├── glob.py         # Fast file pattern matching
│   ├── list_dir.py     # Efficient directory listing
│   ├── read_file.py    # File reading tool
│   ├── run_command.py  # Basic command execution tool
│   ├── todo.py         # Todo management tool
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
| **Parallel Execution** | Concurrent tool execution | `core/agents/agent_components/tool_executor.py` |
| **Background Tasks** | Async task execution     | `core/background/manager.py`    |
| **Code Indexing**    | Fast file discovery      | `core/code_index.py`            |
| **Tool System**      | File/command operations  | `tools/*.py`                    |
| **State Management** | Session state tracking   | `core/state.py`                 |
| **MCP Integration**  | External tool support    | `services/mcp.py`               |
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
Seven internal tools with confirmation UI:

1. `bash` - Enhanced shell command execution with safety features
2. `grep` - Fast parallel content search across files with 3-second deadline
3. `glob` - Fast file pattern matching using glob patterns
4. `list_dir` - Efficient directory listing without shell commands
5. `read_file` - Read file contents with line numbers
6. `update_file` - Update existing files with target/patch pattern
7. `write_file` - Create new files (fails if exists)

Tools extend `BaseTool` or `FileBasedTool` base classes. External tools supported via MCP (Model Context Protocol) through `services/mcp.py`.

### State Management
- `StateManager` (core/state.py) maintains all session state
- Includes user config, agent instances, message history, costs, permissions
- Single source of truth passed throughout the application
- Code indexing system in `core/code_index.py` for codebase understanding

### Memory Anchor System
- In-file memory anchors using `CLAUDE_ANCHOR[key]: description` format
- Persistent references across code changes for LLM optimization
- Stored in `.claude/anchors.json` with location mappings
- Enables semantic navigation and context preservation
- Supports quick navigation to critical implementation points

### Command System
- Command registry pattern in `cli/commands/registry.py`
- Commands implement `BaseCommand` with `matches()` and `execute()` methods
- Registered via `@CommandRegistry.register` decorator
- Shell command execution with `!` prefix (e.g., `!ls`)
- Available commands: `/help`, `/model`, `/clear`, `/compact`, `/branch`, `/yolo`, `/update`, `/exit`, `/thoughts`

### Parallel Tool Execution

- Read-only tools (read_file, grep, list_dir) execute in parallel for 3x performance improvement
- Write/execute tools remain sequential for safety
- Enhanced visual feedback when `/thoughts on` is enabled:
  - Clear batch headers: "🚀 PARALLEL BATCH #X: Executing Y read-only tools concurrently"
  - Detailed tool listing with arguments for each batch
  - Sequential warnings for write/execute tools: "⚠️ SEQUENTIAL: tool_name (write/execute tool)"
  - Completion confirmations: "✅ Parallel batch completed successfully"
- Controlled by `TUNACODE_MAX_PARALLEL` environment variable (defaults to CPU count)
- Automatic batching of consecutive read-only tools
- Read-only tools skip confirmation prompts automatically

### Setup Coordinator
Modular setup with validation steps:
1. Environment detection (API keys)
2. Model validation
3. Configuration setup (`~/.config/tunacode.json`)
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
- Background task management via `core/background/manager.py`

### Performance Optimizations

- Grep tool uses fast-glob prefiltering with MAX_GLOB limit
- 3-second deadline for first match in searches
- Background task management for non-blocking operations
- Code indexing system for efficient file lookups without timeout-prone grep searches
- Parallel tool execution for read-only operations

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
