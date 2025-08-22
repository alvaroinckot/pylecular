"""NATS transporter implementation for the Pylecular framework.

This module provides a NATS-based transporter for inter-node communication
in a Pylecular cluster using the NATS messaging system.
"""

import asyncio
import json
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

import nats
from nats.aio.msg import Msg

if TYPE_CHECKING:
    from ..packet import Packet
    from ..transit import Transit

from .base import Transporter


class NatsTransporter(Transporter):
    """NATS transporter for Pylecular inter-node communication.

    This transporter uses NATS (https://nats.io/) as the messaging backbone
    for communication between Pylecular nodes in a distributed system.
    """

    name = "nats"

    def __init__(
        self,
        connection_string: str,
        transit: "Transit",
        handler: Optional[Callable] = None,
        node_id: Optional[str] = None,
    ) -> None:
        """Initialize the NATS transporter.

        Args:
            connection_string: NATS server connection string
            transit: Transit instance for message routing
            handler: Optional message handler function
            node_id: Unique identifier for this node
        """
        super().__init__(self.name)
        self.connection_string = connection_string
        self.transit = transit
        self.handler = handler
        self.node_id = node_id
        self.nc: Optional[Any] = None

    def _serialize(self, payload: Dict[str, Any]) -> bytes:
        """Serialize a payload for transmission over NATS.

        Args:
            payload: Dictionary payload to serialize

        Returns:
            Serialized payload as bytes
        """
        # Add protocol version and sender information
        payload["ver"] = "4"
        payload["sender"] = self.node_id
        return json.dumps(payload).encode("utf-8")

    def get_topic_name(self, command: str, node_id: Optional[str] = None) -> str:
        """Generate a NATS topic name for a command.

        Args:
            command: Command type for the topic
            node_id: Optional specific node ID to target

        Returns:
            Formatted NATS topic name
        """
        topic = f"MOL.{command}"
        if node_id:
            topic += f".{node_id}"
        return topic

    async def message_handler(self, msg: Msg) -> None:
        """Handle incoming NATS messages.

        Args:
            msg: NATS message object

        Raises:
            ValueError: If no handler is configured or JSON parsing fails
        """
        try:
            data = json.loads(msg.data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Failed to decode message data: {e}") from e

        # Import here to avoid circular imports
        from ..packet import Packet

        packet_type = Packet.from_topic(msg.subject)
        if packet_type is None:
            raise ValueError(f"Could not determine packet type from topic: {msg.subject}")
        sender = data.get("sender")
        packet = Packet(packet_type, sender, data)
        packet.sender = sender  # Set the sender attribute

        if self.handler:
            await self.handler(packet)
        else:
            raise ValueError("Message received but no handler is defined")

    async def publish(self, packet: "Packet") -> None:
        """Publish a packet to NATS.

        Args:
            packet: Packet to publish

        Raises:
            RuntimeError: If not connected to NATS
        """
        if not self.nc:
            raise RuntimeError("Not connected to NATS server")

        topic = self.get_topic_name(packet.type.value, packet.target)
        serialized_payload = self._serialize(packet.payload)
        await self.nc.publish(topic, serialized_payload)

    async def connect(self) -> None:
        """Establish connection to the NATS server.

        Raises:
            Exception: If connection fails
        """
        try:
            self.nc = await nats.connect(self.connection_string)
        except Exception as e:
            raise Exception(f"Failed to connect to NATS server: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from the NATS server gracefully."""
        if self.nc:
            try:
                await self.nc.close()
            except Exception:
                # Log the error but don't raise to ensure cleanup continues
                pass
            finally:
                self.nc = None

    async def subscribe(self, command: str, topic: Optional[str] = None) -> None:
        """Subscribe to messages for a specific command.

        Args:
            command: Command type to subscribe to
            topic: Optional specific topic (uses node_id if not provided)

        Raises:
            ValueError: If handler is not configured or not async
            RuntimeError: If not connected to NATS
        """
        if not self.nc:
            raise RuntimeError("Not connected to NATS server")

        if self.handler is None:
            raise ValueError("Handler must be provided for subscription")

        # Validate that the handler is properly configured
        if not asyncio.iscoroutinefunction(self.message_handler):
            raise ValueError("Message handler must be an async function")

        topic_name = self.get_topic_name(command, topic)
        await self.nc.subscribe(topic_name, cb=self.message_handler)

    @classmethod
    def from_config(
        cls: type["NatsTransporter"],
        config: Dict[str, Any],
        transit: "Transit",
        handler: Optional[Callable] = None,
        node_id: Optional[str] = None,
    ) -> "NatsTransporter":
        """Create a NATS transporter from configuration.

        Args:
            config: Configuration dictionary containing connection details
            transit: Transit instance for message routing
            handler: Optional message handler function
            node_id: Optional node identifier

        Returns:
            Configured NatsTransporter instance

        Raises:
            KeyError: If required configuration keys are missing
        """
        try:
            connection_string = config["connection"]
        except KeyError:
            raise KeyError("NATS configuration must include 'connection' key") from None

        return cls(
            connection_string=connection_string,
            transit=transit,
            handler=handler,
            node_id=node_id,
        )
