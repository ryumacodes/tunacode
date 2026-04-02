"""Render-safety helpers for Rich styles under Textual 4.0.0."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.color import Color as RichColor
from rich.style import Style, StyleType
from rich.text import Span, Text
from textual.color import Color
from textual.constants import DIM_FACTOR

if TYPE_CHECKING:
    from rich.terminal_theme import TerminalTheme
    from textual.theme import Theme


def _coerce_style(style: StyleType | None) -> Style | None:
    if style in (None, ""):
        return None
    return style if isinstance(style, Style) else Style.parse(style)


def _default_terminal_color(*, ansi_theme: TerminalTheme, foreground: bool) -> RichColor:
    triplet = ansi_theme.foreground_color if foreground else ansi_theme.background_color
    return RichColor.from_rgb(*triplet)


def _resolve_color(
    color: RichColor | None,
    *,
    ansi_theme: TerminalTheme,
    fallback: RichColor,
    foreground: bool,
) -> RichColor | None:
    if color is None:
        return None
    if color.triplet is not None:
        return color
    resolved = RichColor.from_rgb(*color.get_truecolor(ansi_theme, foreground=foreground))
    if resolved.triplet is None or resolved.is_default:
        return fallback
    return resolved


def theme_fallback_colors(theme: Theme, ansi_theme: TerminalTheme) -> tuple[RichColor, RichColor]:
    """Return concrete foreground/background fallbacks for the active theme."""

    default_foreground = _default_terminal_color(ansi_theme=ansi_theme, foreground=True)
    default_background = _default_terminal_color(ansi_theme=ansi_theme, foreground=False)

    foreground = _resolve_color(
        Color.parse(theme.foreground).rich_color if theme.foreground is not None else None,
        ansi_theme=ansi_theme,
        fallback=default_foreground,
        foreground=True,
    )
    background = _resolve_color(
        Color.parse(theme.background).rich_color if theme.background is not None else None,
        ansi_theme=ansi_theme,
        fallback=default_background,
        foreground=False,
    )

    return foreground or default_foreground, background or default_background


def normalize_rich_style(
    style: Style | None,
    *,
    ansi_theme: TerminalTheme,
    fallback_foreground: RichColor,
    fallback_background: RichColor,
) -> Style | None:
    """Resolve ANSI/default colors and precompute dim blending."""

    if style is None:
        return None

    foreground = _resolve_color(
        style.color,
        ansi_theme=ansi_theme,
        fallback=fallback_foreground,
        foreground=True,
    )
    background = _resolve_color(
        style.bgcolor,
        ansi_theme=ansi_theme,
        fallback=fallback_background,
        foreground=False,
    )

    if style.dim and foreground is not None:
        blend_background = background or fallback_background
        foreground = RichColor.from_rgb(
            blend_background.triplet.red
            + (foreground.triplet.red - blend_background.triplet.red) * DIM_FACTOR,
            blend_background.triplet.green
            + (foreground.triplet.green - blend_background.triplet.green) * DIM_FACTOR,
            blend_background.triplet.blue
            + (foreground.triplet.blue - blend_background.triplet.blue) * DIM_FACTOR,
        )
        style = style + Style(dim=False)

    return style + Style.from_color(foreground, background)


def normalize_text(
    text: Text,
    *,
    ansi_theme: TerminalTheme,
    fallback_foreground: RichColor,
    fallback_background: RichColor,
) -> Text:
    """Return a copy of ``text`` with spans normalized for safe filter handling."""

    normalized = text.copy()
    base_style = _coerce_style(normalized.style)
    if base_style is not None:
        normalized.style = normalize_rich_style(
            base_style,
            ansi_theme=ansi_theme,
            fallback_foreground=fallback_foreground,
            fallback_background=fallback_background,
        )

    normalized.spans = [
        Span(
            span.start,
            span.end,
            normalize_rich_style(
                _coerce_style(span.style),
                ansi_theme=ansi_theme,
                fallback_foreground=fallback_foreground,
                fallback_background=fallback_background,
            ),
        )
        for span in normalized.spans
    ]
    return normalized
