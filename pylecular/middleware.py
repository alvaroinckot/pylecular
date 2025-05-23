"""
Middleware Module for the Pylecular framework.

This module defines the Middleware base class that provides hooks for intercepting and
modifying behavior at various stages of the Pylecular lifecycle. Middleware can be used
for logging, authentication, request/response transformation, error handling, and more.

Each middleware method provides a specific hook point in the broker or service lifecycle.
"""
from typing import Any, Awaitable, Callable, TypeVar

# Define type variables for better type annotations
T = TypeVar("T")
HandlerType = Callable[[Any], Awaitable[T]]


class Middleware:
    """
    Base Middleware class that can be extended to intercept and modify Pylecular behavior.

    Middleware classes can implement any of these methods to hook into the framework's lifecycle:

    Handler hooks (to intercept actions and events):
    - local_action: Called when a local action is being set up
    - remote_action: Called when a remote action is being set up
    - local_event: Called when a local event is being set up

    Broker lifecycle hooks:
    - broker_created: Called synchronously when the broker is created
    - broker_started: Called asynchronously when the broker is started
    - broker_stopped: Called asynchronously when the broker is stopped

    Service lifecycle hooks:
    - service_created: Called asynchronously when a service is registered
    - service_started: Called asynchronously when a service is started
    - service_stopped: Called asynchronously when a service is stopped
    """

    async def local_action(self, next_handler: HandlerType, action: Any) -> HandlerType:
        """
        Hook for local action middleware processing.

        Args:
            next_handler: The next handler in the chain
            action: The action object being registered

        Returns:
            A wrapped handler that will be called when the action is invoked
        """

        async def handler(ctx: Any) -> Any:
            return await next_handler(ctx)

        return handler

    async def remote_action(self, next_handler: HandlerType, action: Any) -> HandlerType:
        """
        Hook for remote action middleware processing.

        Args:
            next_handler: The next handler in the chain
            action: The action object being registered

        Returns:
            A wrapped handler that will be called when the remote action is invoked
        """

        async def handler(ctx: Any) -> Any:
            return await next_handler(ctx)

        return handler

    async def local_event(self, next_handler: HandlerType, event: Any) -> HandlerType:
        """
        Hook for local event middleware processing.

        Args:
            next_handler: The next handler in the chain
            event: The event object being registered

        Returns:
            A wrapped handler that will be called when the event is emitted
        """

        async def handler(ctx: Any) -> Any:
            return await next_handler(ctx)

        return handler

    def broker_created(self, broker: Any) -> None:
        """
        Hook called synchronously when the broker is created.

        This is the only synchronous hook, as it's called from the Broker's __init__ method.

        Args:
            broker: The broker instance
        """
        pass

    async def broker_started(self, broker: Any) -> None:
        """
        Hook called asynchronously when the broker is started.

        Args:
            broker: The broker instance
        """
        pass

    async def broker_stopped(self, broker: Any) -> None:
        """
        Hook called asynchronously when the broker is stopped.

        Args:
            broker: The broker instance
        """
        pass

    async def service_created(self, service: Any) -> None:
        """
        Hook called asynchronously when a service is created.

        Args:
            service: The service instance
        """
        pass

    async def service_started(self, service: Any) -> None:
        """
        Hook called asynchronously when a service is started.

        Args:
            service: The service instance
        """
        pass

    async def service_stopped(self, service: Any) -> None:
        """
        Hook called asynchronously when a service is stopped.

        Args:
            service: The service instance
        """
        pass
