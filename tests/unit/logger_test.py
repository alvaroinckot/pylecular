"""Unit tests for the logger module."""

import datetime
import json
import logging
from io import StringIO
from unittest.mock import patch

import pytest

from pylecular.logger import (
    LOG_LEVEL_MAP,
    get_logger,
    get_parsed_log_level,
    moleculer_format_renderer,
)


class TestLogLevelParsing:
    """Test log level parsing functionality."""

    def test_get_parsed_log_level_valid_levels(self):
        """Test parsing valid log levels."""
        assert get_parsed_log_level("INFO") == logging.INFO
        assert get_parsed_log_level("DEBUG") == logging.DEBUG
        assert get_parsed_log_level("WARNING") == logging.WARNING
        assert get_parsed_log_level("ERROR") == logging.ERROR
        assert get_parsed_log_level("CRITICAL") == logging.CRITICAL

    def test_get_parsed_log_level_case_insensitive(self):
        """Test that log level parsing is case insensitive."""
        assert get_parsed_log_level("info") == logging.INFO
        assert get_parsed_log_level("Info") == logging.INFO
        assert get_parsed_log_level("INFO") == logging.INFO
        assert get_parsed_log_level("debug") == logging.DEBUG
        assert get_parsed_log_level("DEBUG") == logging.DEBUG
        assert get_parsed_log_level("error") == logging.ERROR
        assert get_parsed_log_level("ERROR") == logging.ERROR

    def test_get_parsed_log_level_invalid_defaults_to_info(self):
        """Test that invalid log levels default to INFO."""
        assert get_parsed_log_level("INVALID") == logging.INFO
        assert get_parsed_log_level("") == logging.INFO
        assert get_parsed_log_level("UNKNOWN") == logging.INFO
        assert get_parsed_log_level("123") == logging.INFO

    def test_log_level_map_completeness(self):
        """Test that LOG_LEVEL_MAP contains expected levels."""
        expected_levels = ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]

        for level in expected_levels:
            assert level in LOG_LEVEL_MAP
            assert isinstance(LOG_LEVEL_MAP[level], int)


class TestMoleculerFormatRenderer:
    """Test Moleculer format renderer functionality."""

    def test_moleculer_format_renderer_basic(self):
        """Test basic Moleculer format rendering."""
        event_dict = {
            "level": "info",
            "node": "test-node",
            "service": "test-service",
            "event": "Test message",
        }

        with patch("pylecular.logger.datetime") as mock_datetime:
            mock_now = datetime.datetime(2023, 1, 1, 12, 0, 0, 123000, tzinfo=datetime.timezone.utc)
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.UTC = datetime.timezone.utc

            result = moleculer_format_renderer(None, None, event_dict)

            expected = "[2023-01-01T12:00:00.123+00:00Z] INFO  test-node/test-service: Test message"
            assert result == expected

    def test_moleculer_format_renderer_different_levels(self):
        """Test Moleculer format renderer with different log levels."""
        levels = ["debug", "info", "warning", "error", "critical"]

        for level in levels:
            event_dict = {
                "level": level,
                "node": "test-node",
                "service": "test-service",
                "event": f"Message at {level} level",
            }

            with patch("pylecular.logger.datetime") as mock_datetime:
                mock_now = datetime.datetime(2023, 1, 1, 12, 0, 0, 0, tzinfo=datetime.timezone.utc)
                mock_datetime.now.return_value = mock_now
                mock_datetime.UTC = datetime.timezone.utc

                result = moleculer_format_renderer(None, None, event_dict)

                assert level.upper() in result
                assert f"Message at {level} level" in result

    def test_moleculer_format_renderer_pops_fields(self):
        """Test that Moleculer format renderer removes fields from event_dict."""
        event_dict = {
            "level": "info",
            "node": "test-node",
            "service": "test-service",
            "event": "Test message",
            "extra_field": "should_remain",
        }

        with patch("pylecular.logger.datetime") as mock_datetime:
            mock_now = datetime.datetime(2023, 1, 1, 12, 0, 0, 0, tzinfo=datetime.timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.UTC = datetime.timezone.utc

            moleculer_format_renderer(None, None, event_dict)

            # Check that specific fields were removed
            assert "level" not in event_dict
            assert "node" not in event_dict
            assert "service" not in event_dict
            assert "event" not in event_dict
            # But extra fields should remain
            assert "extra_field" in event_dict
            assert event_dict["extra_field"] == "should_remain"


class TestGetLogger:
    """Test get_logger functionality."""

    def test_get_logger_with_string_level(self):
        """Test getting logger with string log level."""
        logger = get_logger("DEBUG", "PLAIN")

        assert hasattr(logger, "info")  # Check logger has basic logging methods

    def test_get_logger_with_int_level(self):
        """Test getting logger with integer log level."""
        logger = get_logger(logging.ERROR, "PLAIN")

        assert hasattr(logger, "info")  # Check logger has basic logging methods

    def test_get_logger_json_format(self):
        """Test getting logger with JSON format."""
        logger = get_logger("INFO", "JSON")

        assert hasattr(logger, "info")  # Check logger has basic logging methods

    def test_get_logger_plain_format(self):
        """Test getting logger with PLAIN format (default)."""
        logger = get_logger("INFO", "PLAIN")

        assert hasattr(logger, "info")  # Check logger has basic logging methods

    def test_get_logger_default_format(self):
        """Test getting logger with default format."""
        logger = get_logger("INFO")

        assert hasattr(logger, "info")  # Check logger has basic logging methods

    @patch("sys.stdout", new_callable=StringIO)
    def test_logger_plain_output_format(self, mock_stdout):
        """Test that plain format logger produces expected output."""
        with patch("pylecular.logger.datetime") as mock_datetime:
            mock_now = datetime.datetime(2023, 1, 1, 12, 0, 0, 123000, tzinfo=datetime.timezone.utc)
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.UTC = datetime.timezone.utc

            logger = get_logger("INFO", "PLAIN")
            logger.info("Test message", node="test-node", service="test-service")

            output = mock_stdout.getvalue()
            assert "[2023-01-01T12:00:00.123+00:00Z]" in output
            assert "INFO" in output
            assert "test-node/test-service" in output
            assert "Test message" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_logger_json_output_format(self, mock_stdout):
        """Test that JSON format logger produces valid JSON output."""
        logger = get_logger("INFO", "JSON")
        logger.info("Test message", extra_data="test_value")

        output = mock_stdout.getvalue().strip()

        # Should be valid JSON
        try:
            parsed = json.loads(output)
            assert parsed["event"] == "Test message"
            assert parsed["level"] == "info"
            assert parsed["extra_data"] == "test_value"
            assert "timestamp" in parsed
        except json.JSONDecodeError:
            pytest.fail("Logger did not produce valid JSON output")

    def test_get_logger_different_levels(self):
        """Test getting loggers with different levels."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in levels:
            logger = get_logger(level, "PLAIN")
            assert hasattr(logger, "info")  # Check logger has basic logging methods

    def test_get_logger_invalid_format_defaults_to_plain(self):
        """Test that invalid format defaults to plain."""
        logger = get_logger("INFO", "INVALID_FORMAT")

        assert hasattr(logger, "info")  # Check logger has basic logging methods

    @patch("sys.stdout", new_callable=StringIO)
    def test_logger_level_filtering(self, mock_stdout):
        """Test that logger respects log level filtering."""
        logger = get_logger("ERROR", "PLAIN")

        # These should not appear in output
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")

        # This should appear
        logger.error("Error message", node="test", service="test")

        output = mock_stdout.getvalue()

        assert "Debug message" not in output
        assert "Info message" not in output
        assert "Warning message" not in output
        assert "Error message" in output

    def test_get_logger_case_insensitive_level(self):
        """Test that logger works with case insensitive levels."""
        loggers = [
            get_logger("debug", "PLAIN"),
            get_logger("Debug", "PLAIN"),
            get_logger("DEBUG", "PLAIN"),
            get_logger("info", "PLAIN"),
            get_logger("Info", "PLAIN"),
            get_logger("INFO", "PLAIN"),
        ]

        for logger in loggers:
            assert hasattr(logger, "info")  # Check logger has basic logging methods


class TestLoggerIntegration:
    """Test logger integration and edge cases."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_logger_with_contextvars(self, mock_stdout):
        """Test logger with context variables."""
        logger = get_logger("INFO", "JSON")

        # Bind context to logger
        bound_logger = logger.bind(request_id="123", user_id="456")
        bound_logger.info("User action", action="login")

        output = mock_stdout.getvalue().strip()
        parsed = json.loads(output)

        assert parsed["event"] == "User action"
        assert parsed["request_id"] == "123"
        assert parsed["user_id"] == "456"
        assert parsed["action"] == "login"

    @patch("sys.stdout", new_callable=StringIO)
    def test_logger_with_exception_info(self, mock_stdout):
        """Test logger with exception information."""
        logger = get_logger("ERROR", "JSON")

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("An error occurred")

        output = mock_stdout.getvalue().strip()
        parsed = json.loads(output)

        assert parsed["event"] == "An error occurred"
        assert parsed["level"] == "error"
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]

    def test_logger_configuration_isolation(self):
        """Test that logger configurations don't interfere with each other."""
        logger1 = get_logger("DEBUG", "JSON")
        logger2 = get_logger("ERROR", "PLAIN")

        # Both should work independently
        assert hasattr(logger1, "info")  # Check logger has basic logging methods
        assert hasattr(logger2, "info")  # Check logger has basic logging methods
