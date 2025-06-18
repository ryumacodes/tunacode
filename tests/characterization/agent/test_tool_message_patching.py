"""
Characterization tests for tool message patching functionality.
These tests capture the CURRENT behavior of patch_tool_messages().
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from tunacode.core.agents.main import patch_tool_messages

# No async tests in this file, so no pytestmark needed


class TestToolMessagePatching:
    """Golden-master tests for patch_tool_messages behavior."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.state_manager = Mock()
        self.state_manager.session = Mock()
        self.state_manager.session.messages = []
    
    def test_patch_tool_messages_no_orphans(self):
        """Capture behavior when no orphaned tool calls exist."""
        # Arrange
        # Create a tool call with matching return
        tool_call = Mock()
        tool_call.part_kind = "tool-call"
        tool_call.tool_call_id = "test_123"
        tool_call.tool_name = "read_file"
        
        tool_return = Mock()
        tool_return.part_kind = "tool-return"
        tool_return.tool_call_id = "test_123"
        
        message = Mock()
        message.parts = [tool_call, tool_return]
        
        self.state_manager.session.messages = [message]
        
        # Act
        patch_tool_messages("Error occurred", self.state_manager)
        
        # Assert - Golden master
        # No new messages should be added
        assert len(self.state_manager.session.messages) == 1
    
    def test_patch_tool_messages_with_orphans(self):
        """Capture behavior when orphaned tool calls exist."""
        # Arrange
        # Create orphaned tool calls
        tool_call1 = Mock()
        tool_call1.part_kind = "tool-call"
        tool_call1.tool_call_id = "orphan_1"
        tool_call1.tool_name = "write_file"
        
        tool_call2 = Mock()
        tool_call2.part_kind = "tool-call"
        tool_call2.tool_call_id = "orphan_2"
        tool_call2.tool_name = "bash"
        
        message = Mock()
        message.parts = [tool_call1, tool_call2]
        
        self.state_manager.session.messages = [message]
        
        # Mock the lazy imports
        mock_model_request = MagicMock()
        mock_tool_return_part = MagicMock()
        
        with patch('tunacode.core.agents.main.get_model_messages', 
                  return_value=(mock_model_request, mock_tool_return_part)):
            # Act
            patch_tool_messages("Tool operation failed", self.state_manager)
            
            # Assert - Golden master
            # Two new messages should be added (one for each orphan)
            assert len(self.state_manager.session.messages) == 3
            
            # Verify synthetic returns were created
            assert mock_model_request.call_count == 2
            assert mock_tool_return_part.call_count == 2
            
            # Check first synthetic return
            first_call = mock_tool_return_part.call_args_list[0]
            assert first_call.kwargs['tool_name'] == "write_file"
            assert first_call.kwargs['content'] == "Tool operation failed"
            assert first_call.kwargs['tool_call_id'] == "orphan_1"
            assert first_call.kwargs['part_kind'] == "tool-return"
            
            # Check second synthetic return
            second_call = mock_tool_return_part.call_args_list[1]
            assert second_call.kwargs['tool_name'] == "bash"
            assert second_call.kwargs['tool_call_id'] == "orphan_2"
    
    def test_patch_tool_messages_with_retry_prompts(self):
        """Capture behavior when tool has retry prompt (should be ignored)."""
        # Arrange
        tool_call = Mock()
        tool_call.part_kind = "tool-call"
        tool_call.tool_call_id = "retry_123"
        tool_call.tool_name = "update_file"
        
        retry_prompt = Mock()
        retry_prompt.part_kind = "retry-prompt"
        retry_prompt.tool_call_id = "retry_123"
        
        message = Mock()
        message.parts = [tool_call, retry_prompt]
        
        self.state_manager.session.messages = [message]
        
        # Act
        patch_tool_messages("Error", self.state_manager)
        
        # Assert - Golden master
        # No new messages should be added (tool has retry prompt)
        assert len(self.state_manager.session.messages) == 1
    
    def test_patch_tool_messages_no_state_manager(self):
        """Capture behavior when state_manager is None."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            patch_tool_messages("Error", None)
        
        assert "state_manager is required" in str(exc_info.value)
    
    def test_patch_tool_messages_empty_messages(self):
        """Capture behavior with empty message list."""
        # Arrange
        self.state_manager.session.messages = []
        
        # Act
        patch_tool_messages("Error", self.state_manager)
        
        # Assert - Golden master
        # No messages should be added
        assert len(self.state_manager.session.messages) == 0
    
    def test_patch_tool_messages_mixed_scenario(self):
        """Capture behavior with mix of orphaned, completed, and retry tools."""
        # Arrange
        # Completed tool
        tool_call1 = Mock()
        tool_call1.part_kind = "tool-call"
        tool_call1.tool_call_id = "complete_1"
        tool_call1.tool_name = "read_file"
        
        tool_return1 = Mock()
        tool_return1.part_kind = "tool-return"
        tool_return1.tool_call_id = "complete_1"
        
        # Orphaned tool
        tool_call2 = Mock()
        tool_call2.part_kind = "tool-call"
        tool_call2.tool_call_id = "orphan_1"
        tool_call2.tool_name = "grep"
        
        # Tool with retry
        tool_call3 = Mock()
        tool_call3.part_kind = "tool-call"
        tool_call3.tool_call_id = "retry_1"
        tool_call3.tool_name = "bash"
        
        retry_prompt = Mock()
        retry_prompt.part_kind = "retry-prompt"
        retry_prompt.tool_call_id = "retry_1"
        
        message1 = Mock()
        message1.parts = [tool_call1, tool_return1, tool_call2]
        
        message2 = Mock()
        message2.parts = [tool_call3, retry_prompt]
        
        self.state_manager.session.messages = [message1, message2]
        
        # Mock the lazy imports
        mock_model_request = MagicMock()
        mock_tool_return_part = MagicMock()
        
        with patch('tunacode.core.agents.main.get_model_messages', 
                  return_value=(mock_model_request, mock_tool_return_part)):
            # Act
            patch_tool_messages("Task incomplete", self.state_manager)
            
            # Assert - Golden master
            # Only one new message for the orphaned tool
            assert len(self.state_manager.session.messages) == 3
            
            # Verify only one synthetic return was created
            assert mock_tool_return_part.call_count == 1
            assert mock_tool_return_part.call_args.kwargs['tool_name'] == "grep"
            assert mock_tool_return_part.call_args.kwargs['content'] == "Task incomplete"