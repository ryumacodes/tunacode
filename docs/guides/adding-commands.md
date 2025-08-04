<!-- This guide shows how to create new slash commands for the REPL interface, including command structure and registration -->

# Adding Commands to TunaCode

This guide explains how to create new slash commands for TunaCode's REPL interface. Commands provide quick access to functionality without going through the agent.

## Command System Overview

Commands in TunaCode:
- Start with `/` (e.g., `/help`, `/model`)
- Support aliases for convenience
- Auto-discovered by the registry
- Can have subcommands and arguments
- Integrate with the state management system

## Step-by-Step Command Creation

### Step 1: Create Command Implementation

Create a new file in `src/tunacode/cli/commands/implementations/my_commands.py`:

```python
from typing import Optional, List
from tunacode.cli.commands.base import Command, SimpleCommand, CommandCategory
from tunacode.core.state import StateManager
from tunacode.ui.console import info, error, success, warning

class MyAwesomeCommand(SimpleCommand):
    """
    A new command that does something awesome.

    This command demonstrates the key patterns for command implementation.
    """

    @property
    def name(self) -> str:
        """Primary command name"""
        return "awesome"

    @property
    def aliases(self) -> List[str]:
        """Alternative names for the command"""
        return ["aw", "awe"]

    @property
    def description(self) -> str:
        """Description shown in help"""
        return "Do something awesome with the session"

    @property
    def category(self) -> CommandCategory:
        """Category for organization"""
        return CommandCategory.DEVELOPMENT

    async def execute(self, args: str, state: StateManager) -> None:
        """
        Execute the command.

        Args:
            args: Command arguments as a string
            state: Current session state
        """
        # Parse arguments
        parts = args.split(maxsplit=1)

        if not parts:
            # No arguments - show current state
            await self._show_current_state(state)
        elif parts[0] == "set":
            # Subcommand: set
            value = parts[1] if len(parts) > 1 else ""
            await self._set_awesome_value(value, state)
        elif parts[0] == "clear":
            # Subcommand: clear
            await self._clear_awesome_state(state)
        else:
            # Unknown subcommand
            await error(f"Unknown subcommand: {parts[0]}")
            await info("Usage: /awesome [set <value>|clear]")

    async def _show_current_state(self, state: StateManager) -> None:
        """Show current awesome state"""
        awesome_value = state.state.user_config.get("awesome_value", "not set")
        await info(f"Current awesome value: {awesome_value}")

    async def _set_awesome_value(self, value: str, state: StateManager) -> None:
        """Set the awesome value"""
        if not value:
            await error("Value cannot be empty")
            return

        # Update configuration
        state.update_config({"awesome_value": value})

        # Update runtime state if needed
        state.state.awesome_mode = True

        await success(f"Awesome value set to: {value}")

    async def _clear_awesome_state(self, state: StateManager) -> None:
        """Clear awesome state"""
        # Remove from config
        config = state.state.user_config.copy()
        config.pop("awesome_value", None)
        state.update_config(config)

        # Update runtime state
        state.state.awesome_mode = False

        await success("Awesome state cleared")
```

### Step 2: Create Factory Method

In the same file, add a factory method that the registry will discover:

```python
# At the bottom of the file, outside the class
@property
def awesome_command(self) -> Command:
    """Factory method for command registry"""
    return MyAwesomeCommand(self.process_request_callback)
```

### Step 3: Complex Command Example

Here's a more complex command with rich output:

```python
from tunacode.ui.panels import display_help_panel
from tunacode.ui.output import display_banner
from rich.table import Table
from rich.panel import Panel
from tunacode.ui.console import console

class AnalyticsCommand(SimpleCommand):
    """Show session analytics and statistics"""

    @property
    def name(self) -> str:
        return "analytics"

    @property
    def aliases(self) -> List[str]:
        return ["stats", "an"]

    @property
    def description(self) -> str:
        return "Display session analytics and statistics"

    @property
    def category(self) -> CommandCategory:
        return CommandCategory.DEBUG

    async def execute(self, args: str, state: StateManager) -> None:
        """Show analytics based on arguments"""
        if not args or args == "summary":
            await self._show_summary(state)
        elif args == "tools":
            await self._show_tool_stats(state)
        elif args == "tokens":
            await self._show_token_stats(state)
        elif args == "costs":
            await self._show_cost_breakdown(state)
        else:
            await error(f"Unknown analytics type: {args}")
            await info("Available: summary, tools, tokens, costs")

    async def _show_summary(self, state: StateManager) -> None:
        """Show summary statistics"""
        # Create a rich table
        table = Table(title="Session Analytics", show_header=True)
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="green")

        # Add metrics
        table.add_row("Messages", str(len(state.state.messages)))
        table.add_row("Total Tokens", f"{state.state.total_tokens_used:,}")
        table.add_row("Total Cost", f"${state.state.total_cost:.4f}")
        table.add_row("Model", state.get_model() or "Not set")
        table.add_row("Session Duration", self._get_duration(state))

        # Display table
        console.print(table)

    async def _show_tool_stats(self, state: StateManager) -> None:
        """Show tool usage statistics"""
        # Count tool usage from messages
        tool_counts = {}

        for msg in state.state.messages:
            if hasattr(msg, 'tool_calls'):
                for call in msg.tool_calls:
                    tool_name = call.function.name
                    tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

        if not tool_counts:
            await info("No tools have been used yet")
            return

        # Create table
        table = Table(title="Tool Usage", show_header=True)
        table.add_column("Tool", style="cyan")
        table.add_column("Uses", justify="right")
        table.add_column("Category", style="yellow")

        # Sort by usage
        for tool, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
            category = self._get_tool_category(tool)
            table.add_row(tool, str(count), category)

        console.print(table)

    def _get_tool_category(self, tool_name: str) -> str:
        """Get tool category"""
        from tunacode.configuration.settings import ApplicationSettings

        if tool_name in ApplicationSettings.READ_ONLY_TOOLS:
            return "Read-Only"
        elif tool_name in ApplicationSettings.WRITE_TOOLS:
            return "Write"
        elif tool_name in ApplicationSettings.EXECUTE_TOOLS:
            return "Execute"
        else:
            return "External"

    def _get_duration(self, state: StateManager) -> str:
        """Calculate session duration"""
        from datetime import datetime

        if not state.state.messages:
            return "0:00:00"

        # Assume first message has timestamp
        start_time = getattr(state.state.messages[0], 'timestamp', datetime.now())
        duration = datetime.now() - start_time

        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{hours}:{minutes:02d}:{seconds:02d}"

# Factory method
@property
def analytics_command(self) -> Command:
    return AnalyticsCommand()
```

### Step 4: Interactive Command Example

Commands can prompt for additional input:

```python
from prompt_toolkit import prompt as prompt_sync
from prompt_toolkit.completion import WordCompleter

class ConfigureCommand(SimpleCommand):
    """Interactive configuration command"""

    @property
    def name(self) -> str:
        return "configure"

    @property
    def aliases(self) -> List[str]:
        return ["config", "cfg"]

    @property
    def description(self) -> str:
        return "Interactive configuration wizard"

    @property
    def category(self) -> CommandCategory:
        return CommandCategory.SYSTEM

    async def execute(self, args: str, state: StateManager) -> None:
        """Run configuration wizard"""
        await info("Welcome to the configuration wizard!")

        # Model selection
        model = await self._select_model(state)
        if model:
            state.update_config({"default_model": model})

        # Feature toggles
        streaming = await self._ask_yes_no("Enable streaming display?",
                                          state.state.is_streaming)
        state.update_config({"streaming": streaming})

        thoughts = await self._ask_yes_no("Show agent thoughts?",
                                         state.state.show_thoughts)
        state.update_config({"show_thoughts": thoughts})

        # Cost display
        show_costs = await self._ask_yes_no("Display token costs?", True)
        ui_options = state.state.user_config.get("ui_options", {})
        ui_options["show_costs"] = show_costs
        state.update_config({"ui_options": ui_options})

        await success("Configuration updated successfully!")

    async def _select_model(self, state: StateManager) -> Optional[str]:
        """Interactive model selection"""
        from tunacode.configuration.models import MODEL_REGISTRY

        # Get available models
        models = list(MODEL_REGISTRY.keys())
        current = state.get_model()

        # Create completer
        completer = WordCompleter(models, ignore_case=True)

        # Prompt user
        await info(f"Current model: {current}")
        await info("Available models:")
        for i, model in enumerate(models[:10]):  # Show first 10
            await info(f"  {i+1}. {model}")

        if len(models) > 10:
            await info(f"  ... and {len(models) - 10} more")

        # Get selection
        try:
            selection = prompt_sync(
                "Select model (enter to keep current): ",
                completer=completer,
                default=""
            )

            if selection and selection in models:
                return selection
            elif selection:
                await warning(f"Unknown model: {selection}")

        except (EOFError, KeyboardInterrupt):
            pass

        return None

    async def _ask_yes_no(self, question: str, default: bool = True) -> bool:
        """Ask yes/no question"""
        default_str = "Y/n" if default else "y/N"

        try:
            response = prompt_sync(f"{question} [{default_str}]: ").lower()

            if not response:
                return default

            return response.startswith('y')

        except (EOFError, KeyboardInterrupt):
            return default

# Factory method
@property
def configure_command(self) -> Command:
    return ConfigureCommand()
```

### Step 5: Command with Agent Integration

Commands can trigger agent requests:

```python
class RefactorCommand(SimpleCommand):
    """Refactor code using agent with pre-configured prompt"""

    @property
    def name(self) -> str:
        return "refactor"

    @property
    def aliases(self) -> List[str]:
        return ["rf", "improve"]

    @property
    def description(self) -> str:
        return "Refactor code files for better readability"

    @property
    def category(self) -> CommandCategory:
        return CommandCategory.DEVELOPMENT

    async def execute(self, args: str, state: StateManager) -> None:
        """Execute refactor request"""
        if not args:
            await error("Usage: /refactor <file_path> [style_guide]")
            return

        parts = args.split(maxsplit=1)
        file_path = parts[0]
        style_guide = parts[1] if len(parts) > 1 else "PEP8"

        # Validate file exists
        from pathlib import Path
        if not Path(file_path).exists():
            await error(f"File not found: {file_path}")
            return

        # Pre-approve tools for this operation
        state.state.allowed_tools.update(["read_file", "update_file", "grep"])

        # Craft refactoring prompt
        prompt = f"""Please refactor the code in {file_path} following these guidelines:
1. Follow {style_guide} style guide
2. Improve readability and maintainability
3. Add type hints where missing
4. Simplify complex logic
5. Ensure all tests still pass

Preserve all functionality - this is a refactoring, not a rewrite."""

        # Show what we're doing
        await info(f"Refactoring {file_path} using {style_guide} style guide...")

        # Process via agent
        if self.process_request_callback:
            await self.process_request_callback(
                prompt,
                state,
                is_template=True  # Skip additional confirmations
            )
        else:
            await error("Agent callback not available")

# Factory method
@property
def refactor_command(self) -> Command:
    return RefactorCommand(self.process_request_callback)
```

## Command Categories

Choose the appropriate category for your command:

```python
class CommandCategory(Enum):
    SYSTEM = "System"           # System operations (help, clear, update)
    NAVIGATION = "Navigation"   # Navigation commands (cd, ls)
    DEVELOPMENT = "Development" # Dev tools (branch, init, refactor)
    MODEL = "Model"            # Model management (model, provider)
    DEBUG = "Debug"            # Debug tools (dump, yolo, thoughts)
    CONVERSATION = "Conversation"  # Chat management (compact, export)
    TEMPLATES = "Templates"    # Template commands (template, shortcuts)
    TASKS = "Tasks"           # Task management (todo, project)
```

## Command Best Practices

### 1. Argument Parsing

```python
async def execute(self, args: str, state: StateManager) -> None:
    """Parse arguments robustly"""
    # Split with maxsplit for arguments with spaces
    parts = args.split(maxsplit=2)

    # Handle subcommands
    if not parts:
        await self._show_help()
        return

    subcommand = parts[0].lower()

    # Use match for Python 3.10+
    match subcommand:
        case "list":
            await self._list_items(state)
        case "add":
            if len(parts) < 2:
                await error("Usage: /cmd add <item>")
                return
            await self._add_item(parts[1], state)
        case "remove":
            if len(parts) < 2:
                await error("Usage: /cmd remove <id>")
                return
            await self._remove_item(parts[1], state)
        case _:
            await error(f"Unknown subcommand: {subcommand}")
            await self._show_help()
```

### 2. State Management

```python
async def execute(self, args: str, state: StateManager) -> None:
    """Properly manage state changes"""
    # Read from state
    current_value = state.state.user_config.get("my_setting", "default")

    # Validate before changing
    new_value = args.strip()
    if not self._validate_value(new_value):
        await error("Invalid value")
        return

    # Update configuration (persisted)
    state.update_config({"my_setting": new_value})

    # Update runtime state (temporary)
    state.state.my_runtime_value = new_value

    # Show confirmation
    await success(f"Setting updated: {current_value} → {new_value}")
```

### 3. Error Handling

```python
async def execute(self, args: str, state: StateManager) -> None:
    """Handle errors gracefully"""
    try:
        # Parse arguments
        value = int(args)

        # Validate
        if not 1 <= value <= 100:
            await error("Value must be between 1 and 100")
            return

        # Process
        result = await self._process_value(value)
        await success(f"Processed: {result}")

    except ValueError:
        await error("Invalid number format")
        await info("Usage: /cmd <number>")
    except Exception as e:
        await error(f"Command failed: {e}")
        logger.exception("Command execution failed")
```

### 4. User Feedback

```python
async def execute(self, args: str, state: StateManager) -> None:
    """Provide clear user feedback"""
    # Immediate acknowledgment for long operations
    await info("Processing your request...")

    # Use spinner for long operations
    from tunacode.ui.output import show_spinner, hide_spinner

    spinner = await show_spinner("Analyzing codebase...")
    try:
        results = await self._long_operation()
        await hide_spinner()

        # Show results
        if results:
            await success(f"Found {len(results)} items")
            await self._display_results(results)
        else:
            await warning("No results found")

    except Exception as e:
        await hide_spinner()
        await error(f"Analysis failed: {e}")
```

## Testing Your Command

### 1. Unit Test

Create `tests/commands/test_my_command.py`:

```python
import pytest
from tunacode.cli.commands.implementations.my_commands import MyAwesomeCommand
from tunacode.core.state import StateManager
from tests.mocks import MockUI

@pytest.mark.asyncio
async def test_awesome_command_show():
    """Test showing current state"""
    # Setup
    state = StateManager()
    state.state.user_config["awesome_value"] = "test123"

    cmd = MyAwesomeCommand()

    # Execute with no args
    await cmd.execute("", state)

    # Verify output (would need to capture)
    # assert "test123" in captured_output

@pytest.mark.asyncio
async def test_awesome_command_set():
    """Test setting value"""
    state = StateManager()
    cmd = MyAwesomeCommand()

    # Execute set command
    await cmd.execute("set myvalue", state)

    # Verify state updated
    assert state.state.user_config.get("awesome_value") == "myvalue"
    assert state.state.awesome_mode is True

@pytest.mark.asyncio
async def test_awesome_command_clear():
    """Test clearing state"""
    state = StateManager()
    state.state.user_config["awesome_value"] = "test"
    state.state.awesome_mode = True

    cmd = MyAwesomeCommand()

    # Execute clear
    await cmd.execute("clear", state)

    # Verify cleared
    assert "awesome_value" not in state.state.user_config
    assert state.state.awesome_mode is False
```

### 2. Integration Test

Test command discovery:

```python
@pytest.mark.asyncio
async def test_command_registration():
    """Test command is registered"""
    from tunacode.cli.commands.registry import CommandRegistry
    from tests.mocks import MockUI

    registry = CommandRegistry(MockUI())

    # Find command
    commands = registry.find_commands("awe")

    assert len(commands) > 0
    assert any(cmd.name == "awesome" for cmd in commands)
```

### 3. Manual Testing

```bash
# Start TunaCode
python -m tunacode

# Test your command
/awesome
/awesome set hello
/awesome clear
/aw set test  # Test alias

# Test help integration
/help  # Should show your command
```

## Advanced Features

### 1. Command Completion

Add custom completion for your command:

```python
from prompt_toolkit.completion import Completer, Completion

class MyCommandCompleter(Completer):
    """Custom completer for my command"""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        if text.startswith("/awesome "):
            # Complete subcommands
            for subcmd in ["set", "clear", "show"]:
                if subcmd.startswith(text[9:]):
                    yield Completion(
                        subcmd,
                        start_position=-len(text[9:]),
                        display=subcmd,
                        display_meta="subcommand"
                    )
```

### 2. Command History

Track command usage:

```python
async def execute(self, args: str, state: StateManager) -> None:
    """Track command usage"""
    # Log command usage
    from datetime import datetime

    # Get or create command history
    history = state.state.user_config.get("command_history", [])

    # Add this usage
    history.append({
        "command": self.name,
        "args": args,
        "timestamp": datetime.now().isoformat()
    })

    # Keep last 100 entries
    history = history[-100:]

    # Save
    state.update_config({"command_history": history})

    # Execute actual command
    await self._do_work(args, state)
```

### 3. Command Aliases with Arguments

Handle complex aliases:

```python
def matches(self, command: str) -> bool:
    """Match command and aliases with shortcuts"""
    # Direct match
    if command == self.name or command in self.aliases:
        return True

    # Special shortcuts
    shortcuts = {
        "rf-pep8": "refactor {} PEP8",
        "rf-black": "refactor {} black",
        "rf-google": "refactor {} google"
    }

    return command in shortcuts
```

## Command Documentation

### In-Code Documentation

```python
class MyCommand(SimpleCommand):
    """
    Brief description of the command.

    This command does XYZ and is useful for ABC.

    Usage:
        /mycommand              - Show current state
        /mycommand set <value>  - Set a value
        /mycommand clear        - Clear the value

    Examples:
        /mycommand set production
        /mycommand clear

    Aliases: mc, my
    """
```

### Help Text

Your command automatically appears in `/help` with its description. For detailed help:

```python
async def execute(self, args: str, state: StateManager) -> None:
    """Show detailed help if requested"""
    if args == "help" or args == "-h":
        help_text = """
MyCommand - Do something awesome

Usage:
  /mycommand [subcommand] [options]

Subcommands:
  set <value>  Set the awesome value
  clear        Clear the awesome state
  show         Show current state (default)

Options:
  -h, --help   Show this help message

Examples:
  /mycommand set production
  /mycommand clear

This command manages the awesome state of your session.
"""
        await info(help_text)
        return

    # Regular execution...
```

## Common Patterns

### 1. Toggle Commands

```python
async def execute(self, args: str, state: StateManager) -> None:
    """Toggle a boolean setting"""
    current = state.state.some_feature
    new_value = not current

    state.state.some_feature = new_value

    status = "enabled" if new_value else "disabled"
    emoji = "✅" if new_value else "❌"

    await info(f"{emoji} Feature {status}")
```

### 2. List and Filter

```python
async def execute(self, args: str, state: StateManager) -> None:
    """List items with optional filter"""
    items = self._get_items(state)

    # Apply filter if provided
    if args:
        filter_text = args.lower()
        items = [item for item in items if filter_text in item.lower()]

    if not items:
        await info("No items found")
        return

    # Display items
    await info(f"Found {len(items)} items:")
    for i, item in enumerate(items, 1):
        await info(f"  {i}. {item}")
```

### 3. Confirmation Prompts

```python
async def execute(self, args: str, state: StateManager) -> None:
    """Command with confirmation"""
    if args == "reset":
        # Dangerous operation - confirm
        try:
            response = prompt_sync("Are you sure? This will reset everything! (y/N): ")
            if response.lower() != 'y':
                await info("Reset cancelled")
                return

            # Perform reset
            await self._perform_reset(state)
            await success("Reset completed")

        except (EOFError, KeyboardInterrupt):
            await info("Reset cancelled")
```

## Next Steps

1. Study existing commands for patterns
2. Understand the [Command System Architecture](../modules/command-system.md)
3. Learn about [UI Components](../modules/ui-system.md)
4. Read [Testing Guidelines](testing-guide.md)
