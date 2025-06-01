"""
Module: tunacode.tools.bash

Enhanced bash execution tool for agent operations in the TunaCode application.
Provides advanced shell command execution with working directory support,
environment variables, timeouts, and improved output handling.
"""

import asyncio
import os
import subprocess
from typing import Dict, Optional

from pydantic_ai.exceptions import ModelRetry

from tunacode.constants import MAX_COMMAND_OUTPUT
from tunacode.exceptions import ToolExecutionError
from tunacode.tools.base import BaseTool
from tunacode.types import ToolResult


class BashTool(BaseTool):
    """Enhanced shell command execution tool with advanced features."""

    @property
    def tool_name(self) -> str:
        return "Bash"

    async def _execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = 30,
        capture_output: bool = True,
    ) -> ToolResult:
        """Execute a bash command with enhanced features.

        Args:
            command: The bash command to execute
            cwd: Working directory for the command (defaults to current)
            env: Additional environment variables to set
            timeout: Command timeout in seconds (default 30, max 300)
            capture_output: Whether to capture stdout/stderr (default True)

        Returns:
            ToolResult: Formatted output with exit code, stdout, and stderr

        Raises:
            ModelRetry: For guidance on command failures
            Exception: Any command execution errors
        """
        # Validate and sanitize inputs
        if timeout and (timeout < 1 or timeout > 300):
            raise ModelRetry(
                "Timeout must be between 1 and 300 seconds. "
                "Use shorter timeouts for quick commands, longer for builds/tests."
            )

        # Validate working directory if specified
        if cwd and not os.path.isdir(cwd):
            raise ModelRetry(
                f"Working directory '{cwd}' does not exist. "
                "Please verify the path or create the directory first."
            )

        # Check for potentially destructive commands
        destructive_patterns = ["rm -rf", "rm -r", "rm /", "dd if=", "mkfs", "fdisk"]
        if any(pattern in command for pattern in destructive_patterns):
            raise ModelRetry(
                f"Command contains potentially destructive operations: {command}\n"
                "Please confirm this is intentional and safe for your system."
            )

        # Prepare environment
        exec_env = os.environ.copy()
        if env:
            # Sanitize environment variables
            for key, value in env.items():
                if isinstance(key, str) and isinstance(value, str):
                    exec_env[key] = value

        # Set working directory
        exec_cwd = cwd or os.getcwd()

        try:
            # Execute command with timeout
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                cwd=exec_cwd,
                env=exec_env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                # Kill the process if it times out
                process.kill()
                await process.wait()
                raise ModelRetry(
                    f"Command timed out after {timeout} seconds: {command}\n"
                    "Consider using a longer timeout or breaking the command into smaller parts."
                )

            # Decode output
            stdout_text = stdout.decode("utf-8", errors="replace").strip() if stdout else ""
            stderr_text = stderr.decode("utf-8", errors="replace").strip() if stderr else ""

            # Format output
            result = self._format_output(
                command=command,
                exit_code=process.returncode,
                stdout=stdout_text,
                stderr=stderr_text,
                cwd=exec_cwd,
            )

            # Handle non-zero exit codes as guidance, not failures
            if process.returncode != 0 and stderr_text:
                # Provide guidance for common error patterns
                if "command not found" in stderr_text.lower():
                    raise ModelRetry(
                        f"Command '{command}' not found. "
                        "Check if the command is installed or use the full path."
                    )
                elif "permission denied" in stderr_text.lower():
                    raise ModelRetry(
                        f"Permission denied for command '{command}'. "
                        "You may need elevated privileges or different file permissions."
                    )
                elif "no such file or directory" in stderr_text.lower():
                    raise ModelRetry(
                        f"File or directory not found when running '{command}'. "
                        "Verify the path exists or create it first."
                    )

            return result

        except FileNotFoundError:
            raise ModelRetry(
                f"Shell not found. Cannot execute command: {command}\n"
                "This typically indicates a system configuration issue."
            )

    def _format_output(
        self,
        command: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        cwd: str,
    ) -> str:
        """Format command output in a consistent way.

        Args:
            command: The executed command
            exit_code: The process exit code
            stdout: Standard output content
            stderr: Standard error content
            cwd: Working directory where command was executed

        Returns:
            str: Formatted output string
        """
        # Build the result
        lines = [
            f"Command: {command}",
            f"Exit Code: {exit_code}",
            f"Working Directory: {cwd}",
            "",
        ]

        # Add stdout if present
        if stdout:
            lines.extend(["STDOUT:", stdout, ""])
        else:
            lines.extend(["STDOUT:", "(no output)", ""])

        # Add stderr if present
        if stderr:
            lines.extend(["STDERR:", stderr])
        else:
            lines.extend(["STDERR:", "(no errors)"])

        result = "\n".join(lines)

        # Truncate if too long
        if len(result) > MAX_COMMAND_OUTPUT:
            truncate_point = MAX_COMMAND_OUTPUT - 100  # Leave room for truncation message
            result = result[:truncate_point] + "\n\n[... output truncated ...]"

        return result

    def _format_args(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Format arguments for display in UI logging."""
        args = [repr(command)]

        if cwd:
            args.append(f"cwd={repr(cwd)}")
        if timeout:
            args.append(f"timeout={timeout}")
        if env:
            env_summary = f"{len(env)} vars" if len(env) > 3 else str(env)
            args.append(f"env={env_summary}")

        return ", ".join(args)

    def _get_error_context(self, command: str = None, **kwargs) -> str:
        """Get error context for bash execution."""
        if command:
            return f"executing bash command '{command}'"
        return super()._get_error_context()


# Create the function that maintains the existing interface
async def bash(
    command: str,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = 30,
    capture_output: bool = True,
) -> ToolResult:
    """
    Execute a bash command with enhanced features.

    Args:
        command (str): The bash command to execute
        cwd (Optional[str]): Working directory for the command
        env (Optional[Dict[str, str]]): Additional environment variables
        timeout (Optional[int]): Command timeout in seconds (default 30, max 300)
        capture_output (bool): Whether to capture stdout/stderr

    Returns:
        ToolResult: Formatted output with exit code, stdout, and stderr
    """
    tool = BashTool()
    try:
        return await tool.execute(
            command, cwd=cwd, env=env, timeout=timeout, capture_output=capture_output
        )
    except ToolExecutionError as e:
        # Return error message for pydantic-ai compatibility
        return str(e)
