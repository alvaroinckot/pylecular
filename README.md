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