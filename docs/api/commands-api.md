<!-- This document provides the API for the command system: base classes, command registry, and all command implementations -->

# Commands API Reference

This document provides detailed API documentation for TunaCode's command system.

## Base Classes

### Command

`tunacode.cli.commands.base.Command`

Abstract base class for all commands.

```python
class Command(ABC):
    """Base interface for all commands."""

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Primary command name.

        Returns:
            str: Command name (without slash)

        Example:
            return "help"
        """

    @property
    def aliases(self) -> List[str]:
        """
        Alternative command names.

        Returns:
            List[str]: List of aliases

        Example:
            return ["h", "?"]
        """
        return []

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Command description for help.

        Returns:
            str: Brief description

        Example:
            return "Show available commands"
        """

    @property
    @abstractmethod
    def category(self) -> CommandCategory:
        """
        Command category for organization.

        Returns:
            CommandCategory: Category enum value
        """

    @abstractmethod
    def matches(self, command: str) -> bool:
        """
        Check if command string matches.

        Args:
            command: Command string to check

        Returns:
            bool: Whether this command handles it
        """

    @abstractmethod
    async def execute(self, args: str, state: StateManager) -> None:
        """
        Execute the command.

        Args:
            args: Command arguments as string
            state: Current state manager
        """
```

### SimpleCommand

`tunacode.cli.commands.base.SimpleCommand`

Base class for simple command implementations.

```python
class SimpleCommand(Command):
    """Base class for simple commands."""

    def __init__(self, process_request_callback=None):
        """
        Initialize command.

        Args:
            process_request_callback: Optional agent callback
        """
        self.process_request_callback = process_request_callback

    def matches(self, command: str) -> bool:
        """
        Default matching implementation.

        Checks exact match or aliases.
        """
        return command == self.name or command in self.aliases
```

### CommandCategory

`tunacode.cli.commands.base.CommandCategory`

```python
class CommandCategory(Enum):
    """Command categories for organization."""
    SYSTEM = "System"
    NAVIGATION = "Navigation"
    DEVELOPMENT = "Development"
    MODEL = "Model"
    DEBUG = "Debug"
    CONVERSATION = "Conversation"
    TEMPLATES = "Templates"
    TASKS = "Tasks"
```

### CommandSpec

`tunacode.cli.commands.base.CommandSpec`

```python
@dataclass
class CommandSpec:
    """Command specification metadata."""
    name: str
    aliases: List[str]
    description: str
    category: CommandCategory
    usage: Optional[str] = None
    examples: Optional[List[str]] = None
```

## Command Registry

`tunacode.cli.commands.registry.CommandRegistry`

```python
class CommandRegistry:
    """Central command management system."""

    def __init__(
        self,
        ui: UIProtocol,
        process_request_callback: Optional[Callable] = None
    ):
        """
        Initialize registry.

        Args:
            ui: UI protocol implementation
            process_request_callback: Optional agent callback
        """
```

### Methods

#### execute()
```python
async def execute(
    self,
    command_str: str,
    state: StateManager
) -> bool:
    """
    Execute a command string.

    Args:
        command_str: Full command string with args
        state: Current state manager

    Returns:
        bool: Whether command was found and executed

    Example:
        >>> await registry.execute("/help", state)
        True
    """
```

#### find_commands()
```python
def find_commands(self, prefix: str) -> List[CommandInfo]:
    """
    Find commands matching prefix.

    Args:
        prefix: Command prefix to match

    Returns:
        List[CommandInfo]: Matching commands

    Example:
        >>> registry.find_commands("he")
        [CommandInfo(name="help", ...)]
    """
```

#### get_commands_by_category()
```python
def get_commands_by_category() -> Dict[str, List[CommandInfo]]:
    """
    Get all commands grouped by category.

    Returns:
        Dict[str, List[CommandInfo]]: Commands by category
    """
```

## Command Implementations

### System Commands

#### HelpCommand
```python
class HelpCommand(SimpleCommand):
    """Show available commands."""

    name = "help"
    aliases = ["h", "?"]
    description = "Show available commands"
    category = CommandCategory.SYSTEM

    async def execute(self, args: str, state: StateManager) -> None:
        """Display help panel with all commands."""
```

#### ClearCommand
```python
class ClearCommand(SimpleCommand):
    """Clear the screen."""

    name = "clear"
    aliases = ["cls"]
    description = "Clear the screen"
    category = CommandCategory.SYSTEM

    async def execute(self, args: str, state: StateManager) -> None:
        """
        Clear screen and optionally message history.

        Args:
            args: "all" to clear message history too
        """
```

#### UpdateCommand
```python
class UpdateCommand(SimpleCommand):
    """Update TunaCode to latest version."""

    name = "update"
    description = "Update TunaCode to latest version"
    category = CommandCategory.SYSTEM

    async def execute(self, args: str, state: StateManager) -> None:
        """Auto-detect installation method and update."""
```

### Model Commands

#### ModelCommand
```python
class ModelCommand(SimpleCommand):
    """Switch AI model."""

    name = "model"
    aliases = ["m"]
    description = "Switch AI model"
    category = CommandCategory.MODEL

    async def execute(self, args: str, state: StateManager) -> None:
        """
        Switch model or show current/available.

        Args:
            args: Model in "provider:model" format
        """
```

### Development Commands

#### BranchCommand
```python
class BranchCommand(SimpleCommand):
    """Create and switch git branch."""

    name = "branch"
    aliases = ["b"]
    description = "Create and switch git branch"
    category = CommandCategory.DEVELOPMENT

    async def execute(self, args: str, state: StateManager) -> None:
        """
        Create new git branch.

        Args:
            args: Branch name
        """
```

#### InitCommand
```python
class InitCommand(SimpleCommand):
    """Initialize TUNACODE.md file."""

    name = "init"
    description = "Create TUNACODE.md project file"
    category = CommandCategory.DEVELOPMENT

    async def execute(self, args: str, state: StateManager) -> None:
        """Create project context file."""
```

### Debug Commands

#### YoloCommand
```python
class YoloCommand(SimpleCommand):
    """Toggle confirmation prompts."""

    name = "yolo"
    description = "Toggle confirmation prompts"
    category = CommandCategory.DEBUG

    async def execute(self, args: str, state: StateManager) -> None:
        """Toggle YOLO mode on/off."""
```

#### ThoughtsCommand
```python
class ThoughtsCommand(SimpleCommand):
    """Toggle agent thought visibility."""

    name = "thoughts"
    description = "Toggle agent thought visibility"
    category = CommandCategory.DEBUG

    async def execute(self, args: str, state: StateManager) -> None:
        """
        Toggle thoughts display.

        Args:
            args: "on" or "off" (optional)
        """
```

#### DumpCommand
```python
class DumpCommand(SimpleCommand):
    """Dump message history."""

    name = "dump"
    description = "Show message history"
    category = CommandCategory.DEBUG

    async def execute(self, args: str, state: StateManager) -> None:
        """Display all messages in history."""
```

### Conversation Commands

#### CompactCommand
```python
class CompactCommand(SimpleCommand):
    """Summarize conversation to save tokens."""

    name = "compact"
    description = "Summarize conversation to save tokens"
    category = CommandCategory.CONVERSATION

    async def execute(self, args: str, state: StateManager) -> None:
        """Use agent to summarize and compress history."""
```

### Template Commands

#### TemplateCommand
```python
class TemplateCommand(SimpleCommand):
    """Manage prompt templates."""

    name = "template"
    aliases = ["tmpl"]
    description = "Manage prompt templates"
    category = CommandCategory.TEMPLATES

    async def execute(self, args: str, state: StateManager) -> None:
        """
        Template management.

        Subcommands:
            list - Show available templates
            load <name> - Load a template
            create - Create new template
            clear - Clear active template
        """
```

### Task Commands

#### TodoCommand
```python
class TodoCommand(SimpleCommand):
    """Manage todo list."""

    name = "todo"
    aliases = ["t", "task"]
    description = "Manage todo list"
    category = CommandCategory.TASKS

    async def execute(self, args: str, state: StateManager) -> None:
        """
        Todo management.

        Subcommands:
            list - Show todos
            add <task> - Add todo
            done <id> - Mark complete
            update <id> <text> - Update todo
            remove <id> - Remove todo
            clear - Clear all todos
        """
```

## Creating Custom Commands

### Basic Example

```python
from tunacode.cli.commands.base import SimpleCommand, CommandCategory
from tunacode.ui.console import info, error

class StatusCommand(SimpleCommand):
    """Show session status."""

    name = "status"
    aliases = ["s", "stat"]
    description = "Show current session status"
    category = CommandCategory.SYSTEM

    async def execute(self, args: str, state: StateManager) -> None:
        """Display session information."""
        model = state.get_model() or "Not set"
        messages = len(state.state.messages)
        tokens = state.state.total_tokens_used

        await info(f"Model: {model}")
        await info(f"Messages: {messages}")
        await info(f"Tokens used: {tokens:,}")
```

### Command with Subcommands

```python
class ConfigCommand(SimpleCommand):
    """Configuration management."""

    name = "config"
    aliases = ["cfg"]
    description = "Manage configuration"
    category = CommandCategory.SYSTEM

    async def execute(self, args: str, state: StateManager) -> None:
        """Handle config subcommands."""
        parts = args.split(maxsplit=1)
        subcommand = parts[0] if parts else "show"

        if subcommand == "show":
            await self._show_config(state)
        elif subcommand == "set":
            if len(parts) < 2:
                await error("Usage: /config set <key> <value>")
                return
            await self._set_config(parts[1], state)
        elif subcommand == "reset":
            await self._reset_config(state)
        else:
            await error(f"Unknown subcommand: {subcommand}")

    async def _show_config(self, state: StateManager) -> None:
        """Show current configuration."""
        # Implementation

    async def _set_config(self, args: str, state: StateManager) -> None:
        """Set configuration value."""
        # Implementation

    async def _reset_config(self, state: StateManager) -> None:
        """Reset to defaults."""
        # Implementation
```

### Command with Agent Integration

```python
class AnalyzeCommand(SimpleCommand):
    """Analyze code with agent."""

    name = "analyze"
    aliases = ["a"]
    description = "Analyze code files"
    category = CommandCategory.DEVELOPMENT

    async def execute(self, args: str, state: StateManager) -> None:
        """Trigger code analysis."""
        if not args:
            await error("Usage: /analyze <file_or_directory>")
            return

        # Pre-approve tools
        state.state.allowed_tools.update([
            "read_file", "grep", "list_dir"
        ])

        # Create analysis prompt
        prompt = f"""Please analyze the code in {args} and provide:
1. Code quality assessment
2. Potential issues or bugs
3. Performance considerations
4. Suggestions for improvement"""

        # Process via agent
        if self.process_request_callback:
            await info(f"Analyzing {args}...")
            await self.process_request_callback(
                prompt,
                state,
                is_template=True
            )
        else:
            await error("Agent not available")
```

## Command Registration

### Factory Method Pattern

Commands use factory methods for registration:

```python
# In implementations/my_commands.py

# Command implementation
class MyCommand(SimpleCommand):
    # ... implementation ...

# Factory method for registry
@property
def my_command(self) -> Command:
    """Factory for my command."""
    return MyCommand(self.process_request_callback)
```

### Auto-Discovery

The registry automatically discovers commands:

1. Scans `implementations/` directory
2. Imports all Python modules
3. Looks for `@property` methods returning `Command`
4. Registers discovered commands

## Template Shortcuts

`tunacode.cli.commands.template_shortcut.TemplateShortcutCommand`

```python
class TemplateShortcutCommand(Command):
    """Dynamic command from template shortcut."""

    def __init__(
        self,
        shortcut: str,
        template_name: str,
        template_prompt: str,
        allowed_tools: List[str],
        process_request_callback: Callable
    ):
        """
        Create shortcut command.

        Args:
            shortcut: Command shortcut
            template_name: Template name
            template_prompt: Template prompt text
            allowed_tools: Pre-approved tools
            process_request_callback: Agent callback
        """
```

## Command Info Types

### CommandInfo

```python
@dataclass
class CommandInfo:
    """Command information for display."""
    name: str
    aliases: List[str]
    description: str
    category: Optional[CommandCategory] = None
    usage: Optional[str] = None
```

## Error Handling

Commands should handle errors gracefully:

```python
async def execute(self, args: str, state: StateManager) -> None:
    try:
        # Validate arguments
        if not args:
            await error("Usage: /mycommand <argument>")
            return

        # Perform operation
        result = await self.perform_operation(args)
        await success(f"Operation completed: {result}")

    except ValueError as e:
        await error(f"Invalid input: {e}")
    except Exception as e:
        await error(f"Command failed: {e}")
        logger.exception("Command execution failed")
```

## Testing Commands

### Unit Testing

```python
import pytest
from tunacode.cli.commands.implementations.my_commands import MyCommand
from tunacode.core.state import StateManager

@pytest.mark.asyncio
async def test_my_command():
    # Setup
    state = StateManager()
    command = MyCommand()

    # Test execution
    await command.execute("test argument", state)

    # Verify state changes
    assert state.state.some_value == expected_value
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_command_discovery():
    """Test command is discovered by registry."""
    from tunacode.cli.commands.registry import CommandRegistry
    from tunacode.ui.console import MockUI

    registry = CommandRegistry(MockUI())

    # Verify command exists
    commands = registry.find_commands("mycommand")
    assert len(commands) > 0

    # Test execution
    success = await registry.execute("/mycommand test", state)
    assert success
```
