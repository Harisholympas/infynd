"""Memory API routes"""
from fastapi import APIRouter
from memory.manager import memory_manager
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class UserMemoryUpdate(BaseModel):
    user_id: str = "default"
    department: Optional[str] = None
    role: Optional[str] = None
    action: Optional[str] = None


@router.get("/user/{user_id}")
async def get_user_memory(user_id: str):
    return await memory_manager.get_user_memory(user_id)


@router.put("/user")
async def update_user_memory(data: UserMemoryUpdate):
    return await memory_manager.update_user_memory(
        data.user_id, data.department, data.role, data.action
    )


@router.get("/department/{department}")
async def get_department_memory(department: str):
    return await memory_manager.get_department_memory(department)
