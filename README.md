# TunaCode

<div align="center">

[![PyPI version](https://badge.fury.io/py/tunacode-cli.svg)](https://badge.fury.io/py/tunacode-cli)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AI-powered CLI coding assistant**

![Demo](demo.gif)

</div>

---

## Quick Install

```bash
# Option 1: One-line install (Linux/macOS)
wget -qO- https://raw.githubusercontent.com/alchemiststudiosDOTai/tunacode/master/scripts/install_linux.sh | bash

# Option 2: pip install
pip install tunacode-cli
```

## Configuration

Choose your AI provider and set your API key:

```bash
# OpenAI
tunacode --model "openai:gpt-4o" --key "sk-your-openai-key"

# Anthropic Claude  
tunacode --model "anthropic:claude-3.5-sonnet" --key "sk-ant-your-anthropic-key"

# OpenRouter (100+ models)
tunacode --model "openrouter:openai/gpt-4o" --key "sk-or-your-openrouter-key"
```

Your config is saved to `~/.config/tunacode.json`

## Start Coding

```bash
tunacode
```

## Basic Commands

| Command | Description |
| ------- | ----------- |
| `/help` | Show all commands |
| `/model <provider:name>` | Switch model |
| `/clear` | Clear message history |
| `/compact` | Summarize conversation |
| `/branch <name>` | Create Git branch |
| `/yolo` | Skip confirmations |
| `!<command>` | Run shell command |
| `exit` | Exit TunaCode |

## Safety First

⚠️ **Important**: TunaCode can modify your codebase. Always:
- Use Git branches before making changes
- Review file modifications before confirming
- Keep backups of important work

## Documentation

- [**Features**](documentation/FEATURES.md) - All features, tools, and commands
- [**Advanced Configuration**](documentation/ADVANCED-CONFIG.md) - Provider setup, MCP, customization
- [**Architecture**](documentation/ARCHITECTURE.md) - Source code organization and design
- [**Development**](documentation/DEVELOPMENT.md) - Contributing and development setup

## Links

- [PyPI Package](https://pypi.org/project/tunacode-cli/)
- [GitHub Repository](https://github.com/alchemiststudiosDOTai/tunacode)
- [Report Issues](https://github.com/alchemiststudiosDOTai/tunacode/issues)

---

MIT License - see [LICENSE](LICENSE) file