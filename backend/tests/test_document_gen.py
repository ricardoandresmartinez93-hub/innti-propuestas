"""
Pruebas unitarias para el generador de documentos.
"""
import pytest
import tempfile
from pathlib import Path

from app.services.document_generator import DocumentGenerator
from app.services.portfolio_service import PortfolioProduct


def _sample_products():
    return [
        PortfolioProduct(
            name="Servicios digitales para el ciudadano",
            product_type="Plataforma",
            description="Plataforma de servicios digitales para trámites.",
            business_framework="Registro de vehículos",
            revenue_info="", operational_costs="",
            monetization_model="Licencia/SaaS",
            pricing_model="SMMLV", country="Colombia"
        ),
        PortfolioProduct(
            name="Qx-Tránsito",
            product_type="Plataforma",
            description="Plataforma misional para gestión de tránsito.",
            business_framework="Multas de tránsito",
            revenue_info="", operational_costs="",
            monetization_model="Licencia",
            pricing_model="Fijo", country="Colombia"
        ),
    ]


class TestDocumentGenerator:
    """Tests del generador de documentos Word."""

    def test_generate_proposal_creates_valid_docx(self):
        """Debe generar un documento Word válido."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="Propuesta de prueba",
            client_name="Test Client",
            client_position="Gerente",
            client_entity="Entidad Test",
            client_city="Bogotá",
            scheme_types=["licensing"],
            products=_sample_products(),
            context_text="Este es el contexto de prueba.",
            scope_text="Este es el alcance de prueba.",
            letter_text="Carta de presentación de prueba.",
        )
        assert doc is not None
        # Verificar que tiene contenido (párrafos)
        assert len(doc.paragraphs) > 0

    def test_save_document(self):
        """Debe guardar el documento en disco."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="Test Save",
            client_name="Client",
            client_position="",
            client_entity="Entity",
            client_city="Bogotá",
            scheme_types=["services"],
            products=[],
            context_text="Contexto",
            scope_text="Alcance",
            letter_text="Carta",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = gen.save_document(doc, f"{tmpdir}/test.docx")
            assert Path(path).exists()
            assert Path(path).stat().st_size > 0

    def test_generate_technical_annex(self):
        """Debe generar el anexo técnico con productos."""
        gen = DocumentGenerator()
        products = _sample_products()
        doc = gen.generate_technical_annex(products)

        assert doc is not None
        # Verificar que incluye los nombres de los productos
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert "Servicios digitales para el ciudadano" in full_text
        assert "Qx-Tránsito" in full_text

    def test_excluded_services_licensing(self):
        """Debe incluir exclusiones de licenciamiento."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="Test", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["licensing"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert "funcionalidades nuevas" in full_text.lower()

    def test_ip_section_licensing_vs_services(self):
        """Propiedad intelectual debe variar según esquema."""
        gen = DocumentGenerator()

        doc_lic = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["licensing"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        text_lic = "\n".join(p.text for p in doc_lic.paragraphs)

        doc_svc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["services"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        text_svc = "\n".join(p.text for p in doc_svc.paragraphs)

        # Licenciamiento: "no será propietario"
        assert "no será propietario" in text_lic
        # Servicios: "derecho de uso durante la vigencia"
        assert "derecho de uso durante la vigencia" in text_svc
