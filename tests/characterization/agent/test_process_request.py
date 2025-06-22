"""
Characterization tests for process_request functionality.
These tests capture the CURRENT behavior of the main request processing function.
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager

from tunacode.core.agents.main import process_request

pytestmark = pytest.mark.asyncio


class MockNode:
    """Mock node for testing."""
    def __init__(self, result=None):
        if result:
            self.result = result


class MockResult:
    """Mock result object."""
    def __init__(self, output=None):
        if output:
            self.output = output


class TestProcessRequest:
    """Golden-master tests for process_request behavior."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.state_manager = Mock()
        self.state_manager.session = Mock()
        self.state_manager.session.messages = []
        self.state_manager.session.agents = {}
        self.state_manager.session.user_config = {
            "settings": {
                "max_retries": 3,
                "max_iterations": 40,
                "fallback_response": True,
                "fallback_verbosity": "normal"
            }
        }
        self.state_manager.session.show_thoughts = False
        self.state_manager.session.tool_calls = []
        self.state_manager.session.files_in_context = set()
        self.state_manager.session.iteration_count = 0
        self.state_manager.session.current_iteration = 0
    
    def create_mock_agent_run(self, nodes):
        """Create a mock agent run that properly implements async iteration."""
        class MockAgentRun:
            def __init__(self, nodes):
                self.nodes = nodes
                self.result = None
                self._index = 0
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, *args):
                pass
            
            def __aiter__(self):
                self._index = 0
                return self
            
            async def __anext__(self):
                if self._index >= len(self.nodes):
                    raise StopAsyncIteration
                node = self.nodes[self._index]
                self._index += 1
                return node
        
        return MockAgentRun(nodes)
    
    async def test_process_request_basic_flow(self):
        """Capture behavior of basic request processing."""
        # Arrange
        message = "Test request"
        nodes = [
            MockNode(),
            MockNode(result=MockResult(output="Task completed"))
        ]
        
        mock_agent = MagicMock()
        mock_agent_run = self.create_mock_agent_run(nodes)
        
        @asynccontextmanager
        async def mock_iter(msg, message_history):
            yield mock_agent_run
        
        mock_agent.iter = mock_iter
        
        with patch('tunacode.core.agents.main.get_or_create_agent', return_value=mock_agent):
            with patch('tunacode.core.agents.main._process_node', new_callable=AsyncMock) as mock_process:
                # Act
                result = await process_request("openai:gpt-4", message, self.state_manager)
                
                # Assert - Golden master
                assert hasattr(result, 'response_state')
                assert result.response_state.has_user_response
                assert not result.response_state.has_final_synthesis
                assert self.state_manager.session.iteration_count == 2
                assert mock_process.call_count == 2
    
    async def test_process_request_max_iterations_reached(self):
        """Capture behavior when max iterations is reached."""
        # Arrange
        self.state_manager.session.user_config["settings"]["max_iterations"] = 3
        message = "Complex task"
        
        # Create nodes that exceed max iterations
        nodes = [MockNode() for _ in range(5)]
        
        mock_agent = MagicMock()
        mock_agent_run = self.create_mock_agent_run(nodes)
        mock_agent_run.result = MockResult()  # No output
        
        @asynccontextmanager
        async def mock_iter(msg, message_history):
            yield mock_agent_run
        
        mock_agent.iter = mock_iter
        
        with patch('tunacode.core.agents.main.get_or_create_agent', return_value=mock_agent):
            with patch('tunacode.core.agents.main._process_node', new_callable=AsyncMock):
                with patch('tunacode.core.agents.main.patch_tool_messages') as mock_patch:
                    # Act
                    result = await process_request("openai:gpt-4", message, self.state_manager)
                    
                    # Assert - Golden master
                    assert self.state_manager.session.iteration_count == 3
                    assert hasattr(result, 'result')
                    assert "maximum iterations" in result.result.output
                    assert result.response_state.has_final_synthesis
                    mock_patch.assert_called_with("Task incomplete", state_manager=self.state_manager)
    
    async def test_process_request_fallback_response_detailed(self):
        """Capture behavior of detailed fallback response generation."""
        # Arrange
        self.state_manager.session.user_config["settings"]["max_iterations"] = 2
        self.state_manager.session.user_config["settings"]["fallback_verbosity"] = "detailed"
        message = "Complex task"
        
        # Add some tool calls to messages for fallback analysis
        tool_call_part1 = Mock()
        tool_call_part1.part_kind = "tool-call"
        tool_call_part1.tool_name = "write_file"
        tool_call_part1.args = {"file_path": "/tmp/test1.txt"}
        
        tool_call_part2 = Mock()
        tool_call_part2.part_kind = "tool-call"
        tool_call_part2.tool_name = "bash"
        tool_call_part2.args = {"command": "echo 'test command'"}
        
        msg_with_tools = Mock()
        msg_with_tools.parts = [tool_call_part1, tool_call_part2]
        
        self.state_manager.session.messages = [msg_with_tools]
        
        nodes = [MockNode(), MockNode()]
        
        mock_agent = MagicMock()
        mock_agent_run = self.create_mock_agent_run(nodes)
        mock_agent_run.result = None
        
        @asynccontextmanager
        async def mock_iter(msg, message_history):
            yield mock_agent_run
        
        mock_agent.iter = mock_iter
        
        with patch('tunacode.core.agents.main.get_or_create_agent', return_value=mock_agent):
            with patch('tunacode.core.agents.main._process_node', new_callable=AsyncMock):
                # Act
                result = await process_request(
                    "openai:gpt-4", message, self.state_manager, AsyncMock()
                )
                
                # Assert - Golden master
                output = result.result.output
                assert "Reached maximum iterations" in output
                assert "Completed 2 iterations (limit: 2)" in output
                assert "Files modified (1):" in output
                assert "/tmp/test1.txt" in output
                assert "Commands executed (1):" in output
                assert "echo 'test command'" in output
                assert "try breaking it into smaller steps" in output
    
    async def test_process_request_fallback_disabled(self):
        """Capture behavior when fallback response is disabled."""
        # Arrange
        self.state_manager.session.user_config["settings"]["max_iterations"] = 2
        self.state_manager.session.user_config["settings"]["fallback_response"] = False
        message = "Test task"
        
        nodes = [MockNode(), MockNode(), MockNode()]
        
        mock_agent = MagicMock()
        mock_agent_run = self.create_mock_agent_run(nodes)
        mock_agent_run.result = None
        
        @asynccontextmanager
        async def mock_iter(msg, message_history):
            yield mock_agent_run
        
        mock_agent.iter = mock_iter
        
        with patch('tunacode.core.agents.main.get_or_create_agent', return_value=mock_agent):
            with patch('tunacode.core.agents.main._process_node', new_callable=AsyncMock):
                # Act
                result = await process_request("openai:gpt-4", message, self.state_manager)
                
                # Assert - Golden master
                assert self.state_manager.session.iteration_count == 2
                assert not hasattr(result.result, 'output')  # No fallback response
                assert hasattr(result, 'response_state')
                assert not result.response_state.has_final_synthesis
    
    async def test_process_request_with_thoughts_enabled(self):
        """Capture behavior with thoughts display enabled."""
        # Arrange
        self.state_manager.session.show_thoughts = True
        message = "Test with thoughts"
        
        # Add some tool calls for summary
        self.state_manager.session.tool_calls = [
            {"tool": "read_file", "args": {}, "iteration": 1},
            {"tool": "bash", "args": {}, "iteration": 1},
            {"tool": "read_file", "args": {}, "iteration": 2}
        ]
        
        nodes = [MockNode(), MockNode()]
        
        mock_agent = MagicMock()
        mock_agent_run = self.create_mock_agent_run(nodes)
        
        @asynccontextmanager
        async def mock_iter(msg, message_history):
            yield mock_agent_run
        
        mock_agent.iter = mock_iter
        
        with patch('tunacode.core.agents.main.get_or_create_agent', return_value=mock_agent):
            with patch('tunacode.core.agents.main._process_node', new_callable=AsyncMock):
                with patch('tunacode.ui.console.muted', new_callable=AsyncMock) as mock_muted:
                    # Act
                    await process_request("openai:gpt-4", message, self.state_manager, AsyncMock())
                    
                    # Assert - Golden master
                    calls = [str(call[0][0]) if call[0] else "" for call in mock_muted.call_args_list]
                    
                    # Should show iteration progress (default is now 40)
                    assert any("ITERATION: 1/40" in call for call in calls)
                    assert any("ITERATION: 2/40" in call for call in calls)
                    
                    # Should show tool summary
                    assert any("TOOLS USED: read_file: 2, bash: 1" in call for call in calls)
    
    async def test_process_request_iteration_tracking(self):
        """Capture behavior of iteration tracking."""
        # Arrange
        message = "Test iteration tracking"
        
        # Track iteration values during processing
        iteration_values = []
        
        async def track_iterations(*args):
            # args = (node, tool_callback, state_manager, tool_buffer)
            sm = args[2] if len(args) > 2 else self.state_manager
            iteration_values.append(sm.session.current_iteration)
        
        nodes = [MockNode(), MockNode(), MockNode()]
        
        mock_agent = MagicMock()
        mock_agent_run = self.create_mock_agent_run(nodes)
        
        @asynccontextmanager
        async def mock_iter(msg, message_history):
            yield mock_agent_run
        
        mock_agent.iter = mock_iter
        
        with patch('tunacode.core.agents.main.get_or_create_agent', return_value=mock_agent):
            with patch('tunacode.core.agents.main._process_node', side_effect=track_iterations):
                # Act
                await process_request("openai:gpt-4", message, self.state_manager)
                
                # Assert - Golden master
                assert self.state_manager.session.iteration_count == 3
                assert iteration_values == [1, 2, 3]  # 1-indexed
    
    async def test_process_request_message_history_copy(self):
        """Capture behavior of message history copying."""
        # Arrange
        message = "Test message"
        original_messages = ["msg1", "msg2"]
        self.state_manager.session.messages = original_messages.copy()
        
        captured_history = None
        
        mock_agent = MagicMock()
        
        @asynccontextmanager
        async def mock_iter(msg, message_history):
            nonlocal captured_history
            captured_history = message_history
            yield self.create_mock_agent_run([])
        
        mock_agent.iter = mock_iter
        
        with patch('tunacode.core.agents.main.get_or_create_agent', return_value=mock_agent):
            # Act
            await process_request("openai:gpt-4", message, self.state_manager)
            
            # Assert - Golden master
            assert captured_history == original_messages
            assert captured_history is not self.state_manager.session.messages  # Different object
    
    async def test_process_request_wrapper_attributes(self):
        """Capture behavior of result wrapper classes."""
        # Arrange
        message = "Test wrapper"
        
        mock_agent = MagicMock()
        mock_agent_run = self.create_mock_agent_run([MockNode()])
        mock_agent_run.custom_attribute = "test_value"
        mock_agent_run.result = MockResult(output="Done")
        
        @asynccontextmanager
        async def mock_iter(msg, message_history):
            yield mock_agent_run
        
        mock_agent.iter = mock_iter
        
        with patch('tunacode.core.agents.main.get_or_create_agent', return_value=mock_agent):
            with patch('tunacode.core.agents.main._process_node', new_callable=AsyncMock):
                # Act
                result = await process_request("openai:gpt-4", message, self.state_manager)
                
                # Assert - Golden master
                # Wrapper should preserve original attributes
                assert hasattr(result, 'response_state')
                assert hasattr(result, 'custom_attribute')
                assert result.custom_attribute == "test_value"
                assert result.result.output == "Done"