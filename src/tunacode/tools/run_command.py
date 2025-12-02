"""Command execution tool with security validation."""

import logging
import subprocess

from tunacode.constants import (
    CMD_OUTPUT_FORMAT,
    CMD_OUTPUT_NO_ERRORS,
    CMD_OUTPUT_NO_OUTPUT,
    CMD_OUTPUT_TRUNCATED,
    COMMAND_OUTPUT_END_SIZE,
    COMMAND_OUTPUT_START_INDEX,
    COMMAND_OUTPUT_THRESHOLD,
    MAX_COMMAND_OUTPUT,
)
from tunacode.tools.decorators import base_tool
from tunacode.utils.security import CommandSecurityError, safe_subprocess_popen

logger = logging.getLogger(__name__)


@base_tool
async def run_command(command: str) -> str:
    """Run a shell command and return the output.

    Uses security validation to block dangerous commands.

    Args:
        command: The command to run.

    Returns:
        The output of the command (stdout and stderr).
    """
    process = None
    try:
        process = safe_subprocess_popen(
            command,
            shell=True,
            validate=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()
    except CommandSecurityError as e:
        return f"Security validation failed: {e}"
    finally:
        _cleanup_process(process)

    output = stdout.strip() or CMD_OUTPUT_NO_OUTPUT
    error = stderr.strip() or CMD_OUTPUT_NO_ERRORS
    resp = CMD_OUTPUT_FORMAT.format(output=output, error=error).strip()

    return _truncate_output(resp)


def _cleanup_process(process) -> None:
    """Ensure process cleanup."""
    if process is None or process.poll() is not None:
        return

    try:
        process.terminate()
        try:
            process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1.0)
    except Exception as e:
        logger.warning(f"Failed to cleanup process: {e}")


def _truncate_output(resp: str) -> str:
    """Truncate output if too long, keeping start and end."""
    if len(resp) <= MAX_COMMAND_OUTPUT:
        return resp

    start_part = resp[:COMMAND_OUTPUT_START_INDEX]
    end_part = (
        resp[-COMMAND_OUTPUT_END_SIZE:]
        if len(resp) > COMMAND_OUTPUT_THRESHOLD
        else resp[COMMAND_OUTPUT_START_INDEX:]
    )
    return start_part + CMD_OUTPUT_TRUNCATED + end_part
