"""Unit tests for the Transit module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pylecular.node import Node
from pylecular.packet import Packet, Topic
from pylecular.transit import RemoteCallError, Transit


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for Transit."""
    return {
        "node_id": "test-node-123",
        "registry": MagicMock(),
        "node_catalog": MagicMock(),
        "settings": MagicMock(transporter="nats://localhost:4222"),
        "logger": MagicMock(),
        "lifecycle": MagicMock(),
    }


@pytest.fixture
def mock_transporter():
    """Create a mock transporter."""
    transporter = AsyncMock()
    transporter.connect = AsyncMock()
    transporter.disconnect = AsyncMock()
    transporter.publish = AsyncMock()
    transporter.subscribe = AsyncMock()
    return transporter


class TestRemoteCallError:
    """Test RemoteCallError exception."""

    def test_remote_call_error_initialization(self):
        """Test RemoteCallError with all parameters."""
        error = RemoteCallError("Test error", "CustomError", "Stack trace here")
        assert str(error) == "Test error"
        assert error.error_name == "CustomError"
        assert error.stack == "Stack trace here"

    def test_remote_call_error_defaults(self):
        """Test RemoteCallError with default parameters."""
        error = RemoteCallError("Test error")
        assert str(error) == "Test error"
        assert error.error_name == "RemoteError"
        assert error.stack is None


class TestTransit:
    """Test Transit class."""

    def test_transit_initialization(self, mock_dependencies, mock_transporter):
        """Test Transit initialization."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            assert transit.node_id == "test-node-123"
            assert transit.registry == mock_dependencies["registry"]
            assert transit.node_catalog == mock_dependencies["node_catalog"]
            assert transit.logger == mock_dependencies["logger"]
            assert transit.lifecycle == mock_dependencies["lifecycle"]
            assert transit.transporter == mock_transporter
            assert transit._pending_requests == {}

    @pytest.mark.asyncio
    async def test_connect(self, mock_dependencies, mock_transporter):
        """Test Transit connect method."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)
            transit.discover = AsyncMock()
            transit.send_node_info = AsyncMock()
            transit._make_subscriptions = AsyncMock()

            await transit.connect()

            mock_transporter.connect.assert_called_once()
            transit.discover.assert_called_once()
            transit.send_node_info.assert_called_once()
            transit._make_subscriptions.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_dependencies, mock_transporter):
        """Test Transit disconnect method."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            # Add a pending request
            future = asyncio.Future()
            transit._pending_requests["test-req"] = future

            await transit.disconnect()

            # Check that disconnect packet was published
            mock_transporter.publish.assert_called()
            packet = mock_transporter.publish.call_args[0][0]
            assert packet.type == Topic.DISCONNECT

            # Check that pending requests were cancelled
            assert future.cancelled()
            assert len(transit._pending_requests) == 0

            # Check that transporter was disconnected
            mock_transporter.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish(self, mock_dependencies, mock_transporter):
        """Test Transit publish method."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)
            packet = Packet(Topic.INFO, None, {"test": "data"})

            await transit.publish(packet)

            mock_transporter.publish.assert_called_once_with(packet)

    @pytest.mark.asyncio
    async def test_discover(self, mock_dependencies, mock_transporter):
        """Test Transit discover method."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            await transit.discover()

            mock_transporter.publish.assert_called_once()
            packet = mock_transporter.publish.call_args[0][0]
            assert packet.type == Topic.DISCOVER
            assert packet.target is None
            assert packet.payload == {}

    @pytest.mark.asyncio
    async def test_beat(self, mock_dependencies, mock_transporter):
        """Test Transit beat method."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            with patch("psutil.cpu_percent", return_value=25.5):
                transit = Transit(**mock_dependencies)

                await transit.beat()

                mock_transporter.publish.assert_called_once()
                packet = mock_transporter.publish.call_args[0][0]
                assert packet.type == Topic.HEARTBEAT
                assert packet.payload["cpu"] == 25.5
                assert "timestamp" in packet.payload

    @pytest.mark.asyncio
    async def test_send_node_info(self, mock_dependencies, mock_transporter):
        """Test Transit send_node_info method."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            # Test with no local node
            transit.node_catalog.local_node = None
            await transit.send_node_info()
            mock_transporter.publish.assert_not_called()

            # Test with local node
            mock_node = MagicMock()
            mock_node.get_info.return_value = {"id": "test-node", "services": []}
            transit.node_catalog.local_node = mock_node

            await transit.send_node_info()

            mock_transporter.publish.assert_called_once()
            packet = mock_transporter.publish.call_args[0][0]
            assert packet.type == Topic.INFO
            assert packet.payload == {"id": "test-node", "services": []}

    @pytest.mark.asyncio
    async def test_make_subscriptions(self, mock_dependencies, mock_transporter):
        """Test Transit _make_subscriptions method."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            await transit._make_subscriptions()

            # Check that all necessary subscriptions were made
            expected_calls = [
                (Topic.INFO.value, None),
                (Topic.INFO.value, "test-node-123"),
                (Topic.DISCOVER.value, None),
                (Topic.HEARTBEAT.value, None),
                (Topic.REQUEST.value, "test-node-123"),
                (Topic.RESPONSE.value, "test-node-123"),
                (Topic.EVENT.value, "test-node-123"),
                (Topic.DISCONNECT.value, None),
            ]

            assert mock_transporter.subscribe.call_count == len(expected_calls)
            for i, (topic, node_id) in enumerate(expected_calls):
                call_args = mock_transporter.subscribe.call_args_list[i][0]
                assert call_args == (topic, node_id)

    @pytest.mark.asyncio
    async def test_handle_discover(self, mock_dependencies, mock_transporter):
        """Test Transit _handle_discover method."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)
            transit.send_node_info = AsyncMock()

            packet = Packet(Topic.DISCOVER, "other-node", {})
            await transit._handle_discover(packet)

            transit.send_node_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_heartbeat(self, mock_dependencies, mock_transporter):
        """Test Transit _handle_heartbeat method."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            mock_node = MagicMock()
            transit.node_catalog.get_node.return_value = mock_node

            packet = Packet(Topic.HEARTBEAT, "other-node", {"cpu": 50.0})
            packet.sender = "other-node"
            await transit._handle_heartbeat(packet)

            transit.node_catalog.get_node.assert_called_once_with("other-node")
            assert mock_node.cpu == 50.0

    @pytest.mark.asyncio
    async def test_handle_info(self, mock_dependencies, mock_transporter):
        """Test Transit _handle_info method."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            packet = Packet(
                Topic.INFO,
                "other-node",
                {"id": "other-node", "services": ["service1", "service2"], "ip": "192.168.1.1"},
            )
            packet.sender = "other-node"

            await transit._handle_info(packet)

            # Check that node was added to catalog
            transit.node_catalog.add_node.assert_called_once()
            call_args = transit.node_catalog.add_node.call_args[0]
            assert call_args[0] == "other-node"
            assert isinstance(call_args[1], Node)

    @pytest.mark.asyncio
    async def test_handle_disconnect(self, mock_dependencies, mock_transporter):
        """Test Transit _handle_disconnect method."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            packet = Packet(Topic.DISCONNECT, "other-node", {})
            packet.sender = "other-node"

            await transit._handle_disconnect(packet)

            transit.node_catalog.disconnect_node.assert_called_once_with("other-node")

    @pytest.mark.asyncio
    async def test_handle_event(self, mock_dependencies, mock_transporter):
        """Test Transit _handle_event method."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            # Setup mock event endpoint
            mock_endpoint = MagicMock()
            mock_endpoint.is_local = True
            mock_endpoint.handler = AsyncMock()
            mock_endpoint.name = "test.event"
            transit.registry.get_event.return_value = mock_endpoint

            mock_context = MagicMock()
            transit.lifecycle.rebuild_context.return_value = mock_context

            packet = Packet(Topic.EVENT, "other-node", {"event": "test.event", "data": "test"})
            await transit._handle_event(packet)

            transit.registry.get_event.assert_called_once_with("test.event")
            transit.lifecycle.rebuild_context.assert_called_once_with(
                {"event": "test.event", "data": "test"}
            )
            mock_endpoint.handler.assert_called_once_with(mock_context)

    @pytest.mark.asyncio
    async def test_handle_request_success(self, mock_dependencies, mock_transporter):
        """Test Transit _handle_request method with successful execution."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            # Setup mock action endpoint
            mock_endpoint = MagicMock()
            mock_endpoint.is_local = True
            mock_endpoint.handler = AsyncMock(return_value={"result": "success"})
            mock_endpoint.name = "test.action"
            mock_endpoint.params_schema = None
            transit.registry.get_action.return_value = mock_endpoint

            mock_context = MagicMock()
            mock_context.id = "req-123"
            mock_context.params = {}
            transit.lifecycle.rebuild_context.return_value = mock_context

            packet = Packet(Topic.REQUEST, "other-node", {"action": "test.action", "id": "req-123"})
            packet.sender = "other-node"
            await transit._handle_request(packet)

            # Check that response was sent
            mock_transporter.publish.assert_called_once()
            response_packet = mock_transporter.publish.call_args[0][0]
            assert response_packet.type == Topic.RESPONSE
            assert response_packet.target == "other-node"
            assert response_packet.payload["success"] is True
            assert response_packet.payload["data"] == {"result": "success"}

    @pytest.mark.asyncio
    async def test_handle_request_error(self, mock_dependencies, mock_transporter):
        """Test Transit _handle_request method with handler error."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            # Setup mock action endpoint that raises error
            mock_endpoint = MagicMock()
            mock_endpoint.is_local = True
            mock_endpoint.handler = AsyncMock(side_effect=ValueError("Test error"))
            mock_endpoint.name = "test.action"
            mock_endpoint.params_schema = None
            transit.registry.get_action.return_value = mock_endpoint

            mock_context = MagicMock()
            mock_context.id = "req-123"
            mock_context.params = {}
            transit.lifecycle.rebuild_context.return_value = mock_context

            packet = Packet(Topic.REQUEST, "other-node", {"action": "test.action", "id": "req-123"})
            packet.sender = "other-node"
            await transit._handle_request(packet)

            # Check that error response was sent
            mock_transporter.publish.assert_called_once()
            response_packet = mock_transporter.publish.call_args[0][0]
            assert response_packet.type == Topic.RESPONSE
            assert response_packet.payload["success"] is False
            assert "error" in response_packet.payload
            assert response_packet.payload["error"]["name"] == "ValueError"
            assert response_packet.payload["error"]["message"] == "Test error"

    @pytest.mark.asyncio
    async def test_handle_response(self, mock_dependencies, mock_transporter):
        """Test Transit _handle_response method."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            # Create a pending request
            future = asyncio.Future()
            transit._pending_requests["req-123"] = future

            packet = Packet(
                Topic.RESPONSE,
                "other-node",
                {"id": "req-123", "success": True, "data": {"result": "success"}},
            )

            await transit._handle_response(packet)

            # Check that future was resolved
            assert future.done()
            assert future.result() == {
                "id": "req-123",
                "success": True,
                "data": {"result": "success"},
            }
            assert "req-123" not in transit._pending_requests

    @pytest.mark.asyncio
    async def test_request_success(self, mock_dependencies, mock_transporter):
        """Test Transit request method with successful response."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            mock_endpoint = MagicMock()
            mock_endpoint.node_id = "remote-node"
            mock_endpoint.name = "test.action"

            mock_context = MagicMock()
            mock_context.id = "req-123"
            mock_context.marshall.return_value = {"id": "req-123", "action": "test.action"}

            # Simulate response
            async def simulate_response():
                await asyncio.sleep(0.01)
                packet = Packet(
                    Topic.RESPONSE,
                    "remote-node",
                    {"id": "req-123", "success": True, "data": {"result": "success"}},
                )
                await transit._handle_response(packet)

            # Start the response simulation
            response_task = asyncio.create_task(simulate_response())

            # Make the request
            result = await transit.request(mock_endpoint, mock_context)

            # Ensure the task completes
            await response_task

            assert result == {"result": "success"}
            mock_transporter.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_remote_error(self, mock_dependencies, mock_transporter):
        """Test Transit request method with remote error."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            mock_endpoint = MagicMock()
            mock_endpoint.node_id = "remote-node"
            mock_endpoint.name = "test.action"

            mock_context = MagicMock()
            mock_context.id = "req-123"
            mock_context.marshall.return_value = {"id": "req-123", "action": "test.action"}

            # Simulate error response
            async def simulate_error_response():
                await asyncio.sleep(0.01)
                packet = Packet(
                    Topic.RESPONSE,
                    "remote-node",
                    {
                        "id": "req-123",
                        "success": False,
                        "error": {
                            "name": "CustomError",
                            "message": "Remote error occurred",
                            "stack": "Stack trace here",
                        },
                    },
                )
                await transit._handle_response(packet)

            # Start the response simulation
            error_task = asyncio.create_task(simulate_error_response())

            # Make the request and expect error
            with pytest.raises(RemoteCallError) as exc_info:
                await transit.request(mock_endpoint, mock_context)

            # Ensure the task completes
            await error_task

            assert str(exc_info.value) == "Remote error occurred"
            assert exc_info.value.error_name == "CustomError"
            assert exc_info.value.stack == "Stack trace here"

    @pytest.mark.asyncio
    async def test_request_timeout(self, mock_dependencies, mock_transporter):
        """Test Transit request method with timeout."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)
            transit.DEFAULT_REQUEST_TIMEOUT = 0.1  # Short timeout for test

            mock_endpoint = MagicMock()
            mock_endpoint.node_id = "remote-node"
            mock_endpoint.name = "test.action"

            mock_context = MagicMock()
            mock_context.id = "req-123"
            mock_context.marshall.return_value = {"id": "req-123", "action": "test.action"}

            # Make the request and expect timeout
            with pytest.raises(Exception) as exc_info:
                await transit.request(mock_endpoint, mock_context)

            assert "timed out" in str(exc_info.value)
            assert "req-123" not in transit._pending_requests

    @pytest.mark.asyncio
    async def test_send_event(self, mock_dependencies, mock_transporter):
        """Test Transit send_event method."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            mock_endpoint = MagicMock()
            mock_endpoint.node_id = "remote-node"
            mock_endpoint.name = "test.event"

            mock_context = MagicMock()
            mock_context.marshall.return_value = {"event": "test.event", "data": "test"}

            await transit.send_event(mock_endpoint, mock_context)

            mock_transporter.publish.assert_called_once()
            packet = mock_transporter.publish.call_args[0][0]
            assert packet.type == Topic.EVENT
            assert packet.target == "remote-node"
            assert packet.payload == {"event": "test.event", "data": "test"}

    @pytest.mark.asyncio
    async def test_message_handler_routing(self, mock_dependencies, mock_transporter):
        """Test Transit _message_handler routing to correct handlers."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            # Mock all handlers
            transit._handle_info = AsyncMock()
            transit._handle_discover = AsyncMock()
            transit._handle_heartbeat = AsyncMock()
            transit._handle_request = AsyncMock()
            transit._handle_response = AsyncMock()
            transit._handle_event = AsyncMock()
            transit._handle_disconnect = AsyncMock()

            # Test each packet type
            test_cases = [
                (Topic.INFO, transit._handle_info),
                (Topic.DISCOVER, transit._handle_discover),
                (Topic.HEARTBEAT, transit._handle_heartbeat),
                (Topic.REQUEST, transit._handle_request),
                (Topic.RESPONSE, transit._handle_response),
                (Topic.EVENT, transit._handle_event),
                (Topic.DISCONNECT, transit._handle_disconnect),
            ]

            for topic, handler in test_cases:
                packet = Packet(topic, None, {})
                await transit._message_handler(packet)
                handler.assert_called_once_with(packet)
                handler.reset_mock()

    @pytest.mark.asyncio
    async def test_message_handler_unknown_type(self, mock_dependencies, mock_transporter):
        """Test Transit _message_handler with unknown packet type."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            # Create a packet with invalid type (using a mock)
            packet = MagicMock()
            packet.type = MagicMock()
            packet.type.value = "UNKNOWN_TYPE"

            # Should log warning but not raise
            await transit._message_handler(packet)

            transit.logger.warning.assert_called_once()
            assert "Unknown packet type" in str(transit.logger.warning.call_args)

    @pytest.mark.asyncio
    async def test_message_handler_error_handling(self, mock_dependencies, mock_transporter):
        """Test Transit _message_handler error handling."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            # Make handler raise an error
            transit._handle_info = AsyncMock(side_effect=RuntimeError("Handler error"))

            packet = Packet(Topic.INFO, None, {})

            # Should log error but not raise
            await transit._message_handler(packet)

            transit.logger.error.assert_called_once()
            assert "Error handling INFO packet" in str(transit.logger.error.call_args)

    @pytest.mark.asyncio
    async def test_packet_sender_access_regression(self, mock_dependencies, mock_transporter):
        """Regression test: Transit handlers should access packet.sender without error."""
        # Previously, accessing packet.sender would raise AttributeError
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            # Test heartbeat handler
            packet = Packet(Topic.HEARTBEAT, "target", {"cpu": 45.0})
            packet.sender = "remote-node"

            mock_node = MagicMock()
            transit.node_catalog.get_node.return_value = mock_node

            # Should not raise AttributeError
            await transit._handle_heartbeat(packet)
            transit.node_catalog.get_node.assert_called_once_with("remote-node")
            assert mock_node.cpu == 45.0

    @pytest.mark.asyncio
    async def test_node_field_mapping_regression(self, mock_dependencies, mock_transporter):
        """Regression test: Transit should handle legacy field names in node info."""
        # Previously, Node constructor would fail with legacy field names like 'ipList'
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            # Create packet with legacy field names (like from Moleculer.js nodes)
            packet = Packet(
                Topic.INFO,
                "target",
                {
                    "id": "remote-node",
                    "ipList": ["192.168.1.100", "10.0.0.100"],  # Legacy field name
                    "instanceID": "instance-456",  # Legacy field name
                    "services": [{"name": "test-service"}],
                    "cpu": 35.5,
                    "available": True,
                },
            )
            packet.sender = "remote-node"

            # Should not raise TypeError about unexpected keyword arguments
            await transit._handle_info(packet)

            # Verify the node was added to catalog
            transit.node_catalog.add_node.assert_called_once()
            call_args = transit.node_catalog.add_node.call_args
            assert call_args[0][0] == "remote-node"

            # Verify the created node has correct attributes
            created_node = call_args[0][1]
            assert isinstance(created_node, Node)
            assert created_node.id == "remote-node"
            assert created_node.ipList == ["192.168.1.100", "10.0.0.100"]
            assert created_node.instanceID == "instance-456"
            assert created_node.cpu == 35.5

    @pytest.mark.asyncio
    async def test_node_field_filtering_regression(self, mock_dependencies, mock_transporter):
        """Regression test: Transit should filter out invalid Node constructor fields."""
        with patch("pylecular.transit.Transporter.get_by_name", return_value=mock_transporter):
            transit = Transit(**mock_dependencies)

            # Create packet with mix of valid and invalid field names
            packet = Packet(
                Topic.INFO,
                "target",
                {
                    "id": "remote-node",
                    "ipList": ["192.168.1.200"],  # Should be mapped to ip_list
                    "hostname": "remote-host",  # Should be preserved as valid field
                    "cpu": 42.0,  # Should be preserved as valid field
                    "customField": "custom-value",  # Should be filtered out (invalid)
                    "instanceID": "inst-789",  # Should be mapped to instance_id
                    "unknownProperty": "unknown-value",  # Should be filtered out (invalid)
                },
            )
            packet.sender = "remote-node"

            # Should not raise TypeError about unexpected keyword arguments
            await transit._handle_info(packet)

            # Verify the node was added
            transit.node_catalog.add_node.assert_called_once()
            created_node = transit.node_catalog.add_node.call_args[0][1]

            # Check mapped fields
            assert created_node.ipList == ["192.168.1.200"]
            assert created_node.instanceID == "inst-789"

            # Check preserved valid fields
            assert created_node.hostname == "remote-host"
            assert created_node.cpu == 42.0

            # Invalid fields should not cause errors (they're filtered out)
