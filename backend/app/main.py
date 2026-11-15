"""Punto de entrada de la API.

Arranque local:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    admin,
    archivos,
    auth,
    comunidad,
    contenido,
    directorio,
    eventos,
    health,
    notificaciones,
    perfiles,
    proveedores,
)
from app.core.config import get_settings
from app.core.database import get_session_manager
from app.events.gestor import configurar_observadores


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Construye el motor una sola vez al arrancar. Si la configuración falta,
    # el proceso falla aquí y no en la primera petición.
    get_session_manager()
    # Suscribe los tres observadores del patrón Observer (informe ES2).
    configurar_observadores()
    yield
    get_session_manager().dispose()


def crear_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Cosplay Chile API",
        description="Plataforma de contenidos, directorio y comunidad para el cosplay chileno.",
        version=health.VERSION,
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # /health queda en la raíz porque Render la consulta sin prefijo.
    app.include_router(health.router)

    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(auth.router_privacidad, prefix=settings.api_prefix)
    app.include_router(admin.router, prefix=settings.api_prefix)
    app.include_router(proveedores.router, prefix=settings.api_prefix)
    app.include_router(contenido.router, prefix=settings.api_prefix)
    app.include_router(eventos.router, prefix=settings.api_prefix)
    app.include_router(comunidad.router_foro, prefix=settings.api_prefix)
    app.include_router(comunidad.router_desafios, prefix=settings.api_prefix)
    app.include_router(perfiles.router, prefix=settings.api_prefix)
    app.include_router(directorio.router, prefix=settings.api_prefix)
    app.include_router(notificaciones.router, prefix=settings.api_prefix)
    app.include_router(archivos.router, prefix=settings.api_prefix)

    # El adaptador local sirve las imágenes subidas. En producción se usa el
    # adaptador de Cloudinary y este montaje queda vacío, sin romper nada.
    directorio_archivos = Path(settings.storage_directorio)
    directorio_archivos.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/archivos", StaticFiles(directory=str(directorio_archivos)), name="archivos"
    )

    @app.get("/", include_in_schema=False)
    def raiz() -> dict:
        return {
            "servicio": settings.app_name,
            "version": health.VERSION,
            "documentacion": "/docs",
            "salud": "/health",
        }

    return app


app = crear_app()
