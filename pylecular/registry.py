
from pylecular.node import NodeCatalog


class Action:
    def __init__(self, name, node_id, is_local, handler=None):
        self.name = name
        self.handler = handler
        self.node_id = node_id
        self.is_local = is_local
        print(f"Action created with values: name={self.name}, node_id={self.node_id}, is_local={self.is_local}, handler={self.handler}")


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
        self.__events__.extend([
            Event(f"{service.name}.{event}", self.__node_id__, is_local=True, handler=getattr(service, event))
            for event in service.events()
        ])
        # self.logger.info(f"Service {service.name} registered with {len(self.actions)} actions and {len(self.events)} events.")

    def get_service(self, name):
        return self.__services__.get(name)
    
    def add_action(self, name, node_id):
        action = Action(name, node_id, is_local=False)
        self.__actions__.append(action)
        
    def get_action(self, name) -> Action:
        print([a.name for a in self.__actions__])
        action = [a for a in self.__actions__ if a.name == name]
        if action:
            return action[0]


    def get_event(self, name):
        service, event = name.split(".")
        service_instance = self.get_service(service)
        if service_instance:
            return getattr(service_instance, event, None)
        return None
        
