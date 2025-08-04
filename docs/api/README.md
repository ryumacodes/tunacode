<!-- This is the main API reference index that links to all module API documentation and provides a quick reference guide -->

# TunaCode API Reference

This directory contains comprehensive API documentation for all TunaCode modules, classes, and functions.

## API Documentation Structure

- [Core API](core-api.md) - Core system components (StateManager, Agent, ToolHandler)
- [Tools API](tools-api.md) - Tool base classes and implementations
- [UI API](ui-api.md) - User interface components and utilities
- [Commands API](commands-api.md) - Command system interfaces
- [Configuration API](configuration-api.md) - Settings and model management
- [Utils API](utils-api.md) - Utility functions and helpers

## Quick Reference

### Core Classes

| Class | Module | Description |
|-------|--------|-------------|
| `StateManager` | `core.state` | Central state management |
| `BaseTool` | `tools.base` | Base class for all tools |
| `Command` | `cli.commands.base` | Command interface |
| `MCPManager` | `services.mcp` | MCP server management |

### Key Functions

| Function | Module | Description |
|----------|--------|-------------|
| `process_request()` | `core.agents.main` | Main agent entry point |
| `load_user_config()` | `utils.user_configuration` | Load configuration |
| `validate_command()` | `utils.security` | Security validation |
| `multiline_input()` | `ui.input` | Get user input |

### Protocols & Types

| Type | Module | Description |
|------|--------|-------------|
| `UIProtocol` | `types` | UI interface protocol |
| `Message` | `types` | Message type |
| `ConfirmationInfo` | `ui.tool_ui` | Tool confirmation data |

## Usage Examples

### Creating a Tool

```python
from tunacode.tools.base import BaseTool
from tunacode.ui.tool_ui import ConfirmationInfo

class MyTool(BaseTool):
    async def run(self, **kwargs) -> str:
        # Implementation
        return "Result"

    def format_confirmation(self, **kwargs) -> ConfirmationInfo:
        return ConfirmationInfo(
            tool_name="my_tool",
            short_description="Do something"
        )
```

### Creating a Command

```python
from tunacode.cli.commands.base import SimpleCommand, CommandCategory

class MyCommand(SimpleCommand):
    name = "mycommand"
    description = "My command"
    category = CommandCategory.SYSTEM

    async def execute(self, args: str, state: StateManager) -> None:
        # Implementation
        pass
```

### Using State Manager

```python
from tunacode.core.state import StateManager

# Create state manager
state = StateManager()

# Access state
model = state.get_model()
messages = state.state.messages

# Update configuration
state.update_config({"key": "value"})
```

## Type Annotations

All APIs use Python type hints for clarity:

```python
async def process_request(
    request: str,
    state: StateManager,
    process_request_callback: Optional[Callable] = None,
    is_template: bool = False
) -> str:
    ...
```

## Error Handling

Most APIs follow these error patterns:

```python
# Retryable errors (agent can fix)
from pydantic_ai import ModelRetry
raise ModelRetry("Fixable error message")

# Non-retryable errors
raise ValueError("Fatal error message")

# Logged errors
logger.error("Error message", exc_info=True)
```

## Async APIs

Most TunaCode APIs are async:

```python
# Async function
async def my_function() -> str:
    result = await some_operation()
    return result

# Usage
result = await my_function()
```

## Context Managers

Some APIs provide context managers:

```python
# Spinner context
async with show_spinner("Processing..."):
    await long_operation()

# MCP server context
async with mcp_manager:
    await use_mcp_tools()
```

## See Also

- [Architecture Documentation](../modules/core-architecture.md)
- [Developer Guides](../guides/getting-started.md)
- [Type Definitions](../../src/tunacode/types.py)
