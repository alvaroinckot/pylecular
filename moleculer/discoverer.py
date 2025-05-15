import asyncio


class Discoverer:
    def __init__(self, broker):
        self.broker = broker
        self.transit = broker.transit
        self.__setup_timers__()

    def __setup_timers__(self):
        async def periodic_beat():
            while True:
                await asyncio.sleep(5)
                await self.transit.beat()
        asyncio.create_task(periodic_beat())


    # TODO: kill timers