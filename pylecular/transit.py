
import asyncio
from typing import Any

import psutil

from pylecular.lifecycle import Lifecycle
from pylecular.node import Node, NodeCatalog
from pylecular.packet import Packet, Topic
from pylecular.registry import Registry
from pylecular.settings import Settings
from pylecular.transporter.base import Transporter


class Transit:
    def __init__(self, node_id: str, registry: Registry, node_catalog: NodeCatalog, settings: Settings, logger: Any, lifecycle: Lifecycle):
        self.node_id = node_id
        self.registry = registry
        self.node_catalog = node_catalog
        self.logger = logger
        self.transporter = Transporter.get_by_name(
            settings.transporter.split("://")[0], 
            {"connection": settings.transporter}, 
            transit=self, handler=self.__message_handler__, node_id=node_id)
        self._pending_requests = {} 
        self.lifecycle = lifecycle


    async def __message_handler__(self, packet: Packet):
        if packet.type == Topic.INFO:
            await self.info_handler(packet)
        elif packet.type == Topic.DISCOVER:
            await self.discover_handler(packet)
        elif packet.type == Topic.HEARTBEAT:
            await self.heartbeat_handler(packet)
        elif packet.type == Topic.REQUEST:
            await self.request_handler(packet)
        elif packet.type == Topic.RESPONSE:
            await self.response_handler(packet)
        elif packet.type == Topic.EVENT:
            await self.event_handler(packet)
        elif packet.type == Topic.DISCONNECT:
            await self.disconnect_handler(packet)

    async def __make_subscriptions__(self):
        await self.transporter.subscribe(Topic.INFO.value)
        await self.transporter.subscribe(Topic.INFO.value, self.node_id)
        await self.transporter.subscribe(Topic.DISCONNECT.value)
        await self.transporter.subscribe(Topic.HEARTBEAT.value)
        await self.transporter.subscribe(Topic.REQUEST.value, self.node_id)
        await self.transporter.subscribe(Topic.RESPONSE.value, self.node_id)
        await self.transporter.subscribe(Topic.EVENT.value, self.node_id)


    async def connect(self):
        await self.transporter.connect()
        await self.discover()
        await self.send_node_info()
        await self.__make_subscriptions__()

        
    async def disconnect(self):
        await self.publish(Packet(Topic.DISCONNECT, None, {}))
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()
        await self.transporter.disconnect()

    async def publish(self, packet: Packet):
        await self.transporter.publish(packet)


    async def discover(self):
        await self.publish(Packet(Topic.DISCOVER, None, {}))


    async def beat(self):
        heartbeat = { # TODO: move to node catalog
            "cpu": psutil.cpu_percent(interval=1),

        }
        await self.publish(Packet(Topic.HEARTBEAT, None, heartbeat))

    async def send_node_info(self):
        if self.node_catalog.local_node is None:
            self.logger.error("Local node is not initialized")
            return
        await self.publish(Packet(Topic.INFO, None, self.node_catalog.local_node.get_info()))


    async def discover_handler(self, packet: Packet):
        await self.send_node_info()

    async def heartbeat_handler(self, packet: Packet):
        # TODO: setup heartbeat times
        pass

    async def info_handler(self, packet: Packet):
        node = Node(
            id=packet.payload.get("id"),
            **{k: v for k, v in packet.payload.items() if k != "id"})
        self.node_catalog.add_node(packet.payload.get("sender"), node)

    async def disconnect_handler(self, packet: Packet):
        self.node_catalog.disconnect_node(packet.target)

    async def event_handler(self,packet: Packet):
        endpoint = self.registry.get_event(packet.payload.get("event"))
        if endpoint and endpoint.is_local and endpoint.handler:
            context = self.lifecycle.rebuild_context(packet.payload)
            try:
                await endpoint.handler(context)
            except Exception as e:
                self.logger.error(f"Failed to process event {endpoint.name}")
                self.logger.error(e)

    async def request_handler(self, packet: Packet):
        endpoint = self.registry.get_action(packet.payload.get("action"))
        if endpoint and endpoint.is_local:
            context = self.lifecycle.rebuild_context(packet.payload)
            try:
                # Validate parameters if schema is defined
                if endpoint.params_schema:
                    from pylecular.validator import ValidationError, validate_params
                    try:
                        validate_params(context.params, endpoint.params_schema)
                    except ValidationError as ve:
                        raise ve  # Re-raise the validation error to be caught below
                
                if endpoint.handler:
                    result = await endpoint.handler(context)
                else:
                    raise Exception(f"No handler defined for action {packet.payload.get('action')}")
                response = {
                    "id": context.id,
                    "data": result,
                    "success": True,
                    "meta": {}
                }
            except Exception as e:
                import traceback
                self.logger.error(f"Failed call to {endpoint.name}: {e!s}")
                response = {
                    "id": context.id,
                    "error": {
                        "name": e.__class__.__name__,
                        "message": str(e),
                        "stack": traceback.format_exc()
                    },
                    "success": False,
                    "meta": {}
                }
            await self.publish(Packet(Topic.RESPONSE, packet.target, response))

    async def response_handler(self, packet: Packet):
        req_id = packet.payload.get("id")
        future = self._pending_requests.pop(req_id, None)
        if future:
            future.set_result(packet.payload)

    async def request(self, endpoint, context):
        req_id = context.id
        future = asyncio.get_running_loop().create_future()
        self._pending_requests[req_id] = future
        await self.publish(Packet(Topic.REQUEST, endpoint.node_id, context.marshall()))
        try:
            response = await asyncio.wait_for(future, 5000) # TODO: fetch timeout from settings
            if not response.get("success", True):
                error_data = response.get("error", {})
                error_msg = error_data.get("message", "Unknown error")
                error_name = error_data.get("name", "RemoteError")
                error_stack = error_data.get("stack")
                
                # Recreate an exception with the remote error information
                exception = Exception(f"{error_name}: {error_msg}")
                if error_stack:
                    self.logger.error(f"Remote error stack: {error_stack}")
                
                raise exception
                
            return response.get("data")
        except asyncio.TimeoutError as err:
            self._pending_requests.pop(req_id, None)
            raise Exception(f"Request to {endpoint.name} timed out") from err
        

    async def send_event(self, endpoint, context):
        await self.publish(Packet(Topic.EVENT, endpoint.node_id, context.marshall()))


