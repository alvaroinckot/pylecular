
from moleculer.context import Context
from moleculer.transporter.base import Transporter
from moleculer.packets import Packet,Packets
from moleculer.transporter.base import Transporter
import psutil


class Transit:
    # TODO move config to a config file
    def __init__(self, broker, config={
            "type": "nats",
            "connection": "nats://localhost:4222"
        }):
        self.broker = broker
        self.transporter = Transporter.get_by_name(config["type"], config, transit=self, handler=self.__message_handler__)


    async def __message_handler__(self, packet: Packet):
        if packet.type == Packets.INFO:
            pass # TODO: handle info packet
        elif packet.type == Packets.DISCOVER:
            pass # TODO: handle discover packet
        elif packet.type == Packets.HEARTBEAT:
            pass # TODO: handle heartbeat packet
        elif packet.type == Packets.REQUEST:
            await self.request_handler(packet)
        elif packet.type == Packets.RESPONSE:
            await self.response_handler(packet)


    async def __make_subscriptions__(self):
        await self.transporter.subscribe(Packets.INFO.value)
        await self.transporter.subscribe(Packets.INFO.value, self.broker.id)
        await self.transporter.subscribe(Packets.HEARTBEAT.value)
        await self.transporter.subscribe(Packets.REQUEST.value, self.broker.id)
        await self.transporter.subscribe(Packets.RESPONSE.value, self.broker.id)


    async def connect(self):
        await self.transporter.connect()
        await self.discover()
        await self.send_node_info()
        await self.__make_subscriptions__()

        
    async def disconnect(self):
        await self.publish(Packet(Packets.DISCONNECT, None, {}))
        self.transporter.disconnect()

    async def publish(self, packet: Packet):
        await self.transporter.publish(packet)


    async def discover(self):
        await self.publish(Packet(Packets.DISCOVER, None, {})) # TODO: listen for response


    async def beat(self):
        heartbeat = { # TODO: move to node catalog
            "cpu": psutil.cpu_percent(interval=1),
        }
        await self.publish(Packet(Packets.HEARTBEAT, None, heartbeat))

    async def send_node_info(self):
        # TODO: move to node catalog
        node_info = {
            "id": self.broker.id,
            "services": [
                {
                    "name": service.name,
                    "fullName": service.name,
                    "settings": service.settings,
                    "metadata": service.metadata,
                    "actions": {
                        f"{service.name}.{action}": {
                            "rawName": action,
                            "name": f"{service.name}.{action}"
                        }
                        for action in service.actions()
                    },
                    "events": {
                        f"{service.name}.{event}": {
                            "rawName": event,
                            "name": f"{service.name}.{event}"
                        }
                        for event in service.events()
                    }
                } 
                for service in self.broker.registry.services.values()
            ]
        }
        await self.publish(Packet(Packets.INFO, None, node_info))


    async def request_handler(self, packet: Packet):
        ctx = Context(id=packet.payload.get("id"), params=packet.payload.get("params"), meta=packet.payload.get("meta"))
        endpoint = self.broker.registry.get_action(packet.payload.get("action"))
        if endpoint:
            result = endpoint(ctx) # TODO: try catch result
            response = {
                "id": ctx.id,
                "data": result,
                "success": True,
                "meta": {}
            }
            await self.publish(Packet(Packets.RESPONSE, packet.target, response))
        else:
            print(f"Service {packet.payload.get("action")} not found")

    async def response_handler(self, response):
        # print(f"Handling response: {response}")
        # Implement response handling logic here
        pass

    async def request(self, request):
        # print(f"Requesting: {request}")
        # Implement request logic here
        pass

    async def sendEvent(self, event):
        # print(f"Sending event: {event}")
        # Implement event sending logic here
        pass

