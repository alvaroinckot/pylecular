from pylecular.context import Context
from pylecular.decorators import action, event
from pylecular.service import Service


class ValidationService(Service):
    name = "validators"

    def __init__(self):
        super().__init__(self.name)
        self.stored_data = {}

    # Using list-style validation
    @action(params=["id", "data"])
    async def store(self, ctx: Context):
        """Store data with required params."""
        id = ctx.params.get("id")
        data = ctx.params.get("data")

        self.stored_data[id] = data
        return {"success": True, "message": f"Data stored with ID: {id}"}

    # Using dict-style validation with simple types
    @action(params={"id": "string", "limit": "number", "detailed": "boolean"})
    async def retrieve(self, ctx: Context):
        """Retrieve data with type validation."""
        id = ctx.params.get("id")
        limit = ctx.params.get("limit", 10)  # Default to 10 if not provided
        detailed = ctx.params.get("detailed", False)  # Default to false

        if id not in self.stored_data:
            return {"success": False, "message": "ID not found"}

        data = self.stored_data[id]

        if isinstance(data, list):
            data = data[:limit]  # Apply limit if data is a list

        result = {"success": True, "id": id, "data": data}

        if detailed:
            result["timestamp"] = "2025-05-20T18:00:00Z"
            result["size"] = len(str(data))

        return result

    # Using complex schema validation
    @action(
        params={
            "user": {"type": "object", "required": True},
            "user.name": {"type": "string", "minLength": 3, "maxLength": 50, "required": True},
            "user.email": {
                "type": "string",
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "required": True,
            },
            "user.age": {"type": "number", "gte": 18},
            "user.preferences": {"type": "object"},
            "role": {
                "type": "string",
                "enum": ["admin", "manager", "user", "guest"],
                "default": "user",
            },
            "permissions": {"type": "array", "items": {"type": "string"}},
        }
    )
    async def register(self, ctx: Context):
        """Register a user with complex validation."""
        user = ctx.params.get("user")
        role = ctx.params.get("role", "user")  # Default to user if not provided
        permissions = ctx.params.get("permissions", [])  # Default to empty list

        # Generate a unique ID
        user_id = f"user-{len(self.stored_data) + 1}"

        # Store the user data
        self.stored_data[user_id] = {
            "id": user_id,
            "user": user,
            "role": role,
            "permissions": permissions,
            "active": True,
        }

        # Emit registration event
        await ctx.emit("user.registered", {"id": user_id, "email": user["email"]})

        return {"success": True, "message": "User registered successfully", "userId": user_id}

    @event(name="user.registered")
    async def on_user_registered(self, ctx: Context):
        """Handle user registration event."""
        user_id = ctx.params.get("id")
        email = ctx.params.get("email")
        print(f"User registered event: ID={user_id}, email={email}")
