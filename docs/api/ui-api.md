<!-- This document covers the API for UI components: console, panels, input handling, and tool confirmation dialogs -->

# UI API Reference

This document provides detailed API documentation for TunaCode's user interface components.

## Console Functions

`tunacode.ui.console`

The console module provides unified access to all UI functions.

### Display Functions

#### display_banner()
```python
async def display_banner() -> None:
    """
    Display TunaCode banner with version info.

    Example:
        >>> await display_banner()
        ╔═══════════════════════════════════════╗
        ║        🐟 TunaCode v0.0.51 🐟         ║
        ╚═══════════════════════════════════════╝
    """
```

#### display_context_window()
```python
async def display_context_window(state: StateManager) -> None:
    """
    Display context window usage bar.

    Args:
        state: Current state manager

    Example:
        >>> await display_context_window(state)
        Context: ████████████████░░░░ 80% (160,000/200,000 tokens)
    """
```

### Logging Functions

#### info()
```python
async def info(message: str) -> None:
    """
    Display info message.

    Args:
        message: Message to display

    Example:
        >>> await info("Processing request...")
        ℹ Processing request...
    """
```

#### warning()
```python
async def warning(message: str) -> None:
    """
    Display warning message.

    Args:
        message: Warning message

    Example:
        >>> await warning("API key not found")
        ⚠ API key not found
    """
```

#### error()
```python
async def error(message: str) -> None:
    """
    Display error message.

    Args:
        message: Error message

    Example:
        >>> await error("Command failed")
        ✗ Command failed
    """
```

#### success()
```python
async def success(message: str) -> None:
    """
    Display success message.

    Args:
        message: Success message

    Example:
        >>> await success("Operation completed")
        ✓ Operation completed
    """
```

### Spinner Functions

#### show_spinner()
```python
async def show_spinner(message: str = "Processing...") -> Live:
    """
    Show loading spinner.

    Args:
        message: Loading message

    Returns:
        Live: Rich Live instance for spinner

    Example:
        >>> spinner = await show_spinner("Loading...")
        >>> # Do work
        >>> await hide_spinner()
    """
```

#### hide_spinner()
```python
async def hide_spinner() -> None:
    """Hide the current spinner."""
```

## Input Functions

`tunacode.ui.input`

### multiline_input()
```python
async def multiline_input(
    prompt_manager: PromptManager,
    completer: Optional[Completer] = None,
    multiline: bool = True,
    key_bindings: Optional[KeyBindings] = None
) -> str:
    """
    Get multiline input from user.

    Args:
        prompt_manager: Prompt configuration manager
        completer: Optional auto-completer
        multiline: Whether to allow multiline input
        key_bindings: Optional custom key bindings

    Returns:
        str: User input text

    Raises:
        EOFError: On Ctrl+D
        KeyboardInterrupt: On Ctrl+C or double ESC

    Example:
        >>> text = await multiline_input(prompt_manager)
    """
```

## Prompt Management

`tunacode.ui.prompt_manager`

### PromptManager
```python
class PromptManager:
    """Manage prompt display and styling."""

    def __init__(self, state_manager: Optional[StateManager] = None):
        """
        Initialize prompt manager.

        Args:
            state_manager: Optional state manager for context
        """
```

#### get_prompt()
```python
def get_prompt(self) -> List[Tuple[str, str]]:
    """
    Get styled prompt tuples.

    Returns:
        List[Tuple[str, str]]: Style and text tuples

    Example:
        >>> prompt_manager.get_prompt()
        [('class:prompt', 'tunacode> ')]
    """
```

### PromptConfig
```python
@dataclass
class PromptConfig:
    """Prompt configuration."""
    prompt_text: str = "tunacode> "
    bash_prompt: str = "BASH MODE > "
    style_overrides: Dict[str, str] = field(default_factory=dict)
```

## Tool Confirmation UI

`tunacode.ui.tool_ui`

### show_tool_confirmation()
```python
async def show_tool_confirmation(
    tool_name: str,
    confirmation_info: ConfirmationInfo,
    state_manager: StateManager
) -> bool:
    """
    Show tool confirmation dialog.

    Args:
        tool_name: Name of the tool
        confirmation_info: Confirmation details
        state_manager: Current state

    Returns:
        bool: Whether tool was approved

    Example:
        >>> approved = await show_tool_confirmation(
        ...     "write_file",
        ...     confirmation_info,
        ...     state
        ... )
    """
```

### ConfirmationInfo
```python
@dataclass
class ConfirmationInfo:
    """Tool confirmation information."""
    tool_name: str
    short_description: str
    details: Optional[Dict[str, str]] = None
    preview: Optional[str] = None
    syntax: Optional[str] = None
    security_level: str = "medium"  # low, medium, high
```

## Panel Functions

`tunacode.ui.panels`

### display_streaming_agent_panel()
```python
def display_streaming_agent_panel(
    content: str,
    title: str = "Assistant"
) -> Live:
    """
    Create streaming panel for agent output.

    Args:
        content: Initial content
        title: Panel title

    Returns:
        Live: Rich Live instance for updates

    Example:
        >>> with display_streaming_agent_panel("Thinking...") as live:
        ...     # Update content
        ...     live.update(Panel("New content"))
    """
```

### display_help_panel()
```python
async def display_help_panel(
    commands: Dict[str, List[CommandInfo]]
) -> None:
    """
    Display help panel with commands.

    Args:
        commands: Commands grouped by category

    Example:
        >>> await display_help_panel({
        ...     "System": [cmd1, cmd2],
        ...     "Development": [cmd3, cmd4]
        ... })
    """
```

### display_models_panel()
```python
async def display_models_panel(models: List[ModelInfo]) -> None:
    """
    Display available models table.

    Args:
        models: List of model information

    Example:
        >>> await display_models_panel(available_models)
    """
```

## Output Formatting

`tunacode.ui.output`

### create_progress_bar()
```python
def create_progress_bar(
    percentage: float,
    width: int = 20,
    color: str = "green"
) -> str:
    """
    Create text progress bar.

    Args:
        percentage: Progress percentage (0-100)
        width: Bar width in characters
        color: Bar color

    Returns:
        str: Formatted progress bar

    Example:
        >>> bar = create_progress_bar(75.0)
        >>> print(bar)
        ████████████████░░░░
    """
```

### format_token_usage()
```python
def format_token_usage(
    tokens_used: int,
    context_window: int,
    cost: Optional[float] = None
) -> str:
    """
    Format token usage display.

    Args:
        tokens_used: Current token count
        context_window: Maximum tokens
        cost: Optional cost in USD

    Returns:
        str: Formatted usage string

    Example:
        >>> usage = format_token_usage(50000, 200000, 0.15)
        '50,000/200,000 tokens ($0.15)'
    """
```

## Completers

`tunacode.ui.completers`

### CommandCompleter
```python
class CommandCompleter(Completer):
    """Auto-complete slash commands."""

    def __init__(self, registry: CommandRegistry):
        """
        Initialize completer.

        Args:
            registry: Command registry instance
        """

    def get_completions(
        self,
        document: Document,
        complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """Get command completions."""
```

### FileReferenceCompleter
```python
class FileReferenceCompleter(Completer):
    """Auto-complete @file references."""

    def get_completions(
        self,
        document: Document,
        complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """Get file path completions."""
```

## Key Bindings

`tunacode.ui.keybindings`

### create_key_bindings()
```python
def create_key_bindings(state_manager: StateManager) -> KeyBindings:
    """
    Create application key bindings.

    Args:
        state_manager: Current state manager

    Returns:
        KeyBindings: Configured key bindings

    Bindings:
        - Enter: Submit input
        - Ctrl+O: Insert newline
        - Esc+Enter: Insert newline
        - Double ESC: Cancel operation
    """
```

## Syntax Highlighting

`tunacode.ui.lexers`

### FileReferenceLexer
```python
class FileReferenceLexer(Lexer):
    """Syntax highlighter for @file references."""

    def lex_document(self, document: Document) -> Callable:
        """
        Tokenize document.

        Args:
            document: Document to tokenize

        Returns:
            Callable: Token getter function
        """
```

## Validators

`tunacode.ui.validators`

### ModelValidator
```python
class ModelValidator(Validator):
    """Validate model selection format."""

    def validate(self, document: Document) -> None:
        """
        Validate model format.

        Args:
            document: Input document

        Raises:
            ValidationError: If format invalid

        Example:
            Valid: "openai:gpt-4"
            Invalid: "gpt-4" (missing provider)
        """
```

## UI Constants

`tunacode.ui.constants`

```python
# Colors
INFO_COLOR = "blue"
WARNING_COLOR = "yellow"
ERROR_COLOR = "red"
SUCCESS_COLOR = "green"

# Symbols
INFO_SYMBOL = "ℹ"
WARNING_SYMBOL = "⚠"
ERROR_SYMBOL = "✗"
SUCCESS_SYMBOL = "✓"

# Styles
PROMPT_STYLE = Style.from_dict({
    'prompt': '#00aa00 bold',
    'file-reference': '#0088ff',
    'command': '#ff8800',
})
```

## UI Utilities

`tunacode.ui.utils`

### format_size()
```python
def format_size(size_bytes: int) -> str:
    """
    Format bytes as human-readable.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size

    Example:
        >>> format_size(1536)
        '1.5KB'
    """
```

### truncate_middle()
```python
def truncate_middle(
    text: str,
    max_length: int,
    separator: str = "..."
) -> str:
    """
    Truncate text in the middle.

    Args:
        text: Text to truncate
        max_length: Maximum length
        separator: Truncation indicator

    Returns:
        str: Truncated text

    Example:
        >>> truncate_middle("very_long_filename.txt", 15)
        'very_l...me.txt'
    """
```

## Decorators

`tunacode.ui.decorators`

### create_sync_wrapper()
```python
def create_sync_wrapper(async_func: Callable) -> Callable:
    """
    Create synchronous wrapper for async function.

    Args:
        async_func: Async function to wrap

    Returns:
        Callable: Sync wrapper function

    Example:
        >>> print_info = create_sync_wrapper(info)
        >>> print_info("Sync call to async function")
    """
```

## Rich Console Instance

`tunacode.ui.console.console`

```python
# Global Rich console instance
console: Console = Console(
    force_terminal=True,
    stderr=False,
    soft_wrap=True,
    tab_size=4
)
```

## Usage Examples

### Basic UI Flow

```python
from tunacode.ui.console import (
    display_banner, info, error, success,
    show_spinner, hide_spinner
)

async def process_request():
    # Show banner
    await display_banner()

    # Info message
    await info("Starting process...")

    # Show spinner
    spinner = await show_spinner("Processing...")

    try:
        # Do work
        result = await perform_operation()

        # Hide spinner
        await hide_spinner()

        # Success message
        await success(f"Completed: {result}")

    except Exception as e:
        await hide_spinner()
        await error(f"Failed: {e}")
```

### Tool Confirmation

```python
from tunacode.ui.tool_ui import show_tool_confirmation, ConfirmationInfo

# Create confirmation info
info = ConfirmationInfo(
    tool_name="dangerous_operation",
    short_description="Delete all files",
    details={
        "Path": "/important/data",
        "Files": "1,234 files"
    },
    security_level="high"
)

# Show confirmation
approved = await show_tool_confirmation(
    "dangerous_operation",
    info,
    state_manager
)

if approved:
    # Execute tool
    pass
```

### Custom Panel

```python
from rich.panel import Panel
from tunacode.ui.console import console

# Create custom panel
panel = Panel(
    "Custom content here",
    title="My Panel",
    border_style="cyan",
    padding=(1, 2)
)

# Display it
console.print(panel)
```
