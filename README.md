# Y&A Coaching Online

Plataforma web para la gestión de entrenamiento, nutrición y seguimiento de clientes.

## Tecnologías

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Pytest
- Docker Compose

### Frontend

- React
- TypeScript
- Vite

## Requisitos

- Python 3.14 o compatible
- Node.js 20 o superior
- Docker Desktop
- Git

## Configuración de PostgreSQL

Crear el archivo privado de configuración:

```powershell
Copy-Item backend\.env.example backend\.env
```

Editar `backend/.env` y reemplazar `CHANGE_ME` por una contraseña local segura.

Iniciar PostgreSQL:

```powershell
docker compose up -d db
docker compose ps
```

## Instalación del backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
```

Backend disponible en:

- API: http://127.0.0.1:8000
- Salud: http://127.0.0.1:8000/health
- Swagger: http://127.0.0.1:8000/docs

## Instalación del frontend

Desde la raíz del proyecto:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Frontend disponible en:

- http://localhost:5173

## Pruebas del backend

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m pytest -v
alembic check
```

## Validación del frontend

```powershell
cd frontend
npm run lint
npm run build
```

## Variables de entorno

Los archivos `.env` contienen información privada y no deben subirse al repositorio.

Utilizar como referencia:

- `backend/.env.example`
- `frontend/.env.example`

## Estado del proyecto

Sprint 0 completado:

- Estructura inicial del proyecto.
- Backend FastAPI operativo.
- Frontend React operativo.
- PostgreSQL ejecutándose con Docker.
- SQLAlchemy y Alembic configurados.
- Migración inicial de `users`.
- Comunicación React → FastAPI.
- CORS configurado.
- Pruebas básicas del backend.
- Validación y compilación del frontend.

El Sprint 1 incluirá autenticación, seguridad y gestión inicial de usuarios.