# Pylecular

Pylecular is a Python library that implements the [Moleculer](https://moleculer.services/) protocol, enabling microservices communication and orchestration.

## Status

🚧 **Early Development**: Pylecular is in alpha stage and under active development. Currently, it supports basic Moleculer protocol features and only includes NATS transport integration. The API is not stable, and breaking changes are expected. Use with caution in production environments.

## Features

- Basic implementation of the Moleculer protocol.
- Support for service-to-service communication.
- Extensible and modular design.

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

For more complete examples, check the `/examples` folder in the repository:


```python
from pylecular.context import Context
from pylecular.service import Service
from pylecular.decorators import action, event
from pylecular.broker import Broker

broker = ServiceBroker("broker-sample")

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

## Roadmap

- Add support for more Moleculer features.
- Improve documentation and examples.
- Enhance performance and stability.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to help improve Pylecular.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
