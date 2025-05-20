import uuid

from pylecular.context import Context


# TODO: handle context list and graceful shutdown
class Lifecycle:
    def __init__(self, broker):
        self.broker = broker

    def create_context(
        self,
        id=uuid.uuid4(),
        event=None,
        action=None,
        parent_id=None,
        params={},
        meta={},
        stream=False,
    ):
        return Context(
            str(id),
            action=action,
            event=event,
            parent_id=parent_id,
            params=params,
            meta=meta,
            stream=stream,
            broker=self.broker,
        )

    def rebuild_context(self, context_dict):
        return Context(
            str(context_dict.get("id")),
            action=context_dict.get("action"),
            event=context_dict.get("event"),
            parent_id=context_dict.get("parent_id"),
            params=context_dict.get("params", {}),
            meta=context_dict.get("meta", {}),
            stream=context_dict.get("stream", False),
            broker=self.broker,
        )
