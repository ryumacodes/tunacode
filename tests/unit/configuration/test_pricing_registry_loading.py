from __future__ import annotations

from tunacode.configuration.pricing import get_model_pricing
from tunacode.infrastructure.cache import clear_all


def test_get_model_pricing_loads_registry_on_cold_cache() -> None:
    clear_all()
    try:
        pricing = get_model_pricing("openrouter:openai/gpt-4.1")

        assert pricing is not None
        assert pricing.input == 2
        assert pricing.cached_input == 0.5
        assert pricing.output == 8
    finally:
        clear_all()
