from unittest.mock import AsyncMock, Mock

import pytest

from pylecular.context import Context


@pytest.fixture
def mock_broker():
    broker = Mock()
    broker.call = AsyncMock(return_value="call_result")
    broker.emit = AsyncMock(return_value="emit_result")
    broker.broadcast = AsyncMock(return_value="broadcast_result")
    return broker


@pytest.fixture
def context(mock_broker):
    return Context(
        id="test-id",
        action="test.action",
        event="test.event",
        parent_id="parent-id",
        params={"key": "value"},
        meta={"meta_key": "meta_value"},
        stream=False,
        broker=mock_broker,
    )


def test_context_initialization(context):
    assert context.id == "test-id"
    assert context.action == "test.action"
    assert context.event == "test.event"
    assert context.parent_id == "parent-id"
    assert context.params == {"key": "value"}
    assert context.meta == {"meta_key": "meta_value"}
    assert context.stream is False
    assert context._broker is not None


def test_context_initialization_with_defaults():
    ctx = Context(id="test-id")
    assert ctx.id == "test-id"
    assert ctx.action is None
    assert ctx.event is None
    assert ctx.parent_id is None
    assert ctx.params == {}
    assert ctx.meta == {}
    assert ctx.stream is False
    assert ctx._broker is None


def test_marshall(context):
    marshalled = context.marshall()
    assert marshalled == {
        "id": "test-id",
        "action": "test.action",
        "event": "test.event",
        "params": {"key": "value"},
        "meta": {"meta_key": "meta_value"},
        "timeout": 0,
        "level": 1,
        "tracing": None,
        "parentID": "parent-id",
        "stream": False,
    }


def test_unmarshall(context):
    unmarshalled = context.unmarshall()
    assert unmarshalled == {
        "id": "test-id",
        "action": "test.action",
        "event": "test.event",
        "params": {"key": "value"},
        "meta": {"meta_key": "meta_value"},
        "timeout": 0,
        "level": 1,
        "tracing": None,
        "parentID": "parent-id",
        "stream": False,
    }


@pytest.mark.asyncio
async def test_prepare_meta(context):
    new_meta = {"new_key": "new_value"}
    result = await context._prepare_meta(new_meta)
    assert result == {"meta_key": "meta_value", "new_key": "new_value"}


@pytest.mark.asyncio
async def test_prepare_meta_empty(context):
    result = await context._prepare_meta()
    assert result == {"meta_key": "meta_value"}


@pytest.mark.asyncio
async def test_call(context, mock_broker):
    params = {"param_key": "param_value"}
    meta = {"meta_key": "new_meta_value"}

    result = await context.call("service.action", params, meta)

    assert result == "call_result"
    mock_broker.call.assert_called_once_with(
        "service.action", {"param_key": "param_value"}, {"meta_key": "new_meta_value"}
    )


@pytest.mark.asyncio
async def test_emit(context, mock_broker):
    params = {"param_key": "param_value"}
    meta = {"meta_key": "new_meta_value"}

    result = await context.emit("event", params, meta)

    assert result == "emit_result"
    mock_broker.emit.assert_called_once_with("event", {"param_key": "param_value"})


@pytest.mark.asyncio
async def test_broadcast(context, mock_broker):
    params = {"param_key": "param_value"}
    meta = {"meta_key": "new_meta_value"}

    result = await context.broadcast("event", params, meta)

    assert result == "broadcast_result"
    mock_broker.broadcast.assert_called_once_with("event", {"param_key": "param_value"})


@pytest.mark.asyncio
async def test_call_without_broker(context):
    context._broker = None
    with pytest.raises(AttributeError):
        await context.call("service.action")


@pytest.mark.asyncio
async def test_emit_without_broker(context):
    context._broker = None
    with pytest.raises(AttributeError):
        await context.emit("service.event")


@pytest.mark.asyncio
async def test_broadcast_without_broker(context):
    context._broker = None
    with pytest.raises(AttributeError):
        await context.broadcast("service.event")
