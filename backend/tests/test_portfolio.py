"""
Pruebas unitarias para el servicio de portafolio.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.portfolio_service import (
    PortfolioService, PortfolioProduct, PortfolioNotFoundError, MVP_SCHEME_STRINGS,
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


def _make_product(name: str, allowed_schemes=None) -> PortfolioProduct:
    """Helper para crear un PortfolioProduct de prueba."""
    return PortfolioProduct(
        name=name,
        product_type="Plataforma",
        description="",
        business_framework="",
        revenue_info="",
        operational_costs="",
        monetization_model="",
        pricing_model="",
        country="Colombia",
        allowed_schemes=allowed_schemes or [],
    )


class TestAllowedSchemes:
    """Tests para la lógica de allowed_schemes en PortfolioService."""

    def test_product_default_empty_allowed_schemes(self):
        """Un producto sin restricciones tiene allowed_schemes vacío."""
        p = _make_product("ProdA")
        assert p.allowed_schemes == []

    def test_get_allowed_schemes_no_products(self):
        """Sin productos retorna lista vacía."""
        service = PortfolioService("dummy.xlsx")
        service._products = []
        assert service.get_allowed_schemes_for_products([]) == []

    def test_get_allowed_schemes_product_not_found_returns_all_mvp(self):
        """Si un producto no está en el portafolio, permite todos los MVP schemes."""
        service = PortfolioService("dummy.xlsx")
        service._products = [_make_product("Otro")]
        result = service.get_allowed_schemes_for_products(["Producto Inexistente"])
        assert set(result) == set(MVP_SCHEME_STRINGS)

    def test_get_allowed_schemes_product_no_restriction_returns_all_mvp(self):
        """Un producto con allowed_schemes vacío permite todos los MVP schemes."""
        service = PortfolioService("dummy.xlsx")
        service._products = [_make_product("ProdA", allowed_schemes=[])]
        result = service.get_allowed_schemes_for_products(["ProdA"])
        assert set(result) == set(MVP_SCHEME_STRINGS)

    def test_get_allowed_schemes_single_product_restricted(self):
        """Un producto con restricciones retorna solo sus esquemas permitidos."""
        service = PortfolioService("dummy.xlsx")
        service._products = [_make_product("ProdA", allowed_schemes=["licensing"])]
        result = service.get_allowed_schemes_for_products(["ProdA"])
        assert result == ["licensing"]

    def test_get_allowed_schemes_intersection_of_two_products(self):
        """La intersección de dos productos sin esquemas en común retorna vacío."""
        service = PortfolioService("dummy.xlsx")
        service._products = [
            _make_product("ProdA", allowed_schemes=["licensing"]),
            _make_product("ProdB", allowed_schemes=["services"]),
        ]
        result = service.get_allowed_schemes_for_products(["ProdA", "ProdB"])
        assert result == []

    def test_get_allowed_schemes_intersection_keeps_common_schemes(self):
        """La intersección retorna solo los esquemas comunes a todos los productos."""
        service = PortfolioService("dummy.xlsx")
        service._products = [
            _make_product("ProdA", allowed_schemes=["licensing", "services"]),
            _make_product("ProdB", allowed_schemes=["services", "support_maintenance"]),
        ]
        result = service.get_allowed_schemes_for_products(["ProdA", "ProdB"])
        assert result == ["services"]

    def test_get_allowed_schemes_unrestricted_product_does_not_narrow_set(self):
        """Un producto sin restricción contribuye todos los MVP schemes: no estrecha la intersección."""
        service = PortfolioService("dummy.xlsx")
        service._products = [
            _make_product("ProdA", allowed_schemes=["licensing"]),
            _make_product("ProdB", allowed_schemes=[]),  # sin restricción
        ]
        result = service.get_allowed_schemes_for_products(["ProdA", "ProdB"])
        # ProdB aporta todos los MVP → intersección con ProdA = ["licensing"]
        assert result == ["licensing"]

    def test_get_allowed_schemes_case_insensitive_lookup(self):
        """La búsqueda por nombre de producto es case-insensitive."""
        service = PortfolioService("dummy.xlsx")
        service._products = [_make_product("Qx-Tránsito", allowed_schemes=["licensing"])]
        result = service.get_allowed_schemes_for_products(["QX-TRÁNSITO"])
        assert result == ["licensing"]

    def test_get_allowed_schemes_preserves_mvp_order(self):
        """El resultado sigue el orden de MVP_SCHEME_STRINGS."""
        service = PortfolioService("dummy.xlsx")
        service._products = [
            _make_product("ProdA", allowed_schemes=["support_maintenance", "licensing"]),
        ]
        result = service.get_allowed_schemes_for_products(["ProdA"])
        # licensing antes que support_maintenance (orden MVP)
        assert result.index("licensing") < result.index("support_maintenance")
