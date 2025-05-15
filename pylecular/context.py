import uuid

class Context:
    def __init__(self, id, params={}, meta={}):
        self.id = id
        self.params = params
        self.meta = meta

    @staticmethod
    def build(params):
        return Context(str(uuid.uuid4()), params=params, meta={})
    
    # TODO: implement call
    def call():
        pass

    # TODO: implement emit
    def emit():
        pass