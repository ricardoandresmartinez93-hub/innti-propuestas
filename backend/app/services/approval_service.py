"""
Servicio de flujo de aprobaciones.
Gestiona las transiciones de estado de las propuestas.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.proposal import Proposal, ProposalStatus
from app.models.approval import Approval, ApprovalAction, ApprovalRole
from app.services.email_service import EmailService


class ApprovalError(Exception):
    """Error en el flujo de aprobaciones."""
    pass


class InvalidTransitionError(ApprovalError):
    """Transición de estado inválida."""
    pass


# Transiciones válidas del flujo de aprobación
VALID_TRANSITIONS = {
    ProposalStatus.DRAFT: [ProposalStatus.PENDING_REVIEW],
    ProposalStatus.PENDING_REVIEW: [ProposalStatus.REVIEWED, ProposalStatus.REJECTED],
    ProposalStatus.REVIEWED: [ProposalStatus.PENDING_VP],
    ProposalStatus.PENDING_VP: [ProposalStatus.APPROVED, ProposalStatus.REJECTED],
    ProposalStatus.APPROVED: [ProposalStatus.SENT_TO_CLIENT],
    ProposalStatus.REJECTED: [ProposalStatus.DRAFT],  # Puede volver a borrador
    ProposalStatus.SENT_TO_CLIENT: [],  # Estado final
}

# Roles requeridos para cada transición de aprobación
REQUIRED_ROLE = {
    ProposalStatus.REVIEWED: ApprovalRole.REVIEWER,     # Ángela aprueba
    ProposalStatus.APPROVED: ApprovalRole.VP,            # Juan Pablo aprueba
}


class ApprovalService:
    """Gestiona el flujo de aprobaciones de propuestas."""

    def __init__(self):
        self.email_service = EmailService()

    def can_transition(
        self, current_status: ProposalStatus, new_status: ProposalStatus
    ) -> bool:
        """Verifica si una transición de estado es válida."""
        return new_status in VALID_TRANSITIONS.get(current_status, [])

    def submit_for_review(
        self, db: Session, proposal_id: int
    ) -> Proposal:
        """Envía una propuesta a revisión (Ángela)."""
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise ApprovalError(f"Propuesta {proposal_id} no encontrada")

        if not self.can_transition(proposal.status, ProposalStatus.PENDING_REVIEW):
            raise InvalidTransitionError(
                f"No se puede enviar a revisión desde estado '{proposal.status}'"
            )

        proposal.status = ProposalStatus.PENDING_REVIEW
        db.commit()
        db.refresh(proposal)
        return proposal

    def approve(
        self,
        db: Session,
        proposal_id: int,
        approver_name: str,
        approver_email: Optional[str],
        role: ApprovalRole,
        comments: Optional[str] = None,
    ) -> Proposal:
        """Registra una aprobación y avanza el estado."""
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise ApprovalError(f"Propuesta {proposal_id} no encontrada")

        # Determinar nuevo estado según el rol
        if role == ApprovalRole.REVIEWER:
            new_status = ProposalStatus.REVIEWED
        elif role == ApprovalRole.VP:
            new_status = ProposalStatus.APPROVED
        else:
            raise ApprovalError(f"Rol desconocido: {role}")

        if not self.can_transition(proposal.status, new_status):
            raise InvalidTransitionError(
                f"No se puede aprobar desde estado '{proposal.status}' con rol '{role}'"
            )

        # Registrar aprobación
        approval = Approval(
            proposal_id=proposal_id,
            role=role,
            approver_name=approver_name,
            approver_email=approver_email,
            action=ApprovalAction.APPROVED,
            comments=comments,
        )
        db.add(approval)

        # Actualizar estado
        proposal.status = new_status
        db.commit()
        db.refresh(proposal)
        return proposal

    def reject(
        self,
        db: Session,
        proposal_id: int,
        rejector_name: str,
        rejector_email: Optional[str],
        role: ApprovalRole,
        comments: Optional[str] = None,
    ) -> Proposal:
        """Registra un rechazo y regresa a borrador."""
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise ApprovalError(f"Propuesta {proposal_id} no encontrada")

        if not self.can_transition(proposal.status, ProposalStatus.REJECTED):
            raise InvalidTransitionError(
                f"No se puede rechazar desde estado '{proposal.status}'"
            )

        # Registrar rechazo
        approval = Approval(
            proposal_id=proposal_id,
            role=role,
            approver_name=rejector_name,
            approver_email=rejector_email,
            action=ApprovalAction.REJECTED,
            comments=comments,
        )
        db.add(approval)

        proposal.status = ProposalStatus.REJECTED
        db.commit()
        db.refresh(proposal)
        return proposal

    def mark_sent_to_client(self, db: Session, proposal_id: int) -> Proposal:
        """Marca una propuesta como enviada al cliente."""
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise ApprovalError(f"Propuesta {proposal_id} no encontrada")

        if not self.can_transition(proposal.status, ProposalStatus.SENT_TO_CLIENT):
            raise InvalidTransitionError(
                f"No se puede marcar como enviada desde estado '{proposal.status}'"
            )

        proposal.status = ProposalStatus.SENT_TO_CLIENT
        db.commit()
        db.refresh(proposal)
        return proposal
