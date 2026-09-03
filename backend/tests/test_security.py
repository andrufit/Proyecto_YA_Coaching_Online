from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing() -> None:
    password = "ClaveSegura123!"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password) is True
    assert verify_password("ClaveIncorrecta", hashed_password) is False


def test_access_token() -> None:
    token = create_access_token(subject="1")
    payload = decode_access_token(token)

    assert payload["sub"] == "1"
    assert "iat" in payload
    assert "exp" in payload