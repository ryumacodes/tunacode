# UV + Hatch Setup Documentation - COMPLETED

## Overview
This project uses **Hatch** with **UV** as the package installer for fast, reliable dependency management. Successfully implemented and published v0.0.62.

## Final Working Configuration

### pyproject.toml Setup
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"  # Fixed: was setuptools

[tool.hatch.envs.default]
installer = "uv"  # Uses UV for 10-100x faster installs
features = ["dev"]  # Ensures dev dependencies are installed

[tool.hatch.build.targets.wheel]
packages = ["src/tunacode"]  # Required for hatchling

[project]
dependencies = [
    "defusedxml",  # Fixed: runtime dependency, not dev-only
    # ... other runtime deps
]

[project.optional-dependencies]
dev = [
    "build", "twine", "ruff", "pytest", "pre-commit",
    # ... dev-only deps (defusedxml moved to runtime)
]
```

## Key Fixes Applied

### 1. Build System
- **Fixed**: Changed from `setuptools` to `hatchling` build-backend
- **Added**: `[tool.hatch.build.targets.wheel]` configuration

### 2. Dependencies
- **Fixed**: Moved `defusedxml` from dev to runtime dependencies (used in bash tool)
- **Root cause**: Dependency not installed in hatch environment despite being in pyproject.toml

### 3. Publishing Script
- **Fixed**: Removed problematic `uv sync --dev` command
- **Uses**: Pure Hatch workflow with UV as installer

### 4. Install Script Enhancement
- **Fixed**: Detection logic now distinguishes wrapper scripts from actual binaries
- **Handles**: venv+wrapper, user site-packages, and system installations correctly
- **Added**: Automatic creation of `~/.config/tunacode.json` with sensible defaults
- **Enhanced**: Comprehensive post-install guidance with next steps
- **Updated**: Default model changed to `openrouter:openai/gpt-4.1` for better accessibility

## Final Result
- ✅ Published tunacode-cli v0.0.62 to PyPI
- ✅ All 298 tests passing
- ✅ Hatch + UV working complementarily
- ✅ Clean install/update process for users
- ✅ Auto-created config file with OpenRouter defaults
- ✅ Enhanced user onboarding with clear next steps

## Recent Improvements (Latest Updates)

### Enhanced Installation Experience
- **Config File Creation**: Install script now automatically creates `~/.config/tunacode.json` with sensible defaults
- **OpenRouter Default**: Changed default model to `openrouter:openai/gpt-4.1` for broader model access
- **User Guidance**: Post-install messages provide clear next steps:
  1. API key configuration options
  2. Reference to `tunacode --setup` wizard
  3. Getting started commands

### Example Fresh Installation Flow
```bash
# Install creates config automatically
./scripts/install_linux.sh

# Results in:
# ✅ ~/.config/tunacode.json created with OpenRouter defaults
# ✅ Clear guidance about API key setup
# ✅ References to setup wizard and documentation
```

### Configuration Auto-Creation
The install script now creates initial config with:
- Default model: `"openrouter:openai/gpt-4.1"`
- Empty API key placeholders for all providers
- Sensible defaults for all settings
- Proper JSON structure ready for user customization

## Usage

```bash
# Development workflow
hatch run test          # Run tests
hatch run lint-check    # Run linting
hatch build            # Build package
./scripts/publish_to_pip.sh  # Publish to PyPI

# User installation (automatic UV detection + config creation)
./scripts/install_linux.sh   # Creates venv + wrapper + config for global use
```
