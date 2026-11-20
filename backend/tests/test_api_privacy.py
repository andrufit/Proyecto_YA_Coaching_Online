from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services import user_service
from tests.test_auth_api import client  # noqa: F401 - shared isolated database fixture


def test_explicit_origins(monkeypatch):
    monkeypatch.setattr(settings, "frontend_url", "https://app.example.test/")
    monkeypatch.setattr(settings, "cors_extra_origins", "http://localhost:5174,https://app.example.test")
    assert settings.browser_origins == ["https://app.example.test", "http://localhost:5174"]


@pytest.mark.parametrize("origin", ["*", "https://*.example.test", "https://app.example.test/path"])
def test_only_complete_origins_accepted(monkeypatch, origin):
    monkeypatch.setattr(settings, "cors_extra_origins", origin)
    with pytest.raises(ValueError):
        _ = settings.browser_origins


def test_browser_preflight_allows_frontend_and_authorization():
    with TestClient(app) as client:
        headers = {
            "Origin": settings.browser_origins[0],
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "authorization,content-type",
        }
        allowed = client.options("/api/v1/users/me", headers=headers)
        assert allowed.status_code == 200
        assert allowed.headers["Access-Control-Allow-Origin"] == headers["Origin"]
        headers["Origin"] = "https://unlisted.example.test"
        denied = client.options("/api/v1/users/me", headers=headers)
        assert "Access-Control-Allow-Origin" not in denied.headers


def test_validation_errors_do_not_echo_form_values(client):
    response = client.post("/api/v1/auth/reset-password", json={"token": "demo-link", "password": "tiny"})
    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert {tuple(e["loc"]) for e in response.json()["detail"]} == {("body", "password"), ("body", "token")}
    assert all(set(e) == {"loc", "type", "msg"} for e in response.json()["detail"])
    assert "demo-link" not in response.text and "tiny" not in response.text


def test_auth_and_private_responses_are_not_cached(client):
    form = {"email": "privacy@example.com", "password": "ExamplePassword000"}
    created = client.post("/api/v1/auth/register", json=form)
    assert created.status_code == 201
    issued = client.post("/api/v1/auth/login", data={"username": form["email"], "password": form["password"]})
    assert issued.status_code == 200
    assert issued.headers["cache-control"] == "no-store"
    profile = client.get("/api/v1/users/me", headers={"Authorization": "Bearer " + issued.json()["access_token"]})
    assert profile.status_code == 200
    assert profile.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("exists,active", [(False, False), (True, False), (True, True)])
def test_failed_login_always_checks_one_hash(monkeypatch, exists, active):
    user = SimpleNamespace(is_active=active, hashed_password="sample") if exists else None
    monkeypatch.setattr(user_service, "get_user_by_email", lambda db, email: user)
    verify = Mock(return_value=False)
    monkeypatch.setattr(user_service, "verify_password", verify)
    assert user_service.authenticate_user(None, "demo@example.com", "demo") is None
    verify.assert_called_once_with("demo", user.hashed_password if exists else user_service._DUMMY_PASSWORD_HASH)
