from pylecular.context import Context
from pylecular.service import Service
from pylecular.decorators import action
from pylecular.broker import Broker
    
class MySyservice(Service):
    name = "myService"

    def __init__(self):
        super().__init__(self.name)

    # TODO: add validation
    @action(params=["param1", "param2"])
    async def foo(self, ctx: Context):
        # print(f"Service {self.name} called with context {ctx.id} and params {ctx.params}")
        return  "100"

# Example usage
import asyncio

async def main():
    broker = Broker("broker1")

    mysvc = MySyservice()

    broker.register(mysvc)

    await broker.start()

    res = await broker.call("myService.foo", {"param1": "aaaa"})

    broker.logger.info(f"local res is {res}")

    broker.logger.info("waiting for services")

    await broker.wait_for_services(["math"])

    broker.logger.info("remote services ready")

    mathRes = await broker.call("math.add", {"a": 1, "b": 50 })

    broker.logger.info(f"math res is {mathRes}")

    await broker.wait_for_shutdown()

asyncio.run(main())