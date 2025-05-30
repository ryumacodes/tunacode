# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Commands
```bash
# Install development environment
pip install -e ".[dev]"

# Run linting (black, isort, flake8)
make lint

# Run tests
make test
pytest tests/                 # Run all tests
pytest tests/test_import.py  # Run single test file
pytest -k "test_name"        # Run specific test

# Run tests with coverage
make coverage

# Build distribution packages
make build

# Clean build artifacts
make clean
```

### Version Management
When updating versions, modify both:
- `pyproject.toml`: version field
- `src/tunacode/constants.py`: VERSION constant

## Architecture

TunaCode is a CLI tool that provides an AI-powered coding assistant using pydantic-ai. Key architectural decisions:

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

## Configuration

### User Configuration
Location: `~/.config/tunacode.json`
```json
{
    "default_model": "provider:model-name",
    "env": {
        "ANTHROPIC_API_KEY": "...",
        "OPENAI_API_KEY": "..."
    }
}
```

### Project Guide
Location: `TUNACODE.md` in project root
- Project-specific context for the AI assistant
- Loaded automatically when present
- Can include codebase conventions, architecture notes

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

### Safety Notes
- No automatic git commits (removed for safety)
- File operations require explicit confirmation
- Encourages git branches for experiments: `/branch <name>`