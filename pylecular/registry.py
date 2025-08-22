"""Service registry for managing actions and events in the Pylecular framework.

This module provides the registry system that tracks services, actions, and events
within a Pylecular node, enabling service discovery and routing capabilities.
"""

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

if TYPE_CHECKING:
    from .service import Service


class Action:
    """Represents a service action in the registry.

    Actions are callable methods on services that can be invoked remotely
    through the service broker.
    """

    def __init__(
        self,
        name: str,
        node_id: str,
        is_local: bool,
        handler: Optional[Callable] = None,
        params_schema: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize an Action instance.

        Args:
            name: Fully qualified action name (service.action)
            node_id: ID of the node hosting this action
            is_local: Whether this action is local to the current node
            handler: Callable handler function for the action
            params_schema: Optional parameter validation schema
        """
        self.name = name
        self.handler = handler
        self.node_id = node_id
        self.is_local = is_local
        self.params_schema = params_schema


class Event:
    """Represents an event handler in the registry.

    Events are methods that can be triggered by other services and
    can have multiple handlers across different services.
    """

    def __init__(
        self,
        name: str,
        node_id: str,
        is_local: bool = False,
        handler: Optional[Callable] = None,
    ) -> None:
        """Initialize an Event instance.

        Args:
            name: Event name
            node_id: ID of the node hosting this event handler
            is_local: Whether this event handler is local to the current node
            handler: Callable handler function for the event
        """
        self.name = name
        self.node_id = node_id
        self.handler = handler
        self.is_local = is_local


class Registry:
    """Central registry for services, actions, and events.

    The Registry maintains catalogs of all available services, actions, and events
    within the Pylecular cluster, enabling service discovery and routing.
    """

    def __init__(self, node_id: Optional[str] = None, logger: Optional[Any] = None) -> None:
        """Initialize a new Registry instance.

        Args:
            node_id: Unique identifier for this node
            logger: Logger instance for registry operations
        """
        self.__services__: Dict[str, Service] = {}
        self.__actions__: List[Action] = []
        self.__events__: List[Event] = []
        self.__node_id__ = node_id
        self.__logger__ = logger

    def register(self, service: "Service") -> None:
        """Register a service and its actions/events in the registry.

        Args:
            service: Service instance to register
        """
        self.__services__[service.name] = service

        # Register service actions
        service_actions = [
            Action(
                name=f"{service.name}.{getattr(getattr(service, action), '_name', action)}",
                node_id=self.__node_id__,
                is_local=True,
                handler=getattr(service, action),
                params_schema=getattr(getattr(service, action), "_params", None),
            )
            for action in service.actions()
        ]
        self.__actions__.extend(service_actions)

        # Register service events
        service_events = [
            Event(
                name=getattr(getattr(service, event), "_name", event),
                node_id=self.__node_id__,
                is_local=True,
                handler=getattr(service, event),
            )
            for event in service.events()
        ]
        self.__events__.extend(service_events)

        # Log registered events for debugging
        if self.__logger__:
            for event in service_events:
                self.__logger__.debug(
                    f"Event {event.name} from node {event.node_id} (local={event.is_local})"
                )

    def get_service(self, name: str) -> Optional["Service"]:
        """Get a service by name.

        Args:
            name: Service name to look up

        Returns:
            Service instance if found, None otherwise
        """
        return self.__services__.get(name)

    def add_action(self, action_obj: Action) -> None:
        """Add an action to the registry.

        Args:
            action_obj: Action object to add
        """
        self.__actions__.append(action_obj)

    def add_event(self, name: str, node_id: str) -> None:
        """Add an event to the registry.

        Args:
            name: Event name
            node_id: Node ID hosting the event
        """
        event = Event(name, node_id, is_local=False)
        self.__events__.append(event)

    def add_event_obj(self, event_obj: Event) -> None:
        """Add an event object to the registry.

        Args:
            event_obj: Event object to add
        """
        self.__events__.append(event_obj)

    def get_action(self, name: str) -> Optional[Action]:
        """Get an action by name.

        Args:
            name: Fully qualified action name to look up

        Returns:
            First matching Action instance, or None if not found
        """
        for action in self.__actions__:
            if action.name == name:
                return action
        return None

    def get_all_events(self, name: str) -> List[Event]:
        """Get all event handlers for a given event name.

        Args:
            name: Event name to look up

        Returns:
            List of Event instances matching the name
        """
        return [event for event in self.__events__ if event.name == name]

    def get_event(self, name: str) -> Optional[Event]:
        """Get the first event handler for a given event name.

        Args:
            name: Event name to look up

        Returns:
            First matching Event instance, or None if not found
        """
        events = self.get_all_events(name)
        return events[0] if events else None
