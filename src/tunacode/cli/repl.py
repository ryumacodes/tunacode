"""
Module: tunacode.cli.repl

Interactive REPL (Read-Eval-Print Loop) implementation for TunaCode.
Handles user input, command processing, and agent interaction in an interactive shell.
"""

import json
import os
import subprocess
from asyncio.exceptions import CancelledError
from pathlib import Path

from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.application.current import get_app
from pydantic_ai.exceptions import UnexpectedModelBehavior

from tunacode.configuration.settings import ApplicationSettings
from tunacode.core.agents import main as agent
from tunacode.core.agents.main import patch_tool_messages
from tunacode.core.tool_handler import ToolHandler
from tunacode.exceptions import AgentError, UserAbortError, ValidationError
from tunacode.ui import console as ui
from tunacode.ui.tool_ui import ToolUI

from ..types import CommandContext, CommandResult, StateManager, ToolArgs
from .commands import CommandRegistry

# Tool UI instance
_tool_ui = ToolUI()


def _parse_args(args) -> ToolArgs:
    """
    Parse tool arguments from a JSON string or dictionary.

    Args:
        args (str or dict): A JSON-formatted string or a dictionary containing tool arguments.

    Returns:
        dict: The parsed arguments.

    Raises:
        ValueError: If 'args' is not a string or dictionary, or if the string is not valid JSON.
    """
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            raise ValidationError(f"Invalid JSON: {args}")
    elif isinstance(args, dict):
        return args
    else:
        raise ValidationError(f"Invalid args type: {type(args)}")


async def _tool_confirm(tool_call, node, state_manager: StateManager):
    """Confirm tool execution with separated business logic and UI."""
    # Create tool handler with state
    tool_handler = ToolHandler(state_manager)
    args = _parse_args(tool_call.args)

    # Check if confirmation is needed
    if not tool_handler.should_confirm(tool_call.tool_name):
        # Log MCP tools when skipping confirmation
        app_settings = ApplicationSettings()
        if tool_call.tool_name not in app_settings.internal_tools:
            title = _tool_ui._get_tool_title(tool_call.tool_name)
            await _tool_ui.log_mcp(title, args)
        return

    # Stop spinner during user interaction
    state_manager.session.spinner.stop()

    # Create confirmation request
    request = tool_handler.create_confirmation_request(tool_call.tool_name, args)

    # Show UI and get response
    response = await _tool_ui.show_confirmation(request, state_manager)

    # Process the response
    if not tool_handler.process_confirmation(response, tool_call.tool_name):
        raise UserAbortError("User aborted.")

    await ui.line()  # Add line after user input
    state_manager.session.spinner.start()


async def _tool_handler(part, node, state_manager: StateManager):
    """Handle tool execution with separated business logic and UI."""
    # Create tool handler with state first to check if confirmation is needed
    tool_handler = ToolHandler(state_manager)

    # Only show tool info for tools that require confirmation
    if tool_handler.should_confirm(part.tool_name):
        await ui.info(f"Tool({part.tool_name})")

    state_manager.session.spinner.stop()

    try:
        args = _parse_args(part.args)

        # Use a synchronous function in run_in_terminal to avoid async deadlocks
        def confirm_func():
            # Skip confirmation if not needed
            if not tool_handler.should_confirm(part.tool_name):
                return False

            # Create confirmation request
            request = tool_handler.create_confirmation_request(part.tool_name, args)

            # Show sync UI and get response
            response = _tool_ui.show_sync_confirmation(request)

            # Process the response
            if not tool_handler.process_confirmation(response, part.tool_name):
                return True  # Abort
            return False  # Continue

        # Run the confirmation in the terminal
        should_abort = await run_in_terminal(confirm_func)

        if should_abort:
            raise UserAbortError("User aborted.")

    except UserAbortError:
        patch_tool_messages("Operation aborted by user.", state_manager)
        raise
    finally:
        state_manager.session.spinner.start()


# Initialize command registry
_command_registry = CommandRegistry()
_command_registry.register_all_default_commands()


async def _handle_command(command: str, state_manager: StateManager) -> CommandResult:
    """
    Handles a command string using the command registry.

    Args:
        command: The command string entered by the user.
        state_manager: The state manager instance.

    Returns:
        Command result (varies by command).
    """
    # Create command context
    context = CommandContext(state_manager=state_manager, process_request=process_request)

    try:
        # Set the process_request callback for commands that need it
        _command_registry.set_process_request_callback(process_request)

        # Execute the command
        return await _command_registry.execute(command, context)
    except ValidationError as e:
        await ui.error(str(e))


async def process_request(text: str, state_manager: StateManager, output: bool = True):
    """Process input using the agent, handling cancellation safely."""
    state_manager.session.spinner = await ui.spinner(
        True, state_manager.session.spinner, state_manager
    )
    try:
        # Patch any orphaned tool calls from previous requests before proceeding
        patch_tool_messages("Tool execution was interrupted", state_manager)

        # Clear tracking for new request when thoughts are enabled
        if state_manager.session.show_thoughts:
            state_manager.session.tool_calls = []
            # Don't clear files_in_context - keep it cumulative for the session
            state_manager.session.iteration_count = 0
            state_manager.session.current_iteration = 0

        # Track message start for thoughts display
        start_idx = len(state_manager.session.messages)

        # Create a partial function that includes state_manager
        def tool_callback_with_state(part, node):
            return _tool_handler(part, node, state_manager)

        # Expand @file references before sending to the agent
        try:
            from tunacode.utils.text_utils import expand_file_refs

            text, referenced_files = expand_file_refs(text)
            # Track the referenced files
            for file_path in referenced_files:
                state_manager.session.files_in_context.add(file_path)
        except ValueError as e:
            await ui.error(str(e))
            return

        # Use normal agent processing
        res = await agent.process_request(
            state_manager.session.current_model,
            text,
            state_manager,
            tool_callback=tool_callback_with_state,
        )
        if output:
            if state_manager.session.show_thoughts:
                new_msgs = state_manager.session.messages[start_idx:]
                for msg in new_msgs:
                    if isinstance(msg, dict) and "thought" in msg:
                        await ui.muted(f"THOUGHT: {msg['thought']}")
            # Check if result exists and has output
            if hasattr(res, "result") and res.result is not None and hasattr(res.result, "output"):
                await ui.agent(res.result.output)
                # Always show files in context after agent response
                if state_manager.session.files_in_context:
                    # Extract just filenames from full paths for readability
                    filenames = [
                        Path(f).name for f in sorted(state_manager.session.files_in_context)
                    ]
                    await ui.muted(f"\nFiles in context: {', '.join(filenames)}")
            else:
                # Fallback: show that the request was processed
                await ui.muted("Request completed")
                # Show files in context even for empty responses
                if state_manager.session.files_in_context:
                    filenames = [
                        Path(f).name for f in sorted(state_manager.session.files_in_context)
                    ]
                    await ui.muted(f"Files in context: {', '.join(filenames)}")
    except CancelledError:
        await ui.muted("Request cancelled")
    except UserAbortError:
        await ui.muted("Operation aborted.")
    except UnexpectedModelBehavior as e:
        error_message = str(e)
        await ui.muted(error_message)
        patch_tool_messages(error_message, state_manager)
    except Exception as e:
        # Check if this might be a tool calling failure that we can recover from
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ["tool", "function", "call", "schema"]):
            # Try to extract and execute tool calls from the last response
            if state_manager.session.messages:
                last_msg = state_manager.session.messages[-1]
                if hasattr(last_msg, "parts"):
                    for part in last_msg.parts:
                        if hasattr(part, "content") and isinstance(part.content, str):
                            from tunacode.core.agents.main import extract_and_execute_tool_calls

                            try:
                                # Create a partial function that includes state_manager
                                def tool_callback_with_state(part, node):
                                    return _tool_handler(part, node, state_manager)

                                await extract_and_execute_tool_calls(
                                    part.content, tool_callback_with_state, state_manager
                                )
                                await ui.warning(" Recovered using JSON tool parsing")
                                return  # Successfully recovered
                            except Exception:
                                pass  # Fallback failed, continue with normal error handling

        # Wrap unexpected exceptions in AgentError for better tracking
        agent_error = AgentError(f"Agent processing failed: {str(e)}")
        agent_error.__cause__ = e  # Preserve the original exception chain
        await ui.error(str(e))
    finally:
        await ui.spinner(False, state_manager.session.spinner, state_manager)
        state_manager.session.current_task = None

        # Force refresh of the multiline input prompt to restore placeholder
        if "multiline" in state_manager.session.input_sessions:
            await run_in_terminal(
                lambda: state_manager.session.input_sessions["multiline"].app.invalidate()
            )


async def repl(state_manager: StateManager):
    action = None
    ctrl_c_pressed = False

    # Professional startup information
    await ui.muted(f"• Model: {state_manager.session.current_model}")
    await ui.success("Ready to assist with your development")
    await ui.line()

    instance = agent.get_or_create_agent(state_manager.session.current_model, state_manager)

    async with instance.run_mcp_servers():
        while True:
            try:
                line = await ui.multiline_input(state_manager, _command_registry)
            except UserAbortError:
                if ctrl_c_pressed:
                    break
                ctrl_c_pressed = True
                await ui.warning("Hit Ctrl+C again to exit")
                continue

            if not line:
                continue

            ctrl_c_pressed = False

            if line.lower() in ["exit", "quit"]:
                break

            if line.startswith("/"):
                action = await _handle_command(line, state_manager)
                if action == "restart":
                    break
                continue

            if line.startswith("!"):
                command = line[1:].strip()

                # Show tool-style header for bash commands
                cmd_display = command if command else "Interactive shell"
                await ui.panel("Tool(bash)", f"Command: {cmd_display}", border_style="yellow")

                def run_shell():
                    try:
                        if command:
                            result = subprocess.run(command, shell=True, capture_output=False)
                            if result.returncode != 0:
                                # Use print directly since we're in a terminal context
                                print(f"\nCommand exited with code {result.returncode}")
                        else:
                            shell = os.environ.get("SHELL", "bash")
                            subprocess.run(shell)
                    except Exception as e:
                        print(f"\nShell command failed: {str(e)}")

                await run_in_terminal(run_shell)
                await ui.line()
                continue

            # Check if another task is already running
            if state_manager.session.current_task and not state_manager.session.current_task.done():
                await ui.muted("Agent is busy, press Ctrl+C to interrupt.")
                continue

            state_manager.session.current_task = get_app().create_background_task(
                process_request(line, state_manager)
            )

    if action == "restart":
        await repl(state_manager)
    else:
        await ui.info("Session ended. Happy coding!")
