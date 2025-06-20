# tests/characterization/conftest.py
# ... existing code ...
# Stub any missing Rich UI dependencies so that characterization tests can
# import TunaCode UI modules without requiring the real ``rich`` package.
#
# The main test suite already supplies a lightweight stub in ``tests/conftest.py``
# but several recently-added UI modules now import extra sub-packages such as
# ``rich.pretty`` and ``rich.table`` that were not covered by the original stub.
# To keep the production code untouched while ensuring reliable test collection,
# we extend the existing stubs (or create them if they are not present).

import sys
import types
from types import ModuleType


# Helper to create a sub-module and register it in ``sys.modules`` as well as on
# its parent package so that ``import rich.xyz`` works transparently.

def _ensure_module(full_name: str) -> ModuleType:
    """Return the (potentially newly-created) module for *full_name*."""
    if full_name in sys.modules:
        return sys.modules[full_name]

    module = types.ModuleType(full_name)
    sys.modules[full_name] = module

    if "." in full_name:
        parent_name, child_name = full_name.rsplit(".", 1)
        parent = _ensure_module(parent_name)
        setattr(parent, child_name, module)
    return module


# Boot-strap the top-level ``rich`` stub if it does not exist. We do *not* import
# the real library because it is intentionally excluded from the runtime
# dependencies to keep the install footprint small.
rich_mod = sys.modules.get("rich")
if rich_mod is None or not hasattr(rich_mod, "console"):
    rich_mod = _ensure_module("rich")

    # ------------------------------------------------------------------
    # rich.console ------------------------------------------------------
    console_mod = _ensure_module("rich.console")

    class Console:  # Minimal subset used in tests
        def __init__(self, *args, **kwargs):
            pass

        def print(self, *args, **kwargs):
            # The real Console prints to stdout; for tests we can safely ignore.
            pass

    console_mod.Console = Console

    # ------------------------------------------------------------------
    # rich.markdown -----------------------------------------------------
    markdown_mod = _ensure_module("rich.markdown")

    class Markdown:  # noqa: D401 – simple stub class
        """Trivial stand-in that stores the provided *text* on ``markup``."""

        def __init__(self, text: str):
            self.markup = text

        def __str__(self) -> str:  # type: ignore[override]
            return self.markup

    markdown_mod.Markdown = Markdown

    # ------------------------------------------------------------------
    # rich.pretty -------------------------------------------------------
    pretty_mod = _ensure_module("rich.pretty")

    class Pretty:  # Simple wrapper used only for type checks in tests
        def __init__(self, obj):
            self.obj = obj

        def __repr__(self):  # pragma: no cover – debugging aid
            return f"<Pretty {self.obj!r}>"

    pretty_mod.Pretty = Pretty

    # ------------------------------------------------------------------
    # rich.padding ------------------------------------------------------
    padding_mod = _ensure_module("rich.padding")

    class Padding:  # Very light replacement
        def __init__(self, content, pad):
            self.content = content
            self.pad = pad

        def __repr__(self):  # pragma: no cover
            return f"<Padding {self.content!r} {self.pad}>"

    padding_mod.Padding = Padding

    # ------------------------------------------------------------------
    # rich.panel --------------------------------------------------------
    panel_mod = _ensure_module("rich.panel")

    class Panel:  # Simplified placeholder
        def __init__(self, *args, **kwargs):
            pass

    panel_mod.Panel = Panel

    # ------------------------------------------------------------------
    # rich.table --------------------------------------------------------
    table_mod = _ensure_module("rich.table")

    class Table:  # Enough API for current tests
        def __init__(self, *args, **kwargs):
            pass

        def add_column(self, *args, **kwargs):
            pass

        def add_row(self, *args, **kwargs):
            pass

    table_mod.Table = Table

    # ------------------------------------------------------------------
    # rich.box ----------------------------------------------------------
    box_mod = _ensure_module("rich.box")
    box_mod.ROUNDED = None 

# ---------------------------------------------------------------------------
# Ensure *all* required sub-modules exist – this runs regardless of whether the
# original stub came from ``tests/conftest.py`` or we just created one above.
# ---------------------------------------------------------------------------
_required_rich_submodules = {
    "rich.console": "Console",
    "rich.markdown": "Markdown",
    "rich.pretty": "Pretty",
    "rich.padding": "Padding",
    "rich.panel": "Panel",
    "rich.table": "Table",
    "rich.box": "ROUNDED",
}

for mod_name, sentinel_attr in _required_rich_submodules.items():
    mod = _ensure_module(mod_name)

    # If the sentinel attribute is already present we assume the module is OK.
    if hasattr(mod, sentinel_attr):
        continue

    # Otherwise provide a minimal default implementation depending on the name.
    if mod_name.endswith(".console"):
        class Console:  # noqa: D401 – minimal stand-in
            def __init__(self, *args, **kwargs):
                pass
            def print(self, *args, **kwargs):
                pass
        mod.Console = Console  # type: ignore[attr-defined]

    elif mod_name.endswith(".markdown"):
        class Markdown:
            def __init__(self, text: str):
                self.markup = text
            def __str__(self):  # pragma: no cover
                return self.markup
        mod.Markdown = Markdown  # type: ignore[attr-defined]

    # If the module already existed but the Markdown implementation does not
    # expose the expected ``markup`` attribute, we transparently subclass it at
    # runtime to add the attribute while preserving the original behaviour.
    elif mod_name.endswith(".markdown") and hasattr(mod, "Markdown"):
        _orig_md_cls = mod.Markdown  # type: ignore[attr-defined]

        if not hasattr(_orig_md_cls("test"), "markup"):
            class _MarkdownWithMarkup(_orig_md_cls):  # type: ignore[misc]
                def __init__(self, text: str):  # type: ignore[no-redef]
                    super().__init__() if hasattr(super(), "__init__") else None
                    self.markup = text
            mod.Markdown = _MarkdownWithMarkup  # type: ignore[attr-defined]

    elif mod_name.endswith(".pretty"):
        class Pretty:
            def __init__(self, obj):
                self.obj = obj
            def __repr__(self):  # pragma: no cover
                return f"<Pretty {self.obj!r}>"
        mod.Pretty = Pretty  # type: ignore[attr-defined]

    elif mod_name.endswith(".padding"):
        class Padding:
            def __init__(self, content, pad):
                self.content = content
                self.pad = pad
        mod.Padding = Padding  # type: ignore[attr-defined]

    elif mod_name.endswith(".panel"):
        class Panel:
            def __init__(self, *args, **kwargs):
                pass
        mod.Panel = Panel  # type: ignore[attr-defined]

    elif mod_name.endswith(".table"):
        class Table:
            def __init__(self, *args, **kwargs):
                pass
            def add_column(self, *args, **kwargs):
                pass
            def add_row(self, *args, **kwargs):
                pass
        mod.Table = Table  # type: ignore[attr-defined]

    elif mod_name.endswith(".box"):
        mod.ROUNDED = None  # type: ignore[attr-defined] 

# ---------------------------------------------------------------------------
# Post-processing: guarantee ``rich.markdown.Markdown`` has the expected API
# ---------------------------------------------------------------------------

_rich_md_mod = sys.modules.get("rich.markdown")
if _rich_md_mod is not None and hasattr(_rich_md_mod, "Markdown"):
    _OrigMarkdown = _rich_md_mod.Markdown  # type: ignore[attr-defined]
    try:
        _instance = _OrigMarkdown("test")
    except Exception:
        _instance = None

    if _instance is None or not hasattr(_instance, "markup"):
        class _MarkdownWithMarkup(_OrigMarkdown):  # type: ignore[misc]
            def __init__(self, text: str):  # type: ignore[no-redef]
                # Call original constructor if it expects parameters
                try:
                    super().__init__(text)  # type: ignore[misc]
                except TypeError:
                    # Some original stubs inherit from 'str' and take no args
                    super().__init__()
                self.markup = text

            def __str__(self):  # pragma: no cover
                return self.markup

        _rich_md_mod.Markdown = _MarkdownWithMarkup  # type: ignore[attr-defined] 