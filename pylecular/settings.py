class Settings:
    def __init__(
        self,
        transporter="nats://localhost:4222",
        serializer="JSON",
        log_level="INFO",
        log_format="PLAIN",
    ):
        self.transporter = transporter
        self.serializer = serializer
        self.log_level = log_level
        self.log_format = log_format
