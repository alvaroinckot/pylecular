import uuid

class Context:
    # TODO: support stream
    def __init__(self, id, action=None, request_id=None, parent_id=None, params={}, meta={}, stream=False):
        self.id = id
        self.action = action
        self.params = params
        self.meta = meta
        self.request_id = request_id if request_id is not None else id
        self.parent_id = parent_id
        self.stream = stream

    @staticmethod
    def build( action=None, request_id=None, parent_id=None, params={}, meta={}, stream=False):
        return Context(
            str(uuid.uuid4()),
            action=action,
            request_id=request_id,
            parent_id=parent_id,
            params=params,
            meta=meta,
            stream=stream
        )
    

    def unmarhshall(self):
        return {
            "id": self.id,
            "action": self.action,
            "params": self.params,
            "meta": self.meta,
            "timeout": 0,
            "level": 1,
            "tracing": None,
            "parentID": self.parent_id,
            "requestID": self.request_id,
            "stream": self.stream,
        }
    
    def marshall(self):
        return {
            "id": self.id,
            "action": self.action,
            "params": self.params,
            "meta": self.meta,
            "timeout": 0,
            "level": 1,
            "tracing": None,
            "parentID": self.parent_id,
            "requestID": self.request_id,
            "stream": self.stream,
        }

    # TODO: implement call
    def call(service_name, params):
        pass

    # TODO: implement emit
    def emit(service_name, params):
        pass