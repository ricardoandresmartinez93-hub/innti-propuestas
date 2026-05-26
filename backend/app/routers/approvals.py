"""
Endpoints para el flujo de aprobaciones de propuestas.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.proposal import Proposal, ProposalStatus
from app.models.approval import Approval
from app.schemas.proposal import ApprovalCreate, ApprovalRead
from app.services.approval_service import (
    ApprovalService, ApprovalError, InvalidTransitionError,
)

router = APIRouter(prefix="/api/proposals", tags=["Aprobaciones"])


def get_approval_service() -> ApprovalService:
    return ApprovalService()


@router.post("/{proposal_id}/submit-review", status_code=status.HTTP_200_OK)
def submit_for_review(
    proposal_id: int,
    db: Session = Depends(get_db),
    service: ApprovalService = Depends(get_approval_service),
):
    """Envía una propuesta a revisión (Ángela) o a VP según estado actual."""
    try:
        # Si está en DRAFT, va a PENDING_REVIEW
        # Si está en REVIEWED, va a PENDING_VP
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
             raise HTTPException(status_code=404, detail="Propuesta no encontrada")
             
        if proposal.status == ProposalStatus.DRAFT:
            proposal = service.submit_for_review(db, proposal_id)
        elif proposal.status == ProposalStatus.REVIEWED:
            # Transición manual a PENDING_VP
            proposal.status = ProposalStatus.PENDING_VP
            db.commit()
            db.refresh(proposal)
        elif proposal.status == ProposalStatus.APPROVED:
            # Transición a SENT_TO_CLIENT
            proposal = service.mark_sent_to_client(db, proposal_id)
        elif proposal.status == ProposalStatus.REJECTED:
            # Volver a DRAFT
            proposal.status = ProposalStatus.DRAFT
            db.commit()
            db.refresh(proposal)
        else:
            raise HTTPException(status_code=400, detail=f"No se puede avanzar desde {proposal.status}")
            
        return {"message": "Propuesta avanzada en el flujo", "status": proposal.status}
    except ApprovalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{proposal_id}/approve", response_model=ApprovalRead)
def approve_proposal(
    proposal_id: int,
    data: ApprovalCreate,
    db: Session = Depends(get_db),
    service: ApprovalService = Depends(get_approval_service),
):
    """Aprueba una propuesta (según rol: reviewer o VP)."""
    try:
        proposal = service.approve(
            db=db,
            proposal_id=proposal_id,
            approver_name=data.approver_name,
            approver_email=data.approver_email,
            role=data.role,
            comments=data.comments,
        )
        # Retornar la última aprobación registrada
        approval = (
            db.query(Approval)
            .filter(Approval.proposal_id == proposal_id)
            .order_by(Approval.created_at.desc())
            .first()
        )
        return approval
    except InvalidTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ApprovalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{proposal_id}/reject", response_model=ApprovalRead)
def reject_proposal(
    proposal_id: int,
    data: ApprovalCreate,
    db: Session = Depends(get_db),
    service: ApprovalService = Depends(get_approval_service),
):
    """Rechaza una propuesta."""
    try:
        proposal = service.reject(
            db=db,
            proposal_id=proposal_id,
            rejector_name=data.approver_name,
            rejector_email=data.approver_email,
            role=data.role,
            comments=data.comments,
        )
        approval = (
            db.query(Approval)
            .filter(Approval.proposal_id == proposal_id)
            .order_by(Approval.created_at.desc())
            .first()
        )
        return approval
    except InvalidTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ApprovalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{proposal_id}/approvals", response_model=List[ApprovalRead])
def get_proposal_approvals(proposal_id: int, db: Session = Depends(get_db)):
    """Obtiene el historial de aprobaciones de una propuesta."""
    approvals = (
        db.query(Approval)
        .filter(Approval.proposal_id == proposal_id)
        .order_by(Approval.created_at.desc())
        .all()
    )
    return approvals
