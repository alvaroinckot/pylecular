"""Transit layer for message handling and communication in Pylecular framework.

This module provides the Transit class which handles message routing, node discovery,
and inter-service communication through various transporter implementations.
"""

import asyncio
import traceback
from typing import TYPE_CHECKING, Any, Dict, Optional

import psutil

if TYPE_CHECKING:
    from .context import Context
    from .lifecycle import Lifecycle
    from .node import NodeCatalog
    from .registry import Action, Event, Registry
    from .settings import Settings

from .node import Node
from .packet import Packet, Topic
from .transporter.base import Transporter


class RemoteCallError(Exception):
    """Exception raised when a remote service call fails."""

    def __init__(self, message: str, error_name: str = "RemoteError", stack: Optional[str] = None):
        super().__init__(message)
        self.error_name = error_name
        self.stack = stack


class Transit:
    """Handles message routing and communication between Pylecular nodes.

    The Transit layer is responsible for:
    - Establishing connections through transporters
    - Routing messages between nodes
    - Handling service discovery and heartbeats
    - Managing request/response cycles
    - Processing events
    """

    DEFAULT_REQUEST_TIMEOUT = 5.0  # seconds

    def __init__(
        self,
        node_id: str,
        registry: "Registry",
        node_catalog: "NodeCatalog",
        settings: "Settings",
        logger: Any,
        lifecycle: "Lifecycle",
    ) -> None:
        """Initialize the Transit layer.

        Args:
            node_id: Unique identifier for this node
            registry: Service registry for action/event lookup
            node_catalog: Catalog of known nodes in the cluster
            settings: Configuration settings
            logger: Logger instance
            lifecycle: Context lifecycle manager
        """
        self.node_id = node_id
        self.registry = registry
        self.node_catalog = node_catalog
        self.logger = logger
        self.lifecycle = lifecycle

        # Initialize transporter based on settings
        transporter_name = settings.transporter.split("://")[0]
        self.transporter: Transporter = Transporter.get_by_name(
            transporter_name,
            {"connection": settings.transporter},
            transit=self,
            handler=self._message_handler,
            node_id=node_id,
        )

        # Track pending requests for timeout handling
        self._pending_requests: Dict[str, asyncio.Future] = {}

    async def _message_handler(self, packet: Packet) -> None:
        """Handle incoming packets based on their type.

        Args:
            packet: Incoming packet to process
        """
        handlers = {
            Topic.INFO: self._handle_info,
            Topic.DISCOVER: self._handle_discover,
            Topic.HEARTBEAT: self._handle_heartbeat,
            Topic.REQUEST: self._handle_request,
            Topic.RESPONSE: self._handle_response,
            Topic.EVENT: self._handle_event,
            Topic.DISCONNECT: self._handle_disconnect,
        }

        handler = handlers.get(packet.type)
        if handler:
            try:
                await handler(packet)
            except Exception as e:
                self.logger.error(f"Error handling {packet.type.value} packet: {e}")
        else:
            self.logger.warning(f"Unknown packet type: {packet.type}")

    async def _make_subscriptions(self) -> None:
        """Subscribe to all necessary topics for this node."""
        subscriptions = [
            (Topic.INFO.value, None),
            (Topic.INFO.value, self.node_id),
            (Topic.DISCOVER.value, None),
            (Topic.HEARTBEAT.value, None),
            (Topic.REQUEST.value, self.node_id),
            (Topic.RESPONSE.value, self.node_id),
            (Topic.EVENT.value, self.node_id),
            (Topic.DISCONNECT.value, None),
        ]

        for topic, node_id in subscriptions:
            await self.transporter.subscribe(topic, node_id)

    async def connect(self) -> None:
        """Establish connection and initialize the node in the cluster."""
        await self.transporter.connect()
        await self.discover()
        await self.send_node_info()
        await self._make_subscriptions()
        self.logger.info(f"Transit connected for node {self.node_id}")

    async def disconnect(self) -> None:
        """Gracefully disconnect from the cluster."""
        # Notify other nodes of disconnection
        try:
            await self.publish(Packet(Topic.DISCONNECT, None, {}))
        except Exception as e:
            self.logger.warning(f"Error sending disconnect notification: {e}")

        # Cancel all pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()

        # Disconnect transporter
        await self.transporter.disconnect()
        self.logger.info(f"Transit disconnected for node {self.node_id}")

    async def publish(self, packet: Packet) -> None:
        """Publish a packet through the transporter.

        Args:
            packet: Packet to publish
        """
        await self.transporter.publish(packet)

    async def discover(self) -> None:
        """Send a discovery request to find other nodes in the cluster."""
        await self.publish(Packet(Topic.DISCOVER, None, {}))

    async def beat(self) -> None:
        """Send a heartbeat with current node metrics."""
        heartbeat_data = {
            "cpu": psutil.cpu_percent(interval=0.1),  # Non-blocking CPU check
            "timestamp": asyncio.get_event_loop().time(),
        }
        await self.publish(Packet(Topic.HEARTBEAT, None, heartbeat_data))

    async def send_node_info(self) -> None:
        """Send current node information to the cluster."""
        if self.node_catalog.local_node is None:
            self.logger.error("Local node is not initialized")
            return

        node_info = self.node_catalog.local_node.get_info()
        await self.publish(Packet(Topic.INFO, None, node_info))

    async def _handle_discover(self, packet: Packet) -> None:
        """Handle discovery requests by sending node info.

        Args:
            packet: Discovery packet
        """
        await self.send_node_info()

    async def _handle_heartbeat(self, packet: Packet) -> None:
        """Handle heartbeat packets from other nodes.

        Args:
            packet: Heartbeat packet
        """
        # Update node's last seen timestamp
        if packet.sender:
            node = self.node_catalog.get_node(packet.sender)
            if node:
                node.cpu = packet.payload.get("cpu", 0.0)
                # Could add timestamp tracking here for node health monitoring

    async def _handle_info(self, packet: Packet) -> None:
        """Handle node info packets.

        Args:
            packet: Info packet containing node details
        """
        if not packet.payload or not packet.sender:
            return

        # Extract node data, excluding the ID from payload and mapping field names
        node_data = {}
        field_mapping = {"ipList": "ip_list", "instanceID": "instance_id"}

        # Valid Node constructor parameters (excluding node_id which is handled separately)
        valid_node_params = {
            "available",
            "local",
            "services",
            "cpu",
            "client",
            "ip_list",
            "hostname",
            "config",
            "instance_id",
            "metadata",
            "seq",
            "ver",
            "sender",
        }

        for k, v in packet.payload.items():
            if k != "id":
                # Map field names to match Node constructor parameters
                mapped_key = field_mapping.get(k, k)
                # Only include fields that are valid Node constructor parameters
                if mapped_key in valid_node_params:
                    node_data[mapped_key] = v

        node = Node(node_id=packet.payload.get("id", packet.sender), **node_data)
        self.node_catalog.add_node(packet.sender, node)

    async def _handle_disconnect(self, packet: Packet) -> None:
        """Handle node disconnection notifications.

        Args:
            packet: Disconnect packet
        """
        if packet.sender:
            self.node_catalog.disconnect_node(packet.sender)

    async def _handle_event(self, packet: Packet) -> None:
        """Handle event packets.

        Args:
            packet: Event packet
        """
        event_name = packet.payload.get("event")
        if not event_name:
            self.logger.warning("Received event packet without event name")
            return

        endpoint = self.registry.get_event(event_name)
        if endpoint and endpoint.is_local and endpoint.handler:
            context = self.lifecycle.rebuild_context(packet.payload)
            try:
                await endpoint.handler(context)
            except Exception as e:
                self.logger.error(f"Failed to process event {endpoint.name}: {e}")

    async def _handle_request(self, packet: Packet) -> None:
        """Handle service request packets.

        Args:
            packet: Request packet
        """
        action_name = packet.payload.get("action")
        if not action_name:
            self.logger.warning("Received request packet without action name")
            return

        endpoint = self.registry.get_action(action_name)
        if not endpoint or not endpoint.is_local:
            self.logger.warning(f"No local handler for action: {action_name}")
            return

        context = self.lifecycle.rebuild_context(packet.payload)

        try:
            # Validate parameters if schema is defined
            if endpoint.params_schema:
                from .validator import ValidationError, validate_params

                try:
                    validate_params(context.params, endpoint.params_schema)
                except ValidationError:
                    raise  # Re-raise validation errors

            # Execute the action handler
            if not endpoint.handler:
                raise Exception(f"No handler defined for action {action_name}")

            result = await endpoint.handler(context)
            response = {"id": context.id, "data": result, "success": True, "meta": {}}

        except Exception as e:
            self.logger.error(f"Failed call to {endpoint.name}: {e}")
            response = {
                "id": context.id,
                "error": {
                    "name": e.__class__.__name__,
                    "message": str(e),
                    "stack": traceback.format_exc(),
                },
                "success": False,
                "meta": {},
            }

        # Send response back to the caller
        await self.publish(Packet(Topic.RESPONSE, packet.sender, response))

    async def _handle_response(self, packet: Packet) -> None:
        """Handle response packets for pending requests.

        Args:
            packet: Response packet
        """
        req_id = packet.payload.get("id")
        if not req_id:
            return

        future = self._pending_requests.pop(req_id, None)
        if future and not future.done():
            future.set_result(packet.payload)

    async def request(self, endpoint: "Action", context: "Context") -> Any:
        """Send a request to a remote service action.

        Args:
            endpoint: Action endpoint to call
            context: Request context

        Returns:
            Response data from the remote service

        Raises:
            RemoteCallError: If the remote call fails
            asyncio.TimeoutError: If the request times out
        """
        req_id = context.id
        future = asyncio.get_running_loop().create_future()
        self._pending_requests[req_id] = future

        # Send the request
        await self.publish(Packet(Topic.REQUEST, endpoint.node_id, context.marshall()))

        try:
            response = await asyncio.wait_for(future, self.DEFAULT_REQUEST_TIMEOUT)

            # Check if the response indicates an error
            if not response.get("success", True):
                error_data = response.get("error", {})
                error_msg = error_data.get("message", "Unknown error")
                error_name = error_data.get("name", "RemoteError")
                error_stack = error_data.get("stack")

                if error_stack:
                    self.logger.error(f"Remote error stack: {error_stack}")

                raise RemoteCallError(error_msg, error_name, error_stack)

            return response.get("data")

        except asyncio.TimeoutError:
            # Clean up the pending request
            self._pending_requests.pop(req_id, None)
            raise Exception(f"Request to {endpoint.name} timed out") from None

    async def send_event(self, endpoint: "Event", context: "Context") -> None:
        """Send an event to a remote service.

        Args:
            endpoint: Event endpoint to send to
            context: Event context
        """
        await self.publish(Packet(Topic.EVENT, endpoint.node_id, context.marshall()))
