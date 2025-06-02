"""Read-only agent implementation for non-mutating operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...tools.grep import grep
from ...tools.read_file import read_file
from ...types import AgentRun, ModelName
from ..state import StateManager

if TYPE_CHECKING:
    from ...types import PydanticAgent


class ReadOnlyAgent:
    """Agent configured with read-only tools for analysis tasks."""

    def __init__(self, model: ModelName, state_manager: StateManager):
        self.model = model
        self.state_manager = state_manager
        self._agent: PydanticAgent | None = None

    def _get_agent(self) -> PydanticAgent:
        """Lazily create the agent with read-only tools."""
        if self._agent is None:
            from .main import get_agent_tool

            Agent, Tool = get_agent_tool()

            # Create agent with only read-only tools
            self._agent = Agent(
                model=self.model,
                system_prompt="You are a read-only assistant. You can analyze and read files but cannot modify them.",
                tools=[
                    Tool(read_file),
                    Tool(grep),
                ],
            )
        return self._agent

    async def process_request(self, request: str) -> AgentRun:
        """Process a request using only read-only tools."""
        agent = self._get_agent()

        # Use iter() like main.py does to get the full run context
        async with agent.iter(request) as agent_run:
            async for _ in agent_run:
                pass  # Let it complete

        return agent_run
