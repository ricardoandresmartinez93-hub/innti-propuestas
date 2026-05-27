"""
Pruebas unitarias para el generador de documentos.
"""
import pytest
import tempfile
from datetime import date
from pathlib import Path

from app.services.document_generator import DocumentGenerator, _MONTHS_ES
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


def _full_text(doc) -> str:
    """Extrae todo el texto del documento (párrafos + tablas)."""
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts)


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
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert "Servicios digitales para el ciudadano" in full_text
        assert "Qx-Tránsito" in full_text

    # ------------------------------------------------------------------ #
    # Servicios excluidos                                                  #
    # ------------------------------------------------------------------ #

    def test_excluded_services_contains_all_10_items(self):
        """Debe incluir los 10 servicios excluidos estándar de Quipux."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="Test", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["licensing"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        full_text = _full_text(doc).lower()
        # Verificar items clave de la lista real
        assert "infraestructura tecnológica centralizada" in full_text
        assert "nuevas funcionalidades" in full_text
        assert "código fuente" in full_text
        assert "modelo de datos" in full_text
        assert "migraciones" in full_text
        assert "hardware" in full_text
        assert "motor de base de datos" in full_text

    def test_excluded_services_same_for_all_schemes(self):
        """Los servicios excluidos deben ser idénticos para todos los esquemas."""
        gen = DocumentGenerator()
        texts = {}
        for scheme in ["licensing", "services", "support_maintenance"]:
            doc = gen.generate_proposal_docx(
                title="T", client_name="C", client_position="",
                client_entity="E", client_city="B",
                scheme_types=[scheme],
                products=[], context_text="", scope_text="", letter_text="",
            )
            # Recopilar solo los bullet points de servicios excluidos
            texts[scheme] = [
                p.text for p in doc.paragraphs if p.style.name == "List Bullet"
            ]
        # Todos los esquemas deben producir la misma lista
        assert texts["licensing"] == texts["services"]
        assert texts["services"] == texts["support_maintenance"]
        assert len(texts["licensing"]) == 10

    # ------------------------------------------------------------------ #
    # Sección PLAZO                                                        #
    # ------------------------------------------------------------------ #

    def test_plazo_section_present(self):
        """El documento debe contener la sección '3. PLAZO'."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["licensing"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
        assert any("PLAZO" in h.upper() for h in headings)

    def test_plazo_uses_custom_text(self):
        """Si se provee validity_period, debe usarlo en vez del texto por defecto."""
        gen = DocumentGenerator()
        custom = "El contrato tendrá vigencia de 12 meses."
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["licensing"],
            products=[], context_text="", scope_text="", letter_text="",
            validity_period=custom,
        )
        full_text = _full_text(doc)
        assert custom in full_text

    def test_plazo_uses_default_text_when_not_provided(self):
        """Si no se provee validity_period, debe usar el texto por defecto."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["licensing"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        full_text = _full_text(doc)
        assert "fecha de suscripción" in full_text.lower()

    # ------------------------------------------------------------------ #
    # Sección PRINCIPIOS DE PREVENCIÓN                                     #
    # ------------------------------------------------------------------ #

    def test_crime_prevention_section_present(self):
        """El documento debe contener la sección de prevención de actividades delictivas."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="Consorcio ABC", client_city="B",
            scheme_types=["support_maintenance"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        full_text = _full_text(doc).lower()
        assert "prevención" in full_text
        assert "actividades delictivas" in full_text

    def test_crime_prevention_contains_client_entity(self):
        """El texto de prevención debe reemplazar {client_entity} con el nombre real del cliente."""
        gen = DocumentGenerator()
        entity = "Movilidad Digital Envigado"
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity=entity, client_city="B",
            scheme_types=["services"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        full_text = _full_text(doc)
        assert entity in full_text
        assert "{client_entity}" not in full_text

    # ------------------------------------------------------------------ #
    # Textos legales actualizados                                          #
    # ------------------------------------------------------------------ #

    def test_ip_text_unified_contains_know_how(self):
        """El texto de propiedad intelectual debe mencionar 'Know How' (texto real Quipux)."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["licensing"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        full_text = _full_text(doc)
        assert "Know How" in full_text

    def test_ip_text_contains_client_entity(self):
        """El texto de propiedad intelectual debe reemplazar {client_entity}."""
        gen = DocumentGenerator()
        entity = "Unión Temporal MDA"
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity=entity, client_city="B",
            scheme_types=["support_maintenance"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        full_text = _full_text(doc)
        assert entity in full_text
        assert "{client_entity}" not in full_text

    def test_confidentiality_contains_client_entity(self):
        """El texto de confidencialidad debe usar el nombre real del cliente."""
        gen = DocumentGenerator()
        entity = "Consorcio Cobro Activo"
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity=entity, client_city="B",
            scheme_types=["services"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        full_text = _full_text(doc)
        assert entity in full_text
        assert "{client_entity}" not in full_text

    def test_ethics_text_contains_linea_etica(self):
        """El texto de transparencia debe referenciar lineaetica@quipux.com."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["licensing"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        full_text = _full_text(doc)
        assert "lineaetica@quipux.com" in full_text

    # ------------------------------------------------------------------ #
    # Tabla de condiciones económicas                                      #
    # ------------------------------------------------------------------ #

    def test_economic_table_column_called_componente(self):
        """La tabla de condiciones económicas debe usar 'Componente' (no 'Concepto')."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["licensing"],
            products=_sample_products(),
            context_text="", scope_text="", letter_text="",
        )
        table_texts = []
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    table_texts.append(cell.text)
        combined = " ".join(table_texts)
        assert "Componente" in combined
        assert "Concepto" not in combined

    def test_economic_table_has_product_names(self):
        """La tabla debe incluir los nombres reales de los productos."""
        gen = DocumentGenerator()
        products = _sample_products()
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["licensing"],
            products=products,
            context_text="", scope_text="", letter_text="",
        )
        table_texts = []
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    table_texts.append(cell.text)
        combined = " ".join(table_texts)
        assert "Servicios digitales para el ciudadano" in combined
        assert "Qx-Tránsito" in combined

    def test_economic_table_has_totals(self):
        """La tabla de condiciones económicas debe tener Subtotal, IVA y Total."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["licensing"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        found = False
        for table in doc.tables:
            text = " ".join(cell.text for row in table.rows for cell in row.cells)
            if "Subtotal" in text and "IVA (19%)" in text and "Total" in text:
                found = True
                break
        assert found is True

    def test_ipc_note_present_for_services(self):
        """Para esquema 'services' debe incluir nota de indexación IPC."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["services"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        full_text = _full_text(doc).lower()
        assert "ipc" in full_text
        assert "dane" in full_text

    def test_ipc_note_present_for_support_maintenance(self):
        """Para esquema 'support_maintenance' debe incluir nota de indexación IPC."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["support_maintenance"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        full_text = _full_text(doc).lower()
        assert "ipc" in full_text

    def test_ipc_note_absent_for_licensing(self):
        """Para esquema 'licensing' NO debe incluir nota de indexación IPC."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["licensing"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        full_text = _full_text(doc)
        # La nota IPC no debe aparecer en licenciamiento
        assert "IPC" not in full_text

    # ------------------------------------------------------------------ #
    # Fecha automática                                                     #
    # ------------------------------------------------------------------ #

    def test_letter_has_real_date_not_placeholder(self):
        """La carta de presentación debe usar la fecha actual, no '[FECHA]'."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="Medellín",
            scheme_types=["licensing"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        full_text = _full_text(doc)
        assert "[FECHA]" not in full_text
        today = date.today()
        month_name = _MONTHS_ES[today.month]
        assert month_name in full_text
        assert str(today.year) in full_text

    # ------------------------------------------------------------------ #
    # Numeración de secciones                                             #
    # ------------------------------------------------------------------ #

    def test_section_numbering(self):
        """Las secciones principales deben estar correctamente numeradas del 1 al 6."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["licensing"],
            products=[], context_text="", scope_text="", letter_text="",
        )
        headings = [p.text for p in doc.paragraphs if p.style.name == "Heading 1"]
        numbered = [h for h in headings if h and h[0].isdigit()]
        # Debe haber al menos 6 secciones numeradas
        assert len(numbered) >= 6
        # Verificar que PLAZO es la sección 3
        assert any("3." in h and "PLAZO" in h.upper() for h in numbered)
        # Verificar que CONDICIONES es la sección 4
        assert any("4." in h and "CONDICIONES" in h.upper() for h in numbered)
        # Verificar que SERVICIOS EXCLUIDOS es la sección 5
        assert any("5." in h and "EXCLUIDOS" in h.upper() for h in numbered)

    # ------------------------------------------------------------------ #
    # Categorización del alcance                                          #
    # ------------------------------------------------------------------ #

    def test_scope_groups_by_category(self):
        """Si los productos tienen categoría, deben agruparse en subsecciones."""
        gen = DocumentGenerator()
        from app.services.portfolio_service import PortfolioProduct

        products_with_cat = [
            PortfolioProduct(
                name="Solución Nueva A", product_type="Plataforma",
                description="", business_framework="", revenue_info="",
                operational_costs="", monetization_model="", pricing_model="",
                country="Colombia", category="Nuevas soluciones"
            ),
            PortfolioProduct(
                name="Modernización B", product_type="Plataforma",
                description="", business_framework="", revenue_info="",
                operational_costs="", monetization_model="", pricing_model="",
                country="Colombia", category="Modernización"
            ),
        ]

        doc = gen.generate_proposal_docx(
            title="T", client_name="C", client_position="",
            client_entity="E", client_city="B",
            scheme_types=["licensing"],
            products=products_with_cat,
            context_text="", scope_text="", letter_text="",
        )
        headings_h2 = [p.text for p in doc.paragraphs if p.style.name == "Heading 2"]
        combined = " ".join(headings_h2)
        assert "Nuevas soluciones" in combined
        assert "Modernización" in combined
