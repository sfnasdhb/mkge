from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, EmailStr


class UserRole(str, Enum):
    admin = "admin"
    researcher = "researcher"
    viewer = "viewer"


class User(BaseModel):
    id: UUID
    email: str
    password_hash: str
    full_name: str
    role: UserRole
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
