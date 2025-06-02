"""Read-only agent with a restricted toolset."""

from __future__ import annotations

from typing import Sequence

from ..state import StateManager
from .main import Agent  # type: ignore

READ_ONLY_TOOLS: Sequence[str] = (
    "read_file",
    "grep",
    "search",
    "explain_symbol",
)


class ReadOnlyAgent(Agent):  # type: ignore[name-defined]
    """Agent configured with read-only tools."""

    def __init__(self, model: str, state_manager: StateManager):
        super().__init__(
            model=model,
            tools=READ_ONLY_TOOLS,
            state_manager=state_manager,
        )
