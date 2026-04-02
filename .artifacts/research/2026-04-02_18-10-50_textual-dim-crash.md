---
title: "textual dim crash research findings"
link: "textual-dim-crash-research"
type: research
ontological_relations:
  - relates_to: [[docs/modules/ui/ui]]
tags: [research, textual, ui, rendering]
uuid: "c19f88bd-633b-4fb5-b7f0-81075fbd10af"
created_at: "2026-04-02T18:10:50-0500"
---

## Structure

- Startup entry to Textual app:
  - `src/tunacode/ui/main.py:L67` defines `_run_textual_app(...)`.
  - `src/tunacode/ui/main.py:L84` awaits `run_textual_repl(...)`.
  - `src/tunacode/ui/repl_support.py:L231` defines `run_textual_repl(...)`.
  - `src/tunacode/ui/repl_support.py:L234` constructs `TextualReplApp(...)`.
  - `src/tunacode/ui/repl_support.py:L235` awaits `app.run_async()`.

- Theme registration and selection:
  - `src/tunacode/ui/app.py:L118` starts `TextualReplApp.__init__(...)`.
  - `src/tunacode/ui/app.py:L120` registers TunaCode theme.
  - `src/tunacode/ui/app.py:L121` registers NeXTSTEP theme.
  - `src/tunacode/ui/app.py:L122` registers wrapped built-in themes from `wrap_builtin_themes(...)`.
  - `src/tunacode/ui/app.py:L124` sets `self.theme = THEME_NAME`.
  - `src/tunacode/ui/lifecycle.py:L45` defines `_init_theme(...)`.
  - `src/tunacode/ui/lifecycle.py:L50` reads `user_config["settings"]["theme"]`.
  - `src/tunacode/ui/lifecycle.py:L54` assigns `self._app.theme = saved_theme`.
  - `src/tunacode/configuration/defaults.py:L29` sets default theme to `"dracula"`.

- Startup welcome render path:
  - `src/tunacode/ui/lifecycle.py:L80` defines `_start_repl(...)`.
  - `src/tunacode/ui/lifecycle.py:L95` imports `show_welcome`.
  - `src/tunacode/ui/lifecycle.py:L97` calls `show_welcome(app.chat_container)`.
  - `src/tunacode/ui/welcome.py:L33` defines `generate_logo()`.
  - `src/tunacode/ui/welcome.py:L35` reads `logo.ansi`.
  - `src/tunacode/ui/welcome.py:L36` returns `Text.from_ansi(logo_ansi)`.
  - `src/tunacode/ui/welcome.py:L46` writes the logo to the log widget.
  - `src/tunacode/ui/welcome.py:L86` writes the textual welcome block to the log widget.
  - `src/tunacode/ui/logo_assets.py:L13` defines `read_logo_ansi(...)`.
  - `src/tunacode/ui/logo_assets.py:L20` returns the asset contents.

- Chat rendering path:
  - `src/tunacode/ui/widgets/chat.py:L224` defines `ChatContainer`.
  - `src/tunacode/ui/widgets/chat.py:L262` defines `ChatContainer.write(...)`.
  - `src/tunacode/ui/widgets/chat.py:L283` wraps content in `CopyOnSelectStatic(panel_content)`.
  - `src/tunacode/ui/widgets/chat.py:L301` mounts the widget into the scroll container.
  - `src/tunacode/ui/widgets/chat.py:L29` defines `SelectableRichVisual`.
  - `src/tunacode/ui/widgets/chat.py:L57` calls `self._widget.post_render(...)`.
  - `src/tunacode/ui/widgets/chat.py:L58` calls `console.render(...)`.
  - `src/tunacode/ui/widgets/chat.py:L66` defines `with_offset(...)`.
  - `src/tunacode/ui/widgets/chat.py:L69` adds `RichStyle(meta={"offset": (x, y)})`.

## Key Files

- `pyproject.toml:L33` declares `rich>=14.2.0,<15.0.0`.
- `pyproject.toml:L34` declares `textual>=4.0.0,<5.0.0`.
- `src/tunacode/constants.py:L118` defines built-in theme palettes.
- `src/tunacode/constants.py:L183` includes the `textual-ansi` palette.
- `src/tunacode/constants.py:L217` defines `SUPPORTED_THEME_NAMES`.
- `src/tunacode/constants.py:L323` defines `wrap_builtin_themes(...)`.
- `/home/fabian/tunacode/.venv/lib/python3.11/site-packages/textual/filter.py:L128` defines `dim_color(...)`.
- `/home/fabian/tunacode/.venv/lib/python3.11/site-packages/textual/filter.py:L142` unpacks `background.triplet`.
- `/home/fabian/tunacode/.venv/lib/python3.11/site-packages/textual/filter.py:L220` defines `ANSIToTruecolor`.
- `/home/fabian/tunacode/.venv/lib/python3.11/site-packages/textual/filter.py:L233` defines `ANSIToTruecolor.truecolor_style(...)`.
- `/home/fabian/tunacode/.venv/lib/python3.11/site-packages/textual/filter.py:L254` checks `if style.dim and color is not None:`.
- `/home/fabian/tunacode/.venv/lib/python3.11/site-packages/textual/filter.py:L255` calls `dim_color(background, color)`.
- `/home/fabian/tunacode/.venv/lib/python3.11/site-packages/textual/filter.py:L273` assigns `background_rich_color = background.rich_color`.

## Patterns Found

- ANSI logo loading:
  - `src/tunacode/ui/welcome.py:L35` reads the ANSI asset.
  - `src/tunacode/ui/welcome.py:L36` parses the asset with `Text.from_ansi(...)`.
  - `src/tunacode/ui/assets/logo.ansi` length on disk: `1529` bytes.
  - `src/tunacode/ui/assets/logo.ansi` contains `75` SGR escape sequences from `\x1b\[[0-9;]*m`.
  - `src/tunacode/ui/assets/logo.ansi` contains no `\x1b[2m`.
  - `src/tunacode/ui/assets/logo.ansi` contains no `\x1b[22m`.
  - Local inspection of `generate_logo()` produced `72` Rich spans.
  - Local inspection of `generate_logo()` found `0` spans with `dim=True`.
  - Local inspection of `generate_logo()` found `6` spans whose `style.color.triplet` is `None`.

- `dim` style use in TunaCode UI:
  - `src/tunacode/ui/context_panel.py:L146`
  - `src/tunacode/ui/context_panel.py:L163`
  - `src/tunacode/ui/context_panel.py:L169`
  - `src/tunacode/ui/app.py:L499`
  - `src/tunacode/ui/app.py:L575`
  - `src/tunacode/ui/commands/debug.py:L39`
  - `src/tunacode/ui/commands/debug.py:L42`
  - `src/tunacode/ui/commands/debug.py:L46`
  - `src/tunacode/ui/commands/debug.py:L50`
  - `src/tunacode/ui/renderers/tools/bash.py:L127`
  - `src/tunacode/ui/renderers/tools/bash.py:L128`
  - `src/tunacode/ui/renderers/tools/bash.py:L129`
  - `src/tunacode/ui/renderers/tools/bash.py:L130`
  - `src/tunacode/ui/renderers/tools/discover.py:L229`
  - `src/tunacode/ui/renderers/tools/read_file.py:L192`
  - `src/tunacode/ui/renderers/tools/web_fetch.py:L96`
  - `src/tunacode/ui/renderers/panels.py:L171`
  - `src/tunacode/ui/renderers/agent_response.py:L84`
  - `src/tunacode/ui/repl_support.py:L94`
  - Local grep count for `dim` style uses under `src/tunacode/ui`: `88`.

- Selection metadata injection:
  - `src/tunacode/ui/widgets/chat.py:L66` creates a helper that preserves or creates a Rich style.
  - `src/tunacode/ui/widgets/chat.py:L69` adds `meta={"offset": (x, y)}` to each segment style.
  - `src/tunacode/ui/widgets/chat.py:L88`
  - `src/tunacode/ui/widgets/chat.py:L103`
  - `src/tunacode/ui/widgets/chat.py:L116`
  - `src/tunacode/ui/widgets/chat.py:L123`
  - `src/tunacode/ui/widgets/chat.py:L132`

## Dependencies

- Import chain in startup path:
  - `src/tunacode/ui/main.py:L14` imports `run_textual_repl` from `tunacode.ui.repl_support`.
  - `src/tunacode/ui/repl_support.py:L232` imports `TextualReplApp` from `tunacode.ui.app`.
  - `src/tunacode/ui/lifecycle.py:L95` imports `show_welcome` from `tunacode.ui.welcome`.
  - `src/tunacode/ui/lifecycle.py:L12` imports `TuiLogDisplay` from `tunacode.ui.widgets`.

- Theme registration path:
  - `src/tunacode/ui/app.py:L29-L37` imports `SUPPORTED_THEME_NAMES`, `THEME_NAME`, `build_nextstep_theme`, `build_tunacode_theme`, and `wrap_builtin_themes` through `tunacode.core.ui_api.constants`.
  - `src/tunacode/constants.py:L323` iterates `BUILTIN_THEME_PALETTES`.
  - `src/tunacode/constants.py:L303-L320` re-creates a `Theme` with original theme properties and merged variables.

- Dependency site of the exception:
  - `/home/fabian/tunacode/.venv/lib/python3.11/site-packages/textual/filter.py:L233-L258` converts system colors to truecolor and processes `style.dim`.
  - `/home/fabian/tunacode/.venv/lib/python3.11/site-packages/textual/filter.py:L255` passes the supplied `background` Rich color to `dim_color(...)`.
  - `/home/fabian/tunacode/.venv/lib/python3.11/site-packages/textual/filter.py:L142-L143` unpacks `background.triplet` and `color.triplet`.

## Symbol Index

- `src/tunacode/ui/main.py:L67` `_run_textual_app`
- `src/tunacode/ui/repl_support.py:L231` `run_textual_repl`
- `src/tunacode/ui/app.py:L90` `TextualReplApp`
- `src/tunacode/ui/lifecycle.py:L21` `AppLifecycle`
- `src/tunacode/ui/welcome.py:L33` `generate_logo`
- `src/tunacode/ui/welcome.py:L39` `show_welcome`
- `src/tunacode/ui/logo_assets.py:L13` `read_logo_ansi`
- `src/tunacode/ui/widgets/chat.py:L29` `SelectableRichVisual`
- `src/tunacode/ui/widgets/chat.py:L224` `ChatContainer`
- `/home/fabian/tunacode/.venv/lib/python3.11/site-packages/textual/filter.py:L128` `dim_color`
- `/home/fabian/tunacode/.venv/lib/python3.11/site-packages/textual/filter.py:L220` `ANSIToTruecolor`

## Observed Local Reproduction

- Installed versions:
  - `textual==4.0.0`
  - `rich==14.2.0`

- Reproduction command:

```python
from rich.color import Color as RichColor
from rich.style import Style
from textual.filter import ANSIToTruecolor
from rich.terminal_theme import DEFAULT_TERMINAL_THEME

flt = ANSIToTruecolor(DEFAULT_TERMINAL_THEME)
style = Style(color="black", bgcolor="#f7f7f7", dim=True)

flt.truecolor_style(style, RichColor.default())
flt.truecolor_style(style, RichColor.from_rgb(247, 247, 247))
```

- Observed output:

```text
truecolor_style Color('default', ColorType.DEFAULT) => TypeError cannot unpack non-iterable NoneType object
truecolor_style Color('#f7f7f7', ColorType.TRUECOLOR, triplet=ColorTriplet(red=247, green=247, blue=247)) => not dim #535353 on #f7f7f7
```
