"""Service broker implementation for the Pylecular framework.

This module provides the main ServiceBroker class which orchestrates all aspects
of the microservices framework including service registration, discovery,
communication, and lifecycle management.
"""

import asyncio
import signal
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

if TYPE_CHECKING:
    from .context import Context
    from .middleware import Middleware
    from .service import Service

from .discoverer import Discoverer
from .lifecycle import Lifecycle
from .logger import get_logger
from .node import NodeCatalog
from .registry import Registry
from .settings import Settings
from .transit import Transit


# For backwards compatibility, alias ServiceBroker as Broker
class ServiceBroker:
    """Main service broker for orchestrating microservices.

    The ServiceBroker is the central component that manages:
    - Service registration and discovery
    - Inter-service communication (calls, events, broadcasts)
    - Node topology and clustering
    - Middleware pipeline execution
    - Lifecycle management
    """

    def __init__(
        self,
        id: str,
        settings: Optional[Settings] = None,
        version: str = "0.14.35",
        namespace: str = "default",
        lifecycle: Optional[Lifecycle] = None,
        registry: Optional[Registry] = None,
        node_catalog: Optional[NodeCatalog] = None,
        transit: Optional[Transit] = None,
        discoverer: Optional[Discoverer] = None,
        middlewares: Optional[List["Middleware"]] = None,
    ) -> None:
        """Initialize the service broker.

        Args:
            id: Unique identifier for this node
            settings: Configuration settings
            version: Pylecular framework version
            namespace: Logical namespace for service isolation
            lifecycle: Custom lifecycle manager
            registry: Custom service registry
            node_catalog: Custom node catalog
            transit: Custom transit layer
            discoverer: Custom service discoverer
            middlewares: List of middleware instances
        """
        self.id = id
        self.settings = settings or Settings()
        self.version = version
        self.namespace = namespace

        # Initialize middleware system
        self.middlewares = self._initialize_middlewares(middlewares)

        # Initialize logger
        self.logger = get_logger(self.settings.log_level, self.settings.log_format).bind(
            node=self.id, service="BROKER", level=self.settings.log_level
        )

        # Initialize core components
        self.lifecycle = lifecycle or Lifecycle(broker=self)
        self.registry = registry or Registry(node_id=self.id, logger=self.logger)
        self.node_catalog = node_catalog or NodeCatalog(
            logger=self.logger, node_id=self.id, registry=self.registry
        )
        self.transit = transit or Transit(
            settings=self.settings,
            node_id=self.id,
            registry=self.registry,
            node_catalog=self.node_catalog,
            lifecycle=self.lifecycle,
            logger=self.logger,
        )
        self.discoverer = discoverer or Discoverer(broker=self)

        # Call middleware broker_created hooks
        self._call_middleware_hooks("broker_created", self, is_async=False)

    def _initialize_middlewares(
        self, middlewares: Optional[List["Middleware"]]
    ) -> List["Middleware"]:
        """Initialize middleware list from various sources.

        Args:
            middlewares: Directly provided middlewares

        Returns:
            List of middleware instances
        """
        if middlewares is not None:
            return middlewares
        elif hasattr(self.settings, "middlewares") and self.settings.middlewares:
            return self.settings.middlewares
        else:
            return []

    def _call_middleware_hooks(
        self, hook_name: str, *args: Any, is_async: bool = True
    ) -> Optional[List[Any]]:
        """Call middleware hooks with proper async handling.

        Args:
            hook_name: Name of the hook method to call
            *args: Arguments to pass to the hook
            is_async: Whether to handle async hooks

        Returns:
            List of coroutines if is_async=True, None otherwise
        """
        if is_async:
            coroutines = []
            for middleware in self.middlewares:
                hook = getattr(middleware, hook_name, None)
                if hook and callable(hook):
                    result = hook(*args)
                    if asyncio.iscoroutine(result):
                        coroutines.append(result)
            return coroutines if coroutines else None
        else:
            # Synchronous hooks
            for middleware in self.middlewares:
                hook = getattr(middleware, hook_name, None)
                if hook and callable(hook):
                    hook(*args)
            return None

    async def start(self) -> None:
        """Start the service broker and establish cluster connectivity."""
        self.logger.info(f"Pylecular v{self.version} is starting...")
        self.logger.info(f"Namespace: {self.namespace}")
        self.logger.info(f"Node ID: {self.id}")
        self.logger.info(f"Transporter: {self.transit.transporter.name}")

        # Connect to the cluster
        await self.transit.connect()

        service_count = len(self.registry.__services__)
        self.logger.info(f"Service broker with {service_count} services started successfully")

        # Call async middleware hooks
        coroutines = self._call_middleware_hooks("broker_started", self)
        if coroutines:
            await asyncio.gather(*coroutines, return_exceptions=True)

    async def stop(self) -> None:
        """Stop the service broker and cleanup resources."""
        self.logger.info("Stopping service broker...")

        # Stop discoverer first to cancel periodic tasks
        if hasattr(self.discoverer, "stop"):
            await self.discoverer.stop()

        # Disconnect from the cluster
        await self.transit.disconnect()

        # Call async middleware hooks
        coroutines = self._call_middleware_hooks("broker_stopped", self)
        if coroutines:
            await asyncio.gather(*coroutines, return_exceptions=True)

        self.logger.info("Service broker stopped successfully")

    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signals and stop the broker gracefully."""
        loop = asyncio.get_event_loop()
        shutdown_event = asyncio.Event()

        def signal_handler() -> None:
            self.logger.info("Received shutdown signal")
            shutdown_event.set()

        # Register signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

        await shutdown_event.wait()
        await self.stop()

    async def wait_for_services(self, services: List[str]) -> None:
        """Wait for specific services to become available.

        Args:
            services: List of service names to wait for
        """
        if not services:
            return

        self.logger.info(f"Waiting for services: {', '.join(services)}")

        while True:
            missing_services = []

            for service_name in services:
                # Check local services first
                local_service = self.registry.get_service(service_name)
                if local_service:
                    continue

                # Check remote services
                found_remote = False
                for node in self.node_catalog.nodes.values():
                    if node.id != self.id:
                        for service_obj in node.services:
                            if service_obj.get("name") == service_name:
                                found_remote = True
                                break
                        if found_remote:
                            break

                if not found_remote:
                    missing_services.append(service_name)

            if not missing_services:
                self.logger.info("All required services are available")
                return

            await asyncio.sleep(0.1)

    async def register(self, service: "Service") -> None:
        """Register a service with the broker.

        Args:
            service: Service instance to register
        """
        self.logger.info(f"Registering service: {service.name}")

        # Register with registry and update local node
        self.registry.register(service)
        self.node_catalog.ensure_local_node()

        # Call middleware hooks for service lifecycle
        coroutines = self._call_middleware_hooks("service_created", service)
        if coroutines:
            await asyncio.gather(*coroutines, return_exceptions=True)

        coroutines = self._call_middleware_hooks("service_started", service)
        if coroutines:
            await asyncio.gather(*coroutines, return_exceptions=True)

        self.logger.info(f"Service {service.name} registered successfully")

    async def _apply_middlewares(
        self, handler: Callable, hook_name: str, metadata: Any
    ) -> Callable:
        """Apply middleware transformations to a handler.

        Args:
            handler: Original handler function
            hook_name: Middleware hook name to apply
            metadata: Metadata to pass to middleware hooks

        Returns:
            Transformed handler function
        """
        current_handler = handler

        # Apply middlewares in reverse order for proper wrapping
        for middleware in reversed(self.middlewares):
            hook = getattr(middleware, hook_name, None)
            if hook and callable(hook):
                result = hook(current_handler, metadata)
                if asyncio.iscoroutine(result):
                    current_handler = await result
                else:
                    current_handler = result

        return current_handler

    async def call(
        self,
        action_name: str,
        params: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Call a service action.

        Args:
            action_name: Fully qualified action name (service.action)
            params: Parameters to pass to the action
            meta: Metadata for the call

        Returns:
            Result from the action

        Raises:
            Exception: If action is not found or execution fails
        """
        if params is None:
            params = {}
        if meta is None:
            meta = {}

        endpoint = self.registry.get_action(action_name)
        if not endpoint:
            raise Exception(f"Action {action_name} not found.")

        context = self.lifecycle.create_context(action=action_name, params=params, meta=meta)

        if endpoint.is_local:
            # Handle local action call
            handler = await self._apply_middlewares(endpoint.handler, "local_action", endpoint)

            try:
                # Validate parameters if schema is defined
                if endpoint.params_schema:
                    from .validator import ValidationError, validate_params

                    try:
                        validate_params(context.params, endpoint.params_schema)
                    except ValidationError:
                        raise  # Re-raise validation errors

                if handler is None:
                    raise Exception(
                        f"Handler for action {action_name} is None after applying middlewares"
                    )

                return await handler(context)

            except Exception as e:
                self.logger.error(f"Error in local action {action_name}: {e}")
                raise
        else:
            # Handle remote action call
            async def remote_request_handler(ctx: "Context") -> Any:
                return await self.transit.request(endpoint, ctx)

            # Apply middlewares to remote call handler
            wrapped_handler = await self._apply_middlewares(
                remote_request_handler, "remote_action", endpoint
            )

            return await wrapped_handler(context)

    async def emit(
        self,
        event_name: str,
        params: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Emit an event to a single service.

        Args:
            event_name: Name of the event to emit
            params: Parameters to pass with the event
            meta: Metadata for the event

        Returns:
            Result from the event handler

        Raises:
            Exception: If event handler is not found
        """
        if params is None:
            params = {}
        if meta is None:
            meta = {}

        endpoint = self.registry.get_event(event_name)
        if not endpoint:
            raise Exception(f"Event {event_name} not found")

        context = self.lifecycle.create_context(event=event_name, params=params, meta=meta)

        if endpoint.is_local and endpoint.handler:
            # Handle local event
            handler = await self._apply_middlewares(endpoint.handler, "local_event", endpoint)
            return await handler(context)
        else:
            # Handle remote event
            return await self.transit.send_event(endpoint, context)

    async def broadcast(
        self,
        event_name: str,
        params: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """Broadcast an event to all registered handlers.

        Args:
            event_name: Name of the event to broadcast
            params: Parameters to pass with the event
            meta: Metadata for the event

        Returns:
            List of results from all event handlers
        """
        if params is None:
            params = {}
        if meta is None:
            meta = {}

        endpoints = self.registry.get_all_events(event_name)
        if not endpoints:
            self.logger.warning(f"No handlers found for event: {event_name}")
            return []

        context = self.lifecycle.create_context(event=event_name, params=params, meta=meta)

        tasks = []
        for endpoint in endpoints:
            if endpoint.is_local and endpoint.handler:
                # Handle local event
                handler = await self._apply_middlewares(endpoint.handler, "local_event", endpoint)
                tasks.append(handler(context))
            else:
                # Handle remote event
                tasks.append(self.transit.send_event(endpoint, context))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results

        return []


# Backwards compatibility alias
Broker = ServiceBroker
