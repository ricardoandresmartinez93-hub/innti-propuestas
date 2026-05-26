"""
Tests para validar la restricción de esquemas MVP.
Usa el fixture 'client' del conftest que inyecta la BD de tests aislada.
"""
import pytest
from fastapi import status


def test_create_proposal_with_mvp_scheme(client, sample_client_data):
    """Debe funcionar con licensing, services, support_maintenance."""
    client_resp = client.post("/api/clients/", json=sample_client_data)
    assert client_resp.status_code == status.HTTP_201_CREATED
    client_id = client_resp.json()["id"]

    proposal_data = {
        "title": "Propuesta MVP completa",
        "client_id": client_id,
        "products": [],
        "schemes": [
            {"scheme_type": "licensing", "payment_frequency": "unico"},
            {"scheme_type": "services", "payment_frequency": "mensual"},
            {"scheme_type": "support_maintenance", "payment_frequency": "anual"},
        ],
    }
    response = client.post("/api/proposals/", json=proposal_data)
    assert response.status_code == status.HTTP_201_CREATED


def test_create_proposal_invalid_scheme_concession(client, sample_client_data):
    """Debe fallar con HTTP 422 al usar concession_bpo."""
    client_resp = client.post("/api/clients/", json=sample_client_data)
    client_id = client_resp.json()["id"]

    proposal_data = {
        "title": "Invalid Proposal concession",
        "client_id": client_id,
        "products": [],
        "schemes": [{"scheme_type": "concession_bpo", "payment_frequency": "mensual"}],
    }
    response = client.post("/api/proposals/", json=proposal_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "no está disponible en el MVP" in response.json()["detail"]


def test_create_proposal_invalid_scheme_supply(client, sample_client_data):
    """Debe fallar con HTTP 422 al usar supply."""
    client_resp = client.post("/api/clients/", json=sample_client_data)
    client_id = client_resp.json()["id"]

    proposal_data = {
        "title": "Invalid Proposal supply",
        "client_id": client_id,
        "products": [],
        "schemes": [{"scheme_type": "supply", "payment_frequency": "unico"}],
    }
    response = client.post("/api/proposals/", json=proposal_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "no está disponible en el MVP" in response.json()["detail"]
