def action(params=None):
    def decorator(func):
        func._is_action = True
        func._params = params
        return func
    return decorator

def event(name=None, params=None):
    def decorator(func):
        func._is_event = True
        func._name = name if name else func.__name__
        func._params = params
        return func
    return decorator
