"""Punto de entrada de la API REST de Cosplay Chile (FastAPI, documentación OpenAPI en /docs)."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routers import (
    archivos,
    auth,
    busqueda,
    comunidad,
    contacto,
    contenidos,
    directorio,
    eventos,
    favoritos,
    inicio,
    meta,
    moderacion,
    notificaciones,
    perfil,
    reportes,
)
from app.core.config import get_settings
from app.db.session_manager import DatabaseSessionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

ROUTERS = [auth, perfil, meta, archivos, contacto, contenidos, favoritos, notificaciones, moderacion,
           directorio, eventos, reportes, comunidad, inicio, busqueda]


@asynccontextmanager
async def lifespan(app: FastAPI):
    gestor_bd = DatabaseSessionManager()
    gestor_bd.init(get_settings().database_url)  # no hace nada si ya fue inicializado (pruebas)
    yield
    await gestor_bd.close()


def crear_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title="Cosplay Chile API",
        version="0.1.0",
        description="API REST del prototipo Cosplay Chile: guías, directorio, calendario y comunidad cosplay.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origenes,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def cabeceras_seguridad(request, call_next):  # RNF-06
        respuesta = await call_next(request)
        respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
        respuesta.headers.setdefault("X-Frame-Options", "DENY")
        respuesta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return respuesta

    for modulo in ROUTERS:
        app.include_router(modulo.router)

    s.media_path.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=s.media_path), name="media")

    @app.get("/api/salud", tags=["Sistema"])
    async def salud():
        return {"estado": "ok"}

    return app


app = crear_app()
