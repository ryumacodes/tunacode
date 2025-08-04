<!-- This is the main documentation index that links to all documentation categories: modules, guides, and API references -->

# TunaCode Documentation

Welcome to the comprehensive TunaCode documentation. This documentation provides complete coverage of the codebase, architecture, APIs, and development guides.

## Documentation Structure

### 📚 Main Documentation
- [**TUNACODE_COMPREHENSIVE_DOCS.md**](../TUNACODE_COMPREHENSIVE_DOCS.md) - Master documentation with complete directory map and overview

### 🏗️ Module Documentation (`docs/modules/`)
Detailed documentation for each major system:

- [**Core Architecture**](modules/core-architecture.md) - StateManager, Agent system, Tool handler, Setup system
- [**Tools System**](modules/tools-system.md) - Tool architecture, implementations, parallel execution
- [**UI System**](modules/ui-system.md) - Console, input handling, panels, and user interaction
- [**Command System**](modules/command-system.md) - Command registry, implementations, and patterns
- [**Configuration**](modules/configuration.md) - Settings, models, user configuration management
- [**Utilities**](modules/utilities.md) - Helper functions for files, text, security, and more

### 👨‍💻 Developer Guides (`docs/guides/`)
Step-by-step guides for developers:

- [**Getting Started**](guides/getting-started.md) - Setup, development workflow, project structure
- [**Adding Tools**](guides/adding-tools.md) - Create new tools for the agent system
- [**Adding Commands**](guides/adding-commands.md) - Create new slash commands
- [**Template System**](guides/template-system.md) - Create and use prompt templates
- [**MCP Integration**](guides/mcp-integration.md) - Integrate external tools via MCP
- [**Performance Guide**](guides/performance-guide.md) - Optimization strategies and best practices

### 🔧 API Reference (`docs/api/`)
Complete API documentation:

- [**API Overview**](api/README.md) - Quick reference and overview
- [**Core API**](api/core-api.md) - StateManager, Agent, ToolHandler, Setup system
- [**Tools API**](api/tools-api.md) - BaseTool, tool implementations, creating tools
- [**UI API**](api/ui-api.md) - Console, panels, input, output components
- [**Commands API**](api/commands-api.md) - Command base classes, registry, implementations
- [**Configuration API**](api/configuration-api.md) - Settings, models, user configuration
- [**Utils API**](api/utils-api.md) - File, text, security, and system utilities

## Quick Links

### For New Developers
1. Start with [Getting Started](guides/getting-started.md)
2. Read the [Core Architecture](modules/core-architecture.md)
3. Explore the [API Overview](api/README.md)

### For Tool Development
1. Read [Tools System](modules/tools-system.md)
2. Follow [Adding Tools Guide](guides/adding-tools.md)
3. Reference [Tools API](api/tools-api.md)

### For Command Development
1. Read [Command System](modules/command-system.md)
2. Follow [Adding Commands Guide](guides/adding-commands.md)
3. Reference [Commands API](api/commands-api.md)

### For Performance
1. Read [Performance Guide](guides/performance-guide.md)
2. Understand [Parallel Tool Execution](modules/tools-system.md#parallel-execution-system)

## Key Concepts

### Architecture
- **Async-first**: Built on asyncio for responsive operation
- **Modular design**: Clear separation of concerns
- **Extensible**: Template system and MCP integration
- **Performance**: Parallel tool execution for 3x speedup

### Security
- **Tool permissions**: Confirmation system with YOLO override
- **Command validation**: Security checks for shell commands
- **Path sanitization**: Protection against traversal attacks

### User Experience
- **Rich UI**: Modern terminal interface with syntax highlighting
- **Auto-completion**: Commands and file paths
- **Streaming**: Real-time agent responses
- **Context management**: Token usage tracking

## Dead Code Identified

The following files/code should be removed as part of cleanup:

### Files to Remove
- `/src/README.md` - Test file
- `/src/components/` - Misplaced React directory
- `/src/tunacode/core/llm/` - Empty directory
- `/src/tunacode/tools/read_file_async_poc.py` - Unused POC
- `/src/tunacode/prompts/system.md.bak` - Backup file
- `/src/tunacode/utils/ripgrep.py` - Replaced by grep.py
- `/src/tunacode/utils/bm25.py` - Unused search
- `/src/tunacode/core/code_index.py` - Unused indexing

### Code to Remove
- `DotDict` class in `utils/file_utils.py`
- `capture_stdout` function in `utils/file_utils.py`

## Contributing

When contributing to TunaCode:

1. Follow the code style guidelines in CLAUDE.md
2. Add tests for new functionality
3. Update relevant documentation
4. Run linting and tests before submitting

## Version

This documentation is for TunaCode v0.0.51
