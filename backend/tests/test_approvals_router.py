"""
Tests para el router de aprobaciones (app/routers/approvals.py).

Cubre las transiciones de estado no ejercitadas por test_proposals_api.py:
- submit-review desde APPROVED, REJECTED y estado inválido
- submit-review con propuesta no encontrada
- Rechazo desde PENDING_REVIEW y PENDING_VP
- Historial de aprobaciones
- Transición inválida en approve → 409
"""
import pytest
from fastapi import status


# ── Helpers para construir escenarios de estado ───────────────────────────────
def _create_proposal(client, sample_client_data, sample_proposal_data, creator_headers) -> int:
    """Crea cliente y propuesta; devuelve el ID de la propuesta."""
    c_res = client.post("/api/clients/", json=sample_client_data)
    assert c_res.status_code == status.HTTP_201_CREATED
    client_id = c_res.json()["id"]

    p_data = {**sample_proposal_data, "client_id": client_id}
    p_res = client.post("/api/proposals/", json=p_data, headers=creator_headers)
    assert p_res.status_code == status.HTTP_201_CREATED
    return p_res.json()["id"]


def _advance_to_pending_review(client, pid: int) -> None:
    res = client.post(f"/api/proposals/{pid}/submit-review")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "pending_review"


def _advance_to_reviewed(client, pid: int, approver_1_headers: dict) -> None:
    _advance_to_pending_review(client, pid)
    res = client.post(f"/api/proposals/{pid}/approve", headers=approver_1_headers, json={
        "role": "reviewer", "approver_name": "Ángela",
        "approver_email": "angela@innti.com", "action": "approved",
    })
    assert res.status_code == status.HTTP_200_OK


def _advance_to_pending_vp(client, pid: int, approver_1_headers: dict) -> None:
    _advance_to_reviewed(client, pid, approver_1_headers)
    res = client.post(f"/api/proposals/{pid}/submit-review")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "pending_vp"


def _advance_to_approved(client, pid: int, approver_1_headers: dict, approver_2_headers: dict) -> None:
    _advance_to_pending_vp(client, pid, approver_1_headers)
    res = client.post(f"/api/proposals/{pid}/approve", headers=approver_2_headers, json={
        "role": "vp", "approver_name": "Juan Pablo",
        "approver_email": "jp@innti.com", "action": "approved",
    })
    assert res.status_code == status.HTTP_200_OK


def _advance_to_rejected(client, pid: int, approver_1_headers: dict) -> None:
    """Avanza DRAFT → PENDING_REVIEW → REJECTED."""
    _advance_to_pending_review(client, pid)
    res = client.post(f"/api/proposals/{pid}/reject", headers=approver_1_headers, json={
        "role": "reviewer", "approver_name": "Ángela",
        "approver_email": "angela@innti.com", "action": "rejected",
        "comments": "No cumple requisitos mínimos.",
    })
    assert res.status_code == status.HTTP_200_OK


# ── Tests de submit-review ────────────────────────────────────────────────────
def test_submit_review_proposal_not_found(client):
    """submit-review con propuesta inexistente → 404."""
    res = client.post("/api/proposals/99999/submit-review")
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_submit_review_from_approved_to_sent(
    client, sample_client_data, sample_proposal_data, creator_headers, approver_1_headers, approver_2_headers
):
    """APPROVED → SENT_TO_CLIENT vía submit-review."""
    pid = _create_proposal(client, sample_client_data, sample_proposal_data, creator_headers)
    _advance_to_approved(client, pid, approver_1_headers, approver_2_headers)

    res = client.post(f"/api/proposals/{pid}/submit-review")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "sent_to_client"


def test_submit_review_from_rejected_to_draft(
    client, sample_client_data, sample_proposal_data, creator_headers, approver_1_headers
):
    """REJECTED → DRAFT vía submit-review."""
    pid = _create_proposal(client, sample_client_data, sample_proposal_data, creator_headers)
    _advance_to_rejected(client, pid, approver_1_headers)

    res = client.post(f"/api/proposals/{pid}/submit-review")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "draft"


def test_submit_review_from_invalid_state_returns_400(
    client, sample_client_data, sample_proposal_data, creator_headers
):
    """submit-review desde PENDING_REVIEW (estado no procesable) → 400."""
    pid = _create_proposal(client, sample_client_data, sample_proposal_data, creator_headers)
    _advance_to_pending_review(client, pid)

    # PENDING_REVIEW no tiene transición permitida en submit-review
    res = client.post(f"/api/proposals/{pid}/submit-review")
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_submit_review_from_pending_vp_returns_400(
    client, sample_client_data, sample_proposal_data, creator_headers, approver_1_headers
):
    """submit-review desde PENDING_VP (estado no procesable) → 400."""
    pid = _create_proposal(client, sample_client_data, sample_proposal_data, creator_headers)
    _advance_to_pending_vp(client, pid, approver_1_headers)

    res = client.post(f"/api/proposals/{pid}/submit-review")
    assert res.status_code == status.HTTP_400_BAD_REQUEST


# ── Tests de rechazo ──────────────────────────────────────────────────────────
def test_reject_proposal_from_pending_review(
    client, sample_client_data, sample_proposal_data, creator_headers, approver_1_headers
):
    """Rechazo de la revisora (Angela) desde PENDING_REVIEW → REJECTED."""
    pid = _create_proposal(client, sample_client_data, sample_proposal_data, creator_headers)
    _advance_to_pending_review(client, pid)

    res = client.post(f"/api/proposals/{pid}/reject", headers=approver_1_headers, json={
        "role": "reviewer",
        "approver_name": "Ángela",
        "approver_email": "angela@innti.com",
        "action": "rejected",
        "comments": "Faltan datos del cliente.",
    })
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["action"] == "rejected"
    assert data["role"] == "reviewer"
    assert data["proposal_id"] == pid

    # Estado de la propuesta cambia a 'rejected'
    prop = client.get(f"/api/proposals/{pid}").json()
    assert prop["status"] == "rejected"


def test_reject_proposal_from_pending_vp(
    client, sample_client_data, sample_proposal_data, creator_headers, approver_1_headers, approver_2_headers
):
    """Rechazo del VP (Juan Pablo) desde PENDING_VP → REJECTED."""
    pid = _create_proposal(client, sample_client_data, sample_proposal_data, creator_headers)
    _advance_to_pending_vp(client, pid, approver_1_headers)

    res = client.post(f"/api/proposals/{pid}/reject", headers=approver_2_headers, json={
        "role": "vp",
        "approver_name": "Juan Pablo",
        "approver_email": "jp@innti.com",
        "action": "rejected",
        "comments": "No cumple estándares de la empresa.",
    })
    assert res.status_code == status.HTTP_200_OK

    prop = client.get(f"/api/proposals/{pid}").json()
    assert prop["status"] == "rejected"


# ── Test de historial de aprobaciones ────────────────────────────────────────
def test_get_proposal_approvals_history(
    client, sample_client_data, sample_proposal_data, creator_headers, approver_1_headers
):
    """GET /{id}/approvals devuelve el historial completo de aprobaciones."""
    pid = _create_proposal(client, sample_client_data, sample_proposal_data, creator_headers)
    _advance_to_reviewed(client, pid, approver_1_headers)  # genera 1 aprobación de tipo reviewer

    res = client.get(f"/api/proposals/{pid}/approvals")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data) >= 1
    first = data[0]
    assert first["proposal_id"] == pid
    assert first["role"] == "reviewer"
    assert first["action"] == "approved"


def test_get_approvals_history_multiple(
    client, sample_client_data, sample_proposal_data, creator_headers, approver_1_headers, approver_2_headers
):
    """Historial acumula aprobaciones de reviewer y VP."""
    pid = _create_proposal(client, sample_client_data, sample_proposal_data, creator_headers)
    _advance_to_approved(client, pid, approver_1_headers, approver_2_headers)  # 2 aprobaciones: reviewer + VP

    res = client.get(f"/api/proposals/{pid}/approvals")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data) == 2
    roles = {a["role"] for a in data}
    assert roles == {"reviewer", "vp"}


# ── Test de transición inválida (409) ────────────────────────────────────────
def test_approve_with_wrong_role_returns_409(
    client, sample_client_data, sample_proposal_data, creator_headers, approver_2_headers
):
    """Intentar aprobar con el rol incorrecto devuelve 409 Conflict."""
    pid = _create_proposal(client, sample_client_data, sample_proposal_data, creator_headers)
    _advance_to_pending_review(client, pid)

    # VP intenta aprobar una propuesta en PENDING_REVIEW (solo el reviewer puede)
    res = client.post(f"/api/proposals/{pid}/approve", headers=approver_2_headers, json={
        "role": "vp",
        "approver_name": "Juan Pablo",
        "approver_email": "jp@innti.com",
        "action": "approved",
    })
    assert res.status_code == status.HTTP_409_CONFLICT
