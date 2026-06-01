"""
Schemas Pydantic para validación de datos de Propuesta.
"""
from pydantic import BaseModel, ConfigDict, model_validator
from datetime import datetime
from typing import Optional, List

from app.models.proposal import ProposalStatus, SchemeType
from app.models.approval import ApprovalAction, ApprovalRole


# --- Productos en Propuesta ---
class ProposalProductCreate(BaseModel):
    """Schema para agregar un producto a la propuesta."""
    product_name: str
    product_type: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class ProposalProductRead(BaseModel):
    """Schema para leer un producto de propuesta."""
    id: int
    product_name: str
    product_type: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Esquemas en Propuesta ---
class ProposalSchemeCreate(BaseModel):
    """Schema para seleccionar un esquema (al crear la propuesta).

    El contenido editable (scope, validity, etc.) es opcional al crear;
    si no se provee, queda vacío y se rellena posteriormente con el editor
    o con Innti.
    """
    scheme_type: SchemeType
    payment_frequency: Optional[str] = None
    scope_content: Optional[str] = None
    validity_period: Optional[str] = None
    economic_conditions: Optional[str] = None
    payment_terms: Optional[str] = None
    excluded_services: Optional[str] = None
    ip_section: Optional[str] = None


class ProposalSchemeUpdate(BaseModel):
    """Schema para editar el contenido de un esquema existente."""
    payment_frequency: Optional[str] = None
    scope_content: Optional[str] = None
    validity_period: Optional[str] = None
    economic_conditions: Optional[str] = None
    payment_terms: Optional[str] = None
    excluded_services: Optional[str] = None
    ip_section: Optional[str] = None


class ProposalSchemeRead(BaseModel):
    """Schema para leer un esquema."""
    id: int
    scheme_type: SchemeType
    payment_frequency: Optional[str] = None
    scope_content: Optional[str] = None
    validity_period: Optional[str] = None
    economic_conditions: Optional[str] = None
    payment_terms: Optional[str] = None
    excluded_services: Optional[str] = None
    ip_section: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Propuesta ---
class ProposalCreate(BaseModel):
    """Schema para crear una propuesta."""
    title: str
    code: Optional[str] = None
    client_id: int
    combine_schemes: bool = True
    products: List[ProposalProductCreate] = []
    schemes: List[ProposalSchemeCreate] = []

    @model_validator(mode="after")
    def _validate_combine_vs_schemes(self) -> "ProposalCreate":
        if not self.combine_schemes and len(self.schemes) < 2:
            raise ValueError(
                "combine_schemes=False requiere al menos 2 esquemas — "
                "no tiene sentido pedir 'Documentos separados' con un único esquema."
            )
        return self


class ProposalUpdate(BaseModel):
    """Schema para actualizar el contenido global de una propuesta."""
    title: Optional[str] = None
    cover_title: Optional[str] = None
    letter_content: Optional[str] = None
    context_content: Optional[str] = None
    confidentiality: Optional[str] = None
    combine_schemes: Optional[bool] = None


class ProposalRead(BaseModel):
    """Schema completo para leer una propuesta."""
    id: int
    title: str
    code: Optional[str] = None
    status: ProposalStatus
    combine_schemes: bool
    cover_title: Optional[str] = None
    letter_content: Optional[str] = None
    context_content: Optional[str] = None
    confidentiality: Optional[str] = None
    client_id: int
    products: List[ProposalProductRead] = []
    schemes: List[ProposalSchemeRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Aprobaciones ---
class ApprovalCreate(BaseModel):
    """Schema para registrar una aprobación/rechazo."""
    role: ApprovalRole
    approver_name: str
    approver_email: Optional[str] = None
    action: ApprovalAction
    comments: Optional[str] = None


class ApprovalRead(BaseModel):
    """Schema para leer una aprobación."""
    id: int
    proposal_id: int
    role: ApprovalRole
    approver_name: str
    approver_email: Optional[str] = None
    action: ApprovalAction
    comments: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
