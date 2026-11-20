from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings


app = FastAPI(
    title="Y&A Coaching Online API",
    description="API REST para la plataforma de gestión de fitness y nutrición",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.browser_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def private_api_responses(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/v1/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Keep form feedback without returning raw inputs or validator context.
    path = request.url.path.rstrip("/")
    credentials_form = path.startswith("/api/v1/auth/") or path == "/api/v1/admin/coaches"
    details = []
    for error in exc.errors():
        location = error.get("loc", ())
        if credentials_form:
            field = location[-1] if location else None
            messages = {
                "email": "Revisa el correo electrónico.",
                "username": "Escribe tu correo electrónico.",
                "password": "Revisa la contraseña ingresada.",
                "token": "Revisa el enlace de recuperación.",
            }
            # Only schema-defined field names may appear in credential errors.
            message = messages.get(field, "Revisa los datos del formulario.")
            location = ("body", field) if field in messages else ("body",)
        else:
            message = error["msg"]
        details.append({"loc": location, "type": error["type"], "msg": message})
    return JSONResponse(status_code=422, content={"detail": details})

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
