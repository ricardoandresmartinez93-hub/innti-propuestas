"""
Tests for product-management endpoints on the proposals router.
Complements test_proposals_api.py — focuses on the previously uncovered
endpoints: POST/DELETE/PUT /api/proposals/{id}/products and the 404 paths
on GET/PATCH/{id}.
"""
import pytest
from fastapi import status

from app.models.proposal import Proposal, ProposalStatus


@pytest.fixture
def draft_proposal_id(client, creator_headers, sample_client_data, sample_proposal_data):
    """Crea cliente + propuesta en DRAFT y retorna el id."""
    client_res = client.post("/api/clients/", json=sample_client_data)
    client_id = client_res.json()["id"]
    proposal_data = sample_proposal_data.copy()
    proposal_data["client_id"] = client_id
    prop_res = client.post(
        "/api/proposals/", json=proposal_data, headers=creator_headers
    )
    return prop_res.json()["id"]


# ---------- GET /{id} 404 ----------

def test_get_proposal_not_found(client):
    """GET /{id} → 404 si no existe."""
    response = client.get("/api/proposals/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "no encontrada" in response.json()["detail"]


# ---------- PATCH /{id} 404 ----------

def test_patch_proposal_not_found(client):
    """PATCH /{id} → 404 si no existe."""
    response = client.patch(
        "/api/proposals/99999", json={"economic_conditions": "x"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------- DELETE /{id} 404 ----------

def test_delete_proposal_not_found(client, creator_headers):
    """DELETE /{id} → 404 si no existe."""
    response = client.delete("/api/proposals/99999", headers=creator_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------- POST /{id}/products ----------

def test_add_product_success(client, draft_proposal_id):
    """POST /{id}/products agrega un producto (con su esquema) a propuesta en DRAFT."""
    new_product = {
        "product_name": "Qx-Notarios",
        "product_type": "Plataforma",
        "description": "Plataforma notarial",
        "category": "nuevo",
        "scheme": {"scheme_type": "licensing", "payment_frequency": "unico"},
    }
    response = client.post(
        f"/api/proposals/{draft_proposal_id}/products", json=new_product
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["product_name"] == "Qx-Notarios"
    assert data["product_type"] == "Plataforma"
    assert data["scheme"]["scheme_type"] == "licensing"
    assert data["scheme"]["product_id"] == data["id"]

    # Verify the product is now part of the proposal
    list_res = client.get(f"/api/proposals/{draft_proposal_id}")
    product_names = [p["product_name"] for p in list_res.json()["products"]]
    assert "Qx-Notarios" in product_names


def test_add_product_proposal_not_found(client):
    """POST /{id}/products → 404 si la propuesta no existe."""
    response = client.post(
        "/api/proposals/99999/products",
        json={
            "product_name": "X",
            "product_type": "Plataforma",
            "description": "...",
            "category": "nuevo",
            "scheme": {"scheme_type": "licensing", "payment_frequency": "unico"},
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_add_product_blocked_when_not_draft(
    client, db_session, draft_proposal_id
):
    """POST /{id}/products → 400 si la propuesta no está en DRAFT."""
    proposal = db_session.query(Proposal).get(draft_proposal_id)
    proposal.status = ProposalStatus.PENDING_REVIEW
    db_session.commit()

    response = client.post(
        f"/api/proposals/{draft_proposal_id}/products",
        json={
            "product_name": "X",
            "product_type": "Plataforma",
            "description": "...",
            "category": "nuevo",
            "scheme": {"scheme_type": "licensing", "payment_frequency": "unico"},
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "DRAFT" in response.json()["detail"]


# ---------- DELETE /{id}/products/{product_id} ----------

def test_remove_product_success(client, draft_proposal_id):
    """DELETE /{id}/products/{pid} elimina un producto."""
    list_res = client.get(f"/api/proposals/{draft_proposal_id}")
    product_id = list_res.json()["products"][0]["id"]

    response = client.delete(
        f"/api/proposals/{draft_proposal_id}/products/{product_id}"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    list_after = client.get(f"/api/proposals/{draft_proposal_id}")
    product_ids = [p["id"] for p in list_after.json()["products"]]
    assert product_id not in product_ids


def test_remove_product_proposal_not_found(client):
    """DELETE /{id}/products/{pid} → 404 si propuesta no existe."""
    response = client.delete("/api/proposals/99999/products/1")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Propuesta" in response.json()["detail"]


def test_remove_product_blocked_when_not_draft(
    client, db_session, draft_proposal_id
):
    """DELETE /{id}/products/{pid} → 400 si no está en DRAFT."""
    list_res = client.get(f"/api/proposals/{draft_proposal_id}")
    product_id = list_res.json()["products"][0]["id"]

    proposal = db_session.query(Proposal).get(draft_proposal_id)
    proposal.status = ProposalStatus.REVIEWED
    db_session.commit()

    response = client.delete(
        f"/api/proposals/{draft_proposal_id}/products/{product_id}"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_remove_product_not_in_proposal(client, draft_proposal_id):
    """DELETE /{id}/products/{pid} → 404 si el producto no pertenece a la propuesta."""
    response = client.delete(
        f"/api/proposals/{draft_proposal_id}/products/99999"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Producto" in response.json()["detail"]


# ---------- PUT /{id}/products (replace all) ----------

def test_replace_products_success(client, draft_proposal_id):
    """PUT /{id}/products reemplaza la lista entera (productos con su esquema)."""
    new_products = [
        {
            "product_name": "Qx-Recaudo",
            "product_type": "Plataforma",
            "description": "Recaudo electrónico",
            "category": "nuevo",
            "scheme": {"scheme_type": "licensing", "payment_frequency": "unico"},
        },
        {
            "product_name": "Qx-Pasaportes",
            "product_type": "Plataforma",
            "description": "Pasaportes",
            "category": "modernización",
            "scheme": {"scheme_type": "services", "payment_frequency": "mensual"},
        },
    ]
    response = client.put(
        f"/api/proposals/{draft_proposal_id}/products", json=new_products
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    names = {p["product_name"] for p in data}
    assert names == {"Qx-Recaudo", "Qx-Pasaportes"}

    # Verify the previous products fueron reemplazados
    list_res = client.get(f"/api/proposals/{draft_proposal_id}")
    proposal_data = list_res.json()
    assert {p["product_name"] for p in proposal_data["products"]} == names
    # Los esquemas viejos se reemplazaron junto con los productos
    assert len(proposal_data["schemes"]) == 2
    scheme_types = {s["scheme_type"] for s in proposal_data["schemes"]}
    assert scheme_types == {"licensing", "services"}


def test_replace_products_proposal_not_found(client):
    """PUT /{id}/products → 404 si la propuesta no existe."""
    response = client.put("/api/proposals/99999/products", json=[])
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_replace_products_blocked_when_not_draft(
    client, db_session, draft_proposal_id
):
    """PUT /{id}/products → 400 si la propuesta no está en DRAFT."""
    proposal = db_session.query(Proposal).get(draft_proposal_id)
    proposal.status = ProposalStatus.APPROVED
    db_session.commit()

    response = client.put(
        f"/api/proposals/{draft_proposal_id}/products",
        json=[
            {
                "product_name": "X",
                "product_type": "Plataforma",
                "description": "...",
                "category": "nuevo",
                "scheme": {"scheme_type": "licensing", "payment_frequency": "unico"},
            }
        ],
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
