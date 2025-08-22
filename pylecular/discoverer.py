"""Service discovery mechanism for the Pylecular framework.

This module provides the Discoverer class which handles periodic heartbeat
broadcasting to maintain cluster topology awareness.
"""

import asyncio
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .broker import ServiceBroker
    from .transit import Transit


class Discoverer:
    """Handles service discovery and cluster topology maintenance.

    The Discoverer manages periodic heartbeat broadcasts to announce
    node presence and maintain awareness of the cluster topology.
    """

    HEARTBEAT_INTERVAL = 5.0  # seconds

    def __init__(self, broker: "ServiceBroker") -> None:
        """Initialize the discoverer.

        Args:
            broker: Service broker instance
        """
        self.broker = broker
        self.transit: Transit = broker.transit
        self._tasks: List[asyncio.Task] = []
        self._setup_timers()

    def _setup_timers(self) -> None:
        """Set up periodic tasks for service discovery."""

        async def periodic_beat() -> None:
            """Send periodic heartbeat broadcasts."""
            try:
                while True:
                    await asyncio.sleep(self.HEARTBEAT_INTERVAL)
                    await self.transit.beat()
            except asyncio.CancelledError:
                # Task cancellation is expected during shutdown
                pass
            except Exception as e:
                # Log the error but don't stop the heartbeat
                if hasattr(self.broker, "logger"):
                    self.broker.logger.error(f"Error in periodic beat: {e}")

        # Create and track the heartbeat task
        task = asyncio.create_task(periodic_beat())
        task.set_name("discoverer-heartbeat")
        self._tasks.append(task)

    async def stop(self) -> None:
        """Stop the discoverer and cancel all running tasks.

        This method gracefully cancels all tasks created by the discoverer
        and waits for them to complete or timeout.
        """
        if not self._tasks:
            return

        # Cancel all tasks
        for task in self._tasks:
            if not task.done() and not task.cancelled():
                task.cancel()

        # Wait for all tasks to complete with timeout
        if self._tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._tasks, return_exceptions=True), timeout=1.0
                )
            except asyncio.TimeoutError:
                # Some tasks didn't finish in time, but that's acceptable
                pass
            except Exception:
                # Ignore exceptions from cancelled tasks
                pass
            finally:
                self._tasks.clear()
