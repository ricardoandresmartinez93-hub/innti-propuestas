"""
Schemas Pydantic para validación de datos de Cliente.
"""
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional


class ClientCreate(BaseModel):
    """Schema para crear un cliente."""
    name: str
    position: Optional[str] = None
    entity: str
    country: Optional[str] = None
    department: Optional[str] = None
    city: Optional[str] = None
    email: Optional[str] = None


class ClientRead(BaseModel):
    """Schema para leer un cliente."""
    id: int
    name: str
    position: Optional[str] = None
    entity: str
    country: Optional[str] = None
    department: Optional[str] = None
    city: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientUpdate(BaseModel):
    """Schema para actualizar un cliente."""
    name: Optional[str] = None
    position: Optional[str] = None
    entity: Optional[str] = None
    country: Optional[str] = None
    department: Optional[str] = None
    city: Optional[str] = None
    email: Optional[str] = None
