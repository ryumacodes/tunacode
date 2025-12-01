"""Simple token usage and cost tracking."""

from dataclasses import dataclass
from typing import Any, Optional

from tunacode.configuration.models import ModelRegistry

TOKENS_PER_MILLION = 1_000_000


@dataclass
class TokenUsage:
    """Token usage from a single API call."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class TokenTracker:
    """Tracks token usage and calculates costs from API responses."""

    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry

    def extract_usage(self, response: Any) -> Optional[TokenUsage]:
        """Extract token usage from pydantic-ai ModelResponse.

        Args:
            response: A pydantic-ai ModelResponse object

        Returns:
            TokenUsage if usage data available, None otherwise
        """
        usage = getattr(response, "usage", None)
        if not usage:
            return None

        prompt = getattr(usage, "request_tokens", 0) or 0
        completion = getattr(usage, "response_tokens", 0) or 0
        return TokenUsage(prompt_tokens=prompt, completion_tokens=completion)

    def calculate_cost(self, model_name: str, usage: TokenUsage) -> float:
        """Calculate cost for token usage.

        Args:
            model_name: Model identifier (with or without provider prefix)
            usage: TokenUsage with prompt and completion counts

        Returns:
            Cost in dollars
        """
        model = self.registry.get_model(model_name)
        if not model or not model.pricing:
            return 0.0

        input_cost = (usage.prompt_tokens / TOKENS_PER_MILLION) * model.pricing.input
        output_cost = (usage.completion_tokens / TOKENS_PER_MILLION) * model.pricing.output
        return input_cost + output_cost

    def track_response(self, model_name: str, response: Any) -> Optional[TokenUsage]:
        """Extract usage and calculate cost in one call.

        Args:
            model_name: Model identifier
            response: pydantic-ai ModelResponse

        Returns:
            TokenUsage with cost populated, or None if no usage data
        """
        usage = self.extract_usage(response)
        if not usage:
            return None

        usage.cost = self.calculate_cost(model_name, usage)
        return usage
