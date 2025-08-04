"""Tool buffer for managing parallel execution of read-only tools."""

from typing import Any, List, Tuple


class ToolBuffer:
    """Buffer for collecting read-only tool calls to execute in parallel."""

    def __init__(self):
        self.read_only_tasks: List[Tuple[Any, Any]] = []

    def add(self, part: Any, node: Any) -> None:
        """Add a read-only tool call to the buffer."""
        self.read_only_tasks.append((part, node))

    def flush(self) -> List[Tuple[Any, Any]]:
        """Return buffered tasks and clear the buffer."""
        tasks = self.read_only_tasks
        self.read_only_tasks = []
        return tasks

    def has_tasks(self) -> bool:
        """Check if there are buffered tasks."""
        return len(self.read_only_tasks) > 0
