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
    def __init__(self, Topics: Topics, target, payload):
        self.type = Topics
        self.target = target
        self.payload = payload


    @staticmethod
    def from_topic(topic: str) -> Topics:
        parts = topic.split(".")
        return Topics(parts[1]) # TODO: ensure and test
