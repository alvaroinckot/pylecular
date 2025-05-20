
from logging import Logger
import sys

from pylecular.registry import Registry


class Node:
    def __init__(self, id, available=True, local=False, services=None, cpu=0, client=None, ipList=None, hostname=None, config=None, instanceID=None, metadata=None, seq=0, ver=0, sender=None):
        self.id = id
        self.available = available
        self.local = local
        self.services = services if services is not None else []
        self.cpu = cpu
        self.client = client
        self.ipList = ipList if ipList is not None else []
        self.hostname = hostname
        self.config = config if config is not None else {}
        self.instanceID = instanceID
        self.metadata = metadata if metadata is not None else {}
        self.seq = seq
        self.ver = ver
        self.sender = sender

    def get_info(self):
        # return {k: v for k, v in self.__dict__.items() if k != 'id'} # when sending info, the transit should not send id and sender in the same payload
        return self.__dict__

class NodeCatalog:
    def __init__(self, registry: Registry, logger: Logger, node_id: str):
        self.nodes = {}
        self.registry = registry
        self.logger = logger
        self.node_id = node_id
        self.local_node = None
        self.ensure_local_node()


    def add_node(self, id: str, node: Node):
        self.nodes[id] = node
        if self.registry and hasattr(node, "services"):
            for service in node.services:
                actions = service.get("actions", {})
                for action_name in actions:
                    self.registry.add_action(action_name, id)
                events = service.get("events", {})
                for event in events:
                    self.registry.add_event(event, id)
        self.logger.info(f"Node \"{id}\" added.")

    def get_node(self, id):
        return self.nodes.get(id)

    def remove_node(self, id):
        if id in self.nodes:
            del self.nodes[id]


    def disconnect_node(self, id):
        node = self.get_node(id)
        if node:
            node.available = False
            self.logger.info(f"Node \"{id} \" is disconnected.")
            self.remove_node(id)

    def process_node_info(self, node_id, payload):
        node = self.get_node(node_id)
        if not node:
            node = Node(node_id)
            self.add_node(node_id, node)
        node.available = True
        node.cpu = payload.get("cpu", 0)
        node.services = payload.get("services", [])
        self.logger.info(f"Node \"{node_id}\" is connected.")


    def ensure_local_node(self):
        if not self.local_node:
            node = Node(self.node_id)
            self.local_node = node
            self.add_node(self.node_id, node)
        self.local_node.local = True
        self.local_node.client = {
            "type": "python",
            "langVersion": sys.version,
            # "version": version,
        }
        # TODO: local_node.services is essentialy different from the class Service
        # Debug print for service events
        for service in self.registry.__services__.values():
            for event in service.events():
                event_name = getattr(getattr(service, event), "_name", event)
                print(f"Service: {service.name}, Event: {event}, Name: {event_name}")

        self.local_node.services = [
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
                        f"{getattr(getattr(service, event), "_name", event)}": {
                            "name": getattr(getattr(service, event), "_name", event)
                        }
                        for event in service.events()
                    }
                } 
                for service in self.registry.__services__.values() 
            ]
