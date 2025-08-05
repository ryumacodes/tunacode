import json
import logging

from rich.console import Console
from rich.text import Text

# Global context for streaming state
_streaming_context = {"just_finished": False}


class RichHandler(logging.Handler):
    """
    Handler that outputs logs to the console using rich formatting.
    """

    level_icons = {
        "INFO": "",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🚨",
        "THOUGHT": "🤔",
        "DEBUG": "",
    }

    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.console = Console()

    def _safe_str(self, value):
        """Coerce any value to a safe string representation."""
        try:
            if value is None:
                return ""
            return str(value)
        except Exception:
            return ""

    def emit(self, record):
        try:
            # Defensive normalization of record fields to avoid None propagation
            record.levelname = self._safe_str(getattr(record, "levelname", "INFO")) or "INFO"
            icon = self.level_icons.get(record.levelname, "")
            timestamp = self.formatTime(record)

            # Ensure message formatting never returns None
            msg = self.format(record)
            if msg is None:
                msg = ""

            msg = self._safe_str(msg)

            if icon:
                output = f"[{timestamp}] {icon} {msg}"
            else:
                output = f"[{timestamp}] {msg}"

            # Check if we just finished streaming to avoid extra newlines
            just_finished_streaming = _streaming_context.get("just_finished", False)
            if just_finished_streaming:
                _streaming_context["just_finished"] = False  # Reset after use
                # Don't add extra newline when transitioning from streaming
                self.console.print(Text(self._safe_str(output)), end="\n")
            else:
                self.console.print(Text(self._safe_str(output)))
        except Exception:
            self.handleError(record)

    def formatTime(self, record, datefmt=None):
        from datetime import datetime

        ct = datetime.fromtimestamp(record.created)
        if datefmt:
            return ct.strftime(datefmt)
        return ct.strftime("%Y-%m-%d %H:%M:%S")


class StructuredFileHandler(logging.FileHandler):
    """
    Handler that outputs logs as structured JSON lines.
    """

    def _coerce_json_safe(self, value):
        """Ensure values are JSON-serializable and not None."""
        if value is None:
            return ""
        try:
            json.dumps(value)
            return value
        except Exception:
            try:
                return str(value)
            except Exception:
                return ""

    def emit(self, record):
        try:
            # Normalize fields to avoid None values in JSON
            log_entry = {
                "timestamp": self.formatTime(record),
                "level": self._coerce_json_safe(getattr(record, "levelname", "")),
                "name": self._coerce_json_safe(getattr(record, "name", "")),
                "line": int(getattr(record, "lineno", 0) or 0),
                "message": self._coerce_json_safe(
                    record.getMessage() if hasattr(record, "getMessage") else ""
                ),
                "extra_data": self._coerce_json_safe(getattr(record, "extra", {})),
            }
            self.stream.write(json.dumps(log_entry) + "\n")
            self.flush()
        except Exception:
            self.handleError(record)

    def formatTime(self, record, datefmt=None):
        from datetime import datetime, timezone

        ct = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return ct.isoformat()
