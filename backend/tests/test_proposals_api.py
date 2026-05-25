import pytest
from fastapi import status
from sqlalchemy.orm import Session
from app.models.proposal import Proposal, ProposalStatus
from app.models.client import Client

def test_list_proposals_empty(client):
    """Lista vacía al inicio."""
    response = client.get("/api/proposals/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_create_proposal_success(client, sample_client_data, sample_proposal_data):
    """Crear propuesta con cliente y productos."""
    # 1. Crear cliente
    client_res = client.post("/api/clients/", json=sample_client_data)
    assert client_res.status_code == status.HTTP_201_CREATED
    client_id = client_res.json()["id"]

    # 2. Crear propuesta
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    
    response = client.post("/api/proposals/", json=proposal_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()
    assert data["title"] == proposal_data["title"]
    assert data["client_id"] == client_id
    assert len(data["products"]) == 2
    assert data["status"] == "draft"

def test_create_proposal_invalid_client(client, sample_proposal_data):
    """Error 404 si el cliente no existe."""
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = 9999  # ID inexistente
    
    response = client.post("/api/proposals/", json=proposal_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "no encontrado" in response.json()["detail"]

def test_update_proposal_content(client, sample_client_data, sample_proposal_data):
    """PATCH para editar condiciones económicas."""
    # 1. Preparar propuesta
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    prop_res = client.post("/api/proposals/", json=proposal_data)
    proposal_id = prop_res.json()["id"]

    # 2. Actualizar
    update_data = {
        "economic_conditions": "<p>Nuevas condiciones 2024</p>",
        "payment_terms": "Contado"
    }
    response = client.patch(f"/api/proposals/{proposal_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["economic_conditions"] == update_data["economic_conditions"]
    assert data["payment_terms"] == update_data["payment_terms"]

def test_delete_proposal(client, sample_client_data, sample_proposal_data):
    """Eliminar propuesta."""
    # 1. Preparar propuesta
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    prop_res = client.post("/api/proposals/", json=proposal_data)
    proposal_id = prop_res.json()["id"]

    # 2. Eliminar
    response = client.delete(f"/api/proposals/{proposal_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # 3. Verificar que no existe
    get_res = client.get(f"/api/proposals/{proposal_id}")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND

def test_full_approval_flow(client, sample_client_data, sample_proposal_data):
    """Crear -> submit_review -> approve(reviewer) -> approve(VP)."""
    # 1. Crear propuesta
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    prop_res = client.post("/api/proposals/", json=proposal_data)
    proposal_id = prop_res.json()["id"]
    assert prop_res.json()["status"] == "draft"

    # 2. Enviar a revisión
    submit_res = client.post(f"/api/proposals/{proposal_id}/submit-review")
    assert submit_res.status_code == status.HTTP_200_OK
    assert submit_res.json()["status"] == "pending_review"

    # 3. Aprobación Reviewer (Ángela)
    angela_app = {
        "approver_name": "Ángela",
        "approver_email": "angela@innti.com",
        "role": "reviewer",
        "action": "approved",
        "comments": "OK para VP"
    }
    app1_res = client.post(f"/api/proposals/{proposal_id}/approve", json=angela_app)
    assert app1_res.status_code == status.HTTP_200_OK
    
    # Verificar cambio de estado en la propuesta
    prop_status_res = client.get(f"/api/proposals/{proposal_id}")
    assert prop_status_res.json()["status"] == "reviewed"

    # 3.5 Enviar a VP
    submit_vp_res = client.post(f"/api/proposals/{proposal_id}/submit-review")
    assert submit_vp_res.status_code == status.HTTP_200_OK
    assert submit_vp_res.json()["status"] == "pending_vp"

    # 4. Aprobación VP (Juan Pablo)
    vp_app = {
        "approver_name": "Juan Pablo",
        "approver_email": "jp@innti.com",
        "role": "vp",
        "action": "approved",
        "comments": "Aprobado totalmente"
    }
    app2_res = client.post(f"/api/proposals/{proposal_id}/approve", json=vp_app)
    assert app2_res.status_code == status.HTTP_200_OK
    
    # Verificar estado final
    final_prop_res = client.get(f"/api/proposals/{proposal_id}")
    assert final_prop_res.json()["status"] == "approved"
    app2_res = client.post(f"/api/proposals/{proposal_id}/approve", json=vp_app)
    assert app2_res.status_code == status.HTTP_200_OK
    
    # Verificar estado final
    final_prop_res = client.get(f"/api/proposals/{proposal_id}")
    assert final_prop_res.json()["status"] == "approved"
