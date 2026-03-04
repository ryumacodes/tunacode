"""TunaCode unified logging system.

Usage:
    from tunacode.core.logging import get_logger, LogLevel

    logger = get_logger()
    logger.info("Starting request", request_id="abc123")
    logger.tool("bash", "Executing command", duration_ms=150.5)
"""

from tunacode.core.logging.handlers import FileHandler, Handler, TUIHandler  # noqa: F401
from tunacode.core.logging.levels import LogLevel  # noqa: F401
from tunacode.core.logging.manager import LogManager, get_logger  # noqa: F401
from tunacode.core.logging.records import LogRecord  # noqa: F401
