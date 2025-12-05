# tunacode-cli

A TUI code agent.

**Note:** TunaCode has full bash shell access. This tool assumes you know what you're doing. If you're concerned, run it in a sandboxed environment.

## v0.1.1 - Major Rewrite

This release is a complete rewrite with a new Textual-based TUI.

**Upgrading from v1?** The legacy v1 codebase is preserved in the `legacy-v1` branch and will only receive security updates.

## Requirements

- Python 3.11+

## Installation

```bash
pip install tunacode-cli
```

Or with uv:

```bash
uv tool install tunacode-cli
```

## Quick Start

1. Run the setup wizard to configure your API key:

```bash
tunacode --wizard
```

2. Start coding:

```bash
tunacode
```

## Configuration

Set your API key as an environment variable or use the setup wizard:

```bash
export OPENAI_API_KEY="your-key"
# or
export ANTHROPIC_API_KEY="your-key"
```

Config file location: `~/.config/tunacode.json`

## Commands

| Command    | Description              |
|------------|--------------------------|
| /help      | Show available commands  |
| /model     | Change AI model          |
| /clear     | Clear conversation       |
| /compact   | Compress context         |
| exit       | Quit tunacode            |

## License

MIT
