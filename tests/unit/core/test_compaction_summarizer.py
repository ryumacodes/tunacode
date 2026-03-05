"""Unit tests for compaction retention boundary policy."""

from __future__ import annotations

import asyncio

import pytest
from tinyagent.agent_types import (
    AgentMessage,
    AssistantMessage,
    TextContent,
    ToolCallContent,
    ToolResultMessage,
    UserMessage,
)

from tunacode.core.compaction.summarizer import ContextSummarizer


async def _unused_summary_generator(_prompt: str, _signal: asyncio.Event | None) -> str:
    raise AssertionError("summary generation should not run in boundary tests")


def _user_message(text: str) -> UserMessage:
    return UserMessage(content=[TextContent(text=text)], timestamp=None)


def _assistant_text_message(
    text: str,
    *,
    stop_reason: str | None = None,
) -> AssistantMessage:
    return AssistantMessage(
        content=[TextContent(text=text)],
        stop_reason=stop_reason,
        timestamp=None,
    )


def _assistant_tool_call_message(
    tool_call_id: str,
    tool_name: str,
    arguments: dict[str, object],
    *,
    stop_reason: str | None,
) -> AssistantMessage:
    return AssistantMessage(
        content=[
            ToolCallContent(
                id=tool_call_id,
                name=tool_name,
                arguments=arguments,
            )
        ],
        stop_reason=stop_reason,
        timestamp=None,
    )


def _tool_result_message(
    tool_call_id: str,
    tool_name: str,
    text: str,
) -> ToolResultMessage:
    return ToolResultMessage(
        tool_call_id=tool_call_id,
        tool_name=tool_name,
        content=[TextContent(text=text)],
        timestamp=None,
    )


def _patch_token_estimates(
    monkeypatch: pytest.MonkeyPatch,
    messages: list[AgentMessage],
    token_counts: list[int],
) -> None:
    if len(messages) != len(token_counts):
        raise AssertionError("messages and token_counts must be the same length")

    token_by_message_identity = {
        id(message): token_count
        for message, token_count in zip(messages, token_counts, strict=True)
    }

    def _fake_estimate_message_tokens(message: object) -> int:
        message_id = id(message)
        if message_id not in token_by_message_identity:
            raise AssertionError(f"Unexpected message identity: {message_id}")
        return token_by_message_identity[message_id]

    monkeypatch.setattr(
        "tunacode.core.compaction.summarizer.estimate_message_tokens",
        _fake_estimate_message_tokens,
    )


def test_retention_boundary_treats_threshold_equality_as_satisfied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Equality contract: retained suffix tokens == threshold keeps current boundary."""

    messages: list[AgentMessage] = [
        _user_message("old"),
        _assistant_text_message("recent-a", stop_reason="complete"),
        _user_message("recent-b"),
    ]
    _patch_token_estimates(monkeypatch, messages, token_counts=[5, 7, 13])

    summarizer = ContextSummarizer(_unused_summary_generator)
    threshold_tokens = 20

    boundary = summarizer.calculate_retention_boundary(messages, threshold_tokens)

    assert boundary == 1


def test_retention_boundary_snaps_to_zero_for_unsafe_assistant_tool_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Boundary contracts must never split at invalid assistant positions."""

    messages: list[AgentMessage] = [
        _assistant_tool_call_message(
            "tc-1",
            "bash",
            {"command": "ls"},
            stop_reason=None,
        ),
        _tool_result_message("tc-1", "bash", "ok"),
    ]
    _patch_token_estimates(monkeypatch, messages, token_counts=[2, 8])

    summarizer = ContextSummarizer(_unused_summary_generator)

    boundary = summarizer.calculate_retention_boundary(messages, keep_recent_tokens=5)

    assert boundary == 0


def test_retention_boundary_allows_safe_assistant_without_stop_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assistant text-only turns can close boundaries even when stop_reason is absent."""

    messages: list[AgentMessage] = [
        _user_message("old"),
        _assistant_text_message("complete turn", stop_reason=None),
        _user_message("recent"),
    ]
    _patch_token_estimates(monkeypatch, messages, token_counts=[3, 4, 10])

    summarizer = ContextSummarizer(_unused_summary_generator)

    boundary = summarizer.calculate_retention_boundary(messages, keep_recent_tokens=8)

    assert boundary == 2


def test_force_retention_boundary_compacts_even_below_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Manual force boundary ignores token threshold and picks the latest valid cut."""

    messages: list[AgentMessage] = [
        _user_message("hello"),
        _assistant_text_message("world", stop_reason="complete"),
    ]
    _patch_token_estimates(monkeypatch, messages, token_counts=[2, 3])

    summarizer = ContextSummarizer(_unused_summary_generator)

    threshold_boundary = summarizer.calculate_retention_boundary(messages, keep_recent_tokens=20)
    force_boundary = summarizer.calculate_force_retention_boundary(messages)

    assert threshold_boundary == 0
    assert force_boundary == 2


def test_retention_boundary_never_starts_with_tool_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compaction must retain tool call/result pairs atomically."""

    messages: list[AgentMessage] = [
        _user_message("first"),
        _assistant_tool_call_message(
            "tc-1",
            "bash",
            {"command": "ls"},
            stop_reason="tool_calls",
        ),
        _tool_result_message("tc-1", "bash", "ok"),
        _assistant_text_message("done", stop_reason="complete"),
    ]
    _patch_token_estimates(monkeypatch, messages, token_counts=[1, 1, 6, 4])

    summarizer = ContextSummarizer(_unused_summary_generator)

    boundary = summarizer.calculate_retention_boundary(messages, keep_recent_tokens=10)

    assert boundary == 1
    assert not isinstance(messages[boundary], ToolResultMessage)
