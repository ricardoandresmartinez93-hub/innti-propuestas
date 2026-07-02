"""
Tests para el router del portafolio (app/routers/portfolio.py).

Cubre GET /api/portfolio/products (con y sin filtros) y GET /api/portfolio/products/types.
La dependencia PortfolioService se sustituye por un MagicMock para evitar depender
del archivo ListaPortafolio.xlsx en el entorno de test.
"""
import pytest
from unittest.mock import MagicMock
from fastapi import status

from app.main import app
from app.routers.portfolio import get_portfolio_service
from app.services.portfolio_service import PortfolioService


# ── Fixture: override del servicio de portafolio ──────────────────────────────
@pytest.fixture
def portfolio_mock(client):
    """
    Inyecta un MagicMock como PortfolioService en la app FastAPI.
    Depende de 'client' para garantizar que el override de DB ya esté activo.
    El fixture 'client' limpia todos los overrides al finalizar.

    get_allowed_schemes_for_product usa la implementación REAL para que los
    tests del router validen la resolución por producto (incl. regla QloudSI).
    """
    mock_svc = MagicMock()
    mock_svc.get_allowed_schemes_for_product.side_effect = (
        lambda p: PortfolioService.get_allowed_schemes_for_product(mock_svc, p)
    )
    app.dependency_overrides[get_portfolio_service] = lambda: mock_svc
    yield mock_svc


# ── Helpers ───────────────────────────────────────────────────────────────────
def _make_product(name: str = "Producto Test", product_type: str = "software", allowed_schemes=None):
    """Crea un objeto mock que simula un PortfolioProduct."""
    p = MagicMock()
    p.name = name
    p.product_type = product_type
    p.description = f"Descripción de {name}"
    p.business_framework = "Framework de negocio"
    p.monetization_model = "SaaS"
    p.pricing_model = "Por usuario"
    p.country = "Colombia"
    p.allowed_schemes = allowed_schemes if allowed_schemes is not None else []
    return p


# ── Tests ─────────────────────────────────────────────────────────────────────
def test_list_products_no_filters(client, portfolio_mock):
    """Sin filtros devuelve todos los productos vía get_products()."""
    portfolio_mock.get_products.return_value = [
        _make_product("Alfa", "software"),
        _make_product("Beta", "platform"),
    ]

    response = client.get("/api/portfolio/products")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Alfa"
    assert data[1]["name"] == "Beta"
    portfolio_mock.get_products.assert_called_once()


def test_list_products_with_search(client, portfolio_mock):
    """Con ?search=... llama a search_products()."""
    portfolio_mock.search_products.return_value = [_make_product("Qx-Tránsito", "platform")]

    response = client.get("/api/portfolio/products?search=transito")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Qx-Tránsito"
    portfolio_mock.search_products.assert_called_once_with("transito")


def test_list_products_with_type_filter(client, portfolio_mock):
    """Con ?product_type=... llama a filter_by_type()."""
    portfolio_mock.filter_by_type.return_value = [_make_product("SoftwareX", "software")]

    response = client.get("/api/portfolio/products?product_type=software")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["product_type"] == "software"
    portfolio_mock.filter_by_type.assert_called_once_with("software")


def test_list_products_empty_result(client, portfolio_mock):
    """Lista vacía cuando el servicio no retorna productos."""
    portfolio_mock.get_products.return_value = []

    response = client.get("/api/portfolio/products")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_list_product_types(client, portfolio_mock):
    """Devuelve los tipos únicos de producto, ordenados y sin duplicados."""
    portfolio_mock.get_products.return_value = [
        _make_product("P1", "software"),
        _make_product("P2", "hardware"),
        _make_product("P3", "software"),  # duplicado
    ]

    response = client.get("/api/portfolio/products/types")

    assert response.status_code == status.HTTP_200_OK
    types = response.json()
    # Ordenados
    assert types == sorted(types)
    # Sin duplicados
    assert len(types) == len(set(types))
    assert "software" in types
    assert "hardware" in types


def test_product_response_includes_allowed_schemes(client, portfolio_mock):
    """La respuesta de productos incluye allowed_schemes con la restricción de columna 9."""
    portfolio_mock.get_products.return_value = [
        _make_product("ProdA", allowed_schemes=["licensing", "services"]),
    ]

    response = client.get("/api/portfolio/products")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "allowed_schemes" in data[0]
    assert set(data[0]["allowed_schemes"]) == {"licensing", "services"}


def test_product_response_no_restriction_resolves_all_mvp(client, portfolio_mock):
    """Un producto sin restricciones devuelve la lista RESUELTA: todos los MVP schemes."""
    portfolio_mock.get_products.return_value = [
        _make_product("ProdB", allowed_schemes=[]),
    ]

    response = client.get("/api/portfolio/products")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data[0]["allowed_schemes"] == ["licensing", "services", "support_maintenance"]


def test_qloudsi_product_never_offers_licensing(client, portfolio_mock):
    """Un servicio QloudSI nunca incluye licensing en allowed_schemes, aunque el Excel lo liste."""
    portfolio_mock.get_products.return_value = [
        _make_product(
            "Innti", product_type="Servicio QloudSI",
            allowed_schemes=["licensing", "services"],
        ),
    ]

    response = client.get("/api/portfolio/products")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data[0]["allowed_schemes"] == ["services"]
