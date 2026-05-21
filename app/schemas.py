from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Literal, Optional

# --- User Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=1, max_length=50)

class UserResponse(BaseModel):
    email: EmailStr
    username: str

    class Config:
        from_attributes = True

# --- Task Schemas ---
class TaskCreate(BaseModel):
    creator_email: EmailStr
    title: str = Field(..., min_length=1)
    type: Literal["PERSONAL", "GLOBAL"]

class TaskResponse(BaseModel):
    task_id: UUID
    creator_email: EmailStr
    title: str
    type: Literal["PERSONAL", "GLOBAL"]
    status: Literal["PENDING", "COMPLETED"] = "PENDING"
    created_at: datetime

    class Config:
        from_attributes = True

class TaskOtherResponse(BaseModel):
    task_id: UUID
    creator_email: EmailStr
    creator_username: str
    title: str
    type: Literal["PERSONAL", "GLOBAL"]
    created_at: datetime

    class Config:
        from_attributes = True

# --- Task Status Schemas ---
class TaskStatusUpdate(BaseModel):
    email: EmailStr
    status: Literal["PENDING", "COMPLETED"]

class TaskStatusResponse(BaseModel):
    task_id: UUID
    email: EmailStr
    status: Literal["PENDING", "COMPLETED"]

    class Config:
        from_attributes = True
