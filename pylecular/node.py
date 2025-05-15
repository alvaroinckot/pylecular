
import sys

class Node:
    def __init__(self, id):
        self.id = id
        self.available = True
        self.local = False
        self.services = []
        self.cpu = 0
        self.client = None


class NodeCatalog:
    def __init__(self, registry=None, logger=None, node_id=None):
        self.nodes = {}
        self.registry = registry
        self.logger = logger
        self.node_id = node_id
        self.local_node = None
        self.ensure_local_node()


    def add_node(self, id, node):
        self.nodes[id] = node

    def get_node(self, id):
        return self.nodes.get(id)

    def remove_node(self, id):
        if id in self.nodes:
            del self.nodes[id]

    def disconnect_node(self, id):
        node = self.get_node(id)
        if node:
            node.available = False
            self.logger.info(f"Node {id} is disconnected.")
            # self.remove_node(id)

    def process_node_info(self, node_id, payload):
        node = self.get_node(node_id)
        if not node:
            node = Node(node_id)
            self.add_node(node)
        node.available = True
        node.cpu = payload.get("cpu", 0)
        node.services = payload.get("services", [])
        self.logger.info(f"Node {node_id} is connected.")


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
                        f"{service.name}.{event}": {
                            "rawName": event,
                            "name": f"{service.name}.{event}"
                        }
                        for event in service.events()
                    }
                } 
                for service in self.registry.services.values()
            ]
