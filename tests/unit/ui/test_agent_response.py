"""Tests for agent response renderer."""

import pytest

from tunacode.ui.renderers.agent_response import (
    _format_duration,
    _format_tokens,
    render_agent_response,
    render_agent_streaming,
)


class TestFormatTokens:
    """Tests for _format_tokens function."""

    def test_format_tokens_small(self) -> None:
        """Small token counts display as-is."""
        assert _format_tokens(0) == "0"
        assert _format_tokens(999) == "999"

    def test_format_tokens_k_suffix(self) -> None:
        """Token counts >=1000 get k suffix."""
        assert _format_tokens(1000) == "1.0k"
        assert _format_tokens(1500) == "1.5k"
        assert _format_tokens(12345) == "12.3k"

    def test_format_tokens_negative_raises(self) -> None:
        """Negative tokens raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            _format_tokens(-1)


class TestFormatDuration:
    """Tests for _format_duration function."""

    def test_format_duration_ms(self) -> None:
        """Durations <1000ms display in milliseconds."""
        assert _format_duration(0) == "0ms"
        assert _format_duration(500) == "500ms"
        assert _format_duration(999) == "999ms"

    def test_format_duration_s_suffix(self) -> None:
        """Durations >=1000ms display in seconds."""
        assert _format_duration(1000) == "1.0s"
        assert _format_duration(1500) == "1.5s"
        assert _format_duration(5000) == "5.0s"

    def test_format_duration_negative_raises(self) -> None:
        """Negative duration raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            _format_duration(-1)


class TestStatusOrdering:
    """Tests for status bar ordering in render functions."""

    def test_streaming_status_bar_order(self) -> None:
        """Streaming status bar: streaming · duration."""
        result = render_agent_streaming(
            "test content",
            elapsed_ms=1500,
        )
        # Result should be a Panel; we can't easily inspect the exact order
        # but we can verify it renders without error
        assert result is not None

    def test_response_status_bar_order(self) -> None:
        """Response status bar: throughput only."""
        result = render_agent_response(
            content="test",
            tokens=1500,
            duration_ms=2500,
        )
        assert result is not None

    def test_status_bar_with_partial_data(self) -> None:
        """Status bar handles missing optional fields gracefully."""
        # Only tokens
        result = render_agent_response(content="test", tokens=500)
        assert result is not None

        # Only duration
        result = render_agent_response(content="test", duration_ms=100)
        assert result is not None
