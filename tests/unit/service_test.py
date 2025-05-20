from pylecular.service import Service
from pylecular.decorators import action, event


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

