
import asyncio
from pylecular.context import Context
from pylecular.node import Node
from pylecular.transporter.base import Transporter
from pylecular.packets import Packet,Packets
from pylecular.transporter.base import Transporter
import psutil


class Transit:
    def __init__(self, node_id=None, registry=None, node_catalog=None, config=None, logger=None):
        if config is None:
            config = {"type": "nats", "connection": "nats://localhost:4222"} # TODO move config to a config file
        self.node_id = node_id
        self.registry = registry
        self.node_catalog = node_catalog
        self.loggger = logger
        self.transporter = Transporter.get_by_name(config["type"], config, transit=self, handler=self.__message_handler__, node_id=node_id)
        self._pending_requests = {} 


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


    async def __make_subscriptions__(self):
        await self.transporter.subscribe(Packets.INFO.value)
        await self.transporter.subscribe(Packets.INFO.value, self.node_id)
        await self.transporter.subscribe(Packets.HEARTBEAT.value)
        await self.transporter.subscribe(Packets.REQUEST.value, self.node_id)
        await self.transporter.subscribe(Packets.RESPONSE.value, self.node_id)


    async def connect(self):
        await self.transporter.connect()
        await self.discover()
        await self.send_node_info()
        await self.__make_subscriptions__()

        
    async def disconnect(self):
        await self.publish(Packet(Packets.DISCONNECT, None, {}))
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
        # print(f"Handling heartbeat: {packet}")
        # Implement heartbeat handling logic here
        pass

    async def info_handler(self, packet: Packet):
        node = Node(
            id=packet.payload.get("id"),
            **packet.payload
        )
        self.node_catalog.add_node(packet.target, node)

    async def disconnect_handler(self, packet: Packet):
        # print(f"Handling disconnect: {packet}")
        # Implement disconnect handling logic here
        pass

    async def request_handler(self, packet: Packet):
        endpoint = self.registry.get_action(packet.payload.get("action"))
        if endpoint and endpoint.is_local:
            ctx = Context(id=packet.payload.get("id"), params=packet.payload.get("params"), meta=packet.payload.get("meta"))
            try:
                result = await endpoint.handler(ctx) # TODO: try catch result
                response = {
                    "id": ctx.id,
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

    async def request(self, endpoint, params):
        ctx = Context.build(params=params)
        req_id = ctx.id
        future = asyncio.get_running_loop().create_future()
        self._pending_requests[req_id] = future
        await self.publish(Packet(Packets.REQUEST, endpoint.node_id, {
            "action": endpoint.name,
            "params": ctx.params,
            "id": ctx.id
        }))
        response = await future
        return response.get("data")
        

    async def sendEvent(self, event):
        # print(f"Sending event: {event}")
        # Implement event sending logic here
        pass

