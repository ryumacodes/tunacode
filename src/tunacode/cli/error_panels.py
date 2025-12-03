"""Error Panel System for Textual TUI.

Provides structured error display with recovery options, following NeXTSTEP:
- User Control: Actionable recovery commands
- Visual Feedback: Error severity through color coding
- Consistency: All errors rendered with same structure
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import RenderableType

from tunacode.cli.rich_panels import ErrorDisplayData, RichPanelRenderer

if TYPE_CHECKING:
    pass


# Error type to severity mapping
ERROR_SEVERITY_MAP: dict[str, str] = {
    # Critical errors (red)
    "ToolExecutionError": "error",
    "FileOperationError": "error",
    "AgentError": "error",
    "GitOperationError": "error",
    "GlobalRequestTimeoutError": "error",
    "ToolBatchingJSONError": "error",
    # Configuration errors (warning - recoverable)
    "ConfigurationError": "warning",
    "ModelConfigurationError": "warning",
    "ValidationError": "warning",
    "SetupValidationError": "warning",
    # User-initiated (info - not really an error)
    "UserAbortError": "info",
    "StateError": "info",
}

# Exception attribute to display label mapping
EXCEPTION_CONTEXT_ATTRS: dict[str, str] = {
    "tool_name": "Tool",
    "path": "Path",
    "operation": "Operation",
    "server_name": "Server",
    "model": "Model",
    "step": "Step",
    "validation_type": "Validation",
}


def _extract_exception_context(exc: Exception) -> dict[str, str]:
    """Extract displayable context from exception attributes."""
    context: dict[str, str] = {}
    for attr, label in EXCEPTION_CONTEXT_ATTRS.items():
        if hasattr(exc, attr):
            value = getattr(exc, attr)
            if value is not None:
                context[label] = str(value)
    return context


# Default recovery commands by error type
DEFAULT_RECOVERY_COMMANDS: dict[str, list[str]] = {
    "ConfigurationError": [
        "tunacode --wizard  # Run setup wizard",
        "cat ~/.tunacode/tunacode.json  # Check config",
    ],
    "ModelConfigurationError": [
        "/model  # List available models",
        "tunacode --wizard  # Reconfigure",
    ],
    "FileOperationError": [
        "ls -la <path>  # Check permissions",
        "pwd  # Verify current directory",
    ],
    "GitOperationError": [
        "git status  # Check repository state",
        "git stash  # Stash uncommitted changes",
    ],
    "GlobalRequestTimeoutError": [
        "Check network connectivity",
        "Increase timeout in tunacode.json",
    ],
}


def render_exception(exc: Exception) -> RenderableType:
    """Render any exception as an error panel.

    Extracts structured information from TunaCode exceptions
    and provides appropriate recovery options.
    """
    error_type = type(exc).__name__
    severity = ERROR_SEVERITY_MAP.get(error_type, "error")

    # Extract structured information from TunaCode exceptions
    suggested_fix = getattr(exc, "suggested_fix", None)
    recovery_commands = getattr(exc, "recovery_commands", None)

    # Build context from exception attributes using mapping
    context = _extract_exception_context(exc)

    # Use default recovery commands if none provided
    if not recovery_commands:
        recovery_commands = DEFAULT_RECOVERY_COMMANDS.get(error_type)

    # Extract clean message (without emoji formatting)
    message = str(exc)
    # Remove emoji prefixes from formatted messages
    for prefix in ("Fix: ", "Suggested fix: ", "Recovery commands:"):
        if prefix in message:
            message = message.split(prefix)[0].strip()

    data = ErrorDisplayData(
        error_type=error_type,
        message=message,
        suggested_fix=suggested_fix,
        recovery_commands=recovery_commands,
        context=context if context else None,
        severity=severity,
    )

    return RichPanelRenderer.render_error(data)


def render_tool_error(
    tool_name: str,
    message: str,
    suggested_fix: str | None = None,
    file_path: str | None = None,
) -> RenderableType:
    """Render a tool execution error with context."""
    context = {}
    if file_path:
        context["Path"] = file_path

    data = ErrorDisplayData(
        error_type=f"{tool_name} Error",
        message=message,
        suggested_fix=suggested_fix,
        recovery_commands=[
            f"Check file exists: ls -la {file_path}" if file_path else None,
            "Try with different arguments",
        ],
        context=context if context else None,
        severity="error",
    )
    # Filter None from recovery commands
    if data.recovery_commands:
        data.recovery_commands = [cmd for cmd in data.recovery_commands if cmd]

    return RichPanelRenderer.render_error(data)


def render_validation_error(
    field: str,
    message: str,
    valid_examples: list[str] | None = None,
) -> RenderableType:
    """Render a validation error with examples."""
    suggested_fix = None
    if valid_examples:
        suggested_fix = f"Valid examples: {', '.join(valid_examples[:3])}"

    data = ErrorDisplayData(
        error_type="Validation Error",
        message=f"{field}: {message}",
        suggested_fix=suggested_fix,
        context={"Field": field},
        severity="warning",
    )

    return RichPanelRenderer.render_error(data)


def render_connection_error(
    service: str,
    message: str,
    retry_available: bool = True,
) -> RenderableType:
    """Render a connection/service error."""
    recovery = []
    if retry_available:
        recovery.append("Retry the operation")
    recovery.extend(
        [
            "Check network connectivity",
            f"Verify {service} service status",
        ]
    )

    data = ErrorDisplayData(
        error_type=f"{service} Connection Error",
        message=message,
        recovery_commands=recovery,
        severity="error",
    )

    return RichPanelRenderer.render_error(data)


def render_user_abort() -> RenderableType:
    """Render a user abort notification (not really an error)."""
    data = ErrorDisplayData(
        error_type="Operation Cancelled",
        message="User cancelled the operation",
        severity="info",
    )

    return RichPanelRenderer.render_error(data)
