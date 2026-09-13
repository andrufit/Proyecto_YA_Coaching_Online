from datetime import datetime, timedelta, timezone
import hashlib
import smtplib

import pytest
from sqlalchemy import select
from app.core.config import settings
from app.models.password_reset import PasswordReset
from app.services import password_reset_service as recovery
from tests.test_auth_api import client  # noqa: F401


@pytest.fixture
def mailbox(monkeypatch):
    messages = []
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from", "noreply@example.com")
    monkeypatch.setattr(recovery, "send_reset_email", lambda email, token: messages.append((email, token)))
    return messages


def register(client):
    response = client.post("/api/v1/auth/register", json={"email": "reset@example.com", "password": "OriginalPass123!"})
    assert response.status_code == 201


def login(client, password):
    return client.post("/api/v1/auth/login", data={"username": "reset@example.com", "password": password})


def test_reset_single_use_and_revokes_existing_session(client, mailbox):
    register(client)
    old_token = login(client, "OriginalPass123!").json()["access_token"]
    response = client.post("/api/v1/auth/forgot-password", json={"email": "RESET@example.com"})
    assert response.status_code == 200
    token = mailbox[0][1]
    assert token not in response.text
    result = client.post("/api/v1/auth/reset-password", json={"token": token, "password": "NewPassword123!"})
    assert result.status_code == 200
    assert login(client, "OriginalPass123!").status_code == 401
    fresh = login(client, "NewPassword123!")
    assert fresh.status_code == 200
    assert client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {old_token}"}).status_code == 401
    assert client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {fresh.json()['access_token']}"}).status_code == 200
    assert client.post("/api/v1/auth/reset-password", json={"token": token, "password": "AnotherPass123!"}).status_code == 400


def test_generic_response_and_cooldown(client, mailbox):
    register(client)
    a = client.post("/api/v1/auth/forgot-password", json={"email": "reset@example.com"})
    b = client.post("/api/v1/auth/forgot-password", json={"email": "missing@example.com"})
    c = client.post("/api/v1/auth/forgot-password", json={"email": "reset@example.com"})
    assert a.json() == b.json() == c.json()
    assert len(mailbox) == 1


def test_expired_link_and_hash_storage(client, mailbox):
    register(client)
    client.post("/api/v1/auth/forgot-password", json={"email": "reset@example.com"})
    token = mailbox[0][1]
    from app.main import app
    from app.api.dependencies import get_db
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    try:
        record = db.scalar(select(PasswordReset))
        assert record.token_hash == hashlib.sha256(token.encode()).hexdigest()
        assert record.token_hash != token
        record.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    finally:
        generator.close()
    result = client.post("/api/v1/auth/reset-password", json={"token": token, "password": "NewPassword123!"})
    assert result.status_code == 400
    assert login(client, "OriginalPass123!").status_code == 200


def test_invalid_link_and_password_validation(client, mailbox):
    register(client)
    client.post("/api/v1/auth/forgot-password", json={"email": "reset@example.com"})
    token = mailbox[0][1]
    assert client.post("/api/v1/auth/reset-password", json={"token": "x" * 43, "password": "NewPassword123!"}).status_code == 400
    assert client.post("/api/v1/auth/reset-password", json={"token": token, "password": "short"}).status_code == 422
    assert client.post("/api/v1/auth/reset-password", json={"token": token, "password": "NewPassword123!"}).status_code == 200


def test_unconfigured_mail_returns_uniform_503(client, monkeypatch):
    monkeypatch.setattr(settings, "smtp_host", "")
    register(client)
    for email in ["reset@example.com", "missing@example.com"]:
        assert client.post("/api/v1/auth/forgot-password", json={"email": email}).status_code == 503


def test_delivery_failure_rolls_back_without_disclosing_account(client, mailbox, monkeypatch):
    register(client)
    def fail(*args):
        raise smtplib.SMTPException("test failure")
    monkeypatch.setattr(recovery, "send_reset_email", fail)
    response = client.post("/api/v1/auth/forgot-password", json={"email": "reset@example.com"})
    assert response.status_code == 200
    assert response.json()["message"] == recovery.GENERIC_MESSAGE
    from app.main import app
    from app.api.dependencies import get_db
    generator = app.dependency_overrides[get_db]()
    try:
        assert next(generator).scalar(select(PasswordReset)) is None
    finally:
        generator.close()
