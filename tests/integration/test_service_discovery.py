"""Integration tests for service discovery between Python and Node.js."""

import asyncio
import sys

from pylecular.broker import ServiceBroker
from pylecular.decorators import action
from pylecular.service import Service
from pylecular.settings import Settings


class DiscoveryTestService(Service):
    name = "py-discovery"
    version = "1.0.0"

    def __init__(self):
        super().__init__(self.name)

    @action()
    async def ping(self, ctx):
        return {"pong": True, "node": ctx.broker.id}

    @action()
    async def list_nodes(self, ctx):
        nodes = ctx.broker.node_catalog.nodes
        return [{"id": node_id, "available": node.available} for node_id, node in nodes.items()]

    @action()
    async def list_services(self, ctx):
        # Access internal services dict
        services = ctx.broker.registry.__services__
        return [
            {"name": name, "version": getattr(svc, "version", "1.0.0")}
            for name, svc in services.items()
        ]

    @action()
    async def list_actions(self, ctx):
        # Access internal actions list
        actions = ctx.broker.registry.__actions__
        return [action.name for action in actions]


async def test_service_discovery():
    """Test service discovery and registry synchronization."""
    settings = Settings(transporter="nats://localhost:4222")
    broker = ServiceBroker(id="python-discovery-test", settings=settings)

    await broker.register(DiscoveryTestService())

    await broker.start()

    # Wait for discovery
    print("Waiting for service discovery...")
    await asyncio.sleep(5)

    results = {}

    try:
        # Check discovered nodes
        nodes = await broker.call("py-discovery.list_nodes")
        print(f"\n✓ Discovered {len(nodes)} nodes:")
        for node in nodes:
            print(f"  - {node['id']}: {'Available' if node['available'] else 'Unavailable'}")
        results["nodes_discovered"] = len(nodes)

        # Check discovered services
        services = await broker.call("py-discovery.list_services")
        print(f"\n✓ Discovered {len(services)} services:")
        for svc in services:
            print(f"  - {svc['name']} v{svc.get('version', 'unknown')}")
        results["services_discovered"] = len(services)

        # Check available actions
        actions = await broker.call("py-discovery.list_actions")
        print(f"\n✓ Discovered {len(actions)} actions:")
        for act in sorted(actions)[:10]:  # Show first 10
            print(f"  - {act}")
        if len(actions) > 10:
            print(f"  ... and {len(actions) - 10} more")
        results["actions_discovered"] = len(actions)

        # Test if Node.js math service is discovered
        if "math.add" in actions:
            print("\n✓ Node.js math service discovered")
            result = await broker.call("math.add", {"a": 1, "b": 2})
            print(f"  Test call result: {result}")
            results["node_service_callable"] = "PASSED"
        else:
            print("\n✗ Node.js math service not found")
            results["node_service_callable"] = "NOT_FOUND"

        # Test heartbeat/health
        ping_result = await broker.call("py-discovery.ping")
        print(f"\n✓ Self-ping successful: {ping_result}")
        results["self_ping"] = "PASSED"

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        results["error"] = str(e)
        return False
    finally:
        await broker.stop()

    print("\n=== Discovery Test Results ===")
    for test, status in results.items():
        print(f"{test}: {status}")

    success = (
        results.get("nodes_discovered", 0) >= 2  # At least Python and Node
        and results.get("services_discovered", 0) >= 2
        and results.get("actions_discovered", 0) > 0
        and results.get("self_ping") == "PASSED"
    )

    return success


if __name__ == "__main__":
    success = asyncio.run(test_service_discovery())
    sys.exit(0 if success else 1)
