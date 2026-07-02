"""
Pruebas unitarias para el servicio de portafolio.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.portfolio_service import (
    PortfolioService, PortfolioProduct, PortfolioNotFoundError, MVP_SCHEME_STRINGS,
    QLOUDSI_FORBIDDEN_SCHEMES, is_qloudsi_product,
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


def _make_product(name: str, allowed_schemes=None, product_type: str = "Plataforma") -> PortfolioProduct:
    """Helper para crear un PortfolioProduct de prueba."""
    return PortfolioProduct(
        name=name,
        product_type=product_type,
        description="",
        business_framework="",
        revenue_info="",
        operational_costs="",
        monetization_model="",
        pricing_model="",
        country="Colombia",
        allowed_schemes=allowed_schemes or [],
    )


class TestIsQloudsiProduct:
    """Tests de la regla de detección de servicios QloudSI."""

    def test_servicio_qloudsi(self):
        assert is_qloudsi_product("Servicio QloudSI") is True

    def test_case_insensitive(self):
        assert is_qloudsi_product("servicio qloudsi") is True
        assert is_qloudsi_product("SERVICIO QLOUDSI") is True

    def test_plataforma_is_not_qloudsi(self):
        assert is_qloudsi_product("Plataforma") is False

    def test_empty_string(self):
        assert is_qloudsi_product("") is False

    def test_none(self):
        assert is_qloudsi_product(None) is False


class TestAllowedSchemesPerProduct:
    """Tests para la resolución de esquemas permitidos POR PRODUCTO."""

    def test_product_no_restriction_returns_all_mvp(self):
        """Producto sin columna 9 → todos los MVP schemes."""
        service = PortfolioService("dummy.xlsx")
        result = service.get_allowed_schemes_for_product(_make_product("ProdA"))
        assert result == list(MVP_SCHEME_STRINGS)

    def test_product_with_column9_restriction(self):
        """Producto con columna 9 → solo sus esquemas, en orden MVP."""
        service = PortfolioService("dummy.xlsx")
        product = _make_product("ProdA", allowed_schemes=["support_maintenance", "licensing"])
        result = service.get_allowed_schemes_for_product(product)
        assert result == ["licensing", "support_maintenance"]

    def test_qloudsi_without_column9_never_includes_licensing(self):
        """QloudSI sin restricción de Excel → todos los MVP menos licensing."""
        service = PortfolioService("dummy.xlsx")
        product = _make_product("Innti", product_type="Servicio QloudSI")
        result = service.get_allowed_schemes_for_product(product)
        assert "licensing" not in result
        assert result == ["services", "support_maintenance"]

    def test_qloudsi_with_column9_licensing_still_excluded(self):
        """Aunque el Excel liste licensing, un QloudSI NUNCA lo ofrece (regla dura)."""
        service = PortfolioService("dummy.xlsx")
        product = _make_product(
            "Innti", allowed_schemes=["licensing", "services"],
            product_type="Servicio QloudSI",
        )
        result = service.get_allowed_schemes_for_product(product)
        assert result == ["services"]

    def test_forbidden_schemes_constant(self):
        """La regla dura solo prohíbe licensing (documentado como constante)."""
        assert QLOUDSI_FORBIDDEN_SCHEMES == {"licensing"}

    def test_by_name_found(self):
        """Resolución por nombre: usa la restricción del producto encontrado."""
        service = PortfolioService("dummy.xlsx")
        service._products = [_make_product("ProdA", allowed_schemes=["licensing"])]
        assert service.get_allowed_schemes_for_product_name("ProdA") == ["licensing"]

    def test_by_name_case_insensitive(self):
        """La búsqueda por nombre de producto es case-insensitive."""
        service = PortfolioService("dummy.xlsx")
        service._products = [_make_product("Qx-Tránsito", allowed_schemes=["licensing"])]
        assert service.get_allowed_schemes_for_product_name("QX-TRÁNSITO") == ["licensing"]

    def test_by_name_not_found_returns_all_mvp(self):
        """Producto que no está en el portafolio → sin restricción (todos los MVP)."""
        service = PortfolioService("dummy.xlsx")
        service._products = [_make_product("Otro")]
        result = service.get_allowed_schemes_for_product_name("Producto Inexistente")
        assert result == list(MVP_SCHEME_STRINGS)

    def test_intersection_method_removed(self):
        """El método de intersección (modelo viejo) ya no existe."""
        assert not hasattr(PortfolioService, "get_allowed_schemes_for_products")
