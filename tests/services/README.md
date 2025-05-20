# Test Services for Pylecular

This directory contains sample microservices for testing the Pylecular CLI command and framework.

## Available Services

1. **MathService** (`math_service.py`)
   - Simple arithmetic operations
   - Actions: add, subtract, multiply, divide

2. **GreeterService** (`greeter_service.py`)
   - Simple greeting service
   - Actions: hello, welcome, goodbye

3. **UserService** (`user_service.py`)
   - Basic CRUD operations for users
   - Actions: list, get, create, update, delete

4. **MonitorService** (`monitor_service.py`)
   - System monitoring and metrics
   - Actions: health, metrics, set_health

5. **ApiGatewayService** (`api_gateway_service.py`)
   - Gateway to access other services
   - Actions: call, services

## Running the Services

Use the `pylecular` command to run these services:

```bash
# Run all services in this directory
pylecular /path/to/tests/services

# Run with custom broker ID
pylecular /path/to/tests/services --broker-id my-broker

# Run with custom transporter
pylecular /path/to/tests/services --transporter nats://custom-host:4222

# Run with custom log level
pylecular /path/to/tests/services --log-level DEBUG
```

The services will be loaded, and the broker will wait for signal termination (Ctrl+C).

## Example Client Usage

You can interact with these services by creating a client that connects to the same broker:

```python
import asyncio
from pylecular.broker import Broker

async def run_client():
    # Create a client broker
    broker = Broker("client-1")
    await broker.start()
    
    # Call the math service
    result = await broker.call("math.add", {"a": 5, "b": 10})
    print(f"5 + 10 = {result}")
    
    # Call the greeter service
    greeting = await broker.call("greeter.hello", {"name": "Developer"})
    print(greeting)
    
    # Call through the API gateway
    api_result = await broker.call("api.call", {
        "service": "users", 
        "action": "list", 
        "params": {}
    })
    print(f"Users: {api_result}")
    
    await broker.stop()

asyncio.run(run_client())
```
