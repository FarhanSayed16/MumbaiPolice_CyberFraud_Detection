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
    Outbound mail. HARD-OFF unless ENABLE_EMAILS=true AND EMAIL_DELIVERY_MODE=smtp
    and SMTP_* are set. Default config keeps ENABLE_EMAILS=false so SLA jobs never spam.
    """
    # Absolute kill-switch (default False in Settings / .env)
    if not settings.ENABLE_EMAILS:
        logger.info("[EMAIL OFF] Skipped (ENABLE_EMAILS=false): to=%s subject=%s", to_email, subject)
        return {"success": True, "mode": "disabled", "detail": "ENABLE_EMAILS=false — no outbound mail"}

    mode = (settings.EMAIL_DELIVERY_MODE or "mock").lower().strip()
    if mode != "smtp":
        logger.info("[EMAIL MOCK] to=%s subject=%s", to_email, subject)
        return {
            "success": True,
            "mode": "mock",
            "detail": "logged only — set ENABLE_EMAILS=true and EMAIL_DELIVERY_MODE=smtp for live mail",
        }

    if not (settings.SMTP_HOST and settings.SMTP_FROM):
        logger.warning("[EMAIL] smtp mode but SMTP_HOST/FROM missing — not sending")
        return {"success": False, "mode": "smtp", "detail": "SMTP_HOST or SMTP_FROM missing"}

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
