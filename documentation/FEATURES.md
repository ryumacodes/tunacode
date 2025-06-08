# Features

TunaCode is a powerful AI-powered CLI coding assistant with comprehensive features for developers.

## Core Features

### Multi-Provider Support

TunaCode supports multiple AI providers, giving you flexibility in choosing your preferred model:

- **Anthropic Claude** - Including Claude 3.5 Sonnet and Haiku models
- **OpenAI GPT** - GPT-4o, GPT-4o-mini, and other OpenAI models  
- **Google Gemini** - Gemini 2.0 Flash and other Google models
- **OpenRouter** - Access to 100+ models through a single API
- **Any OpenAI-compatible API** - Support for custom endpoints

### Developer Tools

TunaCode includes 6 core tools designed for efficient coding:

1. **bash** - Enhanced shell command execution with safety features
2. **grep** - Fast parallel content search across files
3. **read_file** - Read file contents with line numbers
4. **write_file** - Create new files (fails if file exists)
5. **update_file** - Modify existing files with precise replacements
6. **run_command** - Basic command execution (simpler than bash)

Additional developer features:
- Direct shell command execution with `!` prefix
- MCP (Model Context Protocol) support for extensibility
- File operation confirmations with diffs
- Per-project context guides (TUNACODE.md)
- JSON tool parsing fallback for API compatibility

### Safety & Control

TunaCode prioritizes safety with these features:

- **Git branch integration** (`/branch`) - Create and switch branches easily
- **No automatic commits** - All git operations require explicit user action
- **Explicit file operation confirmations** - Review changes before they're applied
- **Permission tracking per session** - Know what the AI has access to
- **`/yolo` mode for power users** - Skip confirmations when you're confident

### Architecture Benefits

Built on modern foundations:

- **pydantic-ai** - Type-safe AI agent framework
- **Async throughout** - Non-blocking operations for better performance
- **Modular command system** - Easy to extend and customize
- **Rich UI with syntax highlighting** - Beautiful terminal interface
- **ReAct reasoning patterns** - Transparent AI decision-making

## Reliability Features

### JSON Tool Parsing Fallback

TunaCode automatically handles API provider failures with robust JSON parsing:

- **Automatic Recovery**: When structured tool calling fails, TunaCode parses JSON from text responses
- **Multiple Formats**: Supports inline JSON, code blocks, and complex nested structures
- **Manual Recovery**: Use `/parsetools` when automatic parsing needs assistance
- **Visual Feedback**: See `🔧 Recovered using JSON tool parsing` messages during fallback

### Enhanced Error Handling

- **Tool Schema Fixes**: Consistent parameter naming across all tools
- **Orphaned Tool Call Recovery**: Automatic cleanup with `/fix` command
- **Configuration Refresh**: Update settings without restart using `/refresh`
- **ReAct Reasoning**: Configurable iteration limits for complex problem solving

## Bash Tool Features

The enhanced bash tool provides advanced shell command execution:

- **Working Directory Support**: Execute commands in specific directories
- **Environment Variables**: Set custom environment variables for commands
- **Timeout Control**: Configurable timeouts (1-300 seconds) to prevent hanging
- **Output Capture**: Full stdout/stderr capture with truncation for large outputs
- **Safety Checks**: Warns about potentially destructive commands
- **Error Guidance**: Helpful error messages for common issues

Example usage by the AI:
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
| `/fix`                           | Fix orphaned tool calls          |
| `/refresh`                       | Reload configuration from defaults |

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

This guide helps TunaCode understand your project's specific requirements and coding standards.