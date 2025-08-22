"""Unit tests for the packet module."""

import pytest

from pylecular.packet import Packet, Topic


class TestTopic:
    """Test Topic enum."""

    def test_topic_enum_values(self):
        """Test that Topic enum has correct values."""
        assert Topic.HEARTBEAT.value == "HEARTBEAT"
        assert Topic.EVENT.value == "EVENT"
        assert Topic.DISCONNECT.value == "DISCONNECT"
        assert Topic.DISCOVER.value == "DISCOVER"
        assert Topic.INFO.value == "INFO"
        assert Topic.REQUEST.value == "REQ"
        assert Topic.RESPONSE.value == "RES"

    def test_topic_enum_membership(self):
        """Test Topic enum membership."""
        all_topics = [
            Topic.HEARTBEAT,
            Topic.EVENT,
            Topic.DISCONNECT,
            Topic.DISCOVER,
            Topic.INFO,
            Topic.REQUEST,
            Topic.RESPONSE,
        ]

        for topic in all_topics:
            assert isinstance(topic, Topic)

    def test_topic_enum_comparison(self):
        """Test Topic enum comparison."""
        assert Topic.REQUEST == Topic.REQUEST
        assert Topic.REQUEST != Topic.RESPONSE
        assert Topic.EVENT != Topic.HEARTBEAT

    def test_topic_enum_string_representation(self):
        """Test Topic enum string representation."""
        assert str(Topic.REQUEST) == "Topic.REQUEST"
        assert repr(Topic.HEARTBEAT) == "<Topic.HEARTBEAT: 'HEARTBEAT'>"


class TestPacket:
    """Test Packet class."""

    def test_packet_initialization(self):
        """Test Packet initialization."""
        payload = {"message": "test", "data": 123}
        packet = Packet(Topic.REQUEST, "target-node", payload)

        assert packet.type == Topic.REQUEST
        assert packet.target == "target-node"
        assert packet.payload == payload

    def test_packet_with_none_target(self):
        """Test Packet with None target."""
        payload = {"broadcast": True}
        packet = Packet(Topic.DISCOVER, None, payload)

        assert packet.type == Topic.DISCOVER
        assert packet.target is None
        assert packet.payload == payload

    def test_packet_with_empty_payload(self):
        """Test Packet with empty payload."""
        packet = Packet(Topic.HEARTBEAT, "node-123", {})

        assert packet.type == Topic.HEARTBEAT
        assert packet.target == "node-123"
        assert packet.payload == {}

    def test_packet_with_none_payload(self):
        """Test Packet with None payload."""
        packet = Packet(Topic.DISCONNECT, "node-456", None)

        assert packet.type == Topic.DISCONNECT
        assert packet.target == "node-456"
        assert packet.payload is None

    def test_packet_with_complex_payload(self):
        """Test Packet with complex payload."""
        complex_payload = {
            "user": {"id": 123, "name": "John Doe", "preferences": ["email", "sms"]},
            "action": "user.create",
            "metadata": {"timestamp": 1234567890, "source": "web"},
        }

        packet = Packet(Topic.EVENT, "user-service", complex_payload)

        assert packet.type == Topic.EVENT
        assert packet.target == "user-service"
        assert packet.payload == complex_payload

    def test_packet_with_list_payload(self):
        """Test Packet with list payload."""
        list_payload = ["item1", "item2", "item3"]
        packet = Packet(Topic.INFO, "collector", list_payload)

        assert packet.type == Topic.INFO
        assert packet.target == "collector"
        assert packet.payload == list_payload

    def test_packet_with_string_payload(self):
        """Test Packet with string payload."""
        string_payload = "Simple string message"
        packet = Packet(Topic.RESPONSE, "client", string_payload)

        assert packet.type == Topic.RESPONSE
        assert packet.target == "client"
        assert packet.payload == string_payload

    def test_packet_with_numeric_payload(self):
        """Test Packet with numeric payload."""
        packet_int = Packet(Topic.HEARTBEAT, "monitor", 42)
        packet_float = Packet(Topic.HEARTBEAT, "monitor", 3.14)

        assert packet_int.payload == 42
        assert packet_float.payload == 3.14


class TestPacketFromTopic:
    """Test Packet.from_topic static method."""

    def test_from_topic_valid_topics(self):
        """Test from_topic with valid topic strings."""
        test_cases = [
            ("prefix.HEARTBEAT.suffix", Topic.HEARTBEAT),
            ("MOL.EVENT.node123", Topic.EVENT),
            ("system.DISCONNECT", Topic.DISCONNECT),
            ("discovery.DISCOVER.broadcast", Topic.DISCOVER),
            ("info.INFO.local", Topic.INFO),
            ("request.REQ.action", Topic.REQUEST),
            ("response.RES.result", Topic.RESPONSE),
        ]

        for topic_string, expected_topic in test_cases:
            result = Packet.from_topic(topic_string)
            assert result == expected_topic

    def test_from_topic_minimal_format(self):
        """Test from_topic with minimal topic format."""
        # Minimum format: "prefix.TOPIC"
        result = Packet.from_topic("prefix.HEARTBEAT")
        assert result == Topic.HEARTBEAT

        result = Packet.from_topic("x.EVENT")
        assert result == Topic.EVENT

    def test_from_topic_case_sensitive(self):
        """Test that from_topic is case sensitive."""
        # Should work with correct case
        result = Packet.from_topic("prefix.REQ.suffix")
        assert result == Topic.REQUEST

        # Should fail with incorrect case
        with pytest.raises(ValueError, match="Unknown topic type: req"):
            Packet.from_topic("prefix.req.suffix")

        with pytest.raises(ValueError, match="Unknown topic type: Req"):
            Packet.from_topic("prefix.Req.suffix")

    def test_from_topic_empty_string(self):
        """Test from_topic with empty string."""
        with pytest.raises(ValueError, match="Topic string cannot be empty"):
            Packet.from_topic("")

    def test_from_topic_none_input(self):
        """Test from_topic with None input."""
        with pytest.raises(ValueError, match="Topic string cannot be empty"):
            Packet.from_topic(None)

    def test_from_topic_invalid_format_single_part(self):
        """Test from_topic with single part (invalid format)."""
        with pytest.raises(ValueError, match="Invalid topic format: HEARTBEAT"):
            Packet.from_topic("HEARTBEAT")

    def test_from_topic_invalid_format_no_topic_part(self):
        """Test from_topic with missing topic part."""
        with pytest.raises(ValueError, match="Invalid topic format: prefix"):
            Packet.from_topic("prefix")

        with pytest.raises(ValueError, match="Unknown topic type: "):
            Packet.from_topic(".")

    def test_from_topic_unknown_topic_type(self):
        """Test from_topic with unknown topic type."""
        with pytest.raises(ValueError, match="Unknown topic type: UNKNOWN"):
            Packet.from_topic("prefix.UNKNOWN.suffix")

        with pytest.raises(ValueError, match="Unknown topic type: INVALID"):
            Packet.from_topic("system.INVALID")

    def test_from_topic_empty_topic_part(self):
        """Test from_topic with empty topic part."""
        with pytest.raises(ValueError, match="Unknown topic type: "):
            Packet.from_topic("prefix..suffix")

        with pytest.raises(ValueError, match="Unknown topic type: "):
            Packet.from_topic("prefix.")

    def test_from_topic_with_extra_dots(self):
        """Test from_topic with many dot-separated parts."""
        # Should still work - only second part matters
        result = Packet.from_topic("a.HEARTBEAT.c.d.e.f.g.h")
        assert result == Topic.HEARTBEAT

        result = Packet.from_topic("complex.EVENT.node.service.action.params")
        assert result == Topic.EVENT

    def test_from_topic_special_characters_in_prefix_suffix(self):
        """Test from_topic with special characters in prefix/suffix."""
        # Topic type parsing should work regardless of prefix/suffix content
        result = Packet.from_topic("node-123.DISCONNECT.service_name")
        assert result == Topic.DISCONNECT

        result = Packet.from_topic("@@#$.INFO.%^&*()")
        assert result == Topic.INFO

    def test_from_topic_numeric_parts(self):
        """Test from_topic with numeric parts."""
        result = Packet.from_topic("123.REQ.456")
        assert result == Topic.REQUEST

        result = Packet.from_topic("0.RES.999")
        assert result == Topic.RESPONSE

    def test_from_topic_edge_cases(self):
        """Test from_topic with various edge cases."""
        # Multiple consecutive dots
        with pytest.raises(ValueError, match="Unknown topic type: "):
            Packet.from_topic("prefix...HEARTBEAT")

        # Starting/ending with dots
        result = Packet.from_topic(".DISCOVER.suffix")
        assert result == Topic.DISCOVER

        # Very long topic string
        long_prefix = "a" * 1000
        long_suffix = "b" * 1000
        result = Packet.from_topic(f"{long_prefix}.EVENT.{long_suffix}")
        assert result == Topic.EVENT


class TestPacketIntegration:
    """Test integration between Packet and Topic."""

    def test_packet_creation_with_all_topic_types(self):
        """Test creating packets with all topic types."""
        topics_and_payloads = [
            (Topic.HEARTBEAT, {"cpu": 25.5, "memory": 60.2}),
            (Topic.EVENT, {"event": "user.created", "userId": 123}),
            (Topic.DISCONNECT, {"reason": "shutdown"}),
            (Topic.DISCOVER, {}),
            (Topic.INFO, {"services": ["auth", "user"], "version": "1.0"}),
            (Topic.REQUEST, {"action": "user.get", "params": {"id": 456}}),
            (Topic.RESPONSE, {"success": True, "data": {"name": "John"}}),
        ]

        for topic, payload in topics_and_payloads:
            packet = Packet(topic, "test-node", payload)
            assert packet.type == topic
            assert packet.target == "test-node"
            assert packet.payload == payload

    def test_packet_from_topic_round_trip(self):
        """Test that from_topic can parse topics that match enum values."""
        for topic in Topic:
            topic_string = f"prefix.{topic.value}.suffix"
            parsed_topic = Packet.from_topic(topic_string)
            assert parsed_topic == topic

            # Create packet with parsed topic
            packet = Packet(parsed_topic, "node", {"test": True})
            assert packet.type == topic

    def test_packet_sender_attribute_regression(self):
        """Regression test: Ensure packet has sender attribute to prevent AttributeError."""
        # Previously, packets were missing the sender attribute which caused errors
        # in transit layer message handlers when accessing packet.sender
        packet = Packet(Topic.INFO, "target-node", {"test": "data"})

        # Should have sender attribute (initially None)
        assert hasattr(packet, "sender")
        assert packet.sender is None

    def test_packet_sender_can_be_set_regression(self):
        """Regression test: Ensure packet sender attribute can be set."""
        packet = Packet(Topic.HEARTBEAT, "target-node", {"cpu": 25.0})
        packet.sender = "source-node"

        assert packet.sender == "source-node"

    def test_packet_sender_attribute_all_topics_regression(self):
        """Regression test: All packet types should support sender attribute."""
        test_cases = [
            Topic.HEARTBEAT,
            Topic.EVENT,
            Topic.DISCONNECT,
            Topic.DISCOVER,
            Topic.INFO,
            Topic.REQUEST,
            Topic.RESPONSE,
        ]

        for topic in test_cases:
            packet = Packet(topic, "target", {"test": "data"})

            # Should be able to set sender without error
            packet.sender = f"sender-for-{topic.value}"
            assert packet.sender == f"sender-for-{topic.value}"

            # Should be able to access sender without error
            sender_value = packet.sender
            assert sender_value is not None
