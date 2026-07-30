import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any


class JSONLogFormatter(logging.Formatter):
    """
    Structured JSON log formatter for production and staging observability (`Sub-phase 5.4`).
    Ensures every log record contains timestamp, log level, logger name, correlation/request ID, and message.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }

        # Include correlation/request ID if attached to extra/context
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def configure_structured_logging(level: int = logging.INFO):
    """
    Configures root and application loggers to emit structured JSON logs.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONLogFormatter())
    root_logger.addHandler(console_handler)

    # Suppress verbose external library logs unless WARN/ERROR
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
