import asyncio


class Discoverer:
    def __init__(self, broker):
        self.broker = broker
        self.transit = broker.transit
        self._tasks = []
        self.__setup_timers__()

    def __setup_timers__(self):
        async def periodic_beat():
            try:
                while True:
                    await asyncio.sleep(5)
                    await self.transit.beat()
            except asyncio.CancelledError:
                # Handle task cancellation gracefully
                pass
        
        task = asyncio.create_task(periodic_beat())
        self._tasks.append(task)

    async def stop(self):
        """Cancel all running tasks created by this discoverer."""
        for task in self._tasks:
            if not task.done() and not task.cancelled():
                task.cancel()
                try:
                    # Wait for the task to be cancelled with a short timeout
                    await asyncio.wait_for(asyncio.shield(task), timeout=0.5)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    # Expected exceptions when cancelling a task
                    pass
        self._tasks.clear()