"""
Pruebas unitarias para el servicio de aprobaciones.
"""
import pytest
from app.models.proposal import Proposal, ProposalStatus
from app.models.client import Client
from app.models.approval import ApprovalRole, ApprovalAction, Approval
from app.services.approval_service import (
    ApprovalService, ApprovalError, InvalidTransitionError,
)


class TestApprovalService:
    """Tests del flujo de aprobaciones."""

    def _create_proposal(self, db_session, status=ProposalStatus.DRAFT):
        """Helper para crear una propuesta con cliente."""
        client = Client(name="Test", entity="Test Entity")
        db_session.add(client)
        db_session.flush()

        proposal = Proposal(
            title="Test Proposal", client_id=client.id, status=status
        )
        db_session.add(proposal)
        db_session.commit()
        db_session.refresh(proposal)
        return proposal

    def test_valid_transitions(self):
        """Verifica que las transiciones válidas son aceptadas."""
        service = ApprovalService()
        assert service.can_transition(ProposalStatus.DRAFT, ProposalStatus.PENDING_REVIEW)
        assert service.can_transition(ProposalStatus.PENDING_REVIEW, ProposalStatus.REVIEWED)
        assert service.can_transition(ProposalStatus.PENDING_VP, ProposalStatus.APPROVED)

    def test_invalid_transitions(self):
        """Verifica que las transiciones inválidas son rechazadas."""
        service = ApprovalService()
        assert not service.can_transition(ProposalStatus.DRAFT, ProposalStatus.APPROVED)
        assert not service.can_transition(ProposalStatus.APPROVED, ProposalStatus.DRAFT)
        assert not service.can_transition(ProposalStatus.SENT_TO_CLIENT, ProposalStatus.DRAFT)

    def test_submit_for_review(self, db_session):
        """Debe cambiar estado de DRAFT a PENDING_REVIEW."""
        service = ApprovalService()
        proposal = self._create_proposal(db_session)

        result = service.submit_for_review(db_session, proposal.id)
        assert result.status == ProposalStatus.PENDING_REVIEW

    def test_submit_for_review_invalid_state(self, db_session):
        """No debe permitir enviar a revisión desde estado APPROVED."""
        service = ApprovalService()
        proposal = self._create_proposal(db_session, status=ProposalStatus.APPROVED)

        with pytest.raises(InvalidTransitionError):
            service.submit_for_review(db_session, proposal.id)

    def test_approve_reviewer(self, db_session):
        """Ángela (reviewer) debe poder aprobar desde PENDING_REVIEW."""
        service = ApprovalService()
        proposal = self._create_proposal(db_session, status=ProposalStatus.PENDING_REVIEW)

        result = service.approve(
            db=db_session,
            proposal_id=proposal.id,
            approver_name="Ángela",
            approver_email="angela@quipux.com",
            role=ApprovalRole.REVIEWER,
            comments="Aprobada, todo correcto.",
        )
        assert result.status == ProposalStatus.REVIEWED

        # Verificar que se registró la aprobación
        approvals = db_session.query(Approval).filter(
            Approval.proposal_id == proposal.id
        ).all()
        assert len(approvals) == 1
        assert approvals[0].action == ApprovalAction.APPROVED

    def test_approve_vp(self, db_session):
        """Juan Pablo (VP) debe poder aprobar desde PENDING_VP."""
        service = ApprovalService()
        proposal = self._create_proposal(db_session, status=ProposalStatus.PENDING_VP)

        result = service.approve(
            db=db_session,
            proposal_id=proposal.id,
            approver_name="Juan Pablo Ramírez Madrid",
            approver_email="juanpablo@quipux.com",
            role=ApprovalRole.VP,
        )
        assert result.status == ProposalStatus.APPROVED

    def test_reject_from_review(self, db_session):
        """Debe permitir rechazar desde PENDING_REVIEW."""
        service = ApprovalService()
        proposal = self._create_proposal(db_session, status=ProposalStatus.PENDING_REVIEW)

        result = service.reject(
            db=db_session,
            proposal_id=proposal.id,
            rejector_name="Ángela",
            rejector_email="angela@quipux.com",
            role=ApprovalRole.REVIEWER,
            comments="Falta información de condiciones económicas.",
        )
        assert result.status == ProposalStatus.REJECTED

    def test_proposal_not_found(self, db_session):
        """Debe lanzar error si la propuesta no existe."""
        service = ApprovalService()
        with pytest.raises(ApprovalError, match="no encontrada"):
            service.submit_for_review(db_session, 99999)
