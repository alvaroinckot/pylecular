"""Context class for handling service requests and events in Pylecular framework.

The Context class provides the execution context for service actions and events,
including metadata handling and broker communication capabilities.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from .broker import ServiceBroker


class Context:
    """Represents the execution context for a service action or event.

    The Context contains all relevant information about a request including
    parameters, metadata, tracing information, and provides methods to
    call other services or emit events.
    """

    def __init__(
        self,
        id: str,
        action: Optional[str] = None,
        event: Optional[str] = None,
        parent_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        broker: Optional["ServiceBroker"] = None,
    ) -> None:
        """Initialize a new Context instance.

        Args:
            id: Unique identifier for this context
            action: Name of the action being executed
            event: Name of the event being handled
            parent_id: ID of the parent context (for nested calls)
            params: Parameters passed to the action/event
            meta: Metadata associated with the request
            stream: Whether this is a streaming context
            broker: Reference to the service broker
        """
        self.id = id
        self.action = action
        self.event = event
        self.params = params or {}
        self.meta = meta or {}
        self.parent_id = parent_id
        self.stream = stream
        self._broker = broker

    @property
    def broker(self) -> Optional["ServiceBroker"]:
        """Get the service broker instance.

        Returns:
            The service broker instance or None if not set
        """
        return self._broker

    def unmarshall(self) -> Dict[str, Any]:
        """Convert context to dictionary format for serialization.

        Returns:
            Dictionary representation of the context
        """
        return {
            "id": self.id,
            "action": self.action,
            "event": self.event,
            "params": self.params,
            "meta": self.meta,
            "timeout": 0,
            "level": 1,
            "tracing": None,
            "parentID": self.parent_id,
            "stream": self.stream,
        }

    def marshall(self) -> Dict[str, Any]:
        """Convert context to dictionary format for serialization.

        Note: This method is identical to unmarshall() and is kept for compatibility.

        Returns:
            Dictionary representation of the context
        """
        return self.unmarshall()

    async def _prepare_meta(self, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Merge context metadata with provided metadata.

        Args:
            meta: Additional metadata to merge

        Returns:
            Merged metadata dictionary
        """
        if meta is None:
            meta = {}
        return {**self.meta, **meta}

    async def call(
        self,
        service_name: str,
        params: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Call another service action.

        Args:
            service_name: Name of the service action to call
            params: Parameters to pass to the service
            meta: Additional metadata for the call

        Returns:
            Result from the service call

        Raises:
            AttributeError: If broker is not available
        """
        if self._broker is None:
            raise AttributeError("Broker not available in context")

        if params is None:
            params = {}

        merged_meta = await self._prepare_meta(meta)
        return await self._broker.call(service_name, params, merged_meta)

    async def emit(
        self,
        service_name: str,
        params: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Emit an event to services.

        Args:
            service_name: Name of the event to emit
            params: Parameters to pass with the event
            meta: Additional metadata for the event

        Returns:
            Result from the emit operation

        Raises:
            AttributeError: If broker is not available
        """
        if self._broker is None:
            raise AttributeError("Broker not available in context")

        if params is None:
            params = {}

        await self._prepare_meta(meta)
        return await self._broker.emit(service_name, params)

    async def broadcast(
        self,
        service_name: str,
        params: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Broadcast an event to all services.

        Args:
            service_name: Name of the event to broadcast
            params: Parameters to pass with the event
            meta: Additional metadata for the event

        Returns:
            Result from the broadcast operation

        Raises:
            AttributeError: If broker is not available
        """
        if self._broker is None:
            raise AttributeError("Broker not available in context")

        if params is None:
            params = {}

        await self._prepare_meta(meta)
        return await self._broker.broadcast(service_name, params)
