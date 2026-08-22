import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

import core.email as email


async def test_send_password_reset_email_logs_when_smtp_not_configured(monkeypatch, caplog):
    monkeypatch.setattr(email, "SMTP_HOST", None)

    with caplog.at_level("INFO"):
        await email.send_password_reset_email("user@example.com", "sometoken")

    assert "user@example.com" in caplog.text
    assert "sometoken" in caplog.text


async def test_send_password_reset_email_sends_via_smtp(monkeypatch):
    monkeypatch.setattr(email, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(email, "SMTP_PORT", 587)
    monkeypatch.setattr(email, "SMTP_USERNAME", "smtp-user")
    monkeypatch.setattr(email, "SMTP_PASSWORD", "smtp-pass")

    smtp_instance = MagicMock()
    smtp_instance.__enter__.return_value = smtp_instance
    smtp_cls = MagicMock(return_value=smtp_instance)
    monkeypatch.setattr(email.smtplib, "SMTP", smtp_cls)

    await email.send_password_reset_email("user@example.com", "sometoken")

    smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=10)
    smtp_instance.starttls.assert_called_once()
    smtp_instance.login.assert_called_once_with("smtp-user", "smtp-pass")
    smtp_instance.send_message.assert_called_once()
    sent_message = smtp_instance.send_message.call_args.args[0]
    assert sent_message["To"] == "user@example.com"
    assert "sometoken" in sent_message.get_content()


async def test_send_password_reset_email_swallows_smtp_errors(monkeypatch):
    monkeypatch.setattr(email, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(email.smtplib, "SMTP", MagicMock(side_effect=OSError("connection refused")))

    await email.send_password_reset_email("user@example.com", "sometoken")


async def test_schedule_password_reset_email_runs_in_background(monkeypatch):
    send_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(email, "send_password_reset_email", send_mock)

    task = email.schedule_password_reset_email("user@example.com", "sometoken")
    assert isinstance(task, asyncio.Task)

    await task

    send_mock.assert_awaited_once_with("user@example.com", "sometoken")


async def test_send_verification_email_logs_when_smtp_not_configured(monkeypatch, caplog):
    monkeypatch.setattr(email, "SMTP_HOST", None)

    with caplog.at_level("INFO"):
        await email.send_verification_email("user@example.com", "sometoken")

    assert "user@example.com" in caplog.text
    assert "sometoken" in caplog.text


async def test_send_verification_email_sends_via_smtp(monkeypatch):
    monkeypatch.setattr(email, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(email, "SMTP_PORT", 587)
    monkeypatch.setattr(email, "SMTP_USERNAME", "smtp-user")
    monkeypatch.setattr(email, "SMTP_PASSWORD", "smtp-pass")

    smtp_instance = MagicMock()
    smtp_instance.__enter__.return_value = smtp_instance
    smtp_cls = MagicMock(return_value=smtp_instance)
    monkeypatch.setattr(email.smtplib, "SMTP", smtp_cls)

    await email.send_verification_email("user@example.com", "sometoken")

    smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=10)
    smtp_instance.starttls.assert_called_once()
    smtp_instance.login.assert_called_once_with("smtp-user", "smtp-pass")
    smtp_instance.send_message.assert_called_once()
    sent_message = smtp_instance.send_message.call_args.args[0]
    assert sent_message["To"] == "user@example.com"
    assert "sometoken" in sent_message.get_content()


async def test_send_verification_email_swallows_smtp_errors(monkeypatch):
    monkeypatch.setattr(email, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(email.smtplib, "SMTP", MagicMock(side_effect=OSError("connection refused")))

    await email.send_verification_email("user@example.com", "sometoken")


async def test_schedule_verification_email_runs_in_background(monkeypatch):
    send_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(email, "send_verification_email", send_mock)

    task = email.schedule_verification_email("user@example.com", "sometoken")
    assert isinstance(task, asyncio.Task)

    await task

    send_mock.assert_awaited_once_with("user@example.com", "sometoken")


def test_validate_email_config_raises_in_production_without_smtp(monkeypatch):
    monkeypatch.setattr(email, "ENV", "production")
    monkeypatch.setattr(email, "SMTP_HOST", None)

    with pytest.raises(RuntimeError):
        email.validate_email_config()


def test_validate_email_config_allows_development_without_smtp(monkeypatch):
    monkeypatch.setattr(email, "ENV", "development")
    monkeypatch.setattr(email, "SMTP_HOST", None)

    email.validate_email_config()


def test_validate_email_config_allows_production_with_smtp(monkeypatch):
    monkeypatch.setattr(email, "ENV", "production")
    monkeypatch.setattr(email, "SMTP_HOST", "smtp.example.com")

    email.validate_email_config()
