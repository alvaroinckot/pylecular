from pylecular.service import Service
from pylecular.context import Context
from pylecular.decorators import action, event
import asyncio
import time


class MonitorService(Service):
    name = "monitor"

    def __init__(self):
        super().__init__(self.name)
        self.start_time = time.time()
        self.metrics = {
            "requests_processed": 0,
            "errors": 0,
            "last_request_time": None
        }
        self.health_status = "healthy"

    @action(params=[])
    async def health(self, ctx: Context):
        return {
            "status": self.health_status,
            "uptime": time.time() - self.start_time,
        }

    @action(params=[])
    async def metrics(self, ctx: Context):
        return self.metrics

    @action(params=["status"])
    async def set_health(self, ctx: Context):
        status = ctx.params.get("status")
        if status in ["healthy", "degraded", "unhealthy"]:
            self.health_status = status
            await ctx.emit("monitor.health_changed", {"status": status})
            return {"success": True, "status": status}
        return {"success": False, "error": "Invalid status"}
    
    @event()
    async def request_processed(self, ctx: Context):
        self.metrics["requests_processed"] += 1
        self.metrics["last_request_time"] = time.time()
        
    @event()
    async def error_occurred(self, ctx: Context):
        self.metrics["errors"] += 1
