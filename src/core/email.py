import asyncio
import logging
import smtplib
from email.message import EmailMessage

from core.config import (
    EMAIL_FROM_ADDRESS,
    PASSWORD_RESET_URL_BASE,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
)

logger = logging.getLogger(__name__)


def _send_password_reset_email_sync(to_email: str, token: str) -> None:
    reset_link = f"{PASSWORD_RESET_URL_BASE}?token={token}"

    if not SMTP_HOST:
        logger.warning("SMTP not configured; password reset link for %s: %s", to_email, reset_link)
        return

    message = EmailMessage()
    message["Subject"] = "Reset your password"
    message["From"] = EMAIL_FROM_ADDRESS
    message["To"] = to_email
    message.set_content(
        "We received a request to reset your password.\n\n"
        f"Reset it here: {reset_link}\n\n"
        "This link expires in 30 minutes. If you didn't request this, you can ignore this email."
    )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(message)
    except smtplib.SMTPException, OSError:
        logger.exception("Failed to send password reset email to %s", to_email)


async def send_password_reset_email(to_email: str, token: str) -> None:
    """
    Send (or, if SMTP isn't configured, log) the password reset link.
    Never raises: /forgot-password must return the same response whether or
    not delivery succeeds, to avoid leaking account existence via errors.
    """
    await asyncio.to_thread(_send_password_reset_email_sync, to_email, token)
