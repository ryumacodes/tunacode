import json
from typing import List

from ..agents.planner_schema import Task
from ..state import StateManager
from ...types import ModelName

_SYSTEM = """You are a senior software project planner.
Break the USER_REQUEST into the fewest possible, strictly ordered tasks.
Each task should have:
- id: Sequential number starting from 1
- description: Clear description of what needs to be done
- mutate: true if the task modifies files/code, false if it only reads/analyzes

Return ONLY a valid JSON array of tasks, no other text.
Example:
[
  {"id": 1, "description": "Read the main.py file to understand the structure", "mutate": false},
  {"id": 2, "description": "Update the function to handle edge cases", "mutate": true}
]"""


async def make_plan(request: str, model: ModelName, state_manager: StateManager) -> List[Task]:
    """Generate an execution plan from a user request using TunaCode's LLM infrastructure."""
    # Lazy import to avoid circular dependencies
    from ..agents.main import get_agent_tool
    
    Agent, _ = get_agent_tool()
    
    # Create a simple planning agent
    planner = Agent(
        model=model,
        system_prompt=_SYSTEM,
        result_type=List[Task],
    )
    
    # Get the plan from the agent
    result = await planner.run(request)
    return result.data
