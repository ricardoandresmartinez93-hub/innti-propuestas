import pytest
from unittest.mock import MagicMock
from fastapi import status
from sqlalchemy.orm import Session
from app.models.proposal import Proposal, ProposalStatus
from app.models.client import Client
from app.main import app
from app.routers.portfolio import get_portfolio_service

def test_list_proposals_empty(client):
    """Lista vacía al inicio."""
    response = client.get("/api/proposals/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_create_proposal_success(client, creator_headers, sample_client_data, sample_proposal_data):
    """Crear propuesta con cliente y productos."""
    client_res = client.post("/api/clients/", json=sample_client_data)
    assert client_res.status_code == status.HTTP_201_CREATED
    client_id = client_res.json()["id"]

    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id

    response = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["title"] == proposal_data["title"]
    assert data["client_id"] == client_id
    assert len(data["products"]) == 2
    assert data["status"] == "draft"

def test_create_proposal_invalid_client(client, creator_headers, sample_proposal_data):
    """Error 404 si el cliente no existe."""
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = 9999

    response = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "no encontrado" in response.json()["detail"]

def test_create_proposal_requires_auth(client, sample_proposal_data):
    """POST /proposals/ devuelve 401 sin token."""
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = 1
    response = client.post("/api/proposals/", json=proposal_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_update_proposal_global_content(client, creator_headers, sample_client_data, sample_proposal_data):
    """PATCH para editar contenido GLOBAL (carta, contexto, confidencialidad)."""
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    prop_res = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    proposal_id = prop_res.json()["id"]

    update_data = {
        "context_content": "<p>Contexto actualizado 2026</p>",
        "letter_content": "<p>Carta personalizada</p>",
    }
    response = client.patch(f"/api/proposals/{proposal_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["context_content"] == update_data["context_content"]
    assert data["letter_content"] == update_data["letter_content"]


def test_update_proposal_scheme_content(client, creator_headers, sample_client_data, sample_proposal_data):
    """PATCH /api/proposals/{id}/schemes/{scheme_id} edita contenido POR esquema."""
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    prop_res = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    proposal = prop_res.json()
    proposal_id = proposal["id"]
    scheme_id = proposal["schemes"][0]["id"]

    update_data = {
        "economic_conditions": "<p>Nuevas condiciones 2026</p>",
        "payment_terms": "Contado",
        "ip_section": "<p>IP personalizada para este esquema</p>",
    }
    response = client.patch(
        f"/api/proposals/{proposal_id}/schemes/{scheme_id}",
        json=update_data,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["economic_conditions"] == update_data["economic_conditions"]
    assert data["payment_terms"] == update_data["payment_terms"]
    assert data["ip_section"] == update_data["ip_section"]


def test_update_scheme_unknown_returns_404(client, creator_headers, sample_client_data, sample_proposal_data):
    """PATCH a un esquema inexistente devuelve 404."""
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    prop_res = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    proposal_id = prop_res.json()["id"]

    response = client.patch(
        f"/api/proposals/{proposal_id}/schemes/99999",
        json={"payment_terms": "X"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_proposal(client, creator_headers, sample_client_data, sample_proposal_data):
    """Eliminar propuesta en DRAFT."""
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    prop_res = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    proposal_id = prop_res.json()["id"]

    response = client.delete(f"/api/proposals/{proposal_id}", headers=creator_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    get_res = client.get(f"/api/proposals/{proposal_id}")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND

def test_delete_proposal_requires_auth(client, creator_headers, sample_client_data, sample_proposal_data):
    """DELETE /proposals/{id} devuelve 401 sin token."""
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    prop_res = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    proposal_id = prop_res.json()["id"]

    response = client.delete(f"/api/proposals/{proposal_id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_delete_proposal_draft_success(client, creator_headers, sample_client_data, sample_proposal_data):
    """DELETE exitoso cuando la propuesta está en DRAFT."""
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    prop_res = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    proposal_id = prop_res.json()["id"]
    assert prop_res.json()["status"] == "draft"

    response = client.delete(f"/api/proposals/{proposal_id}", headers=creator_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    get_res = client.get(f"/api/proposals/{proposal_id}")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND


def test_delete_proposal_non_draft_fails(client, creator_headers, sample_client_data, sample_proposal_data):
    """DELETE rechazado con 409 si la propuesta no está en DRAFT."""
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    prop_res = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    proposal_id = prop_res.json()["id"]

    # Avanzar a PENDING_REVIEW
    client.post(f"/api/proposals/{proposal_id}/submit-review")

    response = client.delete(f"/api/proposals/{proposal_id}", headers=creator_headers)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "DRAFT" in response.json()["detail"]


def test_full_approval_flow(client, creator_headers, approver_1_headers, approver_2_headers, sample_client_data, sample_proposal_data):
    """Crear -> submit_review -> approve(reviewer) -> approve(VP)."""
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    prop_res = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    proposal_id = prop_res.json()["id"]
    assert prop_res.json()["status"] == "draft"

    submit_res = client.post(f"/api/proposals/{proposal_id}/submit-review")
    assert submit_res.status_code == status.HTTP_200_OK
    assert submit_res.json()["status"] == "pending_review"

    angela_app = {
        "approver_name": "Ángela",
        "approver_email": "angela@innti.com",
        "role": "reviewer",
        "action": "approved",
        "comments": "OK para VP"
    }
    app1_res = client.post(f"/api/proposals/{proposal_id}/approve", json=angela_app, headers=approver_1_headers)
    assert app1_res.status_code == status.HTTP_200_OK

    prop_status_res = client.get(f"/api/proposals/{proposal_id}")
    assert prop_status_res.json()["status"] == "reviewed"

    submit_vp_res = client.post(f"/api/proposals/{proposal_id}/submit-review")
    assert submit_vp_res.status_code == status.HTTP_200_OK
    assert submit_vp_res.json()["status"] == "pending_vp"

    vp_app = {
        "approver_name": "Juan Pablo",
        "approver_email": "jp@innti.com",
        "role": "vp",
        "action": "approved",
        "comments": "Aprobado totalmente"
    }
    app2_res = client.post(f"/api/proposals/{proposal_id}/approve", json=vp_app, headers=approver_2_headers)
    assert app2_res.status_code == status.HTTP_200_OK

    final_prop_res = client.get(f"/api/proposals/{proposal_id}")
    assert final_prop_res.json()["status"] == "approved"


# ── Fixtures para validación esquema-producto ─────────────────────────────────

def _make_portfolio_product(name: str, allowed_schemes: list):
    """Crea un mock de PortfolioProduct con restricciones específicas."""
    p = MagicMock()
    p.name = name
    p.allowed_schemes = allowed_schemes
    return p


@pytest.fixture
def restricted_portfolio(client):
    """Portfolio mock que restringe 'ProdRestringido' a solo 'licensing'."""
    mock_svc = MagicMock()
    mock_svc.get_products.return_value = [
        _make_portfolio_product("ProdRestringido", allowed_schemes=["licensing"]),
    ]
    mock_svc.get_allowed_schemes_for_products.return_value = ["licensing"]
    app.dependency_overrides[get_portfolio_service] = lambda: mock_svc
    yield mock_svc


@pytest.fixture
def permissive_portfolio(client):
    """Portfolio mock que permite todos los MVP schemes para cualquier producto."""
    mock_svc = MagicMock()
    mock_svc.get_products.return_value = []
    mock_svc.get_allowed_schemes_for_products.return_value = [
        "licensing", "services", "support_maintenance"
    ]
    app.dependency_overrides[get_portfolio_service] = lambda: mock_svc
    yield mock_svc


# ── Tests de validación esquema-producto ──────────────────────────────────────

def test_create_proposal_scheme_not_allowed_for_product(
    client, creator_headers, sample_client_data, sample_proposal_data, restricted_portfolio
):
    """Retorna 422 si el esquema seleccionado no está permitido para los productos."""
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]

    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    # Solo 'licensing' está permitido; intentamos 'services'
    proposal_data["products"] = [{"product_name": "ProdRestringido", "product_type": "Plataforma"}]
    proposal_data["schemes"] = [{"scheme_type": "services", "payment_frequency": "Mensual"}]

    response = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "no están permitidos" in response.json()["detail"]


def test_create_proposal_scheme_allowed_for_product_succeeds(
    client, creator_headers, sample_client_data, sample_proposal_data, restricted_portfolio
):
    """Crea la propuesta correctamente cuando el esquema está permitido."""
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]

    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    # 'licensing' sí está permitido para este producto
    proposal_data["products"] = [{"product_name": "ProdRestringido", "product_type": "Plataforma"}]
    proposal_data["schemes"] = [{"scheme_type": "licensing", "payment_frequency": "Único"}]

    response = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)

    assert response.status_code == status.HTTP_201_CREATED


def test_create_proposal_no_products_skips_scheme_validation(
    client, creator_headers, sample_client_data, permissive_portfolio
):
    """Sin productos, no se valida compatibilidad de esquemas."""
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]

    proposal_data = {
        "title": "Sin productos",
        "code": "0001-0626",
        "client_id": client_id,
        "combine_schemes": True,
        "products": [],
        "schemes": [{"scheme_type": "licensing", "payment_frequency": "Único"}],
    }

    response = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    assert response.status_code == status.HTTP_201_CREATED


def test_create_proposal_multiple_schemes_all_allowed(
    client, creator_headers, sample_client_data, permissive_portfolio
):
    """Con portfolio permisivo, se pueden seleccionar múltiples esquemas MVP."""
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]

    proposal_data = {
        "title": "Multi-esquema",
        "code": "0002-0626",
        "client_id": client_id,
        "combine_schemes": True,
        "products": [{"product_name": "ProdX", "product_type": "Plataforma"}],
        "schemes": [
            {"scheme_type": "licensing", "payment_frequency": "Único"},
            {"scheme_type": "services", "payment_frequency": "Mensual"},
        ],
    }

    response = client.post("/api/proposals/", json=proposal_data, headers=creator_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.json()["schemes"]) == 2
