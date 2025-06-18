import pytest
import asyncio
from unittest.mock import Mock
from tunacode.core.background.manager import BackgroundTaskManager

@pytest.mark.asyncio
async def test_task_exception_is_propagated():
    manager = BackgroundTaskManager()
    async def fail():
        raise ValueError("fail!")
    task_id = manager.spawn(fail(), name="failtask")
    task = manager.tasks[task_id]
    await asyncio.wait([task])
    assert task.done()
    with pytest.raises(ValueError):
        task.result()

@pytest.mark.asyncio
async def test_listener_exception_does_not_crash_manager():
    manager = BackgroundTaskManager()
    bad_cb = Mock(side_effect=RuntimeError("listener fail"))
    good_cb = Mock()
    async def work():
        return 1
    task_id = manager.spawn(work(), name="cbfail")
    manager.listeners["cbfail"].extend([bad_cb, good_cb])
    task = manager.tasks[task_id]
    await asyncio.wait([task])
    # Current behavior: exception in listener stops further processing
    # bad_cb is called and raises, good_cb is NOT called
    bad_cb.assert_called_once_with(task)
    good_cb.assert_not_called()

@pytest.mark.asyncio
async def test_spawn_with_duplicate_name_overwrites_task():
    manager = BackgroundTaskManager()
    async def work1():
        return "first"
    async def work2():
        return "second"
    manager.spawn(work1(), name="dup")
    # Overwrite with new task of same name
    manager.spawn(work2(), name="dup")
    # Only the latest task is tracked
    assert list(manager.tasks.keys()).count("dup") == 1
    await asyncio.wait([manager.tasks["dup"]])
    assert manager.tasks["dup"].result() == "second"

def test_spawn_non_awaitable_raises():
    manager = BackgroundTaskManager()
    # Current behavior: RuntimeError due to no running event loop
    with pytest.raises(RuntimeError, match="no running event loop"):
        manager.spawn(123)  # Not awaitable

@pytest.mark.asyncio
async def test_rapid_spawn_and_shutdown():
    manager = BackgroundTaskManager()
    async def sleeper():
        await asyncio.sleep(0.01)
    for _ in range(10):
        manager.spawn(sleeper())
    await manager.shutdown()
    # All tasks should be done or cancelled
    assert all(t.done() or t.cancelled() for t in manager.tasks.values())