from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import (
    CurrentUserDependency,
    SessionDependency,
)
from app.models.client_profile import ClientProfile
from app.models.user import User
from app.schemas.body_assessment import (
    BodyAssessmentCreate,
    BodyAssessmentResponse,
)
from app.schemas.client_profile import (
    ClientProfileCreate,
    ClientProfileResponse,
    ClientProfileUpdate,
)
from app.services.client_profile_service import (
    create_body_assessment,
    create_client_profile,
    get_body_assessments,
    get_client_profile_by_user_id,
    update_client_profile,
)


router = APIRouter(
    prefix="/client-profile",
    tags=["Client Profile"],
)


def require_client_role(current_user: User) -> None:
    if current_user.role != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operación está disponible solamente para clientes.",
        )


def require_client_profile(
    db: SessionDependency,
    current_user: CurrentUserDependency,
) -> ClientProfile:
    require_client_role(current_user)

    profile = get_client_profile_by_user_id(
        db,
        current_user.id,
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El cliente todavía no tiene un perfil.",
        )

    return profile


@router.post(
    "",
    response_model=ClientProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_client_profile(
    profile_data: ClientProfileCreate,
    db: SessionDependency,
    current_user: CurrentUserDependency,
) -> ClientProfile:
    require_client_role(current_user)

    existing_profile = get_client_profile_by_user_id(
        db,
        current_user.id,
    )

    if existing_profile is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El cliente ya tiene un perfil.",
        )

    return create_client_profile(
        db,
        current_user.id,
        profile_data,
    )


@router.get(
    "/me",
    response_model=ClientProfileResponse,
)
def get_my_client_profile(
    db: SessionDependency,
    current_user: CurrentUserDependency,
) -> ClientProfile:
    return require_client_profile(
        db,
        current_user,
    )


@router.patch(
    "/me",
    response_model=ClientProfileResponse,
)
def update_my_client_profile(
    profile_data: ClientProfileUpdate,
    db: SessionDependency,
    current_user: CurrentUserDependency,
) -> ClientProfile:
    profile = require_client_profile(
        db,
        current_user,
    )

    return update_client_profile(
        db,
        profile,
        profile_data,
    )


@router.post(
    "/me/assessments",
    response_model=BodyAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_body_assessment(
    assessment_data: BodyAssessmentCreate,
    db: SessionDependency,
    current_user: CurrentUserDependency,
):
    profile = require_client_profile(
        db,
        current_user,
    )

    return create_body_assessment(
        db,
        profile.id,
        assessment_data,
    )


@router.get(
    "/me/assessments",
    response_model=list[BodyAssessmentResponse],
)
def list_my_body_assessments(
    db: SessionDependency,
    current_user: CurrentUserDependency,
) -> list:
    profile = require_client_profile(
        db,
        current_user,
    )

    return get_body_assessments(
        db,
        profile.id,
    )