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
from app.models.coach_assignment import CoachAssignment
from app.models.user import User
from app.schemas.coach_assignment import (
    CoachAssignmentCreate,
    CoachAssignmentRead,
)
from app.schemas.user import UserCreate, UserRead
from app.services.admin_service import (
    create_coach,
    list_coaches,
)
from app.services.coach_assignment_service import (
    AssignmentConflictError,
    AssignmentUserNotFoundError,
    InvalidAssignmentError,
    assign_coach,
    get_client_assignment,
    list_clients,
)
from app.services.user_service import UserAlreadyExistsError


def require_admin(
    current_user: CurrentUserDependency,
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operación requiere una cuenta administradora.",
        )

    return current_user


router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
    dependencies=[Depends(require_admin)],
)


@router.post(
    "/coaches",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_coach_account(
    user_data: UserCreate,
    db: SessionDependency,
) -> User:
    try:
        return create_coach(db, user_data)
    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con este correo.",
        ) from error


@router.get(
    "/coaches",
    response_model=list[UserRead],
)
def get_coach_accounts(
    db: SessionDependency,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[User]:
    return list_coaches(db, offset=offset, limit=limit)


@router.get(
    "/clients",
    response_model=list[UserRead],
)
def get_client_accounts(
    db: SessionDependency,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[User]:
    return list_clients(db, offset=offset, limit=limit)


@router.put(
    "/clients/{client_id}/coach",
    response_model=CoachAssignmentRead,
)
def set_client_coach(
    client_id: Annotated[int, Path(gt=0)],
    assignment_data: CoachAssignmentCreate,
    db: SessionDependency,
) -> CoachAssignment:
    try:
        return assign_coach(
            db,
            client_id=client_id,
            coach_id=assignment_data.coach_id,
        )
    except AssignmentUserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except InvalidAssignmentError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except AssignmentConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "/clients/{client_id}/coach",
    response_model=CoachAssignmentRead,
)
def get_assigned_coach(
    client_id: Annotated[int, Path(gt=0)],
    db: SessionDependency,
) -> CoachAssignment:
    client = db.get(User, client_id)

    if client is None or client.role != "client":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe el cliente indicado.",
        )

    assignment = get_client_assignment(db, client_id)

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El cliente todavía no tiene entrenador asignado.",
        )

    return assignment