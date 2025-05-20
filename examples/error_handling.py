#!/usr/bin/env python3
import asyncio
import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)  # Add pylecular to path

from pylecular.broker import Broker
from pylecular.context import Context
from pylecular.decorators import action
from pylecular.service import Service


class ErrorService(Service):
    name = "error"

    def __init__(self):
        super().__init__(self.name)

    @action()
    async def throw_value_error(self, ctx: Context):
        """Throws a ValueError to demonstrate error handling."""
        raise ValueError("This is a sample error from the service")

    @action()
    async def throw_custom_error(self, ctx: Context):
        """Throws a custom error type."""

        class CustomServiceError(Exception):
            pass

        raise CustomServiceError("This is a custom error type")

    @action()
    async def success(self, ctx: Context):
        """Returns a successful response."""
        return {"status": "success", "message": "This action completed successfully"}

    @action()
    async def call_with_error_handling(self, ctx: Context):
        """Demonstrates how to handle errors when calling another service."""
        try:
            # This will fail
            result = await ctx.call("error.throw_value_error")
            return {"status": "success", "result": result}
        except Exception as e:
            return {
                "status": "error",
                "error_type": e.__class__.__name__,
                "error_message": str(e),
                "handled": True,
            }


async def main():
    # Create a broker
    broker = Broker("error-example")

    # Create and register our service
    error_service = ErrorService()
    broker.register(error_service)

    # Start the broker
    print("Starting broker...")
    await broker.start()

    print("\n1. Calling a successful action:")
    try:
        result = await broker.call("error.success")
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print("\n2. Calling an action that throws a ValueError:")
    try:
        result = await broker.call("error.throw_value_error")
        print(f"Success: {result}")
    except ValueError as e:
        print(f"✅ Caught ValueError as expected: {e}")
    except Exception as e:
        print(f"❌ Caught unexpected error type: {type(e).__name__}: {e}")

    print("\n3. Calling an action that throws a custom error:")
    try:
        result = await broker.call("error.throw_custom_error")
        print(f"Success: {result}")
    except Exception as e:
        print(f"✅ Caught exception: {type(e).__name__}: {e}")

    print("\n4. Calling an action that handles errors internally:")
    try:
        result = await broker.call("error.call_with_error_handling")
        print(f"✅ Action handled the error: {result}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print("\n5. Calling a non-existent action:")
    try:
        result = await broker.call("error.does_not_exist")
        print(f"Success: {result}")
    except Exception as e:
        print(f"✅ Caught expected error for non-existent action: {type(e).__name__}: {e}")

    # If this were a real example with remote services, you could also demonstrate
    # remote error handling here by connecting to other nodes

    print("\nShutting down...")
    await broker.stop()


if __name__ == "__main__":
    asyncio.run(main())
