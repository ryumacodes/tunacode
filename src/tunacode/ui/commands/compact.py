"""Compact command for TunaCode REPL.

Manual conversation compaction - compresses message history into a summary
to reduce context size while preserving essential information.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tunacode.ui.app import TextualReplApp

from tunacode.core.configuration import get_summary_threshold
from tunacode.core.constants import RETAINED_MESSAGES_COUNT


# Inline Command base class to avoid circular import with ui.commands
class Command(ABC):
    """Base class for REPL commands."""

    name: str
    description: str
    usage: str = ""

    @abstractmethod
    async def execute(self, app: TextualReplApp, args: str) -> None:
        """Execute the command."""


class CompactCommand(Command):
    """Compress conversation history into a summary."""

    name = "compact"
    description = "Compress conversation history into a summary"
    usage = "/compact [status]"

    async def execute(self, app: TextualReplApp, args: str) -> None:
        from tunacode.core.agents.resume import filter_compacted

        session = app.state_manager.session
        messages = session.conversation.messages

        # Use session's token count (maintained by update_token_count)
        total_tokens = session.conversation.total_tokens

        subcommand = args.strip().lower() if args else ""
        configured_threshold = get_summary_threshold()

        if subcommand == "status":
            self._show_status(app, messages, total_tokens, configured_threshold)
            return

        # Precondition: need enough messages
        if len(messages) < 4:
            app.notify("Not enough messages to compact (need at least 4)", severity="warning")
            return

        # Precondition: not already compacted recently
        filtered = filter_compacted(messages)
        if len(filtered) < len(messages) and len(filtered) <= 4:
            app.notify("Already compacted recently", severity="warning")
            return

        app.notify("Compacting conversation...")
        await self._perform_compaction(app, session, messages, session.current_model)

    def _show_status(
        self,
        app: TextualReplApp,
        messages: list[Any],
        total_tokens: int,
        threshold: int,
    ) -> None:
        """Display compaction status."""
        app.rich_log.write(f"Messages: {len(messages)}")
        app.rich_log.write(f"Tokens: ~{total_tokens:,}")
        app.rich_log.write(f"Threshold: {threshold:,}")

        if total_tokens > threshold:
            app.rich_log.write("[yellow]Above threshold - /compact will summarize[/yellow]")
        else:
            app.rich_log.write("[dim]Below threshold[/dim]")

    async def _perform_compaction(
        self,
        app: TextualReplApp,
        session: Any,
        messages: list[Any],
        model: str,
    ) -> None:
        """Perform the actual compaction operation."""
        from tunacode.core.agents.agent_components.agent_config import get_or_create_agent
        from tunacode.core.agents.resume import (
            create_summary_request_message,
            generate_summary,
        )

        try:
            agent = get_or_create_agent(model, app.state_manager)
        except Exception as e:
            app.notify(f"Compact failed: could not get agent - {e}", severity="error")
            return

        tail_start = max(0, len(messages) - RETAINED_MESSAGES_COUNT)
        tail_messages = messages[tail_start:]

        try:
            summary = await generate_summary(
                agent,
                messages,
                model,
                start_index=0,
                end_index=tail_start,
            )
        except Exception as e:
            app.notify(f"Compact failed: summary generation error - {e}", severity="error")
            return

        summary_message = create_summary_request_message(summary)

        # Store summary for ctrl+o viewing
        session.last_summary = summary

        # Replace messages: [summary] + [tail]
        messages[:] = [summary_message] + tail_messages
        session.update_token_count()

        app.rich_log.write(
            f"[green]Compacted[/green] {tail_start} messages [dim](ctrl+o to see summary)[/dim]"
        )
        app.rich_log.write(f"[dim]Summary: {summary.token_count} tokens[/dim]")
        app.notify(f"Compacted! {summary.token_count} token summary")
        app.state_manager.save_session()
