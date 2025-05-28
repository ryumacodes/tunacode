# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TunaCode is an agentic CLI-based AI development tool, providing an open-source alternative to Claude Code, Copilot, and Cursor. It supports multiple LLM providers (Anthropic, OpenAI, Google Gemini, OpenRouter) without vendor lock-in.

## Essential Commands

### Development
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run TunaCode locally
tunacode

# Development commands
make lint         # Run black, isort, flake8
make test         # Run pytest
make coverage     # Run tests with coverage report
make build        # Build distribution package
make clean        # Clean build artifacts
```

### Running Single Tests
```bash
pytest path/to/test_file.py::TestClass::test_method
pytest -v -s path/to/test_file.py  # Verbose with stdout
```

## Architecture

### Core Components

1. **StateManager** (`src/tunacode/core/state.py`) - Central state management handling:
   - Session state and message history
   - Agent instances and cost tracking
   - Configuration and environment setup

2. **Agent System** (`src/tunacode/core/agents/main.py`):
   - Uses `pydantic-ai` for agent creation
   - Implements tool-first approach for all operations
   - Message history management with compaction support

3. **Tool Framework** (`src/tunacode/tools/`):
   - Base classes provide consistent error handling and UI logging
   - Tools: `read_file`, `write_file`, `update_file`, `run_command`
   - All tools inherit from `BaseTool` or `FileBasedTool`

4. **Setup Coordinator** (`src/tunacode/core/setup/coordinator.py`):
   - Modular initialization system with registered setup steps
   - Handles environment, config, and undo setup

5. **UI Layer** (`src/tunacode/ui/`):
   - Terminal UI using `prompt_toolkit` and `rich`
   - Custom lexers, completers, and keybindings
   - Tool confirmation system with skip options

### Key Design Patterns

- **Tool-First Approach**: Agent prioritizes using tools for all file/command operations
- **Git-Based Undo**: Uses git for reverting changes via `/undo` command
- **Per-Project Guides**: `TUNACODE.md` files for project-specific instructions
- **MCP Support**: Model Context Protocol for extended capabilities
- **Cost Tracking**: Per-message and session-level token/cost tracking

## Code Style

- Line length: 100 characters (configured in black)
- Import sorting: isort with black compatibility
- Type hints encouraged throughout codebase
- Follow conventional commits for version history

## Testing Approach

- Tests use pytest (framework in development)
- Mock external services and file operations
- Test tools independently from agent logic
- Verify UI components separately from core logic

## Release Process

1. Update version in `pyproject.toml` and `src/tunacode/constants.py`
2. Follow conventional commits specification
3. Tag with `vX.Y.Z` format
4. Create GitHub release
5. PyPI release automated on main branch merge