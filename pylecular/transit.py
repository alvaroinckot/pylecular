
import asyncio
from pylecular.context import Context
from pylecular.node import Node
from pylecular.transporter.base import Transporter
from pylecular.packets import Packet,Packets
from pylecular.transporter.base import Transporter
import psutil


class Transit:
    def __init__(self, node_id=None, registry=None, node_catalog=None, config=None, logger=None, lifecycle=None):
        if config is None:
            config = {"type": "nats", "connection": "nats://localhost:4222"} # TODO move config to a config file
        self.node_id = node_id
        self.registry = registry
        self.node_catalog = node_catalog
        self.loggger = logger
        self.transporter = Transporter.get_by_name(config["type"], config, transit=self, handler=self.__message_handler__, node_id=node_id)
        self._pending_requests = {} 
        self.lifecycle = lifecycle


    async def __message_handler__(self, packet: Packet):
        if packet.type == Packets.INFO:
            await self.info_handler(packet)
        elif packet.type == Packets.DISCOVER:
            await self.discover_handler(packet)
        elif packet.type == Packets.HEARTBEAT:
            await self.heartbeat_handler(packet)
        elif packet.type == Packets.REQUEST:
            await self.request_handler(packet)
        elif packet.type == Packets.RESPONSE:
            await self.response_handler(packet)
        elif packet.type == Packets.EVENT:
            await self.event_handler(packet)
        elif packet.type == Packets.DISCONNECT:
            await self.disconnect_handler(packet)

    async def __make_subscriptions__(self):
        await self.transporter.subscribe(Packets.INFO.value)
        await self.transporter.subscribe(Packets.INFO.value, self.node_id)
        await self.transporter.subscribe(Packets.DISCONNECT.value)
        await self.transporter.subscribe(Packets.HEARTBEAT.value)
        await self.transporter.subscribe(Packets.REQUEST.value, self.node_id)
        await self.transporter.subscribe(Packets.RESPONSE.value, self.node_id)
        await self.transporter.subscribe(Packets.EVENT.value, self.node_id)


    async def connect(self):
        await self.transporter.connect()
        await self.discover()
        await self.send_node_info()
        await self.__make_subscriptions__()

        
    async def disconnect(self):
        await self.publish(Packet(Packets.DISCONNECT, None, {}))
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()
        await self.transporter.disconnect()

    async def publish(self, packet: Packet):
        await self.transporter.publish(packet)


    async def discover(self):
        await self.publish(Packet(Packets.DISCOVER, None, {}))


    async def beat(self):
        heartbeat = { # TODO: move to node catalog
            "cpu": psutil.cpu_percent(interval=1),

        }
        await self.publish(Packet(Packets.HEARTBEAT, None, heartbeat))

    async def send_node_info(self):
        await self.publish(Packet(Packets.INFO, None, self.node_catalog.local_node.__dict__))


    async def discover_handler(self, packet: Packet):
        await self.send_node_info()

    async def heartbeat_handler(self, packet: Packet):
        # TODO: setup heartbeat times
        pass

    async def info_handler(self, packet: Packet):
        node = Node(
            id=packet.payload.get("id"),
            **packet.payload
        )
        self.node_catalog.add_node(packet.target, node)

    async def disconnect_handler(self, packet: Packet):
        self.node_catalog.disconnect_node(packet.target)

    async def event_handler(self,packet: Packet):
        endpoint = self.registry.get_event(packet.payload.get("event"))
        if endpoint and endpoint.is_local:
            context = self.lifecycle.rebuild_context(packet.payload)
            try:
                await endpoint.handler(context)
            except Exception as e:
                self.logger.error(f"Failed to process event {endpoint.name}.", e)

    async def request_handler(self, packet: Packet):
        endpoint = self.registry.get_action(packet.payload.get("action"))
        if endpoint and endpoint.is_local:
            context = self.lifecycle.rebuild_context(packet.payload)
            try:
                result = await endpoint.handler(context)
                response = {
                    "id": context.id,
                    "data": result,
                    "success": True,
                    "meta": {}
                }
                await self.publish(Packet(Packets.RESPONSE, packet.target, response))
            except Exception as e:
                self.logger.error(f"Failed call to {endpoint.name}.", e)

    async def response_handler(self, packet: Packet):
        req_id = packet.payload.get("id")
        future = self._pending_requests.pop(req_id, None)
        if future:
            future.set_result(packet.payload)

    async def request(self, endpoint, context):
        req_id = context.id
        future = asyncio.get_running_loop().create_future()
        self._pending_requests[req_id] = future
        await self.publish(Packet(Packets.REQUEST, endpoint.node_id, context.marshall()))
        try:
            response = await asyncio.wait_for(future, 5000) # TODO: fetch timeout from settings
            return response.get("data")
        except asyncio.TimeoutError:
            self._pending_requests.pop(req_id, None)
            # Optionally log or raise a custom exception
            return None
        

    async def send_event(self, endpoint, context):
        await self.publish(Packet(Packets.EVENT, endpoint.node_id, context.marshall()))


