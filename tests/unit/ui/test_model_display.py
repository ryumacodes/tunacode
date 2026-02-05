"""Tests for model display formatting utilities."""

import pytest

from tunacode.ui.model_display import format_model_for_display


class TestFormatModelForDisplay:
    def test_abbreviates_provider_slash(self) -> None:
        assert format_model_for_display("anthropic/claude-3.5-sonnet") == "ANTH/claude-3.5-sonnet"
        assert format_model_for_display("openai/gpt-4o") == "OA/gpt-4o"
        assert format_model_for_display("google/gemini-pro") == "GOOG/gemini-pro"
        assert format_model_for_display("mistral/mistral-large") == "MIST/mistral-large"
        assert format_model_for_display("openrouter/anthropic/claude-3") == "OR/anthropic/claude-3"
        assert (
            format_model_for_display("together/meta-llama/Llama-3-70b")
            == "TOG/meta-llama/Llama-3-70b"
        )
        assert format_model_for_display("groq/llama3-70b-8192") == "GROQ/llama3-70b-8192"

    def test_abbreviates_provider_colon(self) -> None:
        assert format_model_for_display("openai:gpt-4o") == "OA/gpt-4o"
        assert format_model_for_display("anthropic:claude-3.5-sonnet") == "ANTH/claude-3.5-sonnet"

    def test_unknown_provider_passthrough(self) -> None:
        assert format_model_for_display("local/llama-3-70b") == "local/llama-3-70b"
        assert format_model_for_display("custom-model") == "custom-model"

    def test_truncates_long_names(self) -> None:
        long_model = "anthropic/" + "x" * 60
        result = format_model_for_display(long_model, max_length=40)
        assert len(result) == 40
        assert result.endswith("...")

    def test_max_length_too_small_raises(self) -> None:
        with pytest.raises(ValueError, match="max_length"):
            format_model_for_display("openai/gpt-4o", max_length=3)
