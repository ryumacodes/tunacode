from __future__ import annotations

import pytest

from tunacode.configuration.models import (
    get_model_context_window,
    get_provider_alchemy_api,
    get_provider_env_var,
)
from tunacode.configuration.pricing import get_model_pricing

from tunacode.infrastructure.cache import clear_all


@pytest.fixture(autouse=True)
def reset_registry_cache() -> None:
    clear_all()
    yield
    clear_all()


def test_registry_metadata_accessors_lazy_load_on_cold_cache() -> None:
    assert get_provider_env_var("minimax-coding-plan") == "MINIMAX_API_KEY"
    assert get_provider_alchemy_api("minimax-coding-plan") == "minimax-completions"
    assert get_model_context_window("minimax-coding-plan:MiniMax-M2.1") == 204800


def test_registry_pricing_accessor_lazy_loads_on_cold_cache() -> None:
    pricing = get_model_pricing("openrouter:openai/gpt-4.1")

    assert pricing is not None
    assert pricing.input == 2
    assert pricing.cached_input == 0.5
    assert pricing.output == 8
