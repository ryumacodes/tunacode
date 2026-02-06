from __future__ import annotations

import json
from pathlib import Path

import pytest

from tunacode.configuration import limits
from tunacode.configuration.models import get_cached_models_registry, load_models_registry

from tunacode.tools.utils.ripgrep import get_ripgrep_binary_path
from tunacode.tools.xml_helper import load_prompt_from_xml

from tunacode.infrastructure.cache import clear_all
from tunacode.infrastructure.cache.caches import xml_prompts as xml_prompts_cache


@pytest.fixture
def clean_caches() -> None:
    clear_all()
    yield
    clear_all()


def test_models_registry_cache_clears_via_clear_all(clean_caches: None) -> None:
    assert get_cached_models_registry() is None

    loaded = load_models_registry()
    assert isinstance(loaded, dict)
    assert get_cached_models_registry() is not None

    clear_all()

    assert get_cached_models_registry() is None


def test_ripgrep_binary_path_cache_clears_via_clear_all(
    clean_caches: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_rg = tmp_path / "rg-first"
    second_rg = tmp_path / "rg-second"
    first_rg.write_text("", encoding="utf-8")
    second_rg.write_text("", encoding="utf-8")

    monkeypatch.setenv("TUNACODE_RIPGREP_PATH", str(first_rg))
    first = get_ripgrep_binary_path()
    assert first == first_rg

    monkeypatch.setenv("TUNACODE_RIPGREP_PATH", str(second_rg))
    second = get_ripgrep_binary_path()

    # Cached.
    assert second == first_rg

    clear_all()

    third = get_ripgrep_binary_path()
    assert third == second_rg


def test_limits_settings_cache_requires_explicit_clear(
    clean_caches: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    config_dir = home / ".config"
    config_dir.mkdir(parents=True)

    config_path = config_dir / "tunacode.json"
    config_path.write_text(json.dumps({"settings": {"max_tokens": 111}}), encoding="utf-8")

    monkeypatch.setenv("HOME", str(home))

    assert limits.get_max_tokens() == 111

    config_path.write_text(json.dumps({"settings": {"max_tokens": 222}}), encoding="utf-8")

    # Still cached (matches historical lru_cache behavior).
    assert limits.get_max_tokens() == 111

    limits.clear_cache()

    assert limits.get_max_tokens() == 222


def test_xml_prompt_none_is_cached_and_cleared(clean_caches: None) -> None:
    tool_name = "definitely-not-a-real-tool"

    assert xml_prompts_cache.try_get_prompt(tool_name) == (False, None)

    assert load_prompt_from_xml(tool_name) is None

    assert xml_prompts_cache.try_get_prompt(tool_name) == (True, None)

    clear_all()

    assert xml_prompts_cache.try_get_prompt(tool_name) == (False, None)
