"""Todo list tools for tracking task progress during complex operations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic_ai.exceptions import ModelRetry

from tunacode.core.state import StateManager
from tunacode.tools.xml_helper import load_prompt_from_xml

# Valid status values
VALID_STATUSES = frozenset({"pending", "in_progress", "completed"})

# Status display symbols
STATUS_SYMBOLS = {
    "pending": "[ ]",
    "in_progress": "[>]",
    "completed": "[x]",
}


def _validate_todo(todo: dict[str, Any], index: int) -> None:
    """Validate a single todo item has required fields.

    Args:
        todo: The todo dictionary to validate.
        index: The index of the todo in the list (for error messages).

    Raises:
        ModelRetry: If validation fails.
    """
    if not isinstance(todo, dict):
        raise ModelRetry(f"Todo at index {index} must be a dictionary, got {type(todo).__name__}")

    required_fields = ("content", "status", "activeForm")
    missing = [f for f in required_fields if f not in todo]
    if missing:
        raise ModelRetry(f"Todo at index {index} missing required fields: {', '.join(missing)}")

    if todo["status"] not in VALID_STATUSES:
        raise ModelRetry(
            f"Todo at index {index} has invalid status '{todo['status']}'. "
            f"Must be one of: {', '.join(sorted(VALID_STATUSES))}"
        )

    if not todo["content"] or not isinstance(todo["content"], str):
        raise ModelRetry(f"Todo at index {index} must have non-empty string 'content'")

    if not todo["activeForm"] or not isinstance(todo["activeForm"], str):
        raise ModelRetry(f"Todo at index {index} must have non-empty string 'activeForm'")


def _format_todos(todos: list[dict[str, Any]]) -> str:
    """Format todos for display output.

    Args:
        todos: List of todo dictionaries.

    Returns:
        Formatted string representation of the todo list.
    """
    if not todos:
        return "No todos in list."

    lines = []
    for i, todo in enumerate(todos, 1):
        symbol = STATUS_SYMBOLS.get(todo["status"], "[ ]")
        content = todo["content"]
        active_form = todo.get("activeForm", "")

        if todo["status"] == "in_progress" and active_form:
            lines.append(f"{i}. {symbol} {content} ({active_form})")
        else:
            lines.append(f"{i}. {symbol} {content}")

    return "\n".join(lines)


def create_todowrite_tool(state_manager: StateManager) -> Callable:
    """Factory to create a todowrite tool bound to a state manager.

    Args:
        state_manager: The state manager instance to use.

    Returns:
        An async function that implements the todowrite tool.
    """

    async def todowrite(todos: list[dict[str, Any]]) -> str:
        """Create or update the todo list for tracking task progress.

        Use this tool to manage and display tasks during complex multi-step operations.
        The entire todo list is replaced with each call.

        Args:
            todos: List of todo items. Each item must have:
                - content: Task description in imperative form (e.g., "Fix the bug")
                - status: One of "pending", "in_progress", or "completed"
                - activeForm: Present continuous form for display (e.g., "Fixing the bug")

        Returns:
            Formatted display of the updated todo list.
        """
        if not isinstance(todos, list):
            raise ModelRetry(f"todos must be a list, got {type(todos).__name__}")

        for i, todo in enumerate(todos):
            _validate_todo(todo, i)

        state_manager.set_todos(todos)
        return _format_todos(todos)

    # Load prompt from XML if available
    prompt = load_prompt_from_xml("todowrite")
    if prompt:
        todowrite.__doc__ = prompt

    return todowrite


def create_todoread_tool(state_manager: StateManager) -> Callable:
    """Factory to create a todoread tool bound to a state manager.

    Args:
        state_manager: The state manager instance to use.

    Returns:
        An async function that implements the todoread tool.
    """

    async def todoread() -> str:
        """Read the current todo list.

        Use this tool to check the current state of all tasks.

        Returns:
            Formatted display of the current todo list, or a message if empty.
        """
        todos = state_manager.get_todos()
        return _format_todos(todos)

    # Load prompt from XML if available
    prompt = load_prompt_from_xml("todoread")
    if prompt:
        todoread.__doc__ = prompt

    return todoread


def create_todoclear_tool(state_manager: StateManager) -> Callable:
    """Factory to create a todoclear tool bound to a state manager.

    Args:
        state_manager: The state manager instance to use.

    Returns:
        An async function that implements the todoclear tool.
    """

    async def todoclear() -> str:
        """Clear the entire todo list.

        Use this tool when starting fresh or when all tasks are complete.

        Returns:
            Confirmation message.
        """
        state_manager.clear_todos()
        return "Todo list cleared."

    return todoclear
