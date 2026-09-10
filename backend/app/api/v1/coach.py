from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)

from app.api.dependencies import (
    CurrentUserDependency,
    SessionDependency,
)
from app.models.body_assessment import BodyAssessment
from app.models.client_profile import ClientProfile
from app.models.user import User
from app.schemas.body_assessment import BodyAssessmentResponse
from app.schemas.client_profile import ClientProfileResponse
from app.schemas.user import UserRead
from app.services.coach_service import (
    ClientProfileNotFoundError,
    CoachClientNotFoundError,
    get_assigned_client_profile,
    list_assigned_client_assessments,
    list_assigned_clients,
)


def require_coach(
    current_user: CurrentUserDependency,
) -> User:
    if current_user.role != "coach":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operación requiere una cuenta de entrenador.",
        )

    return current_user


CoachDependency = Annotated[
    User,
    Depends(require_coach),
]


router = APIRouter(
    prefix="/coach",
    tags=["Coach"],
)


@router.get(
    "/clients",
    response_model=list[UserRead],
)
def get_my_clients(
    db: SessionDependency,
    coach: CoachDependency,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[User]:
    return list_assigned_clients(
        db,
        coach_id=coach.id,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/clients/{client_id}/profile",
    response_model=ClientProfileResponse,
)
def get_my_client_profile(
    client_id: Annotated[int, Path(gt=0)],
    db: SessionDependency,
    coach: CoachDependency,
) -> ClientProfile:
    try:
        return get_assigned_client_profile(
            db,
            coach_id=coach.id,
            client_id=client_id,
        )
    except (
        CoachClientNotFoundError,
        ClientProfileNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.get(
    "/clients/{client_id}/assessments",
    response_model=list[BodyAssessmentResponse],
)
def get_my_client_assessments(
    client_id: Annotated[int, Path(gt=0)],
    db: SessionDependency,
    coach: CoachDependency,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[BodyAssessment]:
    try:
        return list_assigned_client_assessments(
            db,
            coach_id=coach.id,
            client_id=client_id,
            offset=offset,
            limit=limit,
        )
    except (
        CoachClientNotFoundError,
        ClientProfileNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error