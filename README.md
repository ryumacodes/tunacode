# TunaCode

<div align="center">

[![PyPI version](https://badge.fury.io/py/tunacode-cli.svg)](https://badge.fury.io/py/tunacode-cli)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Your AI-powered CLI coding assistant**

[Quick Start](#quick-start) • [Features](#features) • [Configuration](#configuration) • [Documentation](#documentation)

</div>

---

## Overview

> **⚠️ Safety First**: TunaCode can modify your codebase. Always use git branches before making major changes. The `/undo` command has been removed - use git for version control.

> **Beta Notice**: TunaCode is currently in beta. [Report issues](https://github.com/alchemiststudiosDOTai/tunacode/issues) or share feedback to help us improve!

---

### Recent Updates

- **Simplified Setup**: Direct CLI configuration with `--model` and `--key` flags
- **Enhanced Safety**: Removed `/undo` command in favor of git-based workflows
- **Cleaner Codebase**: Removed `/init` command and automatic TUNACODE.md generation
- **Better Onboarding**: No model validation - trust users to provide correct model names
- **Unified Model Format**: All models use `provider:model-name` format

### Core Features

<table>
<tr>
<td width="50%">

### **Multi-Provider Support**

- Anthropic Claude
- OpenAI GPT
- Google Gemini
- OpenRouter (100+ models)
- Any OpenAI-compatible API

### **Developer Tools**

- 4 core tools: read_file, write_file, update_file, run_command
- MCP (Model Context Protocol) support
- File operation confirmations with diffs
- Per-project context guides (TUNACODE.md)

</td>
<td width="50%">

### **Safety & Control**

- Git branch integration (`/branch`)
- No automatic commits
- Explicit file operation confirmations
- Permission tracking per session
- `/yolo` mode for power users

### **Architecture**

- Built on pydantic-ai
- Async throughout
- Modular command system
- Rich UI with syntax highlighting

</td>
</tr>
</table>

---

## Quick Start

### Installation

#### PyPI

```bash
pip install tunacode-cli
```

#### One-line Install (Linux/macOS)

```bash
wget -qO- https://raw.githubusercontent.com/alchemiststudiosDOTai/tunacode/master/scripts/install_linux.sh | bash
```

### Uninstallation

To completely remove TunaCode from your system:

```bash
# Download and run the uninstall script
wget -qO- https://raw.githubusercontent.com/alchemiststudiosDOTai/tunacode/master/scripts/uninstall.sh | bash

# Or manually:
# 1. Remove the package
pipx uninstall tunacode  # if installed via pipx
# OR
pip uninstall tunacode-cli  # if installed via pip

# 2. Remove configuration files
rm -rf ~/.config/tunacode*

# 3. Remove any leftover binaries
rm -f ~/.local/bin/tunacode
```

### Setup Options

<details>
<summary><b>Option 1: Interactive Setup (Beginner-friendly)</b></summary>

```bash
tunacode
```

Follow the interactive prompts to configure your preferred LLM provider.

</details>

<details>
<summary><b>Option 2: Direct CLI Setup (Recommended)</b></summary>

```bash
# OpenAI
tunacode --model "openai:gpt-4.1" --key "your-openai-key"

# Anthropic Claude
tunacode --model "anthropic:claude-3-opus" --key "your-anthropic-key"

# OpenRouter (Access to multiple models)
tunacode --baseurl "https://openrouter.ai/api/v1" \
         --model "openrouter:openai/gpt-4.1" \
         --key "your-openrouter-key"
```

</details>

> **Important**: Model names require provider prefixes (e.g., `openai:gpt-4.1`, not `gpt-4.1`)

---

## Configuration

### Config Location

Configuration is stored in `~/.config/tunacode.json`

### Model Format

```
provider:model-name
```

**Examples:**

- `openai:gpt-4.1`
- `anthropic:claude-3-opus`
- `google-gla:gemini-2.0-flash`
- `openrouter:mistralai/devstral-small`

### OpenRouter Integration

<details>
<summary><b>Click to expand OpenRouter setup</b></summary>

[OpenRouter](https://openrouter.ai) provides access to 100+ models through a single API:

```bash
tunacode --baseurl "https://openrouter.ai/api/v1" \
         --model "openrouter:openai/gpt-4.1" \
         --key "your-openrouter-key"
```

**Manual Configuration:**

```json
{
  "env": {
    "OPENROUTER_API_KEY": "<YOUR_KEY>",
    "OPENAI_BASE_URL": "https://openrouter.ai/api/v1"
  },
  "default_model": "openrouter:openai/gpt-4.1"
}
```

**Popular Models:**

- `openrouter:mistralai/devstral-small`
- `openrouter:openai/gpt-4.1-mini`
- `openrouter:codex-mini-latest`

</details>

### MCP (Model Context Protocol) Support

<details>
<summary><b>Click to expand MCP configuration</b></summary>

Extend your AI's capabilities with MCP servers:

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<YOUR_TOKEN>"
      }
    }
  }
}
```

Learn more at [modelcontextprotocol.io](https://modelcontextprotocol.io/)

</details>

---

## Commands Reference

| Command                          | Description                      |
| -------------------------------- | -------------------------------- |
| `/help`                          | Show available commands          |
| `/yolo`                          | Toggle confirmation skipping     |
| `/clear`                         | Clear message history            |
| `/compact`                       | Summarize and clear old messages |
| `/model`                         | Show current model               |
| `/model <provider:name>`         | Switch model                     |
| `/model <provider:name> default` | Set default model                |
| `/branch <name>`                 | Create and switch Git branch     |
| `/dump`                          | Show message history (debug)     |
| `exit`                           | Exit application                 |

---

## Customization

### Project Guides

Create a `TUNACODE.md` file your project root to customize TunaCode's behavior:

```markdown
# Project Guide

## Tech Stack

- Python 3.11
- FastAPI
- PostgreSQL

## Preferences

- Use type hints
- Follow PEP 8
- Write tests for new features
```

---

## Development

### Requirements

- Python 3.10+
- Git (for version control)

### Development Setup

```bash
# Install development dependencies
make install

# Run linting
make lint

# Run tests
make test
```

### Release Process

<details>
<summary><b>Click to expand release steps</b></summary>

1. **Update versions:**

   - `pyproject.toml`
   - `src/tunacode/constants.py` (APP_VERSION)

2. **Commit and tag:**

   ```bash
   git add pyproject.toml src/tunacode/constants.py
   git commit -m "chore: bump version to X.Y.Z"
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

3. **Create release:**
   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z" --notes "Release notes"
   ```

</details>

### Commit Convention

Following [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation
- `style:` Code formatting
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Maintenance

---

## Links

<div align="center">

[![PyPI](https://img.shields.io/badge/PyPI-Package-blue?logo=pypi)](https://pypi.org/project/tunacode-cli/)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black?logo=github)](https://github.com/alchemiststudiosDOTai/tunacode)
[![Issues](https://img.shields.io/badge/GitHub-Issues-red?logo=github)](https://github.com/alchemiststudiosDOTai/tunacode/issues)

</div>

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

TunaCode is a fork of [sidekick-cli](https://github.com/geekforbrains/sidekick-cli). Special thanks to the sidekick-cli team for creating the foundation that made TunaCode possible.
