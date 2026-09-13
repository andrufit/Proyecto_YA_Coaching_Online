from collections.abc import Generator
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core.database import Base
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import CoachAssignment, User


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

            db.flush()

            ids = {
                name: user.id
                for name, user in users.items()
            }

            db.add(
                CoachAssignment(
                    client_id=ids["client"],
                    coach_id=ids["coach"],
                )
            )
            db.commit()

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
        "title": "Plan nutricional de prueba",
        "instructions": "Indicaciones de prueba.",
        "meals": [
            {
                "position": 1,
                "name": "Desayuno",
                "notes": None,
                "foods": [
                    {
                        "position": 1,
                        "name": "Avena",
                        "quantity": "50 g",
                        "notes": "Peso en seco",
                    },
                    {
                        "position": 2,
                        "name": "Huevos",
                        "quantity": "2 unidades",
                        "notes": None,
                    },
                ],
            }
        ],
    }


def coach_path(context, client_name="client"):
    client_id = context["ids"][client_name]
    return f"/api/v1/coach/clients/{client_id}/nutrition-plan"


def save_plan(context, payload=None, actor="coach"):
    return context["api"].put(
        coach_path(context),
        headers=context["headers"][actor],
        json=plan_payload() if payload is None else payload,
    )


def create_plan(context):
    response = save_plan(context)
    assert response.status_code == 200, response.text
    return response.json()


def read_client_plan(context, actor="client"):
    return context["api"].get(
        "/api/v1/users/me/nutrition-plan",
        headers=context["headers"][actor],
    )


def test_coach_creates_and_client_reads_plan(context):
    created = create_plan(context)

    assert created["client_id"] == context["ids"]["client"]
    assert len(created["meals"]) == 1
    assert len(created["meals"][0]["foods"]) == 2

    coach_response = context["api"].get(
        coach_path(context),
        headers=context["headers"]["coach"],
    )
    client_response = read_client_plan(context)

    assert coach_response.status_code == 200
    assert client_response.status_code == 200
    assert coach_response.json() == created
    assert client_response.json() == created


def test_update_replaces_meals_and_preserves_plan_id(context):
    original = create_plan(context)
    payload = plan_payload()

    payload["title"] = "Plan actualizado"
    payload["meals"][0]["name"] = "Cena"
    payload["meals"][0]["foods"] = [
        {
            "position": 1,
            "name": "Arroz",
            "quantity": "120 g",
            "notes": None,
        }
    ]

    updated = save_plan(context, payload)
    assert updated.status_code == 200, updated.text

    saved = updated.json()
    assert saved["id"] == original["id"]
    assert saved["created_at"] == original["created_at"]
    assert saved["title"] == "Plan actualizado"
    assert saved["meals"][0]["name"] == "Cena"
    assert len(saved["meals"][0]["foods"]) == 1
    assert saved["meals"][0]["foods"][0]["name"] == "Arroz"

    fetched = read_client_plan(context)
    assert fetched.status_code == 200
    assert fetched.json() == saved


def test_missing_plan_returns_404(context):
    response = read_client_plan(context)
    assert response.status_code == 404

    response = context["api"].get(
        coach_path(context),
        headers=context["headers"]["coach"],
    )
    assert response.status_code == 404


def test_other_coach_cannot_read_or_modify_plan(context):
    original = create_plan(context)

    response = context["api"].get(
        coach_path(context),
        headers=context["headers"]["other_coach"],
    )
    assert response.status_code == 404

    payload = plan_payload()
    payload["title"] = "Cambio no autorizado"

    response = save_plan(context, payload, actor="other_coach")
    assert response.status_code == 404

    fetched = read_client_plan(context)
    assert fetched.status_code == 200
    assert fetched.json() == original


def test_coach_cannot_create_plan_for_unassigned_client(context):
    response = context["api"].put(
        coach_path(context, client_name="other_client"),
        headers=context["headers"]["coach"],
        json=plan_payload(),
    )
    assert response.status_code == 404

    response = read_client_plan(context, actor="other_client")
    assert response.status_code == 404


def test_other_client_does_not_receive_saved_plan(context):
    create_plan(context)

    response = read_client_plan(context, actor="other_client")
    assert response.status_code == 404


@pytest.mark.parametrize("actor", [None, "admin", "client"])
def test_coach_routes_require_coach_role(context, actor):
    headers = {} if actor is None else context["headers"][actor]
    expected = 401 if actor is None else 403

    for method in ["GET", "PUT"]:
        response = context["api"].request(
            method,
            coach_path(context),
            headers=headers,
            json=plan_payload() if method == "PUT" else None,
        )
        assert response.status_code == expected, response.text


@pytest.mark.parametrize("actor", [None, "admin", "coach"])
def test_client_route_requires_client_role(context, actor):
    headers = {} if actor is None else context["headers"][actor]
    expected = 401 if actor is None else 403

    response = context["api"].get(
        "/api/v1/users/me/nutrition-plan",
        headers=headers,
    )
    assert response.status_code == expected


@pytest.mark.parametrize("actor", ["coach", "client"])
def test_inactive_account_cannot_access(context, actor):
    create_plan(context)

    with context["sessions"]() as db:
        user = db.get(User, context["ids"][actor])
        user.is_active = False
        db.commit()

    path = (
        coach_path(context)
        if actor == "coach"
        else "/api/v1/users/me/nutrition-plan"
    )

    response = context["api"].get(
        path,
        headers=context["headers"][actor],
    )
    assert response.status_code == 401


def test_reassignment_transfers_access(context):
    original = create_plan(context)
    client_id = context["ids"]["client"]

    reassigned = context["api"].put(
        f"/api/v1/admin/clients/{client_id}/coach",
        headers=context["headers"]["admin"],
        json={"coach_id": context["ids"]["other_coach"]},
    )
    assert reassigned.status_code == 200, reassigned.text

    previous_coach = context["api"].get(
        coach_path(context),
        headers=context["headers"]["coach"],
    )
    assert previous_coach.status_code == 404

    blocked_update = save_plan(context)
    assert blocked_update.status_code == 404

    new_coach = context["api"].get(
        coach_path(context),
        headers=context["headers"]["other_coach"],
    )
    assert new_coach.status_code == 200
    assert new_coach.json() == original

    payload = plan_payload()
    payload["title"] = "Plan del nuevo entrenador"

    updated = save_plan(context, payload, actor="other_coach")
    assert updated.status_code == 200
    assert updated.json()["id"] == original["id"]

    fetched = read_client_plan(context)
    assert fetched.status_code == 200
    assert fetched.json() == updated.json()


@pytest.mark.parametrize(
    "case",
    [
        "blank_title",
        "empty_meals",
        "duplicate_meals",
        "blank_meal",
        "empty_foods",
        "duplicate_foods",
        "blank_food",
        "blank_quantity",
        "invalid_meal_position",
        "invalid_food_position",
        "extra_client_id",
    ],
)
def test_invalid_update_preserves_saved_plan(context, case):
    original = create_plan(context)
    payload = plan_payload()
    meal = payload["meals"][0]
    food = meal["foods"][0]

    if case == "blank_title":
        payload["title"] = "   "
    elif case == "empty_meals":
        payload["meals"] = []
    elif case == "duplicate_meals":
        payload["meals"].append(deepcopy(meal))
    elif case == "blank_meal":
        meal["name"] = "   "
    elif case == "empty_foods":
        meal["foods"] = []
    elif case == "duplicate_foods":
        meal["foods"].append(deepcopy(food))
    elif case == "blank_food":
        food["name"] = "   "
    elif case == "blank_quantity":
        food["quantity"] = "   "
    elif case == "invalid_meal_position":
        meal["position"] = 11
    elif case == "invalid_food_position":
        food["position"] = 31
    elif case == "extra_client_id":
        payload["client_id"] = context["ids"]["other_client"]

    response = save_plan(context, payload)
    assert response.status_code == 422, response.text

    fetched = read_client_plan(context)
    assert fetched.status_code == 200
    assert fetched.json() == original