from __future__ import annotations

from rich.color import Color as RichColor
from rich.style import Style

from tunacode.core.session import StateManager

from tunacode.ui.app import TextualReplApp
from tunacode.ui.render_safety import (
    normalize_rich_style,
    normalize_text,
    theme_fallback_colors,
)
from tunacode.ui.welcome import generate_logo


def _theme_context() -> tuple[TextualReplApp, RichColor, RichColor]:
    app = TextualReplApp(state_manager=StateManager())
    fallback_foreground, fallback_background = theme_fallback_colors(
        app.current_theme,
        app.ansi_theme,
    )
    return app, fallback_foreground, fallback_background


def test_normalize_rich_style_resolves_default_colors_and_clears_dim() -> None:
    app, fallback_foreground, fallback_background = _theme_context()
    style = Style.parse("dim default on default")

    normalized = normalize_rich_style(
        style,
        ansi_theme=app.ansi_theme,
        fallback_foreground=fallback_foreground,
        fallback_background=fallback_background,
    )

    assert normalized is not None
    assert normalized.dim is False
    assert normalized.color is not None
    assert normalized.color.triplet is not None
    assert normalized.bgcolor is not None
    assert normalized.bgcolor.triplet is not None


def test_normalize_text_converts_default_color_logo_spans() -> None:
    app, fallback_foreground, fallback_background = _theme_context()
    logo = generate_logo()

    default_spans = [
        span
        for span in logo.spans
        if isinstance(span.style, Style)
        and span.style.color is not None
        and span.style.color.is_default
    ]
    assert default_spans

    normalized = normalize_text(
        logo,
        ansi_theme=app.ansi_theme,
        fallback_foreground=fallback_foreground,
        fallback_background=fallback_background,
    )

    normalized_default_spans = [
        span
        for span in normalized.spans
        if isinstance(span.style, Style)
        and span.style.color is not None
        and span.style.color.is_default
    ]
    assert normalized_default_spans == []


def test_normalize_rich_style_leaves_truecolor_styles_unchanged() -> None:
    app, fallback_foreground, fallback_background = _theme_context()
    style = Style.parse("#abcdef on #123456 bold")

    normalized = normalize_rich_style(
        style,
        ansi_theme=app.ansi_theme,
        fallback_foreground=fallback_foreground,
        fallback_background=fallback_background,
    )

    assert normalized == style
