import asyncio
import signal
from pylecular.context import Context
from pylecular.discoverer import Discoverer
from pylecular.packets import Packet, Packets
from pylecular.registry import Registry 
from pylecular.transit import Transit

class Broker:
    def __init__(self, id):
        self.id = id
        self.registry = Registry()
        self.transit = Transit(broker=self)
        self.discoverer = Discoverer(broker=self)


    async def start(self):
        await self.transit.connect()

    async def stop(self):
        await self.transit.disconnect()

    async def wait_for_shutdown(self):
        loop = asyncio.get_event_loop()
        shutdown_event = asyncio.Event()

        def signal_handler():
            shutdown_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

        await shutdown_event.wait()
        await self.stop()

    def register(self, service):
        self.registry.register(service)

    async def __call_unbalanced__(self, action_name, *args):
        await self.transit.request({
            "action": action_name,
            "args": args
        })

    async def call(self, action_name, *args):
        await self.__call_unbalanced__(action_name, *args)

    async def emit(self, event_name, *args): # TODO: emit with transit 
        endpoint = self.registry.get_event(event_name)
        if endpoint:
            ctx = Context.build()
            endpoint(ctx, *args) # emit vs broadcast to all nodes logic
        
