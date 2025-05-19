import asyncio
import signal
from pylecular.context import Context
from pylecular.discoverer import Discoverer
from pylecular.lifecycle import Lifecycle
from pylecular.node import NodeCatalog
from pylecular.registry import Registry 
from pylecular.settings import Settings
from pylecular.transit import Transit
from pylecular.logger import get_logger

class Broker:
    def __init__(self, id, settings: Settings=Settings()):
        self.id = id
        self.version = "0.14.35"
        self.namespace = "default"
        self.logger = get_logger(settings.log_level, settings.log_format).bind(
            node=self.id,
            service="BROKER",
            level=settings.log_level
        )
        self.lifecycle = Lifecycle(broker=self)
        self.registry = Registry(node_id=self.id, logger=self.logger)
        self.node_catalog: NodeCatalog = NodeCatalog(logger=self.logger, node_id=self.id, registry=self.registry)
        self.transit = Transit(settings=settings,node_id=self.id, registry=self.registry, node_catalog=self.node_catalog, lifecycle=self.lifecycle, logger=self.logger)
        self.discoverer = Discoverer(broker=self)


    async def start(self):
        self.logger.info(f"Moleculer v{self.version} is starting...")
        self.logger.info(f"Namespace: {self.namespace}.")
        self.logger.info(f"Node ID: {self.id}.")
        self.logger.info(f"Transporter: {self.transit.transporter.name}.")
        await self.transit.connect()
        self.logger.info(f"✔ Service broker with {len(self.registry.__services__)} services started.")


    async def stop(self):
        await self.transit.disconnect()
        self.logger.info("Service broker is stopped. Good bye.")

    async def wait_for_shutdown(self):
        loop = asyncio.get_event_loop()
        shutdown_event = asyncio.Event()

        def signal_handler():
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
    def register(self, service):
        self.registry.register(service)
        self.node_catalog.ensure_local_node()

    # TODO: support balancing strategies
    # TODO: support unbalanced
    async def call(self, action_name, params={}):
        endpoint = self.registry.get_action(action_name)
        context = self.lifecycle.create_context(action=action_name, params=params)
        if endpoint and endpoint.is_local:
            return await endpoint.handler(context)
        elif endpoint and not endpoint.is_local:
            return await self.transit.request(endpoint, context)
        else:
            raise Exception(f"Action {action_name} not found.")
        

    async def emit(self, event_name, params={}): # TODO: emit with transit 
        endpoint = self.registry.get_event(event_name)
        context = self.lifecycle.create_context(event=event_name, params=params)
        if endpoint and endpoint.is_local:
            return await endpoint.handler(context)
        elif endpoint and not endpoint.is_local:
            return await self.transit.send_event(endpoint, context)
        
    
    async def broadcast(self, event_name, params={}):
        endpoints = self.registry.get_all_events(event_name)
        context = self.lifecycle.create_context(event=event_name, params=params)
        await asyncio.gather(*[
            endpoint.handler(context) if endpoint.is_local 
            else self.transit.send_event(endpoint, context)
            for endpoint in endpoints
        ])