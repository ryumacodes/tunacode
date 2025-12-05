# Research – Theme Switching with Config Persistence

**Date:** 2025-12-04
**Owner:** Claude Agent
**Phase:** Research

## Goal

Determine the simplest, cleanest way to add runtime theme switching to TunaCode that persists to the config file.

## Findings

### Textual's Built-in Theme System

Textual provides 11 built-in themes ready for use:
- `textual-dark` (default)
- `textual-light`
- `nord`, `gruvbox`, `catppuccin-mocha`, `dracula`, `tokyo-night`, `monokai`, `flexoki`, `catppuccin-latte`, `solarized-light`

**Runtime switching is trivial:**
```python
# One line to switch themes
self.theme = "nord"  # Automatic CSS refresh via Reactive
```

**How it works:**
- `app.theme` is a `Reactive[str]` attribute
- Setting it triggers `_watch_theme()` which invalidates CSS
- All widgets automatically repaint with new colors

### TunaCode's Current Implementation

| File | Purpose |
|------|---------|
| `src/tunacode/constants.py:109-124` | `UI_COLORS` dict defines color palette |
| `src/tunacode/constants.py:195-220` | `build_tunacode_theme()` creates custom Theme |
| `src/tunacode/ui/app.py:102-105` | Registers and activates "tunacode" theme on mount |

**Current theme registration:**
```python
def on_mount(self) -> None:
    tunacode_theme = build_tunacode_theme()
    self.register_theme(tunacode_theme)
    self.theme = THEME_NAME  # "tunacode"
```

### TunaCode's Config System

| File | Purpose |
|------|---------|
| `~/.config/tunacode.json` | User config file location |
| `src/tunacode/configuration/defaults.py` | Default config values |
| `src/tunacode/utils/config/user_configuration.py` | Load/save functions |
| `src/tunacode/core/state.py:113-130` | Config merged with defaults |

**Config structure:**
```json
{
  "default_model": "...",
  "env": {...},
  "settings": {
    "max_retries": 10,
    "enable_streaming": true,
    // NEW: "theme": "tunacode" would go here
  }
}
```

## Key Patterns / Solutions Found

### Pattern 1: One-Line Theme Switching (Textual Built-in)

```python
def action_toggle_theme(self) -> None:
    """Toggle between tunacode and textual-light."""
    self.theme = "textual-light" if self.theme == "tunacode" else "tunacode"
```

### Pattern 2: `/theme` Command Pattern

```python
class ThemeCommand(Command):
    name = "theme"
    description = "Switch theme: /theme [name] or /theme to list"

    async def execute(self, app, args: str) -> None:
        if args:
            app.theme = args.strip()
            # Save to config
            app.state_manager.session.user_config["settings"]["theme"] = app.theme
            save_config(app.state_manager)
        else:
            # List available themes
            ...
```

### Pattern 3: Config Persistence on Change

**Add to `defaults.py`:**
```python
DEFAULT_USER_CONFIG = {
    "settings": {
        "theme": "tunacode",  # Add this line
    }
}
```

**Load on mount in `app.py`:**
```python
def on_mount(self) -> None:
    self.register_theme(build_tunacode_theme())
    saved_theme = self.state_manager.session.user_config.get("settings", {}).get("theme", "tunacode")
    if saved_theme in self.available_themes:
        self.theme = saved_theme
    else:
        self.theme = "tunacode"
```

## Simplest Implementation (4 Changes)

### Change 1: Add default to `defaults.py`
```python
"settings": {
    "theme": "tunacode",
}
```

### Change 2: Load saved theme in `app.py` on_mount
```python
saved_theme = self.state_manager.session.user_config.get("settings", {}).get("theme", "tunacode")
self.theme = saved_theme if saved_theme in self.available_themes else "tunacode"
```

### Change 3: Add `/theme` command to `commands/__init__.py`
```python
class ThemeCommand(Command):
    name = "theme"
    description = "List or switch theme"
    usage = "/theme [name]"

    async def execute(self, app: "TextualReplApp", args: str) -> None:
        if args:
            theme_name = args.strip()
            if theme_name in app.available_themes:
                app.theme = theme_name
                app.state_manager.session.user_config.setdefault("settings", {})["theme"] = theme_name
                save_config(app.state_manager)
                app.notify(f"Theme: {theme_name}")
            else:
                app.notify(f"Unknown theme: {theme_name}", severity="error")
        else:
            # Show available themes in a table
            from rich.table import Table
            table = Table(title="Themes")
            table.add_column("Name")
            table.add_column("Type")
            table.add_column("Active")
            for name, theme in app.available_themes.items():
                marker = "●" if name == app.theme else ""
                table.add_row(name, "Dark" if theme.dark else "Light", marker)
            app.rich_log.write(table)

COMMANDS.append(ThemeCommand())
```

### Change 4: (Optional) Add keybinding for quick toggle
```python
BINDINGS = [
    Binding("ctrl+t", "toggle_theme", "Theme", show=False),
]

def action_toggle_theme(self) -> None:
    themes = list(self.available_themes.keys())
    current_idx = themes.index(self.theme) if self.theme in themes else 0
    next_theme = themes[(current_idx + 1) % len(themes)]
    self.theme = next_theme
    self.state_manager.session.user_config.setdefault("settings", {})["theme"] = next_theme
    save_config(self.state_manager)
```

## Knowledge Gaps

- **Light mode for TunaCode brand theme**: Currently only `tunacode` (dark) exists. Creating `tunacode-light` would require designing a new color palette.

## References

- `src/tunacode/constants.py:195-220` → `build_tunacode_theme()`
- `src/tunacode/ui/app.py:102-105` → Theme registration
- `src/tunacode/configuration/defaults.py` → Default config
- `src/tunacode/utils/config/user_configuration.py` → `save_config()` function
- `src/tunacode/ui/commands/__init__.py` → Command pattern
- Textual docs: https://textual.textualize.io/guide/design/ → Built-in themes

## Summary

**Textual makes theme switching trivial**: Just set `app.theme = "theme-name"`.

**Implementation effort**: ~20 lines of code across 3 files:
1. Add `"theme": "tunacode"` to defaults
2. Load saved theme on mount
3. Add `/theme` command that saves to config

**Available themes out-of-box**: 11 built-in + "tunacode" custom = 12 themes with zero additional work.
