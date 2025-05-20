from pylecular.context import Context
from pylecular.decorators import action, event
from pylecular.service import Service


class MathService(Service):
    name = "math"

    def __init__(self):
        super().__init__(self.name)

    @action(params=["a", "b"])
    async def add(self, ctx: Context):
        a = float(ctx.params.get("a", 0))
        b = float(ctx.params.get("b", 0))
        return a + b

    @action(params=["a", "b"])
    async def subtract(self, ctx: Context):
        a = float(ctx.params.get("a", 0))
        b = float(ctx.params.get("b", 0))
        return a - b

    @action(params=["a", "b"])
    async def multiply(self, ctx: Context):
        a = float(ctx.params.get("a", 0))
        b = float(ctx.params.get("b", 0))
        return a * b
        
    @action(params=["a", "b"])
    async def divide(self, ctx: Context):
        a = float(ctx.params.get("a", 0))
        b = float(ctx.params.get("b", 1))
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    @event()
    async def calculation_performed(self, ctx: Context):
        operation = ctx.params.get("operation")
        result = ctx.params.get("result")
        print(f"Calculation performed: {operation} = {result}")
