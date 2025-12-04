# TunaCode 2.0 (Textual Edition)

<div align="center">

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AI-powered CLI coding assistant - now with a native TUI**

</div>

---

## What's New in 2.0

- Native Textual-based terminal UI
- Real-time streaming with pause/resume (Ctrl+P)
- Interactive resource bar showing model, tokens, cost
- Status bar with git branch and last action
- Setup wizard for first-time configuration

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/ryumacodes/tunacode.git
cd tunacode
pip install hatch
hatch run tunacode --wizard
```

Or without wizard:

```bash
hatch run tunacode --model openrouter:openai/gpt-4.1
```

---

## Configuration

TunaCode stores config in `~/.tunacode/config.json`:

```json
{
  "default_model": "openrouter:openai/gpt-4.1",
  "env": {
    "OPENROUTER_API_KEY": "sk-or-v1-your-key-here",
    "OPENAI_API_KEY": "",
    "ANTHROPIC_API_KEY": "",
    "GEMINI_API_KEY": ""
  },
  "settings": {
    "max_iterations": 40,
    "enable_streaming": true
  }
}
```

### Supported Providers

| Provider | Model Format | API Key |
|----------|-------------|---------|
| OpenRouter | `openrouter:openai/gpt-4.1` | `OPENROUTER_API_KEY` |
| OpenAI | `openai:gpt-4o` | `OPENAI_API_KEY` |
| Anthropic | `anthropic:claude-3-5-sonnet` | `ANTHROPIC_API_KEY` |
| Google | `google:gemini-2.0-flash` | `GEMINI_API_KEY` |

---

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/model` | List available models |
| `/model <name>` | Switch to model |
| `/clear` | Clear conversation |
| `/yolo` | Toggle auto-confirm |
| `/branch <name>` | Create git branch |
| `!<cmd>` | Run shell command |
| `exit` | Exit TunaCode |

---

## CLI Flags

```bash
tunacode --wizard          # Run setup wizard
tunacode --model <name>    # Set model for session
tunacode --version         # Show version
```

---

## Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Submit input |
| `Esc` | Cancel streaming |
| `Esc + Enter` | Insert newline |
| `Ctrl+O` | Insert newline |
| `Ctrl+P` | Pause/resume streaming |
| `Tab` | Path completion |

---

## Development

```bash
git clone https://github.com/ryumacodes/tunacode.git
cd tunacode
pip install hatch
hatch run tunacode
```

---

## What's Coming

- `/compact` - Summarize conversation to save context
- `/plan` - Read-only planning mode
- More model integrations

---

MIT License
