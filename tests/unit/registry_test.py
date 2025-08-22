"""Unit tests for the Registry module."""

from unittest.mock import MagicMock, Mock

from pylecular.registry import Action, Event, Registry


class TestAction:
    """Test Action class."""

    def test_action_initialization(self):
        """Test Action initialization with all parameters."""
        handler = Mock()
        params_schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        action = Action(
            name="service.action",
            node_id="node-123",
            is_local=True,
            handler=handler,
            params_schema=params_schema,
        )

        assert action.name == "service.action"
        assert action.node_id == "node-123"
        assert action.is_local is True
        assert action.handler == handler
        assert action.params_schema == params_schema

    def test_action_minimal_initialization(self):
        """Test Action initialization with minimal parameters."""
        action = Action(name="service.action", node_id="node-123", is_local=False)

        assert action.name == "service.action"
        assert action.node_id == "node-123"
        assert action.is_local is False
        assert action.handler is None
        assert action.params_schema is None


class TestEvent:
    """Test Event class."""

    def test_event_initialization(self):
        """Test Event initialization with all parameters."""
        handler = Mock()

        event = Event(name="user.created", node_id="node-123", is_local=True, handler=handler)

        assert event.name == "user.created"
        assert event.node_id == "node-123"
        assert event.is_local is True
        assert event.handler == handler

    def test_event_minimal_initialization(self):
        """Test Event initialization with minimal parameters."""
        event = Event(name="user.created", node_id="node-123")

        assert event.name == "user.created"
        assert event.node_id == "node-123"
        assert event.is_local is False
        assert event.handler is None

    def test_event_default_is_local(self):
        """Test Event initialization with default is_local value."""
        event = Event(name="user.created", node_id="node-123", handler=Mock())

        assert event.is_local is False


class TestRegistry:
    """Test Registry class."""

    def test_registry_initialization(self):
        """Test Registry initialization."""
        logger = Mock()
        registry = Registry(node_id="node-123", logger=logger)

        assert registry.__node_id__ == "node-123"
        assert registry.__logger__ == logger
        assert registry.__services__ == {}
        assert registry.__actions__ == []
        assert registry.__events__ == []

    def test_registry_minimal_initialization(self):
        """Test Registry initialization without optional parameters."""
        registry = Registry()

        assert registry.__node_id__ is None
        assert registry.__logger__ is None
        assert registry.__services__ == {}
        assert registry.__actions__ == []
        assert registry.__events__ == []

    def test_register_service(self):
        """Test registering a service with actions and events."""
        registry = Registry(node_id="node-123", logger=Mock())

        # Create mock service
        service = MagicMock()
        service.name = "test-service"

        # Mock actions
        action1 = Mock()
        action1._name = "customAction"
        action1._params = {"type": "object"}

        action2 = Mock()
        # No _name attribute, should use method name
        del action2._name
        del action2._params

        service.actions.return_value = ["action1", "action2"]
        service.action1 = action1
        service.action2 = action2

        # Mock events
        event1 = Mock()
        event1._name = "custom.event"

        event2 = Mock()
        # No _name attribute, should use method name
        del event2._name

        service.events.return_value = ["event1", "event2"]
        service.event1 = event1
        service.event2 = event2

        # Register the service
        registry.register(service)

        # Check service registration
        assert registry.__services__["test-service"] == service

        # Check actions registration
        assert len(registry.__actions__) == 2
        assert registry.__actions__[0].name == "test-service.customAction"
        assert registry.__actions__[0].node_id == "node-123"
        assert registry.__actions__[0].is_local is True
        assert registry.__actions__[0].handler == action1
        assert registry.__actions__[0].params_schema == {"type": "object"}

        assert registry.__actions__[1].name == "test-service.action2"
        assert registry.__actions__[1].handler == action2
        assert registry.__actions__[1].params_schema is None

        # Check events registration
        assert len(registry.__events__) == 2
        assert registry.__events__[0].name == "custom.event"
        assert registry.__events__[0].node_id == "node-123"
        assert registry.__events__[0].is_local is True
        assert registry.__events__[0].handler == event1

        assert registry.__events__[1].name == "event2"
        assert registry.__events__[1].handler == event2

    def test_get_service(self):
        """Test getting a service by name."""
        registry = Registry()

        service1 = MagicMock()
        service1.name = "service1"
        service1.actions.return_value = []
        service1.events.return_value = []

        service2 = MagicMock()
        service2.name = "service2"
        service2.actions.return_value = []
        service2.events.return_value = []

        registry.register(service1)
        registry.register(service2)

        # Test getting existing services
        assert registry.get_service("service1") == service1
        assert registry.get_service("service2") == service2

        # Test getting non-existent service
        assert registry.get_service("nonexistent") is None

    def test_add_action(self):
        """Test adding an action directly."""
        registry = Registry()

        action = Action(name="service.action", node_id="node-123", is_local=False)

        registry.add_action(action)

        assert len(registry.__actions__) == 1
        assert registry.__actions__[0] == action

    def test_add_event(self):
        """Test adding an event by name and node_id."""
        registry = Registry()

        registry.add_event("user.created", "node-123")

        assert len(registry.__events__) == 1
        assert registry.__events__[0].name == "user.created"
        assert registry.__events__[0].node_id == "node-123"
        assert registry.__events__[0].is_local is False
        assert registry.__events__[0].handler is None

    def test_add_event_obj(self):
        """Test adding an event object directly."""
        registry = Registry()

        event = Event(name="user.created", node_id="node-123", is_local=True, handler=Mock())

        registry.add_event_obj(event)

        assert len(registry.__events__) == 1
        assert registry.__events__[0] == event

    def test_get_action(self):
        """Test getting an action by name."""
        registry = Registry()

        action1 = Action("service.action1", "node-1", True)
        action2 = Action("service.action2", "node-2", False)
        action3 = Action("other.action", "node-3", True)

        registry.add_action(action1)
        registry.add_action(action2)
        registry.add_action(action3)

        # Test getting existing actions
        assert registry.get_action("service.action1") == action1
        assert registry.get_action("service.action2") == action2
        assert registry.get_action("other.action") == action3

        # Test getting non-existent action
        assert registry.get_action("nonexistent.action") is None

    def test_get_action_returns_first_match(self):
        """Test that get_action returns the first matching action."""
        registry = Registry()

        # Add multiple actions with the same name (different nodes)
        action1 = Action("service.action", "node-1", True)
        action2 = Action("service.action", "node-2", False)

        registry.add_action(action1)
        registry.add_action(action2)

        # Should return the first one
        assert registry.get_action("service.action") == action1

    def test_get_all_events(self):
        """Test getting all events by name."""
        registry = Registry()

        # Add multiple events with same and different names
        event1 = Event("user.created", "node-1", True)
        event2 = Event("user.created", "node-2", False)
        event3 = Event("user.updated", "node-3", True)
        event4 = Event("user.created", "node-4", False)

        registry.add_event_obj(event1)
        registry.add_event_obj(event2)
        registry.add_event_obj(event3)
        registry.add_event_obj(event4)

        # Test getting all events with name 'user.created'
        user_created_events = registry.get_all_events("user.created")
        assert len(user_created_events) == 3
        assert event1 in user_created_events
        assert event2 in user_created_events
        assert event4 in user_created_events

        # Test getting all events with name 'user.updated'
        user_updated_events = registry.get_all_events("user.updated")
        assert len(user_updated_events) == 1
        assert event3 in user_updated_events

        # Test getting events with non-existent name
        nonexistent_events = registry.get_all_events("nonexistent.event")
        assert len(nonexistent_events) == 0

    def test_get_event(self):
        """Test getting the first event by name."""
        registry = Registry()

        # Add multiple events with same name
        event1 = Event("user.created", "node-1", True)
        event2 = Event("user.created", "node-2", False)
        event3 = Event("user.updated", "node-3", True)

        registry.add_event_obj(event1)
        registry.add_event_obj(event2)
        registry.add_event_obj(event3)

        # Should return the first matching event
        assert registry.get_event("user.created") == event1
        assert registry.get_event("user.updated") == event3

        # Test getting non-existent event
        assert registry.get_event("nonexistent.event") is None

    def test_register_service_without_logger(self):
        """Test registering a service without a logger."""
        registry = Registry(node_id="node-123")  # No logger

        service = MagicMock()
        service.name = "test-service"
        service.actions.return_value = []

        event_method = Mock()
        event_method._name = "test.event"
        service.events.return_value = ["event_method"]
        service.event_method = event_method

        # Should not raise any errors
        registry.register(service)

        assert len(registry.__events__) == 1
        assert registry.__events__[0].name == "test.event"

    def test_register_service_with_logger(self):
        """Test that events are logged when logger is present."""
        logger = Mock()
        registry = Registry(node_id="node-123", logger=logger)

        service = MagicMock()
        service.name = "test-service"
        service.actions.return_value = []

        event1 = Mock()
        event1._name = "event.one"
        event2 = Mock()
        event2._name = "event.two"

        service.events.return_value = ["event1", "event2"]
        service.event1 = event1
        service.event2 = event2

        registry.register(service)

        # Check that debug logs were made for each event
        assert logger.debug.call_count == 2

        call_args_list = [call[0][0] for call in logger.debug.call_args_list]
        assert "Event event.one from node node-123 (local=True)" in call_args_list
        assert "Event event.two from node node-123 (local=True)" in call_args_list

    def test_empty_registry_operations(self):
        """Test operations on an empty registry."""
        registry = Registry()

        # All get operations should return None or empty lists
        assert registry.get_service("any-service") is None
        assert registry.get_action("any.action") is None
        assert registry.get_event("any.event") is None
        assert registry.get_all_events("any.event") == []
