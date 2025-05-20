
from pylecular.context import Context
from pylecular.decorators import action
from pylecular.service import Service


class ApiGatewayService(Service):
    name = "api"

    def __init__(self):
        super().__init__(self.name)

    @action(params=["service", "action", "params"])
    async def call(self, ctx: Context):
        """Gateway to call other services"""
        service = ctx.params.get("service")
        action = ctx.params.get("action")
        params = ctx.params.get("params", {})
        
        if not service or not action:
            return {"success": False, "error": "Service and action are required"}
        
        try:
            # Call the requested service action
            result = await ctx.call(f"{service}.{action}", params)
            
            # Log the call
            await ctx.emit("monitor.request_processed", {
                "service": service, 
                "action": action,
                "success": True
            })
            
            return {"success": True, "data": result}
        except Exception as e:
            # Log the error
            await ctx.emit("monitor.error_occurred", {
                "service": service,
                "action": action,
                "error": str(e)
            })
            
            return {"success": False, "error": str(e)}

    @action(params=[])
    async def services(self, ctx: Context):
        """List all available services"""
        # This would typically come from registry in a real implementation
        # For this example, we're hard-coding the available services
        return [
            {"name": "math", "actions": ["add", "subtract", "multiply", "divide"]},
            {"name": "greeter", "actions": ["hello", "welcome", "goodbye"]},
            {"name": "users", "actions": ["list", "get", "create", "update", "delete"]},
            {"name": "monitor", "actions": ["health", "metrics", "set_health"]},
        ]
