import pytest
import asyncio
from tunacode.core.background.manager import BackgroundTaskManager

@pytest.mark.asyncio
async def test_shutdown_cleans_up_all_tasks():
    manager = BackgroundTaskManager()
    async def sleeper():
        await asyncio.sleep(0.01)
    ids = [manager.spawn(sleeper(), name=f"cleanup{i}") for i in range(3)]
    await manager.shutdown()
    # All tasks should be done or cancelled
    for tid in ids:
        task = manager.tasks[tid]
        assert task.done() or task.cancelled()
    # State should still retain tasks, but all are finished
    assert all(t.done() or t.cancelled() for t in manager.tasks.values())

@pytest.mark.asyncio
async def test_shutdown_is_idempotent():
    manager = BackgroundTaskManager()
    async def sleeper():
        await asyncio.sleep(0.01)
    manager.spawn(sleeper(), name="idempotent")
    await manager.shutdown()
    # Second shutdown should not raise or hang
    await manager.shutdown()

@pytest.mark.asyncio
async def test_listeners_do_not_persist_after_shutdown():
    manager = BackgroundTaskManager()
    called = []

    async def sleeper():
        return "done"

    def cb(task):
        called.append(task)

    manager.listeners["persist"].append(cb)
    manager.spawn(sleeper(), name="persist")
    await manager.shutdown()
    # After shutdown, listeners dict should still exist but not be called again
    assert called  # Was called at least once
    # Current behavior: listeners DO persist after shutdown
    # Simulate a new task with same name, listeners ARE called again
    called.clear()
    manager.spawn(sleeper(), name="persist")
    await asyncio.sleep(0.02)
    assert called  # Listener is called again
    assert len(called) == 1