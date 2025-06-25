"""Model management commands for TunaCode CLI."""

from typing import Optional

from .... import utils
from ....exceptions import ConfigurationError
from ....types import CommandArgs, CommandContext
from ....ui import console as ui
from ..base import CommandCategory, CommandSpec, SimpleCommand


class ModelCommand(SimpleCommand):
    """Manage model selection."""

    spec = CommandSpec(
        name="model",
        aliases=["/model"],
        description="Switch model (e.g., /model gpt-4 or /model openai:gpt-4)",
        category=CommandCategory.MODEL,
    )

    async def execute(self, args: CommandArgs, context: CommandContext) -> Optional[str]:
        # No arguments - show current model
        if not args:
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
            try:
                utils.user_configuration.set_default_model(model_name, context.state_manager)
                await ui.muted("Updating default model")
                return "restart"
            except ConfigurationError as e:
                await ui.error(str(e))
                return None

        # Show success message with the new model
        await ui.success(f"Switched to model: {model_name}")
        return None
