from collections.abc import Generator
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core.database import Base
from app.main import app
from app.models import User


PROFILE_URL = "/api/v1/client-profile"
ASSESSMENTS_URL = f"{PROFILE_URL}/me/assessments"


@pytest.fixture
def db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    try:
        with Session(engine, expire_on_commit=False) as session:
            yield session
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def register_and_login(
    client: TestClient,
    email: str = "cliente@example.com",
) -> dict[str, str]:
    password = "ClaveSegura123!"

    registration = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert registration.status_code == 201, registration.text

    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login.status_code == 200, login.text

    return {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }


@pytest.fixture
def headers(client: TestClient) -> dict[str, str]:
    return register_and_login(client)


@pytest.fixture
def profile_data() -> dict:
    return {
        "full_name": "Cliente de prueba",
        "birth_date": "1995-06-15",
        "sex": "male",
        "height_cm": "175.00",
        "goal": "muscle_gain",
        "training_level": "intermediate",
        "medical_restrictions": "Restricción de prueba",
    }


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("GET", f"{PROFILE_URL}/me", None),
        ("POST", PROFILE_URL, {}),
        ("PATCH", f"{PROFILE_URL}/me", {}),
        ("GET", ASSESSMENTS_URL, None),
        ("POST", ASSESSMENTS_URL, {"weight_kg": "75"}),
    ],
)
def test_endpoints_require_authentication(
    client, method, path, payload
):
    response = client.request(method, path, json=payload)
    assert response.status_code == 401


def test_create_read_update_and_duplicate_profile(
    client, headers, profile_data
):
    created = client.post(
        PROFILE_URL, headers=headers, json=profile_data
    )
    assert created.status_code == 201, created.text
    profile_id = created.json()["id"]

    current_user = client.get(
        "/api/v1/users/me", headers=headers
    )
    assert current_user.status_code == 200
    assert created.json()["user_id"] == current_user.json()["id"]

    duplicate = client.post(
        PROFILE_URL, headers=headers, json=profile_data
    )
    assert duplicate.status_code == 409

    updated = client.patch(
        f"{PROFILE_URL}/me",
        headers=headers,
        json={
            "goal": "maintenance",
            "medical_restrictions": None,
        },
    )
    assert updated.status_code == 200, updated.text

    fetched = client.get(
        f"{PROFILE_URL}/me", headers=headers
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == profile_id
    assert fetched.json()["goal"] == "maintenance"
    assert fetched.json()["medical_restrictions"] is None
    assert fetched.json()["full_name"] == profile_data["full_name"]


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("GET", f"{PROFILE_URL}/me", None),
        ("PATCH", f"{PROFILE_URL}/me", {"goal": "maintenance"}),
        ("GET", ASSESSMENTS_URL, None),
        ("POST", ASSESSMENTS_URL, {"weight_kg": "75"}),
    ],
)
def test_missing_profile_returns_404(
    client, headers, method, path, payload
):
    response = client.request(
        method, path, headers=headers, json=payload
    )
    assert response.status_code == 404


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("full_name", "   "),
        ("height_cm", "0"),
        ("goal", "invalid"),
        ("birth_date", "2999-01-01"),
    ],
)
def test_invalid_profile_is_rejected(
    client, headers, profile_data, field, value
):
    profile_data[field] = value

    response = client.post(
        PROFILE_URL, headers=headers, json=profile_data
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "field",
    [
        "full_name",
        "birth_date",
        "sex",
        "height_cm",
        "goal",
        "training_level",
    ],
)
def test_update_rejects_null_required_fields(
    client, headers, profile_data, field
):
    created = client.post(
        PROFILE_URL, headers=headers, json=profile_data
    )
    assert created.status_code == 201

    response = client.patch(
        f"{PROFILE_URL}/me",
        headers=headers,
        json={field: None},
    )
    assert response.status_code == 422

    fetched = client.get(
        f"{PROFILE_URL}/me", headers=headers
    )
    assert fetched.status_code == 200
    assert fetched.json()[field] is not None


def test_assessments_are_saved_and_sorted(
    client, headers, profile_data
):
    created = client.post(
        PROFILE_URL, headers=headers, json=profile_data
    )
    assert created.status_code == 201

    yesterday = (date.today() - timedelta(days=1)).isoformat()

    for measurement_date, weight in [
        (yesterday, "75.50"),
        (date.today().isoformat(), "75.80"),
    ]:
        response = client.post(
            ASSESSMENTS_URL,
            headers=headers,
            json={
                "assessment_date": measurement_date,
                "weight_kg": weight,
            },
        )
        assert response.status_code == 201, response.text
        assert (
            response.json()["client_profile_id"]
            == created.json()["id"]
        )

    history = client.get(ASSESSMENTS_URL, headers=headers)
    assert history.status_code == 200

    rows = history.json()
    assert len(rows) == 2
    assert rows[0]["assessment_date"] == date.today().isoformat()
    assert Decimal(str(rows[0]["weight_kg"])) == Decimal("75.80")
    assert rows[1]["assessment_date"] == yesterday


@pytest.mark.parametrize(
    "invalid_data",
    [
        {"weight_kg": "0"},
        {"weight_kg": "-1"},
        {"weight_kg": "75", "body_fat_percentage": "101"},
        {"weight_kg": "75", "waist_cm": "-2"},
        {"weight_kg": "75", "assessment_date": "2999-01-01"},
    ],
)
def test_invalid_assessment_is_rejected(
    client, headers, profile_data, invalid_data
):
    created = client.post(
        PROFILE_URL, headers=headers, json=profile_data
    )
    assert created.status_code == 201

    response = client.post(
        ASSESSMENTS_URL, headers=headers, json=invalid_data
    )
    assert response.status_code == 422

    history = client.get(ASSESSMENTS_URL, headers=headers)
    assert history.status_code == 200
    assert history.json() == []


def test_clients_have_separate_profiles_and_assessments(
    client, headers, profile_data
):
    first = client.post(
        PROFILE_URL, headers=headers, json=profile_data
    )
    assert first.status_code == 201

    measurement = client.post(
        ASSESSMENTS_URL,
        headers=headers,
        json={"weight_kg": "75"},
    )
    assert measurement.status_code == 201

    other_headers = register_and_login(
        client, "otro@example.com"
    )

    missing = client.get(
        f"{PROFILE_URL}/me", headers=other_headers
    )
    assert missing.status_code == 404

    second = client.post(
        PROFILE_URL,
        headers=other_headers,
        json={**profile_data, "full_name": "Segundo cliente"},
    )
    assert second.status_code == 201
    assert second.json()["id"] != first.json()["id"]

    other_history = client.get(
        ASSESSMENTS_URL, headers=other_headers
    )
    assert other_history.status_code == 200
    assert other_history.json() == []

    updated = client.patch(
        f"{PROFILE_URL}/me",
        headers=other_headers,
        json={"full_name": "Segundo actualizado"},
    )
    assert updated.status_code == 200

    original = client.get(
        f"{PROFILE_URL}/me", headers=headers
    )
    assert original.status_code == 200
    assert original.json()["full_name"] == profile_data["full_name"]


@pytest.mark.parametrize("role", ["admin", "coach"])
def test_non_client_roles_are_forbidden(
    client, db, headers, profile_data, role
):
    user = db.scalar(
        select(User).where(User.email == "cliente@example.com")
    )
    assert user is not None

    user.role = role
    db.commit()

    requests = [
        ("POST", PROFILE_URL, profile_data),
        ("GET", f"{PROFILE_URL}/me", None),
        ("PATCH", f"{PROFILE_URL}/me", {"goal": "maintenance"}),
        ("POST", ASSESSMENTS_URL, {"weight_kg": "75"}),
        ("GET", ASSESSMENTS_URL, None),
    ]

    for method, path, payload in requests:
        response = client.request(
            method, path, headers=headers, json=payload
        )
        assert response.status_code == 403, response.text