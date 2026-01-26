"""Callback type definitions for TunaCode CLI.

Contains callback signatures and the ToolProgress dataclass for
structured progress reporting.

Callback contracts (preconditions/postconditions):
- ToolResultCallback: Preconditions: tool_name is registered, args are normalized,
  status reflects tool lifecycle. Postconditions: side effects only (UI/logging) and
  should not raise.
- StreamingCallback: Preconditions: chunk is ordered text delta. Postconditions:
  enqueue or render the chunk without raising.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeAlias

from tunacode.types.base import ModelName, ToolArgs, ToolName
from tunacode.types.pydantic_ai import AgentRun
from tunacode.types.state import StateManagerProtocol

if TYPE_CHECKING:
    from pydantic_ai.messages import ToolCallPart  # noqa: F401
    from pydantic_ai.result import StreamedRunResult  # noqa: F401


@dataclass(frozen=True, slots=True)
class ToolProgress:
    """Structured progress information for subagent tool execution.

    Attributes:
        subagent: Name of the subagent (e.g., "research")
        operation: Description of current operation (e.g., "grep pattern...")
        current: Current operation count (1-indexed)
        total: Total expected operations (0 if unknown)
    """

    subagent: str
    operation: str
    current: int
    total: int


# Tool callbacks
ToolCallback: TypeAlias = Callable[
    ["ToolCallPart", "StreamedRunResult[None, str]"],
    Awaitable[None],
]
ToolStartCallback: TypeAlias = Callable[[str], None]
ToolProgressCallback: TypeAlias = Callable[[ToolProgress], None]
ToolResultCallback: TypeAlias = Callable[
    [ToolName, str, ToolArgs, str | None, float | None],
    None,
]
NoticeCallback: TypeAlias = Callable[[str], None]

# UI callbacks
StreamingCallback: TypeAlias = Callable[[str], Awaitable[None]]
UICallback: TypeAlias = Callable[[str], Awaitable[None]]
UIInputCallback: TypeAlias = Callable[[str, str], Awaitable[str]]

# Request orchestration callbacks
ProcessRequestCallback: TypeAlias = Callable[
    [
        str,
        ModelName,
        StateManagerProtocol,
        ToolCallback | None,
        StreamingCallback | None,
        ToolResultCallback | None,
        ToolStartCallback | None,
        NoticeCallback | None,
    ],
    Awaitable[AgentRun],
]

# Async function types
AsyncFunc: TypeAlias = Callable[..., Awaitable[Any]]
AsyncToolFunc: TypeAlias = Callable[..., Awaitable[str]]
AsyncVoidFunc: TypeAlias = Callable[..., Awaitable[None]]

__all__ = [
    "AsyncFunc",
    "AsyncToolFunc",
    "AsyncVoidFunc",
    "ProcessRequestCallback",
    "StreamingCallback",
    "ToolCallback",
    "ToolProgress",
    "ToolProgressCallback",
    "ToolResultCallback",
    "ToolStartCallback",
    "NoticeCallback",
    "UICallback",
    "UIInputCallback",
]
