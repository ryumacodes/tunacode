"""
Characterization tests for _process_node functionality.
These tests capture the CURRENT behavior of node processing.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import json

from tunacode.core.agents.main import _process_node

pytestmark = pytest.mark.asyncio


class MockNode:
    """Mock node for testing."""
    def __init__(self, request=None, thought=None, model_response=None, result=None):
        if request:
            self.request = request
        if thought:
            self.thought = thought
        if model_response:
            self.model_response = model_response
        if result:
            self.result = result


class MockPart:
    """Mock message part."""
    def __init__(self, content=None, part_kind=None, tool_name=None, args=None, tool_call_id=None):
        self.part_kind = part_kind  # Always set part_kind, even if None
        if content is not None:
            self.content = content
        if tool_name:
            self.tool_name = tool_name
        if args is not None:
            self.args = args
        if tool_call_id:
            self.tool_call_id = tool_call_id


class MockModelResponse:
    """Mock model response."""
    def __init__(self, parts):
        self.parts = parts


class TestProcessNode:
    """Golden-master tests for _process_node behavior."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.state_manager = Mock()
        self.state_manager.session = Mock()
        self.state_manager.session.messages = []
        self.state_manager.session.show_thoughts = False
        self.state_manager.session.tool_calls = []
        self.state_manager.session.files_in_context = set()
        self.state_manager.session.current_iteration = 1
    
    async def test_process_node_with_request(self):
        """Capture behavior when node has request."""
        # Arrange
        request = {"role": "user", "content": "Test request"}
        node = MockNode(request=request)
        
        # Act
        await _process_node(node, None, self.state_manager)
        
        # Assert - Golden master
        assert len(self.state_manager.session.messages) == 1
        assert self.state_manager.session.messages[0] == request
    
    async def test_process_node_with_thought(self):
        """Capture behavior when node has thought."""
        # Arrange
        thought = "Thinking about the problem..."
        node = MockNode(thought=thought)
        
        # Act
        await _process_node(node, None, self.state_manager)
        
        # Assert - Golden master
        assert len(self.state_manager.session.messages) == 1
        assert self.state_manager.session.messages[0] == {"thought": thought}
    
    async def test_process_node_with_thought_display_enabled(self):
        """Capture behavior when thoughts display is enabled."""
        # Arrange
        self.state_manager.session.show_thoughts = True
        thought = "Planning the approach..."
        node = MockNode(thought=thought)
        
        with patch('tunacode.ui.console.muted', new_callable=AsyncMock) as mock_muted:
            # Act
            await _process_node(node, None, self.state_manager)
            
            # Assert - Golden master
            mock_muted.assert_called_with(f"THOUGHT: {thought}")
    
    async def test_process_node_with_tool_calls(self):
        """Capture behavior processing tool calls."""
        # Arrange
        tool_call = MockPart(
            part_kind="tool-call",
            tool_name="read_file",
            args={"file_path": "/tmp/test.txt"},
            tool_call_id="tool_123"
        )
        response = MockModelResponse([tool_call])
        node = MockNode(model_response=response)
        tool_callback = AsyncMock()
        
        # Act
        await _process_node(node, tool_callback, self.state_manager)
        
        # Assert - Golden master
        assert len(self.state_manager.session.messages) == 1
        assert self.state_manager.session.messages[0] == response
        
        # Tool call tracked
        assert len(self.state_manager.session.tool_calls) == 1
        assert self.state_manager.session.tool_calls[0] == {
            "tool": "read_file",
            "args": {"file_path": "/tmp/test.txt"},
            "iteration": 1
        }
        
        # File tracked (read_file special case)
        assert "/tmp/test.txt" in self.state_manager.session.files_in_context
        
        # Callback invoked
        tool_callback.assert_called_once_with(tool_call, node)
    
    async def test_process_node_tool_call_with_string_args(self):
        """Capture behavior when tool args is string instead of dict."""
        # Arrange
        self.state_manager.session.show_thoughts = True
        tool_call = MockPart(
            part_kind="tool-call",
            tool_name="bash",
            args="echo 'string args'",  # String instead of dict
            tool_call_id="tool_456"
        )
        response = MockModelResponse([tool_call])
        node = MockNode(model_response=response)
        tool_callback = AsyncMock()
        
        with patch('tunacode.ui.console.muted', new_callable=AsyncMock) as mock_muted:
            # Act
            await _process_node(node, tool_callback, self.state_manager)
            
            # Assert - Golden master
            # Should log the tool collection line for bash even when args is a raw string
            calls = [c.args[0] for c in mock_muted.call_args_list]
            assert any("COLLECTED: bash" in line for line in calls)
    
    async def test_process_node_tool_return(self):
        """Capture behavior processing tool returns."""
        # Arrange
        tool_return = MockPart(
            part_kind="tool-return",
            tool_name="grep",
            content="Found 5 matches in 3 files"
        )
        response = MockModelResponse([tool_return])
        node = MockNode(model_response=response)
        
        # Act
        await _process_node(node, None, self.state_manager)
        
        # Assert - Golden master
        assert len(self.state_manager.session.messages) == 2
        assert self.state_manager.session.messages[0] == response
        assert self.state_manager.session.messages[1] == "OBSERVATION[grep]: Found 5 matches in 3 files"
    
    async def test_process_node_model_response_thoughts_enabled(self):
        """Capture behavior extracting thoughts from model response."""
        # Arrange
        self.state_manager.session.show_thoughts = True
        
        # Multiple thought patterns
        content_with_thoughts = '''
        Let me think about this problem.
        {"thought": "Need to check the file first"}
        I'll read the file to understand the context.
        {"thought": "File might contain configuration data"}
        '''
        
        part = MockPart(content=content_with_thoughts)
        response = MockModelResponse([part])
        node = MockNode(model_response=response)
        
        with patch('tunacode.ui.console.muted', new_callable=AsyncMock) as mock_muted:
            with patch('tunacode.utils.token_counter.estimate_tokens', return_value=150):
                # Act
                await _process_node(node, None, self.state_manager)
                
                # Assert - Golden master
                calls = [call[0][0] for call in mock_muted.call_args_list]
                
                # Should display response content
                assert any("RESPONSE:" in call for call in calls)
                assert any("TOKENS: ~150" in call for call in calls)
                
                # Should extract both thoughts
                assert any("REASONING: Need to check the file first" in call for call in calls)
                assert any("REASONING: File might contain configuration data" in call for call in calls)
    
    async def test_process_node_fallback_json_parsing(self):
        """Capture behavior when no structured tool calls but JSON in content."""
        # Arrange
        content_with_json_tool = 'I need to read a file: {"tool": "read_file", "args": {"file_path": "config.json"}}'
        part = MockPart(content=content_with_json_tool)
        response = MockModelResponse([part])
        node = MockNode(model_response=response)
        tool_callback = AsyncMock()
        
        # Act
        await _process_node(node, tool_callback, self.state_manager)
        
        # Assert - Golden master
        # Should have called extract_and_execute_tool_calls
        tool_callback.assert_called_once()
        call_args = tool_callback.call_args[0][0]
        assert call_args.tool_name == "read_file"
        assert call_args.args == {"file_path": "config.json"}
    
    async def test_process_node_tool_display_formatting(self):
        """Capture behavior of special tool display formatting."""
        # Arrange
        self.state_manager.session.show_thoughts = True
        
        # Various tool types
        tools = [
            MockPart(part_kind="tool-call", tool_name="read_file", 
                    args={"file_path": "/very/long/path/to/some/file.txt"}, tool_call_id="1"),
            MockPart(part_kind="tool-call", tool_name="write_file",
                    args={"file_path": "output.txt", "content": "data"}, tool_call_id="2"),
            MockPart(part_kind="tool-call", tool_name="update_file",
                    args={"file_path": "main.py", "pattern": "old", "replacement": "new"}, tool_call_id="3"),
            MockPart(part_kind="tool-call", tool_name="bash",
                    args={"command": "find . -name '*.py' | xargs grep -l 'import os' | head -20"}, tool_call_id="4"),
            MockPart(part_kind="tool-call", tool_name="list_dir",
                    args={"directory": "/home/user/projects"}, tool_call_id="5"),
            MockPart(part_kind="tool-call", tool_name="grep",
                    args={"pattern": "TODO", "directory": ".", "include_files": "*.py"}, tool_call_id="6")
        ]
        
        response = MockModelResponse(tools)
        node = MockNode(model_response=response)
        tool_callback = AsyncMock()
        
        with patch('tunacode.ui.console.muted', new_callable=AsyncMock) as mock_muted:
            # Act
            await _process_node(node, tool_callback, self.state_manager)
            
            # Assert - Golden master
            calls = [call[0][0] for call in mock_muted.call_args_list]
            
            # Verify that each tool name was logged via the "COLLECTED:" prefix
            expected_tools = [
                "read_file",
                "write_file",
                "update_file",
                "bash",
                "list_dir",
                "grep",
            ]
            for tool_name in expected_tools:
                assert any(f"COLLECTED: {tool_name}" in line for line in calls)
    
    async def test_process_node_edge_cases(self):
        """Capture behavior with edge cases."""
        # Arrange
        # Tool with no args attribute
        tool_no_args = MockPart(part_kind="tool-call", tool_name="custom_tool", tool_call_id="no_args")
        
        # Tool with None args
        tool_none_args = MockPart(part_kind="tool-call", tool_name="another_tool", 
                                 args=None, tool_call_id="none_args")
        
        response = MockModelResponse([tool_no_args, tool_none_args])
        node = MockNode(model_response=response)
        tool_callback = AsyncMock()
        
        # Act
        await _process_node(node, tool_callback, self.state_manager)
        
        # Assert - Golden master
        assert len(self.state_manager.session.tool_calls) == 2
        
        # No args becomes empty dict
        assert self.state_manager.session.tool_calls[0]["args"] == {}
        
        # None args becomes empty dict
        assert self.state_manager.session.tool_calls[1]["args"] == {}