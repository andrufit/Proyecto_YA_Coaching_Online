import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.schemas.user import UserCreate
from app.services.user_service import (
    UserAlreadyExistsError,
    authenticate_user,
    create_user,
)


@pytest.fixture
def db() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_create_user(db: Session) -> None:
    user = create_user(
        db,
        UserCreate(
            email="CLIENTE@EXAMPLE.COM",
            password="ClaveSegura123!",
        ),
    )

    assert user.id is not None
    assert user.email == "cliente@example.com"
    assert user.role == "client"
    assert user.hashed_password != "ClaveSegura123!"


def test_duplicate_email_is_rejected(
    db: Session,
) -> None:
    user_data = UserCreate(
        email="cliente@example.com",
        password="ClaveSegura123!",
    )

    create_user(db, user_data)

    with pytest.raises(UserAlreadyExistsError):
        create_user(db, user_data)


def test_authenticate_user(db: Session) -> None:
    create_user(
        db,
        UserCreate(
            email="cliente@example.com",
            password="ClaveSegura123!",
        ),
    )

    authenticated_user = authenticate_user(
        db,
        "cliente@example.com",
        "ClaveSegura123!",
    )

    assert authenticated_user is not None

    assert (
        authenticate_user(
            db,
            "cliente@example.com",
            "ClaveIncorrecta",
        )
        is None
    )