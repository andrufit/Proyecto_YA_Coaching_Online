from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core.database import Base
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import User


@pytest.fixture
def context() -> Generator[dict, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    testing_sessions = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    Base.metadata.create_all(engine)
    previous_overrides = app.dependency_overrides.copy()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_sessions() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with testing_sessions() as db:
            users = {}
            password_hash = hash_password("ClavePrueba123!")

            for name, role in [
                ("admin", "admin"),
                ("coach", "coach"),
                ("other_coach", "coach"),
                ("client", "client"),
                ("other_client", "client"),
            ]:
                user = User(
                    email=f"{name}@example.com",
                    hashed_password=password_hash,
                    role=role,
                    is_active=True,
                )
                db.add(user)
                users[name] = user

            db.commit()

            ids = {
                name: user.id
                for name, user in users.items()
            }

        headers = {
            name: {
                "Authorization": (
                    "Bearer "
                    + create_access_token(subject=str(user_id))
                )
            }
            for name, user_id in ids.items()
        }

        with TestClient(app) as api:
            yield {
                "api": api,
                "ids": ids,
                "headers": headers,
                "sessions": testing_sessions,
            }
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        Base.metadata.drop_all(engine)
        engine.dispose()


def assign(context, coach_name="coach", client_name="client"):
    client_id = context["ids"][client_name]
    coach_id = context["ids"][coach_name]

    return context["api"].put(
        f"/api/v1/admin/clients/{client_id}/coach",
        headers=context["headers"]["admin"],
        json={"coach_id": coach_id},
    )


def create_profile(context, client_name="client"):
    return context["api"].post(
        "/api/v1/client-profile",
        headers=context["headers"][client_name],
        json={
            "full_name": "Cliente de prueba",
            "birth_date": "1995-06-15",
            "sex": "male",
            "height_cm": "175.00",
            "goal": "maintenance",
            "training_level": "intermediate",
            "medical_restrictions": None,
        },
    )


def test_admin_creates_coach_and_coach_can_login(context):
    api = context["api"]
    data = {
        "email": "NUEVO.COACH@example.com",
        "password": "ClaveCoach123!",
    }

    created = api.post(
        "/api/v1/admin/coaches",
        headers=context["headers"]["admin"],
        json=data,
    )

    assert created.status_code == 201, created.text
    assert created.json()["role"] == "coach"
    assert created.json()["email"] == "nuevo.coach@example.com"
    assert "password" not in created.json()
    assert "hashed_password" not in created.json()

    login = api.post(
        "/api/v1/auth/login",
        data={
            "username": "nuevo.coach@example.com",
            "password": data["password"],
        },
    )

    assert login.status_code == 200, login.text

    me = api.get(
        "/api/v1/users/me",
        headers={
            "Authorization": (
                f"Bearer {login.json()['access_token']}"
            )
        },
    )

    assert me.status_code == 200
    assert me.json()["role"] == "coach"


def test_duplicate_coach_email_is_rejected(context):
    response = context["api"].post(
        "/api/v1/admin/coaches",
        headers=context["headers"]["admin"],
        json={
            "email": "coach@example.com",
            "password": "ClaveCoach123!",
        },
    )

    assert response.status_code == 409


@pytest.mark.parametrize("requested_role", ["admin", "coach"])
def test_public_registration_cannot_grant_privileged_role(
    context, requested_role
):
    response = context["api"].post(
        "/api/v1/auth/register",
        json={
            "email": f"public.{requested_role}@example.com",
            "password": "ClavePublica123!",
            "role": requested_role,
        },
    )

    # Es válido rechazar el campo extra o ignorarlo.
    if response.status_code == 201:
        assert response.json()["role"] == "client"
    else:
        assert response.status_code == 422


@pytest.mark.parametrize(
    "actor",
    [None, "client", "coach"],
)
def test_admin_operations_require_admin(context, actor):
    api = context["api"]
    headers = {} if actor is None else context["headers"][actor]
    expected = 401 if actor is None else 403
    client_id = context["ids"]["client"]

    operations = [
        (
            "POST",
            "/api/v1/admin/coaches",
            {
                "email": "blocked@example.com",
                "password": "ClaveCoach123!",
            },
        ),
        ("GET", "/api/v1/admin/coaches", None),
        ("GET", "/api/v1/admin/clients", None),
        (
            "PUT",
            f"/api/v1/admin/clients/{client_id}/coach",
            {"coach_id": context["ids"]["coach"]},
        ),
        (
            "GET",
            f"/api/v1/admin/clients/{client_id}/coach",
            None,
        ),
    ]

    for method, path, payload in operations:
        response = api.request(
            method,
            path,
            headers=headers,
            json=payload,
        )
        assert response.status_code == expected, response.text


def test_admin_lists_users_by_role(context):
    api = context["api"]
    headers = context["headers"]["admin"]

    coaches = api.get(
        "/api/v1/admin/coaches", headers=headers
    )
    clients = api.get(
        "/api/v1/admin/clients", headers=headers
    )

    assert coaches.status_code == 200
    assert clients.status_code == 200

    assert {row["id"] for row in coaches.json()} == {
        context["ids"]["coach"],
        context["ids"]["other_coach"],
    }
    assert {row["id"] for row in clients.json()} == {
        context["ids"]["client"],
        context["ids"]["other_client"],
    }


def test_assignment_can_be_created_and_consulted(context):
    created = assign(context)
    assert created.status_code == 200, created.text

    client_id = context["ids"]["client"]
    fetched = context["api"].get(
        f"/api/v1/admin/clients/{client_id}/coach",
        headers=context["headers"]["admin"],
    )

    assert fetched.status_code == 200
    assert fetched.json()["client_id"] == client_id
    assert fetched.json()["coach_id"] == context["ids"]["coach"]


@pytest.mark.parametrize("missing", ["client", "coach"])
def test_assignment_rejects_nonexistent_users(context, missing):
    client_id = context["ids"]["client"]
    coach_id = context["ids"]["coach"]

    if missing == "client":
        client_id = 999999
    else:
        coach_id = 999999

    response = context["api"].put(
        f"/api/v1/admin/clients/{client_id}/coach",
        headers=context["headers"]["admin"],
        json={"coach_id": coach_id},
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("client_name", "coach_name"),
    [
        ("coach", "other_coach"),
        ("client", "other_client"),
        ("client", "admin"),
        ("client", "client"),
    ],
)
def test_assignment_rejects_invalid_roles(
    context, client_name, coach_name
):
    response = assign(
        context,
        coach_name=coach_name,
        client_name=client_name,
    )
    assert response.status_code == 422


@pytest.mark.parametrize("inactive", ["client", "coach"])
def test_assignment_rejects_inactive_accounts(context, inactive):
    with context["sessions"]() as db:
        user = db.get(User, context["ids"][inactive])
        user.is_active = False
        db.commit()

    response = assign(context)
    assert response.status_code == 422


def test_coach_only_lists_assigned_clients(context):
    assert assign(context).status_code == 200

    api = context["api"]
    result = api.get(
        "/api/v1/coach/clients",
        headers=context["headers"]["coach"],
    )
    other_result = api.get(
        "/api/v1/coach/clients",
        headers=context["headers"]["other_coach"],
    )

    assert result.status_code == 200
    assert [row["id"] for row in result.json()] == [
        context["ids"]["client"]
    ]
    assert other_result.status_code == 200
    assert other_result.json() == []


def test_coach_reads_assigned_profile_and_assessments(context):
    assert assign(context).status_code == 200
    assert create_profile(context).status_code == 201

    api = context["api"]
    measurement = api.post(
        "/api/v1/client-profile/me/assessments",
        headers=context["headers"]["client"],
        json={"weight_kg": "75.50"},
    )
    assert measurement.status_code == 201

    client_id = context["ids"]["client"]
    headers = context["headers"]["coach"]

    profile = api.get(
        f"/api/v1/coach/clients/{client_id}/profile",
        headers=headers,
    )
    history = api.get(
        f"/api/v1/coach/clients/{client_id}/assessments",
        headers=headers,
    )

    assert profile.status_code == 200, profile.text
    assert profile.json()["user_id"] == client_id
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["id"] == measurement.json()["id"]


def test_other_coach_cannot_read_client_data(context):
    assert assign(context).status_code == 200
    assert create_profile(context).status_code == 201

    client_id = context["ids"]["client"]

    for resource in ["profile", "assessments"]:
        response = context["api"].get(
            f"/api/v1/coach/clients/{client_id}/{resource}",
            headers=context["headers"]["other_coach"],
        )
        assert response.status_code == 404


def test_missing_profile_returns_404(context):
    assert assign(context).status_code == 200
    client_id = context["ids"]["client"]

    for resource in ["profile", "assessments"]:
        response = context["api"].get(
            f"/api/v1/coach/clients/{client_id}/{resource}",
            headers=context["headers"]["coach"],
        )
        assert response.status_code == 404


def test_reassignment_transfers_access(context):
    first = assign(context)
    assert first.status_code == 200
    assert create_profile(context).status_code == 201

    reassigned = assign(context, coach_name="other_coach")
    assert reassigned.status_code == 200
    assert reassigned.json()["id"] == first.json()["id"]

    client_id = context["ids"]["client"]

    for resource in ["profile", "assessments"]:
        path = f"/api/v1/coach/clients/{client_id}/{resource}"

        previous_coach = context["api"].get(
            path, headers=context["headers"]["coach"]
        )
        new_coach = context["api"].get(
            path, headers=context["headers"]["other_coach"]
        )

        assert previous_coach.status_code == 404
        assert new_coach.status_code == 200


@pytest.mark.parametrize("actor", [None, "admin", "client"])
def test_coach_operations_require_coach_role(context, actor):
    client_id = context["ids"]["client"]
    headers = {} if actor is None else context["headers"][actor]
    expected = 401 if actor is None else 403

    paths = [
        "/api/v1/coach/clients",
        f"/api/v1/coach/clients/{client_id}/profile",
        f"/api/v1/coach/clients/{client_id}/assessments",
    ]

    for path in paths:
        response = context["api"].get(path, headers=headers)
        assert response.status_code == expected


def test_inactive_coach_cannot_access(context):
    with context["sessions"]() as db:
        coach = db.get(User, context["ids"]["coach"])
        coach.is_active = False
        db.commit()

    response = context["api"].get(
        "/api/v1/coach/clients",
        headers=context["headers"]["coach"],
    )

    assert response.status_code == 401