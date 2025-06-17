"""
Test JSON tool parsing fallback functionality.
Tests the ability to parse and execute tool calls from JSON when structured calling fails.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from tunacode.core.agents.main import parse_json_tool_calls, extract_and_execute_tool_calls
from tunacode.configuration.defaults import DEFAULT_USER_CONFIG


class MockStateManager:
    """Mock state manager for testing."""
    def __init__(self):
        self.session = MagicMock()
        self.session.show_thoughts = True
        self.session.user_config = DEFAULT_USER_CONFIG.copy()


class TestJSONToolParsing:
    """Test suite for JSON tool parsing functionality."""
    
    @pytest.fixture
    def state_manager(self):
        """Create a mock state manager."""
        return MockStateManager()
    
    @pytest.fixture
    def mock_tool_callback(self):
        """Create a mock tool callback function."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_parse_simple_json_tool_call(self, state_manager, mock_tool_callback):
        """Test parsing a simple JSON tool call."""
        text = '{"tool": "write_file", "args": {"path": "test.js", "content": "console.log(\'hello\');"}}'
        
        await parse_json_tool_calls(text, mock_tool_callback, state_manager)
        
        # Verify tool callback was called
        assert mock_tool_callback.called
        call_args = mock_tool_callback.call_args[0]
        tool_call = call_args[0]
        
        assert tool_call.tool_name == "write_file"
        assert tool_call.args["path"] == "test.js"
        assert tool_call.args["content"] == "console.log('hello');"
        assert tool_call.tool_call_id.startswith("fallback_")
    
    @pytest.mark.asyncio
    async def test_parse_multiple_json_tool_calls(self, state_manager, mock_tool_callback):
        """Test parsing multiple JSON tool calls in one text."""
        text = '''
        First, let me read the file: {"tool": "read_file", "args": {"path": "package.json"}}
        Then I'll write a new file: {"tool": "write_file", "args": {"path": "output.txt", "content": "result"}}
        '''
        
        await parse_json_tool_calls(text, mock_tool_callback, state_manager)
        
        # Verify both tool calls were made
        assert mock_tool_callback.call_count == 2
        
        # Check first call
        first_call = mock_tool_callback.call_args_list[0][0][0]
        assert first_call.tool_name == "read_file"
        assert first_call.args["path"] == "package.json"
        
        # Check second call
        second_call = mock_tool_callback.call_args_list[1][0][0]
        assert second_call.tool_name == "write_file"
        assert second_call.args["path"] == "output.txt"
    
    @pytest.mark.asyncio
    async def test_parse_code_block_tool_calls(self, state_manager, mock_tool_callback):
        """Test parsing tool calls from JSON code blocks."""
        text = '''
        I need to run a command:
        ```json
        {"tool": "run_command", "args": {"command": "ls -la"}}
        ```
        '''
        
        await extract_and_execute_tool_calls(text, mock_tool_callback, state_manager)
        
        # Verify tool callback was called
        assert mock_tool_callback.called
        call_args = mock_tool_callback.call_args[0]
        tool_call = call_args[0]
        
        assert tool_call.tool_name == "run_command"
        assert tool_call.args["command"] == "ls -la"
        # Could be either fallback_ or codeblock_ depending on which parser matches first
        assert tool_call.tool_call_id.startswith(("fallback_", "codeblock_"))
    
    @pytest.mark.asyncio
    async def test_invalid_json_handling(self, state_manager, mock_tool_callback):
        """Test handling of invalid JSON gracefully."""
        text = '{"tool": "invalid_json", "args": {"broken": json}}'  # Invalid JSON
        
        # Should not raise exception
        await parse_json_tool_calls(text, mock_tool_callback, state_manager)
        
        # Tool callback should not be called for invalid JSON
        assert not mock_tool_callback.called
    
    @pytest.mark.asyncio
    async def test_no_tool_callback(self, state_manager):
        """Test behavior when no tool callback is provided."""
        text = '{"tool": "write_file", "args": {"path": "test.js", "content": "code"}}'
        
        # Should not raise exception
        await parse_json_tool_calls(text, None, state_manager)
        # No assertions needed - just ensuring it doesn't crash
    
    @pytest.mark.asyncio
    async def test_extract_and_execute_combination(self, state_manager, mock_tool_callback):
        """Test extract_and_execute_tool_calls with both inline JSON and code blocks."""
        text = '''
        Let me start with: {"tool": "read_file", "args": {"path": "config.json"}}
        
        Then I'll execute this:
        ```json
        {"tool": "run_command", "args": {"command": "npm test"}}
        ```
        
        Finally: {"tool": "write_file", "args": {"path": "result.txt", "content": "done"}}
        '''
        
        await extract_and_execute_tool_calls(text, mock_tool_callback, state_manager)
        
        # Should have called tool callback multiple times (both parsers may find the same tools)
        assert mock_tool_callback.call_count >= 3
        
        # Verify all different tool types were called
        called_tools = [call[0][0].tool_name for call in mock_tool_callback.call_args_list]
        assert "read_file" in called_tools
        assert "run_command" in called_tools
        assert "write_file" in called_tools
    
    @pytest.mark.asyncio
    async def test_empty_text_handling(self, state_manager, mock_tool_callback):
        """Test handling of empty or whitespace-only text."""
        empty_texts = ["", "   ", "\n\n", "No tool calls here"]
        
        for text in empty_texts:
            await extract_and_execute_tool_calls(text, mock_tool_callback, state_manager)
        
        # No tool calls should be made for empty/non-tool text
        assert not mock_tool_callback.called
    
    @pytest.mark.asyncio
    async def test_complex_nested_args(self, state_manager, mock_tool_callback):
        """Test parsing complex nested JSON arguments."""
        text = ('{"tool": "update_file", "args": {"path": "config.json", ' 
                '"target": "{\\"port\\": 3000}", ' 
                '"patch": "{\\"port\\": 8080, \\"host\\": \\"localhost\\"}"}}')
        
        await parse_json_tool_calls(text, mock_tool_callback, state_manager)
        
        assert mock_tool_callback.called
        tool_call = mock_tool_callback.call_args[0][0]
        
        assert tool_call.tool_name == "update_file"
        assert tool_call.args["path"] == "config.json"
        assert "port" in tool_call.args["target"]
        assert "host" in tool_call.args["patch"]


if __name__ == "__main__":
    # Run tests directly if executed as script
    import sys
    import subprocess
    
    try:
        # Try to run with pytest
        result = subprocess.run(
            [sys.executable, "-m", "pytest", __file__, "-v"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        sys.exit(result.returncode)
    except FileNotFoundError:
        # Fallback to manual test execution
        print("pytest not available, running tests manually...")
        
        async def run_manual_tests():
            test_instance = TestJSONToolParsing()
            state_manager = MockStateManager()
            mock_callback = AsyncMock()
            
            print("Running test_parse_simple_json_tool_call...")
            await test_instance.test_parse_simple_json_tool_call(state_manager, mock_callback)
            print("✓ PASSED")
            
            mock_callback.reset_mock()
            print("Running test_parse_multiple_json_tool_calls...")
            await test_instance.test_parse_multiple_json_tool_calls(state_manager, mock_callback)
            print("✓ PASSED")
            
            mock_callback.reset_mock()
            print("Running test_parse_code_block_tool_calls...")
            await test_instance.test_parse_code_block_tool_calls(state_manager, mock_callback)
            print("✓ PASSED")
            
            print("All manual tests passed!")
        
        asyncio.run(run_manual_tests())