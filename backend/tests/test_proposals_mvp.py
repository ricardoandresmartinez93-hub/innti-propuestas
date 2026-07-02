"""
Tests para validar la restricción de esquemas MVP (por producto).
Usa el fixture 'client' del conftest que inyecta la BD de tests aislada.
"""
import pytest
from fastapi import status


def _product(name: str, scheme_type: str, frequency: str) -> dict:
    return {
        "product_name": name,
        "product_type": "Plataforma",
        "scheme": {"scheme_type": scheme_type, "payment_frequency": frequency},
    }


def test_create_proposal_with_mvp_schemes(client, creator_headers, sample_client_data):
    """Debe funcionar con licensing, services, support_maintenance (uno por producto)."""
    client_resp = client.post("/api/clients/", json=sample_client_data)
    assert client_resp.status_code == status.HTTP_201_CREATED
    client_id = client_resp.json()["id"]

    proposal_data = {
        "title": "Propuesta MVP completa",
        "client_id": client_id,
        "products": [
            _product("Prod Licencias", "licensing", "unico"),
            _product("Prod Servicios", "services", "mensual"),
            _product("Prod Soporte", "support_maintenance", "anual"),
        ],
    }
    response = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    assert response.status_code == status.HTTP_201_CREATED


def test_create_proposal_invalid_scheme_concession(client, creator_headers, sample_client_data):
    """Debe fallar con HTTP 422 al usar concession_bpo."""
    client_resp = client.post("/api/clients/", json=sample_client_data)
    client_id = client_resp.json()["id"]

    proposal_data = {
        "title": "Invalid Proposal concession",
        "client_id": client_id,
        "products": [_product("Prod BPO", "concession_bpo", "mensual")],
    }
    response = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "no está disponible en el MVP" in response.json()["detail"]


def test_create_proposal_invalid_scheme_supply(client, creator_headers, sample_client_data):
    """Debe fallar con HTTP 422 al usar supply."""
    client_resp = client.post("/api/clients/", json=sample_client_data)
    client_id = client_resp.json()["id"]

    proposal_data = {
        "title": "Invalid Proposal supply",
        "client_id": client_id,
        "products": [_product("Prod Supply", "supply", "unico")],
    }
    response = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "no está disponible en el MVP" in response.json()["detail"]


def test_create_proposal_product_without_scheme_rejected(client, creator_headers, sample_client_data):
    """Un producto sin campo 'scheme' → 422 (cada producto lleva exactamente un esquema)."""
    client_resp = client.post("/api/clients/", json=sample_client_data)
    client_id = client_resp.json()["id"]

    proposal_data = {
        "title": "Producto sin esquema",
        "client_id": client_id,
        "products": [{"product_name": "Prod Incompleto", "product_type": "Plataforma"}],
    }
    response = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
