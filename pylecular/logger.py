"""Logging configuration and utilities for the Pylecular framework.

This module provides structured logging capabilities using structlog, with support
for both JSON and plain text formatting compatible with Moleculer.js conventions.
"""

import datetime
import logging
import sys
from typing import Any, Dict, Union

import structlog

# Map string log levels to logging constants
LOG_LEVEL_MAP: Dict[str, int] = {
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def get_parsed_log_level(log_level: str) -> int:
    """Parse a string log level and return the corresponding logging constant.

    Args:
        log_level: String representation of log level (e.g., "INFO", "DEBUG")

    Returns:
        The corresponding logging level constant, defaults to INFO if not found
    """
    return LOG_LEVEL_MAP.get(log_level.upper(), logging.INFO)


def moleculer_format_renderer(_logger: Any, _method_name: str, event_dict: Dict[str, Any]) -> str:
    """Custom log formatter that renders logs in Moleculer.js compatible format.

    Args:
        _logger: The logger instance (unused but required by structlog)
        _method_name: The log method name (unused but required by structlog)
        event_dict: Dictionary containing log event data

    Returns:
        Formatted log string in Moleculer format
    """
    # Get current time and format it
    now = datetime.datetime.now(datetime.UTC)
    timestamp = now.isoformat(timespec="milliseconds") + "Z"
    level = event_dict.pop("level", "INFO").upper()
    node = event_dict.pop("node", "<unknown>")
    service = event_dict.pop("service", "<unspecified>")
    message = event_dict.pop("event", "")
    return f"[{timestamp}] {level:<5} {node}/{service}: {message}"


def get_logger(log_level: Union[str, int], log_format: str = "PLAIN"):
    """Configure and return a structured logger instance.

    Args:
        log_level: Log level as string (e.g., "INFO") or logging constant
        log_format: Output format, either "JSON" or "PLAIN" (default)

    Returns:
        Configured structlog BoundLogger instance
    """
    if isinstance(log_level, str):
        parsed_level = get_parsed_log_level(log_level)
    else:
        parsed_level = log_level

    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=parsed_level)

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
    ]

    if log_format == "JSON":
        processors.extend(
            [
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ]
        )
    else:
        processors.append(moleculer_format_renderer)

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(parsed_level),
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()
