"""Message recording helpers for agent node processing."""

from tunacode.core.types import SessionStateProtocol


def record_thought(session: SessionStateProtocol, thought: str) -> None:
    """Persist agent thoughts outside the conversation history."""
    session.conversation.thoughts.append(thought)
