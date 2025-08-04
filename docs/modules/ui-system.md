<!-- This document details the UI components including console output, input handling, tool confirmation dialogs, panels, and keybindings -->

# TunaCode UI System Documentation

## Overview

TunaCode's UI system provides a modern, responsive terminal interface built on `prompt_toolkit` and `rich`. The system combines advanced input handling, real-time streaming output, syntax highlighting, and interactive confirmations into a cohesive user experience.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Console Layer                       │
│         (Unified coordination via console.py)        │
└─────────────────────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
┌───────────────┐ ┌─────────────┐ ┌──────────────────┐
│  Input Layer  │ │Output Layer │ │ Interaction Layer│
│  (input.py)   │ │(output.py)  │ │   (tool_ui.py)   │
└───────────────┘ └─────────────┘ └──────────────────┘
    │                    │                    │
┌───────────────────────────────────────────────────┐
│              Supporting Components                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Prompts  │ │  Panels  │ │   Completers     │ │
│  │ Lexers   │ │Validators│ │   Keybindings    │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
└───────────────────────────────────────────────────┘
```

## Core Components

### 1. Console Coordination (console.py)

The central hub that imports and re-exports all UI functionality:

```python
# Unified imports for clean API
from tunacode.ui.output import (
    display_banner,
    display_context_window,
    print_info, print_warning, print_error,
    show_spinner, hide_spinner,
    # ... async versions
)

from tunacode.ui.input import multiline_input
from tunacode.ui.prompt_manager import PromptManager
from tunacode.ui.tool_ui import show_tool_confirmation
from tunacode.ui.panels import (
    display_streaming_agent_panel,
    display_help_panel,
    display_models_panel
)

# Async wrappers for logging
async def info(message: str):
    """Async wrapper for thread-safe logging"""
    await asyncio.to_thread(print_info, message)
```

**Key Features:**
- Single import point for all UI functions
- Async wrappers for thread safety
- Consistent API across components
- Rich console instance management

### 2. Input Management (input.py)

Sophisticated multiline input with auto-completion:

```python
async def multiline_input(
    prompt_manager: PromptManager,
    completer: Optional[Completer] = None,
    multiline: bool = True,
    key_bindings: Optional[KeyBindings] = None
) -> str:
    """Advanced input handling with prompt_toolkit"""

    # Dynamic prompt based on input
    def get_prompt():
        text = session.default_buffer.text
        if text.startswith("!"):
            return "BASH MODE > "
        return prompt_manager.get_prompt()

    # Create session with features
    session = PromptSession(
        message=get_prompt,
        multiline=multiline,
        completer=completer,
        complete_while_typing=True,
        key_bindings=key_bindings,
        enable_history_search=True,
        lexer=FileReferenceLexer()  # Syntax highlighting
    )

    # Get input with SIGINT handling
    try:
        result = await session.prompt_async()
        return result.strip()
    except (EOFError, KeyboardInterrupt):
        raise
```

**Features:**
- Dynamic prompt changes (BASH MODE indicator)
- File reference completion (@file patterns)
- Command completion (/commands)
- Syntax highlighting for file references
- Multiline editing with Ctrl+O
- History search support

### 3. Prompt Management (prompt_manager.py)

Session-based prompt configuration:

```python
@dataclass
class PromptConfig:
    """Prompt configuration"""
    prompt_text: str = "tunacode> "
    bash_prompt: str = "BASH MODE > "
    style_overrides: Dict[str, str] = field(default_factory=dict)

class PromptManager:
    """Manage prompt lifecycle and styling"""

    def __init__(self, state_manager: Optional[StateManager] = None):
        self.state_manager = state_manager
        self.config = PromptConfig()
        self._setup_styles()

    def get_prompt(self) -> List[Tuple[str, str]]:
        """Get styled prompt tuples"""
        if self.state_manager and self.state_manager.state.streaming_panel:
            # Simplified prompt during streaming
            return [("class:prompt", "> ")]
        return [("class:prompt", self.config.prompt_text)]

    def _get_style(self) -> Style:
        """Create prompt_toolkit style"""
        return Style.from_dict({
            'prompt': '#00aa00 bold',
            'file-reference': '#0088ff',
            **self.config.style_overrides
        })
```

### 4. Output Management (output.py)

Rich console output with async support:

```python
# Global Rich console instance
console = Console(force_terminal=True, stderr=False)

async def display_banner():
    """Show application banner with ASCII art"""
    banner = """
    ╔═══════════════════════════════════════╗
    ║        🐟 TunaCode v0.0.51 🐟         ║
    ╚═══════════════════════════════════════╝
    """
    console.print(Panel(banner, style="cyan"))

async def display_context_window(state: StateManager):
    """Show context window usage"""
    tokens_used = state.estimate_tokens_in_messages()
    context_window = state.state.context_window
    percentage = (tokens_used / context_window) * 100

    # Color based on usage
    if percentage > 90:
        color = "red"
    elif percentage > 70:
        color = "yellow"
    else:
        color = "green"

    bar = create_progress_bar(percentage, width=20, color=color)
    console.print(f"Context: {bar} {tokens_used:,}/{context_window:,} tokens")

async def show_spinner(message: str = "Processing...") -> Live:
    """Display spinner with message"""
    spinner = Spinner("dots", text=message)
    live = Live(spinner, console=console, transient=True)
    live.start()
    return live

# Logging functions with consistent formatting
def print_info(message: str):
    console.print(f"[blue]ℹ[/blue] {message}")

def print_warning(message: str):
    console.print(f"[yellow]⚠[/yellow] {message}")

def print_error(message: str):
    console.print(f"[red]✗[/red] {message}")

def print_success(message: str):
    console.print(f"[green]✓[/green] {message}")
```

### 5. Panel System (panels.py)

Rich panels for structured output:

```python
def display_streaming_agent_panel(content: str, title: str = "Assistant"):
    """Streaming panel with Live updates"""
    panel = Panel(
        content,
        title=f"[cyan]{title}[/cyan]",
        border_style="cyan",
        padding=(1, 2),
        expand=False
    )

    # Use Live for progressive updates
    with Live(panel, console=console, refresh_per_second=10) as live:
        yield live  # Allow caller to update content

def display_help_panel(commands: Dict[str, List[CommandInfo]]):
    """Formatted help with categories"""
    help_content = []

    for category, cmds in commands.items():
        # Category header
        help_content.append(f"[bold cyan]{category}[/bold cyan]")

        # Command list with descriptions
        for cmd in cmds:
            aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
            help_content.append(
                f"  [green]{cmd.name}[/green]{aliases} - {cmd.description}"
            )
        help_content.append("")  # Spacing

    console.print(Panel(
        "\n".join(help_content),
        title="[bold]Available Commands[/bold]",
        border_style="blue"
    ))

def display_models_panel(models: List[ModelInfo]):
    """Model selection panel with pricing"""
    table = Table(title="Available Models", show_header=True)
    table.add_column("Provider", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Input $/1M", justify="right")
    table.add_column("Output $/1M", justify="right")

    for model in models:
        table.add_row(
            model.provider,
            model.name,
            f"${model.input_price:.2f}",
            f"${model.output_price:.2f}"
        )

    console.print(table)
```

### 6. Tool Confirmation UI (tool_ui.py)

Interactive tool approval dialogs:

```python
async def show_tool_confirmation(
    tool_name: str,
    confirmation_info: ConfirmationInfo,
    state_manager: StateManager
) -> bool:
    """Show tool confirmation dialog"""

    # Build confirmation panel
    content = [f"[bold]Tool:[/bold] {tool_name}"]
    content.append(f"[bold]Action:[/bold] {confirmation_info.short_description}")

    # Add details
    if confirmation_info.details:
        content.append("\n[bold]Details:[/bold]")
        for key, value in confirmation_info.details.items():
            content.append(f"  {key}: {value}")

    # Add preview (e.g., diff for updates)
    if confirmation_info.preview:
        content.append("\n[bold]Preview:[/bold]")
        if confirmation_info.syntax == "diff":
            # Syntax highlight diff
            highlighted = highlight_diff(confirmation_info.preview)
            content.append(highlighted)
        else:
            content.append(confirmation_info.preview)

    # Display panel
    console.print(Panel(
        "\n".join(content),
        title="[yellow]Tool Confirmation Required[/yellow]",
        border_style="yellow"
    ))

    # Get user choice
    choices = [
        "1. Yes (execute this tool)",
        "2. Yes, and don't ask again for this tool",
        "3. No (cancel and tell agent)"
    ]

    choice = await prompt_toolkit.prompt_async(
        "\n".join(choices) + "\n\nYour choice (1-3): "
    )

    # Handle response
    if choice == "2":
        state_manager.state.allowed_tools.add(tool_name)
        return True
    elif choice == "1":
        return True
    else:
        return False
```

### 7. Syntax Highlighting (lexers.py)

Custom lexers for prompt_toolkit:

```python
class FileReferenceLexer(Lexer):
    """Highlight @file references in input"""

    def lex_document(self, document: Document) -> Callable:
        def get_tokens(lineno: int) -> List[Tuple[int, str]]:
            line = document.lines[lineno]
            tokens = []

            # Find @file patterns
            for match in re.finditer(r'@([\w\-./\\]+)', line):
                start, end = match.span()
                # Before match
                if start > 0:
                    tokens.append((0, 'class:text'))
                # The match
                tokens.append((start, 'class:file-reference'))
                # After match
                if end < len(line):
                    tokens.append((end, 'class:text'))

            if not tokens:
                tokens = [(0, 'class:text')]

            return tokens

        return get_tokens
```

### 8. Key Bindings (keybindings.py)

Keyboard shortcut handlers:

```python
def create_key_bindings(state_manager: StateManager) -> KeyBindings:
    """Create application key bindings"""
    kb = KeyBindings()

    @kb.add('enter')
    def submit(event):
        """Submit on enter if input is complete"""
        buffer = event.current_buffer
        if buffer.complete_state:
            buffer.complete_state = None
        elif not buffer.text or is_complete(buffer.text):
            buffer.validate_and_handle()

    @kb.add('c-o')  # Ctrl+O
    @kb.add('escape', 'enter')  # Esc then Enter
    def newline(event):
        """Insert newline for multiline input"""
        event.current_buffer.insert_text('\n')

    # Double ESC handling
    escape_pressed_time = None

    @kb.add('escape')
    def escape_handler(event):
        nonlocal escape_pressed_time
        current_time = time.time()

        if escape_pressed_time and (current_time - escape_pressed_time) < 3:
            # Double ESC - cancel operation
            if state_manager.state.current_task:
                state_manager.state.task_cancelled = True
                state_manager.state.current_task.cancel()
            event.app.exit(exception=KeyboardInterrupt())
        else:
            escape_pressed_time = current_time

    return kb
```

### 9. Auto-completion (completers.py)

Smart completion for commands and files:

```python
class CommandCompleter(Completer):
    """Complete slash commands"""

    def __init__(self, registry: CommandRegistry):
        self.registry = registry

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor

        if text.startswith('/'):
            # Get matching commands
            prefix = text[1:]
            for cmd in self.registry.find_commands(prefix):
                yield Completion(
                    f'/{cmd.name}',
                    start_position=-len(text),
                    display=f'/{cmd.name}',
                    display_meta=cmd.description
                )

class FileReferenceCompleter(Completer):
    """Complete @file references"""

    def get_completions(self, document: Document, complete_event):
        # Find @file pattern
        match = re.search(r'@([\w\-./\\]*)$', document.text_before_cursor)
        if not match:
            return

        prefix = match.group(1)
        base_dir = Path.cwd()

        # Complete file paths
        for path in self._find_files(base_dir, prefix):
            yield Completion(
                f'@{path}',
                start_position=-len(match.group(0)),
                display=f'@{path}',
                display_meta='file'
            )
```

### 10. Decorators (decorators.py)

Async/sync compatibility:

```python
def create_sync_wrapper(async_func: Callable) -> Callable:
    """Create sync version of async function"""

    @functools.wraps(async_func)
    def wrapper(*args, **kwargs):
        # Check if we're in an event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in a loop, use thread
            future = asyncio.run_coroutine_threadsafe(
                async_func(*args, **kwargs),
                loop
            )
            return future.result()
        except RuntimeError:
            # No loop, create one
            return asyncio.run(async_func(*args, **kwargs))

    # Update docstring
    wrapper.__doc__ = f"Sync wrapper for {async_func.__name__}. {async_func.__doc__}"

    return wrapper
```

## UI Flow Patterns

### 1. Input Flow
```
User Types → Lexer Highlights → Completer Suggests → Validator Checks → Submit
```

### 2. Output Flow
```
Function Call → Console Format → Rich Render → Terminal Display
```

### 3. Confirmation Flow
```
Tool Request → Format Info → Display Panel → User Choice → Result
```

### 4. Streaming Flow
```
Agent Response → Token Updates → Live Panel → Progressive Display
```

## Styling and Theming

### Color Scheme
- **Primary**: Cyan (#00FFFF) - Headers, borders
- **Success**: Green (#00FF00) - Confirmations
- **Warning**: Yellow (#FFFF00) - Cautions
- **Error**: Red (#FF0000) - Errors
- **Info**: Blue (#0088FF) - Information
- **Prompt**: Green (#00AA00) - Input prompt

### Typography
- **Headers**: Bold + Color
- **Code**: Monospace with syntax highlighting
- **Emphasis**: Italic or underline
- **Dimmed**: Gray for less important info

## Best Practices

### 1. Async-First Design
```python
# Always prefer async versions
await info("Processing...")  # Good
print_info("Processing...")  # Only if necessary
```

### 2. Consistent Formatting
```python
# Use semantic functions
await error("Command failed")      # Good
console.print("[red]Failed[/red]") # Avoid
```

### 3. User Feedback
```python
# Always provide feedback
async with show_spinner("Loading..."):
    result = await long_operation()
await success("Operation completed!")
```

### 4. Error Handling
```python
try:
    await risky_operation()
except Exception as e:
    await error(f"Operation failed: {e}")
    # Provide actionable feedback
    await info("Try running with --debug for details")
```

## Performance Considerations

### 1. Streaming Updates
- Use `Live` with appropriate refresh rate
- Batch updates to reduce flicker
- Set `transient=True` for temporary displays

### 2. Large Output
- Paginate long lists
- Use tables for structured data
- Implement scrolling for very long content

### 3. Responsive Design
- Test on various terminal sizes
- Handle narrow terminals gracefully
- Provide text-only fallbacks

## Accessibility

### 1. Clear Indicators
- Use both color and symbols (✓, ✗, ℹ, ⚠)
- Provide text descriptions
- Support NO_COLOR environment variable

### 2. Keyboard Navigation
- All features keyboard accessible
- Clear keyboard shortcuts
- Escape sequences for cancellation

### 3. Screen Reader Support
- Semantic text output
- Descriptive messages
- Avoid ASCII art in critical paths

## Future Enhancements

1. **Theme System**: User-customizable colors
2. **Layout Manager**: Split panes, multiple views
3. **Progress Tracking**: Better long operation feedback
4. **Notification System**: Desktop notifications
5. **Plugin UI**: Extensible UI components
