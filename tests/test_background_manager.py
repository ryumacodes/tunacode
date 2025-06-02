#!/usr/bin/env python3
"""Test the background task manager."""

import sys
import os
import asyncio
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))


@pytest.mark.asyncio
async def test_background_task_manager():
    from tunacode.core.background.manager import BackgroundTaskManager
    
    # Create a fresh instance for testing
    manager = BackgroundTaskManager()

    async def dummy():
        await asyncio.sleep(0.01)
        return 42

    tid = manager.spawn(dummy())
    assert tid in manager.tasks
    await manager.shutdown()
    print("✓ BackgroundTaskManager spawn/shutdown")
