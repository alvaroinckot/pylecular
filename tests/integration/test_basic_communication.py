"""Basic communication integration tests between Python and Node.js services."""

import asyncio
import sys
import time

from pylecular.broker import ServiceBroker
from pylecular.decorators import action
from pylecular.service import Service
from pylecular.settings import Settings


class MathService(Service):
    name = "py-math"

    def __init__(self):
        super().__init__(self.name)

    @action()
    async def add(self, ctx):
        return ctx.params["a"] + ctx.params["b"]

    @action()
    async def multiply(self, ctx):
        return ctx.params["a"] * ctx.params["b"]


class GreeterService(Service):
    name = "py-greeter"

    def __init__(self):
        super().__init__(self.name)

    @action()
    async def hello(self, ctx):
        name = ctx.params.get("name", "World")
        return f"Hello {name} from Python!"

    @action()
    async def welcome(self, ctx):
        return {"message": "Welcome!", "timestamp": time.time()}


async def test_cross_platform_communication():
    """Test communication between Python and Node.js services."""
    settings = Settings(transporter="nats://localhost:4222")
    broker = ServiceBroker(id="python-test-node", settings=settings)

    await broker.register(MathService())
    await broker.register(GreeterService())

    await broker.start()

    # Wait for services to be discovered
    await asyncio.sleep(3)

    results = {}

    try:
        # Test calling Node.js math service from Python
        result = await broker.call("math.add", {"a": 10, "b": 20})
        print(f"✓ Called Node.js math.add: {result}")
        assert result == 30, f"Expected 30, got {result}"
        results["node_math_add"] = "PASSED"

        # Test Python service availability
        result = await broker.call("py-math.add", {"a": 5, "b": 7})
        print(f"✓ Called Python py-math.add: {result}")
        assert result == 12, f"Expected 12, got {result}"
        results["python_math_add"] = "PASSED"

        result = await broker.call("py-math.multiply", {"a": 3, "b": 4})
        print(f"✓ Called Python py-math.multiply: {result}")
        assert result == 12, f"Expected 12, got {result}"
        results["python_math_multiply"] = "PASSED"

        result = await broker.call("py-greeter.hello", {"name": "Integration Test"})
        print(f"✓ Called Python py-greeter.hello: {result}")
        assert "Integration Test" in result
        results["python_greeter_hello"] = "PASSED"

    except Exception as e:
        print(f"✗ Test failed: {e}")
        results["error"] = str(e)
        return False
    finally:
        await broker.stop()

    print("\n=== Integration Test Results ===")
    for test, status in results.items():
        print(f"{test}: {status}")

    return all(status == "PASSED" for status in results.values())


if __name__ == "__main__":
    success = asyncio.run(test_cross_platform_communication())
    sys.exit(0 if success else 1)
