"""
Modelo de Usuario para el sistema de propuestas.
"""
import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from datetime import datetime, timezone

from app.database import Base


class UserRole(str, enum.Enum):
    """
    Roles de usuario definidos para el sistema.
    Los roles son configurables y no están limitados a personas específicas.
    """
    creator = "creator"
    approver_1 = "approver_1"
    approver_2 = "approver_2"
    viewer = "viewer"


class User(Base):
    """
    Representa un usuario del sistema con un rol específico.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=True, comment="Contraseña hasheada con bcrypt")
    role = Column(Enum(UserRole), default=UserRole.creator, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
