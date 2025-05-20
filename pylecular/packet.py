from enum import Enum



class Topic(Enum):
    HEARTBEAT = "HEARTBEAT"
    EVENT = "EVENT"
    DISCONNECT = "DISCONNECT"
    DISCOVER = "DISCOVER"
    INFO = "INFO"
    REQUEST = "REQ"
    RESPONSE = "RES"


class Packet:
    def __init__(self, Topics: Topic, target, payload):
        self.type = Topics
        self.target = target
        self.payload = payload


    @staticmethod
    def from_topic(topic: str) -> Topic:
        parts = topic.split(".")
        return Topic(parts[1]) # TODO: ensure and test
