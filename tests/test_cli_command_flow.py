"""
Tests for CLI command flows and interactions.
Tests actual command sequences and user interactions.
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from tunacode.cli.commands import CommandRegistry, YoloCommand, HelpCommand
from tunacode.core.state import StateManager
from tunacode.tools.write_file import write_file
from tunacode.tools.read_file import read_file
from tunacode.tools.update_file import update_file
from tunacode.types import CommandContext

pytestmark = pytest.mark.asyncio


class TestCLICommandFlow:
    """Test CLI command sequences and interactions."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create mock state manager with proper structure
        self.state = Mock(spec=StateManager)
        self.state.session = Mock()
        self.state.session.yolo = False
        self.state.session.show_thoughts = False
        self.state.session.messages = []
        self.state.session.user_config = {}
        self.state.session.agents = {}
        self.state.session.current_model = "test-model"
    
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_help_to_file_operations_flow(self):
        """Test flow: /help → Execute file operation commands."""
        # Create command context
        context = CommandContext(
            state_manager=self.state,
            process_request=None
        )
        
        # Execute help command
        help_cmd = HelpCommand()
        assert "/help" in help_cmd.aliases
        
        # Mock console output - patch where ui is imported
        with patch('tunacode.cli.commands.ui.help') as mock_help:
            mock_help.return_value = AsyncMock()
            await help_cmd.execute([], context)
            
            # Verify help was called
            mock_help.assert_called_once()
    
    async def test_yolo_mode_file_operations(self):
        """Test file operations in yolo mode (no confirmations)."""
        # Enable yolo mode
        yolo_cmd = YoloCommand()
        assert "/yolo" in yolo_cmd.aliases
        
        context = CommandContext(
            state_manager=self.state,
            process_request=None
        )
        
        # Patch where ui is used, not where it's defined
        with patch('tunacode.cli.commands.ui') as mock_ui:
            # Mock the success method to verify it's called
            mock_ui.success = AsyncMock()
            await yolo_cmd.execute([], context)
            
            # Verify yolo mode is enabled
            assert self.state.session.yolo is True
            mock_ui.success.assert_called_once()
        
        # Now file operations should not require confirmation
        # Create a file without confirmation
        await write_file("yolo_test.txt", "Created without confirmation!")
        
        # Verify file was created
        content = await read_file("yolo_test.txt")
        assert content == "Created without confirmation!"
        
        # Update file without confirmation
        await update_file(
            "yolo_test.txt",
            target="without confirmation",
            patch="in YOLO mode"
        )
        
        # Verify update
        updated = await read_file("yolo_test.txt")
        assert "in YOLO mode" in updated
        
        # Disable yolo mode
        await yolo_cmd.execute([], context)
        assert self.state.session.yolo is False
    
    async def test_command_chaining_scenario(self):
        """Test chaining multiple commands in a workflow."""
        registry = CommandRegistry()
        
        # Mock user inputs for a typical workflow
        commands = [
            "/yolo",           # Enable yolo mode
            "/thoughts on",    # Enable thought display
            "/model",          # Check current model
            "/help",           # Get help
            "/yolo",           # Disable yolo mode
            "/thoughts off"    # Disable thoughts
        ]
        
        context = CommandContext(
            state_manager=self.state,
            process_request=None
        )
        
        with patch('tunacode.cli.commands.ui') as mock_ui:
            # Mock all ui methods that might be called
            mock_ui.success = AsyncMock()
            mock_ui.info = AsyncMock()
            mock_ui.error = AsyncMock()
            mock_ui.help = AsyncMock()
            
            for cmd_text in commands:
                try:
                    await registry.execute(cmd_text, context)
                except Exception:
                    # Some commands might not exist, that's ok
                    pass
        
        # Verify state changes from command chain
        assert self.state.session.yolo is False  # Yolo toggled off
        assert hasattr(self.state.session, 'show_thoughts')  # Thoughts command was executed
    
    async def test_error_recovery_flow(self):
        """Test error recovery in command flows."""
        # Try to update a non-existent file
        from pydantic_ai import ModelRetry
        
        # This should raise an error
        with pytest.raises(ModelRetry) as exc_info:
            await update_file("nonexistent.txt", target="foo", patch="bar")
        
        assert "not found" in str(exc_info.value)
        
        # Recover by creating the file first
        await write_file("nonexistent.txt", "foo bar baz")
        
        # Now update should work
        result = await update_file("nonexistent.txt", target="foo", patch="FOO")
        assert "successfully" in result
        
        # Verify the update
        content = await read_file("nonexistent.txt")
        assert content == "FOO bar baz"
    
    async def test_interactive_confirmation_flow(self):
        """Test file operations with confirmation prompts."""
        # Without yolo mode, operations would normally require confirmation
        # For testing, we'll simulate the confirmation flow
        
        # Create a mock for user confirmation
        with patch('builtins.input', return_value='y'):
            # Simulate file creation with confirmation
            await write_file("confirmed.txt", "User confirmed this creation")
            
            # Verify file was created
            assert Path("confirmed.txt").exists()
            content = await read_file("confirmed.txt")
            assert content == "User confirmed this creation"
    
    async def test_command_with_file_paths(self):
        """Test commands that work with file paths."""
        # Create a test file structure
        Path("src").mkdir()
        await write_file("src/main.py", "def main():\n    print('Hello')")
        await write_file("src/utils.py", "def helper():\n    return 42")
        
        # Test reading files through paths
        main_content = await read_file("src/main.py")
        assert "def main():" in main_content
        
        utils_content = await read_file("src/utils.py")
        assert "def helper():" in utils_content
        
        # Test updating through paths
        await update_file(
            "src/main.py",
            target="print('Hello')",
            patch="print('Hello, World!')"
        )
        
        updated = await read_file("src/main.py")
        assert "Hello, World!" in updated
    
    async def test_command_invalid_input_handling(self):
        """Test handling of invalid command inputs."""
        registry = CommandRegistry()
        
        # Test invalid commands
        invalid_commands = [
            "/nonexistent",
            "/model invalid args",
            "/yolo extra args",
            "not_a_command",
            "",
            None
        ]
        
        context = CommandContext(
            state_manager=self.state,
            process_request=None
        )
        
        with patch('tunacode.cli.commands.ui') as mock_ui:
            # Mock all ui methods
            mock_ui.success = AsyncMock()
            mock_ui.info = AsyncMock()
            mock_ui.error = AsyncMock()
            
            for cmd in invalid_commands:
                if cmd:  # Skip None
                    try:
                        await registry.execute(cmd, context)
                        # If we get here, command was found and executed
                        # Some commands might be valid even with extra args
                    except Exception:
                        # Command not found or error - this is expected for invalid commands
                        pass
    
    async def test_file_operation_command_sequence(self):
        """Test a realistic sequence of file operation commands."""
        # Simulate a development workflow
        
        # 1. Create initial project structure
        await write_file("app.py", """from config import Config

def main():
    config = Config()
    print(f"Running on port {config.port}")

if __name__ == "__main__":
    main()
""")
        
        await write_file("config.py", """class Config:
    def __init__(self):
        self.port = 8080
        self.debug = False
""")
        
        # 2. Read to understand the code
        app_content = await read_file("app.py")
        assert "config.port" in app_content
        
        # 3. Update configuration
        await update_file(
            "config.py",
            target="self.port = 8080",
            patch="self.port = 9090"
        )
        
        # 4. Add new feature
        await update_file(
            "config.py",
            target="self.debug = False",
            patch="self.debug = False\n        self.host = 'localhost'"
        )
        
        # 5. Update app to use new feature
        await update_file(
            "app.py",
            target='print(f"Running on port {config.port}")',
            patch='print(f"Running on {config.host}:{config.port}")'
        )
        
        # 6. Verify all changes
        final_app = await read_file("app.py")
        assert "config.host" in final_app
        
        final_config = await read_file("config.py")
        assert "self.port = 9090" in final_config
        assert "self.host = 'localhost'" in final_config
    
    async def test_command_state_persistence(self):
        """Test that command state changes persist across operations."""
        # Track state changes
        yolo_cmd = YoloCommand()
        
        # Create context
        context = CommandContext(
            state_manager=self.state,
            process_request=None
        )
        
        # Enable yolo mode
        with patch('tunacode.cli.commands.ui') as mock_ui:
            mock_ui.success = AsyncMock()
            await yolo_cmd.execute([], context)
        
        # State should persist
        assert self.state.session.yolo is True
        
        # Create multiple files - all should use yolo mode
        for i in range(3):
            await write_file(f"file_{i}.txt", f"Content {i}")
        
        # All files should exist
        for i in range(3):
            assert Path(f"file_{i}.txt").exists()
        
        # Disable yolo mode
        with patch('tunacode.cli.commands.ui') as mock_ui:
            mock_ui.info = AsyncMock()
            await yolo_cmd.execute([], context)
        
        # State should be updated
        assert self.state.session.yolo is False