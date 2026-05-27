"""
Pruebas unitarias para el generador de documentos Word.

Cubre:
  - _strip_html: limpieza de contenido HTML de TipTap
  - _has_content: detección de contenido real en HTML (Tarea 2)
  - generate_proposal_docx: lógica de fallback en secciones 5 y 6.1
  - _add_table_of_contents: campo TOC real con OOXML field codes
  - _build_proposal_docx (router): integración con campos de BD
"""
import io
import zipfile
import pytest
from unittest.mock import MagicMock, patch

from app.services.document_generator import DocumentGenerator, _strip_html, _has_content
from app.services.portfolio_service import PortfolioProduct


# ---------------------------------------------------------------------------
# Helpers de test
# ---------------------------------------------------------------------------

def _make_product(name: str = "Qx-Producto Test", category: str = "") -> PortfolioProduct:
    return PortfolioProduct(
        name=name,
        product_type="Plataforma",
        description="Descripción de prueba",
        business_framework="",
        revenue_info="",
        operational_costs="",
        monetization_model="",
        pricing_model="",
        country="Colombia",
        category=category,
    )


def _extract_text(doc) -> str:
    """Extrae todo el texto plano de un documento python-docx."""
    return "\n".join(p.text for p in doc.paragraphs)


def _build_minimal_docx(
    excluded_services: str | None = None,
    ip_section: str | None = None,
) -> object:
    """Invoca el generador con los parámetros mínimos necesarios."""
    gen = DocumentGenerator()
    return gen.generate_proposal_docx(
        title="Propuesta de Prueba",
        client_name="Juan Pérez",
        client_position="Gerente TI",
        client_entity="Entidad Prueba",
        client_city="Bogotá",
        scheme_types=["licensing"],
        products=[_make_product()],
        context_text="Contexto de prueba",
        scope_text="Alcance de prueba",
        letter_text="Carta de prueba",
        validity_period=None,
        economic_conditions=None,
        payment_terms=None,
        excluded_services=excluded_services,
        ip_section=ip_section,
    )


# ---------------------------------------------------------------------------
# Helper compartido: extrae el XML de word/document.xml del .docx generado
# ---------------------------------------------------------------------------

def _get_doc_xml(doc) -> str:
    """Serializa el Document a bytes y devuelve el XML interno de word/document.xml."""
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    with zipfile.ZipFile(buf) as z:
        return z.read("word/document.xml").decode("utf-8")


# ---------------------------------------------------------------------------
# Tests de _strip_html
# ---------------------------------------------------------------------------

class TestStripHtml:
    """Pruebas para la función utilitaria _strip_html."""

    def test_removes_paragraph_tags(self):
        result = _strip_html("<p>Texto de prueba</p>")
        assert "<p>" not in result
        assert "Texto de prueba" in result

    def test_removes_strong_and_em(self):
        result = _strip_html("<strong>Negrita</strong> y <em>cursiva</em>")
        assert "<strong>" not in result
        assert "Negrita" in result
        assert "cursiva" in result

    def test_decodes_html_entities(self):
        result = _strip_html("Tom&amp;Jerry &lt;personaje&gt; &quot;caricatura&quot;")
        assert "&amp;" not in result
        assert "Tom&Jerry" in result
        assert "<personaje>" in result
        assert '"caricatura"' in result

    def test_nbsp_becomes_space(self):
        result = _strip_html("Palabra&nbsp;separada")
        assert "&nbsp;" not in result
        assert "Palabra separada" in result

    def test_list_items_separated_by_newlines(self):
        html = "<ul><li>Ítem uno</li><li>Ítem dos</li></ul>"
        result = _strip_html(html)
        assert "Ítem uno" in result
        assert "Ítem dos" in result

    def test_br_becomes_newline(self):
        result = _strip_html("Línea A<br/>Línea B")
        assert "Línea A" in result
        assert "Línea B" in result

    def test_plain_text_unchanged(self):
        plain = "Texto sin etiquetas"
        assert _strip_html(plain) == plain

    def test_empty_string_returns_empty(self):
        assert _strip_html("") == ""

    def test_strips_nested_tags(self):
        html = "<div><p><strong>Título</strong></p><p>Párrafo</p></div>"
        result = _strip_html(html)
        assert "Título" in result
        assert "Párrafo" in result
        assert "<" not in result


# ---------------------------------------------------------------------------
# Tests de _has_content (Tarea 2 — helper de detección de contenido real)
# ---------------------------------------------------------------------------

class TestHasContent:
    """Tests para la función utilitaria _has_content."""

    def test_none_returns_false(self):
        assert not _has_content(None)

    def test_empty_string_returns_false(self):
        assert not _has_content("")

    def test_whitespace_only_returns_false(self):
        assert not _has_content("   \n  ")

    def test_empty_p_tag_returns_false(self):
        """TipTap genera <p></p> en pestañas vacías; no debe considerarse contenido."""
        assert not _has_content("<p></p>")

    def test_p_with_content_returns_true(self):
        assert _has_content("<p>Texto real</p>")

    def test_plain_text_returns_true(self):
        assert _has_content("Texto sin tags")

    def test_ul_with_items_returns_true(self):
        assert _has_content("<ul><li>Item</li></ul>")

    def test_nested_empty_tags_returns_false(self):
        """Tags anidados sin texto real no cuentan como contenido."""
        assert not _has_content("<p><br></p>")

    def test_strong_with_text_returns_true(self):
        assert _has_content("<strong>Negrita</strong>")


# ---------------------------------------------------------------------------
# Tests de _add_table_of_contents — campo TOC real con OOXML field codes
# ---------------------------------------------------------------------------

class TestTableOfContents:
    """Verifica que el documento contenga un campo TOC real, no texto placeholder."""

    def test_toc_field_code_is_present(self):
        """El XML del documento debe contener la instrucción del campo TOC."""
        doc = _build_minimal_docx()
        xml = _get_doc_xml(doc)
        assert "TOC" in xml, "No se encontró el campo TOC en el documento generado"

    def test_toc_has_dirty_true_for_auto_update(self):
        """El campo TOC debe llevar w:dirty='true' para que Word lo actualice al abrir."""
        doc = _build_minimal_docx()
        xml = _get_doc_xml(doc)
        # lxml puede serializar el atributo con comillas simples o dobles
        assert 'dirty="true"' in xml or "dirty='true'" in xml, (
            "El campo TOC no tiene el atributo w:dirty='true'"
        )

    def test_toc_includes_headings_1_to_3(self):
        """El campo TOC debe capturar los niveles Heading 1, 2 y 3."""
        doc = _build_minimal_docx()
        xml = _get_doc_xml(doc)
        assert "1-3" in xml, "El campo TOC no incluye la especificación de niveles 1-3"

    def test_toc_has_hyperlink_switch(self):
        """El campo TOC debe incluir el switch \\h para generar hipervínculos internos."""
        doc = _build_minimal_docx()
        xml = _get_doc_xml(doc)
        # La instrucción almacenada en instrText contiene los switches sin escape
        assert r"\h" in xml, "El campo TOC no incluye el switch \\h (hipervínculos)"

    def test_no_placeholder_text(self):
        """El texto estático de marcador de posición no debe aparecer en el documento."""
        doc = _build_minimal_docx()
        text = _extract_text(doc)
        assert "[El índice se genera automáticamente al actualizar campos en Word]" not in text

    def test_toc_title_is_present(self):
        """El encabezado 'TABLA DE CONTENIDO' debe seguir presente en el documento."""
        doc = _build_minimal_docx()
        text = _extract_text(doc)
        assert "TABLA DE CONTENIDO" in text


# ---------------------------------------------------------------------------
# Tests de generate_proposal_docx — sección 5 (Servicios Excluidos)
# ---------------------------------------------------------------------------

class TestSection5ExcludedServices:
    """Sección 5: el contenido de BD tiene precedencia sobre el texto hardcodeado."""

    def test_uses_db_content_when_provided(self):
        """Si excluded_services tiene contenido, debe aparecer en el documento."""
        doc = _build_minimal_docx(excluded_services="Servicio personalizado del cliente")
        text = _extract_text(doc)
        assert "Servicio personalizado del cliente" in text

    def test_db_content_replaces_hardcoded_list(self):
        """Cuando hay contenido en BD, el primer ítem hardcodeado NO debe aparecer."""
        hardcoded_first = DocumentGenerator.EXCLUDED_SERVICES[0]
        doc = _build_minimal_docx(excluded_services="Solo mi servicio excluido")
        text = _extract_text(doc)
        assert hardcoded_first not in text

    def test_fallback_to_hardcoded_when_none(self):
        """Sin contenido en BD (None), debe usar la lista hardcodeada completa."""
        hardcoded_first = DocumentGenerator.EXCLUDED_SERVICES[0]
        doc = _build_minimal_docx(excluded_services=None)
        text = _extract_text(doc)
        assert hardcoded_first in text

    def test_fallback_to_hardcoded_when_empty_string(self):
        """Cadena vacía: debe omitir la sección."""
        hardcoded_first = DocumentGenerator.EXCLUDED_SERVICES[0]
        doc = _build_minimal_docx(excluded_services="")
        text = _extract_text(doc)
        assert hardcoded_first not in text
        assert "SERVICIOS EXCLUIDOS" not in text

    def test_strips_html_from_db_content(self):
        """El contenido HTML de TipTap llega limpio al Word."""
        html_content = "<p>Servicio <strong>excluido</strong> del alcance</p>"
        doc = _build_minimal_docx(excluded_services=html_content)
        text = _extract_text(doc)
        assert "<p>" not in text
        assert "<strong>" not in text
        assert "Servicio excluido del alcance" in text


# ---------------------------------------------------------------------------
# Tests de generate_proposal_docx — sección 6.1 (Propiedad Intelectual)
# ---------------------------------------------------------------------------

class TestSection61IpSection:
    """Sección 6.1: el contenido de BD tiene precedencia sobre el texto hardcodeado."""

    def test_uses_db_content_when_provided(self):
        """Si ip_section tiene contenido, debe aparecer en el documento."""
        doc = _build_minimal_docx(ip_section="IP personalizada de la propuesta")
        text = _extract_text(doc)
        assert "IP personalizada de la propuesta" in text

    def test_db_content_replaces_hardcoded_ip_text(self):
        """Cuando hay contenido en BD, el texto hardcodeado de IP NO debe aparecer."""
        # El IP_TEXT hardcodeado empieza con "La arquitectura"
        doc = _build_minimal_docx(ip_section="Nuestros propios términos de IP")
        text = _extract_text(doc)
        assert "La arquitectura, los diseños técnicos" not in text

    def test_fallback_to_hardcoded_when_none(self):
        """Sin contenido en BD, debe usar el texto hardcodeado de IP."""
        doc = _build_minimal_docx(ip_section=None)
        text = _extract_text(doc)
        # El texto hardcodeado contiene "QUIPUX puede utilizarlos libremente"
        assert "QUIPUX puede utilizarlos libremente" in text

    def test_fallback_to_hardcoded_when_empty_string(self):
        """Cadena vacía: debe omitir la sección."""
        doc = _build_minimal_docx(ip_section="")
        text = _extract_text(doc)
        assert "Propiedad Intelectual" not in text

    def test_client_entity_interpolated_in_fallback(self):
        """El nombre del cliente se interpola correctamente en el fallback hardcodeado (cuando es None)."""
        gen = DocumentGenerator()
        doc = gen.generate_proposal_docx(
            title="Test",
            client_name="Ana López",
            client_position="Directora",
            client_entity="MiEntidad SA",
            client_city="Cali",
            scheme_types=["licensing"],
            products=[],
            context_text="",
            scope_text="",
            letter_text="",
            ip_section=None,
        )
        text = _extract_text(doc)
        assert "MiEntidad SA" in text

    def test_strips_html_from_db_content(self):
        """El contenido HTML de TipTap llega limpio al Word."""
        html_ip = "<p>Todos los derechos de <em>propiedad intelectual</em> pertenecen a QUIPUX.</p>"
        doc = _build_minimal_docx(ip_section=html_ip)
        text = _extract_text(doc)
        assert "<p>" not in text
        assert "<em>" not in text
        assert "propiedad intelectual" in text


# ---------------------------------------------------------------------------
# Test de integración: ambos campos activos simultáneamente
# ---------------------------------------------------------------------------

class TestBothFieldsTogether:
    """Verifica que ambos campos funcionen correctamente en simultáneo."""

    def test_both_db_fields_present(self):
        """Ambos campos de BD deben aparecer; ningún texto hardcodeado."""
        doc = _build_minimal_docx(
            excluded_services="Exclusión A",
            ip_section="IP Sección B",
        )
        text = _extract_text(doc)

        assert "Exclusión A" in text
        assert "IP Sección B" in text

        # Hardcoded NO debe aparecer
        assert DocumentGenerator.EXCLUDED_SERVICES[0] not in text
        assert "La arquitectura, los diseños técnicos" not in text

    def test_both_fields_empty_uses_all_hardcoded(self):
        """Con ambos campos None se usan los textos hardcodeados de fallback."""
        doc = _build_minimal_docx(excluded_services=None, ip_section=None)
        text = _extract_text(doc)

        assert DocumentGenerator.EXCLUDED_SERVICES[0] in text
        assert "Propiedad Intelectual" in text


# ---------------------------------------------------------------------------
# Test de integración con el router documents.py
# ---------------------------------------------------------------------------

class TestDocumentsRouterIntegration:
    """Verifica que _build_proposal_docx pase los campos excluidos e ip al generador."""

    def test_router_passes_excluded_services_to_generator(self):
        """_build_proposal_docx debe propagar excluded_services de la BD al generador."""
        from app.routers.documents import _build_proposal_docx
        from unittest.mock import patch, MagicMock
        import tempfile
        from pathlib import Path

        # Construir mocks de Propuesta y Cliente
        mock_client = MagicMock()
        mock_client.name = "Ana García"
        mock_client.position = "Gerente"
        mock_client.entity = "Entidad Test"
        mock_client.city = "Medellín"

        mock_scheme = MagicMock()
        mock_scheme.scheme_type.value = "licensing"

        mock_product = MagicMock()
        mock_product.product_name = "Producto Test"
        mock_product.category = ""

        mock_proposal = MagicMock()
        mock_proposal.id = 99
        mock_proposal.title = "Propuesta Test"
        mock_proposal.cover_title = None
        mock_proposal.client = mock_client
        mock_proposal.schemes = [mock_scheme]
        mock_proposal.products = [mock_product]
        mock_proposal.context_content = ""
        mock_proposal.scope_content = ""
        mock_proposal.letter_content = ""
        mock_proposal.validity_period = None
        mock_proposal.economic_conditions = None
        mock_proposal.payment_terms = None
        mock_proposal.excluded_services = "Servicio excluido de prueba"
        mock_proposal.ip_section = "IP de prueba"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_proposal

        mock_settings = MagicMock()
        mock_settings.portfolio_file_path = "dummy.xlsx"

        mock_portfolio = MagicMock()
        mock_portfolio.get_by_names.return_value = [_make_product()]

        with patch("app.routers.documents.PortfolioService", return_value=mock_portfolio):
            with patch("app.routers.documents.DocumentGenerator") as MockGenerator:
                mock_gen_instance = MagicMock()
                MockGenerator.return_value = mock_gen_instance
                mock_gen_instance.generate_proposal_docx.return_value = MagicMock()
                mock_gen_instance.save_document.return_value = str(
                    Path(tempfile.gettempdir()) / "innti_docs" / "propuesta_99.docx"
                )

                _build_proposal_docx(
                    proposal_id=99,
                    use_innti=False,
                    db=mock_db,
                    settings=mock_settings,
                )

                call_kwargs = mock_gen_instance.generate_proposal_docx.call_args.kwargs
                assert call_kwargs["excluded_services"] == "Servicio excluido de prueba"
                assert call_kwargs["ip_section"] == "IP de prueba"

    def test_router_passes_empty_strings_when_db_fields_are_none(self):
        """Cuando los campos son None en BD, el router pasa cadena vacía al generador."""
        from app.routers.documents import _build_proposal_docx
        import tempfile
        from pathlib import Path

        mock_client = MagicMock()
        mock_client.name = "Pedro Ruiz"
        mock_client.position = ""
        mock_client.entity = "Corp Test"
        mock_client.city = "Cali"

        mock_scheme = MagicMock()
        mock_scheme.scheme_type.value = "services"

        mock_product = MagicMock()
        mock_product.product_name = "Producto Y"
        mock_product.category = ""

        mock_proposal = MagicMock()
        mock_proposal.id = 77
        mock_proposal.title = "Propuesta Y"
        mock_proposal.cover_title = None
        mock_proposal.client = mock_client
        mock_proposal.schemes = [mock_scheme]
        mock_proposal.products = [mock_product]
        mock_proposal.context_content = None
        mock_proposal.scope_content = None
        mock_proposal.letter_content = None
        mock_proposal.validity_period = None
        mock_proposal.economic_conditions = None
        mock_proposal.payment_terms = None
        mock_proposal.excluded_services = None   # ← None en BD
        mock_proposal.ip_section = None           # ← None en BD

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_proposal

        mock_settings = MagicMock()
        mock_settings.portfolio_file_path = "dummy.xlsx"

        mock_portfolio = MagicMock()
        mock_portfolio.get_by_names.return_value = []

        with patch("app.routers.documents.PortfolioService", return_value=mock_portfolio):
            with patch("app.routers.documents.DocumentGenerator") as MockGenerator:
                mock_gen_instance = MagicMock()
                MockGenerator.return_value = mock_gen_instance
                mock_gen_instance.generate_proposal_docx.return_value = MagicMock()
                mock_gen_instance.save_document.return_value = str(
                    Path(tempfile.gettempdir()) / "innti_docs" / "propuesta_77.docx"
                )

                _build_proposal_docx(
                    proposal_id=77,
                    use_innti=False,
                    db=mock_db,
                    settings=mock_settings,
                )

                call_kwargs = mock_gen_instance.generate_proposal_docx.call_args.kwargs
                # None en BD → el router lo convierte a "" antes de pasar al generador.
                # Con "" el generador OMITE las secciones (Tarea 2: pestañas vacías no aparecen).
                assert call_kwargs["excluded_services"] == ""
                assert call_kwargs["ip_section"] == ""
