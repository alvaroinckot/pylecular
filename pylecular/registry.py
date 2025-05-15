
class Registry:
    def __init__(self, broker=None):
        self.services = {}
        self.broker = broker

    def register(self, service):
        self.services[service.name] = service

    def get_service(self, name):
        return self.services.get(name)

    def get_action(self, name):
        service, action = name.split(".")
        service_instance = self.get_service(service)
        if service_instance:
            return getattr(service_instance, action, None)
        return None

    def get_event(self, name):
        service, event = name.split(".")
        service_instance = self.get_service(service)
        if service_instance:
            return getattr(service_instance, event, None)
        return None
        
