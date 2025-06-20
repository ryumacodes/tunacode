"""
Characterization tests for TunaCode UI tool confirmation flows.
Covers: ToolUI, tool title logic, code block rendering, and argument rendering.
"""

import pytest
from unittest.mock import patch, MagicMock

import tunacode.ui.tool_ui as tool_ui_mod

def test_toolui_get_tool_title_internal():
    tool_ui = tool_ui_mod.ToolUI()
    with patch("tunacode.ui.tool_ui.ApplicationSettings") as mock_settings:
        mock_settings.return_value.internal_tools = ["foo"]
        assert tool_ui._get_tool_title("foo") == "Tool(foo)"
        assert tool_ui._get_tool_title("bar") == "MCP(bar)"

def test_toolui_create_code_block_returns_markdown():
    tool_ui = tool_ui_mod.ToolUI()
    with patch("tunacode.ui.tool_ui.ext_to_lang", return_value="python"):
        # Import the actual markdown function
        from tunacode.ui import console
        with patch.object(console, 'markdown') as mock_md:
            mock_md.return_value = "MARKDOWN_OBJ"
            result = tool_ui._create_code_block("file.py", "print(1)")
            assert result == "MARKDOWN_OBJ"
            mock_md.assert_called_once()