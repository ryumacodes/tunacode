# TunaCode

<div align="center">

[![PyPI version](https://badge.fury.io/py/tunacode-cli.svg)](https://badge.fury.io/py/tunacode-cli)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Your AI-powered CLI coding assistant**

[Quick Start](#quick-start)  [Features](#features)  [Configuration](#configuration)  [Documentation](#documentation)

</div>

---

## Overview

> **Safety First**: TunaCode can modify your codebase. Always use git branches before making major changes. The `/undo` command has been removed - use git for version control.

> **Beta Notice**: TunaCode is currently in beta. [Report issues](https://github.com/alchemiststudiosDOTai/tunacode/issues) or share feedback to help us improve!

---

### Recent Updates (v0.0.15)

- **Shell Command Support**: Execute shell commands directly with `!command` or open interactive shell with `!`
- **Enhanced Bash Tool**: Advanced bash execution with timeouts, working directory, and environment variables
- **JSON Tool Parsing Fallback**: Automatic recovery when API providers fail with structured tool calling
- **Enhanced Reliability**: Fixed parameter naming issues that caused tool schema errors
- **Configuration Management**: New `/refresh` command to reload config without restart
- **Improved ReAct Reasoning**: Enhanced iteration limits (now defaults to 20) and better thought processing
- **New Debug Commands**: `/parsetools` for manual JSON parsing, `/iterations` for controlling reasoning depth
- **Better Error Recovery**: Multiple fallback mechanisms for various failure scenarios

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

- 6 core tools: bash, grep, read_file, write_file, update_file, run_command
- Direct shell command execution with `!` prefix
- MCP (Model Context Protocol) support
- File operation confirmations with diffs
- Per-project context guides (TUNACODE.md)
- JSON tool parsing fallback for API compatibility

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
- ReAct reasoning patterns

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

### Core Commands

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
| `!<command>`                     | Run shell command                |
| `!`                              | Open interactive shell           |
| `exit`                           | Exit application                 |

### Debug & Recovery Commands

| Command                          | Description                      |
| -------------------------------- | -------------------------------- |
| `/thoughts`                      | Toggle ReAct thought display     |
| `/iterations <1-50>`             | Set max reasoning iterations     |
| `/parsetools`                    | Parse JSON tool calls manually   |
| `/fix`                           | Fix orphaned tool calls         |
| `/refresh`                       | Reload configuration from defaults |

---

## Available Tools

### Bash Tool
The enhanced bash tool provides advanced shell command execution with safety features:

- **Working Directory Support**: Execute commands in specific directories
- **Environment Variables**: Set custom environment variables for commands
- **Timeout Control**: Configurable timeouts (1-300 seconds) to prevent hanging
- **Output Capture**: Full stdout/stderr capture with truncation for large outputs
- **Safety Checks**: Warns about potentially destructive commands
- **Error Guidance**: Helpful error messages for common issues (command not found, permission denied, etc.)

**Example usage by the AI:**
```python
# Simple command
await bash("ls -la")

# With working directory
await bash("npm install", cwd="/path/to/project")

# With timeout for long operations
await bash("npm run build", timeout=120)

# With environment variables
await bash("python script.py", env={"API_KEY": "secret"})
```

### Other Core Tools
- **grep**: Fast parallel content search across files
- **read_file**: Read file contents with line numbers
- **write_file**: Create new files (fails if file exists)
- **update_file**: Modify existing files with precise replacements
- **run_command**: Basic command execution (simpler than bash)

---

## Reliability Features

### JSON Tool Parsing Fallback

TunaCode automatically handles API provider failures with robust JSON parsing:

- **Automatic Recovery**: When structured tool calling fails, TunaCode parses JSON from text responses
- **Multiple Formats**: Supports inline JSON, code blocks, and complex nested structures
- **Manual Recovery**: Use `/parsetools` when automatic parsing needs assistance
- **Visual Feedback**: See `Recovered using JSON tool parsing` messages during fallback

### Enhanced Error Handling

- **Tool Schema Fixes**: Consistent parameter naming across all tools
- **Orphaned Tool Call Recovery**: Automatic cleanup with `/fix` command
- **Configuration Refresh**: Update settings without restart using `/refresh`
- **ReAct Reasoning**: Configurable iteration limits for complex problem solving

---

## Customization

### Project Guides

Create a `TUNACODE.md` file in your project root to customize TunaCode's behavior:

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

## Source Code Architecture

### Directory Structure

```
src/tunacode/
├── cli/                    # Command Line Interface
│   ├── commands.py        # Command registry and implementations
│   ├── main.py           # Entry point and CLI setup (Typer)
│   └── repl.py           # Interactive REPL loop
│
├── configuration/         # Configuration Management
│   ├── defaults.py       # Default configuration values
│   ├── models.py         # Configuration data models
│   └── settings.py       # Settings loader and validator
│
├── core/                 # Core Application Logic
│   ├── agents/           # AI Agent System
│   │   └── main.py       # Primary agent implementation (pydantic-ai)
│   ├── setup/            # Application Setup & Initialization
│   │   ├── agent_setup.py     # Agent configuration
│   │   ├── base.py           # Setup step base class
│   │   ├── config_setup.py   # Configuration setup
│   │   ├── coordinator.py    # Setup orchestration
│   │   ├── environment_setup.py  # Environment validation
│   │   └── git_safety_setup.py   # Git safety checks
│   ├── state.py          # Application state management
│   └── tool_handler.py   # Tool execution and validation
│
├── services/             # External Services
│   └── mcp.py           # Model Context Protocol integration
│
├── tools/               # AI Agent Tools
│   ├── base.py         # Tool base classes
│   ├── bash.py         # Enhanced shell command execution
│   ├── grep.py         # Parallel content search tool
│   ├── read_file.py    # File reading tool
│   ├── run_command.py  # Basic command execution tool
│   ├── update_file.py  # File modification tool
│   └── write_file.py   # File creation tool
│
├── ui/                 # User Interface Components
│   ├── completers.py   # Tab completion
│   ├── console.py      # Rich console setup
│   ├── input.py        # Input handling
│   ├── keybindings.py  # Keyboard shortcuts
│   ├── lexers.py       # Syntax highlighting
│   ├── output.py       # Output formatting and banner
│   ├── panels.py       # UI panels and layouts
│   ├── prompt_manager.py # Prompt toolkit integration
│   └── validators.py   # Input validation
│
├── utils/              # Utility Functions
│   ├── bm25.py        # BM25 search algorithm (beta)
│   ├── diff_utils.py  # Diff generation and formatting
│   ├── file_utils.py  # File system operations
│   ├── ripgrep.py     # Code search utilities
│   ├── system.py      # System information
│   ├── text_utils.py  # Text processing
│   └── user_configuration.py # User config management
│
├── constants.py        # Application constants
├── context.py         # Context management
├── exceptions.py      # Custom exceptions
├── types.py           # Type definitions
└── prompts/
    └── system.txt     # System prompts for AI agent
```

### Key Components

| Component            | Purpose                  | Key Files                       |
| -------------------- | ------------------------ | ------------------------------- |
| **CLI Layer**        | Command parsing and REPL | `cli/main.py`, `cli/repl.py`    |
| **Agent System**     | AI-powered assistance    | `core/agents/main.py`           |
| **Tool System**      | File/command operations  | `tools/*.py`                    |
| **State Management** | Session state tracking   | `core/state.py`                 |
| **UI Framework**     | Rich terminal interface  | `ui/output.py`, `ui/console.py` |
| **Configuration**    | User settings & models   | `configuration/*.py`            |
| **Setup System**     | Initial configuration    | `core/setup/*.py`               |

### Data Flow

```
CLI Input 1 Command Registry 1 REPL 1 Agent 1 Tools 1 UI Output
     2              2           2       2       2        1
State Manager 11111111111111111111
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

### Key Differences from sidekick-cli

While TunaCode builds on the foundation of sidekick-cli, we've made several architectural changes for our workflow:

- **JSON Tool Parsing Fallback**: Added fallback parsing for when API providers fail with structured tool calling
- **Parallel Search Tools**: New `bash` and `grep` tools with parallel execution for codebase navigation
- **ReAct Reasoning**: Implemented ReAct (Reasoning + Acting) patterns with configurable iteration limits
- **Dynamic Configuration**: Added `/refresh` command and modified configuration management
- **Safety Changes**: Removed automatic git commits and `/undo` command - requires explicit git usage
- **Error Recovery**: Multiple fallback mechanisms and orphaned tool call recovery
- **Tool System Rewrite**: Complete overhaul of internal tools with atomic operations and different confirmation UIs
- **Debug Commands**: Added `/parsetools`, `/thoughts`, `/iterations` for debugging
