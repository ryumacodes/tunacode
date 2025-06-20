"""
Unit tests for tool categorization constants and helper functions.
"""

import pytest
from tunacode.constants import (
    TOOL_READ_FILE,
    TOOL_WRITE_FILE,
    TOOL_UPDATE_FILE,
    TOOL_BASH,
    TOOL_RUN_COMMAND,
    TOOL_GREP,
    TOOL_LIST_DIR,
    TOOL_GLOB,
)


def test_read_only_tools_constant_exists():
    """Test that READ_ONLY_TOOLS constant is defined."""
    from tunacode.constants import READ_ONLY_TOOLS
    
    assert isinstance(READ_ONLY_TOOLS, (list, tuple, set))
    assert len(READ_ONLY_TOOLS) > 0


def test_write_tools_constant_exists():
    """Test that WRITE_TOOLS constant is defined."""
    from tunacode.constants import WRITE_TOOLS
    
    assert isinstance(WRITE_TOOLS, (list, tuple, set))
    assert len(WRITE_TOOLS) > 0


def test_execute_tools_constant_exists():
    """Test that EXECUTE_TOOLS constant is defined."""
    from tunacode.constants import EXECUTE_TOOLS
    
    assert isinstance(EXECUTE_TOOLS, (list, tuple, set))
    assert len(EXECUTE_TOOLS) > 0


def test_tool_categorization_is_complete():
    """Test that all tools are categorized."""
    from tunacode.constants import READ_ONLY_TOOLS, WRITE_TOOLS, EXECUTE_TOOLS
    
    all_tools = {
        TOOL_READ_FILE,
        TOOL_WRITE_FILE,
        TOOL_UPDATE_FILE,
        TOOL_BASH,
        TOOL_RUN_COMMAND,
        TOOL_GREP,
        TOOL_LIST_DIR,
        TOOL_GLOB,
    }
    
    categorized_tools = set(READ_ONLY_TOOLS) | set(WRITE_TOOLS) | set(EXECUTE_TOOLS)
    
    assert all_tools == categorized_tools, "Not all tools are categorized"


def test_tool_categories_are_disjoint():
    """Test that tool categories don't overlap."""
    from tunacode.constants import READ_ONLY_TOOLS, WRITE_TOOLS, EXECUTE_TOOLS
    
    read_set = set(READ_ONLY_TOOLS)
    write_set = set(WRITE_TOOLS)
    execute_set = set(EXECUTE_TOOLS)
    
    assert read_set.isdisjoint(write_set), "READ_ONLY_TOOLS and WRITE_TOOLS overlap"
    assert read_set.isdisjoint(execute_set), "READ_ONLY_TOOLS and EXECUTE_TOOLS overlap"
    assert write_set.isdisjoint(execute_set), "WRITE_TOOLS and EXECUTE_TOOLS overlap"


def test_correct_tool_categorization():
    """Test that tools are in the correct categories."""
    from tunacode.constants import READ_ONLY_TOOLS, WRITE_TOOLS, EXECUTE_TOOLS
    
    # Read-only tools should include these
    assert TOOL_READ_FILE in READ_ONLY_TOOLS
    assert TOOL_GREP in READ_ONLY_TOOLS
    assert TOOL_LIST_DIR in READ_ONLY_TOOLS
    assert TOOL_GLOB in READ_ONLY_TOOLS
    
    # Write tools should include these
    assert TOOL_WRITE_FILE in WRITE_TOOLS
    assert TOOL_UPDATE_FILE in WRITE_TOOLS
    
    # Execute tools should include these
    assert TOOL_BASH in EXECUTE_TOOLS
    assert TOOL_RUN_COMMAND in EXECUTE_TOOLS


def test_is_read_only_tool_helper():
    """Test the is_read_only_tool helper function."""
    from tunacode.core.tool_handler import is_read_only_tool
    
    # Test read-only tools
    assert is_read_only_tool(TOOL_READ_FILE) is True
    assert is_read_only_tool(TOOL_GREP) is True
    assert is_read_only_tool(TOOL_LIST_DIR) is True
    assert is_read_only_tool(TOOL_GLOB) is True
    
    # Test non-read-only tools
    assert is_read_only_tool(TOOL_WRITE_FILE) is False
    assert is_read_only_tool(TOOL_UPDATE_FILE) is False
    assert is_read_only_tool(TOOL_BASH) is False
    assert is_read_only_tool(TOOL_RUN_COMMAND) is False
    
    # Test unknown tool
    assert is_read_only_tool("unknown_tool") is False