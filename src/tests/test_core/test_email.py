from unittest.mock import MagicMock

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
