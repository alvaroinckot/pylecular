# Pylecular

Pylecular is a Python library that implements the [Moleculer](https://moleculer.services/) protocol, enabling microservices communication and orchestration.

## Status

🚧 **Early Development**: Pylecular is in alpha stage and under active development. Currently, it supports basic Moleculer protocol features and only includes NATS transport integration. The API is not stable, and breaking changes are expected. Use with caution in production environments.

## Features

- Basic implementation of the Moleculer protocol.
- Support for service-to-service communication.
- Extensible and modular design.

## Installation

You can install Pylecular using pip:

```bash
pip install pylecular
```

For development installation, you can clone the repository and install in editable mode:

```bash
git clone https://github.com/alvaroinckot/pylecular.git
cd pylecular
pip install -e .
```

## Usage

### Basic Usage - Python API

```python
import asyncio
from pylecular.broker import Broker
from pylecular.service import Service
from pylecular.decorators import action
from pylecular.context import Context

# Define a service
class GreeterService(Service):
    name = "greeter"

    def __init__(self):
        super().__init__(self.name)

    @action(params=["name"])
    async def hello(self, ctx: Context):
        name = ctx.params.get("name", "World")
        return f"Hello, {name}!"

async def main():
    # Create a broker
    broker = Broker("my-node")

    # Register the service
    broker.register(GreeterService())

    # Start the broker
    await broker.start()

    # Make a call
    result = await broker.call("greeter.hello", {"name": "John"})
    print(result)  # Outputs: Hello, John!

    # Wait for termination
    await broker.wait_for_shutdown()

# Run the main function
asyncio.run(main())
```

### Command Line Interface

Pylecular includes a command line interface (CLI) that allows you to easily start a broker and load services from a directory:

```bash
pylecular <service_directory> [options]
```

#### CLI Options

- `service_directory`: Path to the directory containing service files
- `--broker-id, -b`: Broker ID (default: node-<current_dir_name>)
- `--transporter, -t`: Transporter URL (default: nats://localhost:4222)
- `--log-level, -l`: Log level (default: INFO)
- `--log-format, -f`: Log format (options: PLAIN, JSON) (default: PLAIN)
- `--namespace, -n`: Service namespace (default: default)

#### Example:

```bash
# Start a broker with services from the 'services' directory
pylecular services

# Start with a custom broker ID and transporter
pylecular services -b my-broker -t nats://nats-server:4222

# Use verbose logging
pylecular services -l DEBUG
```

The CLI will:
1. Start a broker
2. Import and register all services found in the specified directory
3. Wait for requests
4. Gracefully shut down on SIGINT or SIGTERM signals (Ctrl+C)

Here is a basic example of how to use Pylecular:

For more complete examples, check the `/examples` folder in the repository.
(The MathService example below seems to have some formatting and content issues compared to the GreeterService example above it, so it might be reviewed or removed in a future cleanup. For now, adding Middlewares section after it.)


```python
from pylecular.context import Context
from pylecular.service import Service
from pylecular.decorators import action, event
from pylecular.broker import Broker

broker = ServiceBroker("broker-sample") # Note: Should be Broker, not ServiceBroker

class MathService(Service):
    name = "math"

    def __init__(self):
        super().__init__(self.name)

    @action()
     def add(self, ctx):
          # Regular action
          result = ctx.params.get("a") + ctx.params.get("b")

          # Emit event to local listeners
          ctx.emit("calculation.done", {"operation": "add", "result": result})

          # Broadcast event to all nodes
          ctx.broadcast("calculation.completed", {"operation": "add", "result": result})

          return result

     @event(name="calculation.done")
     def calculation_done_handler(self, ctx):
          print(f"Calculation done: {ctx.params}")

broker.register(MathService())

await broker.start()

await broker.call("math.add", { "a": 5, "b": 20 })

```

## Middlewares

Middlewares in Pylecular provide a powerful way to extend the functionality of your services and broker by hooking into various stages of the request, event, and lifecycle processes. They are similar to plugins or interceptors in other frameworks, allowing you to execute custom logic, modify context, or manage resources.

### Creating Middlewares

To create a custom middleware, you inherit from `pylecular.middleware.Middleware` and implement the desired hook methods.

```python
from pylecular.middleware import Middleware
from pylecular.context import Context # For type hinting

class MyCustomMiddleware(Middleware):
    async def local_action(self, next_handler, action_endpoint):
        print(f"[MyCustomMiddleware] Before action: {action_endpoint.name}")
        
        async def wrapped_handler(ctx: Context):
            # Modify context before action execution
            ctx.meta['my_middleware_was_here'] = True
            print(f"[MyCustomMiddleware] Context meta updated for {action_endpoint.name}")
            
            result = await next_handler(ctx) # Call the next handler in the chain
            
            # Modify result after action execution
            if isinstance(result, dict):
                result['processed_by_my_middleware'] = True
            print(f"[MyCustomMiddleware] After action: {action_endpoint.name}, Result: {result}")
            return result
            
        return wrapped_handler

    def broker_created(self, broker): # This is a synchronous hook
        print(f"[MyCustomMiddleware] Broker '{broker.id}' has been created.")
```

### Available Hooks

Middleware hooks are methods you can define in your middleware class that Pylecular will call at specific points. They can be broadly categorized:

#### Wrapping Hooks

These hooks allow you to wrap around the execution of action and event handlers. They are called during the setup phase and should return a new handler function (the wrapper).

*   `local_action(self, next_handler, action_endpoint)`: Wraps local action handlers.
    *   `next_handler`: The next handler in the chain (or the original action handler). You must call `await next_handler(ctx)` within your wrapper.
    *   `action_endpoint`: An `ActionEndpoint` object containing metadata about the action (e.g., `name`, `service`).
*   `remote_action(self, next_handler, action_endpoint)`: Wraps remote action calls (i.e., before the request is sent by the transit).
    *   `next_handler`: The next handler, which typically performs the remote call (e.g., `await self.transit.request(...)`).
    *   `action_endpoint`: An `ActionEndpoint` object for the remote action.
*   `local_event(self, next_handler, event_endpoint)`: Wraps local event handlers.
    *   `next_handler`: The next handler in the chain (or the original event handler).
    *   `event_endpoint`: An `EventEndpoint` object containing metadata about the event.

#### Broker Lifecycle Hooks

These hooks are called at different stages of the Broker's lifecycle.

*   `broker_created(self, broker)`: Called **synchronously** immediately after the `Broker` instance is initialized.
    *   `broker`: The `Broker` instance.
*   `broker_started(self, broker)`: Called asynchronously after `await broker.start()` has completed its startup procedures (e.g., transit connected).
    *   `broker`: The `Broker` instance.
*   `broker_stopped(self, broker)`: Called asynchronously after `await broker.stop()` has completed its shutdown procedures (e.g., transit disconnected).
    *   `broker`: The `Broker` instance.

#### Service Lifecycle Hooks

These hooks are called when services are registered with the broker.

*   `service_created(self, service)`: Called asynchronously after a service is registered with the broker via `await broker.register(service)`.
    *   `service`: The `Service` instance that was registered.
*   `service_started(self, service)`: Called asynchronously immediately after `service_created` for a newly registered service.
    *   `service`: The `Service` instance.
*   `service_stopped(self, service)`: *(Note: This hook is defined in the base `Middleware` class but is not yet implemented in the `Broker`'s service unregistration flow, as service unregistration itself is not fully implemented.)*

### Registering Middlewares

You can register your middlewares with the `Broker` in two ways:

1.  **Directly to the Broker:**
    Pass a list of middleware instances to the `middlewares` argument of the `Broker` constructor.

    ```python
    from pylecular.broker import Broker
    # Assuming MyMiddleware1 and MyMiddleware2 are defined
    mw1 = MyMiddleware1()
    mw2 = MyMiddleware2()
    broker = Broker(id="my-node", middlewares=[mw1, mw2])
    ```

2.  **Via Settings Object:**
    Assign a list of middleware instances to the `middlewares` attribute of a `Settings` object, and then pass the settings to the `Broker`.

    ```python
    from pylecular.broker import Broker
    from pylecular.settings import Settings
    # Assuming MyMiddleware1 and MyMiddleware2 are defined
    mw1 = MyMiddleware1()
    mw2 = MyMiddleware2()
    settings = Settings(middlewares=[mw1, mw2])
    broker = Broker(id="my-node", settings=settings)
    ```
    If middlewares are provided both directly and via settings, the ones passed directly to the `Broker` constructor take precedence.

### Middleware Order

The order in which middlewares are registered matters, especially for wrapping hooks. Pylecular applies middlewares in a way that the **first middleware in the registration list becomes the outermost wrapper**, and the last one becomes the innermost.

For example, if you register `middlewares=[mw1, mw2]`:
*   `mw2`'s wrapping hook (e.g., `mw2.local_action`) is applied to the original handler first.
*   Then, `mw1`'s wrapping hook is applied to the handler returned by `mw2`.
*   So, the execution order of the wrappers themselves when an action is called will be: `mw1_wrapper_before` -> `mw2_wrapper_before` -> `original_action` -> `mw2_wrapper_after` -> `mw1_wrapper_after`.

### Runnable Example

For a practical, runnable demonstration of how to create and use various middleware hooks, please see the example file: `examples/middlewares_showcase.py`. This example includes logging and context enrichment middlewares to illustrate their effects on action calls and event emissions.

## Development

### Code Linting

Pylecular uses [Ruff](https://github.com/astral-sh/ruff) for code linting and formatting. Ruff is a fast Python linter that helps maintain code quality.

To set up development dependencies:

```bash
# Install development dependencies
pip install -e ".[dev]"
```

To lint your code:

```bash
# Check your code for linting issues
ruff check .

# Automatically fix many common issues
ruff check --fix .
```

### Pre-commit Hooks

To ensure code quality before each commit, Pylecular uses pre-commit hooks. These hooks will automatically check and fix your code before committing.

```bash
# Install pre-commit hooks
pre-commit install

# Run pre-commit hooks manually (optional)
pre-commit run --all-files
```

VS Code integration is included in the project settings. If you're using VS Code with the recommended extensions, you'll get:
- Real-time linting feedback as you type
- Automatic formatting on save
- Quick fixes for many common issues

The recommended VS Code extensions are:
- [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) - For linting and formatting
- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) - Python language support
- [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) - Fast type checking and language features

## Roadmap

- Add support for more Moleculer features.
- Improve documentation and examples.
- Enhance performance and stability.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to help improve Pylecular.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
