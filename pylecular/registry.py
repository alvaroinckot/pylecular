from typing import List, Optional


class Action:
    def __init__(self, name, node_id, is_local, handler=None, params_schema=None):
        self.name = name
        self.handler = handler
        self.node_id = node_id
        self.is_local = is_local
        self.params_schema = params_schema


class Event:
    def __init__(self, name, node_id, is_local=False, handler=None):
        self.name = name
        self.node_id = node_id
        self.handler = handler
        self.is_local = is_local


class Registry:
    def __init__(self, node_id=None, logger=None):
        self.__services__ = {}  # local services
        self.__actions__ = []
        self.__events__ = []
        self.__node_id__ = node_id
        self.__logger__ = logger

    # TODO: handle service removal
    # TODO: handle remove action removal

    def register(self, service):
        self.__services__[service.name] = service
        self.__actions__.extend(
            [
                Action(
                    f"{service.name}.{getattr(getattr(service, action), '_name', action)}",
                    self.__node_id__,
                    is_local=True,
                    handler=getattr(service, action),
                    params_schema=getattr(getattr(service, action), "_params", None),
                )
                for action in service.actions()
            ]
        )
        self.__events__.extend(
            [
                Event(
                    f"{service.name}.{getattr(getattr(service, event), '_name', event)}",
                    self.__node_id__,
                    is_local=True,
                    handler=getattr(service, event),
                )
                for event in service.events()
            ]
        )
        for event in self.__events__:
            print(f"Event {event.name} from node {event.node_id} (local={event.is_local})")
            service_name = event.name.split(".")[0] if "." in event.name else ""
            event_name = event.name.split(".")[-1] if "." in event.name else event.name
            print(f"Service: {service_name}, Event: {event_name}, Name: {event.name}")

    def get_service(self, name):
        return self.__services__.get(name)

    def add_action(self, action_obj):
        """Add an action to the registry.

        Args:
            action_obj: An Action object with name, node_id, etc.
        """
        self.__actions__.append(action_obj)

    def add_event(self, name, node_id):
        event = Event(name, node_id, is_local=False)
        self.__events__.append(event)

    def get_action(self, name) -> Optional[Action]:
        action = [a for a in self.__actions__ if a.name == name]
        if action:
            return action[0]
        return None  # Explicitly return None for clarity

    def get_all_events(self, name) -> List[Event]:
        return [a for a in self.__events__ if a.name == name]

    def get_event(self, name) -> Optional[Event]:
        event = self.get_all_events(name)
        if event:
            return event[0]
        return None  # Explicitly return None for clarity
