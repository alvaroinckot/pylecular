from enum import Enum
import string

class Packets(Enum):
    HEARTBEAT = "HEARTBEAT"
    DISCONNECT = "DISCONNECT"
    DISCOVER = "DISCOVER"
    INFO = "INFO"
    REQUEST = "REQ"
    RESPONSE = "RES"


class Packet:
    def __init__(self, type: string, target, payload):
        self.type = type
        self.target = target
        self.payload = payload


    @staticmethod
    def from_topic(topic: string):
        """
        Converts a topic string to a Packet object.
        """
        parts = topic.split(".")
        return Packets(parts[1]) # TODO: ensure and test
