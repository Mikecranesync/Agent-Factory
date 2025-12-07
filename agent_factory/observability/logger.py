"""
logger.py - Structured JSON logging for Agent Factory

Phase 5 Enhancement: Production-grade structured logging with JSON output,
context propagation, and log aggregation support.

Features:
- JSON-formatted logs for easy parsing
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Contextual logging (trace_id, user_id, agent_name)
- Structured fields for filtering
- Compatible with log aggregation tools (ELK, Splunk, Datadog)
"""

import json
import logging
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pathlib import Path


class LogLevel(str, Enum):
    """Log severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """
    Structured JSON logger for production observability.

    Outputs JSON-formatted logs with structured fields for easy parsing
    and aggregation in production environments.

    Usage:
        logger = StructuredLogger("agent_factory")
        logger.info("Request started", trace_id="abc123", user_id="user1")
        logger.error("Request failed", error=str(e), trace_id="abc123")

    Example Output:
        {
            "timestamp": "2025-12-07T22:30:00.123456",
            "level": "INFO",
            "logger": "agent_factory",
            "message": "Request started",
            "trace_id": "abc123",
            "user_id": "user1"
        }
    """

    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        output_file: Optional[Path] = None,
        include_timestamp: bool = True,
        include_hostname: bool = False
    ):
        """
        Initialize structured logger.

        Args:
            name: Logger name (e.g., "agent_factory")
            level: Minimum log level to output
            output_file: Optional file path for log output
            include_timestamp: Include ISO timestamp in logs
            include_hostname: Include hostname in logs
        """
        self.name = name
        self.level = level
        self.output_file = output_file
        self.include_timestamp = include_timestamp
        self.include_hostname = include_hostname

        # Create Python logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.value))
        self._logger.propagate = False

        # Clear existing handlers
        self._logger.handlers = []

        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        self._logger.addHandler(console_handler)

        # Add file handler if specified
        if output_file:
            file_handler = logging.FileHandler(output_file)
            file_handler.setFormatter(logging.Formatter('%(message)s'))
            self._logger.addHandler(file_handler)

    def _format_log(
        self,
        level: LogLevel,
        message: str,
        **kwargs: Any
    ) -> str:
        """
        Format log entry as JSON.

        Args:
            level: Log level
            message: Log message
            **kwargs: Additional structured fields

        Returns:
            JSON-formatted log string
        """
        log_entry: Dict[str, Any] = {
            "level": level.value,
            "logger": self.name,
            "message": message
        }

        # Add timestamp
        if self.include_timestamp:
            log_entry["timestamp"] = datetime.utcnow().isoformat()

        # Add hostname
        if self.include_hostname:
            import socket
            log_entry["hostname"] = socket.gethostname()

        # Add all additional fields
        log_entry.update(kwargs)

        return json.dumps(log_entry)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log DEBUG level message."""
        if self._should_log(LogLevel.DEBUG):
            log_str = self._format_log(LogLevel.DEBUG, message, **kwargs)
            self._logger.debug(log_str)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log INFO level message."""
        if self._should_log(LogLevel.INFO):
            log_str = self._format_log(LogLevel.INFO, message, **kwargs)
            self._logger.info(log_str)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log WARNING level message."""
        if self._should_log(LogLevel.WARNING):
            log_str = self._format_log(LogLevel.WARNING, message, **kwargs)
            self._logger.warning(log_str)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log ERROR level message."""
        if self._should_log(LogLevel.ERROR):
            log_str = self._format_log(LogLevel.ERROR, message, **kwargs)
            self._logger.error(log_str)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log CRITICAL level message."""
        if self._should_log(LogLevel.CRITICAL):
            log_str = self._format_log(LogLevel.CRITICAL, message, **kwargs)
            self._logger.critical(log_str)

    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged based on level."""
        level_hierarchy = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        return level_hierarchy[level] >= level_hierarchy[self.level]

    def set_level(self, level: LogLevel) -> None:
        """Change minimum log level."""
        self.level = level
        self._logger.setLevel(getattr(logging, level.value))

    def with_context(self, **kwargs: Any) -> 'LoggerContext':
        """
        Create a logger context with default fields.

        Usage:
            with logger.with_context(trace_id="abc123") as ctx_logger:
                ctx_logger.info("Starting")  # Includes trace_id automatically

        Args:
            **kwargs: Default context fields

        Returns:
            LoggerContext with bound fields
        """
        return LoggerContext(self, kwargs)


class LoggerContext:
    """
    Context manager for logger with bound fields.

    Automatically includes context fields in all log messages.
    """

    def __init__(self, logger: StructuredLogger, context: Dict[str, Any]):
        """
        Initialize logger context.

        Args:
            logger: Parent logger
            context: Context fields to bind
        """
        self.logger = logger
        self.context = context

    def __enter__(self) -> 'LoggerContext':
        """Enter context."""
        return self

    def __exit__(self, *args) -> None:
        """Exit context."""
        pass

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log DEBUG with context."""
        self.logger.debug(message, **{**self.context, **kwargs})

    def info(self, message: str, **kwargs: Any) -> None:
        """Log INFO with context."""
        self.logger.info(message, **{**self.context, **kwargs})

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log WARNING with context."""
        self.logger.warning(message, **{**self.context, **kwargs})

    def error(self, message: str, **kwargs: Any) -> None:
        """Log ERROR with context."""
        self.logger.error(message, **{**self.context, **kwargs})

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log CRITICAL with context."""
        self.logger.critical(message, **{**self.context, **kwargs})


# Global logger instance
_global_logger: Optional[StructuredLogger] = None


def get_logger(
    name: str = "agent_factory",
    level: LogLevel = LogLevel.INFO
) -> StructuredLogger:
    """
    Get or create global logger instance.

    Args:
        name: Logger name
        level: Minimum log level

    Returns:
        StructuredLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = StructuredLogger(name, level)
    return _global_logger


def set_global_logger(logger: StructuredLogger) -> None:
    """
    Set global logger instance.

    Args:
        logger: StructuredLogger to use globally
    """
    global _global_logger
    _global_logger = logger
