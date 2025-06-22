"""Test configuration directory creation and error handling."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tunacode.core.state import StateManager
from tunacode.exceptions import ConfigurationError
from tunacode.utils import user_configuration


@pytest.fixture
def state_manager():
    """Create a mock state manager with session data."""
    manager = MagicMock(spec=StateManager)
    manager.session = MagicMock()
    manager.session.user_config = {"default_model": "test:model", "env": {"TEST_API_KEY": "key"}}
    return manager


def test_save_config_creates_directory_if_missing(state_manager):
    """Test that save_config creates the .config directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config_dir = tmp_path / ".config"
        config_file = config_dir / "tunacode.json"
        
        # Patch the ApplicationSettings to use our temp directory
        with patch("tunacode.utils.user_configuration.ApplicationSettings") as mock_settings:
            mock_settings.return_value.paths.config_dir = config_dir
            mock_settings.return_value.paths.config_file = config_file
            
            # Directory should not exist initially
            assert not config_dir.exists()
            
            # Save config
            result = user_configuration.save_config(state_manager)
            
            # Should succeed
            assert result is True
            
            # Directory should now exist with correct permissions
            assert config_dir.exists()
            assert config_dir.is_dir()
            # Check permissions (0o700 = rwx------)
            assert oct(config_dir.stat().st_mode)[-3:] == "700"
            
            # Config file should exist with correct content
            assert config_file.exists()
            with open(config_file) as f:
                saved_config = json.load(f)
            assert saved_config == state_manager.session.user_config


def test_save_config_permission_error(state_manager):
    """Test that save_config raises ConfigurationError on permission denied."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config_dir = tmp_path / ".config"
        config_file = config_dir / "tunacode.json"
        
        # Create directory with no write permission
        config_dir.mkdir(mode=0o500)  # r-x------
        
        with patch("tunacode.utils.user_configuration.ApplicationSettings") as mock_settings:
            mock_settings.return_value.paths.config_dir = config_dir
            mock_settings.return_value.paths.config_file = config_file
            
            # Should raise ConfigurationError with permission message
            with pytest.raises(ConfigurationError) as exc_info:
                user_configuration.save_config(state_manager)
            
            assert "Permission denied" in str(exc_info.value)
            assert str(config_file) in str(exc_info.value)


def test_save_config_os_error(state_manager):
    """Test that save_config raises ConfigurationError on OS errors."""
    with patch("tunacode.utils.user_configuration.ApplicationSettings") as mock_settings:
        # Use an invalid path that will cause OSError
        mock_settings.return_value.paths.config_dir = Path("/dev/null/invalid")
        mock_settings.return_value.paths.config_file = Path("/dev/null/invalid/tunacode.json")
        
        # Should raise ConfigurationError with OS error message
        with pytest.raises(ConfigurationError) as exc_info:
            user_configuration.save_config(state_manager)
        
        assert "Failed to save configuration" in str(exc_info.value)


def test_set_default_model_propagates_errors(state_manager):
    """Test that set_default_model propagates ConfigurationError."""
    with patch("tunacode.utils.user_configuration.save_config") as mock_save:
        mock_save.side_effect = ConfigurationError("Test error")
        
        # Should re-raise the ConfigurationError
        with pytest.raises(ConfigurationError) as exc_info:
            user_configuration.set_default_model("new:model", state_manager)
        
        assert "Test error" in str(exc_info.value)
        # Model should still be updated in memory
        assert state_manager.session.user_config["default_model"] == "new:model"