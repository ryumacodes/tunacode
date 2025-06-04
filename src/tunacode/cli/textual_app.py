"""
Modern Textual-based TUI for TunaCode.

Provides a rich, interactive terminal user interface with:
- Split-pane layout with chat history and input
- Sidebar with model info and commands
- Modern dialog boxes for tool confirmations
- Real-time status updates
"""

import asyncio
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Footer, Header, Static, TextArea

from tunacode.core.state import StateManager
from tunacode.setup import setup
from tunacode.utils.system import check_for_updates


class ChatMessage(Static):
    """A single chat message widget."""

    def __init__(self, sender: str, content: str, message_type: str = "user"):
        super().__init__()
        self.sender = sender
        self.content = content
        self.message_type = message_type

    def compose(self) -> ComposeResult:
        """Compose the chat message."""
        if self.message_type == "user":
            yield Static(f"[bold cyan]❯ You[/bold cyan]\n{self.content}", classes="user-message")
        elif self.message_type == "agent":
            yield Static(
                f"[bold green]🤖 TunaCode[/bold green]\n{self.content}", classes="agent-message"
            )
        elif self.message_type == "system":
            yield Static(
                f"[bold yellow]⚠️ System[/bold yellow]\n{self.content}", classes="system-message"
            )
        elif self.message_type == "tool":
            yield Static(
                f"[bold magenta]🔧 Tool[/bold magenta]\n{self.content}", classes="tool-message"
            )


class Sidebar(Container):
    """Sidebar with model info and commands."""

    def __init__(self, state_manager: StateManager):
        super().__init__()
        self.state_manager = state_manager

    def compose(self) -> ComposeResult:
        """Compose the sidebar."""
        yield Static("[bold]TunaCode[/bold]", classes="sidebar-title")
        yield Static(f"Model: {self.state_manager.session.current_model}", id="current-model")
        yield Static("", classes="spacer")

        yield Static("[bold]Commands[/bold]", classes="section-title")
        yield Static("/help - Show help", classes="command-item")
        yield Static("/clear - Clear chat", classes="command-item")
        yield Static("/model - Switch model", classes="command-item")
        yield Static("/yolo - Toggle confirmations", classes="command-item")
        yield Static("", classes="spacer")

        yield Static("[bold]Status[/bold]", classes="section-title")
        yield Static("● Ready", id="status", classes="status-ready")


class ChatHistory(VerticalScroll):
    """Scrollable chat history container."""

    def add_message(self, sender: str, content: str, message_type: str = "user") -> None:
        """Add a new message to the chat history."""
        message = ChatMessage(sender, content, message_type)
        self.mount(message)
        self.scroll_end(animate=True)


class InputArea(Container):
    """Input area with text area and send button."""

    class SendMessage(Message):
        """Message sent when user submits input."""

        def __init__(self, content: str) -> None:
            self.content = content
            super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the input area."""
        with Horizontal():
            yield TextArea(id="message-input")
            yield Button("Send", id="send-button", variant="primary")

    @on(Button.Pressed, "#send-button")
    def send_message(self) -> None:
        """Send the current message."""
        text_area = self.query_one("#message-input", TextArea)
        content = text_area.text.strip()
        if content:
            self.post_message(self.SendMessage(content))
            text_area.clear()

    def on_key(self, event) -> None:
        """Handle key events."""
        if event.key == "ctrl+enter":
            self.send_message()


class TunaCodeApp(App):
    """Main TunaCode Textual application."""

    CSS = """
    Sidebar {
        width: 30;
        background: $surface;
        border: thick $primary;
        padding: 1;
    }

    .sidebar-title {
        text-align: center;
        color: $primary;
        margin-bottom: 1;
    }

    .section-title {
        color: $accent;
        margin: 1 0;
    }

    .command-item {
        color: $text-muted;
        margin-left: 1;
    }

    .status-ready {
        color: $success;
    }

    .status-busy {
        color: $warning;
    }

    .status-error {
        color: $error;
    }

    ChatHistory {
        border: thick $primary;
        padding: 1;
        height: 1fr;
    }

    .user-message {
        background: $surface;
        border-left: thick $primary;
        padding: 1;
        margin: 1 0;
    }

    .agent-message {
        background: $surface;
        border-left: thick $success;
        padding: 1;
        margin: 1 0;
    }

    .system-message {
        background: $surface;
        border-left: thick $warning;
        padding: 1;
        margin: 1 0;
    }

    .tool-message {
        background: $surface;
        border-left: thick $accent;
        padding: 1;
        margin: 1 0;
    }

    InputArea {
        height: 5;
        padding: 1;
    }

    #message-input {
        height: 3;
    }

    #send-button {
        width: 10;
        margin-left: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_chat", "Clear"),
        Binding("f1", "help", "Help"),
        Binding("f2", "model_info", "Model"),
    ]

    def __init__(self, state_manager: StateManager):
        super().__init__()
        self.state_manager = state_manager
        self.chat_history: Optional[ChatHistory] = None
        self.sidebar: Optional[Sidebar] = None
        self.input_area: Optional[InputArea] = None

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header()

        with Horizontal():
            self.sidebar = Sidebar(self.state_manager)
            yield self.sidebar

            with Vertical():
                self.chat_history = ChatHistory()
                yield self.chat_history

                self.input_area = InputArea()
                yield self.input_area

        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        # Add welcome messages
        self.chat_history.add_message(
            "System", "Welcome to TunaCode v0.11 - Your AI-powered development assistant", "system"
        )
        self.chat_history.add_message(
            "System", f"Current model: {self.state_manager.session.current_model}", "system"
        )
        self.chat_history.add_message(
            "System",
            "⚠️ IMPORTANT: Always use git branches before making major changes\n"
            "Type '/help' for available commands",
            "system",
        )

    @on(InputArea.SendMessage)
    async def handle_message(self, message: InputArea.SendMessage) -> None:
        """Handle incoming messages from the input area."""
        content = message.content

        # Add user message to chat
        self.chat_history.add_message("You", content, "user")

        # Update status
        status_widget = self.sidebar.query_one("#status", Static)
        status_widget.update("● Processing...")
        status_widget.classes = "status-busy"

        if content.startswith("/"):
            await self.handle_command(content)
        else:
            await self.handle_user_input(content)

        # Reset status
        status_widget.update("● Ready")
        status_widget.classes = "status-ready"

    async def handle_command(self, command: str) -> None:
        """Handle slash commands."""
        if command == "/help":
            help_text = """Available Commands:

/help - Show this help message
/clear - Clear chat history
/model - Show current model info
/yolo - Toggle confirmation prompts
/quit - Exit the application

Keyboard Shortcuts:
Ctrl+C - Quit
Ctrl+L - Clear chat
F1 - Help
F2 - Model info
Ctrl+Enter - Send message"""
            self.chat_history.add_message("System", help_text, "system")

        elif command == "/clear":
            await self.action_clear_chat()

        elif command == "/model":
            model_info = f"Current model: {self.state_manager.session.current_model}"
            self.chat_history.add_message("System", model_info, "system")

        elif command == "/yolo":
            # Toggle yolo mode
            current_state = getattr(self.state_manager.session, "yolo_mode", False)
            self.state_manager.session.yolo_mode = not current_state
            new_state = "enabled" if not current_state else "disabled"
            self.chat_history.add_message("System", f"Confirmation prompts {new_state}", "system")

        elif command == "/quit":
            await self.action_quit()

        else:
            self.chat_history.add_message("System", f"Unknown command: {command}", "system")

    async def handle_user_input(self, text: str) -> None:
        """Handle regular user input."""
        try:
            # Use the bridge to process the input
            if not hasattr(self, "_bridge"):
                from tunacode.cli.textual_bridge import TextualAgentBridge

                self._bridge = TextualAgentBridge(self.state_manager, self._bridge_message_callback)

            # Process the request
            response = await self._bridge.process_user_input(text)

            # Add the agent's response to chat
            self.chat_history.add_message("TunaCode", response, "agent")

        except Exception as e:
            self.chat_history.add_message("System", f"Error: {str(e)}", "system")

    async def _bridge_message_callback(self, message_type: str, content: str) -> None:
        """Callback for bridge to send messages to the UI."""
        self.chat_history.add_message("System", content, message_type)

    def action_clear_chat(self) -> None:
        """Clear the chat history."""
        self.chat_history.remove_children()
        self.chat_history.add_message("System", "Chat cleared", "system")

    def action_help(self) -> None:
        """Show help information."""
        self.handle_command("/help")

    def action_model_info(self) -> None:
        """Show model information."""
        self.handle_command("/model")


async def run_textual_app(state_manager: StateManager) -> None:
    """Run the Textual application."""
    app = TunaCodeApp(state_manager)
    await app.run_async()


def main():
    """Main entry point for the Textual app."""
    import sys

    # Handle command line arguments
    version_flag = "--version" in sys.argv or "-v" in sys.argv
    if version_flag:
        from tunacode.constants import APP_VERSION

        print(f"TunaCode v{APP_VERSION}")
        return

    # Initialize state manager
    state_manager = StateManager()
    # Show banner
    print("🐟 TunaCode - Modern AI Development Assistant")
    print("=" * 50)

    # Check for updates
    has_update, latest_version = check_for_updates()
    if has_update:
        print(f"📦 Update available: v{latest_version}")
        print("Run: pip install --upgrade tunacode-cli")
        print()

    # Parse CLI arguments for configuration
    cli_config = {}
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--model" and i + 1 < len(args):
            cli_config["model"] = args[i + 1]
            i += 2
        elif args[i] == "--key" and i + 1 < len(args):
            cli_config["key"] = args[i + 1]
            i += 2
        elif args[i] == "--baseurl" and i + 1 < len(args):
            cli_config["baseurl"] = args[i + 1]
            i += 2
        elif args[i] == "--setup":
            cli_config["setup"] = True
            i += 1
        else:
            i += 1

    async def run_app():
        try:
            # Run setup
            run_setup = cli_config.get("setup", False)
            await setup(run_setup, state_manager, cli_config)

            # Run the Textual app
            await run_textual_app(state_manager)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ Error: {e}")

    # Run the async app
    asyncio.run(run_app())


if __name__ == "__main__":
    main()
