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

```python
from pylecular import ServiceBroker, action

broker = ServiceBroker()

class MathService(Service):
    @action(params=None)
    def add(self, ctx):
        return ctx.params.get("a") + ctx.params.get("b")

broker.register(MathService())

broker.start()
```

## Roadmap

- Add support for more Moleculer features.
- Improve documentation and examples.
- Enhance performance and stability.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to help improve Pylecular.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.