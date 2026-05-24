"""
Pruebas unitarias para el servicio de integración con Innti.
Usa mocks para no depender del endpoint real.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.innti_service import InntiService, InntiServiceError


class TestInntiService:
    """Tests del servicio de integración con Innti (mocked)."""

    @patch("app.services.innti_service.OpenAI")
    def test_generate_text_success(self, mock_openai_class):
        """Debe retornar texto generado correctamente."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Texto generado de prueba"
        mock_client.chat.completions.create.return_value = mock_response

        service = InntiService()
        result = service.generate_text("system", "user prompt")

        assert result == "Texto generado de prueba"
        mock_client.chat.completions.create.assert_called_once()

    @patch("app.services.innti_service.OpenAI")
    def test_generate_text_api_error(self, mock_openai_class):
        """Debe lanzar InntiServiceError en caso de fallo de API."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Connection timeout")

        service = InntiService()

        with pytest.raises(InntiServiceError, match="Connection timeout"):
            service.generate_text("system", "user prompt")

    @patch("app.services.innti_service.OpenAI")
    def test_generate_context_section(self, mock_openai_class):
        """Debe generar sección de contexto con parámetros correctos."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Contexto generado"
        mock_client.chat.completions.create.return_value = mock_response

        service = InntiService()
        result = service.generate_context_section("Consorcio ITS", "Licenciamiento")

        assert result == "Contexto generado"
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert "Quipux" in messages[0]["content"]
        assert "Consorcio ITS" in messages[1]["content"]

    @patch("app.services.innti_service.OpenAI")
    def test_generate_scope_section(self, mock_openai_class):
        """Debe generar sección de alcance con lista de productos."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Alcance generado"
        mock_client.chat.completions.create.return_value = mock_response

        service = InntiService()
        products = ["Qx-Tránsito", "DEI", "Cobro Coactivo"]
        result = service.generate_scope_section(products, "licensing")

        assert result == "Alcance generado"
        call_args = mock_client.chat.completions.create.call_args
        user_msg = call_args.kwargs["messages"][1]["content"]
        assert "Qx-Tránsito" in user_msg
        assert "DEI" in user_msg

    @patch("app.services.innti_service.OpenAI")
    def test_generate_text_empty_response(self, mock_openai_class):
        """Debe manejar respuesta vacía de la API."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create.return_value = mock_response

        service = InntiService()
        result = service.generate_text("system", "prompt")
        assert result == ""
