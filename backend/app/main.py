from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router


app = FastAPI(
    title="Y&A Coaching Online API",
    description="API REST para la plataforma de gestión de fitness y nutrición",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {
        "message": "Y&A Coaching Online API",
        "status": "running",
    }


@app.get("/health", tags=["Estado del Sistema"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "Backend de Y&A Coaching Online funcionando correctamente",
    }
