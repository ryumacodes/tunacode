<!-- This is the master documentation file containing the complete directory map with detailed comments on every file in the codebase -->

# TunaCode Comprehensive Documentation

> **Version**: 0.0.51
> **Last Updated**: 2025-08-03
> **Python Support**: 3.10 - 3.13

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Complete Directory Map](#complete-directory-map)
4. [Core Components](#core-components)
5. [Design Patterns](#design-patterns)
6. [Module Documentation](#module-documentation)
7. [Dead Code Analysis](#dead-code-analysis)
8. [Development Guidelines](#development-guidelines)

## Overview

TunaCode is a sophisticated AI-powered development assistant that provides an interactive CLI for coding tasks. Built on modern Python async architecture, it integrates with multiple LLM providers through pydantic-ai and offers powerful tool orchestration with parallel execution capabilities.

### Key Features

- **Multi-LLM Support**: Anthropic, OpenAI, Google, OpenRouter integration
- **Parallel Tool Execution**: 3x performance improvement for read-only operations
- **Rich Terminal UI**: Modern interface with syntax highlighting and auto-completion
- **Extensible Architecture**: Template system and MCP (Model Context Protocol) support
- **Security-First Design**: Permission system with confirmation workflows
- **Smart Context Management**: Automatic TUNACODE.md loading for project-specific guidance

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ REPL (CLI)   │  │ Rich Console │  │ Prompt Toolkit     │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        Command System Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │   Registry   │  │   Commands   │  │    Templates       │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                         Core Logic Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ StateManager │  │ Agent System │  │  Tool Handler      │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                          Tools Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │Internal Tools│  │ MCP Servers  │  │ Parallel Executor  │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                      Infrastructure Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │   Logging    │  │Configuration │  │   Utilities        │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → REPL → Command Registry → Command/Agent Execution
2. **Agent Request** → Tool Batching → Parallel/Sequential Execution → Response
3. **Tool Execution** → Permission Check → Confirmation UI → Execution → Result
4. **State Updates** → StateManager → Component Synchronization → UI Update

## Complete Directory Map

### Root Structure
```
/home/tuna/tunacode/src/
├── __init__.py                              # Empty package marker for src directory
├── README.md                                # [DEAD CODE] Test README file - should be removed
├── components/                              # [DEAD CODE] Misplaced React component directory
│   └── Button.tsx                           # [DEAD CODE] React button component - wrong project
│
└── tunacode/                                # Main package directory
```

### Core Package Structure

#### Package Root Files
```
tunacode/
├── __init__.py                              # Package initialization
├── py.typed                                 # PEP 561 marker for type checking support
├── constants.py                             # Global constants (VERSION = "0.0.51", etc.)
├── context.py                               # Context management for TUNACODE.md loading
├── exceptions.py                            # Exception hierarchy
├── setup.py                                 # Legacy setup file (redundant with pyproject.toml)
└── types.py                                 # Type definitions and protocols
```

#### CLI Layer (`cli/`)
```
cli/
├── __init__.py                              # CLI package initialization
├── main.py                                  # Main entry point - Typer app coordination
│                                           # - Handles CLI arguments and options
│                                           # - Coordinates setup process
│                                           # - Launches REPL after initialization
├── repl.py                                  # REPL implementation
│                                           # - prompt_toolkit integration
│                                           # - Multiline input handling
│                                           # - Command/agent request routing
└── commands/                                # Command system
    ├── __init__.py                          # Command package initialization
    ├── base.py                              # Abstract base classes
    │                                       # - Command ABC with metadata
    │                                       # - CommandCategory enum
    │                                       # - SimpleCommand base class
    ├── registry.py                          # Command registry with auto-discovery
    │                                       # - Factory pattern implementation
    │                                       # - Partial matching support
    │                                       # - Template shortcut integration
    ├── template_shortcut.py                 # [INCOMPLETE] Template shortcuts
    └── implementations/                     # Concrete command implementations
        ├── __init__.py
        ├── conversation.py                  # /compact - Conversation summarization
        ├── debug.py                         # Debug commands:
        │                                   # - /dump - Message history
        │                                   # - /yolo - Skip confirmations
        │                                   # - /thoughts - Agent visibility
        │                                   # - /iterations - ReAct limits
        │                                   # - /fix - Tool call recovery
        ├── development.py                   # Development commands:
        │                                   # - /branch - Git branching
        │                                   # - /init - TUNACODE.md creation
        ├── model.py                         # /model - Model switching
        ├── system.py                        # System commands:
        │                                   # - /help - Dynamic help
        │                                   # - /clear - Screen clearing
        │                                   # - /refresh-config - Config reload
        │                                   # - /update - Auto-update
        │                                   # - /streaming - Toggle streaming
        ├── template.py                      # Template management:
        │                                   # - /template list|load|create
        └── todo.py                          # Todo list management:
                                           # - /todo list|add|done|update
```

#### Configuration Layer (`configuration/`)
```
configuration/
├── __init__.py                              # Configuration package initialization
├── defaults.py                              # Default configuration values
│                                           # - Tool ignore patterns
│                                           # - Environment templates
│                                           # - Behavior defaults
├── models.py                                # Model registry with pricing
│                                           # - Provider configurations
│                                           # - Model pricing data
│                                           # - Cost calculation support
└── settings.py                              # Application settings
                                           # - PathConfig for file locations
                                           # - Tool categorization
                                           # - Version management
```

#### Core Business Logic (`core/`)
```
core/
├── __init__.py                              # Core package initialization
├── state.py                                 # StateManager - central state coordination
│                                           # - SessionState dataclass
│                                           # - Message history management
│                                           # - Token usage tracking
│                                           # - Recursive execution context
├── tool_handler.py                          # Tool execution orchestration
│                                           # - Permission management
│                                           # - Template integration
│                                           # - Confirmation workflows
├── code_index.py                            # [UNUSED] Code indexing system
│                                           # - File indexing
│                                           # - Symbol extraction
│                                           # - BM25 search integration
│
├── agents/                                  # AI agent implementation
│   ├── __init__.py
│   ├── main.py                              # Main agent with pydantic-ai
│   │                                       # - Tool integration
│   │                                       # - Parallel execution
│   │                                       # - Iteration management
│   │                                       # - Task completion detection
│   └── utils.py                             # Agent utilities
│                                           # - Tool batching
│                                           # - JSON parsing fallbacks
│                                           # - Message patching
│
├── background/                              # Background task management
│   ├── __init__.py
│   └── manager.py                           # BackgroundTaskManager
│                                           # - Async task lifecycle
│                                           # - Graceful shutdown
│                                           # - Task notifications
│
├── llm/                                     # [DEAD CODE] Empty directory
│   └── __init__.py                          # Should be removed
│
├── logging/                                 # Logging infrastructure
│   ├── __init__.py
│   ├── config.py                            # Logging configuration setup
│   ├── formatters.py                        # Custom log formatters
│   ├── handlers.py                          # File and console handlers
│   └── logger.py                            # Logger factory
│
├── setup/                                   # Application setup
│   ├── __init__.py
│   ├── base.py                              # BaseSetup interface
│   ├── coordinator.py                       # Setup orchestration
│   ├── agent_setup.py                       # Agent initialization
│   ├── config_setup.py                      # Config file creation
│   ├── environment_setup.py                 # API key validation
│   ├── git_safety_setup.py                  # Git repository checks
│   └── template_setup.py                    # Template directory setup
│
└── token_usage/                             # Token tracking
    ├── api_response_parser.py               # Parse API responses
    ├── cost_calculator.py                   # Calculate costs
    └── usage_tracker.py                     # Track usage
```

#### Prompts (`prompts/`)
```
prompts/
├── system.md                                # Main system prompt (731 lines)
│                                           # - Tool usage instructions
│                                           # - Performance optimizations
│                                           # - ReAct framework
└── system.md.bak                            # [DEAD CODE] Backup file
```

#### Services (`services/`)
```
services/
├── __init__.py                              # Services package initialization
└── mcp.py                                   # Model Context Protocol
                                           # - External tool integration
                                           # - Server lifecycle management
                                           # - Tool discovery
```

#### Templates (`templates/`)
```
templates/
├── __init__.py                              # Templates package initialization
└── loader.py                                # Template loading system
                                           # - Template dataclass
                                           # - TemplateLoader class
                                           # - Tool pre-approval
```

#### Tools (`tools/`)
```
tools/
├── __init__.py                              # Tools package initialization
├── base.py                                  # Base tool abstractions
│                                           # - BaseTool with common patterns
│                                           # - FileBasedTool for file ops
│                                           # - Error handling patterns
├── bash.py                                  # Enhanced bash execution
│                                           # - Security validation
│                                           # - Error capture
│                                           # - Async execution
├── glob.py                                  # File pattern matching
│                                           # - Fast glob implementation
│                                           # - Sorted by modification time
├── grep.py                                  # Content search tool
│                                           # - 3-second timeout protection
│                                           # - Fast-glob prefiltering
│                                           # - Async implementation
├── list_dir.py                              # Directory listing
│                                           # - Efficient file enumeration
│                                           # - Size and type info
├── read_file.py                             # File reading tool
│                                           # - Encoding detection
│                                           # - Line numbering
│                                           # - Parallel execution support
├── read_file_async_poc.py                   # [DEAD CODE] Async POC
├── run_command.py                           # Basic command execution
│                                           # - Shell command support
│                                           # - Error handling
├── todo.py                                  # Todo management tool
│                                           # - CRUD operations
│                                           # - Priority management
├── update_file.py                           # File patching tool
│                                           # - Target/patch pattern
│                                           # - Diff preview
│                                           # - Atomic updates
└── write_file.py                            # File creation tool
                                           # - Overwrite protection
                                           # - Encoding support
                                           # - Parent directory creation
```

#### UI Components (`ui/`)
```
ui/
├── __init__.py                              # UI package initialization
├── completers.py                            # Auto-completion system
│                                           # - CommandCompleter
│                                           # - FileReferenceCompleter
│                                           # - Merged completion support
├── console.py                               # Console coordination hub
│                                           # - Unified logging wrappers
│                                           # - Rich console instance
│                                           # - Import coordination
├── constants.py                             # UI constants and styles
├── decorators.py                            # Async/sync wrappers
│                                           # - Event loop management
│                                           # - Docstring preservation
├── input.py                                 # User input handling
│                                           # - Multiline support
│                                           # - Dynamic prompts
│                                           # - Tab completion
├── keybindings.py                           # Keyboard shortcuts
│                                           # - Enter/Ctrl+O handling
│                                           # - Double ESC cancellation
│                                           # - Task interruption
├── lexers.py                                # Syntax highlighting
│                                           # - FileReferenceLexer
│                                           # - Pattern matching
├── logging_compat.py                        # Logging compatibility
│                                           # - UnifiedUILogger
│                                           # - Success formatting
├── output.py                                # Output formatting
│                                           # - Banner display
│                                           # - Context window info
│                                           # - Spinner management
│                                           # - Update notifications
├── panels.py                                # Rich panel components
│                                           # - Streaming agent panel
│                                           # - Help panel
│                                           # - Models panel
├── prompt_manager.py                        # Prompt management
│                                           # - Session-based prompts
│                                           # - Style management
│                                           # - State persistence
├── tool_ui.py                               # Tool confirmation UI
│                                           # - Confirmation dialogs
│                                           # - Diff rendering
│                                           # - MCP tool logging
├── utils.py                                 # UI utilities
└── validators.py                            # Input validation
                                           # - ModelValidator
                                           # - Format checking
```

#### Utilities (`utils/`)
```
utils/
├── __init__.py                              # Utils package initialization
├── bm25.py                                  # [UNUSED] BM25 search algorithm
├── diff_utils.py                            # Diff generation utilities
│                                           # - Unified diff creation
│                                           # - Color highlighting
├── file_utils.py                            # File operations
│                                           # - Safe file reading
│                                           # - [UNUSED] DotDict class
│                                           # - [UNUSED] capture_stdout
├── import_cache.py                          # Import performance optimization
├── message_utils.py                         # Message processing
│                                           # - Format conversions
│                                           # - Content extraction
├── retry.py                                 # Retry logic
│                                           # - Exponential backoff
│                                           # - Custom exceptions
├── ripgrep.py                               # [UNUSED] Ripgrep wrapper
├── security.py                              # Security utilities
│                                           # - Command validation
│                                           # - Path sanitization
│                                           # - Git safety checks
├── system.py                                # System operations
│                                           # - Platform detection
│                                           # - Process management
├── text_utils.py                            # Text processing
│                                           # - Token estimation
│                                           # - Text truncation
├── token_counter.py                         # Token counting
│                                           # - tiktoken integration
│                                           # - Model-specific encoding
└── user_configuration.py                    # User config management
                                           # - JSON persistence
                                           # - Path resolution
                                           # - Default handling
```

#### Package Metadata (`tunacode_cli.egg-info/`)
```
tunacode_cli.egg-info/
├── PKG-INFO                                 # Package information
├── SOURCES.txt                              # List of source files
├── dependency_links.txt                     # External dependencies
├── entry_points.txt                         # Console scripts
├── requires.txt                             # Package requirements
└── top_level.txt                            # Top-level modules
```

## Core Components

### 1. StateManager (core/state.py)
Central coordination point for all application state:
- **SessionState**: Comprehensive dataclass holding all runtime state
- **Message History**: Conversation context with token tracking
- **Permission Tracking**: Tool approval state and YOLO mode
- **Streaming State**: Real-time UI update coordination
- **Recursive Context**: Task hierarchy and iteration budgets

### 2. Agent System (core/agents/)
Sophisticated AI integration with parallel execution:
- **Main Agent**: pydantic-ai based with comprehensive tool suite
- **Parallel Execution**: Read-only tools execute concurrently
- **Iteration Management**: Productive vs unproductive tracking
- **Task Completion**: TUNACODE_TASK_COMPLETE marker detection
- **Fallback Handling**: JSON parsing for malformed responses

### 3. Tool System (tools/)
Modular tool architecture with security focus:
- **Categories**: READ_ONLY_TOOLS, WRITE_TOOLS, EXECUTE_TOOLS
- **Base Classes**: Common patterns for error handling and UI
- **Parallel Support**: Automatic batching of read operations
- **Permission System**: Confirmation workflows with skip options
- **MCP Integration**: External tool support via services

### 4. Command Registry (cli/commands/)
Extensible command system with auto-discovery:
- **Factory Pattern**: Dependency injection for commands
- **Category Organization**: Logical grouping of commands
- **Partial Matching**: Fuzzy command resolution
- **Template Shortcuts**: Dynamic command creation
- **Help Integration**: Auto-generated documentation

### 5. UI System (ui/)
Modern terminal interface with rich features:
- **Rich Console**: Syntax highlighting and formatting
- **prompt_toolkit**: Advanced input handling
- **Streaming Panels**: Real-time agent output
- **Tool Confirmations**: Security-focused dialogs
- **Auto-completion**: Commands and file references

## Design Patterns

### 1. Factory Pattern
- Command creation with proper dependencies
- Agent instantiation with tool configuration
- Setup step coordination

### 2. Observer Pattern
- Async UI event handling
- Token usage monitoring
- Streaming updates

### 3. Strategy Pattern
- Tool execution strategies (parallel/sequential)
- Error recovery mechanisms
- Model provider interfaces

### 4. Builder Pattern
- Agent configuration assembly
- UI component construction
- Command specification

### 5. Facade Pattern
- Console operations unified interface
- State management abstraction
- Tool handler simplification

## Module Documentation

Detailed module documentation is available in the following files:

1. **[Core Architecture](docs/modules/core-architecture.md)** - Deep dive into core components
2. **[Tools System](docs/modules/tools-system.md)** - Complete tool implementation guide
3. **[UI System](docs/modules/ui-system.md)** - UI components and interactions
4. **[Command System](docs/modules/command-system.md)** - Command processing details
5. **[Configuration](docs/modules/configuration.md)** - Settings and model management
6. **[Utilities](docs/modules/utilities.md)** - All utility functions documented

## Dead Code Analysis

### Files to Remove
1. `/src/README.md` - Test file with no value
2. `/src/components/` - Entire React directory (wrong project)
3. `/src/tunacode/core/llm/` - Empty directory
4. `/src/tunacode/tools/read_file_async_poc.py` - Unused POC
5. `/src/tunacode/prompts/system.md.bak` - Backup file
6. `/src/tunacode/utils/ripgrep.py` - Replaced by grep.py
7. `/src/tunacode/utils/bm25.py` - Part of unused search system
8. `/src/tunacode/core/code_index.py` - Unused indexing system

### Functions to Remove
1. `utils/file_utils.py`:
   - `DotDict` class
   - `capture_stdout` function

### Issues to Fix
1. Circular dependency between StateManager and ToolHandler
2. Complete template shortcut implementation
3. Template creation UI (currently shows JSON instructions)

## Development Guidelines

### Adding New Tools
1. Extend `BaseTool` or `FileBasedTool`
2. Implement required methods (`run`, `format_confirmation`)
3. Add to `INTERNAL_TOOLS` in settings.py
4. Categorize in `READ_ONLY_TOOLS`, `WRITE_TOOLS`, or `EXECUTE_TOOLS`

### Adding New Commands
1. Create class extending `SimpleCommand` or implement `Command`
2. Add to appropriate category in `implementations/`
3. Registry will auto-discover via `@property` methods

### Performance Optimization
1. Use parallel execution for read-only operations
2. Implement proper async/await patterns
3. Cache expensive operations (imports, file reads)
4. Monitor token usage to prevent context overflow

### Security Considerations
1. Always validate commands in security.py
2. Require confirmations for destructive operations
3. Sanitize file paths and user input
4. Respect git repository boundaries

---

For more detailed information, see the module-specific documentation in the `docs/` directory.
