# TunaCode

<div align="center">

[![PyPI version](https://badge.fury.io/py/tunacode-cli.svg)](https://badge.fury.io/py/tunacode-cli)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Your agentic CLI developer**

_An open-source alternative to Claude Code, Copilot, Windsurf, and Cursor_

[Quick Start](#quick-start) • [Features](#features) • [Configuration](#configuration) • [Documentation](#documentation)

</div>

---

## Overview

TunaCode is a powerful agentic CLI-based AI development tool that gives you the flexibility to use any LLM provider while maintaining an intelligent, autonomous workflow. No vendor lock-in, maximum flexibility.

> **Beta Notice**: TunaCode is currently in beta. [Report issues](https://github.com/larock22/tunacode/issues) or share feedback to help us improve!

---

## Features

<table>
<tr>
<td width="50%">

### **Multi-Provider Support**

- Anthropic Claude
- OpenAI GPT
- Google Gemini
- OpenRouter
- No vendor lock-in

### **Developer Tools**

- MCP (Model Context Protocol) support
- `/undo` command when AI breaks things
- JIT system prompt injection
- Per-project customization guides

</td>
<td width="50%">

### **User Experience**

- CLI-first design
- Switch models mid-session
- Cost and token tracking
- Skip confirmations per command/session
- Git integration

### **Coming Soon**

- TinyAgent framework integration
- Advanced workflow patterns
- Enhanced UI and error handling

</td>
</tr>
</table>

---

## Quick Start

### Installation

```bash
pip install tunacode-cli
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
| `/undo`                          | Undo recent changes              |
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
- Git (for undo functionality)

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
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black?logo=github)](https://github.com/larock22/tunacode)
[![Issues](https://img.shields.io/badge/GitHub-Issues-red?logo=github)](https://github.com/larock22/tunacode/issues)

</div>

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Built on the foundation of [sidekick-cli](https://github.com/geekforbrains/sidekick-cli).
Thank you to the sidekick-cli team for making TunaCode Possible
