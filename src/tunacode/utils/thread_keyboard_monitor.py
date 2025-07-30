"""
Thread-based keyboard monitor for Esc key detection during agent processing.

This monitor runs in a separate thread and can detect Esc key presses
even when the main thread is blocked on async operations.
"""

import sys
import threading
import time
import select
import termios
import tty
from typing import Optional


class ThreadKeyboardMonitor:
    """Thread-based keyboard monitor for Esc key detection."""
    
    def __init__(self, interrupt_callback):
        """
        Initialize the keyboard monitor.
        
        Args:
            interrupt_callback: Function to call when Esc is pressed
        """
        self.interrupt_callback = interrupt_callback
        self._monitoring = False
        self._thread: Optional[threading.Thread] = None
        self._original_settings = None
        
    def start_monitoring(self):
        """Start monitoring for Esc key in a separate thread."""
        if not sys.stdin.isatty() or self._monitoring:
            return
            
        self._monitoring = True
        self._thread = threading.Thread(target=self._monitor_keyboard, daemon=True)
        self._thread.start()
        
    def stop_monitoring(self):
        """Stop keyboard monitoring."""
        self._monitoring = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.1)
        self._restore_terminal()
        
    def _monitor_keyboard(self):
        """Monitor keyboard input in a separate thread."""
        try:
            # Save terminal settings
            self._original_settings = termios.tcgetattr(sys.stdin.fileno())
            # Set terminal to raw mode for immediate key detection
            tty.setraw(sys.stdin.fileno())
            
            while self._monitoring:
                try:
                    # Check if input is available (non-blocking)
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1)
                        
                        # Check for Esc key (ASCII 27)
                        if ord(key) == 27:
                            # Trigger the interrupt callback
                            self.interrupt_callback()
                            break
                            
                except (OSError, ValueError):
                    # Terminal might not be available or in wrong state
                    break
                except Exception:
                    # Other errors, continue monitoring
                    time.sleep(0.1)
                    
        except (OSError, termios.error):
            # Can't set raw mode, monitoring not possible
            pass
        finally:
            self._restore_terminal()
    
    def _restore_terminal(self):
        """Restore original terminal settings."""
        if self._original_settings and sys.stdin.isatty():
            try:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._original_settings)
            except (OSError, termios.error):
                pass
            self._original_settings = None


# Global monitor instance
_global_monitor: Optional[ThreadKeyboardMonitor] = None


def start_global_esc_monitoring(interrupt_callback):
    """Start global Esc key monitoring."""
    global _global_monitor
    
    if _global_monitor:
        stop_global_esc_monitoring()
    
    _global_monitor = ThreadKeyboardMonitor(interrupt_callback)
    _global_monitor.start_monitoring()


def stop_global_esc_monitoring():
    """Stop global Esc key monitoring."""
    global _global_monitor
    
    if _global_monitor:
        _global_monitor.stop_monitoring()
        _global_monitor = None


def is_monitoring():
    """Check if monitoring is active."""
    global _global_monitor
    return _global_monitor is not None and _global_monitor._monitoring