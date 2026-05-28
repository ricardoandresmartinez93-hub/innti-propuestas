"""
Tests para el router de generación de documentos (app/routers/documents.py).

Estrategia:
- Casos 404: propuesta inexistente → no requieren mocking.
- Casos de éxito: se parchea PortfolioService para evitar depender del xlsx.
  DocumentGenerator se ejecuta normalmente con python-docx.
- Error 500 en PDF: se parchean _build_proposal_docx y DocumentGenerator.
- Documentos separados: se verifican respuestas ZIP cuando combine_schemes=False.
"""
import io
import tempfile
import zipfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi import status

from app.services.innti_service import InntiServiceError

DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _create_proposal(client, sample_client_data, sample_proposal_data) -> int:
    c_res = client.post("/api/clients/", json=sample_client_data)
    assert c_res.status_code == status.HTTP_201_CREATED
    client_id = c_res.json()["id"]

    p_data = {**sample_proposal_data, "client_id": client_id}
    p_res = client.post("/api/proposals/", json=p_data)
    assert p_res.status_code == status.HTTP_201_CREATED
    return p_res.json()["id"]


def _create_multi_scheme_proposal(client, sample_client_data) -> int:
    """Crea una propuesta con dos esquemas y combine_schemes=False."""
    c_res = client.post("/api/clients/", json=sample_client_data)
    assert c_res.status_code == status.HTTP_201_CREATED
    client_id = c_res.json()["id"]

    p_data = {
        "title": "Propuesta multi-esquema",
        "code": "TEST-001",
        "client_id": client_id,
        "combine_schemes": False,
        "products": [],
        "schemes": [
            {"scheme_type": "licensing", "payment_frequency": "unico"},
            {"scheme_type": "services", "payment_frequency": "mensual"},
        ],
    }
    p_res = client.post("/api/proposals/", json=p_data)
    assert p_res.status_code == status.HTTP_201_CREATED
    return p_res.json()["id"]


# ── Tests: generate-document ─────────────────────────────────────────────────
def test_generate_document_not_found(client):
    """Generar documento con propuesta inexistente → 404."""
    response = client.post("/api/proposals/99999/generate-document?use_innti=false")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_generate_document_success(client, sample_client_data, sample_proposal_data):
    """
    Genera documento Word correctamente.
    Se parchea PortfolioService para devolver lista vacía de productos.
    El DocumentGenerator genera un .docx real con python-docx.
    """
    pid = _create_proposal(client, sample_client_data, sample_proposal_data)

    with patch("app.routers.documents.PortfolioService") as MockPortfolio:
        MockPortfolio.return_value.get_by_names.return_value = []

        response = client.post(
            f"/api/proposals/{pid}/generate-document",
            params={"use_innti": False},
        )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.content) > 0  # el body contiene el archivo


# ── Tests: generate-pdf ───────────────────────────────────────────────────────
def test_generate_pdf_not_found(client):
    """Generar PDF con propuesta inexistente → 404."""
    response = client.post("/api/proposals/99999/generate-pdf?use_innti=false")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_generate_pdf_conversion_error_returns_500(client, sample_client_data, sample_proposal_data):
    """
    Si convert_docx_to_pdf lanza una excepción, el endpoint devuelve 500
    con el mensaje 'No se pudo generar el PDF'.
    """
    pid = _create_proposal(client, sample_client_data, sample_proposal_data)

    # Crear un archivo .docx falso para que _build_proposal_docx lo devuelva
    tmpdir = Path(tempfile.gettempdir()) / "innti_docs"
    tmpdir.mkdir(exist_ok=True)
    fake_docx = tmpdir / f"propuesta_{pid}.docx"
    fake_docx.write_bytes(b"PK\x03\x04")  # cabecera mínima de ZIP/DOCX

    with patch("app.routers.documents._build_proposal_docx", return_value=fake_docx):
        with patch("app.routers.documents.DocumentGenerator") as MockDocGen:
            MockDocGen.return_value.convert_docx_to_pdf.side_effect = Exception(
                "WeasyPrint no disponible"
            )
            response = client.post(
                f"/api/proposals/{pid}/generate-pdf",
                params={"use_innti": False},
            )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "No se pudo generar el PDF" in response.json()["detail"]


# ── Tests: documentos separados (combine_schemes=False) ──────────────────────
def test_generate_document_separate_returns_zip(client, sample_client_data):
    """
    Con combine_schemes=False y 2 esquemas, generate-document devuelve un ZIP
    que contiene un .docx por esquema.
    """
    pid = _create_multi_scheme_proposal(client, sample_client_data)

    with patch("app.routers.documents.PortfolioService") as MockPortfolio:
        MockPortfolio.return_value.get_by_names.return_value = []
        response = client.post(
            f"/api/proposals/{pid}/generate-document",
            params={"use_innti": False},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/zip"

    z = zipfile.ZipFile(io.BytesIO(response.content))
    names = z.namelist()
    assert len(names) == 2
    assert any("licenciamiento" in n for n in names)
    assert any("servicios" in n for n in names)


def test_generate_pdf_separate_returns_zip(client, sample_client_data):
    """
    Con combine_schemes=False y 2 esquemas, generate-pdf devuelve un ZIP
    con un .pdf por esquema (convert_docx_to_pdf se parchea para crear el .pdf vacío).
    """
    pid = _create_multi_scheme_proposal(client, sample_client_data)

    def fake_convert(docx_path: str, pdf_path: str) -> None:
        Path(pdf_path).write_bytes(b"%PDF-1.4")

    with patch("app.routers.documents.PortfolioService") as MockPortfolio:
        MockPortfolio.return_value.get_by_names.return_value = []
        with patch.object(
            __import__("app.services.document_generator", fromlist=["DocumentGenerator"]).DocumentGenerator,
            "convert_docx_to_pdf",
            side_effect=fake_convert,
        ):
            response = client.post(
                f"/api/proposals/{pid}/generate-pdf",
                params={"use_innti": False},
            )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/zip"

    z = zipfile.ZipFile(io.BytesIO(response.content))
    names = z.namelist()
    assert len(names) == 2
    assert all(n.endswith(".pdf") for n in names)


def test_generate_document_separate_single_scheme_returns_docx(
    client, sample_client_data, sample_proposal_data
):
    """
    Con combine_schemes=False pero solo 1 esquema, devuelve un .docx único (no ZIP).
    """
    c_res = client.post("/api/clients/", json=sample_client_data)
    client_id = c_res.json()["id"]
    p_data = {
        **sample_proposal_data,
        "client_id": client_id,
        "combine_schemes": False,
        "schemes": [{"scheme_type": "licensing", "payment_frequency": "unico"}],
    }
    p_res = client.post("/api/proposals/", json=p_data)
    pid = p_res.json()["id"]

    with patch("app.routers.documents.PortfolioService") as MockPortfolio:
        MockPortfolio.return_value.get_by_names.return_value = []
        response = client.post(
            f"/api/proposals/{pid}/generate-document",
            params={"use_innti": False},
        )

    assert response.status_code == status.HTTP_200_OK
    assert "wordprocessingml" in response.headers["content-type"]


def test_generate_document_separate_innti_per_scheme(client, sample_client_data):
    """
    Con combine_schemes=False y use_innti=True, las secciones de forma de pago y
    condiciones económicas se generan con el tipo de esquema individual (no combinado).
    Cada documento debe recibir el contenido de pago correspondiente a su esquema.
    """
    pid = _create_multi_scheme_proposal(client, sample_client_data)

    with patch("app.routers.documents.PortfolioService") as MockPortfolio:
        MockPortfolio.return_value.get_by_names.return_value = []

        with patch("app.routers.documents.InntiService") as MockInntiCls:
            mock_innti = MagicMock()
            MockInntiCls.return_value = mock_innti
            mock_innti.generate_context_section.return_value = "context"
            mock_innti.generate_scope_section.return_value = "scope"
            mock_innti.generate_cover_letter.return_value = "letter"
            mock_innti.generate_validity_section.return_value = "validity"
            mock_innti.generate_economic_conditions_section.return_value = "economic"
            mock_innti.generate_payment_terms_section.return_value = "payment"
            mock_innti.generate_excluded_services_section.return_value = "excluded"
            mock_innti.generate_ip_section.return_value = "ip"

            response = client.post(
                f"/api/proposals/{pid}/generate-document",
                params={"use_innti": True},
            )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/zip"

    # Verificar que generate_payment_terms_section fue llamada con cada esquema individual
    payment_calls = [
        call.args[0]
        for call in mock_innti.generate_payment_terms_section.call_args_list
    ]
    assert "licensing" in payment_calls, (
        f"Se esperaba llamada con 'licensing', se recibieron: {payment_calls}"
    )
    assert "services" in payment_calls, (
        f"Se esperaba llamada con 'services', se recibieron: {payment_calls}"
    )

    # Verificar que generate_economic_conditions_section fue llamada con cada esquema individual
    economic_calls = [
        call.args[1]  # segundo arg es scheme_type
        for call in mock_innti.generate_economic_conditions_section.call_args_list
    ]
    assert "licensing" in economic_calls
    assert "services" in economic_calls


# ── Tests: generate-annex ────────────────────────────────────────────────────
def test_generate_annex_not_found(client):
    """Generar anexo técnico con propuesta inexistente → 404."""
    response = client.post("/api/proposals/99999/generate-annex")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_generate_annex_success(client, sample_client_data, sample_proposal_data):
    """
    Genera el anexo técnico correctamente.
    Se parchea PortfolioService; DocumentGenerator se ejecuta con python-docx.
    """
    pid = _create_proposal(client, sample_client_data, sample_proposal_data)

    with patch("app.routers.documents.PortfolioService") as MockPortfolio:
        MockPortfolio.return_value.get_by_names.return_value = []

        response = client.post(f"/api/proposals/{pid}/generate-annex")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.content) > 0


# ── Tests: resiliencia ante fallos parciales de Innti ─────────────────────────
def test_generate_document_innti_cover_letter_failure_uses_fallback(
    client, sample_client_data, sample_proposal_data
):
    """
    Cuando generate_cover_letter lanza InntiServiceError se usa el template
    de respaldo: letter_content queda NO vacío y las demás secciones se persisten.
    """
    pid = _create_proposal(client, sample_client_data, sample_proposal_data)

    with patch("app.routers.documents.PortfolioService") as MockPortfolio:
        MockPortfolio.return_value.get_by_names.return_value = []

        with patch("app.routers.documents.InntiService") as MockInntiCls:
            mock_innti = MagicMock()
            MockInntiCls.return_value = mock_innti
            mock_innti.generate_context_section.return_value = "contexto generado"
            mock_innti.generate_scope_section.return_value = "alcance generado"
            mock_innti.generate_cover_letter.side_effect = InntiServiceError("timeout")
            mock_innti.generate_validity_section.return_value = "plazo generado"
            mock_innti.generate_economic_conditions_section.return_value = "condiciones"
            mock_innti.generate_payment_terms_section.return_value = "forma de pago"
            mock_innti.generate_excluded_services_section.return_value = "excluidos"
            mock_innti.generate_ip_section.return_value = "ip"

            response = client.post(
                f"/api/proposals/{pid}/generate-document",
                params={"use_innti": True},
            )

    assert response.status_code == status.HTTP_200_OK

    updated = client.get(f"/api/proposals/{pid}")
    data = updated.json()
    assert data["context_content"] == "contexto generado", (
        "context_content debe persistirse aunque cover_letter falle"
    )
    assert data["scope_content"] == "alcance generado", (
        "scope_content debe persistirse aunque cover_letter falle"
    )
    # Con el fallback, letter_content debe ser el template (no vacío)
    assert data["letter_content"], (
        "letter_content debe usar el template de respaldo cuando Innti falla"
    )
    assert "Juan Pablo Ramírez Madrid" in data["letter_content"], (
        "El template de respaldo debe incluir la firma del VP"
    )


def test_generate_document_innti_cover_letter_empty_uses_fallback(
    client, sample_client_data, sample_proposal_data
):
    """
    Cuando generate_cover_letter devuelve string vacío (sin excepción)
    se usa igualmente el template de respaldo.
    """
    pid = _create_proposal(client, sample_client_data, sample_proposal_data)

    with patch("app.routers.documents.PortfolioService") as MockPortfolio:
        MockPortfolio.return_value.get_by_names.return_value = []

        with patch("app.routers.documents.InntiService") as MockInntiCls:
            mock_innti = MagicMock()
            MockInntiCls.return_value = mock_innti
            mock_innti.generate_context_section.return_value = "contexto"
            mock_innti.generate_scope_section.return_value = "alcance"
            mock_innti.generate_cover_letter.return_value = ""   # vacío, no excepción
            mock_innti.generate_validity_section.return_value = "plazo"
            mock_innti.generate_economic_conditions_section.return_value = "condiciones"
            mock_innti.generate_payment_terms_section.return_value = "pago"
            mock_innti.generate_excluded_services_section.return_value = "excluidos"
            mock_innti.generate_ip_section.return_value = "ip"

            response = client.post(
                f"/api/proposals/{pid}/generate-document",
                params={"use_innti": True},
            )

    assert response.status_code == status.HTTP_200_OK

    updated = client.get(f"/api/proposals/{pid}")
    data = updated.json()
    assert data["letter_content"], (
        "letter_content debe usar el template cuando Innti devuelve vacío"
    )
    assert "Juan Pablo Ramírez Madrid" in data["letter_content"]


def test_generate_document_innti_all_sections_persisted(
    client, sample_client_data, sample_proposal_data
):
    """
    Cuando todas las llamadas Innti tienen éxito, TODAS las secciones
    (incluida letter_content) se persisten en la BD.
    """
    pid = _create_proposal(client, sample_client_data, sample_proposal_data)

    with patch("app.routers.documents.PortfolioService") as MockPortfolio:
        MockPortfolio.return_value.get_by_names.return_value = []

        with patch("app.routers.documents.InntiService") as MockInntiCls:
            mock_innti = MagicMock()
            MockInntiCls.return_value = mock_innti
            mock_innti.generate_context_section.return_value = "contexto"
            mock_innti.generate_scope_section.return_value = "alcance"
            mock_innti.generate_cover_letter.return_value = "<p>Carta generada</p>"
            mock_innti.generate_validity_section.return_value = "plazo"
            mock_innti.generate_economic_conditions_section.return_value = "condiciones"
            mock_innti.generate_payment_terms_section.return_value = "pago"
            mock_innti.generate_excluded_services_section.return_value = "excluidos"
            mock_innti.generate_ip_section.return_value = "ip"

            response = client.post(
                f"/api/proposals/{pid}/generate-document",
                params={"use_innti": True},
            )

    assert response.status_code == status.HTTP_200_OK

    updated = client.get(f"/api/proposals/{pid}")
    data = updated.json()
    assert data["context_content"] == "contexto"
    assert data["scope_content"] == "alcance"
    assert data["letter_content"] == "<p>Carta generada</p>", (
        "letter_content debe persistirse cuando generate_cover_letter tiene éxito"
    )
