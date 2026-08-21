import asyncio
import logging
import smtplib
from email.message import EmailMessage

from core.config import (
    EMAIL_FROM_ADDRESS,
    ENV,
    PASSWORD_RESET_URL_BASE,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
)

logger = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task] = set()


def validate_email_config() -> None:
    """
    Fail fast at startup rather than silently falling back to logging reset
    links instead of emailing them once deployed to production.
    """
    if ENV == "production" and not SMTP_HOST:
        raise RuntimeError("SMTP_HOST is not set; cannot send password reset emails in production")


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


def schedule_password_reset_email(to_email: str, token: str) -> asyncio.Task:
    """
    Fire-and-forget: schedules delivery without making the caller wait on
    SMTP. A reference to the task is kept until it finishes so it isn't
    garbage-collected mid-flight.
    """
    task = asyncio.create_task(send_password_reset_email(to_email, token))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task
