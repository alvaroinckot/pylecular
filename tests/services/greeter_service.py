
from pylecular.context import Context
from pylecular.decorators import action, event
from pylecular.service import Service


class GreeterService(Service):
    name = "greeter"

    def __init__(self):
        super().__init__(self.name)

    @action(params=["name"])
    async def hello(self, ctx: Context):
        name = ctx.params.get("name", "World")
        message = f"Hello, {name}!"
        
        # Emit a greeting event
        await ctx.emit("greeter.greeting", {"name": name, "message": message})
        
        return message

    @action(params=["name"])
    async def welcome(self, ctx: Context):
        name = ctx.params.get("name", "Guest")
        return f"Welcome to Pylecular, {name}!"

    @action(params=[])
    async def goodbye(self, ctx: Context):
        return "Goodbye! Thank you for using Pylecular!"
        
    @event(name="greeting")
    async def on_greeting(self, ctx: Context):
        name = ctx.params.get("name")
        message = ctx.params.get("message")
        print(f"Greeting event received: {message} for {name}")
