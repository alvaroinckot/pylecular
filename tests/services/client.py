#!/usr/bin/env python3
"""
Example client for testing Pylecular services.
This script demonstrates how to interact with the services started by the pylecular CLI.
"""

import asyncio
import sys
import os
import time

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

from pylecular.broker import Broker
from pylecular.settings import Settings


async def run_client():
    # Create a client broker
    broker = Broker("client-1")
    
    print("Starting client...\n")
    await broker.start()
    
    try:
        # Wait for services to become available
        print("Waiting for services to be available...")
        await asyncio.sleep(1)  # Give services time to register
        
        # Test math service
        print("\n----- Testing Math Service -----")
        result = await broker.call("math.add", {"a": 5, "b": 10})
        print(f"5 + 10 = {result}")
        
        result = await broker.call("math.subtract", {"a": 20, "b": 8})
        print(f"20 - 8 = {result}")
        
        result = await broker.call("math.multiply", {"a": 6, "b": 7})
        print(f"6 * 7 = {result}")
        
        result = await broker.call("math.divide", {"a": 100, "b": 5})
        print(f"100 / 5 = {result}")
        
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
        
        new_user = await broker.call("users.create", {"name": "Alice Wonder", "email": "alice@example.com"})
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
        
        gateway_result = await broker.call("api.call", {
            "service": "math", 
            "action": "add", 
            "params": {"a": 42, "b": 58}
        })
        print(f"API gateway call: {gateway_result}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Stop the broker
        print("\nStopping client...")
        await broker.stop()


if __name__ == "__main__":
    asyncio.run(run_client())
