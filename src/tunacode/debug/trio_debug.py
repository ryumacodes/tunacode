"""
Debug visualization system for Trio migration live testing.

Provides comprehensive visual feedback for:
- Nursery lifecycle and task spawning
- AbortController state changes
- CancelScope operations
- Signal handling
- Prompt recovery
- Background task management
"""

import time
from typing import Optional, Dict, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.align import Align
from datetime import datetime
import trio

console = Console()

class TrioDebugVisualizer:
    """Visual debugger for Trio migration components."""
    
    def __init__(self):
        self.events: List[Dict] = []
        self.nursery_count = 0
        self.task_count = 0
        self.cancel_scopes: Dict[str, Dict] = {}
        self.abort_controllers: Dict[str, Dict] = {}
        self.active_nurseries: Dict[str, Dict] = {}
        self.live_display: Optional[Live] = None
        self.minimal_mode = False
        self.start_time = time.time()

    def start_live_display(self, minimal_mode=True):
        """Start the live debug display."""
        if minimal_mode:
            # In minimal mode, just log events without taking over the terminal
            self.minimal_mode = True
            console.print("🚀 Debug mode enabled - events will be logged in the background")
            console.print("Use '/debug summary' to see the full report")
        else:
            # Full live display mode (can be intrusive)
            self.live_display = Live(self._create_debug_panel(), refresh_per_second=10)
            self.live_display.start()
            self.minimal_mode = False

    def stop_live_display(self):
        """Stop the live debug display."""
        if self.live_display:
            self.live_display.stop()
            self.live_display = None
        if hasattr(self, 'minimal_mode'):
            self.minimal_mode = False
            console.print("Debug mode disabled")

    def log_event(self, event_type: str, component: str, details: str, level: str = "INFO"):
        """Log a debug event with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        elapsed = time.time() - self.start_time
        
        event = {
            "timestamp": timestamp,
            "elapsed": f"{elapsed:.3f}s",
            "type": event_type,
            "component": component,
            "details": details,
            "level": level
        }
        
        self.events.append(event)
        if len(self.events) > 50:  # Keep only last 50 events
            self.events.pop(0)
            
        # Update live display if active (but not in minimal mode)
        if self.live_display and not self.minimal_mode:
            self.live_display.update(self._create_debug_panel())

    def nursery_created(self, nursery_id: str, parent_id: Optional[str] = None):
        """Log nursery creation."""
        self.nursery_count += 1
        self.active_nurseries[nursery_id] = {
            "id": nursery_id,
            "parent": parent_id,
            "tasks": [],
            "created_at": time.time(),
            "status": "active"
        }
        
        details = f"Nursery #{self.nursery_count}"
        if parent_id:
            details += f" (parent: {parent_id})"
            
        self.log_event("NURSERY_CREATE", "Trio", details, "SUCCESS")

    def nursery_closed(self, nursery_id: str):
        """Log nursery closure."""
        if nursery_id in self.active_nurseries:
            self.active_nurseries[nursery_id]["status"] = "closed"
            task_count = len(self.active_nurseries[nursery_id]["tasks"])
            self.log_event("NURSERY_CLOSE", "Trio", f"{nursery_id} ({task_count} tasks)", "INFO")

    def task_spawned(self, nursery_id: str, task_name: str, task_id: str):
        """Log task spawning in nursery."""
        self.task_count += 1
        
        if nursery_id in self.active_nurseries:
            self.active_nurseries[nursery_id]["tasks"].append({
                "name": task_name,
                "id": task_id,
                "spawned_at": time.time()
            })
            
        self.log_event("TASK_SPAWN", "Trio", f"{task_name} in {nursery_id}", "INFO")

    def cancel_scope_created(self, scope_id: str, timeout: Optional[float] = None):
        """Log CancelScope creation."""
        self.cancel_scopes[scope_id] = {
            "id": scope_id,
            "timeout": timeout,
            "cancelled": False,
            "created_at": time.time()
        }
        
        details = f"Scope {scope_id}"
        if timeout:
            details += f" (timeout: {timeout}s)"
            
        self.log_event("CANCEL_SCOPE_CREATE", "Trio", details, "INFO")

    def cancel_scope_cancelled(self, scope_id: str, reason: str = "Manual"):
        """Log CancelScope cancellation."""
        if scope_id in self.cancel_scopes:
            self.cancel_scopes[scope_id]["cancelled"] = True
            
        self.log_event("CANCEL_SCOPE_CANCEL", "Trio", f"{scope_id} ({reason})", "WARNING")

    def abort_controller_created(self, controller_id: str):
        """Log AbortController creation."""
        self.abort_controllers[controller_id] = {
            "id": controller_id,
            "aborted": False,
            "reset_count": 0,
            "created_at": time.time()
        }
        
        self.log_event("ABORT_CONTROLLER_CREATE", "AbortController", controller_id, "SUCCESS")

    def abort_controller_aborted(self, controller_id: str, trigger: str = "Unknown"):
        """Log AbortController abort."""
        if controller_id in self.abort_controllers:
            self.abort_controllers[controller_id]["aborted"] = True
            
        self.log_event("ABORT_SIGNAL", "AbortController", f"{controller_id} triggered by {trigger}", "ERROR")

    def abort_controller_reset(self, controller_id: str):
        """Log AbortController reset."""
        if controller_id in self.abort_controllers:
            self.abort_controllers[controller_id]["aborted"] = False
            self.abort_controllers[controller_id]["reset_count"] += 1
            
        self.log_event("ABORT_RESET", "AbortController", controller_id, "INFO")

    def signal_received(self, signal_name: str, handler: str):
        """Log signal reception."""
        self.log_event("SIGNAL_RECEIVED", "Signal", f"{signal_name} -> {handler}", "WARNING")

    def prompt_interrupted(self, reason: str):
        """Log prompt interruption."""
        self.log_event("PROMPT_INTERRUPT", "UI", reason, "WARNING")

    def prompt_recovered(self, recovery_time: float):
        """Log prompt recovery."""
        self.log_event("PROMPT_RECOVERY", "UI", f"Recovered in {recovery_time:.3f}s", "SUCCESS")

    def key_pressed(self, key: str, action: str):
        """Log key press events."""
        self.log_event("KEY_PRESS", "Input", f"{key} -> {action}", "INFO")

    def streaming_started(self, stream_id: str):
        """Log streaming start."""
        self.log_event("STREAM_START", "Agent", stream_id, "INFO")

    def streaming_stopped(self, stream_id: str, reason: str):
        """Log streaming stop."""
        self.log_event("STREAM_STOP", "Agent", f"{stream_id} ({reason})", "INFO")

    def _create_debug_panel(self) -> Panel:
        """Create the main debug panel."""
        # Create statistics table
        stats_table = Table(title="🚀 Trio Migration Live Debug", show_header=True, header_style="bold magenta")
        stats_table.add_column("Component", style="cyan")
        stats_table.add_column("Active", style="green")
        stats_table.add_column("Total", style="blue")
        stats_table.add_column("Status", style="yellow")
        
        # Nursery stats
        active_nurseries = len([n for n in self.active_nurseries.values() if n["status"] == "active"])
        stats_table.add_row("Nurseries", str(active_nurseries), str(self.nursery_count), "✅ Running")
        
        # Task stats
        total_tasks = sum(len(n["tasks"]) for n in self.active_nurseries.values())
        stats_table.add_row("Tasks", str(total_tasks), str(self.task_count), "✅ Managed")
        
        # CancelScope stats
        active_scopes = len([s for s in self.cancel_scopes.values() if not s["cancelled"]])
        stats_table.add_row("CancelScopes", str(active_scopes), str(len(self.cancel_scopes)), "✅ Protected")
        
        # AbortController stats
        active_controllers = len([c for c in self.abort_controllers.values() if not c["aborted"]])
        stats_table.add_row("AbortControllers", str(active_controllers), str(len(self.abort_controllers)), "✅ Ready")
        
        # Recent events table
        events_table = Table(title="📋 Recent Events", show_header=True, header_style="bold blue")
        events_table.add_column("Time", width=12)
        events_table.add_column("Component", width=15)
        events_table.add_column("Event", width=20)
        events_table.add_column("Details", width=30)
        
        # Show last 10 events
        for event in self.events[-10:]:
            color = {
                "SUCCESS": "green",
                "INFO": "white", 
                "WARNING": "yellow",
                "ERROR": "red"
            }.get(event["level"], "white")
            
            events_table.add_row(
                event["timestamp"],
                event["component"],
                event["type"],
                event["details"],
                style=color
            )
        
        # Create instructions as separate renderable
        instructions = Text("🔧 Live Debug Controls:", style="bold cyan")
        instructions.append("\n• Press Esc to test cancellation")
        instructions.append("\n• Press Ctrl+C to test signal handling") 
        instructions.append("\n• Type commands to see agent processing")
        instructions.append("\n• Use /debug to toggle this display")
        
        # Create combined layout using Columns for proper rendering
        from rich.columns import Columns
        from rich.console import Group
        
        # Group all elements vertically
        content_group = Group(
            stats_table,
            events_table, 
            instructions
        )
        
        return Panel(
            content_group,
            title="[bold red]Trio Migration Debug Console[/bold red]",
            border_style="bright_blue"
        )

    def show_summary(self):
        """Show debug session summary."""
        elapsed = time.time() - self.start_time
        
        summary_table = Table(title="📊 Debug Session Summary", show_header=True, header_style="bold cyan")
        summary_table.add_column("Metric", style="cyan", width=20)
        summary_table.add_column("Value", style="green", width=15)
        
        summary_table.add_row("Session Duration", f"{elapsed:.2f}s")
        summary_table.add_row("Total Events", str(len(self.events)))
        summary_table.add_row("Nurseries Created", str(self.nursery_count))
        summary_table.add_row("Tasks Spawned", str(self.task_count))
        summary_table.add_row("Cancel Scopes", str(len(self.cancel_scopes)))
        summary_table.add_row("Abort Controllers", str(len(self.abort_controllers)))
        
        # Event type breakdown
        event_types = {}
        for event in self.events:
            event_types[event["type"]] = event_types.get(event["type"], 0) + 1
            
        events_table = Table(title="📋 Event Type Breakdown", show_header=True, header_style="bold blue")
        events_table.add_column("Event Type", style="cyan", width=20)
        events_table.add_column("Count", style="green", width=10)
        
        for event_type, count in sorted(event_types.items()):
            events_table.add_row(event_type, str(count))
        
        # Create combined layout
        from rich.columns import Columns
        columns = Columns([summary_table, events_table], equal=True, expand=True)
        
        console.print(Panel(columns, title="[bold red]Debug Session Summary[/bold red]", border_style="bright_blue"))


# Global debug instance
trio_debug = TrioDebugVisualizer()


# Decorator for automatic function debugging
def debug_trio_function(component: str):
    """Decorator to automatically log function entry/exit."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__
            trio_debug.log_event("FUNC_ENTER", component, func_name, "INFO")
            try:
                result = await func(*args, **kwargs)
                trio_debug.log_event("FUNC_EXIT", component, f"{func_name} ✅", "SUCCESS")
                return result
            except Exception as e:
                trio_debug.log_event("FUNC_ERROR", component, f"{func_name} ❌ {str(e)}", "ERROR")
                raise
                
        def sync_wrapper(*args, **kwargs):
            func_name = func.__name__
            trio_debug.log_event("FUNC_ENTER", component, func_name, "INFO")
            try:
                result = func(*args, **kwargs)
                trio_debug.log_event("FUNC_EXIT", component, f"{func_name} ✅", "SUCCESS")
                return result
            except Exception as e:
                trio_debug.log_event("FUNC_ERROR", component, f"{func_name} ❌ {str(e)}", "ERROR")
                raise
        
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    return decorator