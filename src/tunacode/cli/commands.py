"""Command system for TunaCode CLI."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from .. import utils
from ..configuration.models import ModelRegistry
from ..exceptions import ValidationError
from ..types import CommandArgs, CommandContext, CommandResult, ProcessRequestCallback
from ..ui import console as ui


class CommandCategory(Enum):
    """Categories for organizing commands."""

    SYSTEM = "system"
    NAVIGATION = "navigation"
    DEVELOPMENT = "development"
    MODEL = "model"
    DEBUG = "debug"


class Command(ABC):
    """Base class for all commands."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The primary name of the command."""
        pass

    @property
    @abstractmethod
    def aliases(self) -> CommandArgs:
        """Alternative names/aliases for the command."""
        pass

    @property
    def description(self) -> str:
        """Description of what the command does."""
        return ""

    @property
    def category(self) -> CommandCategory:
        """Category this command belongs to."""
        return CommandCategory.SYSTEM

    @abstractmethod
    async def execute(self, args: CommandArgs, context: CommandContext) -> CommandResult:
        """
        Execute the command.

        Args:
            args: Command arguments (excluding the command name)
            context: Execution context with state and config

        Returns:
            Command-specific return value
        """
        pass


@dataclass
class CommandSpec:
    """Specification for a command's metadata."""

    name: str
    aliases: List[str]
    description: str
    category: CommandCategory = CommandCategory.SYSTEM


class SimpleCommand(Command):
    """Base class for simple commands without complex logic."""

    def __init__(self, spec: CommandSpec):
        self.spec = spec

    @property
    def name(self) -> str:
        """The primary name of the command."""
        return self.spec.name

    @property
    def aliases(self) -> CommandArgs:
        """Alternative names/aliases for the command."""
        return self.spec.aliases

    @property
    def description(self) -> str:
        """Description of what the command does."""
        return self.spec.description

    @property
    def category(self) -> CommandCategory:
        """Category this command belongs to."""
        return self.spec.category


class YoloCommand(SimpleCommand):
    """Toggle YOLO mode (skip confirmations)."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="yolo",
                aliases=["/yolo"],
                description="Toggle YOLO mode (skip tool confirmations)",
                category=CommandCategory.DEVELOPMENT,
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        state = context.state_manager.session
        state.yolo = not state.yolo
        if state.yolo:
            await ui.success("Ooh shit, its YOLO time!\n")
        else:
            await ui.info("Pfft, boring...\n")


class DumpCommand(SimpleCommand):
    """Dump message history."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="dump",
                aliases=["/dump"],
                description="Dump the current message history",
                category=CommandCategory.DEBUG,
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await ui.dump_messages(context.state_manager.session.messages)


class ThoughtsCommand(SimpleCommand):
    """Toggle display of agent thoughts."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="thoughts",
                aliases=["/thoughts"],
                description="Show or hide agent thought messages",
                category=CommandCategory.DEBUG,
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        state = context.state_manager.session
        if args:
            arg = args[0].lower()
            if arg in {"on", "1", "true"}:
                state.show_thoughts = True
            elif arg in {"off", "0", "false"}:
                state.show_thoughts = False
            else:
                await ui.error("Usage: /thoughts [on|off]")
                return
        else:
            state.show_thoughts = not state.show_thoughts
        status = "ON" if state.show_thoughts else "OFF"
        await ui.success(f"Thought display {status}")


class IterationsCommand(SimpleCommand):
    """Configure maximum agent iterations for ReAct reasoning."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="iterations",
                aliases=["/iterations"],
                description="Set maximum agent iterations for complex reasoning",
                category=CommandCategory.DEBUG,
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        state = context.state_manager.session
        if args:
            try:
                new_limit = int(args[0])
                if new_limit < 1 or new_limit > 50:
                    await ui.error("Iterations must be between 1 and 50")
                    return
                
                # Update the user config
                if "settings" not in state.user_config:
                    state.user_config["settings"] = {}
                state.user_config["settings"]["max_iterations"] = new_limit
                
                await ui.success(f"Maximum iterations set to {new_limit}")
                await ui.muted("Higher values allow more complex reasoning but may be slower")
            except ValueError:
                await ui.error("Please provide a valid number")
        else:
            current = state.user_config.get("settings", {}).get("max_iterations", 15)
            await ui.info(f"Current maximum iterations: {current}")
            await ui.muted("Usage: /iterations <number> (1-50)")


class ClearCommand(SimpleCommand):
    """Clear screen and message history."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="clear",
                aliases=["/clear"],
                description="Clear the screen and message history",
                category=CommandCategory.NAVIGATION,
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        # Patch any orphaned tool calls before clearing
        from tunacode.core.agents.main import patch_tool_messages
        patch_tool_messages("Conversation cleared", context.state_manager)
        
        await ui.clear()
        context.state_manager.session.messages = []
        await ui.success("Message history cleared")


class FixCommand(SimpleCommand):
    """Fix orphaned tool calls that cause API errors."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="fix",
                aliases=["/fix"],
                description="Fix orphaned tool calls causing API errors",
                category=CommandCategory.DEBUG,
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        from tunacode.core.agents.main import patch_tool_messages
        
        # Count current messages
        before_count = len(context.state_manager.session.messages)
        
        # Patch orphaned tool calls
        patch_tool_messages("Tool call resolved by /fix command", context.state_manager)
        
        # Count after patching
        after_count = len(context.state_manager.session.messages)
        patched_count = after_count - before_count
        
        if patched_count > 0:
            await ui.success(f"Fixed {patched_count} orphaned tool call(s)")
            await ui.muted("You can now continue the conversation normally")
        else:
            await ui.info("No orphaned tool calls found")


class ParseToolsCommand(SimpleCommand):
    """Parse and execute JSON tool calls from the last response."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="parsetools",
                aliases=["/parsetools"],
                description="Parse JSON tool calls from last response when structured calling fails",
                category=CommandCategory.DEBUG,
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        from tunacode.core.agents.main import extract_and_execute_tool_calls
        
        # Find the last model response in messages
        messages = context.state_manager.session.messages
        if not messages:
            await ui.error("No message history found")
            return
        
        # Look for the most recent response with text content
        found_content = False
        for msg in reversed(messages):
            if hasattr(msg, 'parts'):
                for part in msg.parts:
                    if hasattr(part, 'content') and isinstance(part.content, str):
                        # Create tool callback
                        from tunacode.cli.repl import _tool_handler
                        def tool_callback_with_state(part, node):
                            return _tool_handler(part, node, context.state_manager)
                        
                        try:
                            await extract_and_execute_tool_calls(
                                part.content, 
                                tool_callback_with_state, 
                                context.state_manager
                            )
                            await ui.success("JSON tool parsing completed")
                            found_content = True
                            return
                        except Exception as e:
                            await ui.error(f"Failed to parse tools: {str(e)}")
                            return
        
        if not found_content:
            await ui.error("No parseable content found in recent messages")


class RefreshConfigCommand(SimpleCommand):
    """Refresh configuration from defaults."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="refresh",
                aliases=["/refresh"],
                description="Refresh configuration from defaults (useful after updates)",
                category=CommandCategory.SYSTEM,
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        from tunacode.configuration.defaults import DEFAULT_USER_CONFIG
        
        # Update current session config with latest defaults
        for key, value in DEFAULT_USER_CONFIG.items():
            if key not in context.state_manager.session.user_config:
                context.state_manager.session.user_config[key] = value
            elif isinstance(value, dict):
                # Merge dict values, preserving user overrides
                for subkey, subvalue in value.items():
                    if subkey not in context.state_manager.session.user_config[key]:
                        context.state_manager.session.user_config[key][subkey] = subvalue
        
        # Show updated max_iterations
        max_iterations = context.state_manager.session.user_config.get("settings", {}).get("max_iterations", 20)
        await ui.success(f"Configuration refreshed - max iterations: {max_iterations}")


class TunaCodeCommand(SimpleCommand):
    """Use BM25 to inspect the codebase and read relevant files."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="tunaCode",
                aliases=["/tunaCode"],
                description="Scan repo with BM25 and display key files",
                category=CommandCategory.DEVELOPMENT,
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        from pathlib import Path

        from tunacode.constants import UI_COLORS
        from tunacode.utils.file_utils import DotDict

        from ..tools.read_file import read_file
        from ..utils.bm25 import BM25, tokenize
        from ..utils.text_utils import ext_to_lang

        colors = DotDict(UI_COLORS)

        query = " ".join(args) if args else "overview"
        await ui.info("Building BM25 index of repository")

        docs: List[str] = []
        paths: List[Path] = []
        exts = {".py", ".js", ".ts", ".java", ".c", ".cpp", ".md", ".txt"}
        for path in Path(".").rglob("*"):
            if path.is_file() and path.suffix in exts:
                try:
                    docs.append(path.read_text(encoding="utf-8"))
                    paths.append(path)
                except Exception:
                    continue

        if not docs:
            await ui.error("No files found to index")
            return

        bm25 = BM25(docs)
        scores = bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]

        for idx in ranked:
            file_path = paths[idx]
            content = await read_file(str(file_path))
            lang = ext_to_lang(str(file_path))
            await ui.panel(
                str(file_path),
                f"```{lang}\n{content}\n```",
                border_style=colors.muted,
            )


class HelpCommand(SimpleCommand):
    """Show help information."""

    def __init__(self, command_registry=None):
        super().__init__(
            CommandSpec(
                name="help",
                aliases=["/help"],
                description="Show help information",
                category=CommandCategory.SYSTEM,
            )
        )
        self._command_registry = command_registry

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await ui.help(self._command_registry)


class BranchCommand(SimpleCommand):
    """Create and switch to a new git branch."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="branch",
                aliases=["/branch"],
                description="Create and switch to a new git branch",
                category=CommandCategory.DEVELOPMENT,
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        import os
        import subprocess

        if not args:
            await ui.error("Usage: /branch <branch-name>")
            return

        if not os.path.exists(".git"):
            await ui.error("Not a git repository")
            return

        branch_name = args[0]

        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            await ui.success(f"Switched to new branch '{branch_name}'")
        except subprocess.TimeoutExpired:
            await ui.error("Git command timed out")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            await ui.error(f"Git error: {error_msg}")
        except FileNotFoundError:
            await ui.error("Git executable not found")


class CompactCommand(SimpleCommand):
    """Compact conversation context."""

    def __init__(self, process_request_callback: Optional[ProcessRequestCallback] = None):
        super().__init__(
            CommandSpec(
                name="compact",
                aliases=["/compact"],
                description="Summarize and compact the conversation history",
                category=CommandCategory.SYSTEM,
            )
        )
        self._process_request = process_request_callback

    async def execute(self, args: List[str], context: CommandContext) -> None:
        # Use the injected callback or get it from context
        process_request = self._process_request or context.process_request

        if not process_request:
            await ui.error("Compact command not available - process_request not configured")
            return

        # Get the current agent, create a summary of context, and trim message history
        await process_request(
            "Summarize the conversation so far", context.state_manager, output=False
        )
        await ui.success("Context history has been summarized and truncated.")
        context.state_manager.session.messages = context.state_manager.session.messages[-2:]


class ModelCommand(SimpleCommand):
    """Manage model selection."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="model",
                aliases=["/model"],
                description="Switch model (e.g., /model gpt-4 or /model openai:gpt-4)",
                category=CommandCategory.MODEL,
            )
        )

    async def execute(self, args: CommandArgs, context: CommandContext) -> Optional[str]:
        if not args:
            # No arguments - show current model
            current_model = context.state_manager.session.current_model
            await ui.info(f"Current model: {current_model}")
            await ui.muted("Usage: /model <provider:model-name> [default]")
            await ui.muted("Example: /model openai:gpt-4.1")
            return None

        # Get the model name from args
        model_name = args[0]

        # Check if provider prefix is present
        if ":" not in model_name:
            await ui.error("Model name must include provider prefix")
            await ui.muted("Format: provider:model-name")
            await ui.muted(
                "Examples: openai:gpt-4.1, anthropic:claude-3-opus, google-gla:gemini-2.0-flash"
            )
            return None

        # No validation - user is responsible for correct model names
        await ui.warning("Model set without validation - verify the model name is correct")

        # Set the model
        context.state_manager.session.current_model = model_name

        # Check if setting as default
        if len(args) > 1 and args[1] == "default":
            utils.user_configuration.set_default_model(model_name, context.state_manager)
            await ui.muted("Updating default model")
            return "restart"
        else:
            # Show success message with the new model
            await ui.success(f"Switched to model: {model_name}")
            return None


@dataclass
class CommandDependencies:
    """Container for command dependencies."""

    process_request_callback: Optional[ProcessRequestCallback] = None
    command_registry: Optional[Any] = None  # Reference to the registry itself


class CommandFactory:
    """Factory for creating commands with proper dependency injection."""

    def __init__(self, dependencies: Optional[CommandDependencies] = None):
        self.dependencies = dependencies or CommandDependencies()

    def create_command(self, command_class: Type[Command]) -> Command:
        """Create a command instance with proper dependencies."""
        # Special handling for commands that need dependencies
        if command_class == CompactCommand:
            return CompactCommand(self.dependencies.process_request_callback)
        elif command_class == HelpCommand:
            return HelpCommand(self.dependencies.command_registry)

        # Default creation for commands without dependencies
        return command_class()

    def update_dependencies(self, **kwargs) -> None:
        """Update factory dependencies."""
        for key, value in kwargs.items():
            if hasattr(self.dependencies, key):
                setattr(self.dependencies, key, value)


class CommandRegistry:
    """Registry for managing commands with auto-discovery and categories."""

    def __init__(self, factory: Optional[CommandFactory] = None):
        self._commands: Dict[str, Command] = {}
        self._categories: Dict[CommandCategory, List[Command]] = {
            category: [] for category in CommandCategory
        }
        self._factory = factory or CommandFactory()
        self._discovered = False

        # Set registry reference in factory dependencies
        self._factory.update_dependencies(command_registry=self)

    def register(self, command: Command) -> None:
        """Register a command and its aliases."""
        # Register by primary name
        self._commands[command.name] = command

        # Register all aliases
        for alias in command.aliases:
            self._commands[alias.lower()] = command

        # Add to category (remove existing instance first to prevent duplicates)
        category_commands = self._categories[command.category]
        # Remove any existing instance of this command class
        self._categories[command.category] = [
            cmd for cmd in category_commands if cmd.__class__ != command.__class__
        ]
        # Add the new instance
        self._categories[command.category].append(command)

    def register_command_class(self, command_class: Type[Command]) -> None:
        """Register a command class using the factory."""
        command = self._factory.create_command(command_class)
        self.register(command)

    def discover_commands(self) -> None:
        """Auto-discover and register all command classes."""
        if self._discovered:
            return

        # List of all command classes to register
        command_classes = [
            YoloCommand,
            DumpCommand,
            ThoughtsCommand,
            IterationsCommand,
            ClearCommand,
            FixCommand,
            ParseToolsCommand,
            RefreshConfigCommand,
            HelpCommand,
            BranchCommand,
            # TunaCodeCommand,  # TODO: Temporarily disabled
            CompactCommand,
            ModelCommand,
        ]

        # Register all discovered commands
        for command_class in command_classes:
            self.register_command_class(command_class)

        self._discovered = True

    def register_all_default_commands(self) -> None:
        """Register all default commands (backward compatibility)."""
        self.discover_commands()

    def set_process_request_callback(self, callback: ProcessRequestCallback) -> None:
        """Set the process_request callback for commands that need it."""
        # Only update if callback has changed
        if self._factory.dependencies.process_request_callback == callback:
            return

        self._factory.update_dependencies(process_request_callback=callback)

        # Re-register CompactCommand with new dependency if already registered
        if "compact" in self._commands:
            self.register_command_class(CompactCommand)

    async def execute(self, command_text: str, context: CommandContext) -> Any:
        """
        Execute a command.

        Args:
            command_text: The full command text
            context: Execution context

        Returns:
            Command-specific return value, or None if command not found

        Raises:
            ValidationError: If command is not found or empty
        """
        # Ensure commands are discovered
        self.discover_commands()

        parts = command_text.split()
        if not parts:
            raise ValidationError("Empty command")

        command_name = parts[0].lower()
        args = parts[1:]

        # First try exact match
        if command_name in self._commands:
            command = self._commands[command_name]
            return await command.execute(args, context)

        # Try partial matching
        matches = self.find_matching_commands(command_name)

        if not matches:
            raise ValidationError(f"Unknown command: {command_name}")
        elif len(matches) == 1:
            # Unambiguous match
            command = self._commands[matches[0]]
            return await command.execute(args, context)
        else:
            # Ambiguous - show possibilities
            raise ValidationError(
                f"Ambiguous command '{command_name}'. Did you mean: {', '.join(sorted(set(matches)))}?"
            )

    def find_matching_commands(self, partial_command: str) -> List[str]:
        """
        Find all commands that start with the given partial command.

        Args:
            partial_command: The partial command to match

        Returns:
            List of matching command names
        """
        self.discover_commands()
        partial = partial_command.lower()
        return [cmd for cmd in self._commands.keys() if cmd.startswith(partial)]

    def is_command(self, text: str) -> bool:
        """Check if text starts with a registered command (supports partial matching)."""
        if not text:
            return False

        parts = text.split()
        if not parts:
            return False

        command_name = parts[0].lower()

        # Check exact match first
        if command_name in self._commands:
            return True

        # Check partial match
        return len(self.find_matching_commands(command_name)) > 0

    def get_command_names(self) -> CommandArgs:
        """Get all registered command names (including aliases)."""
        self.discover_commands()
        return sorted(self._commands.keys())

    def get_commands_by_category(self, category: CommandCategory) -> List[Command]:
        """Get all commands in a specific category."""
        self.discover_commands()
        return self._categories.get(category, [])

    def get_all_categories(self) -> Dict[CommandCategory, List[Command]]:
        """Get all commands organized by category."""
        self.discover_commands()
        return self._categories.copy()
