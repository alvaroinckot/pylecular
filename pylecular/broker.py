import asyncio
import signal

from pylecular.discoverer import Discoverer
from pylecular.lifecycle import Lifecycle
from pylecular.logger import get_logger
from pylecular.node import NodeCatalog
from pylecular.registry import Registry
from pylecular.settings import Settings
from pylecular.transit import Transit


class Broker:
    def __init__(
        self,
        id,
        settings: Settings = Settings(),
        version: str = "0.14.35",
        namespace: str = "default",
        lifecycle=None,
        registry=None,
        node_catalog=None,
        transit=None,
        discoverer=None,
        middlewares=None,
    ):
        self.id = id
        self.settings = settings  # Store settings

        # Prioritize middlewares passed directly, then from settings
        if middlewares is not None:
            self.middlewares = middlewares
        elif self.settings and hasattr(self.settings, "middlewares"):
            self.middlewares = self.settings.middlewares
        else:
            self.middlewares = []

        self.version = version
        self.namespace = namespace
        self.logger = get_logger(settings.log_level, settings.log_format).bind(
            node=self.id, service="BROKER", level=settings.log_level
        )
        self.lifecycle = lifecycle or Lifecycle(broker=self)
        self.registry = registry or Registry(node_id=self.id, logger=self.logger)
        self.node_catalog = node_catalog or NodeCatalog(
            logger=self.logger, node_id=self.id, registry=self.registry
        )
        self.transit = transit or Transit(
            settings=settings,
            node_id=self.id,
            registry=self.registry,
            node_catalog=self.node_catalog,
            lifecycle=self.lifecycle,
            logger=self.logger,
        )
        self.discoverer = discoverer or Discoverer(broker=self)

        # Call broker_created hooks (synchronous)
        for middleware in self.middlewares:
            if hasattr(middleware, "broker_created") and callable(middleware.broker_created):
                middleware.broker_created(self)

    async def start(self):
        self.logger.info(f"Moleculer v{self.version} is starting...")
        self.logger.info(f"Namespace: {self.namespace}.")
        self.logger.info(f"Node ID: {self.id}.")
        self.logger.info(f"Transporter: {self.transit.transporter.name}.")
        await self.transit.connect()
        self.logger.info(
            f"✔ Service broker with {len(self.registry.__services__)} services started."
        )

        # Call broker_started hooks - handle both async and non-async methods
        coroutines = []
        for middleware in self.middlewares:
            if hasattr(middleware, "broker_started") and callable(middleware.broker_started):
                result = middleware.broker_started(self)
                if asyncio.iscoroutine(result):
                    coroutines.append(result)

        if coroutines:
            await asyncio.gather(*coroutines)

    async def stop(self):
        # First stop the discoverer to cancel periodic tasks
        if hasattr(self.discoverer, "stop"):
            await self.discoverer.stop()
        # Then disconnect the transit
        await self.transit.disconnect()

        # Call broker_stopped hooks - handle both async and non-async methods
        coroutines = []
        for middleware in self.middlewares:
            if hasattr(middleware, "broker_stopped") and callable(middleware.broker_stopped):
                result = middleware.broker_stopped(self)
                if asyncio.iscoroutine(result):
                    coroutines.append(result)

        if coroutines:
            await asyncio.gather(*coroutines)

        self.logger.info("Service broker is stopped. Good bye.")

    async def wait_for_shutdown(self):
        loop = asyncio.get_event_loop()
        shutdown_event = asyncio.Event()

        def signal_handler() -> None:
            shutdown_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

        await shutdown_event.wait()
        await self.stop()

    async def wait_for_services(self, services=[]):
        while True:
            found = True
            for name in services:
                service = self.registry.get_service(name)
                if not service:
                    # check in remote nodes
                    for node in self.node_catalog.nodes.values():
                        if node.id != self.id:
                            for service_obj in node.services:
                                if service_obj.get("name") == name:
                                    service = service_obj
                                    break
                if not service:
                    found = False
                    break
            if found:
                return
            await asyncio.sleep(0.1)

    # TODO: fix service lyfecicle handling on catalog
    # TODO: if service is alive send INFO
    async def register(self, service):  # Make it async
        self.registry.register(service)  # This is synchronous
        self.node_catalog.ensure_local_node()  # Assuming this is sync

        # Call service_created hooks - handle both async and non-async methods
        coroutines = []
        for middleware in self.middlewares:
            if hasattr(middleware, "service_created") and callable(middleware.service_created):
                result = middleware.service_created(service)
                if asyncio.iscoroutine(result):
                    coroutines.append(result)

        if coroutines:
            await asyncio.gather(*coroutines)

        # Call service_started hooks - handle both async and non-async methods
        coroutines = []
        for middleware in self.middlewares:
            if hasattr(middleware, "service_started") and callable(middleware.service_started):
                result = middleware.service_started(service)
                if asyncio.iscoroutine(result):
                    coroutines.append(result)

        if coroutines:
            await asyncio.gather(*coroutines)

        # TODO: Implement service_stopped hook, likely in a new Broker.unregister method or similar

    async def _apply_middlewares(self, handler, hook_name, metadata):
        for middleware in reversed(self.middlewares):
            hook = getattr(middleware, hook_name, None)
            if hook:
                result = hook(handler, metadata)
                if asyncio.iscoroutine(result):
                    handler = await result
                else:
                    handler = result
        return handler

    # TODO: support balancing strategies
    # TODO: support unbalanced
    async def call(self, action_name, params={}, meta={}):
        endpoint = self.registry.get_action(action_name)
        context = self.lifecycle.create_context(action=action_name, params=params, meta=meta)
        if endpoint and endpoint.is_local:
            # Apply middlewares to the local action handler
            handler_to_execute = await self._apply_middlewares(
                endpoint.handler, "local_action", endpoint
            )

            try:
                # Validate parameters if schema is defined
                if endpoint.params_schema:
                    from pylecular.validator import ValidationError, validate_params

                    try:
                        validate_params(context.params, endpoint.params_schema)
                    except ValidationError as ve:
                        raise ve  # Re-raise the validation error to be caught below

                if handler_to_execute is None:  # Check the potentially wrapped handler
                    raise Exception(
                        f"Handler for action {action_name} is None after applying middlewares."
                    )
                return await handler_to_execute(context)  # Use the new handler
            except Exception as e:
                # Local errors are propagated directly
                self.logger.error(f"Error in local action {action_name}: {e!s}")
                raise e
        elif endpoint and not endpoint.is_local:
            # Define a handler that encapsulates the remote call
            async def remote_request_handler(ctx_passed_to_handler):
                # ctx_passed_to_handler here is the same context object created earlier in Broker.call
                return await self.transit.request(endpoint, ctx_passed_to_handler)

            # Apply middlewares to this handler
            # The 'endpoint' (action object) is passed as metadata
            wrapped_remote_request_handler = await self._apply_middlewares(
                remote_request_handler, "remote_action", endpoint
            )

            # Call the (potentially) wrapped handler
            return await wrapped_remote_request_handler(context)
        else:
            raise Exception(f"Action {action_name} not found.")

    async def emit(self, event_name, params={}, meta={}):
        endpoint = self.registry.get_event(event_name)
        context = self.lifecycle.create_context(event=event_name, params=params, meta=meta)
        if endpoint and endpoint.is_local and endpoint.handler:
            handler_to_execute = await self._apply_middlewares(
                endpoint.handler, "local_event", endpoint
            )
            return await handler_to_execute(context)
        elif endpoint and not endpoint.is_local:
            return await self.transit.send_event(endpoint, context)
        else:
            raise Exception(f"Event {event_name} not found.")

    async def broadcast(self, event_name, params={}, meta={}):
        endpoints = self.registry.get_all_events(event_name)
        context = self.lifecycle.create_context(event=event_name, params=params, meta=meta)

        tasks = []
        for endpoint in endpoints:
            if endpoint.is_local and endpoint.handler:
                handler = await self._apply_middlewares(endpoint.handler, "local_event", endpoint)
                tasks.append(handler(context))
            else:
                tasks.append(self.transit.send_event(endpoint, context))

        if tasks:
            results = await asyncio.gather(*tasks)
            return results
        return []
