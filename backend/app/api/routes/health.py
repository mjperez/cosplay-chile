"""Endpoint de salud exigido por US-01.

Render consulta esta ruta para decidir si el servicio está listo para recibir
tráfico. Por eso devuelve 200 solo cuando la base responde: un 200 con la base
caída haría que Render enviara peticiones a un proceso que no puede atenderlas.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.core.database import get_session_manager

router = APIRouter(tags=["salud"])

VERSION = "0.1.0"


@router.get("/health", summary="Estado del servicio y de la base de datos")
def health(response: Response) -> dict:
    settings = get_settings()
    diagnostico = get_session_manager().health_check()

    if not diagnostico["ok"]:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        # En producción no se expone el mensaje del driver: puede incluir
        # host, puerto o usuario de la cadena de conexión.
        if settings.es_produccion:
            diagnostico["detalle"] = "conexion no disponible"

    return {
        "status": "ok" if diagnostico["ok"] else "degradado",
        "version": VERSION,
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": diagnostico,
    }
