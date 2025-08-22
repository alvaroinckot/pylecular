from typing import Any, Callable, Dict, Optional


def action(
    name: Optional[str] = None, params: Optional[Dict[str, Any]] = None
) -> Callable[[Callable], Callable]:
    """Decorator to mark a method as a service action.

    Args:
        name: Optional custom name for the action. Defaults to function name.
        params: Optional parameter schema for validation.

    Returns:
        Decorator function that marks the method as an action.
    """

    def decorator(func: Callable) -> Callable:
        func._is_action = True
        func._name = name if name is not None else func.__name__
        func._params = params
        return func

    return decorator


def event(
    name: Optional[str] = None, params: Optional[Dict[str, Any]] = None
) -> Callable[[Callable], Callable]:
    """Decorator to mark a method as an event handler.

    Args:
        name: Optional custom name for the event. Defaults to function name.
        params: Optional parameter schema for validation.

    Returns:
        Decorator function that marks the method as an event handler.
    """

    def decorator(func: Callable) -> Callable:
        func._is_event = True
        func._name = name if name is not None else func.__name__
        func._params = params
        return func

    return decorator
