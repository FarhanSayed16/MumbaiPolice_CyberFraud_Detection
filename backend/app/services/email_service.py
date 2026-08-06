import logging
import smtplib
from email.message import EmailMessage
from typing import Optional, TypedDict

from app.config import settings

logger = logging.getLogger(__name__)


class EmailResult(TypedDict):
    success: bool
    mode: str
    detail: str


async def send_email_async(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
) -> EmailResult:
    """
    Send email via SMTP when configured, otherwise log mock dispatch.
    Never claims live delivery without SMTP credentials.
    """
    if not getattr(settings, "ENABLE_EMAILS", False):
        logger.info("Email paused by ENABLE_EMAILS=False. Skipping: %s", subject)
        return {"success": True, "mode": "mock", "detail": "emails paused"}

    mode = (settings.EMAIL_DELIVERY_MODE or "mock").lower()

    if mode == "smtp" and settings.SMTP_HOST and settings.SMTP_FROM:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM
            msg["To"] = to_email
            msg.set_content(body)
            if html_body:
                msg.add_alternative(html_body, subtype="html")

            password = (settings.SMTP_PASSWORD or "").replace(" ", "")
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USER and password:
                    server.login(settings.SMTP_USER, password)
                server.send_message(msg)

            logger.info("SMTP email sent to %s subject=%s", to_email, subject)
            return {"success": True, "mode": "smtp", "detail": "delivered via SMTP"}
        except Exception as exc:
            logger.error("SMTP send failed for %s: %s", to_email, exc, exc_info=True)
            return {"success": False, "mode": "smtp", "detail": f"SMTP error: {exc}"}

    logger.info("--- [MOCK EMAIL DISPATCH] ---")
    logger.info("To: %s", to_email)
    logger.info("Subject: %s", subject)
    logger.info("Body:\n%s", body)
    logger.info("-----------------------------")
    return {
        "success": True,
        "mode": "mock",
        "detail": "logged only — set EMAIL_DELIVERY_MODE=smtp and SMTP_* to send live mail",
    }
