"""
Servicio de envío de notificaciones por correo electrónico.
Usado para el flujo de aprobaciones internas.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


class EmailServiceError(Exception):
    """Error en el envío de email."""
    pass


class EmailService:
    """Servicio de envío de emails para notificaciones de aprobación."""

    def send_approval_notification(
        self,
        to_email: str,
        to_name: str,
        proposal_title: str,
        proposal_id: int,
        action_required: str = "revisar y aprobar",
    ) -> bool:
        """
        Envía una notificación de aprobación por email.

        Args:
            to_email: Email del destinatario.
            to_name: Nombre del destinatario.
            proposal_title: Título de la propuesta.
            proposal_id: ID de la propuesta.
            action_required: Acción requerida (ej: "revisar y aprobar").

        Returns:
            True si se envió correctamente, False si hubo error.
        """
        settings = get_settings()

        if not settings.smtp_host:
            logger.warning("SMTP no configurado. Notificación no enviada.")
            return False

        subject = f"[Innti Propuestas] Propuesta pendiente de aprobación: {proposal_title}"

        html_body = f"""
        <html>
        <body style="font-family: Calibri, Arial, sans-serif; padding: 20px;">
            <h2 style="color: #1a365d;">Notificación de Propuesta</h2>
            <p>Estimado/a <strong>{to_name}</strong>,</p>
            <p>Se requiere su aprobación para la siguiente propuesta comercial:</p>
            <table style="border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Propuesta:</td>
                    <td style="padding: 8px;">{proposal_title}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">ID:</td>
                    <td style="padding: 8px;">{proposal_id}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Acción requerida:</td>
                    <td style="padding: 8px;">{action_required}</td>
                </tr>
            </table>
            <p>Por favor ingrese al sistema para {action_required} la propuesta.</p>
            <p style="color: #718096; font-size: 12px;">
                Este es un mensaje automático del sistema Innti Propuestas.
            </p>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_from, to_email, msg.as_string())
            logger.info(f"Email enviado a {to_email} para propuesta {proposal_id}")
            return True
        except Exception as e:
            logger.error(f"Error enviando email a {to_email}: {str(e)}")
            return False

    def send_rejection_notification(
        self,
        to_email: str,
        to_name: str,
        proposal_title: str,
        proposal_id: int,
        rejector_name: str,
        comments: Optional[str] = None,
    ) -> bool:
        """Envía notificación de rechazo de propuesta."""
        settings = get_settings()

        if not settings.smtp_host:
            logger.warning("SMTP no configurado. Notificación no enviada.")
            return False

        subject = f"[Innti Propuestas] Propuesta rechazada: {proposal_title}"
        comments_html = f"<p><strong>Comentarios:</strong> {comments}</p>" if comments else ""

        html_body = f"""
        <html>
        <body style="font-family: Calibri, Arial, sans-serif; padding: 20px;">
            <h2 style="color: #c53030;">Propuesta Rechazada</h2>
            <p>Estimado/a <strong>{to_name}</strong>,</p>
            <p>La propuesta <strong>{proposal_title}</strong> (ID: {proposal_id})
            ha sido rechazada por <strong>{rejector_name}</strong>.</p>
            {comments_html}
            <p>Por favor revise los comentarios y realice las correcciones necesarias.</p>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_from, to_email, msg.as_string())
            return True
        except Exception as e:
            logger.error(f"Error enviando email de rechazo: {str(e)}")
            return False
