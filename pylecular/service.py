"""Base Service class for the Pylecular framework.

This module provides the base Service class that all microservices should inherit from.
It provides functionality for discovering actions and events defined in the service.
"""

from typing import Any, Dict, List, Optional


class Service:
    """Base class for all Pylecular microservices.

    Services should inherit from this class and define their actions and events
    as methods decorated with @action or @event decorators.
    """

    def __init__(self, name: str, settings: Optional[Dict[str, Any]] = None) -> None:
        """Initialize a new Service instance.

        Args:
            name: The name of the service (may include version)
            settings: Optional service-specific settings
        """
        self.name = name
        self.settings = settings or {}
        self.metadata: Dict[str, Any] = {}

    def actions(self) -> List[str]:
        """Get a list of all action method names in this service.

        Returns:
            List of method names that are marked as actions
        """
        return [
            attr
            for attr in dir(self)
            if callable(getattr(self, attr)) and getattr(getattr(self, attr), "_is_action", False)
        ]

    def events(self) -> List[str]:
        """Get a list of all event handler method names in this service.

        Returns:
            List of method names that are marked as event handlers
        """
        return [
            attr
            for attr in dir(self)
            if callable(getattr(self, attr)) and getattr(getattr(self, attr), "_is_event", False)
        ]
