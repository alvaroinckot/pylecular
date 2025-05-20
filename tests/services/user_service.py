from pylecular.service import Service
from pylecular.context import Context
from pylecular.decorators import action
import asyncio


class UserService(Service):
    name = "users"

    def __init__(self):
        super().__init__(self.name)
        # Simple in-memory database for demo purposes
        self.users = {
            "1": {"id": "1", "name": "John Doe", "email": "john@example.com"},
            "2": {"id": "2", "name": "Jane Smith", "email": "jane@example.com"},
            "3": {"id": "3", "name": "Bob Johnson", "email": "bob@example.com"}
        }
        self.next_id = 4

    @action(params=[])
    async def list(self, ctx: Context):
        return list(self.users.values())

    @action(params=["id"])
    async def get(self, ctx: Context):
        user_id = ctx.params.get("id")
        if not user_id or user_id not in self.users:
            return None
        return self.users[user_id]

    @action(params=["name", "email"])
    async def create(self, ctx: Context):
        name = ctx.params.get("name")
        email = ctx.params.get("email")
        
        if not name or not email:
            raise ValueError("Name and email are required")
            
        user_id = str(self.next_id)
        self.next_id += 1
        
        user = {
            "id": user_id,
            "name": name,
            "email": email
        }
        
        self.users[user_id] = user
        return user

    @action(params=["id", "name", "email"])
    async def update(self, ctx: Context):
        user_id = ctx.params.get("id")
        name = ctx.params.get("name")
        email = ctx.params.get("email")
        
        if not user_id or user_id not in self.users:
            raise ValueError("User not found")
            
        user = self.users[user_id]
        
        if name:
            user["name"] = name
        if email:
            user["email"] = email
            
        return user

    @action(params=["id"])
    async def delete(self, ctx: Context):
        user_id = ctx.params.get("id")
        
        if not user_id or user_id not in self.users:
            raise ValueError("User not found")
            
        user = self.users.pop(user_id)
        return user
