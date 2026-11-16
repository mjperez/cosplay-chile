"""Búsqueda global con autocompletado y filtros (RF-31; Fig. 4 «Aplicar filtros»)."""
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.deps import DbSession
from app.models.enums import Nivel, Region
from app.services.busqueda_service import TIPOS, buscar

router = APIRouter(prefix="/api/busqueda", tags=["Inicio y búsqueda"])


class Resultado(BaseModel):
    tipo: str
    id: str
    titulo: str
    subtitulo: str
    enlace: str


class Resultados(BaseModel):
    q: str
    total: int
    grupos: dict[str, list[Resultado]]


@router.get("", response_model=Resultados, summary="Buscar en toda la plataforma")
async def busqueda(
    db: DbSession,
    q: Annotated[str, Query(min_length=2, max_length=100)],
    tipos: Annotated[str | None, Query(description=f"Lista separada por comas: {', '.join(TIPOS)}")] = None,
    region: Region | None = None,
    categoria: str | None = None,
    nivel: Nivel | None = None,
    limite: Annotated[int, Query(ge=1, le=30)] = 8,
):
    elegidos = {t.strip() for t in tipos.split(",")} & set(TIPOS) if tipos else set(TIPOS)
    grupos = await buscar(db, q, tipos=elegidos, region=region, categoria=categoria, nivel=nivel, limite=limite)
    return Resultados(q=q, total=sum(len(v) for v in grupos.values()), grupos=grupos)


@router.get("/sugerencias", response_model=list[Resultado], summary="Autocompletado (máximo 8 sugerencias)")
async def sugerencias(db: DbSession, q: Annotated[str, Query(min_length=2, max_length=100)]):
    grupos = await buscar(db, q, tipos=set(TIPOS), region=None, categoria=None, nivel=None, limite=3)
    # Intercala tipos para que la lista sea variada
    salida, i = [], 0
    while len(salida) < 8 and any(i < len(v) for v in grupos.values()):
        for t in TIPOS:
            if i < len(grupos[t]) and len(salida) < 8:
                salida.append(grupos[t][i])
        i += 1
    return salida
