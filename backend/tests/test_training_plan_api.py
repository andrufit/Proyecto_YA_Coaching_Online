from collections.abc import Generator
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core.database import Base
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import (
    TrainingDay,
    TrainingExercise,
    TrainingPlan,
    User,
)


@pytest.fixture
def context() -> Generator[dict, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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


def plan_payload():
    return {
        "title": "Plan de prueba",
        "instructions": "Indicaciones generales.",
        "days": [
            {
                "position": 1,
                "name": "Día uno",
                "exercises": [
                    {
                        "position": 1,
                        "name": "Sentadilla",
                        "sets": 3,
                        "repetitions": "10",
                        "rest_seconds": 90,
                        "notes": None,
                    },
                    {
                        "position": 2,
                        "name": "Curl femoral",
                        "sets": 3,
                        "repetitions": "12",
                        "rest_seconds": 60,
                        "notes": "Ejercicio de prueba.",
                    },
                ],
            }
        ],
    }


def coach_path(context, client_name="client"):
    client_id = context["ids"][client_name]
    return (
        f"/api/v1/coach/clients/{client_id}/training-plan"
    )


def assign(context, coach_name="coach"):
    client_id = context["ids"]["client"]

    response = context["api"].put(
        f"/api/v1/admin/clients/{client_id}/coach",
        headers=context["headers"]["admin"],
        json={"coach_id": context["ids"][coach_name]},
    )

    assert response.status_code == 200, response.text


def save_plan(context, payload=None, coach_name="coach"):
    if payload is None:
        payload = plan_payload()

    return context["api"].put(
        coach_path(context),
        headers=context["headers"][coach_name],
        json=payload,
    )


def create_plan(context):
    assign(context)
    response = save_plan(context)

    assert response.status_code == 200, response.text
    return response.json()


def test_coach_creates_and_client_reads_plan(context):
    created = create_plan(context)

    assert created["client_id"] == context["ids"]["client"]
    assert created["title"] == "Plan de prueba"
    assert len(created["days"]) == 1
    assert len(created["days"][0]["exercises"]) == 2

    coach_response = context["api"].get(
        coach_path(context),
        headers=context["headers"]["coach"],
    )

    client_response = context["api"].get(
        "/api/v1/users/me/training-plan",
        headers=context["headers"]["client"],
    )

    assert coach_response.status_code == 200
    assert client_response.status_code == 200
    assert coach_response.json() == created
    assert client_response.json() == created


def test_update_replaces_days_and_exercises(context):
    original = create_plan(context)
    payload = plan_payload()

    payload["title"] = "Plan actualizado"
    payload["instructions"] = None
    payload["days"][0]["name"] = "Día modificado"
    payload["days"][0]["exercises"] = [
        {
            "position": 1,
            "name": "Remo en polea",
            "sets": 4,
            "repetitions": "8-10",
            "rest_seconds": 120,
            "notes": None,
        }
    ]

    response = save_plan(context, payload)
    assert response.status_code == 200, response.text

    updated = response.json()

    assert updated["id"] == original["id"]
    assert updated["title"] == "Plan actualizado"
    assert updated["instructions"] is None

    fetched = context["api"].get(
        "/api/v1/users/me/training-plan",
        headers=context["headers"]["client"],
    )

    assert fetched.status_code == 200
    exercises = fetched.json()["days"][0]["exercises"]
    assert len(exercises) == 1
    assert exercises[0]["name"] == "Remo en polea"
    assert exercises[0]["sets"] == 4

    # No deben quedar días ni ejercicios anteriores.
    with context["sessions"]() as db:
        assert db.scalar(
            select(func.count()).select_from(TrainingPlan)
        ) == 1

        assert db.scalar(
            select(func.count()).select_from(TrainingDay)
        ) == 1

        assert db.scalar(
            select(func.count()).select_from(TrainingExercise)
        ) == 1


def test_missing_plan_returns_404(context):
    assign(context)

    coach_response = context["api"].get(
        coach_path(context),
        headers=context["headers"]["coach"],
    )

    client_response = context["api"].get(
        "/api/v1/users/me/training-plan",
        headers=context["headers"]["client"],
    )

    assert coach_response.status_code == 404
    assert client_response.status_code == 404


def test_unassigned_coach_cannot_create_plan(context):
    response = save_plan(context)
    assert response.status_code == 404

    with context["sessions"]() as db:
        assert db.scalar(
            select(func.count()).select_from(TrainingPlan)
        ) == 0


def test_other_coach_cannot_read_or_modify_plan(context):
    original = create_plan(context)

    response = context["api"].get(
        coach_path(context),
        headers=context["headers"]["other_coach"],
    )
    assert response.status_code == 404

    payload = plan_payload()
    payload["title"] = "Cambio no autorizado"

    response = save_plan(
        context,
        payload,
        coach_name="other_coach",
    )
    assert response.status_code == 404

    fetched = context["api"].get(
        "/api/v1/users/me/training-plan",
        headers=context["headers"]["client"],
    )
    assert fetched.json() == original


def test_other_client_cannot_access_plan(context):
    create_plan(context)

    own_response = context["api"].get(
        "/api/v1/users/me/training-plan",
        headers=context["headers"]["other_client"],
    )
    assert own_response.status_code == 404

    targeted_response = context["api"].get(
        coach_path(context),
        headers=context["headers"]["other_client"],
    )
    assert targeted_response.status_code == 403


@pytest.mark.parametrize("actor", [None, "admin", "client"])
def test_coach_routes_require_coach_role(context, actor):
    create_plan(context)

    headers = (
        {} if actor is None else context["headers"][actor]
    )
    expected = 401 if actor is None else 403

    read_response = context["api"].get(
        coach_path(context),
        headers=headers,
    )

    write_response = context["api"].put(
        coach_path(context),
        headers=headers,
        json=plan_payload(),
    )

    assert read_response.status_code == expected
    assert write_response.status_code == expected


@pytest.mark.parametrize("actor", [None, "admin", "coach"])
def test_client_route_requires_client_role(context, actor):
    headers = (
        {} if actor is None else context["headers"][actor]
    )
    expected = 401 if actor is None else 403

    response = context["api"].get(
        "/api/v1/users/me/training-plan",
        headers=headers,
    )

    assert response.status_code == expected


def test_reassignment_transfers_plan_access(context):
    original = create_plan(context)
    assign(context, coach_name="other_coach")

    old_coach = context["api"].get(
        coach_path(context),
        headers=context["headers"]["coach"],
    )
    assert old_coach.status_code == 404

    blocked_write = save_plan(context)
    assert blocked_write.status_code == 404

    new_coach = context["api"].get(
        coach_path(context),
        headers=context["headers"]["other_coach"],
    )
    assert new_coach.status_code == 200
    assert new_coach.json()["id"] == original["id"]

    payload = plan_payload()
    payload["title"] = "Plan del nuevo entrenador"

    updated = save_plan(
        context,
        payload,
        coach_name="other_coach",
    )

    assert updated.status_code == 200, updated.text
    assert updated.json()["id"] == original["id"]

    client_response = context["api"].get(
        "/api/v1/users/me/training-plan",
        headers=context["headers"]["client"],
    )
    assert client_response.status_code == 200
    assert (
        client_response.json()["title"]
        == "Plan del nuevo entrenador"
    )


@pytest.mark.parametrize("actor", ["coach", "client"])
def test_inactive_accounts_cannot_access_plan(context, actor):
    create_plan(context)

    with context["sessions"]() as db:
        user = db.get(User, context["ids"][actor])
        user.is_active = False
        db.commit()

    if actor == "coach":
        response = context["api"].get(
            coach_path(context),
            headers=context["headers"]["coach"],
        )
        assert response.status_code == 401

        response = save_plan(context)
        assert response.status_code == 401

    else:
        response = context["api"].get(
            "/api/v1/users/me/training-plan",
            headers=context["headers"]["client"],
        )
        assert response.status_code == 401

        response = context["api"].get(
            coach_path(context),
            headers=context["headers"]["coach"],
        )
        assert response.status_code == 404

        response = save_plan(context)
        assert response.status_code == 404


@pytest.mark.parametrize(
    "case",
    [
        "blank_title",
        "empty_days",
        "duplicate_days",
        "empty_exercises",
        "duplicate_exercises",
        "blank_exercise",
        "invalid_sets",
        "invalid_rest",
        "blank_repetitions",
        "extra_client_id",
    ],
)
def test_invalid_update_preserves_saved_plan(context, case):
    original = create_plan(context)
    payload = plan_payload()
    day = payload["days"][0]
    exercise = day["exercises"][0]

    if case == "blank_title":
        payload["title"] = "   "
    elif case == "empty_days":
        payload["days"] = []
    elif case == "duplicate_days":
        payload["days"].append(deepcopy(day))
    elif case == "empty_exercises":
        day["exercises"] = []
    elif case == "duplicate_exercises":
        day["exercises"].append(deepcopy(exercise))
    elif case == "blank_exercise":
        exercise["name"] = "   "
    elif case == "invalid_sets":
        exercise["sets"] = 0
    elif case == "invalid_rest":
        exercise["rest_seconds"] = -1
    elif case == "blank_repetitions":
        exercise["repetitions"] = "   "
    elif case == "extra_client_id":
        payload["client_id"] = context["ids"]["other_client"]

    response = save_plan(context, payload)
    assert response.status_code == 422, response.text

    fetched = context["api"].get(
        "/api/v1/users/me/training-plan",
        headers=context["headers"]["client"],
    )

    assert fetched.status_code == 200
    assert fetched.json() == original