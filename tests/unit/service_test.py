from pylecular.decorators import action, event
from pylecular.service import Service


class MyService(Service):
    name = "myService"

    @action()
    def say_hello(self):
        return "hello"
    
    @event()
    def receive(self, ctx):
        return f"Received: {ctx}"
    
    def __internal(self):
        return "internal"

    # Test actions with different schema types
    @action(params=["param1", "param2"])
    def with_list_params(self, ctx):
        return "list params"
    
    @action(params={"name": "string", "age": "number"})
    def with_dict_params(self, ctx):
        return "dict params"
    
    @action(params={
        "email": {"type": "string", "pattern": r".*@.*\..*"},
        "active": {"type": "boolean", "required": True}
    })
    def with_complex_params(self, ctx):
        return "complex params"


def test_service_init():
    s = Service("auth", settings={"foo": "bar"})
    assert s.name == "auth"
    assert s.settings == {"foo": "bar"}
    assert s.metadata == {}

def test_service_default_settings():
    s = Service("test")
    assert s.settings == {}

def test_actions_returns_callable_attrs():
    s = MyService("test")
    actions = s.actions()
    assert "say_hello" in actions
    assert "__internal" not in actions  # because it doesn't start with __
    assert "actions" not in actions
    assert "events" not in actions

def test_events_returns_callable_attrs():
    s = MyService("test")
    events = s.events()
    assert "receive" in events
    assert "say_hello" not in events
    assert "__internal" not in events  # because it doesn't start with __
    assert "actions" not in events
    assert "events" not in events

def test_action_preserves_params_schema():
    """Test that the action decorator properly stores the params schema."""
    s = MyService("test")
    
    # Check that the simple params list is preserved
    list_params_fn = s.with_list_params
    assert hasattr(list_params_fn, "_is_action")
    assert list_params_fn._is_action is True
    assert hasattr(list_params_fn, "_params")
    assert list_params_fn._params == ["param1", "param2"]
    
    # Check that the simple dict params are preserved
    dict_params_fn = s.with_dict_params
    assert hasattr(dict_params_fn, "_is_action")
    assert dict_params_fn._params == {"name": "string", "age": "number"}
    
    # Check that complex params schema is preserved
    complex_params_fn = s.with_complex_params
    assert hasattr(complex_params_fn, "_is_action")
    assert "email" in complex_params_fn._params
    assert "pattern" in complex_params_fn._params["email"]
    assert complex_params_fn._params["active"]["required"] is True

