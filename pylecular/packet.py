from enum import Enum
from typing import Any, Optional


class Topic(Enum):
    """Enumeration of message topic types in the Pylecular framework."""

    HEARTBEAT = "HEARTBEAT"
    EVENT = "EVENT"
    DISCONNECT = "DISCONNECT"
    DISCOVER = "DISCOVER"
    INFO = "INFO"
    REQUEST = "REQ"
    RESPONSE = "RES"


class Packet:
    """Represents a message packet in the Pylecular framework.

    Attributes:
        type: The topic type of the packet
        target: The target node or service for the packet
        payload: The data payload of the packet
        sender: The sender node ID (set by transporter)
    """

    def __init__(self, topic: Topic, target: str, payload: Any) -> None:
        """Initialize a new Packet.

        Args:
            topic: The topic type of the packet
            target: The target node or service
            payload: The data payload
        """
        self.type = topic
        self.target = target
        self.payload = payload
        self.sender: Optional[str] = None  # Will be set by transporter

    @staticmethod
    def from_topic(topic: str) -> Optional[Topic]:
        """Parse a topic string and return the corresponding Topic enum.

        Args:
            topic: The topic string to parse (format: 'prefix.TOPIC_TYPE.suffix')

        Returns:
            The corresponding Topic enum value, or None if parsing fails

        Raises:
            ValueError: If the topic string is invalid or topic type is not recognized
        """
        if not topic:
            raise ValueError("Topic string cannot be empty")

        parts = topic.split(".")
        min_topic_parts = 2
        if len(parts) < min_topic_parts:
            raise ValueError(f"Invalid topic format: {topic}")

        try:
            return Topic(parts[1])
        except (ValueError, KeyError) as e:
            raise ValueError(f"Unknown topic type: {parts[1]}") from e
