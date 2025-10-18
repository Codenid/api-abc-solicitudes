from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api_abc_solicitudes.routers.reclamos import router as reclamos_router

app = FastAPI(
    title="API de Reclamos",
    version="1.0.0",
    description="""
API simple para gestionar **reclamos**.

**Endpoints:**
- `GET /reclamos`: consulta básica con filtros y paginación.
- `GET /reclamos/{id}`: detalle de un reclamo (catálogos, movimientos, decisión).
- `POST /reclamos`: creación de reclamo, opcionalmente con movimientos.
"""
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reclamos_router)
