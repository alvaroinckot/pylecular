class Settings:
    def __init__(
        self,
        transporter="nats://localhost:4222",
        serializer="JSON",
        log_level="INFO",
        log_format="PLAIN",
        middlewares=None,
    ):
        self.transporter = transporter
        self.serializer = serializer
        self.log_level = log_level
        self.log_format = log_format
        self.middlewares = middlewares or []
