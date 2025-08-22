"""Unit tests for the Lifecycle module."""

import uuid
from unittest.mock import Mock

import pytest

from pylecular.context import Context
from pylecular.lifecycle import Lifecycle


class TestLifecycle:
    """Test Lifecycle class."""

    @pytest.fixture
    def mock_broker(self):
        """Create a mock service broker."""
        return Mock()

    def test_lifecycle_initialization(self, mock_broker):
        """Test Lifecycle initialization."""
        lifecycle = Lifecycle(mock_broker)

        assert lifecycle.broker == mock_broker

    def test_create_context_minimal(self, mock_broker):
        """Test creating a context with minimal parameters."""
        lifecycle = Lifecycle(mock_broker)

        context = lifecycle.create_context()

        assert isinstance(context, Context)
        assert context.broker == mock_broker
        assert context.id is not None
        assert uuid.UUID(context.id)  # Should be valid UUID string
        assert context.action is None
        assert context.event is None
        assert context.parent_id is None
        assert context.params == {}
        assert context.meta == {}
        assert context.stream is False

    def test_create_context_with_string_id(self, mock_broker):
        """Test creating a context with string ID."""
        lifecycle = Lifecycle(mock_broker)

        context = lifecycle.create_context(context_id="custom-id-123")

        assert context.id == "custom-id-123"
        assert isinstance(context, Context)

    def test_create_context_with_uuid_id(self, mock_broker):
        """Test creating a context with UUID ID."""
        lifecycle = Lifecycle(mock_broker)
        test_uuid = uuid.uuid4()

        context = lifecycle.create_context(context_id=test_uuid)

        assert context.id == str(test_uuid)
        assert isinstance(context, Context)

    def test_create_context_full_parameters(self, mock_broker):
        """Test creating a context with all parameters."""
        lifecycle = Lifecycle(mock_broker)

        params = {"name": "test", "value": 42}
        meta = {"source": "test", "timestamp": 1234567890}

        context = lifecycle.create_context(
            context_id="ctx-123",
            event="user.created",
            action="user.create",
            parent_id="parent-ctx-456",
            params=params,
            meta=meta,
            stream=True,
        )

        assert context.id == "ctx-123"
        assert context.event == "user.created"
        assert context.action == "user.create"
        assert context.parent_id == "parent-ctx-456"
        assert context.params == params
        assert context.meta == meta
        assert context.stream is True
        assert context.broker == mock_broker

    def test_create_context_action_only(self, mock_broker):
        """Test creating a context with action only."""
        lifecycle = Lifecycle(mock_broker)

        context = lifecycle.create_context(action="user.create", params={"name": "John Doe"})

        assert context.action == "user.create"
        assert context.event is None
        assert context.params == {"name": "John Doe"}

    def test_create_context_event_only(self, mock_broker):
        """Test creating a context with event only."""
        lifecycle = Lifecycle(mock_broker)

        context = lifecycle.create_context(event="user.created", params={"userId": 123})

        assert context.event == "user.created"
        assert context.action is None
        assert context.params == {"userId": 123}

    def test_rebuild_context_minimal(self, mock_broker):
        """Test rebuilding a context with minimal data."""
        lifecycle = Lifecycle(mock_broker)

        context_dict = {}

        context = lifecycle.rebuild_context(context_dict)

        assert isinstance(context, Context)
        assert context.broker == mock_broker
        assert uuid.UUID(context.id)  # Should generate a new UUID
        assert context.action is None
        assert context.event is None
        assert context.parent_id is None
        assert context.params == {}
        assert context.meta == {}
        assert context.stream is False

    def test_rebuild_context_with_id(self, mock_broker):
        """Test rebuilding a context with existing ID."""
        lifecycle = Lifecycle(mock_broker)

        context_dict = {"id": "rebuilt-ctx-123"}

        context = lifecycle.rebuild_context(context_dict)

        assert context.id == "rebuilt-ctx-123"

    def test_rebuild_context_full_data(self, mock_broker):
        """Test rebuilding a context with complete data."""
        lifecycle = Lifecycle(mock_broker)

        params = {"userId": 456, "email": "test@example.com"}
        meta = {"requestId": "req-789", "clientIP": "192.168.1.1"}

        context_dict = {
            "id": "rebuilt-ctx-123",
            "action": "user.update",
            "event": "user.updated",
            "parent_id": "parent-ctx-789",
            "params": params,
            "meta": meta,
            "stream": True,
        }

        context = lifecycle.rebuild_context(context_dict)

        assert context.id == "rebuilt-ctx-123"
        assert context.action == "user.update"
        assert context.event == "user.updated"
        assert context.parent_id == "parent-ctx-789"
        assert context.params == params
        assert context.meta == meta
        assert context.stream is True
        assert context.broker == mock_broker

    def test_rebuild_context_partial_data(self, mock_broker):
        """Test rebuilding a context with partial data."""
        lifecycle = Lifecycle(mock_broker)

        context_dict = {
            "id": "partial-ctx-123",
            "action": "user.get",
            "params": {"userId": 789},
            # Missing event, parent_id, meta, stream
        }

        context = lifecycle.rebuild_context(context_dict)

        assert context.id == "partial-ctx-123"
        assert context.action == "user.get"
        assert context.params == {"userId": 789}
        assert context.event is None
        assert context.parent_id is None
        assert context.meta == {}
        assert context.stream is False  # Default value

    def test_rebuild_context_preserves_stream_false(self, mock_broker):
        """Test rebuilding a context preserves explicit stream=False."""
        lifecycle = Lifecycle(mock_broker)

        context_dict = {"id": "stream-false-ctx", "stream": False}

        context = lifecycle.rebuild_context(context_dict)

        assert context.stream is False

    def test_rebuild_context_converts_id_to_string(self, mock_broker):
        """Test rebuilding a context converts various ID types to string."""
        lifecycle = Lifecycle(mock_broker)

        # Test with integer ID (should be converted to string)
        context_dict = {"id": 12345}
        context = lifecycle.rebuild_context(context_dict)
        assert context.id == "12345"

        # Test with UUID ID (should be converted to string)
        test_uuid = uuid.uuid4()
        context_dict = {"id": test_uuid}
        context = lifecycle.rebuild_context(context_dict)
        assert context.id == str(test_uuid)

    def test_create_and_rebuild_consistency(self, mock_broker):
        """Test that creating and rebuilding contexts maintain consistency."""
        lifecycle = Lifecycle(mock_broker)

        # Create a context
        original_params = {"test": "value"}
        original_meta = {"key": "data"}

        original_context = lifecycle.create_context(
            context_id="consistency-test",
            action="test.action",
            event="test.event",
            parent_id="parent-123",
            params=original_params,
            meta=original_meta,
            stream=True,
        )

        # Simulate marshalling (getting dict representation)
        context_dict = {
            "id": original_context.id,
            "action": original_context.action,
            "event": original_context.event,
            "parent_id": original_context.parent_id,
            "params": original_context.params,
            "meta": original_context.meta,
            "stream": original_context.stream,
        }

        # Rebuild the context
        rebuilt_context = lifecycle.rebuild_context(context_dict)

        # Check that all attributes match
        assert rebuilt_context.id == original_context.id
        assert rebuilt_context.action == original_context.action
        assert rebuilt_context.event == original_context.event
        assert rebuilt_context.parent_id == original_context.parent_id
        assert rebuilt_context.params == original_context.params
        assert rebuilt_context.meta == original_context.meta
        assert rebuilt_context.stream == original_context.stream
        assert rebuilt_context.broker == original_context.broker

    def test_unique_context_ids(self, mock_broker):
        """Test that creating multiple contexts generates unique IDs."""
        lifecycle = Lifecycle(mock_broker)

        context1 = lifecycle.create_context()
        context2 = lifecycle.create_context()
        context3 = lifecycle.create_context()

        # All IDs should be different
        assert context1.id != context2.id
        assert context2.id != context3.id
        assert context1.id != context3.id

        # All should be valid UUIDs
        uuid.UUID(context1.id)
        uuid.UUID(context2.id)
        uuid.UUID(context3.id)
