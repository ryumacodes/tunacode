"""Tests for agent helper tool-argument validation."""

from __future__ import annotations

import pytest

from tunacode.types.canonical import CanonicalToolCall, ToolCallStatus

from tunacode.core.agents.agent_components.agent_helpers import (
    _coerce_tool_args,
    get_recent_tools_context,
)


def test_coerce_tool_args_rejects_non_dict_payload() -> None:
    with pytest.raises(TypeError, match="tool args must be a dict\\[str, object\\]"):
        _coerce_tool_args(["not", "a", "dict"])


def test_coerce_tool_args_rejects_non_string_keys() -> None:
    with pytest.raises(TypeError, match="tool args keys must be strings"):
        _coerce_tool_args({1: "value"})


def test_get_recent_tools_context_propagates_invalid_tool_args() -> None:
    tool_call = CanonicalToolCall(
        tool_call_id="call-1",
        tool_name="read_file",
        args={1: "bad-key"},  # type: ignore[dict-item]
        status=ToolCallStatus.COMPLETED,
    )

    with pytest.raises(TypeError, match="tool args keys must be strings"):
        get_recent_tools_context([tool_call])
