import pytest
import asyncio
from unittest.mock import Mock
from tunacode.core.background.manager import BackgroundTaskManager

@pytest.mark.asyncio
async def test_task_runs_to_completion_and_result_is_accessible():
    manager = BackgroundTaskManager()

    async def work():
        await asyncio.sleep(0.01)
        return "done"

    task_id = manager.spawn(work())
    task = manager.tasks[task_id]
    await asyncio.wait([task])
    assert task.done()
    assert task.result() == "done"

@pytest.mark.asyncio
async def test_listener_is_called_on_task_completion():
    manager = BackgroundTaskManager()
    callback = Mock()

    async def work():
        await asyncio.sleep(0.01)
        return 123

    task_id = manager.spawn(work(), name="cbtask")
    manager.listeners["cbtask"].append(callback)
    task = manager.tasks[task_id]
    await asyncio.wait([task])
    callback.assert_called_once_with(task)

@pytest.mark.asyncio
async def test_multiple_listeners_are_called():
    manager = BackgroundTaskManager()
    cb1 = Mock()
    cb2 = Mock()

    async def work():
        return "multi"

    task_id = manager.spawn(work(), name="multicb")
    manager.listeners["multicb"].extend([cb1, cb2])
    task = manager.tasks[task_id]
    await asyncio.wait([task])
    cb1.assert_called_once_with(task)
    cb2.assert_called_once_with(task)