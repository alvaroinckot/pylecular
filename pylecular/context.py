import uuid

class Context:
    def __init__(self, id, params={}, meta={}):
        self.id = id
        self.params = params
        self.meta = meta

    @staticmethod
    def build():
        return Context(str(uuid.uuid4()))