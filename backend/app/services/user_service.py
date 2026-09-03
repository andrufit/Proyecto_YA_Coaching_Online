from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import UserCreate


class UserAlreadyExistsError(Exception):
    """Indica que el correo ya pertenece a otro usuario."""


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    normalized_email = normalize_email(email)

    statement = select(User).where(
        User.email == normalized_email,
    )

    return db.scalar(statement)


def create_user(
    db: Session,
    user_data: UserCreate,
) -> User:
    normalized_email = normalize_email(
        str(user_data.email),
    )

    if get_user_by_email(db, normalized_email) is not None:
        raise UserAlreadyExistsError

    user = User(
        email=normalized_email,
        hashed_password=hash_password(
            user_data.password,
        ),
        role="client",
        is_active=True,
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise UserAlreadyExistsError from error

    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    user = get_user_by_email(db, email)

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.hashed_password,
    ):
        return None

    return user