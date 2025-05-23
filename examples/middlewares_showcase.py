import asyncio
import time  # For EnrichContextMiddleware

from pylecular.broker import Broker
from pylecular.decorators import action, event
from pylecular.middleware import Middleware
from pylecular.service import Service

# --- Custom Middlewares ---


class LoggingMiddleware(Middleware):
    """
    Logs details about local action calls and event emissions.
    """

    # Implement the broker lifecycle hooks
    def broker_created(self, broker):
        print(f"[LOGGING_MW] Broker '{broker.id}' created.")

    async def broker_started(self, broker):
        print(f"[LOGGING_MW] Broker '{broker.id}' started.")

    async def broker_stopped(self, broker):
        print(f"[LOGGING_MW] Broker '{broker.id}' stopped.")

    async def service_created(self, service):
        print(f"[LOGGING_MW] Service '{service.name}' created.")

    async def service_started(self, service):
        print(f"[LOGGING_MW] Service '{service.name}' started.")

    async def service_stopped(self, service):
        print(f"[LOGGING_MW] Service '{service.name}' stopped.")

    async def local_action(self, next_handler, action_endpoint):
        # This method is called when the broker is setting up the action handler chain.
        # It returns a wrapped handler.
        print(f"[LOGGING_MW] '{action_endpoint.name}' action is being prepared with logging.")

        async def wrapped_handler(ctx):
            # This wrapped_handler is called when the action is actually invoked.
            print(
                f"[LOGGING_MW] ---> Calling action '{action_endpoint.name}' | Params: {ctx.params} | Meta: {ctx.meta}"
            )
            result = await next_handler(ctx)
            print(f"[LOGGING_MW] <--- Action '{action_endpoint.name}' finished | Result: {result}")
            return result

        return wrapped_handler

    async def local_event(self, next_handler, event_endpoint):
        # This method is called when the broker is setting up the event handler chain.
        print(f"[LOGGING_MW] '{event_endpoint.name}' event is being prepared with logging.")

        async def wrapped_handler(ctx):
            # This wrapped_handler is called when the event is actually emitted/broadcast.
            print(
                f"[LOGGING_MW] ---> Emitting event '{event_endpoint.name}' | Params: {ctx.params} | Meta: {ctx.meta}"
            )
            await next_handler(ctx)
            print(f"[LOGGING_MW] <--- Event '{event_endpoint.name}' handler finished.")

        return wrapped_handler


class EnrichContextMiddleware(Middleware):
    """
    Enriches the context by adding a timestamp to ctx.meta for local actions.
    """

    # Lifecycle hooks
    def broker_created(self, broker):
        print(f"[ENRICH_MW] Broker '{broker.id}' created.")

    async def broker_started(self, broker):
        print(f"[ENRICH_MW] Broker '{broker.id}' started.")

    async def broker_stopped(self, broker):
        print(f"[ENRICH_MW] Broker '{broker.id}' stopped.")

    async def service_created(self, service):
        print(f"[ENRICH_MW] Service '{service.name}' created.")

    async def service_started(self, service):
        print(f"[ENRICH_MW] Service '{service.name}' started.")

    async def service_stopped(self, service):
        print(f"[ENRICH_MW] Service '{service.name}' stopped.")

    async def local_action(self, next_handler, action_endpoint):
        print(
            f"[ENRICH_MW] '{action_endpoint.name}' action is being prepared with context enrichment."
        )

        async def wrapped_handler(ctx):
            timestamp = time.time()
            ctx.meta["request_timestamp"] = timestamp
            print(
                f"[ENRICH_MW] Added 'request_timestamp' ({timestamp:.6f}) to meta for action '{action_endpoint.name}'."
            )
            return await next_handler(ctx)

        return wrapped_handler


# --- Simple Service ---


class GreeterService(Service):
    """
    A simple service to demonstrate middleware effects.
    """

    def __init__(self):
        super().__init__("greeter")  # Service name is 'greeter'

    @action()  # Action name will be 'greeter.say_hello'
    async def say_hello(self, ctx):
        name = ctx.params.get("name", "Anonymous")
        timestamp = ctx.meta.get("request_timestamp", "not available")
        # Format timestamp for readability if it's a float
        if isinstance(timestamp, float):
            timestamp_str = f"{timestamp:.6f}"
        else:
            timestamp_str = str(timestamp)

        greeting = f"Hello, {name}! (Request time: {timestamp_str})"
        print(
            f"[SERVICE_ACTION] GreeterService.say_hello: Processing request. Meta received: {ctx.meta}"
        )
        return {"greeting": greeting, "meta_received": ctx.meta.copy()}

    @event()  # Event name will be 'greeter.item_updated'
    async def item_updated(self, ctx):
        item_id = ctx.params.get("item_id", "unknown_item")
        print(
            f"[SERVICE_EVENT] GreeterService.item_updated: Item '{item_id}' was updated. Params: {ctx.params}, Meta: {ctx.meta}"
        )


# --- Main ---
async def main():
    print("--- Initializing Middlewares and Broker ---")
    # Instantiate middlewares
    logging_mw = LoggingMiddleware()
    enrich_mw = EnrichContextMiddleware()

    # Configure broker with middlewares. Order: [logging_mw, enrich_mw]
    # This means enrich_mw's local_action wrapper is applied first (inner),
    # then logging_mw's local_action wrapper (outer).
    # So, logging_mw will log the meta enriched by enrich_mw.
    broker = Broker(id="eg-broker-mw", middlewares=[logging_mw, enrich_mw])
    print(
        f"Broker '{broker.id}' created with middlewares: {[mw.__class__.__name__ for mw in broker.middlewares]}"
    )

    # Register service
    greeter_service = GreeterService()
    await broker.register(greeter_service)
    print(f"Service '{greeter_service.name}' registered.")

    # Start broker
    print("\n--- Starting Broker ---")
    await broker.start()
    print("Broker started.")

    # Call action
    print("\n--- Calling 'greeter.say_hello' action ---")
    action_params = {"name": "Alice"}
    action_result = await broker.call("greeter.say_hello", params=action_params)
    print(f"Action call final result received by caller: {action_result}\n")

    # Emit event
    print("--- Emitting 'greeter.item_updated' event ---")
    event_params = {"item_id": "book-123", "status": "sold"}
    await broker.emit("greeter.item_updated", params=event_params)
    print("\nEvent emitted.")

    print("\n--- Stopping Broker ---")
    await broker.stop()
    print("Broker stopped.")


if __name__ == "__main__":
    asyncio.run(main())
