"""Conversation management commands for TunaCode CLI."""

from typing import List, Optional

from ....types import CommandContext, ProcessRequestCallback
from ....ui import console as ui
from ..base import CommandCategory, CommandSpec, SimpleCommand


class CompactCommand(SimpleCommand):
    """Compact conversation context."""

    spec = CommandSpec(
        name="compact",
        aliases=["/compact"],
        description="Summarize and compact the conversation history",
        category=CommandCategory.SYSTEM,
    )

    def __init__(self, process_request_callback: Optional[ProcessRequestCallback] = None):
        self._process_request = process_request_callback

    async def execute(self, args: List[str], context: CommandContext) -> None:
        # Use the injected callback or get it from context
        process_request = self._process_request or context.process_request

        if not process_request:
            await ui.error("Compact command not available - process_request not configured")
            return

        # Count current messages
        original_count = len(context.state_manager.session.messages)

        # Generate summary with output captured
        summary_prompt = (
            "Summarize the conversation so far in a concise paragraph, "
            "focusing on the main topics discussed and any important context "
            "that should be preserved."
        )
        result = await process_request(
            summary_prompt,
            context.state_manager,
            False,  # We'll handle the output ourselves
        )

        # Extract summary text from result
        summary_text = ""

        # First try: standard result structure
        if (
            result
            and hasattr(result, "result")
            and result.result
            and hasattr(result.result, "output")
        ):
            summary_text = result.result.output

        # Second try: check messages for assistant response
        if not summary_text:
            messages = context.state_manager.session.messages
            # Look through new messages in reverse order
            for i in range(len(messages) - 1, original_count - 1, -1):
                msg = messages[i]
                # Handle ModelResponse objects
                if hasattr(msg, "parts") and msg.parts:
                    for part in msg.parts:
                        if hasattr(part, "content") and part.content:
                            content = part.content
                            # Skip JSON thought objects
                            if content.strip().startswith('{"thought"'):
                                lines = content.split("\n")
                                # Find the actual summary after the JSON
                                for i, line in enumerate(lines):
                                    if (
                                        line.strip()
                                        and not line.strip().startswith("{")
                                        and not line.strip().endswith("}")
                                    ):
                                        summary_text = "\n".join(lines[i:]).strip()
                                        break
                            else:
                                summary_text = content
                            if summary_text:
                                break
                # Handle dict-style messages
                elif isinstance(msg, dict):
                    if msg.get("role") == "assistant" and msg.get("content"):
                        summary_text = msg["content"]
                        break
                # Handle other message types
                elif hasattr(msg, "content") and hasattr(msg, "role"):
                    if getattr(msg, "role", None) == "assistant":
                        summary_text = msg.content
                        break

                if summary_text:
                    break

        if not summary_text:
            await ui.error("Failed to generate summary - no assistant response found")
            return

        # Display summary in a formatted panel
        from tunacode.ui import panels

        await panels.panel("Conversation Summary", summary_text, border_style="cyan")

        # Show statistics
        await ui.info(f"Current message count: {original_count}")
        await ui.info("After compaction: 3 (summary + last 2 messages)")

        # Truncate the conversation history
        context.state_manager.session.messages = context.state_manager.session.messages[-2:]

        await ui.success("Context history has been summarized and truncated.")
