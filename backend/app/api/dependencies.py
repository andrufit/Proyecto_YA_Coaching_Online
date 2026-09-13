from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User
from app.services.user_service import get_user_by_id


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


SessionDependency = Annotated[
    Session,
    Depends(get_db),
]


def get_current_user(
    db: SessionDependency,
    token: Annotated[
        str,
        Depends(oauth2_scheme),
    ],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No fue posible validar las credenciales.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        user_id = int(subject)

    except (
        jwt.InvalidTokenError,
        TypeError,
        ValueError,
    ) as error:
        raise credentials_exception from error

    user = get_user_by_id(db, user_id)

    if user is None or not user.is_active:
        raise credentials_exception

    if payload.get("ver", 0) != user.auth_version:
        raise credentials_exception

    return user


CurrentUserDependency = Annotated[
    User,
    Depends(get_current_user),
]