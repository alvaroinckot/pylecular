def action(params=None):
    def decorator(func):
        func._is_action = True
        return func
    return decorator

def event(params=None):
    def decorator(func):
        func._is_event = True
        return func
    return decorator
