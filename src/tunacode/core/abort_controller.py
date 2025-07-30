"""
Module: tunacode.core.abort_controller

Provides structured cancellation mechanism using asyncio's event system.
Handles cancellation and interruption for long-running operations.
"""

import asyncio
import logging
import uuid
from typing import Optional

# Import debug system
try:
    from tunacode.debug.trio_debug import trio_debug, debug_trio_function
    DEBUG_AVAILABLE = True
except ImportError:
    DEBUG_AVAILABLE = False
    def debug_trio_function(component):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)


class AbortController:
    """
    Centralized cancellation controller for asyncio-based operations.
    
    Provides a unified mechanism for aborting long-running operations
    across the entire application, including agent processing, tool
    execution, and UI operations.
    """
    
    def __init__(self):
        self._abort_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []
        self._aborted = False
        self._controller_id = f"abort-{uuid.uuid4().hex[:8]}"
        
        # Debug logging
        if DEBUG_AVAILABLE:
            trio_debug.abort_controller_created(self._controller_id)
    
    @debug_trio_function("AbortController")
    def abort(self, trigger: str = "Manual") -> None:
        """
        Signal all controlled operations to abort.
        This method is safe to call from any context, including signal handlers.
        """
        if self._aborted:
            return
            
        self._aborted = True
        self._abort_event.set()
        
        # Debug logging
        if DEBUG_AVAILABLE:
            trio_debug.abort_controller_aborted(self._controller_id, trigger)
        
        # Cancel all registered tasks
        for task in self._tasks:
            if not task.done():
                print(f"🔥 FORCE CANCELLING TASK: {task}")
                task.cancel()
                if DEBUG_AVAILABLE:
                    trio_debug.cancel_scope_cancelled(f"task-{id(task)}", f"AbortController {trigger}")
            
        logger.debug(f"AbortController: abort signal sent (trigger: {trigger})")
    
    def is_aborted(self) -> bool:
        """Check if abort has been requested."""
        return self._aborted
    
    async def check_abort(self) -> None:
        """
        Check if abort has been requested and raise CancelledError if so.
        Call this periodically in long-running operations.
        """
        if self._aborted:
            raise asyncio.CancelledError("Operation was aborted")
    
    async def wait_for_abort(self) -> None:
        """Wait until abort is requested."""
        await self._abort_event.wait()
    
    @debug_trio_function("AbortController") 
    def add_task(self, task: asyncio.Task) -> None:
        """Associate a task for automatic cancellation."""
        self._tasks.append(task)
        
        # Debug logging
        if DEBUG_AVAILABLE:
            task_id = f"task-{id(task)}"
            trio_debug.cancel_scope_created(task_id)
            trio_debug.log_event("TASK_LINKED", "AbortController", 
                               f"{self._controller_id} -> {task_id}")
    
    @debug_trio_function("AbortController")
    def reset(self) -> None:
        """Reset the controller for reuse."""
        self._abort_event = asyncio.Event()
        self._tasks.clear()
        self._aborted = False
        
        # Debug logging
        if DEBUG_AVAILABLE:
            trio_debug.abort_controller_reset(self._controller_id)
            
        logger.debug("AbortController: reset")


class AppContext:
    """
    Application-wide context that holds the abort controller.
    This provides structured access to asyncio's concurrency primitives throughout
    the application.
    """
    
    def __init__(self, abort_controller: AbortController):
        import threading
        self.cancel_flag = threading.Event()  # Shared across all operations
        self.abort_controller = abort_controller
        self._shutdown_requested = False
    
    def request_shutdown(self) -> None:
        """Request graceful application shutdown."""
        self._shutdown_requested = True
        self.abort_controller.abort()
    
    def is_shutdown_requested(self) -> bool:
        """Check if graceful shutdown has been requested."""
        return self._shutdown_requested