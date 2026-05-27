"""
Tests para el router de generación de documentos (app/routers/documents.py).

Estrategia:
- Casos 404: propuesta inexistente → no requieren mocking.
- Casos de éxito: se parchea PortfolioService para evitar depender del xlsx.
  DocumentGenerator se ejecuta normalmente con python-docx.
- Error 500 en PDF: se parchean _build_proposal_docx y DocumentGenerator.
"""
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi import status

DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


# ── Helper: crear cliente + propuesta ────────────────────────────────────────
def _create_proposal(client, sample_client_data, sample_proposal_data) -> int:
    c_res = client.post("/api/clients/", json=sample_client_data)
    assert c_res.status_code == status.HTTP_201_CREATED
    client_id = c_res.json()["id"]

    p_data = {**sample_proposal_data, "client_id": client_id}
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
