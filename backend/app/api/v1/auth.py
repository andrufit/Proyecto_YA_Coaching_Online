from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import SessionDependency
from app.core.security import create_access_token
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import (
    UserAlreadyExistsError,
    authenticate_user,
    create_user,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    db: SessionDependency,
) -> UserRead:
    try:
        return create_user(db, user_data)
    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con este correo.",
        ) from error


@router.post(
    "/login",
    response_model=Token,
)
def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    db: SessionDependency,
) -> Token:
    user = authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    access_token = create_access_token(
        subject=str(user.id),
    )

    return Token(
        access_token=access_token,
    )