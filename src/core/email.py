import asyncio
import logging
import smtplib
from collections.abc import Coroutine
from email.message import EmailMessage
from typing import Any

from core.config import (
    EMAIL_FROM_ADDRESS,
    EMAIL_VERIFICATION_URL_BASE,
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


def _send_email_sync(to_email: str, subject: str, body: str) -> None:
    if not SMTP_HOST:
        logger.warning("SMTP not configured; email for %s not sent:\n%s", to_email, body)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = EMAIL_FROM_ADDRESS
    message["To"] = to_email
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(message)
    except smtplib.SMTPException, OSError:
        logger.exception("Failed to send email to %s", to_email)


async def send_password_reset_email(to_email: str, token: str) -> None:
    """
    Send (or, if SMTP isn't configured, log) the password reset link.
    Never raises: /forgot-password must return the same response whether or
    not delivery succeeds, to avoid leaking account existence via errors.
    """
    reset_link = f"{PASSWORD_RESET_URL_BASE}?token={token}"
    body = (
        "We received a request to reset your password.\n\n"
        f"Reset it here: {reset_link}\n\n"
        "This link expires in 30 minutes. If you didn't request this, you can ignore this email."
    )
    await asyncio.to_thread(_send_email_sync, to_email, "Reset your password", body)


async def send_verification_email(to_email: str, token: str) -> None:
    """
    Send (or, if SMTP isn't configured, log) the email verification link.
    Never raises, for the same reason as send_password_reset_email.
    """
    verify_link = f"{EMAIL_VERIFICATION_URL_BASE}?token={token}"
    body = (
        "Thanks for registering. Please verify your email address to activate your account.\n\n"
        f"Verify it here: {verify_link}\n\n"
        "This link expires in 24 hours. If you didn't create this account, you can ignore this "
        "email."
    )
    await asyncio.to_thread(_send_email_sync, to_email, "Verify your email", body)


def _schedule(coro: Coroutine[Any, Any, None]) -> asyncio.Task:
    """
    Fire-and-forget: schedules delivery without making the caller wait on
    SMTP. A reference to the task is kept until it finishes so it isn't
    garbage-collected mid-flight.
    """
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


def schedule_password_reset_email(to_email: str, token: str) -> asyncio.Task:
    return _schedule(send_password_reset_email(to_email, token))


def schedule_verification_email(to_email: str, token: str) -> asyncio.Task:
    return _schedule(send_verification_email(to_email, token))
