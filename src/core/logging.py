# src/core/logging.py
"""Structured logging configuration for Kubernetes environments."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging in Kubernetes."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra"):
            log_entry["extra"] = record.extra

        # Add custom fields from record
        for key in ["request_id", "user_id", "tool_name", "ticker", "query", "duration_ms"]:
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class DevFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        msg = f"{color}[{timestamp}] {record.levelname:8}{reset} | {record.name} | {record.getMessage()}"

        if record.exc_info:
            msg += f"\n{self.formatException(record.exc_info)}"

        return msg


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    app_name: str = "financial-agent",
) -> logging.Logger:
    """
    Setup structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON format (True for K8s, False for dev)
        app_name: Application name for the root logger

    Returns:
        Configured root logger
    """
    # Remove existing handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # Choose formatter based on environment
    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(DevFormatter())

    # Configure root logger
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper()))

    # Set levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Create app logger
    logger = logging.getLogger(app_name)
    logger.info("Logging configured", extra={"format": "json" if json_format else "dev", "level": level})

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(f"financial-agent.{name}")
