"""Dataclass definitions for TunaCode CLI.

Contains structured data types used throughout the application.
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from tunacode.types.callbacks import ProcessRequestCallback

if TYPE_CHECKING:
    from tunacode.types.state import StateManagerProtocol


@dataclass
class ModelPricing:
    """Pricing information for a model."""

    input: float
    cached_input: float
    output: float


@dataclass
class ModelConfig:
    """Configuration for a model including pricing."""

    pricing: ModelPricing


ModelRegistry = dict[str, ModelConfig]


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


@dataclass
class CommandContext:
    """Context passed to command handlers."""

    state_manager: "StateManagerProtocol"
    process_request: ProcessRequestCallback | None = None


@dataclass
class TokenUsage:
    """Token usage for a request."""

    input_tokens: int
    cached_tokens: int
    output_tokens: int


@dataclass
class CostBreakdown:
    """Breakdown of costs for a request."""

    input_cost: float
    cached_cost: float
    output_cost: float
    total_cost: float


__all__ = [
    "AgentState",
    "CommandContext",
    "CostBreakdown",
    "ModelConfig",
    "ModelPricing",
    "ModelRegistry",
    "ResponseState",
    "TokenUsage",
]
