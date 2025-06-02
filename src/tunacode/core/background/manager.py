"""Asynchronous background task management utilities."""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from typing import Awaitable, Callable, Dict, List


class BackgroundTaskManager:
    """Simple manager for background asyncio tasks."""

    def __init__(self) -> None:
        self.tasks: Dict[str, asyncio.Task] = {}
        self.listeners: Dict[str, List[Callable[[asyncio.Task], None]]] = defaultdict(list)

    def spawn(self, coro: Awaitable, *, name: str | None = None) -> str:
        task_id = name or uuid.uuid4().hex[:8]
        task = asyncio.create_task(coro, name=task_id)
        self.tasks[task_id] = task
        task.add_done_callback(self._notify)
        return task_id

    def _notify(self, task: asyncio.Task) -> None:
        for cb in self.listeners.get(task.get_name(), []):
            cb(task)

    async def shutdown(self) -> None:
        for task in self.tasks.values():
            task.cancel()
        if self.tasks:
            await asyncio.gather(*self.tasks.values(), return_exceptions=True)


BG_MANAGER = BackgroundTaskManager()
