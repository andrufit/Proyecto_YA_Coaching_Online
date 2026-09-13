from fastapi import APIRouter
from app.api.v1 import training_plans
from app.api.v1 import nutrition_plans

from app.api.v1 import (
    admin,
    auth,
    client_profiles,
    coach,
    users,
)


api_router = APIRouter(
    prefix="/api/v1",
)

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(client_profiles.router)
api_router.include_router(admin.router)
api_router.include_router(coach.router)
api_router.include_router(training_plans.router)
api_router.include_router(nutrition_plans.router)
