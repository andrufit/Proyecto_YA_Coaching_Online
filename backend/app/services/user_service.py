import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import UserCreate


# Compute once per worker, with the same password hasher as real accounts.
_DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


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

    candidate_hash = user.hashed_password if user is not None else _DUMMY_PASSWORD_HASH
    matches = verify_password(password, candidate_hash)
    if user is None or not user.is_active or not matches:
        return None

    return user
