"""
Bridge module to integrate existing TunaCode agent logic with Textual UI.

This module adapts the existing REPL and agent processing logic to work
with the new Textual-based interface while maintaining compatibility.
"""

from asyncio.exceptions import CancelledError
from typing import Callable

from pydantic_ai.exceptions import UnexpectedModelBehavior

from tunacode.cli.commands import CommandRegistry
from tunacode.cli.repl import _parse_args
from tunacode.core.agents import main as agent
from tunacode.core.agents.main import patch_tool_messages
from tunacode.core.tool_handler import ToolHandler
from tunacode.exceptions import AgentError, UserAbortError, ValidationError
from tunacode.types import StateManager
from tunacode.ui.tool_ui import ToolUI


class TextualAgentBridge:
    """Bridge between Textual UI and existing agent logic."""

    def __init__(self, state_manager: StateManager, message_callback: Callable):
        self.state_manager = state_manager
        self.message_callback = message_callback
        self.tool_ui = ToolUI()
        self.command_registry = CommandRegistry()
        self.command_registry.register_all_default_commands()

    async def process_user_input(self, text: str) -> str:
        """Process user input and return the agent's response."""
        if text.startswith("/"):
            return await self._handle_command(text)
        else:
            return await self._process_agent_request(text)

    async def _handle_command(self, command: str) -> str:
        """Handle slash commands."""
        try:
            from tunacode.types import CommandContext

            # Create command context
            context = CommandContext(
                state_manager=self.state_manager, process_request=self._process_agent_request
            )

            # Set the process_request callback for commands that need it
            self.command_registry.set_process_request_callback(self._process_agent_request)

            # Execute the command
            result = await self.command_registry.execute(command, context)

            if result == "restart":
                return "Application restart requested."
            elif result:
                return str(result)
            else:
                return f"Command '{command}' executed successfully."

        except ValidationError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Command error: {str(e)}"

    async def _process_agent_request(self, text: str) -> str:
        """Process input using the agent."""
        try:
            # Expand @file references before sending to the agent
            try:
                from tunacode.utils.text_utils import expand_file_refs

                text, referenced_files = expand_file_refs(text)
                # Track the referenced files
                for file_path in referenced_files:
                    self.state_manager.session.files_in_context.add(file_path)
            except ValueError as e:
                return f"Error: {str(e)}"

            # Notify UI about processing start
            await self.message_callback("tool", "Processing request...")

            # Create a tool callback that integrates with Textual
            def tool_callback_with_state(part, node):
                return self._tool_handler(part, node)

            # Get or create agent instance
            instance = agent.get_or_create_agent(
                self.state_manager.session.current_model, self.state_manager
            )

            # Process the request
            async with instance.run_mcp_servers():
                res = await agent.process_request(
                    self.state_manager.session.current_model,
                    text,
                    self.state_manager,
                    tool_callback=tool_callback_with_state,
                )

                if res and res.result:
                    return res.result.output
                else:
                    return "Request processed (no output)."

        except CancelledError:
            return "Request cancelled."
        except UserAbortError:
            return "Operation aborted."
        except UnexpectedModelBehavior as e:
            error_message = str(e)
            patch_tool_messages(error_message, self.state_manager)
            return f"Model error: {error_message}"
        except Exception as e:
            # Wrap unexpected exceptions in AgentError for better tracking
            agent_error = AgentError(f"Agent processing failed: {str(e)}")
            agent_error.__cause__ = e
            return f"Error: {str(e)}"

    async def _tool_handler(self, part, node):
        """Handle tool execution with Textual UI integration."""
        await self.message_callback("tool", f"Tool: {part.tool_name}")

        try:
            # Create tool handler with state
            tool_handler = ToolHandler(self.state_manager)
            args = _parse_args(part.args)

            # Check if confirmation is needed
            if tool_handler.should_confirm(part.tool_name):
                # Create confirmation request
                tool_handler.create_confirmation_request(part.tool_name, args)

                # For now, show a simple confirmation in the UI
                # In a full implementation, this would show a proper modal dialog
                await self.message_callback(
                    "system", f"Tool confirmation: {part.tool_name} with args: {args}"
                )

                # For demo purposes, auto-approve (in production, this should be interactive)
                if not tool_handler.process_confirmation(True, part.tool_name):
                    raise UserAbortError("User aborted tool execution.")

        except UserAbortError:
            patch_tool_messages("Operation aborted by user.", self.state_manager)
            raise


class TextualToolConfirmation:
    """Handle tool confirmations in Textual UI."""

    def __init__(self, app_instance):
        self.app = app_instance

    async def show_confirmation(self, tool_name: str, args: dict) -> bool:
        """Show tool confirmation dialog and return user's choice."""
        # This would show a modal dialog in the Textual app
        # For now, return True (auto-approve)
        return True
