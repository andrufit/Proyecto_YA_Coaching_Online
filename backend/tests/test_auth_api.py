from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core.database import Base
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    testing_session_local = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(engine)

    def override_get_db() -> Generator[
        Session,
        None,
        None,
    ]:
        with testing_session_local() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_register_login_and_current_user(
    client: TestClient,
) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "CLIENTE@EXAMPLE.COM",
            "password": "ClaveSegura123!",
        },
    )

    assert register_response.status_code == 201

    registered_user = register_response.json()

    assert registered_user["email"] == "cliente@example.com"
    assert registered_user["role"] == "client"
    assert "hashed_password" not in registered_user
    assert "password" not in registered_user

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "cliente@example.com",
            "password": "ClaveSegura123!",
        },
    )

    assert login_response.status_code == 200

    token_data = login_response.json()

    assert token_data["token_type"] == "bearer"
    assert token_data["access_token"]

    current_user_response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": (
                f"Bearer {token_data['access_token']}"
            ),
        },
    )

    assert current_user_response.status_code == 200
    assert (
        current_user_response.json()["email"]
        == "cliente@example.com"
    )


def test_duplicate_registration(
    client: TestClient,
) -> None:
    user_data = {
        "email": "cliente@example.com",
        "password": "ClaveSegura123!",
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_login_with_invalid_password(
    client: TestClient,
) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "cliente@example.com",
            "password": "ClaveSegura123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "cliente@example.com",
            "password": "ClaveIncorrecta",
        },
    )

    assert response.status_code == 401


def test_current_user_requires_token(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/users/me",
    )

    assert response.status_code == 401