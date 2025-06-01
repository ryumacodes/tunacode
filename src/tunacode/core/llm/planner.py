from typing import List

from .openai import chat_completion  # type: ignore
from ..agents.planner_schema import Task

_SYSTEM = """You are a senior software project planner.
Break the USER_REQUEST into the fewest possible, strictly ordered tasks.
Return *only* valid JSON list of Task objects."""

async def make_plan(request: str) -> List[Task]:
    """Generate an execution plan from a user request."""
    resp = await chat_completion(
        system=_SYSTEM,
        user=request,
        schema=Task,
        array_response=True,
    )
    return resp
