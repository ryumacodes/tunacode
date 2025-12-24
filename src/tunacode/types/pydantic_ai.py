"""Pydantic-AI type wrappers for TunaCode CLI.

Isolates pydantic-ai dependencies to a single module for easier
migration if the underlying library changes.
"""

from typing import Any

from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest as _ModelRequest
from pydantic_ai.messages import ToolReturnPart

# Re-export with stable names ugly but better thab what we had before
PydanticAgent = Agent
MessagePart = ToolReturnPart | Any
ModelRequest = _ModelRequest
ModelResponse = Any

AgentResponse = Any
MessageHistory = list[Any]
AgentRun = Any

__all__ = [
    "AgentResponse",
    "AgentRun",
    "MessageHistory",
    "MessagePart",
    "ModelRequest",
    "ModelResponse",
    "PydanticAgent",
]
