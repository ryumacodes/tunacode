"""Tests for the prompting engine."""

import os
import platform

from tunacode.core.prompting.prompting_engine import (
    PromptingEngine,
    get_prompting_engine,
    resolve_prompt,
)


def test_builtin_placeholder_resolution() -> None:
    """Test that built-in placeholders are resolved."""
    engine = PromptingEngine()
    result = engine.resolve("Working in {{CWD}} on {{OS}}")

    assert "{{CWD}}" not in result
    assert "{{OS}}" not in result
    assert os.getcwd() in result
    assert platform.system() in result


def test_unknown_placeholder_unchanged() -> None:
    """Test that unknown placeholders are left unchanged."""
    engine = PromptingEngine()
    result = engine.resolve("Hello {{UNKNOWN}}")

    assert "{{UNKNOWN}}" in result


def test_empty_template() -> None:
    """Test that empty template returns empty string."""
    engine = PromptingEngine()

    assert engine.resolve("") == ""


def test_no_placeholders() -> None:
    """Test that template without placeholders is unchanged."""
    engine = PromptingEngine()
    template = "Just plain text"

    assert engine.resolve(template) == template


def test_custom_provider_registration() -> None:
    """Test registering custom placeholder providers."""
    engine = PromptingEngine()
    engine.register("CUSTOM", lambda: "custom_value")

    result = engine.resolve("Value is {{CUSTOM}}")

    assert result == "Value is custom_value"


def test_singleton_instance() -> None:
    """Test that get_prompting_engine returns singleton."""
    engine1 = get_prompting_engine()
    engine2 = get_prompting_engine()

    assert engine1 is engine2


def test_resolve_prompt_convenience() -> None:
    """Test the module-level convenience function."""
    result = resolve_prompt("CWD: {{CWD}}")

    assert "{{CWD}}" not in result
    assert os.getcwd() in result


def test_date_placeholder() -> None:
    """Test that DATE placeholder returns ISO format date."""
    engine = PromptingEngine()
    result = engine.resolve("Today is {{DATE}}")

    assert "{{DATE}}" not in result
    assert "Today is " in result
    # ISO format includes T separator
    assert "T" in result


def test_whitespace_in_placeholder() -> None:
    """Test that whitespace in placeholder names is stripped."""
    engine = PromptingEngine()
    result = engine.resolve("{{ CWD }}")

    assert "{{" not in result
    assert os.getcwd() in result
