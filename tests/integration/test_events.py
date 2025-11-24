"""Integration tests for event broadcasting between Python and Node.js services."""

import asyncio
import sys
import time

from pylecular.broker import ServiceBroker
from pylecular.decorators import action, event
from pylecular.service import Service
from pylecular.settings import Settings


class EventEmitterService(Service):
    name = "py-event-emitter"

    def __init__(self):
        super().__init__(self.name)

    @action()
    async def trigger_event(self, ctx):
        event_name = ctx.params.get("event", "test.event")
        data = ctx.params.get("data", {"source": "python"})
        await ctx.emit(event_name, data)
        return {"emitted": event_name, "data": data}


class EventListenerService(Service):
    name = "py-event-listener"

    def __init__(self):
        super().__init__(self.name)
        self.received_events = []

    @event("test.**")
    async def handle_test_event(self, ctx):
        self.received_events.append(
            {"event": ctx.event_name, "data": ctx.params, "timestamp": time.time()}
        )
        print(f"  Received event: {ctx.event_name} with data: {ctx.params}")

    @event("node.event")
    async def handle_node_event(self, ctx):
        self.received_events.append(
            {"event": "node.event", "data": ctx.params, "timestamp": time.time()}
        )
        print(f"  Received Node.js event with data: {ctx.params}")

    @action()
    async def get_events(self, ctx):
        return self.received_events


async def test_event_broadcasting():
    """Test event broadcasting between Python and Node.js services."""
    settings = Settings(transporter="nats://localhost:4222")
    broker = ServiceBroker(id="python-event-test", settings=settings)

    await broker.register(EventEmitterService())
    await broker.register(EventListenerService())

    await broker.start()

    # Wait for services to be discovered
    await asyncio.sleep(3)

    results = {}

    try:
        # Test emitting events from Python
        print("Testing Python event emission...")
        await broker.call(
            "py-event-emitter.trigger_event",
            {"event": "test.python.emit", "data": {"message": "Hello from Python"}},
        )

        # Wait for event propagation
        await asyncio.sleep(1)

        # Emit broadcast event
        print("Broadcasting event...")
        await broker.broadcast("test.broadcast", {"broadcast": True, "source": "python"})

        # Wait for event propagation
        await asyncio.sleep(1)

        # Check received events
        events = await broker.call("py-event-listener.get_events")
        print(f"\n✓ Received {len(events)} events")
        for evt in events:
            print(f"  - {evt['event']}: {evt['data']}")

        results["event_emission"] = "PASSED" if len(events) > 0 else "FAILED"

        # Test Node.js event reception (if Node service emits events)
        print("\nWaiting for Node.js events...")
        await asyncio.sleep(2)

        final_events = await broker.call("py-event-listener.get_events")
        print(f"✓ Total events received: {len(final_events)}")

        results["total_events"] = len(final_events)

    except Exception as e:
        print(f"✗ Test failed: {e}")
        results["error"] = str(e)
        return False
    finally:
        await broker.stop()

    print("\n=== Event Test Results ===")
    for test, status in results.items():
        print(f"{test}: {status}")

    return results.get("event_emission") == "PASSED"


if __name__ == "__main__":
    success = asyncio.run(test_event_broadcasting())
    sys.exit(0 if success else 1)
