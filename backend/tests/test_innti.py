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

    # ---------------------------------------------------------------------- #
    # Tests para los 5 métodos nuevos (Tarea 1)                               #
    # ---------------------------------------------------------------------- #

    def _mock_openai(self, mock_openai_class, response_text: str):
        """Helper: configura el mock de OpenAI para devolver response_text."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = response_text
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client

    @patch("app.services.innti_service.OpenAI")
    def test_generate_validity_section(self, mock_openai_class):
        """generate_validity_section debe incluir scheme_type en el prompt del usuario."""
        mock_client = self._mock_openai(mock_openai_class, "Vigencia generada")
        service = InntiService()
        result = service.generate_validity_section("licensing")
        assert result == "Vigencia generada"
        user_msg = mock_client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
        assert "licensing" in user_msg

    @patch("app.services.innti_service.OpenAI")
    def test_generate_economic_conditions_section(self, mock_openai_class):
        """generate_economic_conditions_section debe incluir productos y scheme en el prompt."""
        mock_client = self._mock_openai(mock_openai_class, "Condiciones generadas")
        service = InntiService()
        result = service.generate_economic_conditions_section(
            ["Qx-Tránsito", "DEI"], "licensing", "Licenciamiento"
        )
        assert result == "Condiciones generadas"
        user_msg = mock_client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
        assert "Qx-Tránsito" in user_msg
        assert "DEI" in user_msg
        assert "Licenciamiento" in user_msg

    @patch("app.services.innti_service.OpenAI")
    def test_generate_payment_terms_section(self, mock_openai_class):
        """generate_payment_terms_section debe incluir scheme_type en el prompt."""
        mock_client = self._mock_openai(mock_openai_class, "Forma de pago generada")
        service = InntiService()
        result = service.generate_payment_terms_section("services")
        assert result == "Forma de pago generada"
        user_msg = mock_client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
        assert "services" in user_msg

    @patch("app.services.innti_service.OpenAI")
    def test_generate_excluded_services_section(self, mock_openai_class):
        """generate_excluded_services_section debe generar texto sobre servicios excluidos."""
        mock_client = self._mock_openai(mock_openai_class, "<p>Servicios excluidos generados</p>")
        service = InntiService()
        result = service.generate_excluded_services_section()
        assert result == "<p>Servicios excluidos generados</p>"
        # Verifica que el prompt menciona servicios excluidos
        user_msg = mock_client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
        assert "EXCLUIDOS" in user_msg.upper()

    @patch("app.services.innti_service.OpenAI")
    def test_generate_ip_section(self, mock_openai_class):
        """generate_ip_section debe incluir el nombre del cliente en el prompt."""
        mock_client = self._mock_openai(mock_openai_class, "<p>IP generada para cliente</p>")
        service = InntiService()
        result = service.generate_ip_section("Consorcio ITS Bogotá")
        assert result == "<p>IP generada para cliente</p>"
        user_msg = mock_client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
        assert "Consorcio ITS Bogotá" in user_msg

    @patch("app.services.innti_service.OpenAI")
    def test_generate_cover_letter(self, mock_openai_class):
        """generate_cover_letter debe incluir destinatario y entidad en el prompt."""
        mock_client = self._mock_openai(mock_openai_class, "Carta generada")
        service = InntiService()
        result = service.generate_cover_letter(
            "Carlos Pérez", "Director TI", "Entidad Distrital", "Propuesta Qx"
        )
        assert result == "Carta generada"
        user_msg = mock_client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
        assert "Carlos Pérez" in user_msg
        assert "Entidad Distrital" in user_msg
