from typing import Annotated

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    status,
)

from app.api.dependencies import (
    CurrentUserDependency,
    SessionDependency,
)
from app.api.v1.coach import CoachDependency
from app.models.training_plan import TrainingPlan
from app.schemas.training_plan import (
    TrainingPlanRead,
    TrainingPlanWrite,
)
from app.services.coach_service import (
    CoachClientNotFoundError,
)
from app.services.training_plan_service import (
    TrainingPlanConflictError,
    TrainingPlanNotFoundError,
    get_coach_training_plan,
    get_training_plan,
    save_coach_training_plan,
)


router = APIRouter(
    tags=["Training plans"],
)


@router.get(
    "/coach/clients/{client_id}/training-plan",
    response_model=TrainingPlanRead,
)
def read_client_training_plan(
    client_id: Annotated[int, Path(gt=0)],
    db: SessionDependency,
    coach: CoachDependency,
) -> TrainingPlan:
    try:
        return get_coach_training_plan(
            db,
            coach_id=coach.id,
            client_id=client_id,
        )

    except (
        CoachClientNotFoundError,
        TrainingPlanNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.put(
    "/coach/clients/{client_id}/training-plan",
    response_model=TrainingPlanRead,
    status_code=status.HTTP_200_OK,
)
def write_client_training_plan(
    client_id: Annotated[int, Path(gt=0)],
    plan_data: TrainingPlanWrite,
    db: SessionDependency,
    coach: CoachDependency,
) -> TrainingPlan:
    try:
        return save_coach_training_plan(
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

    except TrainingPlanConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "/users/me/training-plan",
    response_model=TrainingPlanRead,
)
def read_my_training_plan(
    db: SessionDependency,
    current_user: CurrentUserDependency,
) -> TrainingPlan:
    if current_user.role != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Esta operación requiere "
                "una cuenta de cliente."
            ),
        )

    try:
        return get_training_plan(
            db,
            client_id=current_user.id,
        )

    except TrainingPlanNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todavía no tienes un plan de entrenamiento.",
        ) from error