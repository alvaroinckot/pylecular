"""Unit tests for the NATS transporter."""

from unittest.mock import AsyncMock, Mock

import pytest

from pylecular.packet import Packet, Topic
from pylecular.transporter.nats import NatsTransporter


class TestNatsTransporter:
    """Test NATS transporter functionality."""

    @pytest.mark.asyncio
    async def test_nats_transporter_sets_packet_sender_regression(self):
        """Regression test: NATS transporter should set sender attribute on packets."""
        # Previously, packets were missing the sender attribute which caused errors
        # in transit layer message handlers when accessing packet.sender

        # Mock NATS message
        mock_msg = Mock()
        mock_msg.subject = "MOL.HEARTBEAT.node123"
        mock_msg.data = b'{"sender": "remote-node", "cpu": 30.5}'

        # Create NATS transporter
        handler = AsyncMock()
        transporter = NatsTransporter(
            connection_string="nats://localhost:4222",
            transit=Mock(),
            handler=handler,
            node_id="local-node",
        )

        # Process the message
        await transporter.message_handler(mock_msg)

        # Check that handler was called with packet having sender set
        assert handler.called
        packet = handler.call_args[0][0]
        assert isinstance(packet, Packet)
        assert packet.sender == "remote-node"
        assert packet.type == Topic.HEARTBEAT
        assert packet.payload["cpu"] == 30.5

    @pytest.mark.asyncio
    async def test_nats_message_handler_creates_packet_with_sender_regression(self):
        """Regression test: Message handler should create packets with sender attribute."""
        # Mock NATS message with different packet types
        test_cases = [
            ("MOL.INFO.node1", b'{"sender": "info-node", "id": "test"}', Topic.INFO),
            ("MOL.HEARTBEAT.node2", b'{"sender": "beat-node", "cpu": 25}', Topic.HEARTBEAT),
            ("MOL.EVENT.node3", b'{"sender": "event-node", "event": "test"}', Topic.EVENT),
        ]

        for subject, data, expected_topic in test_cases:
            handler = AsyncMock()
            transporter = NatsTransporter(
                connection_string="nats://localhost:4222",
                transit=Mock(),
                handler=handler,
                node_id="local-node",
            )

            mock_msg = Mock()
            mock_msg.subject = subject
            mock_msg.data = data

            await transporter.message_handler(mock_msg)

            # Verify packet creation and sender attribute
            assert handler.called
            packet = handler.call_args[0][0]
            assert isinstance(packet, Packet)
            assert packet.type == expected_topic
            assert hasattr(packet, "sender")
            assert packet.sender is not None

            handler.reset_mock()
