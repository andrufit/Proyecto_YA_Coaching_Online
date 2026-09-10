from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import (
    UserAlreadyExistsError,
    get_user_by_email,
    normalize_email,
)


def create_coach(
    db: Session,
    user_data: UserCreate,
) -> User:
    email = normalize_email(str(user_data.email))

    if get_user_by_email(db, email) is not None:
        raise UserAlreadyExistsError

    coach = User(
        email=email,
        hashed_password=hash_password(user_data.password),
        role="coach",
        is_active=True,
    )

    db.add(coach)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()

        if get_user_by_email(db, email) is not None:
            raise UserAlreadyExistsError from error

        raise

    db.refresh(coach)
    return coach


def list_coaches(
    db: Session,
    offset: int = 0,
    limit: int = 50,
) -> list[User]:
    statement = (
        select(User)
        .where(User.role == "coach")
        .order_by(User.id)
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).all())