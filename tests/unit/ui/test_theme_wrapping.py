from __future__ import annotations

import pytest
from textual.theme import BUILTIN_THEMES

from tunacode.constants import wrap_builtin_themes


@pytest.mark.parametrize(
    ("theme_name", "expected_colors"),
    [
        (
            "dracula",
            {
                "foreground": "#F8F8F2",
                "background": "#282A36",
                "surface": "#2B2E3B",
                "panel": "#313442",
            },
        ),
        (
            "textual-dark",
            {
                "foreground": "#E0E0E0",
                "background": "#121212",
                "surface": "#1E1E1E",
                "panel": "#242F38",
            },
        ),
        (
            "textual-light",
            {
                "foreground": "#1F1F1F",
                "background": "#E0E0E0",
                "surface": "#D8D8D8",
                "panel": "#D0D0D0",
            },
        ),
        (
            "textual-ansi",
            {
                "foreground": "#000000",
                "background": "#FFFFFF",
                "surface": "#FFFFFF",
                "panel": "#E5E5F2",
            },
        ),
    ],
)
def test_wrap_builtin_themes_provides_concrete_theme_color_fields(
    theme_name: str,
    expected_colors: dict[str, str],
) -> None:
    wrapped_themes = {theme.name: theme for theme in wrap_builtin_themes(BUILTIN_THEMES)}

    wrapped_theme = wrapped_themes[theme_name]

    for field_name, expected_value in expected_colors.items():
        wrapped_value = getattr(wrapped_theme, field_name)
        assert wrapped_value is not None
        assert wrapped_value != "ansi_default"
        assert wrapped_value.lower() == expected_value.lower()
