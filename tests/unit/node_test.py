"""Unit tests for the Node module."""

import sys
from unittest.mock import Mock

import pytest

from pylecular.node import Node, NodeCatalog


class TestNode:
    """Test Node class."""

    def test_node_initialization_minimal(self):
        """Test Node initialization with minimal parameters."""
        node = Node("test-node-123")

        assert node.id == "test-node-123"
        assert node.available is True
        assert node.local is False
        assert node.services == []
        assert node.cpu == 0.0
        assert node.client is None
        assert node.ipList == []
        assert node.hostname is None
        assert node.config == {}
        assert node.instanceID is None
        assert node.metadata == {}
        assert node.seq == 0
        assert node.ver == 0
        assert node.sender is None

    def test_node_initialization_full(self):
        """Test Node initialization with all parameters."""
        services = [{"name": "service1"}, {"name": "service2"}]
        client = {"type": "python", "version": "3.9"}
        ip_list = ["192.168.1.1", "10.0.0.1"]
        config = {"timeout": 5000, "retries": 3}
        metadata = {"region": "us-east-1", "datacenter": "dc1"}

        node = Node(
            node_id="test-node-123",
            available=False,
            local=True,
            services=services,
            cpu=45.5,
            client=client,
            ip_list=ip_list,
            hostname="test-host",
            config=config,
            instance_id="instance-456",
            metadata=metadata,
            seq=5,
            ver=2,
            sender="sender-node",
        )

        assert node.id == "test-node-123"
        assert node.available is False
        assert node.local is True
        assert node.services == services
        assert node.cpu == 45.5
        assert node.client == client
        assert node.ipList == ip_list
        assert node.hostname == "test-host"
        assert node.config == config
        assert node.instanceID == "instance-456"
        assert node.metadata == metadata
        assert node.seq == 5
        assert node.ver == 2
        assert node.sender == "sender-node"

    def test_node_get_info(self):
        """Test Node get_info method returns all attributes."""
        node = Node("test-node", available=True, cpu=25.0, hostname="test-host")

        info = node.get_info()

        # Should return a dictionary with all node attributes
        assert isinstance(info, dict)
        assert info["id"] == "test-node"
        assert info["available"] is True
        assert info["cpu"] == 25.0
        assert info["hostname"] == "test-host"
        assert info["local"] is False
        assert info["services"] == []


class TestNodeCatalog:
    """Test NodeCatalog class."""

    @pytest.fixture
    def mock_registry(self):
        """Create a mock registry."""
        registry = Mock()
        registry.__services__ = {}
        registry.add_action = Mock()
        registry.add_event_obj = Mock()
        return registry

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return Mock()

    def test_node_catalog_initialization(self, mock_registry, mock_logger):
        """Test NodeCatalog initialization."""
        catalog = NodeCatalog(mock_registry, mock_logger, "local-node-123")

        assert catalog.registry == mock_registry
        assert catalog.logger == mock_logger
        assert catalog.node_id == "local-node-123"
        assert "local-node-123" in catalog.nodes  # Local node is auto-created
        assert catalog.local_node is not None
        assert catalog.local_node.id == "local-node-123"
        assert catalog.local_node.local is True

    def test_ensure_local_node_creates_node(self, mock_registry, mock_logger):
        """Test ensure_local_node creates local node if not exists."""
        catalog = NodeCatalog(mock_registry, mock_logger, "local-node-123")
        catalog.local_node = None  # Reset to test creation

        catalog.ensure_local_node()

        assert catalog.local_node is not None
        assert catalog.local_node.id == "local-node-123"
        assert catalog.local_node.local is True
        assert catalog.local_node.client["type"] == "python"
        assert catalog.local_node.client["langVersion"] == sys.version
        assert "local-node-123" in catalog.nodes

    def test_ensure_local_node_configures_existing_node(self, mock_registry, mock_logger):
        """Test ensure_local_node configures existing local node."""
        catalog = NodeCatalog(mock_registry, mock_logger, "local-node-123")

        # Local node should already exist from initialization
        original_node = catalog.local_node

        catalog.ensure_local_node()

        # Should be the same node instance, but properly configured
        assert catalog.local_node == original_node
        assert catalog.local_node.local is True
        assert catalog.local_node.client["type"] == "python"

    def test_ensure_local_node_builds_services_from_registry(self, mock_registry, mock_logger):
        """Test ensure_local_node builds service definitions from registry."""
        # Create mock services
        service1 = Mock()
        service1.name = "user-service"
        service1.settings = {"timeout": 5000}
        service1.metadata = {"version": "1.0"}
        service1.actions.return_value = ["create", "update"]
        service1.events.return_value = ["created", "updated"]

        # Mock event attributes
        created_event = Mock()
        created_event._name = "user.created"
        updated_event = Mock()
        # Ensure updated_event has no _name attribute to test fallback
        del updated_event._name  # Remove the auto-created mock attribute

        service1.created = created_event
        service1.updated = updated_event

        service2 = Mock()
        service2.name = "auth-service"
        service2.settings = {}
        service2.metadata = {}
        service2.actions.return_value = ["login"]
        service2.events.return_value = []

        mock_registry.__services__ = {"user-service": service1, "auth-service": service2}

        catalog = NodeCatalog(mock_registry, mock_logger, "local-node-123")
        catalog.local_node = None

        catalog.ensure_local_node()

        services = catalog.local_node.services
        assert len(services) == 2

        # Check user-service definition
        user_service = next(s for s in services if s["name"] == "user-service")
        assert user_service["fullName"] == "user-service"
        assert user_service["settings"] == {"timeout": 5000}
        assert user_service["metadata"] == {"version": "1.0"}
        assert "user-service.create" in user_service["actions"]
        assert "user-service.update" in user_service["actions"]
        assert user_service["actions"]["user-service.create"]["rawName"] == "create"
        assert "user.created" in user_service["events"]
        assert "updated" in user_service["events"]  # Falls back to event name when no _name

        # Check auth-service definition
        auth_service = next(s for s in services if s["name"] == "auth-service")
        assert auth_service["fullName"] == "auth-service"
        assert "auth-service.login" in auth_service["actions"]
        assert auth_service["events"] == {}

    def test_add_node(self, mock_registry, mock_logger):
        """Test adding a node to the catalog."""
        catalog = NodeCatalog(mock_registry, mock_logger, "local-node-123")

        # Create a node with services
        services = [
            {
                "name": "test-service",
                "actions": {"test.action1": {}, "test.action2": {}},
                "events": {"test.event1": {}, "test.event2": {}},
            }
        ]

        node = Node("remote-node-456", services=services)

        catalog.add_node("remote-node-456", node)

        # Check node was added
        assert "remote-node-456" in catalog.nodes
        assert catalog.nodes["remote-node-456"] == node

        # Check actions were registered
        assert mock_registry.add_action.call_count == 2
        action_calls = mock_registry.add_action.call_args_list
        assert action_calls[0][0][0].name == "test.action1"
        assert action_calls[0][0][0].node_id == "remote-node-456"
        assert action_calls[0][0][0].is_local is False

        # Check events were registered
        assert mock_registry.add_event_obj.call_count == 2
        event_calls = mock_registry.add_event_obj.call_args_list
        assert event_calls[0][0][0].name == "test.event1"
        assert event_calls[0][0][0].node_id == "remote-node-456"
        assert event_calls[0][0][0].is_local is False

        # Check logging
        mock_logger.info.assert_called_with('Node "remote-node-456" added.')

    def test_add_node_without_services(self, mock_registry, mock_logger):
        """Test adding a node without services."""
        catalog = NodeCatalog(mock_registry, mock_logger, "local-node-123")

        node = Node("simple-node")
        catalog.add_node("simple-node", node)

        assert "simple-node" in catalog.nodes
        assert catalog.nodes["simple-node"] == node
        mock_registry.add_action.assert_not_called()
        mock_registry.add_event_obj.assert_not_called()

    def test_get_node(self, mock_registry, mock_logger):
        """Test getting a node by ID."""
        catalog = NodeCatalog(mock_registry, mock_logger, "local-node-123")

        node1 = Node("node-1")
        node2 = Node("node-2")

        catalog.add_node("node-1", node1)
        catalog.add_node("node-2", node2)

        # Test getting existing nodes
        assert catalog.get_node("node-1") == node1
        assert catalog.get_node("node-2") == node2
        assert catalog.get_node("local-node-123") == catalog.local_node

        # Test getting non-existent node
        assert catalog.get_node("non-existent") is None

    def test_remove_node(self, mock_registry, mock_logger):
        """Test removing a node from the catalog."""
        catalog = NodeCatalog(mock_registry, mock_logger, "local-node-123")

        node = Node("removable-node")
        catalog.add_node("removable-node", node)

        # Verify node exists
        assert "removable-node" in catalog.nodes

        # Remove the node
        catalog.remove_node("removable-node")

        # Verify node was removed
        assert "removable-node" not in catalog.nodes
        mock_logger.info.assert_called_with('Node "removable-node" removed.')

    def test_remove_nonexistent_node(self, mock_registry, mock_logger):
        """Test removing a non-existent node."""
        catalog = NodeCatalog(mock_registry, mock_logger, "local-node-123")

        # Should not raise error
        catalog.remove_node("non-existent")

        # Should not log removal
        assert not any("removed" in str(call) for call in mock_logger.info.call_args_list)

    def test_disconnect_node(self, mock_registry, mock_logger):
        """Test disconnecting a node."""
        catalog = NodeCatalog(mock_registry, mock_logger, "local-node-123")

        node = Node("disconnectable-node", available=True)
        catalog.add_node("disconnectable-node", node)

        # Disconnect the node
        catalog.disconnect_node("disconnectable-node")

        # Check that node was marked as unavailable and removed
        assert "disconnectable-node" not in catalog.nodes

        # Check logging - should have both disconnect and remove messages
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("disconnected" in call for call in info_calls)
        assert any("removed" in call for call in info_calls)

    def test_disconnect_nonexistent_node(self, mock_registry, mock_logger):
        """Test disconnecting a non-existent node."""
        catalog = NodeCatalog(mock_registry, mock_logger, "local-node-123")

        # Should not raise error
        catalog.disconnect_node("non-existent")

        # Should not log disconnect
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert not any("disconnected" in call for call in info_calls)

    def test_process_node_info_new_node(self, mock_registry, mock_logger):
        """Test processing node info for a new node."""
        catalog = NodeCatalog(mock_registry, mock_logger, "local-node-123")

        payload = {"cpu": 35.5, "services": [{"name": "test-service"}], "additional": "data"}

        catalog.process_node_info("new-node", payload)

        # Check that node was created and added
        assert "new-node" in catalog.nodes
        node = catalog.nodes["new-node"]
        assert node.id == "new-node"
        assert node.available is True
        assert node.cpu == 35.5
        assert node.services == [{"name": "test-service"}]

        # Check logging
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("added" in call for call in info_calls)
        assert any("connected" in call for call in info_calls)

    def test_process_node_info_existing_node(self, mock_registry, mock_logger):
        """Test processing node info for an existing node."""
        catalog = NodeCatalog(mock_registry, mock_logger, "local-node-123")

        # Add an existing node
        existing_node = Node("existing-node", available=False, cpu=10.0)
        catalog.add_node("existing-node", existing_node)

        # Clear previous log calls
        mock_logger.reset_mock()

        # Process updated info
        payload = {"cpu": 50.0, "services": [{"name": "updated-service"}]}

        catalog.process_node_info("existing-node", payload)

        # Check that existing node was updated
        node = catalog.nodes["existing-node"]
        assert node == existing_node  # Same instance
        assert node.available is True  # Updated
        assert node.cpu == 50.0  # Updated
        assert node.services == [{"name": "updated-service"}]  # Updated

        # Should only log connection, not addition
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("connected" in call for call in info_calls)
        assert not any("added" in call for call in info_calls)

    def test_process_node_info_empty_payload(self, mock_registry, mock_logger):
        """Test processing node info with minimal payload."""
        catalog = NodeCatalog(mock_registry, mock_logger, "local-node-123")

        catalog.process_node_info("minimal-node", {})

        # Check that node was created with defaults
        assert "minimal-node" in catalog.nodes
        node = catalog.nodes["minimal-node"]
        assert node.available is True
        assert node.cpu == 0.0  # Default value
        assert node.services == []  # Default value

    def test_node_constructor_field_names_regression(self):
        """Regression test: Node constructor should accept standard field names."""
        # Previously, there were issues with field name mismatches
        node = Node(
            node_id="test-node",
            ip_list=["192.168.1.1", "10.0.0.1"],
            instance_id="instance-123",
            available=True,
            cpu=25.0,
        )

        assert node.id == "test-node"
        assert node.ipList == ["192.168.1.1", "10.0.0.1"]
        assert node.instanceID == "instance-123"
        assert node.available is True
        assert node.cpu == 25.0
