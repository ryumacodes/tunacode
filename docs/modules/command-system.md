<!-- This document explains the command registry, all slash commands (/help, /model, /yolo, etc.), and how to create new commands -->

# TunaCode Command System Documentation

## Overview

The TunaCode command system provides a flexible, extensible framework for implementing slash commands. Built on a registry pattern with auto-discovery, it supports command aliases, partial matching, and dynamic command creation through templates.

## Architecture

### Command Hierarchy

```
┌─────────────────────────────────────────┐
│         Command Registry                 │
│    (Central command management)          │
└─────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
┌─────────────┐ ┌────────────┐ ┌─────────────┐
│Base Classes │ │Command Impl│ │  Template   │
│(Command ABC)│ │(Concrete)  │ │  Shortcuts  │
└─────────────┘ └────────────┘ └─────────────┘
```

## Base Classes (commands/base.py)

### Command Abstract Base Class

```python
class Command(ABC):
    """Base interface for all commands"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Primary command name"""
        pass

    @property
    def aliases(self) -> List[str]:
        """Alternative names for the command"""
        return []

    @property
    @abstractmethod
    def description(self) -> str:
        """Command description for help"""
        pass

    @property
    @abstractmethod
    def category(self) -> CommandCategory:
        """Command category for organization"""
        pass

    @abstractmethod
    def matches(self, command: str) -> bool:
        """Check if command matches this handler"""
        pass

    @abstractmethod
    async def execute(self, args: str, state: StateManager) -> None:
        """Execute the command with arguments"""
        pass
```

### Command Categories

```python
class CommandCategory(Enum):
    """Command categorization for help display"""
    SYSTEM = "System"
    NAVIGATION = "Navigation"
    DEVELOPMENT = "Development"
    MODEL = "Model"
    DEBUG = "Debug"
    CONVERSATION = "Conversation"
    TEMPLATES = "Templates"
    TASKS = "Tasks"
```

### SimpleCommand Base

```python
class SimpleCommand(Command):
    """Base class for simple command implementations"""

    def __init__(self, process_request_callback=None):
        self.process_request_callback = process_request_callback

    def matches(self, command: str) -> bool:
        """Default matching: exact match or alias"""
        return command == self.name or command in self.aliases
```

## Command Registry (commands/registry.py)

The registry manages command discovery and execution:

### Core Registry

```python
class CommandRegistry:
    """Central command management system"""

    def __init__(self, ui: UIProtocol, process_request_callback=None):
        self.ui = ui
        self.process_request_callback = process_request_callback
        self._commands: List[Command] = []
        self._discover_commands()

    def _discover_commands(self):
        """Auto-discover command implementations"""
        # Import all implementation modules
        implementations_dir = Path(__file__).parent / "implementations"
        for module_file in implementations_dir.glob("*.py"):
            if module_file.name.startswith("_"):
                continue

            module_name = f"tunacode.cli.commands.implementations.{module_file.stem}"
            module = importlib.import_module(module_name)

            # Find command factory methods (@property returning Command)
            for name in dir(module):
                if name.startswith("_"):
                    continue

                attr = getattr(module, name)
                if isinstance(attr, property):
                    try:
                        # Create command instance via factory
                        cmd_instance = attr.fget(self)
                        if isinstance(cmd_instance, Command):
                            self._commands.append(cmd_instance)
                    except:
                        pass
```

### Command Execution

```python
async def execute(self, command_str: str, state: StateManager) -> bool:
    """Execute a command string"""

    # Parse command and arguments
    parts = command_str.split(maxsplit=1)
    command = parts[0]
    args = parts[1] if len(parts) > 1 else ""

    # Remove leading slash if present
    if command.startswith("/"):
        command = command[1:]

    # Find matching command
    for cmd in self._commands:
        if cmd.matches(command):
            try:
                await cmd.execute(args, state)
                return True
            except Exception as e:
                await self.ui.error(f"Command error: {e}")
                return False

    # Check template shortcuts
    if self._handle_template_shortcut(command, args, state):
        return True

    # No match found
    await self.ui.error(f"Unknown command: /{command}")
    return False
```

### Partial Matching

```python
def find_commands(self, prefix: str) -> List[CommandInfo]:
    """Find commands matching prefix"""
    matches = []

    for cmd in self._commands:
        # Check main name
        if cmd.name.startswith(prefix):
            matches.append(CommandInfo(
                name=cmd.name,
                aliases=cmd.aliases,
                description=cmd.description,
                category=cmd.category
            ))
        # Check aliases
        else:
            for alias in cmd.aliases:
                if alias.startswith(prefix):
                    matches.append(CommandInfo(
                        name=cmd.name,
                        aliases=cmd.aliases,
                        description=cmd.description,
                        category=cmd.category
                    ))
                    break

    return matches
```

## Command Implementations

### 1. System Commands (implementations/system.py)

#### HelpCommand
```python
@property
def help_command(self) -> Command:
    """Factory for help command"""

    class HelpCommand(SimpleCommand):
        name = "help"
        aliases = ["h", "?"]
        description = "Show available commands"
        category = CommandCategory.SYSTEM

        async def execute(self, args: str, state: StateManager) -> None:
            # Get commands grouped by category
            commands_by_category = defaultdict(list)

            for cmd in self.registry._commands:
                commands_by_category[cmd.category.value].append(
                    CommandInfo(cmd.name, cmd.aliases, cmd.description)
                )

            # Display formatted help
            await display_help_panel(dict(commands_by_category))

    return HelpCommand(self.process_request_callback)
```

#### ClearCommand
```python
@property
def clear_command(self) -> Command:
    """Factory for clear command"""

    class ClearCommand(SimpleCommand):
        name = "clear"
        aliases = ["cls"]
        description = "Clear the screen"
        category = CommandCategory.SYSTEM

        async def execute(self, args: str, state: StateManager) -> None:
            # Clear terminal
            os.system('clear' if os.name != 'nt' else 'cls')

            # Reset message history if requested
            if args.strip() == "all":
                state.state.messages = []
                await self.ui.info("Message history cleared")

            # Redisplay banner
            await display_banner()

    return ClearCommand()
```

#### UpdateCommand
```python
@property
def update_command(self) -> Command:
    """Factory for update command"""

    class UpdateCommand(SimpleCommand):
        name = "update"
        description = "Update TunaCode to latest version"
        category = CommandCategory.SYSTEM

        async def execute(self, args: str, state: StateManager) -> None:
            # Detect installation method
            in_venv = sys.prefix != sys.base_prefix
            tunacode_path = shutil.which("tunacode")

            if tunacode_path and "pipx" in tunacode_path:
                # pipx installation
                cmd = "pipx upgrade tunacode-cli"
            elif in_venv:
                # Virtual environment
                cmd = "pip install --upgrade tunacode-cli"
            else:
                # Global pip
                cmd = "pip install --upgrade --user tunacode-cli"

            await self.ui.info(f"Running: {cmd}")

            # Execute update
            result = subprocess.run(cmd.split(), capture_output=True, text=True)

            if result.returncode == 0:
                await self.ui.success("Update completed! Please restart TunaCode.")
            else:
                await self.ui.error(f"Update failed: {result.stderr}")

    return UpdateCommand()
```

### 2. Model Commands (implementations/model.py)

```python
@property
def model_command(self) -> Command:
    """Factory for model command"""

    class ModelCommand(SimpleCommand):
        name = "model"
        aliases = ["m"]
        description = "Switch AI model"
        category = CommandCategory.MODEL

        async def execute(self, args: str, state: StateManager) -> None:
            if not args:
                # Show current model
                current = state.get_model()
                await self.ui.info(f"Current model: {current}")

                # Show available models
                models = get_available_models()
                await display_models_panel(models)
                return

            # Parse provider:model format
            if ":" not in args:
                await self.ui.error("Format: /model provider:model-name")
                return

            provider, model = args.split(":", 1)

            # Validate provider
            if provider not in SUPPORTED_PROVIDERS:
                await self.ui.warning(f"Unknown provider: {provider}")

            # Set new model
            new_model = f"{provider}:{model}"
            state.set_model(new_model)

            # Update config
            state.update_config({"default_model": new_model})

            await self.ui.success(f"Model changed to: {new_model}")

    return ModelCommand()
```

### 3. Development Commands (implementations/development.py)

#### BranchCommand
```python
@property
def branch_command(self) -> Command:
    """Factory for branch command"""

    class BranchCommand(SimpleCommand):
        name = "branch"
        aliases = ["b"]
        description = "Create and switch git branch"
        category = CommandCategory.DEVELOPMENT

        async def execute(self, args: str, state: StateManager) -> None:
            if not args:
                await self.ui.error("Usage: /branch <branch-name>")
                return

            branch_name = args.strip()

            # Check if in git repo
            if not Path(".git").exists():
                await self.ui.error("Not in a git repository")
                return

            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                await self.ui.warning("You have uncommitted changes!")
                response = await prompt_async("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    return

            # Create and switch branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                await self.ui.success(f"Created and switched to branch: {branch_name}")
            else:
                await self.ui.error(f"Failed: {result.stderr}")

    return BranchCommand()
```

### 4. Debug Commands (implementations/debug.py)

#### YoloCommand
```python
@property
def yolo_command(self) -> Command:
    """Factory for yolo command"""

    class YoloCommand(SimpleCommand):
        name = "yolo"
        description = "Toggle confirmation prompts"
        category = CommandCategory.DEBUG

        async def execute(self, args: str, state: StateManager) -> None:
            # Toggle YOLO mode
            state.state.yolo_mode = not state.state.yolo_mode

            status = "enabled" if state.state.yolo_mode else "disabled"
            emoji = "🚀" if state.state.yolo_mode else "🔒"

            await self.ui.info(f"{emoji} YOLO mode {status}")

            if state.state.yolo_mode:
                await self.ui.warning(
                    "⚠️  All tool confirmations disabled! "
                    "Tools will execute without asking."
                )

    return YoloCommand()
```

#### ThoughtsCommand
```python
@property
def thoughts_command(self) -> Command:
    """Factory for thoughts command"""

    class ThoughtsCommand(SimpleCommand):
        name = "thoughts"
        description = "Toggle agent thought visibility"
        category = CommandCategory.DEBUG

        async def execute(self, args: str, state: StateManager) -> None:
            # Toggle thoughts display
            state.state.show_thoughts = not state.state.show_thoughts

            status = "visible" if state.state.show_thoughts else "hidden"

            await self.ui.info(f"Agent thoughts are now {status}")

            if state.state.show_thoughts:
                await self.ui.info(
                    "You'll see parallel tool execution details "
                    "and agent reasoning"
                )

    return ThoughtsCommand()
```

### 5. Todo Commands (implementations/todo.py)

```python
@property
def todo_command(self) -> Command:
    """Factory for todo command"""

    class TodoCommand(SimpleCommand):
        name = "todo"
        aliases = ["t", "task"]
        description = "Manage todo list"
        category = CommandCategory.TASKS

        async def execute(self, args: str, state: StateManager) -> None:
            # Parse subcommand
            parts = args.split(maxsplit=1)
            subcommand = parts[0] if parts else "list"
            subargs = parts[1] if len(parts) > 1 else ""

            if subcommand == "list":
                await self._list_todos(state)
            elif subcommand == "add":
                await self._add_todo(subargs, state)
            elif subcommand == "done":
                await self._mark_done(subargs, state)
            elif subcommand == "update":
                await self._update_todo(subargs, state)
            elif subcommand == "remove":
                await self._remove_todo(subargs, state)
            elif subcommand == "clear":
                await self._clear_todos(state)
            else:
                await self.ui.error(f"Unknown subcommand: {subcommand}")

        async def _list_todos(self, state: StateManager):
            """Display todos in a rich table"""
            todos = state.get_todos()

            if not todos:
                await self.ui.info("No todos yet. Use /todo add <task>")
                return

            # Create rich table
            table = Table(title="Todo List", show_header=True)
            table.add_column("ID", style="cyan", width=4)
            table.add_column("Task", style="white")
            table.add_column("Priority", justify="center", width=8)
            table.add_column("Created", style="dim", width=10)

            for todo in todos:
                # Priority styling
                priority_style = {
                    "high": "red bold",
                    "medium": "yellow",
                    "low": "green"
                }.get(todo.priority, "white")

                table.add_row(
                    str(todo.id),
                    todo.content,
                    f"[{priority_style}]{todo.priority}[/{priority_style}]",
                    todo.created_at.strftime("%Y-%m-%d")
                )

            console.print(table)

    return TodoCommand()
```

### 6. Template Commands (implementations/template.py)

```python
@property
def template_command(self) -> Command:
    """Factory for template command"""

    class TemplateCommand(SimpleCommand):
        name = "template"
        aliases = ["tmpl"]
        description = "Manage prompt templates"
        category = CommandCategory.TEMPLATES

        async def execute(self, args: str, state: StateManager) -> None:
            parts = args.split(maxsplit=1)
            subcommand = parts[0] if parts else "list"

            if subcommand == "list":
                await self._list_templates()
            elif subcommand == "load":
                if len(parts) < 2:
                    await self.ui.error("Usage: /template load <name>")
                    return
                await self._load_template(parts[1], state)
            elif subcommand == "create":
                await self._create_template()
            elif subcommand == "clear":
                await self._clear_template(state)

        async def _load_template(self, name: str, state: StateManager):
            """Load and activate a template"""
            loader = TemplateLoader()

            try:
                template = loader.load(name)

                # Set allowed tools
                state.state.allowed_tools = set(template.allowed_tools)

                # Store template
                state.state.active_template = template

                await self.ui.success(f"Loaded template: {template.name}")
                await self.ui.info(f"Pre-approved tools: {', '.join(template.allowed_tools)}")

                # Process template prompt if callback available
                if self.process_request_callback and template.prompt:
                    await self.process_request_callback(
                        template.prompt,
                        state,
                        is_template=True
                    )

            except FileNotFoundError:
                await self.ui.error(f"Template not found: {name}")

    return TemplateCommand()
```

## Template Shortcuts (template_shortcut.py)

Dynamic command creation from templates:

### TemplateShortcutCommand

```python
class TemplateShortcutCommand(Command):
    """Dynamic command created from template shortcut"""

    def __init__(self,
                 shortcut: str,
                 template_name: str,
                 template_prompt: str,
                 allowed_tools: List[str],
                 process_request_callback):
        self.shortcut = shortcut
        self.template_name = template_name
        self.template_prompt = template_prompt
        self.allowed_tools = allowed_tools
        self.process_request_callback = process_request_callback

    @property
    def name(self) -> str:
        return self.shortcut

    @property
    def description(self) -> str:
        return f"Template shortcut for {self.template_name}"

    @property
    def category(self) -> CommandCategory:
        return CommandCategory.TEMPLATES

    def matches(self, command: str) -> bool:
        return command == self.shortcut

    async def execute(self, args: str, state: StateManager) -> None:
        # Pre-approve tools
        state.state.allowed_tools.update(self.allowed_tools)

        # Substitute arguments in prompt
        prompt = self.template_prompt
        if "$ARGUMENTS" in prompt and args:
            prompt = prompt.replace("$ARGUMENTS", args)

        # Process via callback
        if self.process_request_callback:
            await self.ui.info(f"Activating template: {self.template_name}")
            await self.process_request_callback(
                prompt,
                state,
                is_template=True
            )
```

### Integration with Registry

```python
def _handle_template_shortcut(self, command: str, args: str, state: StateManager) -> bool:
    """Check if command is a template shortcut"""

    loader = TemplateLoader()
    templates = loader.list_templates()

    for template in templates:
        if template.shortcuts and command in template.shortcuts:
            # Create dynamic command
            shortcut_cmd = TemplateShortcutCommand(
                shortcut=command,
                template_name=template.name,
                template_prompt=template.prompt,
                allowed_tools=template.allowed_tools,
                process_request_callback=self.process_request_callback
            )

            # Execute it
            asyncio.create_task(shortcut_cmd.execute(args, state))
            return True

    return False
```

## Best Practices

### 1. Command Design

```python
# Good: Clear, descriptive command
class StatusCommand(SimpleCommand):
    name = "status"
    aliases = ["s", "stat"]
    description = "Show current session status"
    category = CommandCategory.SYSTEM

# Bad: Vague command
class DoCommand(SimpleCommand):
    name = "do"
    description = "Do something"  # Too vague!
```

### 2. Error Handling

```python
async def execute(self, args: str, state: StateManager) -> None:
    try:
        # Validate arguments
        if not args:
            await self.ui.error("Usage: /command <argument>")
            return

        # Perform operation
        result = await self.perform_operation(args)

        # Provide feedback
        await self.ui.success(f"Operation completed: {result}")

    except ValueError as e:
        await self.ui.error(f"Invalid input: {e}")
    except Exception as e:
        await self.ui.error(f"Command failed: {e}")
        # Log for debugging
        logger.exception("Command execution failed")
```

### 3. State Management

```python
async def execute(self, args: str, state: StateManager) -> None:
    # Read state
    current_value = state.state.some_setting

    # Modify state
    state.state.some_setting = new_value

    # Persist if needed
    if should_persist:
        state.update_config({"some_setting": new_value})
```

### 4. User Feedback

```python
async def execute(self, args: str, state: StateManager) -> None:
    # Immediate acknowledgment
    await self.ui.info("Processing your request...")

    # Progress for long operations
    async with show_spinner("Analyzing..."):
        result = await long_operation()

    # Clear result
    await self.ui.success("Analysis complete!")

    # Detailed output if needed
    if verbose:
        await display_result_panel(result)
```

## Creating New Commands

### Step 1: Create Implementation File

Create `implementations/mycommand.py`:

```python
from tunacode.cli.commands.base import Command, SimpleCommand, CommandCategory
from tunacode.ui.console import info, error, success

class MyNewCommand(SimpleCommand):
    """Implementation of my new command"""

    @property
    def name(self) -> str:
        return "mynew"

    @property
    def aliases(self) -> List[str]:
        return ["mn", "new"]

    @property
    def description(self) -> str:
        return "Does something new and useful"

    @property
    def category(self) -> CommandCategory:
        return CommandCategory.DEVELOPMENT

    async def execute(self, args: str, state: StateManager) -> None:
        # Implementation here
        await info(f"Executing with args: {args}")

# Factory method for registry
@property
def mynew_command(self) -> Command:
    return MyNewCommand(self.process_request_callback)
```

### Step 2: Test Command

```python
# Command will be auto-discovered
# Test in REPL:
# /mynew test arguments
# /mn test  # Using alias
# /new test # Another alias
```

## Performance Considerations

### 1. Lazy Loading
- Commands are discovered once at startup
- Modules imported only when needed
- Templates loaded on demand

### 2. Async Execution
- All commands execute asynchronously
- Long operations use background tasks
- UI remains responsive

### 3. Caching
- Command instances cached in registry
- Template shortcuts cached after first use
- Configuration cached in state

## Future Enhancements

1. **Command Pipelines**: Chain commands together
2. **Command History**: Persistent command history
3. **Command Macros**: Record and replay command sequences
4. **Plugin Commands**: Load commands from external packages
5. **Command Permissions**: Role-based command access
