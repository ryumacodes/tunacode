from __future__ import annotations

from tunacode.configuration.models import ModelPickerEntry

from tunacode.ui.screens.model_picker import build_model_picker_option_rows


def test_build_model_picker_option_rows_surfaces_current_and_recent_first() -> None:
    entries = [
        ModelPickerEntry(
            full_model="openai:gpt-5",
            provider_id="openai",
            provider_name="OpenAI",
            model_id="gpt-5",
            model_name="GPT-5",
        ),
        ModelPickerEntry(
            full_model="anthropic:claude-sonnet-4",
            provider_id="anthropic",
            provider_name="Anthropic",
            model_id="claude-sonnet-4",
            model_name="Claude Sonnet 4",
        ),
        ModelPickerEntry(
            full_model="google:gemini-2.5-pro",
            provider_id="google",
            provider_name="Google",
            model_id="gemini-2.5-pro",
            model_name="Gemini 2.5 Pro",
        ),
    ]

    option_rows, highlight_index, is_truncated = build_model_picker_option_rows(
        entries,
        current_model="google:gemini-2.5-pro",
        recent_models=["anthropic:claude-sonnet-4"],
        filter_query="",
    )

    assert option_rows[0][1] == "google:gemini-2.5-pro"
    assert option_rows[0][0].startswith("[current]")
    assert option_rows[1][1] == "anthropic:claude-sonnet-4"
    assert option_rows[1][0].startswith("[recent]")
    assert highlight_index == 0
    assert is_truncated is False


def test_build_model_picker_option_rows_filters_by_provider_text() -> None:
    entries = [
        ModelPickerEntry(
            full_model="openai:gpt-5",
            provider_id="openai",
            provider_name="OpenAI",
            model_id="gpt-5",
            model_name="GPT-5",
        ),
        ModelPickerEntry(
            full_model="anthropic:claude-sonnet-4",
            provider_id="anthropic",
            provider_name="Anthropic",
            model_id="claude-sonnet-4",
            model_name="Claude Sonnet 4",
        ),
    ]

    option_rows, highlight_index, is_truncated = build_model_picker_option_rows(
        entries,
        current_model="",
        recent_models=[],
        filter_query="anthropic claude",
    )

    assert len(option_rows) == 1
    assert option_rows[0][1] == "anthropic:claude-sonnet-4"
    assert option_rows[0][0].startswith("Claude Sonnet 4  Anthropic")
    assert highlight_index == 0
    assert is_truncated is False
