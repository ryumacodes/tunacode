#!/usr/bin/env python3
"""Test the background task manager."""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def test_background_task_manager():
    from tunacode.core.background.manager import BG_MANAGER

    async def dummy():
        await asyncio.sleep(0.01)
        return 42

    tid = BG_MANAGER.spawn(dummy())
    assert tid in BG_MANAGER.tasks
    asyncio.run(BG_MANAGER.shutdown())
    print("✓ BackgroundTaskManager spawn/shutdown")
    return True
