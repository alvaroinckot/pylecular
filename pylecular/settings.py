from typing import Any, List, Optional


class Settings:
    """Configuration settings for the Pylecular broker.

    Attributes:
        transporter: Transport protocol URL (e.g., 'nats://localhost:4222')
        serializer: Serialization format for messages
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log output format (PLAIN or JSON)
        middlewares: List of middleware functions to apply
    """

    def __init__(
        self,
        transporter: str = "nats://localhost:4222",
        serializer: str = "JSON",
        log_level: str = "INFO",
        log_format: str = "PLAIN",
        middlewares: Optional[List[Any]] = None,
    ) -> None:
        self.transporter = transporter
        self.serializer = serializer
        self.log_level = log_level
        self.log_format = log_format
        self.middlewares = middlewares or []
