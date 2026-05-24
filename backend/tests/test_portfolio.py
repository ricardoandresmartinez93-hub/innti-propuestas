"""
Pruebas unitarias para el servicio de portafolio.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.portfolio_service import (
    PortfolioService, PortfolioProduct, PortfolioNotFoundError,
)


class TestPortfolioService:
    """Tests del servicio de lectura del portafolio Excel."""

    def test_validate_file_not_found(self):
        """Debe lanzar error si el archivo no existe."""
        service = PortfolioService("/ruta/inexistente.xlsx")
        with pytest.raises(PortfolioNotFoundError):
            service.load_products()

    def test_search_products_case_insensitive(self):
        """La búsqueda debe ser case-insensitive."""
        service = PortfolioService("dummy.xlsx")
        service._products = [
            PortfolioProduct(
                name="Qx-Tránsito", product_type="Plataforma",
                description="desc", business_framework="", revenue_info="",
                operational_costs="", monetization_model="", pricing_model="",
                country="Colombia"
            ),
            PortfolioProduct(
                name="DEI", product_type="Plataforma",
                description="desc", business_framework="", revenue_info="",
                operational_costs="", monetization_model="", pricing_model="",
                country="Colombia"
            ),
        ]

        results = service.search_products("qx-tránsito")
        assert len(results) == 1
        assert results[0].name == "Qx-Tránsito"

    def test_search_products_partial_match(self):
        """La búsqueda parcial debe funcionar."""
        service = PortfolioService("dummy.xlsx")
        service._products = [
            PortfolioProduct(
                name="Servicios digitales para el ciudadano",
                product_type="Plataforma", description="", business_framework="",
                revenue_info="", operational_costs="", monetization_model="",
                pricing_model="", country="Colombia"
            ),
            PortfolioProduct(
                name="Servicios digitales para clientes corporativos",
                product_type="Plataforma", description="", business_framework="",
                revenue_info="", operational_costs="", monetization_model="",
                pricing_model="", country="Colombia"
            ),
            PortfolioProduct(
                name="DEI", product_type="Plataforma", description="",
                business_framework="", revenue_info="", operational_costs="",
                monetization_model="", pricing_model="", country="Colombia"
            ),
        ]

        results = service.search_products("servicios digitales")
        assert len(results) == 2

    def test_filter_by_type(self):
        """Debe filtrar correctamente por tipo de producto."""
        service = PortfolioService("dummy.xlsx")
        service._products = [
            PortfolioProduct(
                name="Qx-Tránsito", product_type="Plataforma",
                description="", business_framework="", revenue_info="",
                operational_costs="", monetization_model="", pricing_model="",
                country="Colombia"
            ),
            PortfolioProduct(
                name="Innti", product_type="Servicio QloudSI",
                description="", business_framework="", revenue_info="",
                operational_costs="", monetization_model="", pricing_model="",
                country="Colombia"
            ),
        ]

        plataformas = service.filter_by_type("Plataforma")
        assert len(plataformas) == 1
        assert plataformas[0].name == "Qx-Tránsito"

    def test_get_by_names(self):
        """Debe obtener productos por nombres exactos."""
        service = PortfolioService("dummy.xlsx")
        service._products = [
            PortfolioProduct(
                name="DEI", product_type="Plataforma", description="",
                business_framework="", revenue_info="", operational_costs="",
                monetization_model="", pricing_model="", country="Colombia"
            ),
            PortfolioProduct(
                name="Innti", product_type="Servicio QloudSI", description="",
                business_framework="", revenue_info="", operational_costs="",
                monetization_model="", pricing_model="", country="Colombia"
            ),
        ]

        results = service.get_by_names(["DEI"])
        assert len(results) == 1
        assert results[0].name == "DEI"

    def test_get_products_lazy_load(self):
        """get_products debe cargar automáticamente si no se ha cargado."""
        service = PortfolioService("dummy.xlsx")
        service._products = [
            PortfolioProduct(
                name="Test", product_type="Plataforma", description="",
                business_framework="", revenue_info="", operational_costs="",
                monetization_model="", pricing_model="", country=""
            ),
        ]
        products = service.get_products()
        assert len(products) == 1
