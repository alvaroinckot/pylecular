
from pylecular.node import NodeCatalog


class Action:
    def __init__(self, name, node_id, is_local, handler=None):
        self.name = name
        self.handler = handler
        self.node_id = node_id
        self.is_local = is_local


class Event:
    def __init__(self, name, node_id, is_local=False, handler=None):
        self.name = name
        self.node_id = node_id
        self.handler = handler
        self.is_local = is_local



class Registry:
    def __init__(self, node_id=None, logger=None):
        self.__services__ = {} # local services
        self.__actions__ = []
        self.__events__ = []
        self.__node_id__ = node_id
        self.__logger__ = logger

    # TODO: handle service removal
    # TODO: handle remove action removal

    def register(self, service):
        self.__services__[service.name] = service
        self.__actions__.extend([
            Action(f"{service.name}.{action}",self.__node_id__, is_local=True, handler=getattr(service, action))
            for action in service.actions()
        ])
        for event in service.events():
            handler = getattr(service, event)
            is_callable = callable(handler)
            event_name = getattr(handler, "_name", event) if is_callable else event
            print(f"Event {event}: callable={is_callable}, name={event_name}")
        self.__events__.extend([
            Event(getattr(getattr(service, event), "_name", event), self.__node_id__, is_local=True, handler=getattr(service, event))
            for event in service.events()
        ])
        for event in self.__events__:
            print(f"Event {event.name} from node {event.node_id} (local={event.is_local})")
        # self.logger.info(f"Service {service.name} registered with {len(self.actions)} actions and {len(self.events)} events.")

    def get_service(self, name):
        return self.__services__.get(name)
    
    def add_action(self, name, node_id):
        action = Action(name, node_id, is_local=False)
        self.__actions__.append(action)
        
    def add_event(self, name, node_id):
        event = Event(name, node_id, is_local=False)
        self.__events__.append(event)

    def get_action(self, name) -> Action:
        action = [a for a in self.__actions__ if a.name == name]
        if action:
            return action[0]

    def get_all_events(self, name):
        return [a for a in self.__events__ if a.name == name]

    def get_event(self, name) -> Event:
        event = self.get_all_events(name)
        if event:
            return event[0]
