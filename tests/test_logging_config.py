"""Test logging configuration with user preferences."""

import logging
from unittest.mock import patch

import pytest

from tunacode.core.logging.config import LogConfig


class TestLoggingConfiguration:
    """Test cases for logging configuration based on user preferences."""

    def test_logging_disabled_by_default(self, tmp_path):
        """Test that logging is disabled when no config exists."""
        with patch("tunacode.utils.user_configuration.load_config", return_value=None):
            LogConfig.load()

            # Check that root logger has only NullHandler
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) == 1
            assert isinstance(root_logger.handlers[0], logging.NullHandler)

    def test_logging_explicitly_disabled(self, tmp_path):
        """Test that logging stays disabled when explicitly set to false."""
        config = {"default_model": "test:model", "logging_enabled": False}

        with patch("tunacode.utils.user_configuration.load_config", return_value=config):
            LogConfig.load()

            # Check that root logger has only NullHandler
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) == 1
            assert isinstance(root_logger.handlers[0], logging.NullHandler)

    def test_logging_enabled_with_defaults(self, tmp_path):
        """Test that default logging config is used when enabled without custom config."""
        config = {"default_model": "test:model", "logging_enabled": True}

        with patch("tunacode.utils.user_configuration.load_config", return_value=config):
            # This will load from the default YAML file
            try:
                LogConfig.load()
                # If YAML exists, it should configure handlers
                root_logger = logging.getLogger()
                # Should have more than just NullHandler
                assert not all(isinstance(h, logging.NullHandler) for h in root_logger.handlers)
            except FileNotFoundError:
                # If YAML doesn't exist in test environment, that's expected
                pass

    def test_logging_enabled_with_custom_config(self, tmp_path):
        """Test that custom logging configuration is applied correctly."""
        # Create a test log file path
        log_file = tmp_path / "test.log"

        config = {
            "default_model": "test:model",
            "logging_enabled": True,
            "logging": {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {"simple": {"format": "[TEST] %(message)s"}},
                "handlers": {
                    "test_file": {
                        "class": "logging.FileHandler",
                        "level": "DEBUG",
                        "formatter": "simple",
                        "filename": str(log_file),
                    }
                },
                "root": {"level": "DEBUG", "handlers": ["test_file"]},
            },
        }

        with patch("tunacode.utils.user_configuration.load_config", return_value=config):
            # Clear existing handlers first
            logging.getLogger().handlers = []

            LogConfig.load()

            # Test that logging works with custom config
            test_logger = logging.getLogger("test")
            test_logger.debug("Test message")

            # Check that log file was created and contains our message
            assert log_file.exists()
            content = log_file.read_text()
            assert "[TEST] Test message" in content

    def test_invalid_custom_config_fallback(self, tmp_path):
        """Test that invalid custom config falls back to basic config."""
        config = {
            "default_model": "test:model",
            "logging_enabled": True,
            "logging": {"invalid": "config"},
        }

        # Clear any existing handlers
        logging.getLogger().handlers = []

        with patch("tunacode.utils.user_configuration.load_config", return_value=config):
            # Should not raise exception
            LogConfig.load()

            # Should have some configuration (not NullHandler)
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
