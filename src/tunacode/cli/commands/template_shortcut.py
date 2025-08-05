"""Template shortcut command base class for dynamic template-based commands."""

from typing import List, Optional

from ...templates.loader import Template
from ...types import CommandArgs, CommandContext
from ...ui import console as ui
from .base import Command, CommandCategory


class TemplateShortcutCommand(Command):
    """Base class for template shortcut commands that auto-load templates and process arguments."""

    def __init__(self, template: Template):
        """Initialize with a specific template.

        Args:
            template: The template instance this shortcut represents
        """
        self.template = template
        self._name = template.shortcut.lstrip("/") if template.shortcut else template.name
        self._aliases = [template.shortcut] if template.shortcut else []
        self._description = f"{template.description} (Template: {template.name})"

    @property
    def name(self) -> str:
        """The primary name of the command."""
        return self._name

    @property
    def aliases(self) -> List[str]:
        """Alternative names for the command."""
        return self._aliases

    @property
    def description(self) -> str:
        """Description of what the command does."""
        return self._description

    @property
    def category(self) -> CommandCategory:
        """Category this command belongs to."""
        return CommandCategory.DEVELOPMENT

    async def execute(self, args: CommandArgs, context: CommandContext) -> Optional[str]:
        """Execute the template shortcut command.

        Args:
            args: Command arguments passed by the user
            context: Command execution context

        Returns:
            Optional string result
        """
        # Set the template as active in the tool handler
        if hasattr(context.state_manager, "tool_handler") and context.state_manager.tool_handler:
            context.state_manager.tool_handler.set_active_template(self.template)
        else:
            await ui.error("Tool handler not initialized. Please restart TunaCode.")
            return None

        # Show template activation
        await ui.success(f"Activated template: {self.template.name}")
        if self.template.allowed_tools:
            await ui.muted(f"Auto-approved tools: {', '.join(self.template.allowed_tools)}")

        # Process the prompt with arguments
        if self.template.prompt:
            # Join all arguments as a single string
            argument = " ".join(args) if args else ""

            # Substitute {argument} placeholder in the prompt
            prompt = self.template.prompt.replace("{argument}", argument)

            # If there are additional parameters, substitute them too
            if self.template.parameters:
                for key, value in self.template.parameters.items():
                    placeholder = f"{{{key}}}"
                    prompt = prompt.replace(placeholder, value)

            # Show the expanded prompt
            await ui.info("Executing prompt:")
            await ui.muted(f"  {prompt}")

            # Execute the prompt via process_request
            if context.process_request:
                await context.process_request(
                    prompt, context.state_manager.session.current_model, context.state_manager
                )
        else:
            await ui.muted("Template activated. No default prompt defined.")

        return None
