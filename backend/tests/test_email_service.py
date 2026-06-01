"""
Tests for EmailService — SMTP-based approval and rejection notifications.
Covers both happy path (mocked smtplib) and failure modes
(SMTP not configured, sendmail exception).
"""
import email
import smtplib
from unittest.mock import MagicMock, patch

import pytest

from app.services.email_service import EmailService


def _extract_html_body(raw_message: str) -> str:
    """Decode the MIME message and return the text/html payload as string."""
    msg = email.message_from_string(raw_message)
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            return part.get_payload(decode=True).decode("utf-8")
    return ""


def _extract_subject(raw_message: str) -> str:
    """Decode the Subject header (handles RFC 2047 encoded-word format)."""
    msg = email.message_from_string(raw_message)
    decoded_parts = email.header.decode_header(msg["Subject"])
    return "".join(
        part.decode(charset or "utf-8") if isinstance(part, bytes) else part
        for part, charset in decoded_parts
    )


@pytest.fixture
def email_service():
    return EmailService()


@pytest.fixture
def smtp_settings():
    """Returns a settings object with SMTP fully configured."""
    settings = MagicMock()
    settings.smtp_host = "smtp.test.local"
    settings.smtp_port = 587
    settings.smtp_user = "user@test.local"
    settings.smtp_password = "secret"
    settings.smtp_from = "noreply@test.local"
    return settings


@pytest.fixture
def empty_smtp_settings():
    """Returns a settings object with no SMTP host configured."""
    settings = MagicMock()
    settings.smtp_host = ""
    return settings


# ---------- send_approval_notification ----------

def test_send_approval_returns_false_when_smtp_not_configured(
    email_service, empty_smtp_settings
):
    """Cuando SMTP no está configurado, no envía y retorna False."""
    with patch(
        "app.services.email_service.get_settings",
        return_value=empty_smtp_settings,
    ):
        result = email_service.send_approval_notification(
            to_email="angela@quipux.com",
            to_name="Ángela",
            proposal_title="Propuesta de Prueba",
            proposal_id=1,
        )
    assert result is False


def test_send_approval_success(email_service, smtp_settings):
    """Envío exitoso retorna True y llama a sendmail con los argumentos esperados."""
    smtp_instance = MagicMock()
    smtp_cm = MagicMock()
    smtp_cm.__enter__.return_value = smtp_instance
    smtp_cm.__exit__.return_value = False

    with patch(
        "app.services.email_service.get_settings",
        return_value=smtp_settings,
    ), patch(
        "app.services.email_service.smtplib.SMTP",
        return_value=smtp_cm,
    ) as mock_smtp:
        result = email_service.send_approval_notification(
            to_email="angela@quipux.com",
            to_name="Ángela",
            proposal_title="Licenciamiento Qx-Tránsito",
            proposal_id=42,
            action_required="revisar y aprobar",
        )

    assert result is True
    mock_smtp.assert_called_once_with("smtp.test.local", 587)
    smtp_instance.starttls.assert_called_once()
    smtp_instance.login.assert_called_once_with("user@test.local", "secret")
    smtp_instance.sendmail.assert_called_once()
    args, _ = smtp_instance.sendmail.call_args
    assert args[0] == "noreply@test.local"
    assert args[1] == "angela@quipux.com"
    # El cuerpo HTML decodificado debe contener el título y el ID
    html_body = _extract_html_body(args[2])
    subject = _extract_subject(args[2])
    assert "Licenciamiento Qx-Tránsito" in html_body
    assert "42" in html_body
    assert "Licenciamiento Qx-Tránsito" in subject


def test_send_approval_default_action_required(email_service, smtp_settings):
    """El parámetro action_required usa 'revisar y aprobar' por defecto."""
    smtp_instance = MagicMock()
    smtp_cm = MagicMock()
    smtp_cm.__enter__.return_value = smtp_instance
    smtp_cm.__exit__.return_value = False

    with patch(
        "app.services.email_service.get_settings",
        return_value=smtp_settings,
    ), patch(
        "app.services.email_service.smtplib.SMTP",
        return_value=smtp_cm,
    ):
        result = email_service.send_approval_notification(
            to_email="vp@quipux.com",
            to_name="Juan Pablo",
            proposal_title="Soporte",
            proposal_id=7,
        )
    assert result is True
    args, _ = smtp_instance.sendmail.call_args
    assert "revisar y aprobar" in _extract_html_body(args[2])


def test_send_approval_returns_false_on_smtp_exception(email_service, smtp_settings):
    """Si smtplib lanza una excepción, retorna False y no propaga el error."""
    with patch(
        "app.services.email_service.get_settings",
        return_value=smtp_settings,
    ), patch(
        "app.services.email_service.smtplib.SMTP",
        side_effect=smtplib.SMTPException("Connection refused"),
    ):
        result = email_service.send_approval_notification(
            to_email="angela@quipux.com",
            to_name="Ángela",
            proposal_title="Test",
            proposal_id=99,
        )
    assert result is False


def test_send_approval_returns_false_on_login_failure(email_service, smtp_settings):
    """Si login falla, retorna False sin propagar la excepción."""
    smtp_instance = MagicMock()
    smtp_instance.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
    smtp_cm = MagicMock()
    smtp_cm.__enter__.return_value = smtp_instance
    smtp_cm.__exit__.return_value = False

    with patch(
        "app.services.email_service.get_settings",
        return_value=smtp_settings,
    ), patch(
        "app.services.email_service.smtplib.SMTP",
        return_value=smtp_cm,
    ):
        result = email_service.send_approval_notification(
            to_email="angela@quipux.com",
            to_name="Ángela",
            proposal_title="Test",
            proposal_id=1,
        )
    assert result is False
    smtp_instance.sendmail.assert_not_called()


# ---------- send_rejection_notification ----------

def test_send_rejection_returns_false_when_smtp_not_configured(
    email_service, empty_smtp_settings
):
    """Cuando SMTP no está configurado, no envía y retorna False."""
    with patch(
        "app.services.email_service.get_settings",
        return_value=empty_smtp_settings,
    ):
        result = email_service.send_rejection_notification(
            to_email="creador@quipux.com",
            to_name="Comercial",
            proposal_title="Propuesta X",
            proposal_id=5,
            rejector_name="Ángela García",
        )
    assert result is False


def test_send_rejection_success_with_comments(email_service, smtp_settings):
    """Envío exitoso con comentarios — los incluye en el cuerpo del mensaje."""
    smtp_instance = MagicMock()
    smtp_cm = MagicMock()
    smtp_cm.__enter__.return_value = smtp_instance
    smtp_cm.__exit__.return_value = False

    with patch(
        "app.services.email_service.get_settings",
        return_value=smtp_settings,
    ), patch(
        "app.services.email_service.smtplib.SMTP",
        return_value=smtp_cm,
    ):
        result = email_service.send_rejection_notification(
            to_email="creador@quipux.com",
            to_name="Comercial",
            proposal_title="Propuesta X",
            proposal_id=5,
            rejector_name="Ángela García",
            comments="Falta seccion de alcance",
        )
    assert result is True
    args, _ = smtp_instance.sendmail.call_args
    html_body = _extract_html_body(args[2])
    assert "Falta seccion de alcance" in html_body
    assert "Comentarios" in html_body


def test_send_rejection_success_without_comments(email_service, smtp_settings):
    """Envío exitoso sin comentarios — no incluye la sección de comentarios."""
    smtp_instance = MagicMock()
    smtp_cm = MagicMock()
    smtp_cm.__enter__.return_value = smtp_instance
    smtp_cm.__exit__.return_value = False

    with patch(
        "app.services.email_service.get_settings",
        return_value=smtp_settings,
    ), patch(
        "app.services.email_service.smtplib.SMTP",
        return_value=smtp_cm,
    ):
        result = email_service.send_rejection_notification(
            to_email="creador@quipux.com",
            to_name="Comercial",
            proposal_title="Propuesta X",
            proposal_id=5,
            rejector_name="Juan Pablo",
        )
    assert result is True
    args, _ = smtp_instance.sendmail.call_args
    # Sin comentarios, el bloque "Comentarios:" no aparece
    assert "<strong>Comentarios:</strong>" not in _extract_html_body(args[2])


def test_send_rejection_returns_false_on_smtp_exception(email_service, smtp_settings):
    """Si smtplib lanza una excepción durante el rechazo, retorna False."""
    with patch(
        "app.services.email_service.get_settings",
        return_value=smtp_settings,
    ), patch(
        "app.services.email_service.smtplib.SMTP",
        side_effect=ConnectionError("No route to host"),
    ):
        result = email_service.send_rejection_notification(
            to_email="creador@quipux.com",
            to_name="Comercial",
            proposal_title="Propuesta X",
            proposal_id=5,
            rejector_name="Juan Pablo",
            comments="Motivo del rechazo",
        )
    assert result is False
