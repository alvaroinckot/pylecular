
class Node:
    def __init__(self, id):
        self.id = id
        self.status = 'offline'

class NodeCatalog:
    def __init__(self):
        self.nodes = {}

    def add_node(self, node):
        self.nodes[node.id] = node

    def get_node(self, id):
        return self.nodes.get(id)

    def remove_node(self, id):
        if id in self.nodes:
            del self.nodes[id]

    def create_local_node(self):
        local_node = Node("local")
        self.add_node(local_node)
        return local_node

