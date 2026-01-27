"""Agent state definitions used by core runtime."""

from dataclasses import dataclass
from enum import Enum


@dataclass
class ResponseState:
    """Track whether a user visible response was produced."""

    has_user_response: bool = False
    has_final_synthesis: bool = False
    task_completed: bool = False
    awaiting_user_guidance: bool = False


class AgentState(Enum):
    """Agent loop states for enhanced completion detection."""

    USER_INPUT = "user_input"
    ASSISTANT = "assistant"
    TOOL_EXECUTION = "tool_execution"
    RESPONSE = "response"


__all__ = ["AgentState", "ResponseState"]
