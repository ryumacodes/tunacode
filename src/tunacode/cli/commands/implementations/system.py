"""System-level commands for TunaCode CLI."""

import shutil
import subprocess
import sys
from typing import List

from ....types import CommandContext
from ....ui import console as ui
from ..base import CommandCategory, CommandSpec, SimpleCommand


class HelpCommand(SimpleCommand):
    """Show help information."""

    spec = CommandSpec(
        name="help",
        aliases=["/help"],
        description="Show help information",
        category=CommandCategory.SYSTEM,
    )

    def __init__(self, command_registry=None):
        self._command_registry = command_registry

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await ui.help(self._command_registry)


class ClearCommand(SimpleCommand):
    """Clear screen and message history."""

    spec = CommandSpec(
        name="clear",
        aliases=["/clear"],
        description="Clear the screen and message history",
        category=CommandCategory.NAVIGATION,
    )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        # Patch any orphaned tool calls before clearing
        from tunacode.core.agents.main import patch_tool_messages

        patch_tool_messages("Conversation cleared", context.state_manager)

        await ui.clear()
        context.state_manager.session.messages = []
        context.state_manager.session.files_in_context.clear()
        await ui.success("Message history and file context cleared")


class RefreshConfigCommand(SimpleCommand):
    """Refresh configuration from defaults."""

    spec = CommandSpec(
        name="refresh",
        aliases=["/refresh"],
        description="Refresh configuration from defaults (useful after updates)",
        category=CommandCategory.SYSTEM,
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
        max_iterations = context.state_manager.session.user_config.get("settings", {}).get(
            "max_iterations", 20
        )
        await ui.success(f"Configuration refreshed - max iterations: {max_iterations}")


class UpdateCommand(SimpleCommand):
    """Update TunaCode to the latest version."""

    spec = CommandSpec(
        name="update",
        aliases=["/update"],
        description="Update TunaCode to the latest version",
        category=CommandCategory.SYSTEM,
    )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await ui.info("Checking for TunaCode updates...")

        # Detect installation method
        installation_method = None

        # Check if installed via pipx
        if shutil.which("pipx"):
            try:
                result = subprocess.run(
                    ["pipx", "list"], capture_output=True, text=True, timeout=10
                )
                pipx_installed = "tunacode" in result.stdout.lower()
                if pipx_installed:
                    installation_method = "pipx"
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass

        # Check if installed via pip
        if not installation_method:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "show", "tunacode-cli"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    installation_method = "pip"
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass

        if not installation_method:
            await ui.error("Could not detect TunaCode installation method")
            await ui.muted("Manual update options:")
            await ui.muted("  pipx: pipx upgrade tunacode")
            await ui.muted("  pip:  pip install --upgrade tunacode-cli")
            return

        # Perform update based on detected method
        try:
            if installation_method == "pipx":
                await ui.info("Updating via pipx...")
                result = subprocess.run(
                    ["pipx", "upgrade", "tunacode"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            else:  # pip
                await ui.info("Updating via pip...")
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "--upgrade",
                        "tunacode-cli",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

            if result.returncode == 0:
                await ui.success("TunaCode updated successfully!")
                await ui.muted("Restart TunaCode to use the new version")

                # Show update output if available
                if result.stdout.strip():
                    output_lines = result.stdout.strip().split("\n")
                    for line in output_lines[-5:]:  # Show last 5 lines
                        if line.strip():
                            await ui.muted(f"  {line}")
            else:
                await ui.error("Update failed")
                if result.stderr:
                    await ui.muted(f"Error: {result.stderr.strip()}")

        except subprocess.TimeoutExpired:
            await ui.error("Update timed out")
        except subprocess.CalledProcessError as e:
            await ui.error(f"Update failed: {e}")
        except FileNotFoundError:
            await ui.error(f"Could not find {installation_method} executable")
