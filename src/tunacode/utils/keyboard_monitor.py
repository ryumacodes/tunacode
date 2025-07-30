"""
Keyboard monitoring utilities for capturing Esc key during agent processing.

This module provides a way to monitor for Esc key presses even when prompt_toolkit
is not active, enabling cancellation during "Thinking..." phases.
"""

import sys
import asyncio
import termios
import tty
import select
from typing import Optional

# Import debug system
try:
    from tunacode.debug.trio_debug import trio_debug
    DEBUG_AVAILABLE = True
except ImportError:
    DEBUG_AVAILABLE = False


class KeyboardMonitor:
    """
    Monitor keyboard input for Esc key presses during background operations.
    
    This works by reading from stdin in non-blocking mode while the main
    operation runs, allowing us to detect Esc key presses even when
    prompt_toolkit is not active.
    """
    
    def __init__(self, abort_controller):
        self.abort_controller = abort_controller
        self._monitoring = False
        self._original_settings = None
        
    async def start_monitoring(self):
        """Start monitoring for Esc key presses."""
        if not sys.stdin.isatty():
            # Can't monitor keyboard on non-terminal input
            return
            
        self._monitoring = True
        self._original_settings = termios.tcgetattr(sys.stdin.fileno())
        
        if DEBUG_AVAILABLE:
            trio_debug.log_event("KEYBOARD_MONITOR", "KeyboardMonitor", "Started Esc key monitoring", "INFO")
        
        try:
            # Set terminal to raw mode for immediate key detection
            tty.setraw(sys.stdin.fileno())
            
            # Monitor keyboard in background
            self._monitor_task = asyncio.create_task(self._monitor_keyboard())
            await self._monitor_task
                
        except Exception as e:
            if DEBUG_AVAILABLE:
                trio_debug.log_event("KEYBOARD_ERROR", "KeyboardMonitor", f"Monitoring error: {e}", "ERROR")
            await self.stop_monitoring()
    
    async def stop_monitoring(self):
        """Stop keyboard monitoring and restore terminal settings."""
        self._monitoring = False
        
        if self._original_settings and sys.stdin.isatty():
            try:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._original_settings)
                if DEBUG_AVAILABLE:
                    trio_debug.log_event("KEYBOARD_MONITOR", "KeyboardMonitor", "Stopped Esc key monitoring", "INFO")
            except Exception as e:
                if DEBUG_AVAILABLE:
                    trio_debug.log_event("KEYBOARD_ERROR", "KeyboardMonitor", f"Restore error: {e}", "ERROR")
        
        self._original_settings = None
    
    async def _monitor_keyboard(self):
        """Background task to monitor for Esc key presses."""
        while self._monitoring:
            try:
                # Check if input is available (non-blocking)
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key = sys.stdin.read(1)
                    
                    if DEBUG_AVAILABLE:
                        trio_debug.log_event("KEY_DETECTED", "KeyboardMonitor", f"Key pressed: {repr(key)}", "INFO")
                    
                    # Check for Esc key (ASCII 27)
                    if ord(key) == 27:
                        if DEBUG_AVAILABLE:
                            trio_debug.log_event("ESC_DETECTED", "KeyboardMonitor", "Esc key detected - triggering abort", "SUCCESS")
                        
                        # Trigger the abort controller and interrupt controller
                        self.abort_controller.abort(trigger="Esc key (keyboard monitor)")
                        
                        # Also trigger global interrupt
                        from tunacode.core.interrupt_controller import trigger_global_interrupt
                        trigger_global_interrupt()
                        
                        await self.stop_monitoring()
                        break
                        
                else:
                    # No input available, yield control
                    await asyncio.sleep(0.05)  # 50ms polling interval
                    
            except Exception as e:
                if DEBUG_AVAILABLE:
                    trio_debug.log_event("KEYBOARD_ERROR", "KeyboardMonitor", f"Monitor error: {e}", "ERROR")
                await asyncio.sleep(0.1)  # Longer wait on error


async def monitor_esc_during_operation(abort_controller, operation_func, *args, **kwargs):
    """
    Run an operation while monitoring for Esc key presses.
    
    Args:
        abort_controller: The AbortController to trigger on Esc
        operation_func: The async function to run
        *args, **kwargs: Arguments to pass to operation_func
    
    Returns:
        The result of operation_func, or raises asyncio.CancelledError if Esc was pressed
    """
    monitor = KeyboardMonitor(abort_controller)
    
    try:
        # Start keyboard monitoring and main operation concurrently
        monitor_task = asyncio.create_task(monitor.start_monitoring())
        operation_task = asyncio.create_task(operation_func(*args, **kwargs))
        
        # Wait for either to complete
        done, pending = await asyncio.wait([monitor_task, operation_task], return_when=asyncio.FIRST_COMPLETED)
        
        # Cancel any pending tasks 
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # If operation completed first, return result
        if operation_task in done:
            await monitor.stop_monitoring()
            return operation_task.result()
        else:
            # Monitor completed first (Esc was pressed)
            await monitor.stop_monitoring()
            raise asyncio.CancelledError("Operation cancelled by Esc key")
            
    except asyncio.CancelledError:
        # Operation was cancelled (likely by Esc key)
        await monitor.stop_monitoring()
        raise
    except Exception as e:
        # Other error occurred
        await monitor.stop_monitoring()
        raise


async def monitor_esc_during_task(abort_controller, existing_task):
    """
    Monitor for Esc key presses while an existing task runs.
    
    Args:
        abort_controller: The AbortController to trigger on Esc
        existing_task: An existing asyncio.Task to monitor
    
    Returns:
        The result of the task, or raises asyncio.CancelledError if Esc was pressed
    """
    monitor = KeyboardMonitor(abort_controller)
    
    try:
        # Start keyboard monitoring
        monitor_task = asyncio.create_task(monitor.start_monitoring())
        
        # Wait for either the existing task or the monitor to complete
        done, pending = await asyncio.wait([monitor_task, existing_task], return_when=asyncio.FIRST_COMPLETED)
        
        # Cancel any pending tasks 
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # If the main task completed first, return its result
        if existing_task in done:
            await monitor.stop_monitoring()
            return existing_task.result()
        else:
            # Monitor completed first (Esc was pressed)
            await monitor.stop_monitoring()
            raise asyncio.CancelledError("Operation cancelled by Esc key")
            
    except asyncio.CancelledError:
        # Operation was cancelled (likely by Esc key)
        await monitor.stop_monitoring()
        raise
    except Exception as e:
        # Other error occurred
        await monitor.stop_monitoring()
        raise