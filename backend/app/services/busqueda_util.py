"""Coincidencia sin tildes ni mayúsculas, que aprovecha los índices trigram (f_unaccent(lower(col)))."""
from sqlalchemy import func


def patron(q: str) -> str:
    escapado = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


def coincide(columna, q: str):
    return func.f_unaccent(func.lower(columna)).like(func.f_unaccent(func.lower(patron(q))), escape="\\")
