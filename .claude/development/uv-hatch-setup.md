# UV + Hatch Setup Documentation

## Overview
This project uses **Hatch** with **UV** as the package installer for fast, reliable dependency management.

## Current Configuration

### pyproject.toml Setup
```toml
[tool.hatch.envs.default]
installer = "uv"  # CRITICAL: This tells hatch to use UV instead of pip
features = ["dev"]  # CRITICAL: This ensures dev dependencies are installed

[project.optional-dependencies]
dev = [
    "build",
    "twine",
    "ruff",
    "pytest",
    "pre-commit",
    "defusedxml",  # Required for XML parsing in tools
    "mypy",
    "bandit",
    # ... other dev dependencies
]
```

## Installation & Setup

### Prerequisites
1. Install UV (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install Hatch as a UV tool:
   ```bash
   uv tool install hatch
   ```

### Environment Management
```bash
# Create environment (uses UV automatically)
hatch env create

# Remove and recreate (when changing installer or dependencies)
hatch env remove default
hatch env create

# Show environments
hatch env show
```

## Common Commands

```bash
# Run tests
hatch run test

# Run linting
hatch run lint-check

# Build package
hatch build

# Run any command in hatch environment
hatch run <command>
```

## Pre-commit Hooks Configuration

The `.git/hooks/pre-commit` file must be modified to use hatch:
```bash
# Changed from: command -v pre-commit
# To: command -v hatch
elif command -v hatch > /dev/null; then
    exec hatch run pre-commit "${ARGS[@]}"
```

## Publishing Script Updates

The `scripts/publish_to_pip.sh` must use hatch commands:
```bash
# Linting
hatch run lint-check

# Testing
hatch run test

# Building
hatch build

# Uploading
hatch run python -m twine upload -r pypi dist/*
```

## CRITICAL MISTAKES TO AVOID

### Mistake 1: Mixing Package Managers
**WRONG:**
```bash
uv pip install <package>  # DON'T do this
uv sync --dev            # DON'T mix with hatch
```

**RIGHT:**
```bash
# Add to pyproject.toml dev dependencies, then:
hatch env remove default && hatch env create
```

### Mistake 2: Not Setting features = ["dev"]
**WRONG:**
```toml
[tool.hatch.envs.default]
installer = "uv"
# Missing features = ["dev"]
```

**RIGHT:**
```toml
[tool.hatch.envs.default]
installer = "uv"
features = ["dev"]  # REQUIRED for dev dependencies
```

### Mistake 3: Using venv/bin paths
**WRONG:**
```yaml
# In .pre-commit-config.yaml
entry: venv/bin/hatch run lint
entry: .venv/bin/pytest
```

**RIGHT:**
```yaml
entry: hatch run lint
entry: hatch run pytest
```

### Mistake 4: Not Recreating Environment After Config Changes
**WRONG:**
```bash
# After changing installer from pip to uv
hatch run test  # Will still use pip!
```

**RIGHT:**
```bash
# After changing installer or features
hatch env remove default
hatch env create
hatch run test  # Now uses UV
```

### Mistake 5: Installing Tools in Wrong Scope
**WRONG:**
```bash
pip install hatch  # System pip
uv pip install pre-commit  # Mixed environment
```

**RIGHT:**
```bash
uv tool install hatch  # Hatch as UV tool (global)
# pre-commit goes in pyproject.toml dev dependencies
```

### Mistake 6: Duplicate Keys in pyproject.toml
**WRONG:**
```toml
[tool.hatch.envs.default.scripts]
test = "pytest tests/"
# ... later in file
test = "python -m pytest"  # DUPLICATE!
```

**RIGHT:**
```toml
[tool.hatch.envs.default.scripts]
test = "pytest -q tests/characterization tests/test_security.py ..."
# Only ONE test key
```

## Best Practices

1. **Always use hatch commands** - Never directly call UV when using hatch
2. **Commit pyproject.toml changes first** - Before recreating environments
3. **Use hatch build** - Not `python -m build` or `uv run build`
4. **Keep dependencies in pyproject.toml** - Never use `pip install` or `uv pip install`
5. **Recreate environment after config changes** - Especially when changing installer

## Troubleshooting

### Issue: Module not found errors
**Solution:**
```bash
hatch env remove default
hatch env create
```

### Issue: Pre-commit hooks failing with "command not found"
**Solution:** Edit `.git/hooks/pre-commit` to use `hatch run pre-commit`

### Issue: Tests pass with hatch but fail in pre-commit
**Solution:** Ensure pre-commit uses hatch: `entry: hatch run pytest`

### Issue: Build fails with "No module named build"
**Solution:** Use `hatch build`, not `uv run python -m build`

## Migration Timeline & Lessons Learned

1. **Initial Confusion**: Tried using `uv sync` directly, creating `.venv`
   - **Lesson**: UV can be used standalone OR with hatch, not both simultaneously

2. **Mixed Environments**: Had venv, .venv, and hatch environments
   - **Lesson**: Clean ALL environments before starting fresh

3. **Missing Dependencies**: defusedxml wasn't in dev dependencies
   - **Lesson**: Check imports and add ALL required packages to pyproject.toml

4. **Pre-commit Hook Issues**: Hook couldn't find pre-commit command
   - **Lesson**: Git hooks need manual updating to use hatch

5. **Build Script Failures**: Used `uv run python -m build` instead of `hatch build`
   - **Lesson**: Use hatch's built-in commands, not UV directly

## Summary

The UV + Hatch combination provides:
- **Speed**: UV's fast package resolution and installation
- **Reliability**: Hatch's robust project management
- **Simplicity**: Single source of truth in pyproject.toml

Remember: Hatch manages the project, UV just makes it faster!
