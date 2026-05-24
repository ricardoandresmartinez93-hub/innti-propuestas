"""
Modelo de Aprobaciones para el flujo de revisión.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


class ApprovalAction(str, enum.Enum):
    """Acciones posibles en una aprobación."""
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalRole(str, enum.Enum):
    """Roles de aprobación."""
    REVIEWER = "reviewer"    # Ángela - primera revisión
    VP = "vp"                # Juan Pablo - aprobación final


class Approval(Base):
    """Registro de aprobación/rechazo de una propuesta."""
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False)
    role = Column(Enum(ApprovalRole), nullable=False, comment="Rol del aprobador")
    approver_name = Column(String(200), nullable=False, comment="Nombre del aprobador")
    approver_email = Column(String(200), nullable=True, comment="Email del aprobador")
    action = Column(Enum(ApprovalAction), nullable=False, comment="Acción tomada")
    comments = Column(Text, nullable=True, comment="Comentarios de la aprobación/rechazo")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relación
    proposal = relationship("Proposal", back_populates="approvals")

    def __repr__(self) -> str:
        return f"<Approval(id={self.id}, role='{self.role}', action='{self.action}')>"
