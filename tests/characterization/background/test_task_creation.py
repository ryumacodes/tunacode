import pytest
import asyncio
from tunacode.core.background.manager import BackgroundTaskManager

@pytest.mark.asyncio
async def test_spawn_creates_task_and_returns_id():
    manager = BackgroundTaskManager()

    async def dummy_coro():
        await asyncio.sleep(0.01)
        return 42

    task_id = manager.spawn(dummy_coro())
    assert isinstance(task_id, str)
    assert task_id in manager.tasks
    task = manager.tasks[task_id]
    assert isinstance(task, asyncio.Task)
    await asyncio.wait([task])
    assert task.done()
    assert task.result() == 42

@pytest.mark.asyncio
async def test_spawn_with_name_uses_given_name():
    manager = BackgroundTaskManager()

    async def dummy_coro():
        return "named"

    task_id = manager.spawn(dummy_coro(), name="mytask")
    assert task_id == "mytask"
    assert "mytask" in manager.tasks
    await asyncio.wait([manager.tasks["mytask"]])
    assert manager.tasks["mytask"].done()
    assert manager.tasks["mytask"].result() == "named"

@pytest.mark.asyncio
async def test_spawn_multiple_tasks_unique_ids():
    manager = BackgroundTaskManager()

    async def dummy_coro():
        await asyncio.sleep(0.01)
        return "ok"

    ids = {manager.spawn(dummy_coro()) for _ in range(5)}
    assert len(ids) == 5
    for task_id in ids:
        assert task_id in manager.tasks
        await asyncio.wait([manager.tasks[task_id]])
        assert manager.tasks[task_id].done()
        assert manager.tasks[task_id].result() == "ok"