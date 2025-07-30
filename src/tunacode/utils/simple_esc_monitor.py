"""
Simple Esc key monitor that works during background processing.
"""

import sys
import threading
import time
import select
import termios
import tty
from typing import Optional, Callable


class SimpleEscMonitor:
    """Simple monitor for Esc key during background operations."""
    
    def __init__(self):
        self._monitoring = False
        self._thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable] = None
        self._original_settings = None
    
    def start(self, callback: Callable) -> bool:
        """Start monitoring for Esc key."""
        if not sys.stdin.isatty() or self._monitoring:
            return False
        
        self._callback = callback
        self._monitoring = True
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()
        return True
    
    def stop(self):
        """Stop monitoring."""
        self._monitoring = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.2)
        self._restore_terminal()
    
    def _monitor(self):
        """Monitor for Esc key in background thread."""
        try:
            # Save terminal settings
            self._original_settings = termios.tcgetattr(sys.stdin.fileno())
            
            # Set terminal to cbreak mode instead of raw mode
            # This is less intrusive and allows Rich to continue working
            new_settings = termios.tcgetattr(sys.stdin.fileno())
            new_settings[3] &= ~termios.ECHO
            new_settings[3] &= ~termios.ICANON
            new_settings[6][termios.VMIN] = 0
            new_settings[6][termios.VTIME] = 0
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, new_settings)
            
            while self._monitoring:
                try:
                    # Non-blocking check for input
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1)
                        if ord(key) == 27:  # Esc key
                            if self._callback:
                                self._callback()
                            break
                except (OSError, ValueError):
                    break
                    
        except (OSError, termios.error):
            # Terminal operations failed
            pass
        finally:
            self._restore_terminal()
    
    def _restore_terminal(self):
        """Restore original terminal settings."""
        if self._original_settings:
            try:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._original_settings)
            except (OSError, termios.error):
                pass
            self._original_settings = None


# Global monitor instance
_monitor: Optional[SimpleEscMonitor] = None


def start_esc_monitoring(callback: Callable) -> bool:
    """Start global Esc monitoring."""
    global _monitor
    
    if _monitor:
        _monitor.stop()
    
    _monitor = SimpleEscMonitor()
    return _monitor.start(callback)


def stop_esc_monitoring():
    """Stop global Esc monitoring."""
    global _monitor
    
    if _monitor:
        _monitor.stop()
        _monitor = None