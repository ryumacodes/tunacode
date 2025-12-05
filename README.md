# TunaCode CLI

[![PyPI version](https://badge.fury.io/py/tunacode-cli.svg)](https://badge.fury.io/py/tunacode-cli)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

TunaCode is an AI-powered CLI coding assistant that helps you write, debug, and refactor code faster through natural language interaction.

## Quick Install

```bash
# Option 1: One-line install (Linux/macOS)
wget -qO- https://raw.githubusercontent.com/alchemiststudiosDOTai/tunacode/master/scripts/install_linux.sh | bash

# Option 2: UV install (recommended)
uv tool install tunacode-cli

# Option 3: pip install
pip install tunacode-cli
```

For detailed installation and configuration instructions, see the [**Getting Started Guide**](documentation/user/getting-started.md).

## What's New in 2.0

- Native Textual-based terminal UI
- Real-time streaming with pause/resume (Ctrl+P)
- Interactive resource bar showing model, tokens, cost
- Status bar with git branch and last action
- Setup wizard for first-time configuration

## Quickstart

```bash
# 1) Install (choose one)
uv tool install tunacode-cli  # recommended
# or: pip install tunacode-cli

# 2) Launch the CLI
tunacode --wizard   # guided setup (enter an API key, pick a model)

# 3) Try common commands in the REPL
/help        # see commands
/model       # explore models and set a default
/plan        # enter read-only Plan Mode
```

Tip: You can also skip the wizard and set everything via flags:

```bash
tunacode --model openai:gpt-4.1 --key sk-your-key
```

## Development Installation

For contributors and developers who want to work on TunaCode:

```bash
# Clone the repository
git clone https://github.com/alchemiststudiosDOTai/tunacode.git
cd tunacode

# Quick setup (recommended) - uses UV automatically if available
./scripts/setup_dev_env.sh

# Or manual setup with UV (recommended)
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Alternative: traditional setup
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"

# Verify installation
tunacode --version
```

See the [Hatch Build System Guide](documentation/development/hatch-build-system.md) for detailed instructions on the development environment.

## Configuration

Choose your AI provider and set your API key. For more details, see the [Configuration Section](documentation/user/getting-started.md#2-configuration) in the Getting Started Guide. For local models (LM Studio, Ollama, etc.), see the [Local Models Setup Guide](documentation/configuration/local-models.md).

### New: Enhanced Model Selection

TunaCode now automatically saves your model selection for future sessions. When you choose a model using `/model <provider:name>`, it will be remembered across restarts.

**If you encounter API key errors**, you can manually create a configuration file that matches the current schema:

```bash
# Create the config file
cat > ~/.config/tunacode.json << 'EOF'
{
  "default_model": "openai:gpt-4.1",
  "env": {
    "OPENAI_API_KEY": "your-openai-api-key-here",
    "ANTHROPIC_API_KEY": "",
    "GEMINI_API_KEY": "",
    "OPENROUTER_API_KEY": ""
  },
  "settings": {
    "enable_streaming": true,
    "max_iterations": 40,
    "context_window_size": 200000
  },
  "mcpServers": {}
}
EOF
```

Replace the model and API key with your preferred provider and credentials. Examples:
- `openai:gpt-4.1` (requires OPENAI_API_KEY)
- `anthropic:claude-4-sonnet-20250522` (requires ANTHROPIC_API_KEY)
- `google:gemini-2.5-pro` (requires GEMINI_API_KEY)




### Recommended Models

- `google/gemini-2.5-pro` - Complex reasoning
- `openai/gpt-4.1` - General purpose
- `deepseek/deepseek-r1-0528` - Code generation
- `openai/gpt-4.1-mini` - Fast and cost-effective
- `anthropic/claude-4-sonnet-20250522` - Context handling

## Start Coding

```bash
tunacode
```

## Basic Commands

| Command                  | Description            |
| ------------------------ | ---------------------- |
| `/help`                  | Show all commands      |
| `/model <provider:name>` | Switch model           |
| `/clear`                 | Clear message history  |
| `/compact`               | Summarize conversation |
| `/branch <name>`         | Create Git branch      |
| `/yolo`                  | Skip confirmations     |
| `!<command>`             | Run shell command      |
| `exit`                   | Exit TunaCode          |

## CLI Flags

```bash
tunacode --wizard          # Run setup wizard
tunacode --model <name>    # Set model for session
tunacode --version         # Show version
```

## Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Submit input |
| `Esc` | Cancel streaming |
| `Esc + Enter` | Insert newline |
| `Ctrl+O` | Insert newline |
| `Ctrl+P` | Pause/resume streaming |
| `Tab` | Path completion |

## Performance

Parallel execution of read-only operations provides 3x faster file operations through concurrent async I/O.

## Development

Focus is on stability and core features. Report bugs via GitHub issues.

## Safety First

⚠️ **Important**: TunaCode can modify your codebase. Always:

- Use Git branches before making changes
- Review file modifications before confirming
- Keep backups of important work

## Documentation

For a complete overview of the documentation, see the [**Documentation Hub**](documentation/README.md).

### User Documentation

- [**Getting Started**](documentation/user/getting-started.md) - How to install, configure, and use TunaCode.
- [**Commands**](documentation/user/commands.md) - A complete list of all available commands.

### Developer Documentation

- [**Advanced Configuration**](documentation/configuration/config-file-example.md) - Configuration examples

## Links

- [PyPI Package](https://pypi.org/project/tunacode-cli/)
- [GitHub Repository](https://github.com/alchemiststudiosDOTai/tunacode)
- [Report Issues](https://github.com/alchemiststudiosDOTai/tunacode/issues)

---

> **Why don't programmers like nature?**  
> It has too many bugs.

---

MIT License - see [LICENSE](LICENSE) file
