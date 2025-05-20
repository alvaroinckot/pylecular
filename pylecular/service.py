class Service:
    def __init__(self, name, settings=None):
        self.name = name  # support version as well
        self.settings = settings or {}
        self.metadata = {}

    def actions(self):
        return [
            attr
            for attr in dir(self)
            if callable(getattr(self, attr)) and getattr(getattr(self, attr), "_is_action", False)
        ]

    def events(self):
        return [
            attr
            for attr in dir(self)
            if callable(getattr(self, attr)) and getattr(getattr(self, attr), "_is_event", False)
        ]
