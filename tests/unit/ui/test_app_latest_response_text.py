"""Tests for extracting latest assistant response text in the app."""

from __future__ import annotations

from tinyagent.agent_types import AssistantMessage, TextContent, ThinkingContent

from tunacode.core.session import StateManager

from tunacode.ui.app import TextualReplApp


def _build_app() -> TextualReplApp:
    return TextualReplApp(state_manager=StateManager())


def test_latest_response_text_ignores_thinking_blocks() -> None:
    app = _build_app()
    app.state_manager.session.conversation.messages = [
        AssistantMessage(
            content=[
                ThinkingContent(thinking="private reasoning"),
                TextContent(text="Part one."),
                TextContent(text="Part two."),
            ]
        )
    ]

    assert app._get_latest_response_text() == "Part one. Part two."


def test_latest_response_text_returns_none_for_thinking_only_message() -> None:
    app = _build_app()
    app.state_manager.session.conversation.messages = [
        AssistantMessage(content=[TextContent(text="Older assistant response")]),
        AssistantMessage(content=[ThinkingContent(thinking="hidden reasoning")]),
    ]

    assert app._get_latest_response_text() is None
