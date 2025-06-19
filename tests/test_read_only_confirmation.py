"""
Tests for read-only tool confirmation behavior.
"""

import pytest
from unittest.mock import Mock
from tunacode.core.tool_handler import ToolHandler, is_read_only_tool
from tunacode.constants import TOOL_READ_FILE, TOOL_GREP, TOOL_LIST_DIR, TOOL_WRITE_FILE, TOOL_BASH


class TestReadOnlyConfirmation:
    """Test that read-only tools skip confirmation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.state_manager = Mock()
        self.state_manager.session = Mock()
        self.state_manager.session.yolo = False
        self.state_manager.session.tool_ignore = []
        self.handler = ToolHandler(self.state_manager)
    
    def test_read_only_tools_skip_confirmation_by_default(self):
        """Test that read-only tools don't require confirmation."""
        # Read-only tools should not require confirmation
        assert self.handler.should_confirm(TOOL_READ_FILE) is False
        assert self.handler.should_confirm(TOOL_GREP) is False
        assert self.handler.should_confirm(TOOL_LIST_DIR) is False
        
        # Write/execute tools should still require confirmation
        assert self.handler.should_confirm(TOOL_WRITE_FILE) is True
        assert self.handler.should_confirm(TOOL_BASH) is True
    
    def test_yolo_mode_skips_all_confirmations(self):
        """Test that yolo mode still works for all tools."""
        self.state_manager.session.yolo = True
        
        # All tools should skip confirmation in yolo mode
        assert self.handler.should_confirm(TOOL_READ_FILE) is False
        assert self.handler.should_confirm(TOOL_WRITE_FILE) is False
        assert self.handler.should_confirm(TOOL_BASH) is False
    
    def test_tool_ignore_list_still_works(self):
        """Test that tool_ignore list is still respected."""
        # Add write_file to ignore list
        self.state_manager.session.tool_ignore = [TOOL_WRITE_FILE]
        
        # Write file should now skip confirmation
        assert self.handler.should_confirm(TOOL_WRITE_FILE) is False
        
        # But bash should still require it
        assert self.handler.should_confirm(TOOL_BASH) is True
    
    def test_unknown_tool_requires_confirmation(self):
        """Test that unknown tools require confirmation by default."""
        assert self.handler.should_confirm("unknown_tool") is True
    
    def test_read_only_helper_function(self):
        """Test the is_read_only_tool helper."""
        # Test all read-only tools
        assert is_read_only_tool(TOOL_READ_FILE) is True
        assert is_read_only_tool(TOOL_GREP) is True
        assert is_read_only_tool(TOOL_LIST_DIR) is True
        
        # Test non-read-only tools
        assert is_read_only_tool(TOOL_WRITE_FILE) is False
        assert is_read_only_tool(TOOL_BASH) is False
        assert is_read_only_tool("unknown") is False