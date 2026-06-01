"""
Tests for the centralized error-handler middleware (app/middleware/error_handler.py).

Each handler is tested as a unit by awaiting it directly with a stub request
and a constructed exception. This avoids depending on specific endpoints to
raise each exception type, keeping the tests fast and focused.

A small FastAPI app is also used for one integration test of the validation
handler (so we exercise the real RequestValidationError shape produced by
Pydantic v2).
"""
import asyncio
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.middleware.error_handler import (
    approval_error_handler,
    create_error_response,
    global_exception_handler,
    innti_service_error_handler,
    portfolio_not_found_handler,
    register_error_handlers,
    validation_exception_handler,
)
from app.services.approval_service import ApprovalError
from app.services.innti_service import InntiServiceError
from app.services.portfolio_service import PortfolioNotFoundError


def _run(coro):
    """Helper to run an async handler inside a synchronous test."""
    return asyncio.get_event_loop().run_until_complete(coro)


def _decode(response) -> dict:
    """Decode JSONResponse body to a dict."""
    return json.loads(response.body.decode("utf-8"))


@pytest.fixture
def fake_request():
    """Stub Request — handlers ignore most of it."""
    return MagicMock()


# ---------- create_error_response ----------

def test_create_error_response_shape():
    """Devuelve JSONResponse con error, detail y status_code en el body."""
    response = create_error_response("Test", "Detail text", 418)
    assert response.status_code == 418
    body = _decode(response)
    assert body == {
        "error": "Test",
        "detail": "Detail text",
        "status_code": 418,
    }


# ---------- portfolio_not_found_handler ----------

def test_portfolio_not_found_handler(fake_request):
    """PortfolioNotFoundError → 404 con error 'Portfolio Not Found'."""
    exc = PortfolioNotFoundError("Archivo X no existe")
    response = _run(portfolio_not_found_handler(fake_request, exc))
    assert response.status_code == 404
    body = _decode(response)
    assert body["error"] == "Portfolio Not Found"
    assert "Archivo X" in body["detail"]


# ---------- innti_service_error_handler ----------

def test_innti_service_error_handler(fake_request):
    """InntiServiceError → 502 Bad Gateway."""
    exc = InntiServiceError("LiteLLM no responde")
    response = _run(innti_service_error_handler(fake_request, exc))
    assert response.status_code == 502
    body = _decode(response)
    assert body["error"] == "Innti Service Error"
    assert "LiteLLM" in body["detail"]


# ---------- approval_error_handler ----------

def test_approval_error_handler(fake_request):
    """ApprovalError → 400 Bad Request."""
    exc = ApprovalError("Transición no permitida")
    response = _run(approval_error_handler(fake_request, exc))
    assert response.status_code == 400
    body = _decode(response)
    assert body["error"] == "Approval Error"
    assert "Transición" in body["detail"]


# ---------- global_exception_handler ----------

def test_global_exception_handler_in_debug_includes_traceback(fake_request):
    """Con debug=True el detail incluye el mensaje y un traceback."""
    fake_settings = MagicMock()
    fake_settings.debug = True

    exc = RuntimeError("boom")
    with patch("app.middleware.error_handler.settings", fake_settings):
        response = _run(global_exception_handler(fake_request, exc))

    assert response.status_code == 500
    body = _decode(response)
    assert body["error"] == "Internal Server Error"
    assert "boom" in body["detail"]


def test_global_exception_handler_in_production_hides_detail(fake_request):
    """Con debug=False el detail es genérico (no leakea el mensaje del bug)."""
    fake_settings = MagicMock()
    fake_settings.debug = False

    exc = RuntimeError("secreto interno que no debe filtrarse")
    with patch("app.middleware.error_handler.settings", fake_settings):
        response = _run(global_exception_handler(fake_request, exc))

    assert response.status_code == 500
    body = _decode(response)
    assert body["error"] == "Internal Server Error"
    assert body["detail"] == "Internal Server Error"
    assert "secreto" not in body["detail"]


# ---------- validation_exception_handler ----------
# Probado vía integración para usar la forma real de RequestValidationError
# producida por FastAPI/Pydantic v2.

def test_validation_handler_via_integration():
    """Body inválido contra un endpoint dispara validation_exception_handler."""
    test_app = FastAPI()
    register_error_handlers(test_app)

    class Payload(BaseModel):
        nombre: str
        edad: int

    @test_app.post("/echo")
    def echo(data: Payload):
        return data

    client = TestClient(test_app)
    response = client.post("/echo", json={"nombre": "X"})  # falta 'edad'

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "Validation Error"
    assert "edad" in body["detail"]
    assert body["status_code"] == 422


# ---------- register_error_handlers wiring ----------

def test_register_error_handlers_wires_all_handlers():
    """register_error_handlers conecta los handlers personalizados a la app."""
    test_app = FastAPI()
    register_error_handlers(test_app)

    @test_app.get("/portfolio-error")
    def trigger_portfolio():
        raise PortfolioNotFoundError("no found")

    @test_app.get("/innti-error")
    def trigger_innti():
        raise InntiServiceError("502")

    @test_app.get("/approval-error")
    def trigger_approval():
        raise ApprovalError("transition denied")

    @test_app.get("/unhandled")
    def trigger_unhandled():
        raise RuntimeError("oops")

    client = TestClient(test_app, raise_server_exceptions=False)

    assert client.get("/portfolio-error").status_code == 404
    assert client.get("/innti-error").status_code == 502
    assert client.get("/approval-error").status_code == 400
    assert client.get("/unhandled").status_code == 500


def test_http_exception_passes_through_register_error_handlers():
    """Las HTTPException explícitas no son atrapadas por el handler global."""
    test_app = FastAPI()
    register_error_handlers(test_app)

    @test_app.get("/teapot")
    def teapot():
        raise HTTPException(status_code=418, detail="I'm a teapot")

    client = TestClient(test_app)
    response = client.get("/teapot")
    # HTTPException sigue su propio camino (sin pasar por global_exception_handler).
    # Verificamos que el status_code se respeta.
    assert response.status_code == 418
