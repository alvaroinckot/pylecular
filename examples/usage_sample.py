import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # import pylecular
from pylecular.context import Context
from pylecular.service import Service
from pylecular.decorators import action, event
from pylecular.broker import Broker
    
class MySyservice(Service):
    name = "myService"

    def __init__(self):
        super().__init__(self.name)

    # TODO: add validation
    @action(params=["param1", "param2"])
    async def foo(self, ctx: Context):
        return  100


    @action(params=[])
    async def bar(self, ctx: Context):
        a = await ctx.call("myService.foo", {}) # internal context call
        res = await ctx.call("math.add", { "a": a, "b": 50 }) # remote service call
        return res
    
    @event()
    async def checked(self, ctx: Context):
        print("checked called")

    @event(name="foo.bar.lol")
    async def complex_handler(self, ctx: Context):
        print("compled called")
    
    
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

    barREs = await broker.call("myService.bar", {})

    broker.logger.info(f"bar res is {barREs}")

    await broker.emit("checked", {})

    await broker.wait_for_shutdown()

asyncio.run(main())