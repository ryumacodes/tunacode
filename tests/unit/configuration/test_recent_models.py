from __future__ import annotations

from tunacode.configuration.models import ModelPickerEntry, rank_model_picker_entries
from tunacode.configuration.user_config import get_recent_models, record_recent_model


def test_record_recent_model_promotes_entry_and_caps_history() -> None:
    user_config = {
        "recent_models": [f"provider:model-{index}" for index in range(1, 10)],
    }

    recent_models = record_recent_model(user_config, "provider:model-4")

    assert recent_models[0] == "provider:model-4"
    assert len(recent_models) == 8
    assert recent_models.count("provider:model-4") == 1


def test_get_recent_models_filters_duplicates_invalid_values_and_stale_entries() -> None:
    user_config = {
        "recent_models": [
            "openai:gpt-4.1",
            "stale:missing",
            "openai:gpt-4.1",
            "",
            None,
            "anthropic:claude-sonnet-4",
        ],
    }

    recent_models = get_recent_models(
        user_config,
        available_models={"openai:gpt-4.1", "anthropic:claude-sonnet-4"},
    )

    assert recent_models == ["openai:gpt-4.1", "anthropic:claude-sonnet-4"]


def test_rank_model_picker_entries_pins_current_and_recent_before_capped_general_results() -> None:
    entries = [
        ModelPickerEntry(
            full_model=f"provider:model-{index:02d}",
            provider_id="provider",
            provider_name="Provider",
            model_id=f"model-{index:02d}",
            model_name=f"Model {index:02d}",
        )
        for index in range(1, 56)
    ]

    ranked_entries, is_truncated = rank_model_picker_entries(
        entries,
        current_model="provider:model-30",
        recent_models=["provider:model-20", "provider:model-40"],
        filter_query="",
    )

    assert [entry.full_model for entry in ranked_entries[:3]] == [
        "provider:model-30",
        "provider:model-20",
        "provider:model-40",
    ]
    assert len(ranked_entries) == 53
    assert is_truncated is True


def test_rank_model_picker_entries_matches_provider_and_model_tokens() -> None:
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

    ranked_entries, is_truncated = rank_model_picker_entries(
        entries,
        current_model="",
        recent_models=[],
        filter_query="openai gpt",
    )

    assert [entry.full_model for entry in ranked_entries] == ["openai:gpt-5"]
    assert is_truncated is False
