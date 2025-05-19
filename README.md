# Pylecular

Pylecular is a Python library that implements the [Moleculer](https://moleculer.services/) protocol, enabling microservices communication and orchestration. 

## Status

🚧 **Alpha Stage**: Pylecular is currently in its early development phase. It does not yet support all features of the Moleculer protocol. Expect breaking changes and limited functionality.

## Features

- Basic implementation of the Moleculer protocol.
- Support for service-to-service communication.
- Extensible and modular design.

## Installation

Pylecular is not yet available on PyPI. You can install it directly from the source:

```bash
git clone https://github.com/alvaroinckot/pylecular.git
cd pylecular
pip install .
```

## Usage


Here is a basic example of how to use Pylecular:

For more complete examples, check the `/examples` folder in the repository:


```python
from pylecular import ServiceBroker, action

broker = ServiceBroker()

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

     @event("calculation.done")
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