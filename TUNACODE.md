# TUNACODE.md

## Build Commands
- Run all tests: `make test`
- Run single test: `pytest tests/test_file.py::test_name`
- Run quick tests: `pytest -m "not slow"`
- Lint code: `make lint`
- Build package: `make build`
- Clean artifacts: `make clean`

## Code Style
- Use type hints for all function signatures
- Prefer guard clauses over nested conditionals
- Keep functions focused and under 50 lines
- Use descriptive variable names
- Follow PEP 8 conventions
- Maximum line length: 120 characters
- Use black for formatting
- Use isort for imports
- Use snake_case for variables and functions
- Use PascalCase for classes
- Prefer explicit error handling, avoid bare excepts

## Architecture Notes
- Agent creation loads this file and appends to system prompt
- Context is loaded synchronously to avoid event loop issues
- TUNACODE.md is walked up directory tree (closest first)