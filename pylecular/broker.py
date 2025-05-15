import asyncio
import signal
from pylecular.context import Context
from pylecular.discoverer import Discoverer
from pylecular.node import NodeCatalog
from pylecular.packets import Packet, Packets
from pylecular.registry import Registry 
from pylecular.transit import Transit
from pylecular.logger import structlog

class Broker:
    def __init__(self, id):
        self.id = id
        self.version = "0.14.5"
        self.namespace = "default"
        self.logger = structlog.get_logger().bind(
            node=self.id,
            service="BROKER",
        )
        self.registry = Registry(node_id=self.id, logger=self.logger)
        self.node_catalog = NodeCatalog(logger=self.logger, node_id=self.id, registry=self.registry)
        self.transit = Transit(node_id=self.id, registry=self.registry, node_catalog=self.node_catalog)
        self.discoverer = Discoverer(broker=self)


    async def start(self):
        self.logger.info(f"Moleculer v{self.version} is starting...")
        self.logger.info(f"Namespace: {self.namespace}.")
        self.logger.info(f"Node ID: {self.id}.")
        self.logger.info(f"Transporter: {self.transit.transporter.name}.")
        await self.transit.connect()
        self.logger.info(f"✔ Service broker with {len(self.registry.services)} services started.")


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

    def register(self, service):
        self.registry.register(service)
        self.node_catalog.ensure_local_node()
        # TODO: fix service lyfecicle handling on catalog
        # TODO: if service is alive send INFO

    async def call(self, action_name, params):
        endpoint = self.registry.get_action(action_name)
        if endpoint and endpoint.is_local:
            ctx = Context.build(params=params)
            return await endpoint.handler(ctx)
        elif endpoint and not endpoint.is_local:
            ctx = Context.build(params=params)
            self.transit.publish(Packet(Packets.REQUEST, endpoint.node_id, {
                "action": action_name,
                "params": params
            }))
        else:
            raise Exception(f"Action {action_name} not found.")
        

    async def emit(self, event_name, *args): # TODO: emit with transit 
        endpoint = self.registry.get_event(event_name)
        if endpoint:
            ctx = Context.build()
            endpoint(ctx, *args) # emit vs broadcast to all nodes logic
        
