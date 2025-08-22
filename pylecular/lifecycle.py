"""Lifecycle management for contexts in the Pylecular framework.

This module provides lifecycle management capabilities for request contexts,
including creation, rebuilding, and cleanup of execution contexts.
"""

import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from .context import Context

if TYPE_CHECKING:
    from .broker import ServiceBroker


class Lifecycle:
    """Manages the lifecycle of execution contexts within a Pylecular node.

    The Lifecycle class is responsible for creating and managing Context instances
    that represent the execution environment for service actions and events.
    """

    def __init__(self, broker: "ServiceBroker") -> None:
        """Initialize a new Lifecycle instance.

        Args:
            broker: Reference to the service broker
        """
        self.broker = broker

    def create_context(
        self,
        context_id: Optional[Union[str, uuid.UUID]] = None,
        event: Optional[str] = None,
        action: Optional[str] = None,
        parent_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> Context:
        """Create a new execution context.

        Args:
            context_id: Unique identifier for the context. If None, a UUID will be generated
            event: Name of the event being handled
            action: Name of the action being executed
            parent_id: ID of the parent context for nested calls
            params: Parameters for the action/event
            meta: Metadata associated with the request
            stream: Whether this is a streaming context

        Returns:
            New Context instance
        """
        if context_id is None:
            context_id = uuid.uuid4()

        return Context(
            id=str(context_id),
            action=action,
            event=event,
            parent_id=parent_id,
            params=params,
            meta=meta,
            stream=stream,
            broker=self.broker,
        )

    def rebuild_context(self, context_dict: Dict[str, Any]) -> Context:
        """Rebuild a context from a dictionary representation.

        This is typically used when reconstructing contexts from serialized
        data received over the network.

        Args:
            context_dict: Dictionary containing context data

        Returns:
            Reconstructed Context instance
        """
        return Context(
            id=str(context_dict.get("id", uuid.uuid4())),
            action=context_dict.get("action"),
            event=context_dict.get("event"),
            parent_id=context_dict.get("parent_id"),
            params=context_dict.get("params"),
            meta=context_dict.get("meta"),
            stream=context_dict.get("stream", False),
            broker=self.broker,
        )
