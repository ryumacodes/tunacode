"""
Characterization tests for TunaCode UI console coordination module.
Covers: console object, markdown utility, and re-exported functions.
"""

import pytest
from unittest.mock import patch, MagicMock

import tunacode.ui.console as console_mod

def test_console_object_is_rich_console():
    # Should be a rich.console.Console instance
    assert hasattr(console_mod, "console")
    assert console_mod.console.__class__.__name__ == "Console"

def test_markdown_returns_markdown_object():
    from rich.markdown import Markdown
    md = console_mod.markdown("# Title")
    assert isinstance(md, Markdown)
    # Current behavior: Markdown object has 'markup' attribute, not '_text'
    assert "# Title" in md.markup

def test_reexported_functions_available():
    # Smoke test: all __all__ functions are present
    for name in console_mod.__all__:
        assert hasattr(console_mod, name)