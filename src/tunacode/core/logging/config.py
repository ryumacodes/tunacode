import logging
import logging.config

from tunacode.utils import user_configuration

# Default logging configuration when none is provided
DEFAULT_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[%(levelname)s] %(message)s"},
        "detailed": {"format": "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"},
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "tunacode.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        }
    },
    "root": {"level": "DEBUG", "handlers": ["file"]},
    "loggers": {
        "tunacode.ui": {"level": "INFO", "propagate": False},
        "tunacode.tools": {"level": "DEBUG"},
        "tunacode.core.agents": {"level": "DEBUG"},
    },
}


class LogConfig:
    @staticmethod
    def load(_config_path=None):
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
            # Use default configuration
            try:
                logging.config.dictConfig(DEFAULT_LOGGING_CONFIG)
            except Exception as e:
                print(f"Failed to configure default logging: {e}")
                logging.basicConfig(level=logging.INFO)
