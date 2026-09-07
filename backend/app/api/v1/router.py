from fastapi import APIRouter

from app.api.v1 import auth, client_profiles, users


api_router = APIRouter(
    prefix="/api/v1",
)

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(client_profiles.router)