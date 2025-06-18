import pytest
import asyncio
from tunacode.core.background.manager import BackgroundTaskManager

@pytest.mark.asyncio
async def test_shutdown_cancels_running_tasks():
    manager = BackgroundTaskManager()
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def long_running():
        started.set()
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled.set()
            raise

    task_id = manager.spawn(long_running(), name="longtask")
    await started.wait()
    await manager.shutdown()
    task = manager.tasks[task_id]
    assert task.cancelled() or (task.done() and isinstance(task.exception(), asyncio.CancelledError))
    assert cancelled.is_set()

@pytest.mark.asyncio
async def test_shutdown_handles_multiple_tasks():
    manager = BackgroundTaskManager()
    events = [asyncio.Event() for _ in range(3)]

    async def sleeper(ev):
        ev.set()
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            return "cancelled"

    ids = [manager.spawn(sleeper(ev), name=f"t{i}") for i, ev in enumerate(events)]
    for ev in events:
        await ev.wait()
    await manager.shutdown()
    for tid in ids:
        task = manager.tasks[tid]
        # Current behavior: tasks catch CancelledError and return 'cancelled'
        assert task.done() and task.result() == "cancelled"