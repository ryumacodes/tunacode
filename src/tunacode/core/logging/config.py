import logging
import logging.config
import os

import yaml

from tunacode.utils import user_configuration

DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "logging.yaml"
)


class LogConfig:
    @staticmethod
    def load(config_path=None):
        """
        Load logging configuration based on user preferences.
        If logging is disabled (default), use minimal configuration.
        """
        # First check if user has enabled logging
        user_config = user_configuration.load_config()
        logging_enabled = False
        custom_logging_config = None

        if user_config:
            logging_enabled = user_config.get("logging_enabled", False)
            custom_logging_config = user_config.get("logging", None)

        if not logging_enabled:
            # Configure minimal logging - only critical errors to console
            logging.basicConfig(level=logging.CRITICAL, handlers=[logging.NullHandler()])
            # Ensure no file handlers are created
            logging.getLogger().handlers = [logging.NullHandler()]
            return

        # Logging is enabled, load configuration
        if custom_logging_config:
            # Use user's custom logging configuration
            try:
                logging.config.dictConfig(custom_logging_config)
            except Exception as e:
                print(f"Failed to configure custom logging: {e}")
                logging.basicConfig(level=logging.INFO)
        else:
            # Use default configuration from YAML file
            path = config_path or DEFAULT_CONFIG_PATH
            if not os.path.exists(path):
                raise FileNotFoundError(f"Logging config file not found: {path}")
            with open(path, "r") as f:
                config = yaml.safe_load(f)
            logging_config = config.get("logging", config)
            try:
                logging.config.dictConfig(logging_config)
            except Exception as e:
                print(f"Failed to configure logging: {e}")
                logging.basicConfig(level=logging.INFO)
