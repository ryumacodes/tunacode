# Fix Theme Typing in constants.py

## Problem

The `_wrap_builtin_theme()` function in `src/tunacode/constants.py` uses `**kwargs` unpacking with a `dict[str, object]` type annotation. Mypy can't verify the dict values match the expected Theme signature.

**Mypy errors:**
```
src/tunacode/constants.py:326: error: Argument 1 to "Theme" has incompatible type "**dict[str, object]"; expected "str"
src/tunacode/constants.py:326: error: Argument 1 to "Theme" has incompatible type "**dict[str, object]"; expected "bool"
src/tunacode/constants.py:326: error: Argument 1 to "Theme" has incompatible type "**dict[str, object]"; expected "float"
src/tunacode/constants.py:326: error: Argument 1 to "Theme" has incompatible type "**dict[str, object]"; expected "dict[str, str]"
```

## Why We Re-register Themes

The app injects custom CSS variables (bevel-light, bevel-dark, border, text-muted, scrollbar-thumb, scrollbar-track) into Textual's built-in themes. This is intentional.

## Solution

Build the Theme explicitly instead of using `**kwargs` unpacking.

**File:** `src/tunacode/constants.py`
**Function:** `_wrap_builtin_theme()` (lines 295-326)

Replace the kwargs dict with explicit Theme() constructor call:

```python
def _wrap_builtin_theme(theme: Theme, palette: Mapping[str, str]) -> Theme:
    from textual.theme import Theme as ThemeCls

    merged_vars = {**theme.variables, **_build_theme_variables(palette)}

    return ThemeCls(
        name=theme.name,
        dark=theme.dark,
        primary=theme.primary,
        secondary=getattr(theme, "secondary", None),
        accent=getattr(theme, "accent", None),
        foreground=getattr(theme, "foreground", None),
        background=getattr(theme, "background", None),
        surface=getattr(theme, "surface", None),
        panel=getattr(theme, "panel", None),
        warning=getattr(theme, "warning", None),
        error=getattr(theme, "error", None),
        success=getattr(theme, "success", None),
        variables=merged_vars,
    )
```

## Verification

Run mypy:
```bash
uv run mypy --ignore-missing-imports --no-strict-optional src/
```

Expected: 0 errors (or only the unrelated Widget.update error in thinking_state.py)
