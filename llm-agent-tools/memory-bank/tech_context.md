# Technical Context

## Technologies Used
- Language: Python 3.9+
- AI Framework: pydantic-ai
- CLI Framework: prompt_toolkit (REPL), rich (formatting)
- Testing: pytest, pytest-asyncio, pytest-cov
- Package Management: pyproject.toml with setuptools

## Architecture Decisions
- **Agent System**: Central agent in `src/tunacode/core/agents/main.py` with retryable tools
- **Tool System**: Seven internal tools extending BaseTool/FileBasedTool base classes
- **State Management**: Single StateManager maintaining all session state
- **Command Pattern**: Registry-based command system with decorator registration
- **Async Architecture**: All agent operations are async with prompt_toolkit integration
- **Memory Workflow**: Dual-memory system (Memory Bank + Scratchpad) for context persistence

## Key Components
1. **Tools**: read_file, write_file, update_file, run_command, bash, grep, list_dir
2. **Commands**: /help, /model, /clear, /compact, /branch, /yolo, /update, /exit
3. **Setup Steps**: Environment → Model → Config → Git Safety
4. **Performance**: Fast-glob grep with 3-second deadline, background task management

## Development Setup
```bash
# Recommended approach
./scripts/setup_dev_env.sh    # Creates fresh venv, installs deps, verifies setup

# Manual installation
pip install -e ".[dev]"      # Install in editable mode with dev dependencies
pip install pytest-asyncio   # Additional test dependency

# Run tests
make test                    # Run all tests via Makefile
pytest -m "not slow"         # Skip slow tests during development

# Linting
make lint                    # black, isort, flake8
```
