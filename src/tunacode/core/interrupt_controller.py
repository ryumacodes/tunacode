"""
Interrupt controller for handling Esc key cancellation during agent processing.
"""

import asyncio
import threading
from typing import Optional


class InterruptController:
    """Global interrupt controller for handling Esc key cancellation."""
    
    def __init__(self):
        self._interrupt_event = asyncio.Event()
        self._interrupted = False
        self._lock = threading.Lock()
    
    def trigger_interrupt(self) -> None:
        """Trigger an interrupt (safe to call from any context)."""
        with self._lock:
            self._interrupted = True
            # Try to set the event if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                loop.call_soon_threadsafe(self._interrupt_event.set)
            except RuntimeError:
                # No running loop, the event will be checked synchronously
                pass
    
    def is_interrupted(self) -> bool:
        """Check if an interrupt has been triggered."""
        with self._lock:
            return self._interrupted
    
    async def wait_for_interrupt(self) -> None:
        """Wait for an interrupt to be triggered."""
        await self._interrupt_event.wait()
    
    def reset(self) -> None:
        """Reset the interrupt state."""
        with self._lock:
            self._interrupted = False
            self._interrupt_event.clear()
    
    async def check_interrupt(self) -> None:
        """Check for interrupt and raise CancelledError if interrupted."""
        if self.is_interrupted():
            raise asyncio.CancelledError("Operation interrupted by user")


# Global interrupt controller instance
_global_interrupt_controller: Optional[InterruptController] = None


def get_interrupt_controller() -> InterruptController:
    """Get the global interrupt controller instance."""
    global _global_interrupt_controller
    if _global_interrupt_controller is None:
        _global_interrupt_controller = InterruptController()
    return _global_interrupt_controller


def trigger_global_interrupt() -> None:
    """Trigger a global interrupt (convenience function)."""
    get_interrupt_controller().trigger_interrupt()


def reset_global_interrupt() -> None:
    """Reset the global interrupt state (convenience function)."""
    get_interrupt_controller().reset()


async def check_global_interrupt() -> None:
    """Check for global interrupt and raise CancelledError if interrupted."""
    await get_interrupt_controller().check_interrupt()