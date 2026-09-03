from fastapi import APIRouter

from app.api.dependencies import CurrentUserDependency
from app.models.user import User
from app.schemas.user import UserRead


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserRead,
)
def read_current_user(
    current_user: CurrentUserDependency,
) -> User:
    return current_user