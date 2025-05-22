class Middleware:
    def local_action(self, next_handler, action):
        def handler(ctx):
            return next_handler(ctx)
        return handler

    def remote_action(self, next_handler, action):
        def handler(ctx):
            return next_handler(ctx)
        return handler

    def local_event(self, next_handler, event):
        def handler(ctx):
            return next_handler(ctx)
        return handler

    def broker_created(self, broker):
        pass

    def broker_started(self, broker):
        pass

    def broker_stopped(self, broker):
        pass

    def service_created(self, service):
        pass

    def service_started(self, service):
        pass

    def service_stopped(self, service):
        pass
