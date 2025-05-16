import uuid

class Context:
    # TODO: support stream
    def __init__(self, id, action=None, event=None, parent_id=None, params={}, meta={}, stream=False, broker=None):
        self.id = id
        self.action = action
        self.event = event
        self.params = params
        self.meta = meta
        self.parent_id = parent_id
        self.stream = stream
        self._broker = broker

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
            "stream": self.stream,
        }

    async def call(self, service_name, params):
        return await self._broker.call(service_name, params)

    async def emit(self, service_name, params):
        return await self._broker.call(service_name, params)
