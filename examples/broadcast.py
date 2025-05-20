import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # import pylecular
from pylecular.context import Context
from pylecular.service import Service
from pylecular.decorators import event
from pylecular.broker import Broker
    
class MySyservice(Service):
    name = "myService"

    def __init__(self):
        super().__init__(self.name)

    @event()
    async def checked(self, ctx: Context):
        print("checked ctx.id: " + ctx.id)
        await ctx.emit("done")
    
    @event()
    async def done(self, ctx: Context):
        print("done ctx.id: " + ctx.id)
        print("done called")

# Example usage
import asyncio

async def main():
    broker3 = Broker("broker-b3")
    await broker3.start()

    broker = Broker("broker-b1")
    mysvc = MySyservice()
    broker.register(mysvc)
    await broker.start()

    broker2 = Broker("broker-b2")
    mysvc2 = MySyservice()
    broker2.register(mysvc2)
    await broker2.start()


    await asyncio.sleep(1)

    await broker3.wait_for_services(["myService"])


    await broker3.broadcast("checked", {})

    await broker3.wait_for_shutdown()

asyncio.run(main())