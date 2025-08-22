"""Node management and catalog for the Pylecular framework.

This module provides node representation and catalog management for tracking
nodes in a Pylecular cluster, including their services, actions, and events.
"""

import sys
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .registry import Registry

from .registry import Action, Event


class Node:
    """Represents a node in the Pylecular cluster.

    A node contains information about its services, capabilities, and current
    status within the distributed system.
    """

    def __init__(
        self,
        node_id: str,
        available: bool = True,
        local: bool = False,
        services: Optional[List[Dict[str, Any]]] = None,
        cpu: float = 0.0,
        client: Optional[Dict[str, Any]] = None,
        ip_list: Optional[List[str]] = None,
        hostname: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        instance_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        seq: int = 0,
        ver: int = 0,
        sender: Optional[str] = None,
    ) -> None:
        """Initialize a new Node instance.

        Args:
            node_id: Unique identifier for this node
            available: Whether the node is currently available
            local: Whether this is the local node
            services: List of services running on this node
            cpu: CPU usage percentage
            client: Client information (type, version, etc.)
            ip_list: List of IP addresses for this node
            hostname: Hostname of the node
            config: Node configuration
            instance_id: Unique instance identifier
            metadata: Additional node metadata
            seq: Sequence number for ordering
            ver: Version number
            sender: Sender identifier for the node info
        """
        self.id = node_id
        self.available = available
        self.local = local
        self.services = services or []
        self.cpu = cpu
        self.client = client
        self.ipList = ip_list or []  # Keep original name for compatibility
        self.hostname = hostname
        self.config = config or {}
        self.instanceID = instance_id  # Keep original name for compatibility
        self.metadata = metadata or {}
        self.seq = seq
        self.ver = ver
        self.sender = sender

    def get_info(self) -> Dict[str, Any]:
        """Get node information as a dictionary.

        Returns:
            Dictionary containing all node attributes
        """
        return self.__dict__


class NodeCatalog:
    """Manages the catalog of nodes in the Pylecular cluster.

    The NodeCatalog tracks all nodes in the cluster, manages their lifecycle,
    and maintains the registry of services, actions, and events they provide.
    """

    def __init__(self, registry: "Registry", logger: Any, node_id: str) -> None:
        """Initialize a new NodeCatalog.

        Args:
            registry: Registry instance for tracking services
            logger: Logger instance for catalog operations
            node_id: ID of the local node
        """
        self.nodes: Dict[str, Node] = {}
        self.registry = registry
        self.logger = logger
        self.node_id = node_id
        self.local_node: Optional[Node] = None
        self.ensure_local_node()

    def add_node(self, node_id: str, node: Node) -> None:
        """Add a node to the catalog.

        Args:
            node_id: Unique identifier for the node
            node: Node instance to add
        """
        self.nodes[node_id] = node

        # Register node's services, actions, and events
        if self.registry and hasattr(node, "services"):
            for service in node.services:
                # Register actions from the service
                actions = service.get("actions", {})
                for action_name in actions:
                    action_obj = Action(name=action_name, node_id=node_id, is_local=False)
                    self.registry.add_action(action_obj)

                # Register events from the service
                events = service.get("events", {})
                for event_name in events:
                    event_obj = Event(name=event_name, node_id=node_id, is_local=False)
                    self.registry.add_event_obj(event_obj)

        self.logger.info(f'Node "{node_id}" added.')

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by its ID.

        Args:
            node_id: ID of the node to retrieve

        Returns:
            Node instance if found, None otherwise
        """
        return self.nodes.get(node_id)

    def remove_node(self, node_id: str) -> None:
        """Remove a node from the catalog.

        Args:
            node_id: ID of the node to remove
        """
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.logger.info(f'Node "{node_id}" removed.')

    def disconnect_node(self, node_id: str) -> None:
        """Mark a node as disconnected and remove it.

        Args:
            node_id: ID of the node to disconnect
        """
        node = self.get_node(node_id)
        if node:
            node.available = False
            self.logger.info(f'Node "{node_id}" is disconnected.')
            self.remove_node(node_id)

    def process_node_info(self, node_id: str, payload: Dict[str, Any]) -> None:
        """Process node information update.

        Args:
            node_id: ID of the node being updated
            payload: Dictionary containing node information
        """
        node = self.get_node(node_id)
        if not node:
            node = Node(node_id)
            self.add_node(node_id, node)

        # Update node information
        node.available = True
        node.cpu = payload.get("cpu", 0.0)
        node.services = payload.get("services", [])
        self.logger.info(f'Node "{node_id}" is connected.')

    def ensure_local_node(self) -> None:
        """Ensure the local node exists and is properly configured."""
        if not self.local_node:
            node = Node(self.node_id)
            self.local_node = node
            self.add_node(self.node_id, node)

        # Configure local node properties
        self.local_node.local = True
        self.local_node.client = {
            "type": "python",
            "langVersion": sys.version,
        }

        # Build service definitions from registry
        self.local_node.services = []
        for service in self.registry.__services__.values():
            service_definition = {
                "name": service.name,
                "fullName": service.name,
                "settings": service.settings,
                "metadata": service.metadata,
                "actions": {},
                "events": {},
            }

            # Add actions
            for action in service.actions():
                action_name = f"{service.name}.{action}"
                service_definition["actions"][action_name] = {
                    "rawName": action,
                    "name": action_name,
                }

            # Add events
            for event in service.events():
                event_name = getattr(getattr(service, event), "_name", event)
                service_definition["events"][event_name] = {"name": event_name}

            self.local_node.services.append(service_definition)
