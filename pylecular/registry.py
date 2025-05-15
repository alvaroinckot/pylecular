
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
        self.services = {}
        self.actions = []
        self.events = []
        self.node_id = node_id
        self.logger = logger

    def register(self, service):
        self.services[service.name] = service
        self.actions.extend([
            Action(f"{service.name}.{action}",self.node_id, is_local=True, handler=getattr(service, action))
            for action in service.actions()
        ])
        self.events.extend([
            Event(f"{service.name}.{event}", self.node_id, is_local=True, handler=getattr(service, event))
            for event in service.events()
        ])
        # self.logger.info(f"Service {service.name} registered with {len(self.actions)} actions and {len(self.events)} events.")

    def get_service(self, name):
        return self.services.get(name)

    def get_action(self, name) -> Action:
        action = [a for a in self.actions if a.name == name and a.node_id == self.node_id and a.is_local]
        if action:
            return action[0]


    def get_event(self, name):
        service, event = name.split(".")
        service_instance = self.get_service(service)
        if service_instance:
            return getattr(service_instance, event, None)
        return None
        
