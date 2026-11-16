"""Vocabularios para el frontend (etiquetas en español de Chile)."""
from fastapi import APIRouter

from app.models.enums import REGIONES
from app.models.etiquetas import ETIQUETAS

router = APIRouter(prefix="/api/meta", tags=["Metadatos"])


@router.get("", summary="Regiones y etiquetas de los vocabularios")
async def meta():
    return {"regiones": {r.value: nombre for r, nombre in REGIONES.items()}, **ETIQUETAS}
