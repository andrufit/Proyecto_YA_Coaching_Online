from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.coach_assignment import CoachAssignment
from app.models.nutrition_plan import (
    NutritionFood,
    NutritionMeal,
    NutritionPlan,
)
from app.schemas.nutrition_plan import NutritionPlanWrite
from app.services.coach_service import (
    CoachClientNotFoundError,
    get_assigned_client,
)


class NutritionPlanNotFoundError(Exception):
    """El cliente todavía no tiene un plan nutricional."""


class NutritionPlanConflictError(Exception):
    """No fue posible guardar el plan nutricional."""


def get_nutrition_plan(
    db: Session,
    client_id: int,
) -> NutritionPlan:
    # La autorización se comprueba antes de llamar a esta función.
    statement = (
        select(NutritionPlan)
        .where(NutritionPlan.client_id == client_id)
        .options(
            selectinload(NutritionPlan.meals).selectinload(
                NutritionMeal.foods
            )
        )
    )

    plan = db.scalar(statement)

    if plan is None:
        raise NutritionPlanNotFoundError(
            "El cliente todavía no tiene un plan nutricional."
        )

    return plan


def get_coach_nutrition_plan(
    db: Session,
    coach_id: int,
    client_id: int,
) -> NutritionPlan:
    get_assigned_client(
        db,
        coach_id=coach_id,
        client_id=client_id,
    )

    return get_nutrition_plan(db, client_id)


def build_nutrition_meals(
    plan_data: NutritionPlanWrite,
) -> list[NutritionMeal]:
    meals = []

    for meal_data in sorted(
        plan_data.meals,
        key=lambda item: item.position,
    ):
        foods = [
            NutritionFood(
                position=food_data.position,
                name=food_data.name,
                quantity=food_data.quantity,
                notes=food_data.notes,
            )
            for food_data in sorted(
                meal_data.foods,
                key=lambda item: item.position,
            )
        ]

        meal = NutritionMeal(
            position=meal_data.position,
            name=meal_data.name,
            notes=meal_data.notes,
            foods=foods,
        )

        meals.append(meal)

    return meals


def save_coach_nutrition_plan(
    db: Session,
    coach_id: int,
    client_id: int,
    plan_data: NutritionPlanWrite,
) -> NutritionPlan:
    try:
        # En PostgreSQL bloquea la asignación durante el guardado.
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

        # También comprueba que sea un cliente activo.
        get_assigned_client(
            db,
            coach_id=coach_id,
            client_id=client_id,
        )

        statement = (
            select(NutritionPlan)
            .where(NutritionPlan.client_id == client_id)
            .options(
                selectinload(NutritionPlan.meals).selectinload(
                    NutritionMeal.foods
                )
            )
        )

        plan = db.scalar(statement)

        if plan is None:
            plan = NutritionPlan(
                client_id=client_id,
                title=plan_data.title,
                instructions=plan_data.instructions,
            )
            db.add(plan)
        else:
            plan.title = plan_data.title
            plan.instructions = plan_data.instructions

            # Elimina las comidas anteriores antes de reutilizar
            # sus posiciones. Todo sigue en la misma transacción.
            plan.meals.clear()
            db.flush()

        plan.meals = build_nutrition_meals(plan_data)
        plan.updated_at = datetime.now(timezone.utc)

        db.commit()

    except IntegrityError as error:
        db.rollback()
        raise NutritionPlanConflictError(
            "No fue posible guardar el plan nutricional. "
            "Recarga la información e inténtalo nuevamente."
        ) from error

    except Exception:
        db.rollback()
        raise

    return plan