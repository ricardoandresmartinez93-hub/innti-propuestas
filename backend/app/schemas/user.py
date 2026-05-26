"""
Esquemas de Pydantic para el modelo User.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base para esquemas de usuario."""
    full_name: str
    email: EmailStr
    role: UserRole = UserRole.creator


class UserCreate(UserBase):
    """Esquema para creación de usuario."""
    pass


class UserUpdate(BaseModel):
    """Esquema para actualización de usuario."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    """Esquema para lectura de usuario."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
