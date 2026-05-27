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


# ── Fixture: override del servicio de portafolio ──────────────────────────────
@pytest.fixture
def portfolio_mock(client):
    """
    Inyecta un MagicMock como PortfolioService en la app FastAPI.
    Depende de 'client' para garantizar que el override de DB ya esté activo.
    El fixture 'client' limpia todos los overrides al finalizar.
    """
    mock_svc = MagicMock()
    app.dependency_overrides[get_portfolio_service] = lambda: mock_svc
    yield mock_svc


# ── Helpers ───────────────────────────────────────────────────────────────────
def _make_product(name: str = "Producto Test", product_type: str = "software"):
    """Crea un objeto mock que simula un PortfolioProduct."""
    p = MagicMock()
    p.name = name
    p.product_type = product_type
    p.description = f"Descripción de {name}"
    p.business_framework = "Framework de negocio"
    p.monetization_model = "SaaS"
    p.pricing_model = "Por usuario"
    p.country = "Colombia"
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
