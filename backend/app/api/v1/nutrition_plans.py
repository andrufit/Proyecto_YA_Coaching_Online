from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from app.api.dependencies import (
    CurrentUserDependency,
    SessionDependency,
)
from app.api.v1.coach import CoachDependency
from app.models.nutrition_plan import NutritionPlan
from app.schemas.nutrition_plan import (
    NutritionPlanRead,
    NutritionPlanWrite,
)
from app.services.coach_service import CoachClientNotFoundError
from app.services.nutrition_plan_service import (
    NutritionPlanConflictError,
    NutritionPlanNotFoundError,
    get_coach_nutrition_plan,
    get_nutrition_plan,
    save_coach_nutrition_plan,
)

router = APIRouter(
    tags=["Nutrition plans"],
)


@router.get(
    "/coach/clients/{client_id}/nutrition-plan",
    response_model=NutritionPlanRead,
)
def read_client_nutrition_plan(
    client_id: Annotated[int, Path(gt=0)],
    db: SessionDependency,
    coach: CoachDependency,
) -> NutritionPlan:
    try:
        return get_coach_nutrition_plan(
            db,
            coach_id=coach.id,
            client_id=client_id,
        )
    except (
        CoachClientNotFoundError,
        NutritionPlanNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.put(
    "/coach/clients/{client_id}/nutrition-plan",
    response_model=NutritionPlanRead,
    status_code=status.HTTP_200_OK,
)
def write_client_nutrition_plan(
    client_id: Annotated[int, Path(gt=0)],
    plan_data: NutritionPlanWrite,
    db: SessionDependency,
    coach: CoachDependency,
) -> NutritionPlan:
    try:
        return save_coach_nutrition_plan(
            db,
            coach_id=coach.id,
            client_id=client_id,
            plan_data=plan_data,
        )
    except CoachClientNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except NutritionPlanConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "/users/me/nutrition-plan",
    response_model=NutritionPlanRead,
)
def read_my_nutrition_plan(
    db: SessionDependency,
    current_user: CurrentUserDependency,
) -> NutritionPlan:
    if current_user.role != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operación requiere una cuenta de cliente.",
        )

    try:
        return get_nutrition_plan(
            db,
            client_id=current_user.id,
        )
    except NutritionPlanNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todavía no tienes un plan nutricional.",
        ) from error