from moleculer.context import Context
from moleculer.service import Service
from moleculer.decorators import action
from moleculer.broker import Broker
    
class MySyservice(Service):
    name = "myService"

    def __init__(self):
        super().__init__(self.name)

    # TODO: add validation
    @action(params=["param1", "param2"])
    def foo(self, ctx: Context):
        print(f"Service {self.name} called with context {ctx.id} and params {ctx.params}")
        return  "100"

# Example usage
import asyncio

async def main():
    broker = Broker("broker1")

    mysvc = MySyservice()

    broker.register(mysvc)

    await broker.start()

    await broker.call("myService.foo", {"param1": "aaaa"})

    await broker.wait_for_shutdown()

asyncio.run(main())