from enum import Enum



class Topics(Enum):
    HEARTBEAT = "HEARTBEAT"
    EVENT = "EVENT"
    DISCONNECT = "DISCONNECT"
    DISCOVER = "DISCOVER"
    INFO = "INFO"
    REQUEST = "REQ"
    RESPONSE = "RES"


class Packet:
    def __init__(self, type: str, target, payload):
        self.type = type
        self.target = target
        self.payload = payload


    @staticmethod
    def from_topic(topic: str) -> Topics:
        parts = topic.split(".")
        return Topics(parts[1]) # TODO: ensure and test
