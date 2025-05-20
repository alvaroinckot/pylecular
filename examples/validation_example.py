# Example of using action parameter validation
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # import pylecular
from pylecular.broker import Broker
from pylecular.context import Context
from pylecular.decorators import action
from pylecular.service import Service


class ValidationService(Service):
    name = "validator"

    def __init__(self):
        super().__init__(self.name)

    @action(params={
        "name": {
            "type": "string",
            "minLength": 2,
            "maxLength": 100,
            "required": True
        },
        "age": {
            "type": "number",
            "gte": 0,
            "lt": 150
        },
        "role": {
            "type": "string",
            "enum": ["admin", "user", "guest"]
        },
        "active": {
            "type": "boolean"
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "settings": "object"  # Shorthand for {"type": "object"}
    })
    async def create_user(self, ctx: Context):
        """Create a user with validated parameters."""
        name = ctx.params.get("name")
        age = ctx.params.get("age")
        role = ctx.params.get("role", "user")
        active = ctx.params.get("active", True)
        tags = ctx.params.get("tags", [])
        settings = ctx.params.get("settings", {})

        print(f"Creating user: {name}, age: {age}, role: {role}")
        print(f"Active: {active}, tags: {tags}, settings: {settings}")

        return {
            "id": "user-123",
            "name": name,
            "age": age,
            "role": role,
            "active": active,
            "tags": tags,
            "settings": settings,
            "created": True
        }

    # Simple validation with just type checking
    @action(params={
        "x": "number",
        "y": "number"
    })
    async def add(self, ctx: Context):
        """Add two numbers with type validation."""
        x = ctx.params.get("x", 0)
        y = ctx.params.get("y", 0)
        return x + y

    # List-style validation (just checks parameter existence)
    @action(params=["email", "password"])
    async def login(self, ctx: Context):
        """Login a user with required parameters."""
        email = ctx.params.get("email")
        password = ctx.params.get("password")
        
        # In a real app, you would authenticate the user here
        return {
            "token": "sample-jwt-token",
            "email": email,
            "success": True
        }


async def main():
    broker = Broker("validation-example")
    
    # Register our service with parameter validation
    broker.register(ValidationService())
    
    # Start the broker
    print("Starting broker...")
    await broker.start()
    
    print("\n1. Calling create_user with valid parameters:")
    try:
        result = await broker.call("validator.create_user", {
            "name": "John Doe",
            "age": 30,
            "role": "admin",
            "active": True,
            "tags": ["developer", "python"],
            "settings": {"theme": "dark", "notifications": True}
        })
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n2. Calling create_user with invalid age (negative):")
    try:
        result = await broker.call("validator.create_user", {
            "name": "Jane Smith",
            "age": -5,  # Invalid: age must be >= 0
            "role": "user"
        })
        print(f"Result: {result}")
    except Exception as e:
        print(f"✅ Caught expected validation error: {e}")

    print("\n3. Calling create_user with invalid role:")
    try:
        result = await broker.call("validator.create_user", {
            "name": "Bob Johnson",
            "age": 25,
            "role": "superadmin"  # Invalid: not in enum
        })
        print(f"Result: {result}")
    except Exception as e:
        print(f"✅ Caught expected validation error: {e}")

    print("\n4. Calling create_user without required name:")
    try:
        result = await broker.call("validator.create_user", {
            "age": 40,
            "role": "user"
        })
        print(f"Result: {result}")
    except Exception as e:
        print(f"✅ Caught expected validation error: {e}")

    print("\n5. Calling add with valid parameters:")
    try:
        result = await broker.call("validator.add", {"x": 10, "y": 20})
        print(f"✅ 10 + 20 = {result}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print("\n6. Calling add with invalid parameters:")
    try:
        result = await broker.call("validator.add", {"x": "10", "y": 20})  # x should be a number
        print(f"Result: {result}")
    except Exception as e:
        print(f"✅ Caught expected validation error: {e}")

    print("\n7. Calling login with valid parameters:")
    try:
        result = await broker.call("validator.login", {
            "email": "user@example.com",
            "password": "secret123"
        })
        print(f"✅ Login successful: {result}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print("\n8. Calling login with missing parameters:")
    try:
        result = await broker.call("validator.login", {
            "email": "user@example.com"
            # Missing required password parameter
        })
        print(f"Result: {result}")
    except Exception as e:
        print(f"✅ Caught expected validation error: {e}")

    # Stop the broker
    print("\nShutting down...")
    await broker.stop()


if __name__ == "__main__":
    asyncio.run(main())
