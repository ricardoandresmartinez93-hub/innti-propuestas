"""
Modelos de Propuesta Comercial.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from typing import Optional
import enum

from app.database import Base


class ProposalStatus(str, enum.Enum):
    """Estados de una propuesta en el flujo de aprobación."""
    DRAFT = "draft"                    # Borrador - en edición
    PENDING_REVIEW = "pending_review"  # Enviada a revisión (Ángela)
    REVIEWED = "reviewed"              # Aprobada por Ángela, pendiente VP
    PENDING_VP = "pending_vp"          # Enviada a VP (Juan Pablo)
    APPROVED = "approved"              # Aprobada por VP
    REJECTED = "rejected"              # Rechazada (en cualquier etapa)
    SENT_TO_CLIENT = "sent_to_client"  # Enviada al cliente


class SchemeType(str, enum.Enum):
    """Tipos de esquema de propuesta."""
    LICENSING = "licensing"                   # Licenciamiento
    SERVICES = "services"                     # Prestación de Servicios
    SUPPORT_MAINTENANCE = "support_maintenance"  # Soporte y Mantenimiento
    CONCESSION_BPO = "concession_bpo"         # Fase 2 – No disponible en MVP
    SUPPLY = "supply"                         # Fase 2 – No disponible en MVP


MVP_SCHEME_TYPES = {SchemeType.LICENSING, SchemeType.SERVICES, SchemeType.SUPPORT_MAINTENANCE}
"""Esquemas disponibles en el MVP. Concesión/BPO y Suministro son para versiones futuras."""


class Proposal(Base):
    """Propuesta comercial principal.

    Contenido global (compartido por todos los esquemas):
        - cover_title, letter_content, context_content, confidentiality.

    Contenido por esquema (alcance, plazo, condiciones económicas, forma de pago,
    servicios excluidos, propiedad intelectual) vive en ProposalScheme — esto permite
    que "Documentos separados" produzca documentos realmente diferenciados.
    """
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, comment="Título de la propuesta")
    code = Column(String(50), nullable=True, comment="Código interno (ej: 3018-0226)")
    status = Column(
        Enum(ProposalStatus),
        default=ProposalStatus.DRAFT,
        nullable=False,
        comment="Estado actual en el flujo de aprobación"
    )
    combine_schemes = Column(
        Boolean, default=True,
        comment="True=combinar esquemas en un documento, False=documentos separados"
    )

    # Contenido global editable (HTML del editor TipTap)
    cover_title = Column(String(500), nullable=True, comment="Título de portada")
    letter_content = Column(Text, nullable=True, comment="Carta de presentación (global)")
    context_content = Column(Text, nullable=True, comment="Contexto/introducción (global)")
    confidentiality = Column(Text, nullable=True, comment="Confidencialidad y ética (global)")

    # Relaciones
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    client = relationship("Client", back_populates="proposals")
    products = relationship("ProposalProduct", back_populates="proposal", cascade="all, delete-orphan")
    schemes = relationship("ProposalScheme", back_populates="proposal", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="proposal", cascade="all, delete-orphan")

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    @property
    def client_entity(self) -> Optional[str]:
        return self.client.entity if self.client else None

    def __repr__(self) -> str:
        return f"<Proposal(id={self.id}, title='{self.title}', status='{self.status}')>"


class ProposalProduct(Base):
    """Producto/servicio del portafolio incluido en una propuesta."""
    __tablename__ = "proposal_products"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False)
    product_name = Column(String(300), nullable=False, comment="Nombre del producto/servicio")
    product_type = Column(String(100), nullable=True, comment="Tipo: Plataforma o Servicio")
    description = Column(Text, nullable=True, comment="Descripción de la solución")
    category = Column(String(200), nullable=True, comment="Categoría (nuevo/modernización)")

    # Relación
    proposal = relationship("Proposal", back_populates="products")

    def __repr__(self) -> str:
        return f"<ProposalProduct(id={self.id}, product='{self.product_name}')>"


class ProposalScheme(Base):
    """Esquema de propuesta seleccionado, con contenido propio por esquema.

    Cada esquema (licensing, services, support_maintenance) tiene su propio alcance,
    plazo, condiciones económicas, forma de pago, servicios excluidos y propiedad
    intelectual. Cuando combine_schemes=False, cada esquema se exporta como un
    documento independiente usando estos campos.
    """
    __tablename__ = "proposal_schemes"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False)
    scheme_type = Column(Enum(SchemeType), nullable=False, comment="Tipo de esquema")
    payment_frequency = Column(
        String(50), nullable=True,
        comment="Frecuencia de pago: unico, mensual, anual"
    )

    # Contenido editable por esquema
    scope_content = Column(Text, nullable=True, comment="Alcance específico de este esquema")
    validity_period = Column(Text, nullable=True, comment="Plazo/vigencia de este esquema")
    economic_conditions = Column(Text, nullable=True, comment="Condiciones económicas de este esquema")
    payment_terms = Column(Text, nullable=True, comment="Forma de pago de este esquema")
    excluded_services = Column(Text, nullable=True, comment="Servicios excluidos de este esquema (SaaS suele quedar vacío)")
    ip_section = Column(Text, nullable=True, comment="Propiedad intelectual aplicable a este esquema")

    # Relación
    proposal = relationship("Proposal", back_populates="schemes")

    def __repr__(self) -> str:
        return f"<ProposalScheme(id={self.id}, type='{self.scheme_type}')>"
