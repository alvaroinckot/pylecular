
from abc import ABC, abstractmethod
import importlib

class Transporter(ABC):
    def __init__(self, name):
        self.name = name
        
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def publish(self):
        pass

    @abstractmethod
    async def subscribe(self, command, topic):
        pass

    @classmethod
    def get_by_name(cls, name: str, config: dict, transit, handler=None) -> "Transporter":
        importlib.import_module("pylecular.transporter.nats")  # import all possible implementations here

        for subclass in cls.__subclasses__():
            if subclass.__name__.lower().startswith(name.lower()):
                return subclass.from_config(config, transit, handler)
        raise ValueError(f"No transporter found for: {name}")

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict, transit, handler=None) -> "Transporter":
        pass

