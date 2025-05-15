from .base import Transporter
from pylecular.packets import Packet, Packets
import nats
import json

class NatsTransporter(Transporter):
    name = "nats"

    def __init__(self, connection_string, transit, handler=None):
        super().__init__(self.name)
        self.connection_string = connection_string
        self.transit = transit
        self.handler = handler
        self.nc = None

    # TODO: maybe move it to base class
    # TODO: user real world serializer
    def _serialize(self, payload): 
        payload["ver"] = "4"
        payload["sender"] = self.transit.broker.id
        return json.dumps(payload).encode('utf-8')
    
    def get_topic_name(self, command, node_id=None):
        topic = f"MOL.{command}"
        if node_id:
            topic += f".{node_id}"
        return topic
    
    async def message_handler(self, msg):
        # print(f"Received message: {msg}")
        data = json.loads(msg.data.decode("utf-8"))
        type = Packet.from_topic(msg.subject)
        sender = data.get("sender")
        packet = Packet(type, sender, data)
        await self.handler(packet)

    async def publish(self, packet: Packet):
        topic = self.get_topic_name(packet.type.value, packet.target) 
        await self.nc.publish(topic, self._serialize(packet.payload))

    async def connect(self):
        print(f"Connecting to NATS with name {self.name}")
        # Implement NATS connection logic here
        self.nc = await nats.connect(self.connection_string)


    async def subscribe(self, command, node_id=None):
        topic = self.get_topic_name(command, node_id)
        print(f"Subscribing to topic: {topic}")
        if self.handler is None:
            raise ValueError("Handler must be provided for subscription.")
        if not callable(self.message_handler) or not hasattr(self.message_handler, "__call__") or not hasattr(self.message_handler, "__code__") or not self.message_handler.__code__.co_flags & 0x80:
            raise ValueError("Handler must be an async function.")
        await self.nc.subscribe(topic, cb=self.message_handler)
    
    @classmethod
    def from_config(cls, config, transit, handler=None) -> "Transporter":
        return cls(connection_string=config["connection"], transit=transit, handler=handler)
