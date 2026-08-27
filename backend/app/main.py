from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings



# Inicializamos la aplicación con la información de tu proyecto
app = FastAPI(
    title="Y&A Coaching Online API",
    description="API REST para la plataforma de gestión de fitness y nutrición",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {
        "message": "Y&A Coaching Online API",
        "status": "running",
    }

# Endpoint de salud requerido en el Sprint 0
@app.get("/health", tags=["Estado del Sistema"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok", 
        "message": "Backend de Y&A Coaching Online funcionando correctamente"
    }

