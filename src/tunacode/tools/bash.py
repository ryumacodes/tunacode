"""Bash command execution tool for agent operations."""

import asyncio
import logging
import os
import subprocess
from typing import Dict, Optional

from pydantic_ai.exceptions import ModelRetry

from tunacode.constants import MAX_COMMAND_OUTPUT
from tunacode.tools.decorators import base_tool

logger = logging.getLogger(__name__)

DESTRUCTIVE_PATTERNS = ["rm -rf", "rm -r", "rm /", "dd if=", "mkfs", "fdisk"]


@base_tool
async def bash(
    command: str,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = 30,
    capture_output: bool = True,
) -> str:
    """Execute a bash command with enhanced features.

    Args:
        command: The bash command to execute.
        cwd: Working directory for the command.
        env: Additional environment variables to set.
        timeout: Command timeout in seconds (1-300, default 30).
        capture_output: Whether to capture stdout/stderr.

    Returns:
        Formatted output with exit code, stdout, and stderr.
    """
    _validate_inputs(command, cwd, timeout)

    exec_env = os.environ.copy()
    if env:
        for key, value in env.items():
            if isinstance(key, str) and isinstance(value, str):
                exec_env[key] = value

    exec_cwd = cwd or os.getcwd()

    process = None
    try:
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
            process.kill()
            await process.wait()
            raise ModelRetry(
                f"Command timed out after {timeout} seconds: {command}\n"
                "Consider using a longer timeout or breaking the command into smaller parts."
            )

        stdout_text = stdout.decode("utf-8", errors="replace").strip() if stdout else ""
        stderr_text = stderr.decode("utf-8", errors="replace").strip() if stderr else ""

        _check_common_errors(command, process.returncode, stderr_text)

        return _format_output(command, process.returncode, stdout_text, stderr_text, exec_cwd)

    except FileNotFoundError:
        raise ModelRetry(
            f"Shell not found. Cannot execute command: {command}\n"
            "This typically indicates a system configuration issue."
        )
    finally:
        await _cleanup_process(process)


def _validate_inputs(command: str, cwd: Optional[str], timeout: Optional[int]) -> None:
    """Validate command inputs."""
    if timeout and (timeout < 1 or timeout > 300):
        raise ModelRetry(
            "Timeout must be between 1 and 300 seconds. "
            "Use shorter timeouts for quick commands, longer for builds/tests."
        )

    if cwd and not os.path.isdir(cwd):
        raise ModelRetry(
            f"Working directory '{cwd}' does not exist. "
            "Please verify the path or create the directory first."
        )

    if any(pattern in command for pattern in DESTRUCTIVE_PATTERNS):
        raise ModelRetry(
            f"Command contains potentially destructive operations: {command}\n"
            "Please confirm this is intentional and safe for your system."
        )


def _check_common_errors(command: str, returncode: int, stderr: str) -> None:
    """Check for common error patterns and provide guidance."""
    if returncode == 0 or not stderr:
        return

    stderr_lower = stderr.lower()

    if "command not found" in stderr_lower:
        raise ModelRetry(
            f"Command '{command}' not found. "
            "Check if the command is installed or use the full path."
        )
    if "permission denied" in stderr_lower:
        raise ModelRetry(
            f"Permission denied for command '{command}'. "
            "You may need elevated privileges or different file permissions."
        )
    if "no such file or directory" in stderr_lower:
        raise ModelRetry(
            f"File or directory not found when running '{command}'. "
            "Verify the path exists or create it first."
        )


async def _cleanup_process(process) -> None:
    """Ensure process cleanup."""
    if process is None or process.returncode is not None:
        return

    try:
        try:
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            process.kill()
            await asyncio.wait_for(process.wait(), timeout=1.0)
    except Exception as e:
        logger.warning(f"Failed to cleanup process: {e}")


def _format_output(
    command: str, exit_code: int, stdout: str, stderr: str, cwd: str
) -> str:
    """Format command output."""
    lines = [
        f"Command: {command}",
        f"Exit Code: {exit_code}",
        f"Working Directory: {cwd}",
        "",
        "STDOUT:",
        stdout or "(no output)",
        "",
        "STDERR:",
        stderr or "(no errors)",
    ]

    result = "\n".join(lines)

    if len(result) > MAX_COMMAND_OUTPUT:
        truncate_point = MAX_COMMAND_OUTPUT - 100
        result = result[:truncate_point] + "\n\n[... output truncated ...]"

    return result
