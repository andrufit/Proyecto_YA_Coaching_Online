import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate


def test_user_create_valid() -> None:
    user = UserCreate(
        email="CLIENTE@EXAMPLE.COM",
        password="ClaveSegura123!",
    )

    assert str(user.email).lower() == "cliente@example.com"
    assert user.password == "ClaveSegura123!"


def test_user_create_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            email="correo-invalido",
            password="ClaveSegura123!",
        )


def test_user_create_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            email="cliente@example.com",
            password="123",
        )