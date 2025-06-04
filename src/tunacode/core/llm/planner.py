from typing import List

from ...types import ModelName
from ..agents.planner_schema import Task
from ..state import StateManager

_SYSTEM = """You are a senior software project planner.

Your job is to break down a USER_REQUEST into a logical sequence of tasks.

Guidelines:
1. Use the FEWEST tasks possible - combine related operations
2. Order tasks logically - reads before writes, understand before modify
3. Mark read-only tasks (reading files, searching, analyzing) as mutate: false
4. Mark modifying tasks (writing, updating, creating files) as mutate: true
5. Write clear, actionable descriptions

Each task MUST have:
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
    from rich.console import Console

    from ..agents.main import get_agent_tool

    console = Console()
    Agent, _ = get_agent_tool()

    # Show planning is starting
    console.print("\n[dim][Planning] Breaking down request into tasks...[/dim]")

    # Create a simple planning agent
    planner = Agent(
        model=model,
        system_prompt=_SYSTEM,
        result_type=List[Task],
    )

    # Get the plan from the agent
    result = await planner.run(request)
    tasks = result.data

    # Display the plan
    console.print(f"[dim][Planning] Generated {len(tasks)} tasks:[/dim]")
    for task in tasks:
        task_type = "WRITE" if task.mutate else "READ"
        console.print(f"[dim]  Task {task.id}: {task_type} - {task.description}[/dim]")
    console.print("")

    return tasks
