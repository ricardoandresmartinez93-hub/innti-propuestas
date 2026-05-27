"""
Modelo de Cliente para propuestas comerciales.
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Client(Base):
    """Datos del cliente destinatario de la propuesta."""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="Nombre del contacto")
    position = Column(String(200), nullable=True, comment="Cargo del contacto")
    entity = Column(String(300), nullable=False, comment="Nombre de la entidad/empresa")
    country = Column(String(100), nullable=True, comment="País del cliente")
    department = Column(String(200), nullable=True, comment="Área o departamento")
    city = Column(String(100), nullable=True, comment="Ciudad")
    email = Column(String(200), nullable=True, comment="Email del contacto")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones
    proposals = relationship("Proposal", back_populates="client")

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name='{self.name}', entity='{self.entity}')>"
