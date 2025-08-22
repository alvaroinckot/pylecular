"""Unit tests for the settings module."""

from pylecular.settings import Settings


class TestSettings:
    """Test Settings class."""

    def test_settings_default_initialization(self):
        """Test Settings initialization with default values."""
        settings = Settings()

        assert settings.transporter == "nats://localhost:4222"
        assert settings.serializer == "JSON"
        assert settings.log_level == "INFO"
        assert settings.log_format == "PLAIN"
        assert settings.middlewares == []

    def test_settings_custom_initialization(self):
        """Test Settings initialization with custom values."""
        custom_middlewares = ["middleware1", "middleware2"]

        settings = Settings(
            transporter="redis://localhost:6379",
            serializer="MSGPACK",
            log_level="DEBUG",
            log_format="JSON",
            middlewares=custom_middlewares,
        )

        assert settings.transporter == "redis://localhost:6379"
        assert settings.serializer == "MSGPACK"
        assert settings.log_level == "DEBUG"
        assert settings.log_format == "JSON"
        assert settings.middlewares == custom_middlewares

    def test_settings_partial_initialization(self):
        """Test Settings initialization with some custom values."""
        settings = Settings(transporter="tcp://localhost:8080", log_level="ERROR")

        assert settings.transporter == "tcp://localhost:8080"
        assert settings.log_level == "ERROR"
        # Others should use defaults
        assert settings.serializer == "JSON"
        assert settings.log_format == "PLAIN"
        assert settings.middlewares == []

    def test_settings_empty_middlewares(self):
        """Test Settings with explicitly empty middlewares."""
        settings = Settings(middlewares=[])

        assert settings.middlewares == []

    def test_settings_none_middlewares(self):
        """Test Settings with None middlewares (should default to empty list)."""
        settings = Settings(middlewares=None)

        assert settings.middlewares == []

    def test_settings_complex_middlewares(self):
        """Test Settings with complex middleware objects."""

        def middleware_func():
            pass

        class MiddlewareClass:
            pass

        middlewares = [
            middleware_func,
            MiddlewareClass(),
            "string_middleware",
            {"type": "dict_middleware", "config": {"timeout": 5000}},
        ]

        settings = Settings(middlewares=middlewares)

        assert settings.middlewares == middlewares
        assert len(settings.middlewares) == 4

    def test_settings_different_transporter_urls(self):
        """Test Settings with different transporter URL formats."""
        transporter_urls = [
            "nats://localhost:4222",
            "redis://redis.example.com:6379",
            "tcp://10.0.0.1:8080",
            "amqp://user:pass@rabbitmq.local:5672",
            "ws://websocket-server:3000",
            "custom-protocol://host:port",
        ]

        for url in transporter_urls:
            settings = Settings(transporter=url)
            assert settings.transporter == url

    def test_settings_different_log_levels(self):
        """Test Settings with different log levels."""
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in log_levels:
            settings = Settings(log_level=level)
            assert settings.log_level == level

    def test_settings_different_log_formats(self):
        """Test Settings with different log formats."""
        log_formats = ["PLAIN", "JSON", "XML", "CUSTOM"]

        for format_type in log_formats:
            settings = Settings(log_format=format_type)
            assert settings.log_format == format_type

    def test_settings_different_serializers(self):
        """Test Settings with different serializers."""
        serializers = ["JSON", "MSGPACK", "PICKLE", "PROTOBUF", "AVRO"]

        for serializer in serializers:
            settings = Settings(serializer=serializer)
            assert settings.serializer == serializer

    def test_settings_attribute_modification(self):
        """Test that Settings attributes can be modified after creation."""
        settings = Settings()

        # Modify all attributes
        settings.transporter = "new://localhost:9999"
        settings.serializer = "NEW_SERIALIZER"
        settings.log_level = "CRITICAL"
        settings.log_format = "CUSTOM"
        settings.middlewares = ["new_middleware"]

        assert settings.transporter == "new://localhost:9999"
        assert settings.serializer == "NEW_SERIALIZER"
        assert settings.log_level == "CRITICAL"
        assert settings.log_format == "CUSTOM"
        assert settings.middlewares == ["new_middleware"]

    def test_settings_middlewares_list_operations(self):
        """Test that middlewares list can be manipulated."""
        settings = Settings()

        # Start with empty list
        assert len(settings.middlewares) == 0

        # Add middlewares
        settings.middlewares.append("middleware1")
        settings.middlewares.extend(["middleware2", "middleware3"])

        assert len(settings.middlewares) == 3
        assert "middleware1" in settings.middlewares
        assert "middleware2" in settings.middlewares
        assert "middleware3" in settings.middlewares

        # Remove middleware
        settings.middlewares.remove("middleware2")
        assert len(settings.middlewares) == 2
        assert "middleware2" not in settings.middlewares

    def test_settings_case_sensitivity(self):
        """Test that Settings preserves case sensitivity."""
        settings = Settings(
            log_level="debug",  # lowercase
            log_format="json",  # lowercase
            serializer="msgpack",  # lowercase
        )

        assert settings.log_level == "debug"
        assert settings.log_format == "json"
        assert settings.serializer == "msgpack"

    def test_settings_special_characters_in_values(self):
        """Test Settings with special characters in values."""
        settings = Settings(
            transporter="custom://user:p@ssw0rd@host.example.com:8080/path?query=value&other=123",
            serializer="CUSTOM-SERIALIZER_v2.0",
            log_level="DEBUG-VERBOSE",
            log_format="JSON-PRETTY",
        )

        assert "p@ssw0rd" in settings.transporter
        assert settings.serializer == "CUSTOM-SERIALIZER_v2.0"
        assert settings.log_level == "DEBUG-VERBOSE"
        assert settings.log_format == "JSON-PRETTY"

    def test_settings_unicode_values(self):
        """Test Settings with unicode characters."""
        settings = Settings(
            transporter="nats://localhost:4222/テスト",
            serializer="JSON-文字化け",
            log_level="デバッグ",
            log_format="プレーン",
        )

        assert "テスト" in settings.transporter
        assert settings.serializer == "JSON-文字化け"
        assert settings.log_level == "デバッグ"
        assert settings.log_format == "プレーン"

    def test_settings_empty_string_values(self):
        """Test Settings with empty string values."""
        settings = Settings(transporter="", serializer="", log_level="", log_format="")

        assert settings.transporter == ""
        assert settings.serializer == ""
        assert settings.log_level == ""
        assert settings.log_format == ""

    def test_settings_with_callable_middlewares(self):
        """Test Settings with callable middlewares."""

        def sync_middleware():
            return "sync"

        async def async_middleware():
            return "async"

        class CallableMiddleware:
            def __call__(self):
                return "callable"

        middlewares = [sync_middleware, async_middleware, CallableMiddleware()]
        settings = Settings(middlewares=middlewares)

        assert callable(settings.middlewares[0])
        assert callable(settings.middlewares[1])
        assert callable(settings.middlewares[2])

        # Test that they can be called
        assert settings.middlewares[0]() == "sync"
        assert settings.middlewares[2]() == "callable"
