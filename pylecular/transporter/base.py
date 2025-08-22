"""Base transporter abstraction for the Pylecular framework.

This module provides the abstract base class for all transporters, which handle
communication between Pylecular nodes over various messaging protocols.
"""

import importlib
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

if TYPE_CHECKING:
    from ..packet import Packet
    from ..transit import Transit


class Transporter(ABC):
    """Abstract base class for all Pylecular transporters.

    Transporters handle the low-level communication between nodes in a Pylecular
    cluster. They are responsible for publishing and subscribing to messages
    using various messaging protocols (NATS, Redis, etc.).
    """

    def __init__(self, name: str) -> None:
        """Initialize the transporter.

        Args:
            name: Name identifier for this transporter
        """
        self.name = name

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the messaging system.

        This method should handle the connection establishment and any
        necessary authentication or initialization procedures.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the messaging system.

        This method should handle graceful disconnection and cleanup
        of any resources used by the transporter.
        """
        pass

    @abstractmethod
    async def publish(self, packet: "Packet") -> None:
        """Publish a packet to the messaging system.

        Args:
            packet: The packet to publish containing the message data
        """
        pass

    @abstractmethod
    async def subscribe(self, command: str, topic: Optional[str] = None) -> None:
        """Subscribe to messages for a specific command or topic.

        Args:
            command: The command type to subscribe to
            topic: Optional specific topic to subscribe to
        """
        pass

    @classmethod
    def get_by_name(
        cls: type["Transporter"],
        name: str,
        config: Dict[str, Any],
        transit: "Transit",
        handler: Optional[Callable] = None,
        node_id: Optional[str] = None,
    ) -> "Transporter":
        """Get a transporter instance by name.

        This factory method dynamically loads and instantiates the appropriate
        transporter subclass based on the provided name.

        Args:
            name: Name of the transporter (e.g., "nats", "redis")
            config: Configuration dictionary for the transporter
            transit: Transit instance for handling message routing
            handler: Optional message handler function
            node_id: Optional node identifier

        Returns:
            Configured transporter instance

        Raises:
            ValueError: If no transporter is found for the given name
        """
        # Import known transporters to ensure they're registered
        importlib.import_module("pylecular.transporter.nats")

        for subclass in cls.__subclasses__():
            if subclass.__name__.lower().startswith(name.lower()):
                return subclass.from_config(config, transit, handler, node_id)

        raise ValueError(f"No transporter found for: {name}")

    @classmethod
    @abstractmethod
    def from_config(
        cls: type["Transporter"],
        config: Dict[str, Any],
        transit: "Transit",
        handler: Optional[Callable] = None,
        node_id: Optional[str] = None,
    ) -> "Transporter":
        """Create a transporter instance from configuration.

        Args:
            config: Configuration dictionary
            transit: Transit instance for message routing
            handler: Optional message handler function
            node_id: Optional node identifier

        Returns:
            Configured transporter instance
        """
        pass
