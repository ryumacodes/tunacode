"""StarCraft-inspired TUI dashboard using Textual.

Layout:
┌─────────────────────────────────────────────────────────────────────┐
│ ◇ tokens: 12,847  ◇ model  ○ 0.7  ◇ cycle: 3/10  $ 0.0041          │ <- ResourceBar
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  > User query here                                                  │
│                                                                     │
│  Response content streams here...                                   │ <- MainPane
│                                                                     │
├──────────────┬─────────────────────────┬────────────────────────────┤
│  reasoning   │        tool             │           log              │ <- BottomPanels
│  cycle 3/10  │  tool_name              │  timestamp event           │
│  ● step      │  args...                │  timestamp event           │
├──────────────┴─────────────────────────┴────────────────────────────┤
│ q quit  p pause  s step  y yolo                                     │ <- Footer
└─────────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static, RichLog


@dataclass
class DashboardState:
    """Holds dashboard state."""
    tokens: int = 0
    model: str = ""
    temperature: float = 0.7
    cycle: int = 0
    max_cycles: int = 10
    cost: float = 0.0
    query: str = ""
    content: str = ""
    reasoning_step: str = ""
    reasoning_steps: list[str] = field(default_factory=list)
    tool_name: str = ""
    tool_args: str = ""
    tool_status: str = ""
    log_entries: list[str] = field(default_factory=list)


class ResourceBar(Static):
    """Top resource bar showing tokens, model, temp, cycle, cost."""

    tokens = reactive(0)
    model = reactive("")
    temperature = reactive(0.7)
    cycle = reactive(0)
    max_cycles = reactive(10)
    cost = reactive(0.0)

    def render(self) -> Text:
        return Text.assemble(
            ("◇ ", "dim"),
            ("tokens: ", "bold cyan"),
            (f"{self.tokens:,}", "white"),
            ("    ", ""),
            ("◇ ", "dim"),
            (self.model or "---", "bold cyan"),
            ("    ", ""),
            ("○ ", "dim"),
            (f"{self.temperature}", "white"),
            ("    ", ""),
            ("◇ ", "dim"),
            ("cycle: ", "bold cyan"),
            (f"{self.cycle}/{self.max_cycles}", "white"),
            ("    ", ""),
            ("$ ", "green"),
            (f"{self.cost:.4f}", "white"),
        )


class MainPane(Static):
    """Main content pane showing query and streaming response."""

    query = reactive("")
    content = reactive("")
    status = reactive("")

    def render(self) -> Text:
        lines = []

        if self.query:
            lines.append(Text.assemble(
                ("> ", "bold cyan"),
                (self.query, "white"),
            ))
            lines.append(Text(""))

        if self.status:
            lines.append(Text.assemble(
                ("◇ ", "dim"),
                (self.status, "yellow"),
            ))
            lines.append(Text(""))

        if self.content:
            # Show last N lines of content
            content_lines = self.content.split("\n")
            max_lines = 15
            if len(content_lines) > max_lines:
                content_lines = content_lines[-max_lines:]
            for line in content_lines:
                lines.append(Text(line))

        result = Text("\n").join(lines) if lines else Text("[dim]Waiting...[/dim]")
        return result


class ReasoningPanel(Static):
    """Shows reasoning/cycle state."""

    cycle = reactive(0)
    max_cycles = reactive(10)
    steps = reactive([])
    current_step = reactive("")

    DEFAULT_CSS = """
    ReasoningPanel {
        border: solid cyan;
        height: 100%;
        padding: 0 1;
    }
    """

    def render(self) -> Text:
        lines = [
            Text.assemble(("cycle ", "dim"), (f"{self.cycle}/{self.max_cycles}", "bold")),
            Text("──────────", style="dim"),
        ]

        step_icons = {
            "api_call": "●",
            "tool": "●",
            "observe": "●",
            "done": "◉",
            "pending": "○",
        }

        for step in self.steps:
            icon = step_icons.get(step, "○")
            style = "green" if step == self.current_step else "dim"
            lines.append(Text.assemble((f"{icon} ", style), (step, style)))

        return Text("\n").join(lines)


class ToolPanel(Static):
    """Shows current tool execution."""

    tool_name = reactive("")
    tool_args = reactive("")
    tool_status = reactive("")

    DEFAULT_CSS = """
    ToolPanel {
        border: solid cyan;
        height: 100%;
        padding: 0 1;
    }
    """

    def render(self) -> Text:
        name = self.tool_name or "---"
        args = self.tool_args[:40] + "..." if len(self.tool_args) > 40 else self.tool_args or "---"
        status = self.tool_status or "idle"

        return Text("\n").join([
            Text(name, style="bold"),
            Text(args, style="dim"),
            Text(""),
            Text.assemble(
                ("██████████ ", "green" if status == "done" else "yellow"),
                (status, "bold"),
            ),
        ])


class LogPanel(RichLog):
    """Shows event log."""

    DEFAULT_CSS = """
    LogPanel {
        border: solid cyan;
        height: 100%;
    }
    """

    def add_entry(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(Text.assemble(
            (f"{timestamp} ", "dim"),
            (message, "white"),
        ))


class StarCraftTUI(App):
    """StarCraft-inspired dashboard TUI."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #resource-bar {
        height: 1;
        background: $surface;
        padding: 0 1;
    }

    #main-pane {
        border: solid cyan;
        height: 1fr;
        padding: 1;
    }

    #bottom-panels {
        height: 10;
    }

    #bottom-panels > * {
        width: 1fr;
    }

    ReasoningPanel {
        width: 15;
    }

    ToolPanel {
        width: 1fr;
    }

    LogPanel {
        width: 1fr;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("p", "pause", "Pause"),
        Binding("s", "step", "Step"),
        Binding("y", "yolo", "YOLO"),
        Binding("escape", "quit", "Quit", show=False),
    ]

    def __init__(
        self,
        on_quit: Optional[Callable] = None,
        on_pause: Optional[Callable] = None,
        on_step: Optional[Callable] = None,
        on_yolo: Optional[Callable] = None,
    ):
        super().__init__()
        self.state = DashboardState()
        self._on_quit = on_quit
        self._on_pause = on_pause
        self._on_step = on_step
        self._on_yolo = on_yolo
        self._paused = False

    def compose(self) -> ComposeResult:
        yield ResourceBar(id="resource-bar")
        yield MainPane(id="main-pane")
        with Horizontal(id="bottom-panels"):
            yield ReasoningPanel(id="reasoning")
            yield ToolPanel(id="tool")
            yield LogPanel(id="log")
        yield Footer()

    def action_quit(self) -> None:
        if self._on_quit:
            self._on_quit()
        self.exit()

    def action_pause(self) -> None:
        self._paused = not self._paused
        if self._on_pause:
            self._on_pause(self._paused)
        self.log_event("paused" if self._paused else "resumed")

    def action_step(self) -> None:
        if self._on_step:
            self._on_step()
        self.log_event("step")

    def action_yolo(self) -> None:
        if self._on_yolo:
            self._on_yolo()
        self.log_event("yolo mode")

    # --- Public API for updating state ---

    def set_tokens(self, tokens: int) -> None:
        self.query_one("#resource-bar", ResourceBar).tokens = tokens

    def set_model(self, model: str) -> None:
        self.query_one("#resource-bar", ResourceBar).model = model

    def set_temperature(self, temp: float) -> None:
        self.query_one("#resource-bar", ResourceBar).temperature = temp

    def set_cycle(self, cycle: int, max_cycles: int = 10) -> None:
        rb = self.query_one("#resource-bar", ResourceBar)
        rb.cycle = cycle
        rb.max_cycles = max_cycles
        self.query_one("#reasoning", ReasoningPanel).cycle = cycle
        self.query_one("#reasoning", ReasoningPanel).max_cycles = max_cycles

    def set_cost(self, cost: float) -> None:
        self.query_one("#resource-bar", ResourceBar).cost = cost

    def set_query(self, query: str) -> None:
        self.query_one("#main-pane", MainPane).query = query

    def set_status(self, status: str) -> None:
        self.query_one("#main-pane", MainPane).status = status

    def append_content(self, content: str) -> None:
        pane = self.query_one("#main-pane", MainPane)
        pane.content = pane.content + content

    def clear_content(self) -> None:
        self.query_one("#main-pane", MainPane).content = ""

    def set_reasoning_steps(self, steps: list[str], current: str = "") -> None:
        panel = self.query_one("#reasoning", ReasoningPanel)
        panel.steps = steps
        panel.current_step = current

    def set_tool(self, name: str, args: str = "", status: str = "running") -> None:
        panel = self.query_one("#tool", ToolPanel)
        panel.tool_name = name
        panel.tool_args = args
        panel.tool_status = status

    def log_event(self, message: str) -> None:
        self.query_one("#log", LogPanel).add_entry(message)

    # Compatibility shims for old API
    async def scratchpad(self, content: str) -> None:
        self.append_content(content)

    async def tool_call(self, tool_name: str, args=None, status: str = "running") -> None:
        args_str = str(args)[:100] if args else ""
        self.set_tool(tool_name, args_str, status)
        self.log_event(f"tool {tool_name}")


# Factory function for easy creation
def create_dashboard(**callbacks) -> StarCraftTUI:
    """Create a dashboard instance."""
    return StarCraftTUI(**callbacks)
