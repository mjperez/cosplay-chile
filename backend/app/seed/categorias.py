"""Categorías iniciales para el contenido editorial.

Sin categorías el editor no se puede probar: la validación rechaza cualquier
id que no exista. Estas cinco salen de los temas que aparecen en la toma de
requerimientos (dolores D1 a D5 de la codificación de comentarios).

Ejecución:
    python -m app.seed.categorias
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.contenido import CategoriaContenido
from app.repositories import contenido as repo

CATEGORIAS: list[dict] = [
    {"nombre": "Armaduras y props", "descripcion": "Goma eva, termoformado, impresión 3D y pintura."},
    {"nombre": "Pelucas y maquillaje", "descripcion": "Estilizado, colocación y caracterización."},
    {"nombre": "Costura y vestuario", "descripcion": "Patrones, telas, confección y ajustes."},
    {"nombre": "Presupuesto y compras", "descripcion": "Dónde comprar, cuánto cuesta y cómo ahorrar."},
    {"nombre": "Eventos y comunidad", "descripcion": "Convenciones, concursos y organización de grupos."},
]


def cargar(sesion: Session) -> tuple[int, int]:
    """Devuelve (creadas, ya existentes)."""
    creadas = 0
    existentes = 0

    for categoria in CATEGORIAS:
        if repo.categoria_por_nombre(sesion, categoria["nombre"]) is not None:
            existentes += 1
            continue
        sesion.add(CategoriaContenido(**categoria))
        creadas += 1

    sesion.flush()
    return creadas, existentes


def main() -> None:
    from app.core.database import get_session_manager

    with get_session_manager().session() as sesion:
        creadas, existentes = cargar(sesion)

    print(f"categorias creadas: {creadas}")
    print(f"ya existian:        {existentes}")
    print(f"total definido:     {len(CATEGORIAS)}")


if __name__ == "__main__":
    main()
