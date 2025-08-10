# Hatch Build System

## Overview

TunaCode uses [Hatch](https://hatch.pypa.io/) as its build system and development environment manager. Hatch provides cross-platform compatibility, standardized Python tooling, and simplified dependency management.

## Installation

```bash
pip install hatch
```

## Common Commands

### Development

```bash
# Install development dependencies
hatch run install

# Run the application
hatch run run

# Start development mode
hatch run dev
```

### Testing

```bash
# Run test suite
hatch run test

# Run tests with coverage
hatch run coverage

# Test specific Python version
hatch run py310:test
hatch run py311:test
hatch run py312:test
```

### Code Quality

```bash
# Lint and format code
hatch run lint

# Check without modifying
hatch run lint-check

# Type checking
hatch run typecheck

# Security analysis
hatch run security

# Dead code analysis
hatch run vulture
hatch run dead-code-check
hatch run dead-code-clean
hatch run dead-code-report
```

### Building & Publishing

```bash
# Build distribution packages
hatch build

# Clean build artifacts
hatch run clean

# Publish to PyPI
hatch publish
```

## Environment Management

Hatch manages isolated environments for different purposes:

- **default**: Main development environment
- **test**: Testing with pytest and coverage tools
- **lint**: Linting and formatting tools
- **py310/py311/py312**: Python version-specific environments

### Using Environments

```bash
# Run command in specific environment
hatch run test:pytest tests/

# Enter environment shell
hatch shell test
```

## Configuration

All Hatch configuration is in `pyproject.toml`:

```toml
[tool.hatch.envs.default.scripts]
# Script definitions

[tool.hatch.envs.test]
# Test environment configuration

[tool.hatch.build.targets.wheel]
# Build configuration
```

## Migration from Makefile

| Old Command | New Command |
|------------|-------------|
| `make install` | `hatch run install` |
| `make test` | `hatch run test` |
| `make lint` | `hatch run lint` |
| `make build` | `hatch build` |
| `make clean` | `hatch run clean` |
| `make coverage` | `hatch run coverage` |
| `make vulture` | `hatch run vulture` |

## Troubleshooting

### Command not found

Ensure hatch is installed:
```bash
pip install --upgrade hatch
```

### Environment issues

Reset environments:
```bash
hatch env prune
```

### Build errors

Clean and rebuild:
```bash
hatch run clean
hatch build
```

## Advanced Usage

### Matrix Testing

Test across multiple Python versions:
```bash
hatch run test:all
```

### Custom Scripts

Add custom scripts to `pyproject.toml`:
```toml
[tool.hatch.envs.default.scripts]
my-command = "python scripts/my_script.py"
```

### Environment Variables

Set environment variables:
```toml
[tool.hatch.envs.default.env-vars]
MY_VAR = "value"
```

## Benefits

1. **Cross-platform**: Works on Windows, macOS, and Linux
2. **No external dependencies**: No need for make or other build tools
3. **Python-native**: Integrates seamlessly with Python ecosystem
4. **Environment isolation**: Separate environments for different tasks
5. **Standardized**: Follows Python packaging standards (PEP 517/518)
