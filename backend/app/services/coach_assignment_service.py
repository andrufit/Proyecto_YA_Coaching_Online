from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.coach_assignment import CoachAssignment
from app.models.user import User


class AssignmentUserNotFoundError(Exception):
    """El cliente o entrenador solicitado no existe."""


class InvalidAssignmentError(Exception):
    """La asignación no cumple las reglas del sistema."""


class AssignmentConflictError(Exception):
    """La asignación cambió durante la operación."""


def assign_coach(
    db: Session,
    client_id: int,
    coach_id: int,
) -> CoachAssignment:
    client = db.get(User, client_id)
    coach = db.get(User, coach_id)

    if client is None:
        raise AssignmentUserNotFoundError(
            "No existe el cliente indicado."
        )

    if coach is None:
        raise AssignmentUserNotFoundError(
            "No existe el entrenador indicado."
        )

    if client.role != "client":
        raise InvalidAssignmentError(
            "El usuario seleccionado no tiene rol client."
        )

    if coach.role != "coach":
        raise InvalidAssignmentError(
            "El usuario seleccionado no tiene rol coach."
        )

    if not client.is_active:
        raise InvalidAssignmentError(
            "El cliente está desactivado."
        )

    if not coach.is_active:
        raise InvalidAssignmentError(
            "El entrenador está desactivado."
        )

    statement = select(CoachAssignment).where(
        CoachAssignment.client_id == client_id
    )
    assignment = db.scalar(statement)

    if assignment is None:
        assignment = CoachAssignment(
            client_id=client_id,
            coach_id=coach_id,
        )
        db.add(assignment)
    else:
        assignment.coach_id = coach_id

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise AssignmentConflictError(
            "No se pudo guardar la asignación. "
            "Consulta su estado e intenta nuevamente."
        ) from error

    db.refresh(assignment)
    return assignment


def get_client_assignment(
    db: Session,
    client_id: int,
) -> CoachAssignment | None:
    statement = select(CoachAssignment).where(
        CoachAssignment.client_id == client_id
    )
    return db.scalar(statement)


def list_clients(
    db: Session,
    offset: int = 0,
    limit: int = 50,
) -> list[User]:
    statement = (
        select(User)
        .where(User.role == "client")
        .order_by(User.id)
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).all())