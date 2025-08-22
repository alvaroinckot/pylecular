"""Unit tests for the decorators module."""

from pylecular.decorators import action, event


class TestActionDecorator:
    """Test the action decorator."""

    def test_action_decorator_without_parameters(self):
        """Test action decorator without any parameters."""

        @action()
        def test_function():
            """Test function docstring."""
            return "test result"

        assert hasattr(test_function, "_is_action")
        assert test_function._is_action is True
        assert test_function._name == "test_function"
        assert test_function._params is None

        # Function should still be callable
        assert test_function() == "test result"
        assert test_function.__doc__ == "Test function docstring."

    def test_action_decorator_with_custom_name(self):
        """Test action decorator with custom name."""

        @action(name="custom.action.name")
        def my_function():
            return "custom action"

        assert my_function._is_action is True
        assert my_function._name == "custom.action.name"
        assert my_function._params is None
        assert my_function() == "custom action"

    def test_action_decorator_with_params_schema(self):
        """Test action decorator with parameter schema."""
        params_schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer", "minimum": 0}},
            "required": ["name"],
        }

        @action(params=params_schema)
        def user_action():
            return "user created"

        assert user_action._is_action is True
        assert user_action._name == "user_action"
        assert user_action._params == params_schema
        assert user_action() == "user created"

    def test_action_decorator_with_name_and_params(self):
        """Test action decorator with both name and params."""
        params_schema = {"type": "string"}

        @action(name="greet.user", params=params_schema)
        def greeting_function():
            return "Hello, World!"

        assert greeting_function._is_action is True
        assert greeting_function._name == "greet.user"
        assert greeting_function._params == params_schema
        assert greeting_function() == "Hello, World!"

    def test_action_decorator_preserves_function_metadata(self):
        """Test that action decorator preserves function metadata."""

        def original_function():
            """Original function documentation."""
            pass

        original_function.custom_attr = "custom_value"

        decorated = action(name="test.action")(original_function)

        # Should preserve original attributes
        assert decorated.__name__ == "original_function"
        assert decorated.__doc__ == "Original function documentation."
        assert decorated.custom_attr == "custom_value"

        # Should add decorator attributes
        assert decorated._is_action is True
        assert decorated._name == "test.action"

    def test_action_decorator_with_function_that_takes_parameters(self):
        """Test action decorator on function that takes parameters."""

        @action(name="calculate.sum")
        def add_numbers(a, b):
            """Add two numbers together."""
            return a + b

        assert add_numbers._is_action is True
        assert add_numbers._name == "calculate.sum"
        assert add_numbers(3, 4) == 7

    def test_action_decorator_with_async_function(self):
        """Test action decorator on async function."""

        @action(name="async.action")
        async def async_function():
            """Async function."""
            return "async result"

        assert async_function._is_action is True
        assert async_function._name == "async.action"
        # Note: We don't actually await the function in the test
        # just verify the decorator worked

    def test_action_decorator_none_name_uses_function_name(self):
        """Test that None name parameter uses function name."""

        @action(name=None)
        def test_function_name():
            return "result"

        assert test_function_name._name == "test_function_name"

    def test_action_decorator_empty_string_name(self):
        """Test action decorator with empty string name."""

        @action(name="")
        def function_with_empty_name():
            return "result"

        # Empty string should be used as is (not default to function name)
        assert function_with_empty_name._name == ""


class TestEventDecorator:
    """Test the event decorator."""

    def test_event_decorator_without_parameters(self):
        """Test event decorator without any parameters."""

        @event()
        def test_event_handler():
            """Test event handler docstring."""
            return "event handled"

        assert hasattr(test_event_handler, "_is_event")
        assert test_event_handler._is_event is True
        assert test_event_handler._name == "test_event_handler"
        assert test_event_handler._params is None

        # Function should still be callable
        assert test_event_handler() == "event handled"
        assert test_event_handler.__doc__ == "Test event handler docstring."

    def test_event_decorator_with_custom_name(self):
        """Test event decorator with custom name."""

        @event(name="user.created")
        def handle_user_creation():
            return "user creation handled"

        assert handle_user_creation._is_event is True
        assert handle_user_creation._name == "user.created"
        assert handle_user_creation._params is None
        assert handle_user_creation() == "user creation handled"

    def test_event_decorator_with_params_schema(self):
        """Test event decorator with parameter schema."""
        params_schema = {
            "type": "object",
            "properties": {"userId": {"type": "string"}, "timestamp": {"type": "number"}},
        }

        @event(params=params_schema)
        def user_event_handler():
            return "event processed"

        assert user_event_handler._is_event is True
        assert user_event_handler._name == "user_event_handler"
        assert user_event_handler._params == params_schema
        assert user_event_handler() == "event processed"

    def test_event_decorator_with_name_and_params(self):
        """Test event decorator with both name and params."""
        params_schema = {"type": "object"}

        @event(name="order.placed", params=params_schema)
        def order_handler():
            return "order processed"

        assert order_handler._is_event is True
        assert order_handler._name == "order.placed"
        assert order_handler._params == params_schema
        assert order_handler() == "order processed"

    def test_event_decorator_preserves_function_metadata(self):
        """Test that event decorator preserves function metadata."""

        def original_handler():
            """Original handler documentation."""
            pass

        original_handler.custom_property = "test_value"

        decorated = event(name="test.event")(original_handler)

        # Should preserve original attributes
        assert decorated.__name__ == "original_handler"
        assert decorated.__doc__ == "Original handler documentation."
        assert decorated.custom_property == "test_value"

        # Should add decorator attributes
        assert decorated._is_event is True
        assert decorated._name == "test.event"

    def test_event_decorator_with_function_that_takes_parameters(self):
        """Test event decorator on function that takes parameters."""

        @event(name="notification.send")
        def send_notification(message, recipient):
            """Send a notification."""
            return f"Sent '{message}' to {recipient}"

        assert send_notification._is_event is True
        assert send_notification._name == "notification.send"
        assert send_notification("Hello", "user@example.com") == "Sent 'Hello' to user@example.com"

    def test_event_decorator_with_async_function(self):
        """Test event decorator on async function."""

        @event(name="async.event")
        async def async_event_handler():
            """Async event handler."""
            return "async event handled"

        assert async_event_handler._is_event is True
        assert async_event_handler._name == "async.event"
        # Note: We don't actually await the function in the test

    def test_event_decorator_none_name_uses_function_name(self):
        """Test that None name parameter uses function name."""

        @event(name=None)
        def test_event_function():
            return "result"

        assert test_event_function._name == "test_event_function"

    def test_event_decorator_empty_string_name(self):
        """Test event decorator with empty string name."""

        @event(name="")
        def handler_with_empty_name():
            return "result"

        # Empty string should be used as is (not default to function name)
        assert handler_with_empty_name._name == ""


class TestDecoratorsInteraction:
    """Test interactions between decorators."""

    def test_function_can_have_both_action_and_event_decorators(self):
        """Test that a function can have both decorators (though not recommended)."""

        @action(name="dual.action")
        @event(name="dual.event")
        def dual_purpose_function():
            return "dual purpose"

        # Should have both sets of attributes
        assert dual_purpose_function._is_action is True
        assert dual_purpose_function._is_event is True
        assert hasattr(dual_purpose_function, "_name")  # Both decorators set this
        assert dual_purpose_function() == "dual purpose"

    def test_decorators_with_complex_schemas(self):
        """Test decorators with complex parameter schemas."""
        complex_schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                    },
                    "required": ["id", "name"],
                },
                "preferences": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["user"],
        }

        @action(name="user.update", params=complex_schema)
        def update_user():
            return "user updated"

        @event(name="user.updated", params=complex_schema)
        def handle_user_updated():
            return "user update handled"

        assert update_user._params == complex_schema
        assert handle_user_updated._params == complex_schema

    def test_decorators_return_same_function_object(self):
        """Test that decorators return the same function object (not a wrapper)."""

        def original_function():
            pass

        original_id = id(original_function)

        decorated_action = action()(original_function)
        decorated_event = event()(original_function)

        # Should be the same object with added attributes
        assert id(decorated_action) == original_id
        assert id(decorated_event) == original_id
        assert decorated_action is original_function
        assert decorated_event is original_function
