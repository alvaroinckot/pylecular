#!/usr/bin/env python3
"""
Example client for testing Pylecular services.
This script demonstrates how to interact with the services started by the pylecular CLI.
"""

import asyncio
import os
import sys

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

from pylecular.broker import Broker


async def run_client():
    # Create a client broker
    broker = Broker("client-1")

    try:
        # Start the broker
        print("Starting client broker...")
        await broker.start()

        # Test math service
        print("\n----- Testing Math Service -----")
        addition = await broker.call("math.add", {"a": 5, "b": 10})
        print(f"5 + 10 = {addition}")

        subtraction = await broker.call("math.subtract", {"a": 15, "b": 7})
        print(f"15 - 7 = {subtraction}")

        product = await broker.call("math.multiply", {"a": 6, "b": 8})
        print(f"6 * 8 = {product}")

        quotient = await broker.call("math.divide", {"a": 20, "b": 4})
        print(f"20 / 4 = {quotient}")

        # Test greeter service
        print("\n----- Testing Greeter Service -----")
        greeting = await broker.call("greeter.hello", {"name": "Developer"})
        print(greeting)

        welcome = await broker.call("greeter.welcome", {"name": "Pylecular User"})
        print(welcome)

        goodbye = await broker.call("greeter.goodbye", {})
        print(goodbye)

        # Test user service
        print("\n----- Testing User Service -----")
        users = await broker.call("users.list", {})
        print(f"Users: {users}")

        user = await broker.call("users.get", {"id": "1"})
        print(f"User #1: {user}")

        new_user = await broker.call(
            "users.create", {"name": "Alice Wonder", "email": "alice@example.com"}
        )
        print(f"Created user: {new_user}")

        updated_user = await broker.call("users.update", {"id": "2", "name": "Jane Doe"})
        print(f"Updated user: {updated_user}")

        # Test monitor service
        print("\n----- Testing Monitor Service -----")
        health = await broker.call("monitor.health", {})
        print(f"System health: {health}")

        metrics = await broker.call("monitor.metrics", {})
        print(f"System metrics: {metrics}")

        # Test API gateway
        print("\n----- Testing API Gateway -----")
        services = await broker.call("api.services", {})
        print(f"Available services: {services}")

        gateway_result = await broker.call(
            "api.call", {"service": "math", "action": "add", "params": {"a": 42, "b": 58}}
        )
        print(f"API gateway call: {gateway_result}")

        # Test validation service
        print("\n----- Testing Validation Service -----")
        print("\nTesting simple validation (store):")
        try:
            store_result = await broker.call(
                "validators.store",
                {"id": "item1", "data": {"value": "Test data", "timestamp": "2025-05-20"}},
            )
            print(f"✅ Store successful: {store_result}")
        except Exception as e:
            print(f"❌ Store error: {e}")

        print("\nTesting type validation (retrieve):")
        try:
            retrieve_result = await broker.call(
                "validators.retrieve", {"id": "item1", "limit": 5, "detailed": True}
            )
            print(f"✅ Retrieve successful: {retrieve_result}")
        except Exception as e:
            print(f"❌ Retrieve error: {e}")

        # Try with invalid type
        try:
            invalid_retrieve = await broker.call(
                "validators.retrieve",
                {
                    "id": "item1",
                    "limit": "5",  # Should be a number
                    "detailed": True,
                },
            )
            print(f"❌ Invalid retrieve didn't fail: {invalid_retrieve}")
        except Exception as e:
            print(f"✅ Expected error on invalid type: {e}")

        print("\nTesting complex validation (register):")
        try:
            register_result = await broker.call(
                "validators.register",
                {
                    "user": {
                        "name": "John Smith",
                        "email": "john.smith@example.com",
                        "age": 28,
                        "preferences": {"theme": "dark", "notifications": True},
                    },
                    "role": "admin",
                    "permissions": ["read", "write", "delete"],
                },
            )
            print(f"✅ Register successful: {register_result}")
        except Exception as e:
            print(f"❌ Register error: {e}")

        # Try with invalid data
        try:
            invalid_register = await broker.call(
                "validators.register",
                {
                    "user": {
                        "name": "Jo",  # Too short, should be min 3 chars
                        "email": "invalid-email",  # Invalid email format
                        "age": 16,  # Too young, should be >= 18
                    },
                    "role": "superuser",  # Invalid role
                },
            )
            print(f"❌ Invalid register didn't fail: {invalid_register}")
        except Exception as e:
            print(f"✅ Expected error on invalid register: {e}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Stop the broker
        print("\nStopping client...")
        await broker.stop()


if __name__ == "__main__":
    asyncio.run(run_client())
