from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.body_assessment import BodyAssessment
from app.models.client_profile import ClientProfile
from app.models.coach_assignment import CoachAssignment
from app.models.user import User


class CoachClientNotFoundError(Exception):
    """El cliente no está disponible para este entrenador."""


class ClientProfileNotFoundError(Exception):
    """El cliente asignado todavía no tiene perfil."""


def list_assigned_clients(
    db: Session,
    coach_id: int,
    offset: int = 0,
    limit: int = 50,
) -> list[User]:
    statement = (
        select(User)
        .join(
            CoachAssignment,
            CoachAssignment.client_id == User.id,
        )
        .where(
            CoachAssignment.coach_id == coach_id,
            User.role == "client",
            User.is_active.is_(True),
        )
        .order_by(User.id)
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def get_assigned_client(
    db: Session,
    coach_id: int,
    client_id: int,
) -> User:
    statement = (
        select(User)
        .join(
            CoachAssignment,
            CoachAssignment.client_id == User.id,
        )
        .where(
            CoachAssignment.coach_id == coach_id,
            User.id == client_id,
            User.role == "client",
            User.is_active.is_(True),
        )
    )

    client = db.scalar(statement)

    if client is None:
        raise CoachClientNotFoundError(
            "El cliente no existe o no está disponible "
            "entre tus clientes asignados."
        )

    return client


def get_assigned_client_profile(
    db: Session,
    coach_id: int,
    client_id: int,
) -> ClientProfile:
    get_assigned_client(db, coach_id, client_id)

    statement = select(ClientProfile).where(
        ClientProfile.user_id == client_id
    )
    profile = db.scalar(statement)

    if profile is None:
        raise ClientProfileNotFoundError(
            "El cliente asignado todavía no ha completado su perfil."
        )

    return profile


def list_assigned_client_assessments(
    db: Session,
    coach_id: int,
    client_id: int,
    offset: int = 0,
    limit: int = 50,
) -> list[BodyAssessment]:
    profile = get_assigned_client_profile(
        db,
        coach_id,
        client_id,
    )

    statement = (
        select(BodyAssessment)
        .where(
            BodyAssessment.client_profile_id == profile.id
        )
        .order_by(
            BodyAssessment.assessment_date.desc(),
            BodyAssessment.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).all())