from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.coach_assignment import CoachAssignment
from app.models.training_plan import (
    TrainingDay,
    TrainingExercise,
    TrainingPlan,
)
from app.schemas.training_plan import TrainingPlanWrite
from app.services.coach_service import (
    CoachClientNotFoundError,
    get_assigned_client,
)


class TrainingPlanNotFoundError(Exception):
    """El cliente todavía no tiene un plan de entrenamiento."""


class TrainingPlanConflictError(Exception):
    """No fue posible guardar el plan por un conflicto de datos."""


def get_training_plan(
    db: Session,
    client_id: int,
) -> TrainingPlan:
    statement = (
        select(TrainingPlan)
        .where(TrainingPlan.client_id == client_id)
        .options(
            selectinload(TrainingPlan.days)
            .selectinload(TrainingDay.exercises)
        )
    )

    plan = db.scalar(statement)

    if plan is None:
        raise TrainingPlanNotFoundError(
            "El cliente todavía no tiene un plan "
            "de entrenamiento."
        )

    return plan


def get_coach_training_plan(
    db: Session,
    coach_id: int,
    client_id: int,
) -> TrainingPlan:
    get_assigned_client(
        db,
        coach_id=coach_id,
        client_id=client_id,
    )

    return get_training_plan(
        db,
        client_id=client_id,
    )


def build_training_days(
    plan_data: TrainingPlanWrite,
) -> list[TrainingDay]:
    days = []

    for day_data in plan_data.days:
        day = TrainingDay(
            position=day_data.position,
            name=day_data.name,
        )

        day.exercises = [
            TrainingExercise(
                position=exercise.position,
                name=exercise.name,
                sets=exercise.sets,
                repetitions=exercise.repetitions,
                rest_seconds=exercise.rest_seconds,
                notes=exercise.notes,
            )
            for exercise in day_data.exercises
        ]

        days.append(day)

    return days


def save_coach_training_plan(
    db: Session,
    coach_id: int,
    client_id: int,
    plan_data: TrainingPlanWrite,
) -> TrainingPlan:
    try:
        assignment_statement = (
            select(CoachAssignment)
            .where(
                CoachAssignment.client_id == client_id,
                CoachAssignment.coach_id == coach_id,
            )
            .with_for_update()
        )

        assignment = db.scalar(assignment_statement)

        if assignment is None:
            raise CoachClientNotFoundError(
                "El cliente no existe o no está disponible "
                "entre tus clientes asignados."
            )

        get_assigned_client(
            db,
            coach_id=coach_id,
            client_id=client_id,
        )

        statement = (
            select(TrainingPlan)
            .where(
                TrainingPlan.client_id == client_id,
            )
            .options(
                selectinload(TrainingPlan.days)
                .selectinload(TrainingDay.exercises)
            )
        )

        plan = db.scalar(statement)

        if plan is None:
            plan = TrainingPlan(
                client_id=client_id,
                title=plan_data.title,
                instructions=plan_data.instructions,
            )

            db.add(plan)
        else:
            plan.title = plan_data.title
            plan.instructions = plan_data.instructions

            plan.days.clear()

            # Elimina los días anteriores antes de insertar
            # otros con las mismas posiciones.
            # Todavía no confirma la transacción.
            db.flush()

        plan.days = build_training_days(plan_data)

        # También cambia cuando solo se modifican ejercicios.
        plan.updated_at = datetime.now(timezone.utc)

        db.commit()

    except IntegrityError as error:
        db.rollback()

        raise TrainingPlanConflictError(
            "No fue posible guardar el plan. "
            "Recarga la información e inténtalo nuevamente."
        ) from error

    except Exception:
        db.rollback()
        raise

    return plan