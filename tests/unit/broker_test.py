import pytest
import asyncio
import signal
import os
from unittest.mock import Mock, AsyncMock
from pylecular.broker import Broker
from pylecular.settings import Settings
from pylecular.service import Service
from pylecular.decorators import action, event
from pylecular.transit import Transit
from pylecular.registry import Registry
from pylecular.node import NodeCatalog
from pylecular.lifecycle import Lifecycle

class TestService(Service):
    def __init__(self):
        super().__init__(name="test")

    @action()
    async def hello(self, _):
        return "Hello!"

    @event()
    async def test_event(self, _):
        return "Event received"

    @event(name="custom.event")
    async def another_event(self, _):
        return "Custom event received"
    

@pytest.fixture(scope="function")
def mock_transit():
    transit = AsyncMock(spec=Transit)
    transit.connect = AsyncMock()
    transit.disconnect = AsyncMock()
    transit.transporter = Mock(name="mock_nats")
    return transit

@pytest.fixture
def mock_registry():
    registry = Mock(spec=Registry)
    registry.__services__ = {}
    return registry

@pytest.fixture
def mock_node_catalog():
    catalog = Mock(spec=NodeCatalog)
    catalog.nodes = Mock()
    return catalog

@pytest.fixture
def mock_lifecycle():
    return Mock(spec=Lifecycle)

@pytest.fixture
async def broker(mock_transit, mock_registry, mock_node_catalog, mock_lifecycle):
    # Create and set an event loop for the test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    settings = Settings(transporter="mock://localhost:4222")
    broker = Broker(
        "test-node",
        settings=settings,
        transit=mock_transit,
        registry=mock_registry,
        node_catalog=mock_node_catalog,
        lifecycle=mock_lifecycle
    )
    return broker

@pytest.mark.asyncio
async def test_broker_initialization(broker):
    broker_instance = await broker
    assert broker_instance.id == "test-node"
    assert broker_instance.version == "0.14.35"
    assert broker_instance.namespace == "default"
    assert broker_instance.registry is not None
    assert broker_instance.transit is not None
    

@pytest.mark.asyncio
async def test_broker_start(broker, mock_transit):
    broker_instance = await broker
    await broker_instance.start()


@pytest.mark.asyncio
async def test_broker_stop(broker, mock_transit):
    broker_instance = await broker
    await broker_instance.stop()


@pytest.mark.asyncio
async def test_broker_stop(broker, mock_transit):
    broker_instance = await broker
    await broker_instance.stop()
    mock_transit.disconnect.assert_called_once()

@pytest.mark.asyncio
async def test_broker_register_service(broker, mock_registry, mock_node_catalog):
    broker_instance = await broker
    service = TestService()
    broker_instance.register(service)
    mock_registry.register.assert_called_once_with(service)
    mock_node_catalog.ensure_local_node.assert_called_once()


@pytest.mark.asyncio
async def test_broker_call_local_action(broker, mock_registry, mock_lifecycle):
    endpoint = Mock(is_local=True)
    endpoint.handler = AsyncMock(return_value="result")
    mock_registry.get_action.return_value = endpoint
    
    context = Mock()
    mock_lifecycle.create_context.return_value = context
    
    broker_instance = await broker

    result = await broker_instance.call("test.hello", {"param": "value"})
    
    assert result == "result"
    mock_registry.get_action.assert_called_once_with("test.hello")
    endpoint.handler.assert_called_once_with(context)


@pytest.mark.asyncio
async def test_broker_call_remote_action(broker, mock_registry, mock_transit, mock_lifecycle):
    endpoint = Mock(is_local=False, node_id="remote-node")
    mock_registry.get_action.return_value = endpoint
    mock_transit.request.return_value = "remote result"
    
    context = Mock()
    mock_lifecycle.create_context.return_value = context
    
    broker_instance = await broker

    result = await broker_instance.call("remote.action")
    
    assert result == "remote result"
    mock_transit.request.assert_called_once_with(endpoint, context)


@pytest.mark.asyncio
async def test_broker_call_nonexistent_action(broker, mock_registry):
    broker_instance = await broker

    mock_registry.get_action.return_value = None
    with pytest.raises(Exception, match="Action nonexistent.action not found."):
        await broker_instance.call("nonexistent.action")

@pytest.mark.asyncio
async def test_broker_emit_local_event(broker, mock_registry, mock_lifecycle):
    endpoint = Mock(is_local=True)
    endpoint.handler = AsyncMock()
    mock_registry.get_event.return_value = endpoint
    
    context = Mock()
    mock_lifecycle.create_context.return_value = context
    
    broker_instance = await broker

    await broker_instance.emit("test_event", {"param": "value"})
    
    endpoint.handler.assert_called_once_with(context)


@pytest.mark.asyncio
async def test_broker_emit_remote_event(broker, mock_registry, mock_transit, mock_lifecycle):
    endpoint = Mock(is_local=False)
    mock_registry.get_event.return_value = endpoint
    
    context = Mock()
    mock_lifecycle.create_context.return_value = context

    broker_instance = await broker
    
    await broker_instance.emit("remote.event")
    
    mock_transit.send_event.assert_called_once_with(endpoint, context)

@pytest.mark.asyncio
async def test_broker_broadcast_event(broker, mock_registry, mock_transit, mock_lifecycle):
    local_endpoint = Mock(is_local=True)
    local_endpoint.handler = AsyncMock()
    remote_endpoint = Mock(is_local=False)
    
    mock_registry.get_all_events.return_value = [local_endpoint, remote_endpoint]
    
    context = Mock()
    mock_lifecycle.create_context.return_value = context
    
    broker_instance = await broker

    await broker_instance.broadcast("test_event")
    
    local_endpoint.handler.assert_called_once_with(context)
    mock_transit.send_event.assert_called_once_with(remote_endpoint, context)

@pytest.mark.asyncio
async def test_wait_for_services_found_locally(broker, mock_registry):
    mock_registry.get_service.return_value = Mock()
    broker_instance = await broker
    await broker_instance.wait_for_services(["test"])
    mock_registry.get_service.assert_called_once_with("test")

@pytest.mark.asyncio
async def test_wait_for_services_found_remotely(broker, mock_registry, mock_node_catalog):
    mock_registry.get_service.return_value = None
    remote_node = Mock()
    remote_node.id = "remote-node"
    remote_node.services = [{"name": "test"}]
    mock_node_catalog.nodes.values.return_value = [remote_node]
    broker_instance = await broker
    await broker_instance.wait_for_services(["test"])
